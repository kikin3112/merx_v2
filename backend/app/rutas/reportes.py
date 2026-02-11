from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import Ventas, Productos, Inventarios, Usuarios
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/dashboard")
async def dashboard_kpis(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """KPIs principales del dashboard."""
    ventas = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado.in_(["CONFIRMADA", "FACTURADA"])
    ).all()

    total_ventas = sum(v.total_venta for v in ventas)
    cantidad_ventas = len(ventas)

    # Stock bajo
    from sqlalchemy import and_
    alertas_stock = db.query(Inventarios).join(
        Productos, Productos.id == Inventarios.producto_id
    ).filter(
        Inventarios.tenant_id == tenant_id,
        Productos.stock_minimo.isnot(None),
        Inventarios.cantidad_disponible <= Productos.stock_minimo
    ).count()

    return {
        "total_ventas": float(total_ventas),
        "cantidad_ventas": cantidad_ventas,
        "promedio_venta": float(total_ventas / cantidad_ventas) if cantidad_ventas > 0 else 0,
        "alertas_stock_bajo": alertas_stock
    }


@router.get("/ventas")
async def reporte_ventas(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Reporte de ventas por periodo."""
    query = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado != "ANULADA"
    )
    if fecha_inicio:
        query = query.filter(Ventas.fecha_venta >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Ventas.fecha_venta <= fecha_fin)

    ventas = query.order_by(Ventas.fecha_venta.desc()).all()

    total = sum(v.total_venta for v in ventas)
    return {
        "total_ventas": float(total),
        "cantidad": len(ventas),
        "promedio": float(total / len(ventas)) if ventas else 0
    }


@router.get("/productos-top")
async def productos_top(
    limite: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Top productos por valor de inventario."""
    inventarios = db.query(
        Productos.nombre,
        Productos.codigo_interno,
        Inventarios.cantidad_disponible,
        Inventarios.valor_total
    ).join(
        Inventarios, Productos.id == Inventarios.producto_id
    ).filter(
        Productos.tenant_id == tenant_id,
        Productos.deleted_at.is_(None),
        Inventarios.cantidad_disponible > 0
    ).order_by(Inventarios.valor_total.desc()).limit(limite).all()

    return [
        {
            "nombre": row.nombre,
            "codigo": row.codigo_interno,
            "stock": float(row.cantidad_disponible),
            "valor_total": float(row.valor_total)
        }
        for row in inventarios
    ]
