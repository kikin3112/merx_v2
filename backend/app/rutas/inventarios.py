from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import Inventarios, MovimientosInventario, Usuarios
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..servicios.servicio_inventario import ServicioInventario
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
    """Lista inventario del tenant."""
    items = db.query(Inventarios).filter(
        Inventarios.tenant_id == tenant_id
    ).offset(skip).limit(limit).all()
    return items


@router.get("/valorizado")
async def inventario_valorizado(
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene inventario valorizado por producto."""
    servicio = ServicioInventario(db, tenant_id)
    return servicio.obtener_inventario_valorizado()


@router.get("/alertas")
async def alertas_stock(
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene alertas de stock bajo."""
    servicio = ServicioInventario(db, tenant_id)
    return servicio.obtener_alertas_stock_bajo()


@router.get("/producto/{producto_id}")
async def por_producto(
        producto_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene inventario de un producto específico."""
    inv = db.query(Inventarios).filter(
        Inventarios.producto_id == producto_id,
        Inventarios.tenant_id == tenant_id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="No encontrado")
    return inv


@router.get("/movimientos")
async def listar_movimientos(
        producto_id: Optional[UUID] = Query(None),
        limite: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Lista movimientos de inventario."""
    servicio = ServicioInventario(db, tenant_id)
    return servicio.listar_movimientos(producto_id=producto_id, limite=limite)
