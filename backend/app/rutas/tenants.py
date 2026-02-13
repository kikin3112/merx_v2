"""
Rutas para gestión de Tenants y Multi-Tenancy.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantBriefResponse,
    TenantRegisterRequest, TenantRegisterResponse,
    PlanResponse, PlanCreate, PlanUpdate, PlanWithStats,
    UsuarioTenantResponse, UsuarioTenantDetailResponse,
    TenantChangePlanRequest, TenantExtendTrialRequest,
    TenantMetricas, SaaSDashboardKPIs,
    SuscripcionResponse, PagoHistorialResponse,
    AuditLogResponse, AuditLogListResponse
)
from ..datos.modelos import Usuarios
from ..servicios.servicio_tenants import ServicioTenants
from ..servicios.servicio_audit import ServicioAuditLog
from ..utils.seguridad import get_current_user, get_superadmin
from ..utils.logger import setup_logger

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
    description="Registro público de nuevos tenants. No requiere autenticación."
)
async def registrar_tenant(
    datos: TenantRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo tenant con su usuario administrador.
    """
    servicio = ServicioTenants(db)

    try:
        tenant, admin = servicio.registrar_tenant(datos)

        return TenantRegisterResponse(
            tenant=TenantResponse.model_validate(tenant),
            user=admin,
            message="Tenant registrado exitosamente. Puede iniciar sesión."
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# PLANES (Público)
# ============================================================================

@router.get(
    "/planes",
    response_model=List[PlanResponse],
    summary="Listar planes disponibles"
)
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

@router.get(
    "/mis-tenants",
    response_model=List[TenantBriefResponse],
    summary="Listar mis tenants"
)
async def mis_tenants(
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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


@router.get(
    "/me",
    response_model=TenantResponse,
    summary="Obtener tenant actual"
)
async def obtener_tenant_actual(
    tenant_id: UUID = Query(..., description="ID del tenant"),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene información del tenant actual del usuario.
    Valida que el usuario tenga acceso al tenant.
    """
    servicio = ServicioTenants(db)

    # Validar acceso
    acceso = servicio.validar_acceso_tenant(current_user.id, tenant_id)
    if not acceso:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este tenant"
        )

    tenant = servicio.obtener_tenant_por_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )

    return TenantResponse.model_validate(tenant)


# ============================================================================
# PLANES ADMIN (Superadmin) - MUST be before /{tenant_id}
# ============================================================================

@router.get(
    "/planes/admin/",
    response_model=List[PlanWithStats],
    summary="Listar todos los planes con stats",
    dependencies=[Depends(get_superadmin)]
)
async def listar_planes_admin(db: Session = Depends(get_db)):
    """
    Lista todos los planes (activos e inactivos) con cantidad de tenants.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    resultados = servicio.listar_todos_planes()
    return [
        PlanWithStats(
            **PlanResponse.model_validate(r["plan"]).model_dump(),
            tenant_count=r["tenant_count"]
        )
        for r in resultados
    ]


@router.post(
    "/planes/admin/",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear plan",
    dependencies=[Depends(get_superadmin)]
)
async def crear_plan(request: Request, datos: PlanCreate, superadmin: Usuarios = Depends(get_superadmin), db: Session = Depends(get_db)):
    """Crea un nuevo plan de suscripción. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        plan = servicio.crear_plan(datos)
        audit.registrar_desde_request(request, superadmin, "plan.create", "plan", resource_id=plan.id, changes=datos.model_dump())
        return PlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/planes/admin/{plan_id}",
    response_model=PlanWithStats,
    summary="Obtener plan con stats",
    dependencies=[Depends(get_superadmin)]
)
async def obtener_plan_admin(plan_id: UUID, db: Session = Depends(get_db)):
    """Obtiene un plan con count de tenants. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    plan = servicio.obtener_plan_por_id(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan no encontrado"
        )
    # Get tenant count
    from sqlalchemy import func as sqla_func
    from ..datos.modelos_tenant import Tenants
    tenant_count = db.query(sqla_func.count(Tenants.id)).filter(
        Tenants.plan_id == plan_id,
        Tenants.estado.in_(["activo", "trial"])
    ).scalar() or 0

    return PlanWithStats(
        **PlanResponse.model_validate(plan).model_dump(),
        tenant_count=tenant_count
    )


@router.put(
    "/planes/admin/{plan_id}",
    response_model=PlanResponse,
    summary="Actualizar plan",
    dependencies=[Depends(get_superadmin)]
)
async def actualizar_plan(
    request: Request,
    plan_id: UUID,
    datos: PlanUpdate,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
):
    """Actualiza un plan existente. **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        plan = servicio.actualizar_plan(plan_id, datos)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        audit.registrar_desde_request(request, superadmin, "plan.update", "plan", resource_id=plan_id, changes=datos.model_dump(exclude_unset=True))
        return PlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/planes/admin/{plan_id}",
    response_model=PlanResponse,
    summary="Desactivar plan",
    dependencies=[Depends(get_superadmin)]
)
async def desactivar_plan(request: Request, plan_id: UUID, superadmin: Usuarios = Depends(get_superadmin), db: Session = Depends(get_db)):
    """Desactiva un plan (no lo elimina). **Requiere ser SuperAdmin.**"""
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    try:
        plan = servicio.desactivar_plan(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        audit.registrar_desde_request(request, superadmin, "plan.deactivate", "plan", resource_id=plan_id)
        return PlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# DASHBOARD SAAS (Superadmin) - MUST be before /{tenant_id}
# ============================================================================

@router.get(
    "/dashboard/",
    response_model=SaaSDashboardKPIs,
    summary="Dashboard SaaS KPIs",
    dependencies=[Depends(get_superadmin)]
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
    dependencies=[Depends(get_superadmin)]
)
async def listar_audit_logs_globales(
    action: Optional[str] = Query(None, description="Filtrar por acción"),
    resource_type: Optional[str] = Query(None, description="Filtrar por tipo de recurso"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
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
# SUPERADMIN - GESTIÓN DE TENANTS
# ============================================================================

@router.get(
    "/",
    response_model=List[TenantResponse],
    summary="Listar todos los tenants",
    dependencies=[Depends(get_superadmin)]
)
async def listar_tenants(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre, slug, NIT o email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Lista todos los tenants del sistema.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    tenants = servicio.listar_tenants(
        estado=estado,
        busqueda=busqueda,
        skip=skip,
        limit=limit
    )
    return [TenantResponse.model_validate(t) for t in tenants]


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Obtener tenant por ID",
    dependencies=[Depends(get_superadmin)]
)
async def obtener_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Obtiene un tenant por su ID.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    tenant = servicio.obtener_tenant_por_id(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )

    return TenantResponse.model_validate(tenant)


@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear tenant (admin)",
    dependencies=[Depends(get_superadmin)]
)
async def crear_tenant_admin(
    request: Request,
    datos: TenantCreate,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo tenant desde el panel de administración.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)

    try:
        tenant = servicio.crear_tenant(datos, creado_por=superadmin.id)
        audit.registrar_desde_request(request, superadmin, "tenant.create", "tenant", resource_id=tenant.id, changes={"nombre": tenant.nombre, "slug": tenant.slug})
        return TenantResponse.model_validate(tenant)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Actualizar tenant",
    dependencies=[Depends(get_superadmin)]
)
async def actualizar_tenant(
    request: Request,
    tenant_id: UUID,
    datos: TenantUpdate,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
):
    """
    Actualiza un tenant existente.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    tenant = servicio.actualizar_tenant(tenant_id, datos)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )

    audit.registrar_desde_request(request, superadmin, "tenant.update", "tenant", resource_id=tenant_id, tenant_id=tenant_id, changes=datos.model_dump(exclude_unset=True))
    return TenantResponse.model_validate(tenant)


@router.post(
    "/{tenant_id}/suspender",
    response_model=TenantResponse,
    summary="Suspender tenant",
    dependencies=[Depends(get_superadmin)]
)
async def suspender_tenant(
    request: Request,
    tenant_id: UUID,
    motivo: Optional[str] = Query(None, description="Motivo de la suspensión"),
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
):
    """
    Suspende un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    tenant = servicio.suspender_tenant(tenant_id, motivo)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )

    audit.registrar_desde_request(request, superadmin, "tenant.suspend", "tenant", resource_id=tenant_id, tenant_id=tenant_id, changes={"motivo": motivo})
    return TenantResponse.model_validate(tenant)


@router.post(
    "/{tenant_id}/reactivar",
    response_model=TenantResponse,
    summary="Reactivar tenant",
    dependencies=[Depends(get_superadmin)]
)
async def reactivar_tenant(
    request: Request,
    tenant_id: UUID,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant no encontrado"
            )

        audit.registrar_desde_request(request, superadmin, "tenant.reactivate", "tenant", resource_id=tenant_id, tenant_id=tenant_id)
        return TenantResponse.model_validate(tenant)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{tenant_id}/cancelar",
    response_model=TenantResponse,
    summary="Cancelar tenant",
    dependencies=[Depends(get_superadmin)]
)
async def cancelar_tenant(
    request: Request,
    tenant_id: UUID,
    motivo: Optional[str] = Query(None, description="Motivo de la cancelación"),
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant no encontrado"
            )
        audit.registrar_desde_request(request, superadmin, "tenant.cancel", "tenant", resource_id=tenant_id, tenant_id=tenant_id, changes={"motivo": motivo})
        return TenantResponse.model_validate(tenant)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{tenant_id}/cambiar-plan",
    response_model=TenantResponse,
    summary="Cambiar plan del tenant",
    dependencies=[Depends(get_superadmin)]
)
async def cambiar_plan_tenant(
    request: Request,
    tenant_id: UUID,
    datos: TenantChangePlanRequest,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant no encontrado"
            )
        audit.registrar_desde_request(request, superadmin, "tenant.change_plan", "tenant", resource_id=tenant_id, tenant_id=tenant_id, changes={"nuevo_plan_id": str(datos.plan_id)})
        return TenantResponse.model_validate(tenant)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{tenant_id}/extender-trial",
    response_model=TenantResponse,
    summary="Extender trial del tenant",
    dependencies=[Depends(get_superadmin)]
)
async def extender_trial(
    request: Request,
    tenant_id: UUID,
    datos: TenantExtendTrialRequest,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant no encontrado"
            )
        audit.registrar_desde_request(request, superadmin, "tenant.extend_trial", "tenant", resource_id=tenant_id, tenant_id=tenant_id, changes={"dias_adicionales": datos.dias_adicionales})
        return TenantResponse.model_validate(tenant)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{tenant_id}/metricas",
    response_model=TenantMetricas,
    summary="Métricas de uso del tenant",
    dependencies=[Depends(get_superadmin)]
)
async def metricas_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Métricas de uso de un tenant: usuarios, productos, facturas, ventas.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    metricas = servicio.obtener_metricas_tenant(tenant_id)
    if not metricas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    return TenantMetricas(**metricas)


@router.get(
    "/{tenant_id}/suscripciones",
    response_model=List[SuscripcionResponse],
    summary="Historial de suscripciones",
    dependencies=[Depends(get_superadmin)]
)
async def suscripciones_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Historial de suscripciones de un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    tenant = servicio.obtener_tenant_por_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    suscripciones = servicio.obtener_suscripciones_tenant(tenant_id)
    return [SuscripcionResponse.model_validate(s) for s in suscripciones]


@router.get(
    "/{tenant_id}/pagos",
    response_model=List[PagoHistorialResponse],
    summary="Historial de pagos",
    dependencies=[Depends(get_superadmin)]
)
async def pagos_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Historial de pagos de un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    tenant = servicio.obtener_tenant_por_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    pagos = servicio.obtener_pagos_tenant(tenant_id)
    return [PagoHistorialResponse.model_validate(p) for p in pagos]


# ============================================================================
# USUARIOS DEL TENANT
# ============================================================================

@router.get(
    "/{tenant_id}/usuarios",
    response_model=List[UsuarioTenantDetailResponse],
    summary="Listar usuarios del tenant (con detalle)",
    dependencies=[Depends(get_superadmin)]
)
async def listar_usuarios_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Lista los usuarios de un tenant con nombre y email.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)

    tenant = servicio.obtener_tenant_por_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )

    usuarios = servicio.obtener_usuarios_tenant_con_detalle(tenant_id)
    return [UsuarioTenantDetailResponse(**u) for u in usuarios]


@router.put(
    "/{tenant_id}/usuarios/{usuario_id}/rol",
    response_model=UsuarioTenantResponse,
    summary="Cambiar rol de usuario en tenant",
    dependencies=[Depends(get_superadmin)]
)
async def cambiar_rol_usuario_tenant(
    request: Request,
    tenant_id: UUID,
    usuario_id: UUID,
    rol: str = Query(..., description="Nuevo rol (admin, operador, contador, vendedor, readonly)"),
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado en el tenant"
            )
        audit.registrar_desde_request(request, superadmin, "user.role_change", "user", resource_id=usuario_id, tenant_id=tenant_id, changes={"nuevo_rol": rol})
        return UsuarioTenantResponse.model_validate(ut)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{tenant_id}/usuarios/{usuario_id}",
    response_model=UsuarioTenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar usuario al tenant",
    dependencies=[Depends(get_superadmin)]
)
async def agregar_usuario_tenant(
    request: Request,
    tenant_id: UUID,
    usuario_id: UUID,
    rol: str = Query("operador", description="Rol del usuario en el tenant (admin, operador, contador, vendedor, readonly)"),
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
):
    """
    Agrega un usuario existente a un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)

    try:
        usuario_tenant = servicio.agregar_usuario_a_tenant(
            usuario_id=usuario_id,
            tenant_id=tenant_id,
            rol=rol
        )
        audit.registrar_desde_request(request, superadmin, "user.add_to_tenant", "user", resource_id=usuario_id, tenant_id=tenant_id, changes={"rol": rol})
        return UsuarioTenantResponse.model_validate(usuario_tenant)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{tenant_id}/usuarios/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover usuario del tenant",
    dependencies=[Depends(get_superadmin)]
)
async def remover_usuario_tenant(
    request: Request,
    tenant_id: UUID,
    usuario_id: UUID,
    superadmin: Usuarios = Depends(get_superadmin),
    db: Session = Depends(get_db)
):
    """
    Remueve un usuario de un tenant.
    **Requiere ser SuperAdmin.**
    """
    servicio = ServicioTenants(db)
    audit = ServicioAuditLog(db)
    eliminado = servicio.remover_usuario_de_tenant(usuario_id, tenant_id)

    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en el tenant"
        )

    audit.registrar_desde_request(request, superadmin, "user.remove_from_tenant", "user", resource_id=usuario_id, tenant_id=tenant_id)


# ============================================================================
# AUDIT LOGS POR TENANT (Superadmin)
# ============================================================================

@router.get(
    "/{tenant_id}/audit-logs/",
    response_model=AuditLogListResponse,
    summary="Audit logs de un tenant",
    dependencies=[Depends(get_superadmin)]
)
async def listar_audit_logs_tenant(
    tenant_id: UUID,
    action: Optional[str] = Query(None, description="Filtrar por acción"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
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
