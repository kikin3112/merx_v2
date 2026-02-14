"""
Rutas CRM: Gestión de pipelines, deals y activities.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional, Dict, Any

from ..datos.db import get_db
from ..datos.esquemas import (
    CrmPipelineCreate, CrmPipelineUpdate, CrmPipelineResponse,
    CrmStageResponse,
    CrmDealCreate, CrmDealUpdate, CrmDealResponse,
    CrmActivityCreate, CrmActivityResponse
)
from ..datos.modelos_crm import EstadoDeal
from ..servicios.servicio_crm import ServicioCRM
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..datos.modelos import Usuarios


router = APIRouter(prefix="/crm", tags=["CRM"])


# ============================================================================
# PIPELINES
# ============================================================================

@router.get("/pipelines/", response_model=List[CrmPipelineResponse])
def listar_pipelines(
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos los pipelines del tenant con sus etapas (stages).
    Ordenados por es_default DESC, nombre ASC.
    """
    servicio = ServicioCRM(db)
    pipelines = servicio.listar_pipelines(tenant_id)

    # Convertir a response schema
    return [
        CrmPipelineResponse(
            id=p.id,
            nombre=p.nombre,
            descripcion=p.descripcion,
            es_default=p.es_default,
            color=p.color,
            tenant_id=p.tenant_id,
            created_at=p.created_at,
            etapas=[
                CrmStageResponse(
                    id=s.id,
                    pipeline_id=s.pipeline_id,
                    nombre=s.nombre,
                    orden=s.orden,
                    probabilidad=s.probabilidad
                )
                for s in p.etapas
            ]
        )
        for p in pipelines
    ]


@router.post("/pipelines/", response_model=CrmPipelineResponse, status_code=status.HTTP_201_CREATED)
def crear_pipeline(
    data: CrmPipelineCreate,
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo pipeline. Si es_default=True, quita el default de otros.
    """
    servicio = ServicioCRM(db)
    pipeline = servicio.crear_pipeline(tenant_id, data)

    return CrmPipelineResponse(
        id=pipeline.id,
        nombre=pipeline.nombre,
        descripcion=pipeline.descripcion,
        es_default=pipeline.es_default,
        color=pipeline.color,
        tenant_id=pipeline.tenant_id,
        created_at=pipeline.created_at,
        etapas=[]
    )


@router.patch("/pipelines/{pipeline_id}", response_model=CrmPipelineResponse)
def actualizar_pipeline(
    pipeline_id: UUID,
    data: CrmPipelineUpdate,
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza datos de un pipeline (nombre, color, descripción).
    """
    servicio = ServicioCRM(db)
    pipeline = servicio.actualizar_pipeline(pipeline_id, tenant_id, data)

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline no encontrado"
        )

    return CrmPipelineResponse(
        id=pipeline.id,
        nombre=pipeline.nombre,
        descripcion=pipeline.descripcion,
        es_default=pipeline.es_default,
        color=pipeline.color,
        tenant_id=pipeline.tenant_id,
        created_at=pipeline.created_at,
        etapas=[
            CrmStageResponse(
                id=s.id,
                pipeline_id=s.pipeline_id,
                nombre=s.nombre,
                orden=s.orden,
                probabilidad=s.probabilidad
            )
            for s in pipeline.etapas
        ]
    )


@router.delete("/pipelines/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pipeline(
    pipeline_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete de pipeline. Valida que no tenga deals activos.
    Retorna 400 si hay deals activos.
    """
    servicio = ServicioCRM(db)

    try:
        success = servicio.eliminar_pipeline(pipeline_id, tenant_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline no encontrado"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return None


# ============================================================================
# DEALS
# ============================================================================

@router.get("/deals/", response_model=List[CrmDealResponse])
def listar_deals(
    pipeline_id: Optional[UUID] = Query(None, description="Filtrar por pipeline"),
    stage_id: Optional[UUID] = Query(None, description="Filtrar por stage"),
    usuario_id: Optional[UUID] = Query(None, description="Filtrar por usuario asignado"),
    estado_cierre: Optional[str] = Query(None, description="ABIERTO|GANADO|PERDIDO|ABANDONADO"),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista deals con filtros opcionales. Eager load: tercero, usuario, stage.
    Ordenados por created_at DESC.
    """
    servicio = ServicioCRM(db)

    # Construir filtros
    filters: Dict[str, Any] = {}
    if pipeline_id:
        filters["pipeline_id"] = pipeline_id
    if stage_id:
        filters["stage_id"] = stage_id
    if usuario_id:
        filters["usuario_id"] = usuario_id
    if estado_cierre:
        try:
            filters["estado_cierre"] = EstadoDeal(estado_cierre)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"estado_cierre inválido: {estado_cierre}"
            )

    deals = servicio.listar_deals(tenant_id, filters)

    return [
        CrmDealResponse(
            id=d.id,
            nombre=d.nombre,
            tercero_id=d.tercero_id,
            tercero_nombre=d.tercero.nombre if d.tercero else None,
            stage_id=d.stage_id,
            stage_nombre=d.stage.nombre if d.stage else None,
            pipeline_id=d.pipeline_id,
            usuario_id=d.usuario_id,
            usuario_nombre=f"{d.usuario.nombre} {d.usuario.apellido}" if d.usuario else None,
            valor_estimado=d.valor_estimado,
            moneda=d.moneda,
            fecha_cierre_estimada=d.fecha_cierre_estimada,
            origen=d.origen,
            estado_cierre=d.estado_cierre.value,
            motivo_perdida=d.motivo_perdida,
            fecha_ultimo_contacto=d.fecha_ultimo_contacto,
            created_at=d.created_at,
            updated_at=d.updated_at
        )
        for d in deals
    ]


@router.post("/deals/", response_model=CrmDealResponse, status_code=status.HTTP_201_CREATED)
def crear_deal(
    data: CrmDealCreate,
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo deal. Valida tercero y stage. Log activity automática.
    """
    servicio = ServicioCRM(db)

    try:
        deal = servicio.crear_deal(tenant_id, data, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return CrmDealResponse(
        id=deal.id,
        nombre=deal.nombre,
        tercero_id=deal.tercero_id,
        tercero_nombre=deal.tercero.nombre if deal.tercero else None,
        stage_id=deal.stage_id,
        stage_nombre=deal.stage.nombre if deal.stage else None,
        pipeline_id=deal.pipeline_id,
        usuario_id=deal.usuario_id,
        usuario_nombre=f"{deal.usuario.nombre} {deal.usuario.apellido}" if deal.usuario else None,
        valor_estimado=deal.valor_estimado,
        moneda=deal.moneda,
        fecha_cierre_estimada=deal.fecha_cierre_estimada,
        origen=deal.origen,
        estado_cierre=deal.estado_cierre.value,
        motivo_perdida=deal.motivo_perdida,
        fecha_ultimo_contacto=deal.fecha_ultimo_contacto,
        created_at=deal.created_at,
        updated_at=deal.updated_at
    )


@router.get("/deals/{deal_id}", response_model=CrmDealResponse)
def obtener_deal(
    deal_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene detalle de un deal. Incluye tercero, usuario, stage, pipeline.
    """
    servicio = ServicioCRM(db)
    deal = servicio.obtener_deal(deal_id, tenant_id)

    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal no encontrado"
        )

    return CrmDealResponse(
        id=deal.id,
        nombre=deal.nombre,
        tercero_id=deal.tercero_id,
        tercero_nombre=deal.tercero.nombre if deal.tercero else None,
        stage_id=deal.stage_id,
        stage_nombre=deal.stage.nombre if deal.stage else None,
        pipeline_id=deal.pipeline_id,
        usuario_id=deal.usuario_id,
        usuario_nombre=f"{deal.usuario.nombre} {deal.usuario.apellido}" if deal.usuario else None,
        valor_estimado=deal.valor_estimado,
        moneda=deal.moneda,
        fecha_cierre_estimada=deal.fecha_cierre_estimada,
        origen=deal.origen,
        estado_cierre=deal.estado_cierre.value,
        motivo_perdida=deal.motivo_perdida,
        fecha_ultimo_contacto=deal.fecha_ultimo_contacto,
        created_at=deal.created_at,
        updated_at=deal.updated_at
    )


@router.put("/deals/{deal_id}", response_model=CrmDealResponse)
def actualizar_deal(
    deal_id: UUID,
    data: CrmDealUpdate,
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza datos de un deal (nombre, valor, fecha, usuario asignado).
    """
    servicio = ServicioCRM(db)
    deal = servicio.actualizar_deal(deal_id, tenant_id, data)

    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal no encontrado"
        )

    return CrmDealResponse(
        id=deal.id,
        nombre=deal.nombre,
        tercero_id=deal.tercero_id,
        tercero_nombre=deal.tercero.nombre if deal.tercero else None,
        stage_id=deal.stage_id,
        stage_nombre=deal.stage.nombre if deal.stage else None,
        pipeline_id=deal.pipeline_id,
        usuario_id=deal.usuario_id,
        usuario_nombre=f"{deal.usuario.nombre} {deal.usuario.apellido}" if deal.usuario else None,
        valor_estimado=deal.valor_estimado,
        moneda=deal.moneda,
        fecha_cierre_estimada=deal.fecha_cierre_estimada,
        origen=deal.origen,
        estado_cierre=deal.estado_cierre.value,
        motivo_perdida=deal.motivo_perdida,
        fecha_ultimo_contacto=deal.fecha_ultimo_contacto,
        created_at=deal.created_at,
        updated_at=deal.updated_at
    )


@router.patch("/deals/{deal_id}/stage", response_model=CrmDealResponse)
def mover_deal(
    deal_id: UUID,
    stage_id: UUID = Query(..., description="Nuevo stage_id"),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mueve deal a otro stage (drag & drop handler). Log activity automática.
    """
    servicio = ServicioCRM(db)

    try:
        deal = servicio.mover_deal(deal_id, stage_id, tenant_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return CrmDealResponse(
        id=deal.id,
        nombre=deal.nombre,
        tercero_id=deal.tercero_id,
        tercero_nombre=deal.tercero.nombre if deal.tercero else None,
        stage_id=deal.stage_id,
        stage_nombre=deal.stage.nombre if deal.stage else None,
        pipeline_id=deal.pipeline_id,
        usuario_id=deal.usuario_id,
        usuario_nombre=f"{deal.usuario.nombre} {deal.usuario.apellido}" if deal.usuario else None,
        valor_estimado=deal.valor_estimado,
        moneda=deal.moneda,
        fecha_cierre_estimada=deal.fecha_cierre_estimada,
        origen=deal.origen,
        estado_cierre=deal.estado_cierre.value,
        motivo_perdida=deal.motivo_perdida,
        fecha_ultimo_contacto=deal.fecha_ultimo_contacto,
        created_at=deal.created_at,
        updated_at=deal.updated_at
    )


@router.post("/deals/{deal_id}/cerrar", response_model=CrmDealResponse)
def cerrar_deal(
    deal_id: UUID,
    estado: str = Query(..., description="GANADO|PERDIDO|ABANDONADO"),
    motivo: Optional[str] = Query(None, description="Motivo del cierre"),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cierra un deal (GANADO/PERDIDO/ABANDONADO). Log activity.
    """
    servicio = ServicioCRM(db)

    # Validar estado
    try:
        estado_enum = EstadoDeal(estado)
        if estado_enum == EstadoDeal.ABIERTO:
            raise ValueError("No se puede cerrar un deal con estado ABIERTO")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido: {estado}"
        )

    try:
        deal = servicio.cerrar_deal(deal_id, estado_enum, motivo, tenant_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return CrmDealResponse(
        id=deal.id,
        nombre=deal.nombre,
        tercero_id=deal.tercero_id,
        tercero_nombre=deal.tercero.nombre if deal.tercero else None,
        stage_id=deal.stage_id,
        stage_nombre=deal.stage.nombre if deal.stage else None,
        pipeline_id=deal.pipeline_id,
        usuario_id=deal.usuario_id,
        usuario_nombre=f"{deal.usuario.nombre} {deal.usuario.apellido}" if deal.usuario else None,
        valor_estimado=deal.valor_estimado,
        moneda=deal.moneda,
        fecha_cierre_estimada=deal.fecha_cierre_estimada,
        origen=deal.origen,
        estado_cierre=deal.estado_cierre.value,
        motivo_perdida=deal.motivo_perdida,
        fecha_ultimo_contacto=deal.fecha_ultimo_contacto,
        created_at=deal.created_at,
        updated_at=deal.updated_at
    )


@router.delete("/deals/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_deal(
    deal_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete de deal.
    """
    servicio = ServicioCRM(db)
    success = servicio.eliminar_deal(deal_id, tenant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal no encontrado"
        )

    return None


# ============================================================================
# ACTIVITIES
# ============================================================================

@router.get("/deals/{deal_id}/activities/", response_model=List[CrmActivityResponse])
def listar_actividades(
    deal_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista activities de un deal. Order by fecha_actividad DESC.
    """
    servicio = ServicioCRM(db)
    activities = servicio.listar_actividades(deal_id, tenant_id)

    return [
        CrmActivityResponse(
            id=a.id,
            deal_id=a.deal_id,
            usuario_id=a.usuario_id,
            usuario_nombre=f"{a.usuario.nombre} {a.usuario.apellido}" if a.usuario else "Sistema",
            tipo=a.tipo.value,
            asunto=a.asunto,
            contenido=a.contenido,
            fecha_actividad=a.fecha_actividad,
            duracion_minutos=a.duracion_minutos,
            es_automatica=a.es_automatica,
            created_at=a.created_at
        )
        for a in activities
    ]


@router.post("/deals/{deal_id}/activities/", response_model=CrmActivityResponse, status_code=status.HTTP_201_CREATED)
def crear_actividad(
    deal_id: UUID,
    data: CrmActivityCreate,
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea una activity. Actualiza fecha_ultimo_contacto del deal.
    """
    servicio = ServicioCRM(db)

    # Validar que deal_id en path coincide con data
    if data.deal_id != deal_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="deal_id en path no coincide con body"
        )

    try:
        activity = servicio.crear_actividad(tenant_id, data, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return CrmActivityResponse(
        id=activity.id,
        deal_id=activity.deal_id,
        usuario_id=activity.usuario_id,
        usuario_nombre=f"{activity.usuario.nombre} {activity.usuario.apellido}" if activity.usuario else None,
        tipo=activity.tipo.value,
        asunto=activity.asunto,
        contenido=activity.contenido,
        fecha_actividad=activity.fecha_actividad,
        duracion_minutos=activity.duracion_minutos,
        es_automatica=activity.es_automatica,
        created_at=activity.created_at
    )


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_actividad(
    activity_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id_from_token),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete de activity.
    """
    servicio = ServicioCRM(db)
    success = servicio.eliminar_actividad(activity_id, tenant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity no encontrada"
        )

    return None
