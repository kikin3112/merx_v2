"""
Rutas de Calificaciones: rating 1-5 estrellas por tenant con moderación superadmin.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import (
    CalificacionCreate,
    CalificacionModerarRequest,
    CalificacionPublicaResponse,
    CalificacionResponse,
)
from ..datos.modelos import Usuarios
from ..datos.modelos_tenant import Tenants
from ..servicios.servicio_calificaciones import ServicioCalificaciones
from ..utils.logger import setup_logger
from ..utils.seguridad import get_current_user, get_tenant_id_from_token

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/", response_model=CalificacionResponse, status_code=status.HTTP_200_OK)
async def crear_o_actualizar_calificacion(
    datos: CalificacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Crea o actualiza la calificación del tenant autenticado."""
    # Obtener nombre de empresa para cachear
    tenant = db.query(Tenants).filter(Tenants.id == tenant_id).first()
    nombre_empresa = tenant.nombre if tenant else None

    servicio = ServicioCalificaciones(db)
    return servicio.crear_o_actualizar(
        tenant_id=tenant_id,
        usuario_id=current_user.id,
        datos=datos,
        nombre_empresa=nombre_empresa,
    )


@router.get("/mi-tenant", response_model=Optional[CalificacionResponse])
async def obtener_mi_calificacion(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Retorna la calificación actual del tenant autenticado, o null si no existe."""
    servicio = ServicioCalificaciones(db)
    return servicio.obtener_calificacion_tenant(tenant_id)


@router.get("/publicas", response_model=list[CalificacionPublicaResponse])
async def listar_calificaciones_publicas(
    limit: int = Query(default=6, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Endpoint público (sin autenticación). Retorna calificaciones aprobadas para landing."""
    servicio = ServicioCalificaciones(db)
    return servicio.listar_publicas(limit=limit)


@router.get("/admin", response_model=list[CalificacionResponse])
async def listar_calificaciones_admin(
    estado: Optional[str] = Query(None, description="pendiente|aprobada|rechazada"),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
):
    """Solo superadmin. Lista todas las calificaciones."""
    if not current_user.es_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo superadmin")
    servicio = ServicioCalificaciones(db)
    return servicio.listar_admin(estado=estado)


@router.patch("/{calificacion_id}/moderar", response_model=CalificacionResponse)
async def moderar_calificacion(
    calificacion_id: UUID,
    datos: CalificacionModerarRequest,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
):
    """Solo superadmin. Aprueba o rechaza una calificación."""
    if not current_user.es_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo superadmin")
    servicio = ServicioCalificaciones(db)
    return servicio.moderar(calificacion_id, datos.nuevo_estado)
