"""
Rutas para gestión de Tenants y Multi-Tenancy.
"""

import os
from datetime import timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import (
    AuditLogListResponse,
    AuditLogResponse,
    ForcePasswordRequest,
    GlobalUserCreate,
    GlobalUserListResponse,
    GlobalUserResponse,
    GlobalUserUpdate,
    ImpersonationResponse,
    PagoHistorialResponse,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
    PlanWithStats,
    SaaSDashboardKPIs,
    SuscripcionResponse,
    TenantBriefResponse,
    TenantChangePlanRequest,
    TenantCreate,
    TenantExtendTrialRequest,
    TenantMetricas,
    TenantPulse,
    TenantRegisterRequest,
    TenantRegisterResponse,
    TenantResponse,
    TenantUpdate,
    UsuarioResponse,
    UsuarioTenantDetailResponse,
    UsuarioTenantResponse,
)
from ..datos.modelos import Usuarios
from ..datos.modelos_tenant import Tenants
from ..servicios.servicio_audit import ServicioAuditLog
from ..servicios.servicio_tenants import ServicioTenants
from ..utils.logger import setup_logger
from ..utils.seguridad import create_access_token, get_current_user, get_superadmin

router = APIRouter()
logger = setup_logger(__name__)


# ============================================================================
# REGISTRO PÚBLICO (Onboarding)
# ============================================================================


@router.post(
    "/register",
    response_model=TenantRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo tenant",
    description="Registro público de nuevos tenants. No requiere autenticación.",
)
async def registrar_tenant(datos: TenantRegisterRequest, db: Session = Depends(get_db)):
    """
    Registra un nuevo tenant con su usuario administrador.
    """
    servicio = ServicioTenants(db)

    try:
        tenant, admin = servicio.registrar_tenant(datos)

        return TenantRegisterResponse(
            tenant=TenantResponse.model_validate(tenant),
            user=admin,
            message="Tenant registrado exitosamente. Puede iniciar sesión.",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# PLANES (Público)
# ============================================================================


@router.get("/planes", response_model=List[PlanResponse], summary="Listar planes disponibles")
async def listar_planes(db: Session = Depends(get_db)):
    """
    Lista los planes de suscripción disponibles.
    Endpoint público para mostrar en la página de registro.
    """
    servicio = ServicioTenants(db)
    planes = servicio.obtener_planes_activos()
    return [PlanResponse.model_validate(p) for p in planes]


# ============================================================================
# MIS TENANTS (Usuario autenticado)
# ============================================================================


@router.get("/mis-tenants", response_model=List[TenantBriefResponse], summary="Listar mis tenants")
async def mis_tenants(current_user: Usuarios = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Lista los tenants a los que pertenece el usuario autenticado.
    """
    servicio = ServicioTenants(db)
    usuarios_tenants = servicio.obtener_tenants_usuario(current_user.id)

    tenants = []
    for ut in usuarios_tenants:
        tenant = servicio.obtener_tenant_por_id(ut.tenant_id)
        if tenant and tenant.esta_activo:
            tenants.append(TenantBriefResponse.model_validate(tenant))

    return tenants


@router.get("/me", response_model=TenantResponse, summary="Obtener tenant actual")
async def obtener_tenant_actual(
    tenant_id: UUID = Query(..., description="ID del tenant"),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene información del tenant actual del usuario.
    Valida que el usuario tenga acceso al tenant.
    """
    servicio = ServicioTenants(db)

    # Validar acceso
    acceso = servicio.validar_acceso_tenant(current_user.id, tenant_id)
    if not acceso:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este tenant")

    tenant = servicio.obtener_tenant_por_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    return TenantResponse.model_validate(tenant)


# ============================================================================
# PLANES ADMIN (Superadmin) - MUST be before /{tenant_id}
# ============================================================================


@router.get(
    "/planes/admin/",
    response_model=List[PlanWithStats],
    summary="Listar todos los planes con stats",
    dependencies=[Depends(get_superadmin)],
)
async def listar_planes_admin(db: Session = Depends(get_db)):
    """
    Lista todos los planes (activos e inactivos) con cantidad de tenants.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    resultados = servicio.listar_todos_planes()
    return [
        PlanWithStats(**PlanResponse.model_validate(r["plan"]).model_dump(), tenant_count=r["tenant_count"])
        for r in resultados
    ]


@router.post(
    "/planes/admin/",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear plan",
    dependencies=[Depends(get_superadmin)],
)
async def crear_plan(
    request: Request, datos: PlanCreate, superadmin: Usuarios = Depends(get_superadmin), db: Session = Depends(get_db)
):
    """Crea un nuevo plan de suscripción. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        plan = servicio.crear_plan(datos)
        audit.registrar_desde_request(
            request, superadmin, "plan.create", "plan", resource_id=plan.id, changes=datos.model_dump()
        )
        return PlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/planes/admin/{plan_id}",
    response_model=PlanWithStats,
    summary="Obtener plan con stats",
    dependencies=[Depends(get_superadmin)],
)
async def obtener_plan_admin(plan_id: UUID, db: Session = Depends(get_db)):
    """Obtiene un plan con count de tenants. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    plan = servicio.obtener_plan_por_id(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
    # Get tenant count
    from sqlalchemy import func as sqla_func

    from ..datos.modelos_tenant import Tenants

    tenant_count = (
        db.query(sqla_func.count(Tenants.id))
        .filter(Tenants.plan_id == plan_id, Tenants.estado.in_(["activo", "trial"]))
        .scalar()
        or 0
    )

    return PlanWithStats(**PlanResponse.model_validate(plan).model_dump(), tenant_count=tenant_count)


@router.put(
    "/planes/admin/{plan_id}",
    response_model=PlanResponse,
    summary="Actualizar plan",
    dependencies=[Depends(get_superadmin)],
)
async def actualizar_plan(
    request: Request,
    plan_id: UUID,
    datos: PlanUpdate,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """Actualiza un plan existente. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        plan = servicio.actualizar_plan(plan_id, datos)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
        audit.registrar_desde_request(
            request,
            superadmin,
            "plan.update",
            "plan",
            resource_id=plan_id,
            changes=datos.model_dump(exclude_unset=True),
        )
        return PlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/planes/admin/{plan_id}",
    response_model=PlanResponse,
    summary="Desactivar plan",
    dependencies=[Depends(get_superadmin)],
)
async def desactivar_plan(
    request: Request, plan_id: UUID, superadmin: Usuarios = Depends(get_superadmin), db: Session = Depends(get_db)
):
    """Desactiva un plan (no lo elimina). **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        plan = servicio.desactivar_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
        audit.registrar_desde_request(request, superadmin, "plan.deactivate", "plan", resource_id=plan_id)
        return PlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# DASHBOARD SAAS (Superadmin) - MUST be before /{tenant_id}
# ============================================================================


@router.get(
    "/dashboard/",
    response_model=SaaSDashboardKPIs,
    summary="Dashboard SaaS KPIs",
    dependencies=[Depends(get_superadmin)],
)
async def dashboard_saas(db: Session = Depends(get_db)):
    """
    KPIs del negocio SaaS: MRR, tenants por estado, churn, revenue por plan.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    kpis = servicio.obtener_saas_kpis()
    return SaaSDashboardKPIs(**kpis)


# ============================================================================
# AUDIT LOGS (Superadmin) - MUST be before /{tenant_id}
# ============================================================================


@router.get(
    "/audit-logs/",
    response_model=AuditLogListResponse,
    summary="Audit logs globales",
    dependencies=[Depends(get_superadmin)],
)
async def listar_audit_logs_globales(
    action: Optional[str] = Query(None, description="Filtrar por acción"),
    resource_type: Optional[str] = Query(None, description="Filtrar por tipo de recurso"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Lista todos los audit logs del sistema (cross-tenant).
    **Requiere ser SuperAdmin.**
    """
    audit = ServicioAuditLog(db)
    items, total = audit.listar(
        action=action,
        resource_type=resource_type,
        page=page,
        limit=limit,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        limit=limit,
    )


# ============================================================================
# USER GOVERNANCE (Superadmin) - MUST be before /{tenant_id}
# ============================================================================


@router.get(
    "/usuarios/",
    response_model=GlobalUserListResponse,
    summary="Listar todos los usuarios globales",
    dependencies=[Depends(get_superadmin)],
)
async def listar_usuarios_global(
    busqueda: Optional[str] = Query(None, description="Buscar por nombre o email"),
    estado: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    es_superadmin: Optional[bool] = Query(None, description="Filtrar por superadmin"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista todos los usuarios del sistema. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    items, total = servicio.listar_usuarios_global(
        busqueda=busqueda, estado=estado, es_superadmin=es_superadmin, page=page, limit=limit
    )
    return GlobalUserListResponse(
        items=[
            GlobalUserResponse(
                **UsuarioResponse.model_validate(i["usuario"]).model_dump(), tenant_count=i["tenant_count"]
            )
            for i in items
        ],
        total=total,
        page=page,
        limit=limit,
    )


@router.post(
    "/usuarios/",
    response_model=GlobalUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario global",
    dependencies=[Depends(get_superadmin)],
)
async def crear_usuario_global(
    request: Request,
    datos: GlobalUserCreate,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """Crea un usuario global sin asociación a tenant. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        usuario = servicio.crear_usuario_global(datos)
        audit.registrar_desde_request(
            request,
            superadmin,
            "user.create",
            "user",
            resource_id=usuario.id,
            changes={"email": usuario.email, "rol": usuario.rol},
        )
        return GlobalUserResponse(**UsuarioResponse.model_validate(usuario).model_dump(), tenant_count=0)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/usuarios/{user_id}",
    response_model=GlobalUserResponse,
    summary="Obtener usuario global",
    dependencies=[Depends(get_superadmin)],
)
async def obtener_usuario_global(user_id: UUID, db: Session = Depends(get_db)):
    """Obtiene un usuario por su ID. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    usuario = servicio.obtener_usuario_por_id(user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    tenants = servicio.obtener_tenants_de_usuario(user_id)
    return GlobalUserResponse(**UsuarioResponse.model_validate(usuario).model_dump(), tenant_count=len(tenants))


@router.put(
    "/usuarios/{user_id}",
    response_model=GlobalUserResponse,
    summary="Actualizar usuario global",
    dependencies=[Depends(get_superadmin)],
)
async def actualizar_usuario_global(
    request: Request,
    user_id: UUID,
    datos: GlobalUserUpdate,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """Actualiza datos de un usuario. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        usuario = servicio.actualizar_usuario_global(user_id, datos)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        audit.registrar_desde_request(
            request,
            superadmin,
            "user.update",
            "user",
            resource_id=user_id,
            changes=datos.model_dump(exclude_unset=True),
        )
        tenants = servicio.obtener_tenants_de_usuario(user_id)
        return GlobalUserResponse(**UsuarioResponse.model_validate(usuario).model_dump(), tenant_count=len(tenants))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/usuarios/{user_id}/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Forzar reset de contraseña",
    dependencies=[Depends(get_superadmin)],
)
async def force_reset_password(
    request: Request,
    user_id: UUID,
    datos: ForcePasswordRequest,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """Fuerza el cambio de contraseña de cualquier usuario. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    usuario = servicio.force_reset_password(user_id, datos.new_password)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    audit.registrar_desde_request(request, superadmin, "user.force_password_reset", "user", resource_id=user_id)


@router.post(
    "/usuarios/{user_id}/toggle-status",
    response_model=GlobalUserResponse,
    summary="Activar/desactivar usuario",
    dependencies=[Depends(get_superadmin)],
)
async def toggle_user_status(
    request: Request, user_id: UUID, superadmin: Usuarios = Depends(get_superadmin), db: Session = Depends(get_db)
):
    """Activa o desactiva un usuario globalmente. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        usuario = servicio.toggle_user_status(user_id)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        audit.registrar_desde_request(
            request,
            superadmin,
            "user.toggle_status",
            "user",
            resource_id=user_id,
            changes={"nuevo_estado": usuario.estado},
        )
        tenants = servicio.obtener_tenants_de_usuario(user_id)
        return GlobalUserResponse(**UsuarioResponse.model_validate(usuario).model_dump(), tenant_count=len(tenants))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/usuarios/{user_id}/tenants", summary="Tenants del usuario", dependencies=[Depends(get_superadmin)])
async def obtener_tenants_de_usuario(user_id: UUID, db: Session = Depends(get_db)):
    """Lista todos los tenants a los que pertenece un usuario. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    usuario = servicio.obtener_usuario_por_id(user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return servicio.obtener_tenants_de_usuario(user_id)


# ============================================================================
# GHOST MODE - IMPERSONACIÓN (Superadmin) - MUST be before generic /{tenant_id}
# ============================================================================


@router.post(
    "/{tenant_id}/impersonate/{user_id}",
    response_model=ImpersonationResponse,
    summary="Impersonar usuario en tenant",
)
async def impersonar_usuario(
    request: Request,
    tenant_id: UUID,
    user_id: UUID,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Genera un token de 15 minutos que actúa como el usuario especificado en el tenant.
    El token de impersonación NO permite: acceso superadmin, cambio de contraseña, ni re-impersonación.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)

    # Validar usuario existe y está activo
    usuario = servicio.obtener_usuario_por_id(user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if not usuario.estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede impersonar a un usuario inactivo"
        )

    # Validar que el usuario pertenece al tenant
    ut = servicio.validar_acceso_tenant(user_id, tenant_id)
    if not ut:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario no pertenece a este tenant")

    # Generar token de impersonación (15 minutos, sin refresh)
    token = create_access_token(
        data={
            "sub": str(user_id),
            "email": usuario.email,
            "rol": ut.rol,
            "impersonating": True,
            "impersonator_id": str(superadmin.id),
        },
        expires_delta=timedelta(minutes=15),
        tenant_id=tenant_id,
        rol_en_tenant=ut.rol,
    )

    audit.registrar_desde_request(
        request,
        superadmin,
        "user.impersonate",
        "user",
        resource_id=user_id,
        tenant_id=tenant_id,
        changes={"impersonated_user": usuario.email, "tenant_id": str(tenant_id), "rol": ut.rol},
    )

    return ImpersonationResponse(
        access_token=token,
        expires_in=900,
        impersonated_user=UsuarioResponse.model_validate(usuario),
        tenant_id=tenant_id,
        rol_en_tenant=ut.rol,
    )


# ============================================================================
# SUPERADMIN - GESTIÓN DE TENANTS
# ============================================================================


@router.get(
    "/", response_model=List[TenantResponse], summary="Listar todos los tenants", dependencies=[Depends(get_superadmin)]
)
async def listar_tenants(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre, slug, NIT o email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Lista todos los tenants del sistema.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    tenants = servicio.listar_tenants(estado=estado, busqueda=busqueda, skip=skip, limit=limit)
    return [TenantResponse.model_validate(t) for t in tenants]


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Obtener tenant por ID",
    dependencies=[Depends(get_superadmin)],
)
async def obtener_tenant(tenant_id: UUID, db: Session = Depends(get_db)):
    """
    Obtiene un tenant por su ID.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    tenant = servicio.obtener_tenant_por_id(tenant_id)

    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    return TenantResponse.model_validate(tenant)


@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear tenant (admin)",
    dependencies=[Depends(get_superadmin)],
)
async def crear_tenant_admin(
    request: Request, datos: TenantCreate, superadmin: Usuarios = Depends(get_superadmin), db: Session = Depends(get_db)
):
    """
    Crea un nuevo tenant desde el panel de administración.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)

    try:
        tenant = servicio.crear_tenant(datos, creado_por=superadmin.id)
        audit.registrar_desde_request(
            request,
            superadmin,
            "tenant.create",
            "tenant",
            resource_id=tenant.id,
            changes={"nombre": tenant.nombre, "slug": tenant.slug},
        )
        return TenantResponse.model_validate(tenant)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{tenant_id}", response_model=TenantResponse, summary="Actualizar tenant", dependencies=[Depends(get_superadmin)]
)
async def actualizar_tenant(
    request: Request,
    tenant_id: UUID,
    datos: TenantUpdate,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Actualiza un tenant existente.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    tenant = servicio.actualizar_tenant(tenant_id, datos)

    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    audit.registrar_desde_request(
        request,
        superadmin,
        "tenant.update",
        "tenant",
        resource_id=tenant_id,
        tenant_id=tenant_id,
        changes=datos.model_dump(exclude_unset=True),
    )
    return TenantResponse.model_validate(tenant)


# ============================================================================
# PULSE (Health Score)
# ============================================================================


@router.get(
    "/{tenant_id}/pulse",
    response_model=TenantPulse,
    summary="Calcular health score de tenant",
    dependencies=[Depends(get_superadmin)],
)
async def get_tenant_pulse(
    tenant_id: UUID, superadmin: Usuarios = Depends(get_superadmin), db: Session = Depends(get_db)
):
    """
    Calcula el Health Score (0-100) de un tenant.
    Basado en: logins recientes, actividad de ventas, estado de suscripción y antigüedad.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    try:
        pulse_data = servicio.calcular_pulse_tenant(tenant_id)
        return TenantPulse(**pulse_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# MAINTENANCE MODE
# ============================================================================


@router.post(
    "/{tenant_id}/mantenimiento",
    response_model=TenantResponse,
    summary="Poner tenant en modo mantenimiento",
    dependencies=[Depends(get_superadmin)],
)
async def poner_mantenimiento(
    request: Request,
    tenant_id: UUID,
    motivo: Optional[str] = Query(None, description="Motivo del mantenimiento"),
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Pone un tenant en modo mantenimiento.
    Los usuarios pueden leer pero no realizar escrituras (POST/PUT/PATCH/DELETE devuelven 503).
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        tenant = servicio.poner_mantenimiento(tenant_id, motivo)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
        audit.registrar_desde_request(
            request,
            superadmin,
            "tenant.maintenance_on",
            "tenant",
            resource_id=tenant_id,
            tenant_id=tenant_id,
            changes={"motivo": motivo},
        )
        return TenantResponse.model_validate(tenant)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{tenant_id}/salir-mantenimiento",
    response_model=TenantResponse,
    summary="Sacar tenant del modo mantenimiento",
    dependencies=[Depends(get_superadmin)],
)
async def salir_mantenimiento(
    request: Request, tenant_id: UUID, superadmin: Usuarios = Depends(get_superadmin), db: Session = Depends(get_db)
):
    """
    Restaura un tenant del modo mantenimiento al estado 'activo'.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        tenant = servicio.salir_mantenimiento(tenant_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
        audit.registrar_desde_request(
            request, superadmin, "tenant.maintenance_off", "tenant", resource_id=tenant_id, tenant_id=tenant_id
        )
        return TenantResponse.model_validate(tenant)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{tenant_id}/suspender",
    response_model=TenantResponse,
    summary="Suspender tenant",
    dependencies=[Depends(get_superadmin)],
)
async def suspender_tenant(
    request: Request,
    tenant_id: UUID,
    motivo: Optional[str] = Query(None, description="Motivo de la suspensión"),
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Suspende un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    tenant = servicio.suspender_tenant(tenant_id, motivo)

    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    audit.registrar_desde_request(
        request,
        superadmin,
        "tenant.suspend",
        "tenant",
        resource_id=tenant_id,
        tenant_id=tenant_id,
        changes={"motivo": motivo},
    )
    return TenantResponse.model_validate(tenant)


@router.post(
    "/{tenant_id}/reactivar",
    response_model=TenantResponse,
    summary="Reactivar tenant",
    dependencies=[Depends(get_superadmin)],
)
async def reactivar_tenant(
    request: Request, tenant_id: UUID, superadmin: Usuarios = Depends(get_superadmin), db: Session = Depends(get_db)
):
    """
    Reactiva un tenant suspendido.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)

    try:
        tenant = servicio.reactivar_tenant(tenant_id)

        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

        audit.registrar_desde_request(
            request, superadmin, "tenant.reactivate", "tenant", resource_id=tenant_id, tenant_id=tenant_id
        )
        return TenantResponse.model_validate(tenant)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{tenant_id}/cancelar",
    response_model=TenantResponse,
    summary="Cancelar tenant",
    dependencies=[Depends(get_superadmin)],
)
async def cancelar_tenant(
    request: Request,
    tenant_id: UUID,
    motivo: Optional[str] = Query(None, description="Motivo de la cancelación"),
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Cancela un tenant permanentemente.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        tenant = servicio.cancelar_tenant(tenant_id, motivo)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
        audit.registrar_desde_request(
            request,
            superadmin,
            "tenant.cancel",
            "tenant",
            resource_id=tenant_id,
            tenant_id=tenant_id,
            changes={"motivo": motivo},
        )
        return TenantResponse.model_validate(tenant)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{tenant_id}/cambiar-plan",
    response_model=TenantResponse,
    summary="Cambiar plan del tenant",
    dependencies=[Depends(get_superadmin)],
)
async def cambiar_plan_tenant(
    request: Request,
    tenant_id: UUID,
    datos: TenantChangePlanRequest,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Cambia el plan de un tenant y crea nueva suscripción.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        tenant = servicio.cambiar_plan_tenant(tenant_id, datos.plan_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
        audit.registrar_desde_request(
            request,
            superadmin,
            "tenant.change_plan",
            "tenant",
            resource_id=tenant_id,
            tenant_id=tenant_id,
            changes={"nuevo_plan_id": str(datos.plan_id)},
        )
        return TenantResponse.model_validate(tenant)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{tenant_id}/extender-trial",
    response_model=TenantResponse,
    summary="Extender trial del tenant",
    dependencies=[Depends(get_superadmin)],
)
async def extender_trial(
    request: Request,
    tenant_id: UUID,
    datos: TenantExtendTrialRequest,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Extiende el periodo trial de un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        tenant = servicio.extender_trial(tenant_id, datos.dias_adicionales)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
        audit.registrar_desde_request(
            request,
            superadmin,
            "tenant.extend_trial",
            "tenant",
            resource_id=tenant_id,
            tenant_id=tenant_id,
            changes={"dias_adicionales": datos.dias_adicionales},
        )
        return TenantResponse.model_validate(tenant)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{tenant_id}/metricas",
    response_model=TenantMetricas,
    summary="Métricas de uso del tenant",
    dependencies=[Depends(get_superadmin)],
)
async def metricas_tenant(tenant_id: UUID, db: Session = Depends(get_db)):
    """
    Métricas de uso de un tenant: usuarios, productos, facturas, ventas.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    metricas = servicio.obtener_metricas_tenant(tenant_id)
    if not metricas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return TenantMetricas(**metricas)


@router.get(
    "/{tenant_id}/suscripciones",
    response_model=List[SuscripcionResponse],
    summary="Historial de suscripciones",
    dependencies=[Depends(get_superadmin)],
)
async def suscripciones_tenant(tenant_id: UUID, db: Session = Depends(get_db)):
    """
    Historial de suscripciones de un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    tenant = servicio.obtener_tenant_por_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    suscripciones = servicio.obtener_suscripciones_tenant(tenant_id)
    return [SuscripcionResponse.model_validate(s) for s in suscripciones]


@router.get(
    "/{tenant_id}/pagos",
    response_model=List[PagoHistorialResponse],
    summary="Historial de pagos",
    dependencies=[Depends(get_superadmin)],
)
async def pagos_tenant(tenant_id: UUID, db: Session = Depends(get_db)):
    """
    Historial de pagos de un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    tenant = servicio.obtener_tenant_por_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    pagos = servicio.obtener_pagos_tenant(tenant_id)
    return [PagoHistorialResponse.model_validate(p) for p in pagos]


# ============================================================================
# USUARIOS DEL TENANT
# ============================================================================


@router.get(
    "/{tenant_id}/usuarios",
    response_model=List[UsuarioTenantDetailResponse],
    summary="Listar usuarios del tenant (con detalle)",
    dependencies=[Depends(get_superadmin)],
)
async def listar_usuarios_tenant(tenant_id: UUID, db: Session = Depends(get_db)):
    """
    Lista los usuarios de un tenant con nombre y email.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)

    tenant = servicio.obtener_tenant_por_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    usuarios = servicio.obtener_usuarios_tenant_con_detalle(tenant_id)
    return [UsuarioTenantDetailResponse(**u) for u in usuarios]


@router.put(
    "/{tenant_id}/usuarios/{usuario_id}/rol",
    response_model=UsuarioTenantResponse,
    summary="Cambiar rol de usuario en tenant",
    dependencies=[Depends(get_superadmin)],
)
async def cambiar_rol_usuario_tenant(
    request: Request,
    tenant_id: UUID,
    usuario_id: UUID,
    rol: str = Query(..., description="Nuevo rol (admin, operador, contador, vendedor, readonly)"),
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Cambia el rol de un usuario dentro de un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        ut = servicio.actualizar_rol_usuario_tenant(usuario_id, tenant_id, rol)
        if not ut:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado en el tenant")
        audit.registrar_desde_request(
            request,
            superadmin,
            "user.role_change",
            "user",
            resource_id=usuario_id,
            tenant_id=tenant_id,
            changes={"nuevo_rol": rol},
        )
        return UsuarioTenantResponse.model_validate(ut)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{tenant_id}/usuarios/{usuario_id}",
    response_model=UsuarioTenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar usuario al tenant",
    dependencies=[Depends(get_superadmin)],
)
async def agregar_usuario_tenant(
    request: Request,
    tenant_id: UUID,
    usuario_id: UUID,
    rol: str = Query(
        "operador", description="Rol del usuario en el tenant (admin, operador, contador, vendedor, readonly)"
    ),
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Agrega un usuario existente a un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)

    try:
        usuario_tenant = servicio.agregar_usuario_a_tenant(usuario_id=usuario_id, tenant_id=tenant_id, rol=rol)
        audit.registrar_desde_request(
            request,
            superadmin,
            "user.add_to_tenant",
            "user",
            resource_id=usuario_id,
            tenant_id=tenant_id,
            changes={"rol": rol},
        )
        return UsuarioTenantResponse.model_validate(usuario_tenant)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{tenant_id}/usuarios/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover usuario del tenant",
    dependencies=[Depends(get_superadmin)],
)
async def remover_usuario_tenant(
    request: Request,
    tenant_id: UUID,
    usuario_id: UUID,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Remueve un usuario de un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    eliminado = servicio.remover_usuario_de_tenant(usuario_id, tenant_id)

    if not eliminado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado en el tenant")

    audit.registrar_desde_request(
        request, superadmin, "user.remove_from_tenant", "user", resource_id=usuario_id, tenant_id=tenant_id
    )


# ============================================================================
# AUDIT LOGS POR TENANT (Superadmin)
# ============================================================================


@router.get(
    "/{tenant_id}/audit-logs/",
    response_model=AuditLogListResponse,
    summary="Audit logs de un tenant",
    dependencies=[Depends(get_superadmin)],
)
async def listar_audit_logs_tenant(
    tenant_id: UUID,
    action: Optional[str] = Query(None, description="Filtrar por acción"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Lista los audit logs de un tenant específico.
    **Requiere ser SuperAdmin.**
    """
    audit = ServicioAuditLog(db)
    items, total = audit.listar(
        tenant_id=tenant_id,
        action=action,
        page=page,
        limit=limit,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        limit=limit,
    )


# ============================================================================
# LOGO UPLOAD (Superadmin)
# ============================================================================

_LOGOS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "logos")
_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
_MAX_SIZE = 2 * 1024 * 1024  # 2 MB


@router.post(
    "/{tenant_id}/logo",
    response_model=TenantResponse,
    summary="Subir logo del tenant",
    dependencies=[Depends(get_superadmin)],
)
async def subir_logo_tenant(
    request: Request,
    tenant_id: UUID,
    file: UploadFile = File(...),
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db),
):
    """
    Sube el logo de un tenant. Acepta JPEG, PNG o WebP (máx. 2 MB).
    **Requiere ser SuperAdmin.**
    """
    # Validar tipo MIME
    if file.content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no permitido. Use JPEG, PNG o WebP.",
        )

    # Leer contenido y validar tamaño
    content = await file.read()
    if len(content) > _MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo supera el límite de 2 MB.",
        )

    # Determinar extensión
    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    ext = ext_map[file.content_type]

    # Guardar en disco
    os.makedirs(_LOGOS_DIR, exist_ok=True)
    filename = f"{tenant_id}.{ext}"
    filepath = os.path.join(_LOGOS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    # Actualizar url_logo en DB
    tenant = db.query(Tenants).filter(Tenants.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    tenant.url_logo = f"/static/logos/{filename}"
    db.commit()
    db.refresh(tenant)

    audit = ServicioAuditLog(db)
    audit.registrar_desde_request(
        request,
        superadmin,
        "tenant.logo_upload",
        "tenant",
        resource_id=tenant_id,
        tenant_id=tenant_id,
        changes={"url_logo": tenant.url_logo},
    )

    return TenantResponse.model_validate(tenant)
