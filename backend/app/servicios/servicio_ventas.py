"""
Servicio de Ventas - Lógica de negocio para gestión de ventas.
Usa @hybrid_property de modelos para cálculos automáticos.
"""

from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from ..datos.esquemas import VentasCreate, VentasUpdate
from ..datos.modelos import Productos, Terceros, TipoMovimiento, Ventas, VentasDetalle
from ..servicios.servicio_inventario import ServicioInventario
from ..utils.logger import setup_logger
from ..utils.secuencia_helper import generar_numero_secuencia

logger = setup_logger(__name__)


def crear_venta(db: Session, venta_data: VentasCreate, tenant_id: UUID) -> Ventas:
    """
    Crea una nueva venta con sus detalles.

    Args:
        db: Sesión de base de datos
        venta_data: Datos de la venta a crear
        tenant_id: UUID del tenant

    Returns:
        Venta creada con todos los campos calculados
    """
    # Validar tercero
    tercero = db.query(Terceros).filter(Terceros.id == venta_data.tercero_id, Terceros.tenant_id == tenant_id).first()
    if not tercero:
        raise ValueError("El tercero especificado no existe")

    if tercero.tipo_tercero not in ("CLIENTE", "AMBOS"):
        raise ValueError("El tercero no está marcado como cliente")

    # Generar número de venta
    numero_venta = generar_numero_secuencia(db, "FACTURAS", tenant_id)

    # Crear venta
    nueva_venta = Ventas(
        tenant_id=tenant_id,
        numero_venta=numero_venta,
        tercero_id=venta_data.tercero_id,
        fecha_venta=venta_data.fecha_venta,
        estado="PENDIENTE",
        descuento_global=getattr(venta_data, "descuento_global", Decimal("0.00")) or Decimal("0.00"),
        observaciones=venta_data.observaciones,
    )
    db.add(nueva_venta)
    db.flush()

    # Crear detalles
    for detalle_data in venta_data.detalles:
        producto = (
            db.query(Productos)
            .filter(Productos.id == detalle_data.producto_id, Productos.tenant_id == tenant_id)
            .first()
        )
        if not producto:
            raise ValueError(f"Producto {detalle_data.producto_id} no existe")

        if not producto.estado:
            raise ValueError(f"Producto {producto.nombre} está inactivo")

        precio_unitario = detalle_data.precio_unitario
        if precio_unitario == Decimal("0.00"):
            precio_unitario = producto.precio_venta

        porcentaje_iva = detalle_data.porcentaje_iva
        if porcentaje_iva == Decimal("0.00"):
            porcentaje_iva = producto.porcentaje_iva

        detalle = VentasDetalle(
            tenant_id=tenant_id,
            venta_id=nueva_venta.id,
            producto_id=detalle_data.producto_id,
            cantidad=detalle_data.cantidad,
            precio_unitario=precio_unitario,
            descuento=detalle_data.descuento,
            porcentaje_iva=porcentaje_iva,
        )
        db.add(detalle)

    db.flush()

    logger.info(
        f"Venta {numero_venta} creada - "
        f"Tercero: {tercero.nombre}, "
        f"Items: {len(venta_data.detalles)}, "
        f"Total: ${nueva_venta.total_venta}"
    )

    return nueva_venta


def listar_ventas(
    db: Session, tenant_id: UUID, skip: int = 0, limit: int = 100, tercero_id: UUID = None, estado: str = None
) -> List[Ventas]:
    """Lista ventas con filtros opcionales."""
    query = (
        db.query(Ventas)
        .options(
            selectinload(Ventas.created_by_user),
            selectinload(Ventas.updated_by_user),
            selectinload(Ventas.tercero),
            selectinload(Ventas.envios),
        )
        .filter(Ventas.tenant_id == tenant_id)
    )

    if tercero_id:
        query = query.filter(Ventas.tercero_id == tercero_id)

    if estado:
        query = query.filter(Ventas.estado == estado)

    return query.order_by(Ventas.fecha_venta.desc()).offset(skip).limit(limit).all()


def obtener_venta(db: Session, venta_id: UUID, tenant_id: UUID) -> Ventas:
    """Obtiene una venta por ID."""
    venta = (
        db.query(Ventas)
        .options(
            selectinload(Ventas.created_by_user),
            selectinload(Ventas.updated_by_user),
            selectinload(Ventas.detalles),
            selectinload(Ventas.tercero),
            selectinload(Ventas.envios),
        )
        .filter(Ventas.id == venta_id, Ventas.tenant_id == tenant_id)
        .first()
    )

    if not venta:
        raise HTTPException(status_code=404, detail=f"Venta con ID {venta_id} no encontrada")

    return venta


def actualizar_venta(db: Session, venta_id: UUID, venta_data: VentasUpdate, tenant_id: UUID) -> Ventas:
    """Actualiza una venta existente."""
    venta = obtener_venta(db, venta_id, tenant_id)

    if venta.estado == "ANULADA":
        raise ValueError("No se puede modificar una venta anulada")

    if venta_data.estado is not None:
        if venta_data.estado == "ANULADA" and venta.estado == "FACTURADA":
            raise ValueError("No se puede anular una venta facturada")
        venta.estado = venta_data.estado

    if venta_data.observaciones is not None:
        venta.observaciones = venta_data.observaciones

    logger.info(f"Venta {venta.numero_venta} actualizada - Estado: {venta.estado}")

    return venta


def anular_venta(db: Session, venta_id: UUID, tenant_id: UUID, motivo: str = None) -> Ventas:
    """Anula una venta (cambio de estado a ANULADA)."""
    venta = obtener_venta(db, venta_id, tenant_id)

    if venta.estado == "ANULADA":
        raise ValueError("La venta ya está anulada")

    if venta.estado == "FACTURADA":
        raise ValueError("No se puede anular una venta facturada")

    # Si la venta estaba confirmada, revertir inventario
    if venta.estado == "CONFIRMADA":
        servicio_inv = ServicioInventario(db, tenant_id)
        for detalle in venta.detalles:
            producto = db.query(Productos).filter(Productos.id == detalle.producto_id).first()
            if producto and producto.maneja_inventario:
                servicio_inv.crear_movimiento(
                    producto_id=detalle.producto_id,
                    tipo=TipoMovimiento.ENTRADA,
                    cantidad=detalle.cantidad,
                    costo_unitario=servicio_inv.obtener_costo_promedio(detalle.producto_id),
                    documento_referencia=f"ANULACION-{venta.numero_venta}",
                    observaciones=f"Reversión por anulación de venta {venta.numero_venta}",
                )

    venta.estado = "ANULADA"

    if motivo:
        observacion_anulacion = f"ANULADA: {motivo}"
        if venta.observaciones:
            venta.observaciones += f"\n{observacion_anulacion}"
        else:
            venta.observaciones = observacion_anulacion

    logger.warning(f"Venta {venta.numero_venta} ANULADA - Motivo: {motivo or 'No especificado'}")

    return venta


def confirmar_venta(db: Session, venta_id: UUID, tenant_id: UUID) -> Ventas:
    """
    Confirma una venta (PENDIENTE -> CONFIRMADA).
    Descuenta inventario de cada producto que maneja inventario.
    """
    venta = obtener_venta(db, venta_id, tenant_id)

    if venta.estado != "PENDIENTE":
        raise ValueError(f"Solo se pueden confirmar ventas en estado PENDIENTE. Estado actual: {venta.estado}")

    # Descontar inventario
    servicio_inv = ServicioInventario(db, tenant_id)
    for detalle in venta.detalles:
        producto = db.query(Productos).filter(Productos.id == detalle.producto_id).first()
        if producto and producto.maneja_inventario:
            servicio_inv.crear_movimiento(
                producto_id=detalle.producto_id,
                tipo=TipoMovimiento.SALIDA,
                cantidad=detalle.cantidad,
                documento_referencia=f"VENTA-{venta.numero_venta}",
                observaciones=f"Venta {venta.numero_venta}",
            )

    venta.estado = "CONFIRMADA"

    logger.info(f"Venta {venta.numero_venta} CONFIRMADA con descuento de inventario")

    return venta


def obtener_estadisticas_ventas(
    db: Session, tenant_id: UUID, fecha_inicio: datetime = None, fecha_fin: datetime = None
) -> dict:
    """Obtiene estadísticas de ventas en un rango de fechas."""
    query = db.query(Ventas).filter(Ventas.tenant_id == tenant_id, Ventas.estado != "ANULADA")

    if fecha_inicio:
        query = query.filter(Ventas.fecha_venta >= fecha_inicio)

    if fecha_fin:
        query = query.filter(Ventas.fecha_venta <= fecha_fin)

    ventas = query.all()

    total_ventas = len(ventas)
    total_monto = sum(venta.total_venta for venta in ventas)

    ventas_por_estado = {}
    for venta in ventas:
        estado = venta.estado
        if estado not in ventas_por_estado:
            ventas_por_estado[estado] = {"cantidad": 0, "monto": Decimal("0.00")}
        ventas_por_estado[estado]["cantidad"] += 1
        ventas_por_estado[estado]["monto"] += venta.total_venta

    return {
        "total_ventas": total_ventas,
        "total_monto": float(total_monto),
        "promedio_venta": float(total_monto / total_ventas) if total_ventas > 0 else 0,
        "por_estado": ventas_por_estado,
    }
