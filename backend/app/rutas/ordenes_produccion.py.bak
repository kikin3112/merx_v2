from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import OrdenesProduccion, Usuarios
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..utils.secuencia_helper import generar_numero_secuencia
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/")
async def listar(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Lista órdenes de producción del tenant."""
    return db.query(OrdenesProduccion).filter(
        OrdenesProduccion.tenant_id == tenant_id
    ).order_by(OrdenesProduccion.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear(
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Crea una orden de producción."""
    numero = generar_numero_secuencia(db, 'ORDENES_PRODUCCION', tenant_id)
    orden = OrdenesProduccion(
        tenant_id=tenant_id,
        numero_orden=numero,
        estado="PENDIENTE"
    )
    db.add(orden)
    db.commit()
    db.refresh(orden)
    logger.info(f"Orden producción creada: {orden.numero_orden}")
    return orden


@router.get("/{orden_id}")
async def obtener(
        orden_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene una orden de producción por ID."""
    orden = db.query(OrdenesProduccion).filter(
        OrdenesProduccion.id == orden_id,
        OrdenesProduccion.tenant_id == tenant_id
    ).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de producción no encontrada")
    return orden
