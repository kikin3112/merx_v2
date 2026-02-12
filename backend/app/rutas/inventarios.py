from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field

from ..datos.db import get_db
from ..datos.modelos import Inventarios, MovimientosInventario, Usuarios, Productos, TipoMovimiento
from ..datos.esquemas import MovimientoInventarioResponse
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..servicios.servicio_inventario import ServicioInventario
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


# ---- Request schemas ----

class AjusteInventarioRequest(BaseModel):
    producto_id: UUID
    cantidad_nueva: Decimal = Field(..., ge=0)
    motivo: str = Field(..., min_length=3, max_length=200)


class EntradaInventarioRequest(BaseModel):
    producto_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    costo_unitario: Decimal = Field(..., ge=0)
    documento_referencia: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None


# ---- Endpoints ----

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
    movimientos = servicio.listar_movimientos(producto_id=producto_id, limite=limite)
    return [MovimientoInventarioResponse.model_validate(m) for m in movimientos]


@router.post("/ajuste", status_code=status.HTTP_201_CREATED)
async def ajustar_inventario(
        ajuste: AjusteInventarioRequest,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Ajusta el inventario de un producto a una cantidad específica."""
    if current_user.rol not in ['admin', 'operador']:
        raise HTTPException(status_code=403, detail="Sin permisos para ajustar inventario")

    producto = db.query(Productos).filter(
        Productos.id == ajuste.producto_id,
        Productos.tenant_id == tenant_id
    ).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    try:
        servicio = ServicioInventario(db, tenant_id)
        movimiento = servicio.ajustar_inventario(
            producto_id=ajuste.producto_id,
            cantidad_nueva=ajuste.cantidad_nueva,
            motivo=ajuste.motivo,
            usuario_id=current_user.id
        )
        return MovimientoInventarioResponse.model_validate(movimiento)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/entrada", status_code=status.HTTP_201_CREATED)
async def entrada_inventario(
        entrada: EntradaInventarioRequest,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Registra una entrada de mercancía al inventario."""
    if current_user.rol not in ['admin', 'operador']:
        raise HTTPException(status_code=403, detail="Sin permisos para registrar entrada")

    producto = db.query(Productos).filter(
        Productos.id == entrada.producto_id,
        Productos.tenant_id == tenant_id
    ).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    try:
        servicio = ServicioInventario(db, tenant_id)
        movimiento = servicio.crear_movimiento(
            producto_id=entrada.producto_id,
            tipo=TipoMovimiento.ENTRADA,
            cantidad=entrada.cantidad,
            costo_unitario=entrada.costo_unitario,
            documento_referencia=entrada.documento_referencia,
            observaciones=entrada.observaciones
        )
        db.commit()
        return MovimientoInventarioResponse.model_validate(movimiento)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
