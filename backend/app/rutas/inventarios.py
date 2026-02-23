import base64
import json
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import MovimientoInventarioResponse
from ..datos.modelos import Inventarios, Productos, TipoMovimiento, Usuarios
from ..servicios.servicio_inventario import ServicioInventario
from ..utils.logger import setup_logger
from ..utils.seguridad import get_current_user, get_tenant_id_from_token

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
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Lista inventario del tenant."""
    items = db.query(Inventarios).filter(Inventarios.tenant_id == tenant_id).offset(skip).limit(limit).all()
    return items


@router.get("/valorizado")
async def inventario_valorizado(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Obtiene inventario valorizado por producto."""
    servicio = ServicioInventario(db, tenant_id)
    return servicio.obtener_inventario_valorizado()


@router.get("/alertas")
async def alertas_stock(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Obtiene alertas de stock bajo."""
    servicio = ServicioInventario(db, tenant_id)
    return servicio.obtener_alertas_stock_bajo()


@router.get("/producto/{producto_id}")
async def por_producto(
    producto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Obtiene inventario de un producto específico."""
    inv = (
        db.query(Inventarios).filter(Inventarios.producto_id == producto_id, Inventarios.tenant_id == tenant_id).first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="No encontrado")
    return inv


@router.get("/movimientos")
async def listar_movimientos(
    producto_id: Optional[UUID] = Query(None),
    limite: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Lista movimientos de inventario."""
    servicio = ServicioInventario(db, tenant_id)
    movimientos = servicio.listar_movimientos(producto_id=producto_id, limite=limite)
    return [MovimientoInventarioResponse.model_validate(m) for m in movimientos]


@router.get("/paginado")
async def listar_inventario_cursor(
    cursor: Optional[str] = Query(None, description="Cursor opaco de paginación (base64)"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """
    Lista inventario valorizado con paginación por cursor.
    Retorna: { items: [...], next_cursor: str | null, has_more: bool }
    """
    servicio = ServicioInventario(db, tenant_id)
    all_items = servicio.obtener_inventario_valorizado()

    # Aplicar cursor: buscar posición por nombre del producto
    start_idx = 0
    if cursor:
        try:
            raw = base64.urlsafe_b64decode(cursor.encode()).decode()
            pos = json.loads(raw)
            cursor_nombre = pos.get("nombre", "")
            cursor_producto_id = pos.get("producto_id", "")
            for i, item in enumerate(all_items):
                if item["nombre"] > cursor_nombre or (
                    item["nombre"] == cursor_nombre and str(item["producto_id"]) > cursor_producto_id
                ):
                    start_idx = i
                    break
            else:
                start_idx = len(all_items)
        except Exception:
            raise HTTPException(status_code=400, detail="Cursor inválido")

    page_items = all_items[start_idx : start_idx + limit + 1]
    has_more = len(page_items) > limit
    page_items = page_items[:limit]

    next_cursor = None
    if has_more and page_items:
        last = page_items[-1]
        pos = {"nombre": last["nombre"], "producto_id": str(last["producto_id"])}
        next_cursor = base64.urlsafe_b64encode(json.dumps(pos).encode()).decode()

    return {
        "items": page_items,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get("/jerarquia")
async def inventario_jerarquico(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """
    Vista jerárquica del inventario: total → por producto → movimientos recientes.

    Estructura de respuesta:
    {
      "total_productos": int,
      "valor_total": float,
      "productos": [
        {
          "producto_id": str,
          "nombre": str,
          "codigo": str,
          "cantidad": float,
          "costo_promedio": float,
          "valor_total": float,
          "stock_minimo": float | null,
          "alerta": bool,
          "ultimos_movimientos": [{ tipo, cantidad, fecha, referencia }]
        }
      ]
    }
    """
    servicio = ServicioInventario(db, tenant_id)
    valorizado = servicio.obtener_inventario_valorizado()

    # Obtener alertas para marcar productos
    alertas = servicio.obtener_alertas_stock_bajo()
    alerta_ids = {str(a["producto_id"]) for a in alertas}

    # Obtener últimos movimientos agrupados por producto (top 5 por producto)
    movimientos = servicio.listar_movimientos(limite=200)
    movs_by_producto: dict = {}
    for m in movimientos:
        pid = str(m.producto_id)
        if pid not in movs_by_producto:
            movs_by_producto[pid] = []
        if len(movs_by_producto[pid]) < 5:
            movs_by_producto[pid].append(
                {
                    "id": str(m.id),
                    "tipo": m.tipo_movimiento,
                    "cantidad": float(m.cantidad),
                    "fecha": m.fecha_movimiento.isoformat() if m.fecha_movimiento else None,
                    "referencia": m.documento_referencia,
                }
            )

    # Obtener info de productos para stock_minimo
    productos_info = (
        db.query(Productos.id, Productos.stock_minimo)
        .filter(Productos.tenant_id == tenant_id, Productos.maneja_inventario)
        .all()
    )
    stock_minimo_map = {str(p.id): p.stock_minimo for p in productos_info}

    productos_jerarquia = []
    for item in valorizado:
        pid = str(item["producto_id"])
        productos_jerarquia.append(
            {
                "producto_id": pid,
                "nombre": item["nombre"],
                "codigo": item["codigo"],
                "cantidad": item["cantidad"],
                "costo_promedio": item["costo_promedio"],
                "valor_total": item["valor_total"],
                "stock_minimo": stock_minimo_map.get(pid),
                "alerta": pid in alerta_ids,
                "ultimos_movimientos": movs_by_producto.get(pid, []),
            }
        )

    valor_total = sum(p["valor_total"] for p in productos_jerarquia)

    return {
        "total_productos": len(productos_jerarquia),
        "valor_total": valor_total,
        "productos": productos_jerarquia,
    }


@router.post("/ajuste", status_code=status.HTTP_201_CREATED)
async def ajustar_inventario(
    ajuste: AjusteInventarioRequest,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Ajusta el inventario de un producto a una cantidad específica."""
    if current_user.rol not in ["admin", "operador"]:
        raise HTTPException(status_code=403, detail="Sin permisos para ajustar inventario")

    producto = db.query(Productos).filter(Productos.id == ajuste.producto_id, Productos.tenant_id == tenant_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    try:
        servicio = ServicioInventario(db, tenant_id)
        movimiento = servicio.ajustar_inventario(
            producto_id=ajuste.producto_id,
            cantidad_nueva=ajuste.cantidad_nueva,
            motivo=ajuste.motivo,
            usuario_id=current_user.id,
        )
        return MovimientoInventarioResponse.model_validate(movimiento)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/entrada", status_code=status.HTTP_201_CREATED)
async def entrada_inventario(
    entrada: EntradaInventarioRequest,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Registra una entrada de mercancía al inventario."""
    if current_user.rol not in ["admin", "operador"]:
        raise HTTPException(status_code=403, detail="Sin permisos para registrar entrada")

    producto = db.query(Productos).filter(Productos.id == entrada.producto_id, Productos.tenant_id == tenant_id).first()
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
            observaciones=entrada.observaciones,
        )
        db.commit()
        return MovimientoInventarioResponse.model_validate(movimiento)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
