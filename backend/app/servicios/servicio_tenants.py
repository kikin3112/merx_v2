"""
Servicio para gestión de Tenants y Multi-Tenancy.
Maneja CRUD de tenants, onboarding, y asignación de usuarios.
"""

import re
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import or_, func as sqla_func

from ..datos.modelos import (
    Usuarios,
    Productos,
    Ventas,
    Terceros,
    CuentasContables,
    ConfiguracionContable,
    MediosPago,
    Secuencias,
)
from ..datos.modelos_tenant import Planes, Tenants, UsuariosTenants, Suscripciones, HistorialPagos
from ..datos.esquemas import (
    TenantCreate,
    TenantUpdate,
    TenantRegisterRequest,
    UsuarioTenantCreate,
    UsuarioTenantUpdate,
    PlanCreate,
    PlanUpdate,
    GlobalUserCreate,
    GlobalUserUpdate,
)
from ..datos.db import set_tenant_context
from ..utils.seguridad import hash_password
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ServicioTenants:
    """
    Servicio para operaciones de tenants.
    """

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # PLANES
    # ========================================================================

    def obtener_planes_activos(self) -> List[Planes]:
        """Obtiene todos los planes activos."""
        return self.db.query(Planes).filter(Planes.esta_activo == True).order_by(Planes.precio_mensual).all()

    def obtener_plan_por_id(self, plan_id: UUID) -> Optional[Planes]:
        """Obtiene un plan por su ID."""
        return self.db.query(Planes).filter(Planes.id == plan_id).first()

    def obtener_plan_default(self) -> Optional[Planes]:
        """Obtiene el plan marcado como default."""
        return self.db.query(Planes).filter(Planes.es_default == True, Planes.esta_activo == True).first()

    # ========================================================================
    # TENANTS - CRUD
    # ========================================================================

    def obtener_tenant_por_id(self, tenant_id: UUID) -> Optional[Tenants]:
        """Obtiene un tenant por su ID."""
        return self.db.query(Tenants).filter(Tenants.id == tenant_id).first()

    def obtener_tenant_por_slug(self, slug: str) -> Optional[Tenants]:
        """Obtiene un tenant por su slug."""
        return self.db.query(Tenants).filter(Tenants.slug == slug).first()

    def obtener_tenant_por_nit(self, nit: str) -> Optional[Tenants]:
        """Obtiene un tenant por su NIT."""
        return self.db.query(Tenants).filter(Tenants.nit == nit).first()

    def listar_tenants(
        self, estado: Optional[str] = None, busqueda: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Tenants]:
        """
        Lista tenants con filtros opcionales.
        Solo para superadmin.
        """
        query = self.db.query(Tenants)

        if estado:
            query = query.filter(Tenants.estado == estado)

        if busqueda:
            busqueda_like = f"%{busqueda}%"
            query = query.filter(
                or_(
                    Tenants.nombre.ilike(busqueda_like),
                    Tenants.slug.ilike(busqueda_like),
                    Tenants.nit.ilike(busqueda_like),
                    Tenants.email_contacto.ilike(busqueda_like),
                )
            )

        return query.order_by(Tenants.created_at.desc()).offset(skip).limit(limit).all()

    def crear_tenant(self, datos: TenantCreate, creado_por: Optional[UUID] = None) -> Tenants:
        """
        Crea un nuevo tenant con su usuario admin inicial.

        Args:
            datos: Datos del tenant y admin
            creado_por: ID del usuario que crea el tenant (superadmin)

        Returns:
            Tenant creado

        Raises:
            ValueError: Si el slug o NIT ya existen
        """
        # Validar slug único
        if self.obtener_tenant_por_slug(datos.slug):
            raise ValueError(f"El slug '{datos.slug}' ya está en uso")

        # Validar NIT único si se proporciona
        if datos.nit and self.obtener_tenant_por_nit(datos.nit):
            raise ValueError(f"El NIT '{datos.nit}' ya está registrado")

        # Validar plan
        plan = self.obtener_plan_por_id(datos.plan_id)
        if not plan:
            raise ValueError("Plan no encontrado")

        # Validar email admin único
        admin_existente = self.db.query(Usuarios).filter(Usuarios.email == datos.admin_email).first()
        if admin_existente:
            raise ValueError(f"El email '{datos.admin_email}' ya está registrado")

        # Crear tenant
        tenant = Tenants(
            nombre=datos.nombre,
            slug=datos.slug,
            nit=datos.nit,
            email_contacto=datos.email_contacto,
            telefono=datos.telefono,
            direccion=datos.direccion,
            ciudad=datos.ciudad,
            departamento=datos.departamento,
            url_logo=datos.url_logo,
            color_primario=datos.color_primario,
            color_secundario=datos.color_secundario,
            plan_id=datos.plan_id,
            estado="activo",
            fecha_inicio_suscripcion=datetime.now(timezone.utc),
            fecha_fin_suscripcion=datetime.now(timezone.utc) + timedelta(days=30),
        )
        self.db.add(tenant)
        self.db.flush()  # Para obtener el ID

        # Crear usuario admin
        admin = Usuarios(
            nombre=datos.admin_nombre,
            email=datos.admin_email,
            password_hash=hash_password(datos.admin_password),
            rol="admin",
            estado=True,
            es_superadmin=False,
        )
        self.db.add(admin)
        self.db.flush()

        # Crear relación usuario-tenant
        usuario_tenant = UsuariosTenants(
            usuario_id=admin.id, tenant_id=tenant.id, rol="admin", esta_activo=True, es_default=True
        )
        self.db.add(usuario_tenant)

        # Crear suscripción inicial
        suscripcion = Suscripciones(
            tenant_id=tenant.id,
            plan_id=datos.plan_id,
            periodo_inicio=datetime.now(timezone.utc),
            periodo_fin=datetime.now(timezone.utc) + timedelta(days=30),
            estado="trial" if plan.precio_mensual == 0 else "activo",
        )
        self.db.add(suscripcion)

        self.db.commit()
        self.db.refresh(tenant)

        self._inicializar_configuracion_tenant(tenant.id)
        self.db.commit()

        logger.info(f"Tenant creado: {tenant.slug} (ID: {tenant.id})")
        return tenant

    def actualizar_tenant(self, tenant_id: UUID, datos: TenantUpdate) -> Optional[Tenants]:
        """Actualiza un tenant existente."""
        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            return None

        # Actualizar campos no nulos
        update_data = datos.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            setattr(tenant, campo, valor)

        self.db.commit()
        self.db.refresh(tenant)

        logger.info(f"Tenant actualizado: {tenant.slug}")
        return tenant

    def suspender_tenant(self, tenant_id: UUID, motivo: str = None) -> Optional[Tenants]:
        """Suspende un tenant."""
        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            return None

        tenant.estado = "suspendido"
        self.db.commit()

        logger.warning(f"Tenant suspendido: {tenant.slug}. Motivo: {motivo or 'No especificado'}")
        return tenant

    def reactivar_tenant(self, tenant_id: UUID) -> Optional[Tenants]:
        """Reactiva un tenant suspendido."""
        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            return None

        if tenant.estado != "suspendido":
            raise ValueError("Solo se pueden reactivar tenants suspendidos")

        tenant.estado = "activo"
        self.db.commit()

        logger.info(f"Tenant reactivado: {tenant.slug}")
        return tenant

    # ========================================================================
    # REGISTRO PÚBLICO (ONBOARDING)
    # ========================================================================

    def registrar_tenant(self, datos: TenantRegisterRequest) -> tuple[Tenants, Usuarios]:
        """
        Registra un nuevo tenant desde el formulario público de onboarding.

        Args:
            datos: Datos del formulario de registro

        Returns:
            Tuple (tenant, usuario_admin)

        Raises:
            ValueError: Si hay datos duplicados
        """
        # Normalizar slug
        slug = self._normalizar_slug(datos.slug)

        # Validar slug único
        if self.obtener_tenant_por_slug(slug):
            raise ValueError(f"El identificador '{slug}' ya está en uso")

        # Validar NIT único si se proporciona
        if datos.nit and self.obtener_tenant_por_nit(datos.nit):
            raise ValueError(f"El NIT '{datos.nit}' ya está registrado")

        # Validar email admin único
        if self.db.query(Usuarios).filter(Usuarios.email == datos.admin_email).first():
            raise ValueError(f"El email '{datos.admin_email}' ya está registrado")

        # Obtener plan (default o especificado)
        if datos.plan_id:
            plan = self.obtener_plan_por_id(datos.plan_id)
            if not plan or not plan.esta_activo:
                raise ValueError("Plan no disponible")
        else:
            plan = self.obtener_plan_default()
            if not plan:
                raise ValueError("No hay plan default configurado")

        # Crear tenant
        tenant = Tenants(
            nombre=datos.nombre_empresa,
            slug=slug,
            nit=datos.nit,
            email_contacto=datos.email_empresa,
            telefono=datos.telefono,
            ciudad=datos.ciudad,
            departamento=datos.departamento,
            plan_id=plan.id,
            estado="trial",
            fecha_inicio_suscripcion=datetime.now(timezone.utc),
            fecha_fin_suscripcion=datetime.now(timezone.utc) + timedelta(days=14),  # 14 días trial
        )
        self.db.add(tenant)
        self.db.flush()

        # Crear usuario admin
        admin = Usuarios(
            nombre=datos.admin_nombre,
            email=datos.admin_email,
            password_hash=hash_password(datos.admin_password),
            rol="admin",
            estado=True,
            es_superadmin=False,
        )
        self.db.add(admin)
        self.db.flush()

        # Crear relación usuario-tenant
        usuario_tenant = UsuariosTenants(
            usuario_id=admin.id, tenant_id=tenant.id, rol="admin", esta_activo=True, es_default=True
        )
        self.db.add(usuario_tenant)

        # Crear suscripción trial
        suscripcion = Suscripciones(
            tenant_id=tenant.id,
            plan_id=plan.id,
            periodo_inicio=datetime.now(timezone.utc),
            periodo_fin=datetime.now(timezone.utc) + timedelta(days=14),
            estado="trial",
        )
        self.db.add(suscripcion)

        self.db.commit()
        self.db.refresh(tenant)
        self.db.refresh(admin)

        self._inicializar_configuracion_tenant(tenant.id)
        self.db.commit()

        logger.info(f"Nuevo tenant registrado: {tenant.slug} (admin: {admin.email})")
        return tenant, admin

    def _normalizar_slug(self, slug: str) -> str:
        """Normaliza un slug a minúsculas y caracteres válidos."""
        slug = slug.lower().strip()
        slug = re.sub(r"[^a-z0-9-]", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")
        return slug

    # ========================================================================
    # USUARIOS-TENANTS
    # ========================================================================

    def obtener_tenants_usuario(self, usuario_id: UUID) -> List[UsuariosTenants]:
        """Obtiene los tenants a los que pertenece un usuario."""
        return (
            self.db.query(UsuariosTenants)
            .filter(UsuariosTenants.usuario_id == usuario_id, UsuariosTenants.esta_activo == True)
            .all()
        )

    def obtener_usuarios_tenant(self, tenant_id: UUID) -> List[UsuariosTenants]:
        """Obtiene los usuarios de un tenant."""
        return (
            self.db.query(UsuariosTenants)
            .filter(UsuariosTenants.tenant_id == tenant_id, UsuariosTenants.esta_activo == True)
            .all()
        )

    def obtener_usuario_tenant(self, usuario_id: UUID, tenant_id: UUID) -> Optional[UsuariosTenants]:
        """Obtiene la relación usuario-tenant específica."""
        return (
            self.db.query(UsuariosTenants)
            .filter(UsuariosTenants.usuario_id == usuario_id, UsuariosTenants.tenant_id == tenant_id)
            .first()
        )

    # Roles permitidos dentro de un tenant (superadmin es EXCLUSIVO del sistema)
    ROLES_TENANT_PERMITIDOS = {"admin", "operador", "contador", "vendedor", "readonly"}

    def agregar_usuario_a_tenant(
        self, usuario_id: UUID, tenant_id: UUID, rol: str = "operador", es_default: bool = False
    ) -> UsuariosTenants:
        """
        Agrega un usuario existente a un tenant.

        Args:
            usuario_id: ID del usuario
            tenant_id: ID del tenant
            rol: Rol en el tenant (NO puede ser 'superadmin')
            es_default: Si es el tenant default del usuario

        Returns:
            UsuariosTenants creado

        Raises:
            ValueError: Si el usuario ya pertenece al tenant, rol inválido,
                        o ya existe un admin en el tenant
        """
        # Validar que el rol sea permitido en contexto de tenant
        if rol not in self.ROLES_TENANT_PERMITIDOS:
            raise ValueError(
                f"Rol '{rol}' no permitido en tenants. Roles válidos: {', '.join(sorted(self.ROLES_TENANT_PERMITIDOS))}"
            )

        # Validar máximo 1 admin por tenant
        if rol == "admin":
            admin_existente = (
                self.db.query(UsuariosTenants)
                .filter(
                    UsuariosTenants.tenant_id == tenant_id,
                    UsuariosTenants.rol == "admin",
                    UsuariosTenants.esta_activo == True,
                )
                .first()
            )
            if admin_existente:
                raise ValueError("Este tenant ya tiene un usuario con rol admin. Solo se permite un admin por tenant.")

        # Verificar que no exista la relación
        existente = self.obtener_usuario_tenant(usuario_id, tenant_id)
        if existente:
            raise ValueError("El usuario ya pertenece a este tenant")

        # Verificar usuario existe
        usuario = self.db.query(Usuarios).filter(Usuarios.id == usuario_id).first()
        if not usuario:
            raise ValueError("Usuario no encontrado")

        # No permitir asignar superadmins a tenants
        if usuario.es_superadmin:
            raise ValueError(
                "Un superadmin del sistema no puede ser asignado a un tenant. "
                "El superadmin gestiona tenants sin pertenecer a ellos."
            )

        # Verificar tenant existe
        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant no encontrado")

        # Si es default, quitar default de otros
        if es_default:
            self.db.query(UsuariosTenants).filter(
                UsuariosTenants.usuario_id == usuario_id, UsuariosTenants.es_default == True
            ).update({"es_default": False})

        # Crear relación
        usuario_tenant = UsuariosTenants(
            usuario_id=usuario_id, tenant_id=tenant_id, rol=rol, esta_activo=True, es_default=es_default
        )
        self.db.add(usuario_tenant)
        self.db.commit()
        self.db.refresh(usuario_tenant)

        logger.info(f"Usuario {usuario_id} agregado al tenant {tenant_id} como {rol}")
        return usuario_tenant

    def actualizar_rol_usuario_tenant(
        self, usuario_id: UUID, tenant_id: UUID, nuevo_rol: str
    ) -> Optional[UsuariosTenants]:
        """Actualiza el rol de un usuario en un tenant."""
        # Validar que el rol sea permitido en contexto de tenant
        if nuevo_rol not in self.ROLES_TENANT_PERMITIDOS:
            raise ValueError(
                f"Rol '{nuevo_rol}' no permitido en tenants. "
                f"Roles válidos: {', '.join(sorted(self.ROLES_TENANT_PERMITIDOS))}"
            )

        usuario_tenant = self.obtener_usuario_tenant(usuario_id, tenant_id)
        if not usuario_tenant:
            return None

        # Validar máximo 1 admin por tenant (si se cambia a admin)
        if nuevo_rol == "admin" and usuario_tenant.rol != "admin":
            admin_existente = (
                self.db.query(UsuariosTenants)
                .filter(
                    UsuariosTenants.tenant_id == tenant_id,
                    UsuariosTenants.rol == "admin",
                    UsuariosTenants.esta_activo == True,
                    UsuariosTenants.usuario_id != usuario_id,
                )
                .first()
            )
            if admin_existente:
                raise ValueError("Este tenant ya tiene un usuario con rol admin. Solo se permite un admin por tenant.")

        usuario_tenant.rol = nuevo_rol
        self.db.commit()
        self.db.refresh(usuario_tenant)

        logger.info(f"Rol actualizado: usuario {usuario_id} en tenant {tenant_id} -> {nuevo_rol}")
        return usuario_tenant

    def remover_usuario_de_tenant(self, usuario_id: UUID, tenant_id: UUID) -> bool:
        """
        Remueve un usuario de un tenant (desactiva la relación).

        Returns:
            True si se removió, False si no existía
        """
        usuario_tenant = self.obtener_usuario_tenant(usuario_id, tenant_id)
        if not usuario_tenant:
            return False

        usuario_tenant.esta_activo = False
        self.db.commit()

        logger.info(f"Usuario {usuario_id} removido del tenant {tenant_id}")
        return True

    def validar_acceso_tenant(self, usuario_id: UUID, tenant_id: UUID) -> Optional[UsuariosTenants]:
        """
        Valida si un usuario tiene acceso a un tenant.

        Returns:
            UsuariosTenants si tiene acceso activo, None si no
        """
        # Primero verificar si es superadmin
        usuario = self.db.query(Usuarios).filter(Usuarios.id == usuario_id).first()
        if usuario and usuario.es_superadmin:
            # Superadmin tiene acceso a todo, crear objeto virtual
            return UsuariosTenants(
                usuario_id=usuario_id, tenant_id=tenant_id, rol="superadmin", esta_activo=True, es_default=False
            )

        # Verificar membresía normal
        usuario_tenant = (
            self.db.query(UsuariosTenants)
            .filter(
                UsuariosTenants.usuario_id == usuario_id,
                UsuariosTenants.tenant_id == tenant_id,
                UsuariosTenants.esta_activo == True,
            )
            .first()
        )

        if not usuario_tenant:
            return None

        # Verificar que el tenant esté activo
        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant or not tenant.esta_activo:
            return None

        return usuario_tenant

    # ========================================================================
    # PLANES - CRUD ADMIN
    # ========================================================================

    def listar_todos_planes(self) -> List[dict]:
        """Lista TODOS los planes (activos e inactivos) con count de tenants."""
        planes = self.db.query(Planes).order_by(Planes.precio_mensual).all()
        resultado = []
        for plan in planes:
            tenant_count = (
                self.db.query(sqla_func.count(Tenants.id))
                .filter(Tenants.plan_id == plan.id, Tenants.estado.in_(["activo", "trial"]))
                .scalar()
                or 0
            )
            resultado.append({"plan": plan, "tenant_count": tenant_count})
        return resultado

    def crear_plan(self, datos: PlanCreate) -> Planes:
        """Crea un nuevo plan. Valida nombre único."""
        existente = self.db.query(Planes).filter(Planes.nombre == datos.nombre).first()
        if existente:
            raise ValueError(f"Ya existe un plan con el nombre '{datos.nombre}'")

        plan = Planes(**datos.model_dump())
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        logger.info(f"Plan creado: {plan.nombre} (ID: {plan.id})")
        return plan

    def actualizar_plan(self, plan_id: UUID, datos: PlanUpdate) -> Optional[Planes]:
        """Actualiza un plan existente."""
        plan = self.obtener_plan_por_id(plan_id)
        if not plan:
            return None

        update_data = datos.model_dump(exclude_unset=True)
        # Validar nombre único si se cambia
        if "nombre" in update_data and update_data["nombre"] != plan.nombre:
            existente = (
                self.db.query(Planes).filter(Planes.nombre == update_data["nombre"], Planes.id != plan_id).first()
            )
            if existente:
                raise ValueError(f"Ya existe un plan con el nombre '{update_data['nombre']}'")

        for campo, valor in update_data.items():
            setattr(plan, campo, valor)

        self.db.commit()
        self.db.refresh(plan)
        logger.info(f"Plan actualizado: {plan.nombre}")
        return plan

    def desactivar_plan(self, plan_id: UUID) -> Optional[Planes]:
        """Desactiva un plan. Valida que no tenga tenants activos."""
        plan = self.obtener_plan_por_id(plan_id)
        if not plan:
            return None

        tenant_count = (
            self.db.query(sqla_func.count(Tenants.id))
            .filter(Tenants.plan_id == plan_id, Tenants.estado.in_(["activo", "trial"]))
            .scalar()
            or 0
        )

        if tenant_count > 0:
            raise ValueError(
                f"No se puede desactivar el plan '{plan.nombre}': tiene {tenant_count} tenant(s) activo(s)"
            )

        plan.esta_activo = False
        self.db.commit()
        self.db.refresh(plan)
        logger.info(f"Plan desactivado: {plan.nombre}")
        return plan

    # ========================================================================
    # CICLO DE VIDA TENANT
    # ========================================================================

    def cancelar_tenant(self, tenant_id: UUID, motivo: Optional[str] = None) -> Optional[Tenants]:
        """Cancela un tenant permanentemente."""
        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            return None

        if tenant.estado == "cancelado":
            raise ValueError("El tenant ya está cancelado")

        tenant.estado = "cancelado"
        self.db.commit()
        self.db.refresh(tenant)

        logger.warning(f"Tenant cancelado: {tenant.slug}. Motivo: {motivo or 'No especificado'}")
        return tenant

    def cambiar_plan_tenant(self, tenant_id: UUID, nuevo_plan_id: UUID) -> Optional[Tenants]:
        """Cambia el plan de un tenant y crea nueva suscripción."""
        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            return None

        nuevo_plan = self.obtener_plan_por_id(nuevo_plan_id)
        if not nuevo_plan:
            raise ValueError("Plan no encontrado")
        if not nuevo_plan.esta_activo:
            raise ValueError("El plan seleccionado no está activo")

        plan_anterior_id = tenant.plan_id
        tenant.plan_id = nuevo_plan_id
        tenant.fecha_inicio_suscripcion = datetime.now(timezone.utc)
        tenant.fecha_fin_suscripcion = datetime.now(timezone.utc) + timedelta(days=30)

        # Crear nueva suscripción
        suscripcion = Suscripciones(
            tenant_id=tenant_id,
            plan_id=nuevo_plan_id,
            periodo_inicio=datetime.now(timezone.utc),
            periodo_fin=datetime.now(timezone.utc) + timedelta(days=30),
            estado="activo",
        )
        self.db.add(suscripcion)

        # Si estaba en trial, activar
        if tenant.estado == "trial":
            tenant.estado = "activo"

        self.db.commit()
        self.db.refresh(tenant)

        logger.info(f"Plan cambiado para {tenant.slug}: {plan_anterior_id} -> {nuevo_plan_id}")
        return tenant

    def extender_trial(self, tenant_id: UUID, dias: int) -> Optional[Tenants]:
        """Extiende el periodo trial de un tenant."""
        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            return None

        if tenant.estado != "trial":
            raise ValueError("Solo se puede extender el trial de tenants en estado 'trial'")

        if tenant.fecha_fin_suscripcion:
            tenant.fecha_fin_suscripcion = tenant.fecha_fin_suscripcion + timedelta(days=dias)
        else:
            tenant.fecha_fin_suscripcion = datetime.now(timezone.utc) + timedelta(days=dias)

        self.db.commit()
        self.db.refresh(tenant)

        logger.info(f"Trial extendido +{dias} días para {tenant.slug}")
        return tenant

    # ========================================================================
    # MÉTRICAS
    # ========================================================================

    def obtener_metricas_tenant(self, tenant_id: UUID) -> dict:
        """
        Obtiene métricas de uso de un tenant.
        Queries directas con WHERE tenant_id (superadmin, sin RLS).
        """
        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            return None

        plan = self.obtener_plan_por_id(tenant.plan_id)

        usuarios_count = (
            self.db.query(sqla_func.count(UsuariosTenants.id))
            .filter(UsuariosTenants.tenant_id == tenant_id, UsuariosTenants.esta_activo == True)
            .scalar()
            or 0
        )

        productos_count = (
            self.db.query(sqla_func.count(Productos.id)).filter(Productos.tenant_id == tenant_id).scalar() or 0
        )

        terceros_count = (
            self.db.query(sqla_func.count(Terceros.id)).filter(Terceros.tenant_id == tenant_id).scalar() or 0
        )

        # Ventas del mes actual
        inicio_mes = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        facturas_mes = (
            self.db.query(sqla_func.count(Ventas.id))
            .filter(
                Ventas.tenant_id == tenant_id,
                Ventas.created_at >= inicio_mes,
                Ventas.estado.in_(["CONFIRMADA", "FACTURADA"]),
            )
            .scalar()
            or 0
        )

        # Total ventas mes (sum no funciona con hybrid_property, usar raw)
        ventas_mes_rows = (
            self.db.query(Ventas)
            .filter(
                Ventas.tenant_id == tenant_id,
                Ventas.created_at >= inicio_mes,
                Ventas.estado.in_(["CONFIRMADA", "FACTURADA"]),
            )
            .all()
        )
        ventas_total_mes = sum(float(v.total_venta) for v in ventas_mes_rows)

        return {
            "tenant_id": tenant_id,
            "usuarios_count": usuarios_count,
            "productos_count": productos_count,
            "facturas_mes_count": facturas_mes,
            "ventas_total_mes": ventas_total_mes,
            "terceros_count": terceros_count,
            "max_usuarios": plan.max_usuarios if plan else 0,
            "max_productos": plan.max_productos if plan else 0,
            "max_facturas_mes": plan.max_facturas_mes if plan else 0,
        }

    def obtener_saas_kpis(self) -> dict:
        """Obtiene KPIs agregados del SaaS para dashboard superadmin."""
        total = self.db.query(sqla_func.count(Tenants.id)).scalar() or 0
        activos = self.db.query(sqla_func.count(Tenants.id)).filter(Tenants.estado == "activo").scalar() or 0
        trial = self.db.query(sqla_func.count(Tenants.id)).filter(Tenants.estado == "trial").scalar() or 0
        suspendidos = self.db.query(sqla_func.count(Tenants.id)).filter(Tenants.estado == "suspendido").scalar() or 0
        cancelados = self.db.query(sqla_func.count(Tenants.id)).filter(Tenants.estado == "cancelado").scalar() or 0

        # Nuevos últimos 30 días
        hace_30_dias = datetime.now(timezone.utc) - timedelta(days=30)
        nuevos_30d = self.db.query(sqla_func.count(Tenants.id)).filter(Tenants.created_at >= hace_30_dias).scalar() or 0

        # MRR: sum precio_mensual de planes con tenants activos
        mrr_result = (
            self.db.query(sqla_func.sum(Planes.precio_mensual))
            .join(Tenants, Tenants.plan_id == Planes.id)
            .filter(Tenants.estado.in_(["activo", "trial"]))
            .scalar()
        )
        mrr = float(mrr_result) if mrr_result else 0.0

        # Churn rate: cancelados últimos 30d / (activos al inicio del periodo)
        cancelados_30d = (
            self.db.query(sqla_func.count(Tenants.id))
            .filter(Tenants.estado == "cancelado", Tenants.updated_at >= hace_30_dias)
            .scalar()
            or 0
        )
        base_churn = activos + trial + cancelados_30d
        churn_rate = (cancelados_30d / base_churn * 100) if base_churn > 0 else 0.0

        # Revenue por plan
        revenue_por_plan = []
        planes = self.db.query(Planes).filter(Planes.esta_activo == True).all()
        for plan in planes:
            count = (
                self.db.query(sqla_func.count(Tenants.id))
                .filter(Tenants.plan_id == plan.id, Tenants.estado.in_(["activo", "trial"]))
                .scalar()
                or 0
            )
            revenue_por_plan.append(
                {
                    "plan_id": str(plan.id),
                    "plan_nombre": plan.nombre,
                    "tenant_count": count,
                    "revenue": float(plan.precio_mensual) * count,
                }
            )

        return {
            "total_tenants": total,
            "tenants_activos": activos,
            "tenants_trial": trial,
            "tenants_suspendidos": suspendidos,
            "tenants_cancelados": cancelados,
            "mrr": mrr,
            "nuevos_ultimos_30_dias": nuevos_30d,
            "churn_rate": round(churn_rate, 2),
            "revenue_por_plan": revenue_por_plan,
        }

    # ========================================================================
    # USUARIOS ENHANCED
    # ========================================================================

    def obtener_usuarios_tenant_con_detalle(self, tenant_id: UUID) -> List[dict]:
        """Obtiene usuarios del tenant con nombre y email (JOIN con Usuarios)."""
        resultados = (
            self.db.query(UsuariosTenants, Usuarios)
            .join(Usuarios, Usuarios.id == UsuariosTenants.usuario_id)
            .filter(UsuariosTenants.tenant_id == tenant_id, UsuariosTenants.esta_activo == True)
            .all()
        )

        return [
            {
                "id": ut.id,
                "usuario_id": ut.usuario_id,
                "tenant_id": ut.tenant_id,
                "rol": ut.rol,
                "esta_activo": ut.esta_activo,
                "fecha_ingreso": ut.fecha_ingreso,
                "usuario_nombre": u.nombre,
                "usuario_email": u.email,
            }
            for ut, u in resultados
        ]

    # ========================================================================
    # SUSCRIPCIONES / PAGOS
    # ========================================================================

    def obtener_suscripciones_tenant(self, tenant_id: UUID) -> List[Suscripciones]:
        """Obtiene historial de suscripciones de un tenant."""
        return (
            self.db.query(Suscripciones)
            .filter(Suscripciones.tenant_id == tenant_id)
            .order_by(Suscripciones.created_at.desc())
            .all()
        )

    def obtener_pagos_tenant(self, tenant_id: UUID) -> List[HistorialPagos]:
        """Obtiene historial de pagos de un tenant via sus suscripciones."""
        suscripcion_ids = self.db.query(Suscripciones.id).filter(Suscripciones.tenant_id == tenant_id).subquery()

        return (
            self.db.query(HistorialPagos)
            .filter(HistorialPagos.suscripcion_id.in_(suscripcion_ids))
            .order_by(HistorialPagos.created_at.desc())
            .all()
        )

    # ========================================================================
    # USER GOVERNANCE (GOD MODE)
    # ========================================================================

    def listar_usuarios_global(
        self,
        busqueda: Optional[str] = None,
        estado: Optional[bool] = None,
        es_superadmin: Optional[bool] = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple:
        """Lista todos los usuarios del sistema con count de tenants."""
        query = (
            self.db.query(Usuarios, sqla_func.count(UsuariosTenants.id).label("tenant_count"))
            .outerjoin(UsuariosTenants, Usuarios.id == UsuariosTenants.usuario_id)
            .group_by(Usuarios.id)
        )

        if busqueda:
            term = f"%{busqueda}%"
            query = query.filter(or_(Usuarios.nombre.ilike(term), Usuarios.email.ilike(term)))
        if estado is not None:
            query = query.filter(Usuarios.estado == estado)
        if es_superadmin is not None:
            query = query.filter(Usuarios.es_superadmin == es_superadmin)

        total = query.count()
        offset = (page - 1) * limit
        resultados = query.order_by(Usuarios.created_at.desc()).offset(offset).limit(limit).all()

        items = [{"usuario": u, "tenant_count": tc} for u, tc in resultados]
        return items, total

    def obtener_usuario_por_id(self, user_id: UUID) -> Optional[Usuarios]:
        """Obtiene un usuario global por ID."""
        return self.db.query(Usuarios).filter(Usuarios.id == user_id).first()

    def crear_usuario_global(self, datos: GlobalUserCreate) -> Usuarios:
        """Crea un usuario global sin asociación a tenant.

        Raises:
            ValueError: Si el email ya está registrado.
        """
        existing = self.db.query(Usuarios).filter(Usuarios.email == datos.email).first()
        if existing:
            raise ValueError(f"El email '{datos.email}' ya está registrado")

        usuario = Usuarios(
            nombre=datos.nombre,
            email=datos.email,
            password_hash=hash_password(datos.password),
            rol=datos.rol,
            estado=datos.estado,
            es_superadmin=False,
        )
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def actualizar_usuario_global(self, user_id: UUID, datos: GlobalUserUpdate) -> Optional[Usuarios]:
        """Actualiza datos globales de un usuario.

        Raises:
            ValueError: Si el email ya está en uso por otro usuario.
        """
        usuario = self.db.query(Usuarios).filter(Usuarios.id == user_id).first()
        if not usuario:
            return None

        update_data = datos.model_dump(exclude_unset=True)

        if "email" in update_data:
            existing = (
                self.db.query(Usuarios).filter(Usuarios.email == update_data["email"], Usuarios.id != user_id).first()
            )
            if existing:
                raise ValueError(f"El email '{update_data['email']}' ya está en uso")

        for field, value in update_data.items():
            setattr(usuario, field, value)

        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def force_reset_password(self, user_id: UUID, new_password: str) -> Optional[Usuarios]:
        """Fuerza el cambio de contraseña de cualquier usuario (superadmin)."""
        usuario = self.db.query(Usuarios).filter(Usuarios.id == user_id).first()
        if not usuario:
            return None
        usuario.password_hash = hash_password(new_password)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def toggle_user_status(self, user_id: UUID) -> Optional[Usuarios]:
        """Activa/desactiva un usuario globalmente.

        Raises:
            ValueError: Si se intenta desactivar al único superadmin.
        """
        usuario = self.db.query(Usuarios).filter(Usuarios.id == user_id).first()
        if not usuario:
            return None

        # No permitir desactivar al último superadmin activo
        if usuario.es_superadmin and usuario.estado:
            activos_count = (
                self.db.query(sqla_func.count(Usuarios.id))
                .filter(Usuarios.es_superadmin == True, Usuarios.estado == True)
                .scalar()
                or 0
            )
            if activos_count <= 1:
                raise ValueError("No se puede desactivar al único superadmin activo")

        usuario.estado = not usuario.estado
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def obtener_tenants_de_usuario(self, user_id: UUID) -> list:
        """Lista todos los tenants+roles de un usuario con nombre del tenant."""
        resultados = (
            self.db.query(UsuariosTenants, Tenants)
            .join(Tenants, UsuariosTenants.tenant_id == Tenants.id)
            .filter(UsuariosTenants.usuario_id == user_id)
            .order_by(Tenants.nombre)
            .all()
        )

        return [
            {
                "usuario_tenant_id": ut.id,
                "tenant_id": t.id,
                "tenant_nombre": t.nombre,
                "tenant_slug": t.slug,
                "tenant_estado": t.estado,
                "rol": ut.rol,
                "esta_activo": ut.esta_activo,
                "fecha_ingreso": ut.fecha_ingreso,
            }
            for ut, t in resultados
        ]

    # =========================================================================
    # PULSE (Health Score)
    # =========================================================================

    def calcular_pulse_tenant(self, tenant_id: UUID) -> dict:
        """
        Calcula el Health Score (0-100) de un tenant para predecir churn.

        Score components:
        - Logins recientes (7d):  30 pts
        - Actividad ventas (30d): 30 pts
        - Estado suscripción:     25 pts
        - Antigüedad:             15 pts
        """
        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} no encontrado")

        now = datetime.now(timezone.utc)
        score = 0

        # --- Logins recientes (últimos 7 días) ---
        siete_dias = now - timedelta(days=7)
        logins_recientes = (
            self.db.query(sqla_func.count(Usuarios.id))
            .join(UsuariosTenants, UsuariosTenants.usuario_id == Usuarios.id)
            .filter(UsuariosTenants.tenant_id == tenant_id, Usuarios.ultimo_acceso >= siete_dias)
            .scalar()
            or 0
        )

        # 0 logins=0, 1=15, 2=22, 3+=30
        if logins_recientes >= 3:
            score += 30
        elif logins_recientes == 2:
            score += 22
        elif logins_recientes == 1:
            score += 15

        # --- Actividad de ventas (últimos 30 días) ---
        treinta_dias = now - timedelta(days=30)
        ventas_mes = (
            self.db.query(sqla_func.count(Ventas.id))
            .filter(Ventas.tenant_id == tenant_id, Ventas.created_at >= treinta_dias, Ventas.deleted_at.is_(None))
            .scalar()
            or 0
        )

        # 0 ventas=0, 1-4=10, 5-14=20, 15+=30
        if ventas_mes >= 15:
            score += 30
        elif ventas_mes >= 5:
            score += 20
        elif ventas_mes >= 1:
            score += 10

        # --- Estado suscripción ---
        estado_pts = {
            "activo": 25,
            "trial": 15,
            "pendiente": 10,
            "suspendido": 0,
            "cancelado": 0,
            "mantenimiento": 10,
        }
        score += estado_pts.get(tenant.estado, 0)

        # --- Antigüedad ---
        created = tenant.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        dias_activo = (now - created).days

        if dias_activo >= 90:
            score += 15
        elif dias_activo >= 30:
            score += 8
        else:
            score += 3

        # Determinar estado de salud
        if score >= 70:
            estado_salud = "saludable"
        elif score >= 40:
            estado_salud = "en_riesgo"
        else:
            estado_salud = "critico"

        return {
            "tenant_id": tenant_id,
            "score": min(score, 100),
            "estado_salud": estado_salud,
            "logins_recientes": logins_recientes,
            "ventas_mes": ventas_mes,
            "dias_activo": dias_activo,
            "calculado_en": now,
        }

    # =========================================================================
    # MAINTENANCE MODE
    # =========================================================================

    def poner_mantenimiento(self, tenant_id: UUID, motivo: Optional[str] = None) -> Optional[Tenants]:
        """
        Pone un tenant en modo mantenimiento.
        Los usuarios pueden leer pero no escribir (bloqueado en middleware).
        """
        from ..middleware.tenant_context import invalidate_maintenance_cache

        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            return None
        if tenant.estado == "mantenimiento":
            raise ValueError("El tenant ya está en modo mantenimiento")
        if tenant.estado in ("cancelado",):
            raise ValueError(f"No se puede poner en mantenimiento un tenant '{tenant.estado}'")
        tenant.estado = "mantenimiento"
        self.db.commit()
        self.db.refresh(tenant)
        invalidate_maintenance_cache(tenant_id)
        return tenant

    def salir_mantenimiento(self, tenant_id: UUID) -> Optional[Tenants]:
        """
        Saca un tenant del modo mantenimiento, restaurando estado 'activo'.
        """
        from ..middleware.tenant_context import invalidate_maintenance_cache

        tenant = self.obtener_tenant_por_id(tenant_id)
        if not tenant:
            return None
        if tenant.estado != "mantenimiento":
            raise ValueError("El tenant no está en modo mantenimiento")
        tenant.estado = "activo"
        self.db.commit()
        self.db.refresh(tenant)
        invalidate_maintenance_cache(tenant_id)
        return tenant

    def _inicializar_configuracion_tenant(self, tenant_id: UUID) -> None:
        """
        Inicializa configuraciones básicas para un nuevo tenant:
        - Cuentas contables PUC
        - Configuración contable
        - Secuencias
        - Medios de pago
        - Cliente Mostrador
        """
        from decimal import Decimal

        logger.info(f"Inicializando configuración para tenant {tenant_id}...")

        cuentas_map = self._seed_cuentas_contables(tenant_id)
        self._seed_configuracion_contable(tenant_id, cuentas_map)
        self._seed_secuencias(tenant_id)
        self._seed_medios_pago(tenant_id)
        self._seed_cliente_mostrador(tenant_id)

        logger.info(f"Configuración inicial completada para tenant {tenant_id}")

    def _seed_cuentas_contables(self, tenant_id: UUID) -> dict:
        """Crea plan de cuentas PUC básico. Retorna dict codigo -> id."""
        cuentas = [
            {
                "codigo": "1",
                "nombre": "ACTIVO",
                "nivel": 1,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "ACTIVO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "11",
                "nombre": "DISPONIBLE",
                "nivel": 2,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "ACTIVO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "1105",
                "nombre": "CAJA",
                "nivel": 3,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "ACTIVO",
                "acepta_movimiento": True,
            },
            {
                "codigo": "1110",
                "nombre": "BANCOS",
                "nivel": 3,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "ACTIVO",
                "acepta_movimiento": True,
            },
            {
                "codigo": "13",
                "nombre": "DEUDORES",
                "nivel": 2,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "ACTIVO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "1305",
                "nombre": "CLIENTES",
                "nivel": 3,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "ACTIVO",
                "acepta_movimiento": True,
            },
            {
                "codigo": "14",
                "nombre": "INVENTARIOS",
                "nivel": 2,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "ACTIVO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "1430",
                "nombre": "PRODUCTOS EN PROCESO",
                "nivel": 3,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "ACTIVO",
                "acepta_movimiento": True,
            },
            {
                "codigo": "1435",
                "nombre": "MERCANCÍAS",
                "nivel": 3,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "ACTIVO",
                "acepta_movimiento": True,
            },
            {
                "codigo": "2",
                "nombre": "PASIVO",
                "nivel": 1,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "PASIVO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "22",
                "nombre": "PROVEEDORES",
                "nivel": 2,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "PASIVO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "2205",
                "nombre": "PROVEEDORES NACIONALES",
                "nivel": 3,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "PASIVO",
                "acepta_movimiento": True,
            },
            {
                "codigo": "24",
                "nombre": "IMPUESTOS",
                "nivel": 2,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "PASIVO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "2408",
                "nombre": "IVA POR PAGAR",
                "nivel": 3,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "PASIVO",
                "acepta_movimiento": True,
            },
            {
                "codigo": "3",
                "nombre": "PATRIMONIO",
                "nivel": 1,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "PATRIMONIO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "31",
                "nombre": "CAPITAL SOCIAL",
                "nivel": 2,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "PATRIMONIO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "3105",
                "nombre": "CAPITAL SUSCRITO Y PAGADO",
                "nivel": 3,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "PATRIMONIO",
                "acepta_movimiento": True,
            },
            {
                "codigo": "4",
                "nombre": "INGRESOS",
                "nivel": 1,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "INGRESO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "41",
                "nombre": "OPERACIONALES",
                "nivel": 2,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "INGRESO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "4135",
                "nombre": "COMERCIO AL POR MAYOR Y MENOR",
                "nivel": 3,
                "naturaleza": "CREDITO",
                "tipo_cuenta": "INGRESO",
                "acepta_movimiento": True,
            },
            {
                "codigo": "5",
                "nombre": "GASTOS",
                "nivel": 1,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "EGRESO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "51",
                "nombre": "OPERACIONALES DE ADMINISTRACIÓN",
                "nivel": 2,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "EGRESO",
                "acepta_movimiento": False,
            },
            {
                "codigo": "5105",
                "nombre": "GASTOS DE PERSONAL",
                "nivel": 3,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "EGRESO",
                "acepta_movimiento": True,
            },
            {
                "codigo": "6",
                "nombre": "COSTOS DE VENTAS",
                "nivel": 1,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "COSTOS",
                "acepta_movimiento": False,
            },
            {
                "codigo": "61",
                "nombre": "COSTO DE VENTAS Y PRESTACIÓN DE SERVICIOS",
                "nivel": 2,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "COSTOS",
                "acepta_movimiento": False,
            },
            {
                "codigo": "6135",
                "nombre": "COMERCIO AL POR MAYOR Y MENOR",
                "nivel": 3,
                "naturaleza": "DEBITO",
                "tipo_cuenta": "COSTOS",
                "acepta_movimiento": True,
            },
        ]

        cuentas_map = {}
        for cuenta_data in cuentas:
            existing = (
                self.db.query(CuentasContables)
                .filter(CuentasContables.tenant_id == tenant_id, CuentasContables.codigo == cuenta_data["codigo"])
                .first()
            )
            if not existing:
                cuenta = CuentasContables(tenant_id=tenant_id, **cuenta_data)
                self.db.add(cuenta)
                self.db.flush()
                cuentas_map[cuenta_data["codigo"]] = cuenta.id
            else:
                cuentas_map[cuenta_data["codigo"]] = existing.id

        return cuentas_map

    def _seed_configuracion_contable(self, tenant_id: UUID, cuentas_map: dict) -> None:
        """Crea configuración contable básica."""
        configs = [
            {
                "concepto": "VENTA_CONTADO",
                "cuenta_debito_id": cuentas_map.get("1105"),
                "cuenta_credito_id": cuentas_map.get("4135"),
                "descripcion": "Venta de contado: Débito Caja, Crédito Ventas",
            },
            {
                "concepto": "VENTA_CREDITO",
                "cuenta_debito_id": cuentas_map.get("1305"),
                "cuenta_credito_id": cuentas_map.get("4135"),
                "descripcion": "Venta a crédito: Débito Clientes, Crédito Ventas",
            },
            {
                "concepto": "IVA_VENTAS",
                "cuenta_debito_id": None,
                "cuenta_credito_id": cuentas_map.get("2408"),
                "descripcion": "IVA generado en ventas",
            },
            {
                "concepto": "COSTO_VENTAS",
                "cuenta_debito_id": cuentas_map.get("6135"),
                "cuenta_credito_id": cuentas_map.get("1435"),
                "descripcion": "Costo de mercancía vendida",
            },
            {
                "concepto": "COMPRA_CONTADO",
                "cuenta_debito_id": cuentas_map.get("1435"),
                "cuenta_credito_id": cuentas_map.get("1105"),
                "descripcion": "Compra de mercancía de contado",
            },
            {
                "concepto": "PRODUCCION",
                "cuenta_debito_id": cuentas_map.get("1435"),
                "cuenta_credito_id": cuentas_map.get("1430"),
                "descripcion": "Producción: Débito Mercancías, Crédito Productos en Proceso",
            },
        ]

        for cfg in configs:
            existing = (
                self.db.query(ConfiguracionContable)
                .filter(ConfiguracionContable.tenant_id == tenant_id, ConfiguracionContable.concepto == cfg["concepto"])
                .first()
            )
            if not existing:
                config = ConfiguracionContable(tenant_id=tenant_id, **cfg)
                self.db.add(config)

    def _seed_secuencias(self, tenant_id: UUID) -> None:
        """Crea secuencias para numeración automática."""
        secuencias = [
            {"nombre": "COMPRAS", "prefijo": "CMP-", "siguiente_numero": 1, "longitud_numero": 6},
            {"nombre": "COTIZACIONES", "prefijo": "COT-", "siguiente_numero": 1, "longitud_numero": 6},
            {"nombre": "ORDENES_PRODUCCION", "prefijo": "OP-", "siguiente_numero": 1, "longitud_numero": 6},
            {"nombre": "ASIENTOS", "prefijo": "ASI-", "siguiente_numero": 1, "longitud_numero": 6},
            {"nombre": "FACTURAS", "prefijo": "FAC-", "siguiente_numero": 1, "longitud_numero": 6},
            {"nombre": "VENTAS", "prefijo": "VTA-", "siguiente_numero": 1, "longitud_numero": 6},
        ]

        for seq_data in secuencias:
            existing = (
                self.db.query(Secuencias)
                .filter(Secuencias.tenant_id == tenant_id, Secuencias.nombre == seq_data["nombre"])
                .first()
            )
            if not existing:
                secuencia = Secuencias(tenant_id=tenant_id, **seq_data)
                self.db.add(secuencia)

    def _seed_medios_pago(self, tenant_id: UUID) -> None:
        """Crea medios de pago."""
        medios = [
            {"nombre": "Efectivo", "tipo": "EFECTIVO", "requiere_referencia": False, "estado": True},
            {"nombre": "Transferencia Bancaria", "tipo": "TRANSFERENCIA", "requiere_referencia": True, "estado": True},
            {"nombre": "Tarjeta Débito", "tipo": "TARJETA_DEBITO", "requiere_referencia": True, "estado": True},
            {"nombre": "Tarjeta Crédito", "tipo": "TARJETA_CREDITO", "requiere_referencia": True, "estado": True},
        ]

        for medio_data in medios:
            existing = (
                self.db.query(MediosPago)
                .filter(MediosPago.tenant_id == tenant_id, MediosPago.nombre == medio_data["nombre"])
                .first()
            )
            if not existing:
                medio = MediosPago(tenant_id=tenant_id, **medio_data)
                self.db.add(medio)

    def _seed_cliente_mostrador(self, tenant_id: UUID) -> None:
        """Crea el cliente genérico 'Cliente Mostrador'."""
        existing = (
            self.db.query(Terceros)
            .filter(Terceros.tenant_id == tenant_id, Terceros.numero_documento == "222222222222")
            .first()
        )
        if not existing:
            cliente = Terceros(
                tenant_id=tenant_id,
                tipo_documento="NIT",
                numero_documento="222222222222",
                nombre="CLIENTE MOSTRADOR",
                tipo_tercero="CLIENTE",
                email="mostrador@demo.com",
                telefono="0000000",
                direccion="N/A",
                estado=True,
            )
            self.db.add(cliente)
