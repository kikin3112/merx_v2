"""
Servicio de Ventas - Lógica de negocio para gestión de ventas.
Usa @hybrid_property de modelos para cálculos automáticos.
"""

from decimal import Decimal
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException

from ..datos.modelos import Ventas, VentasDetalle, Terceros, Productos
from ..datos.esquemas import VentasCreate, VentasUpdate
from ..utils.secuencia_helper import generar_numero_secuencia
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


def crear_venta(db: Session, venta_data: VentasCreate) -> Ventas:
    """
    Crea una nueva venta con sus detalles.
    Los totales se calculan automáticamente via @hybrid_property.

    Args:
        db: Sesión de base de datos
        venta_data: Datos de la venta a crear

    Returns:
        Venta creada con todos los campos calculados

    Raises:
        ValueError: Si el tercero no existe o no es cliente
        HTTPException: Si hay errores de inventario
    """
    # Validar tercero
    tercero = db.query(Terceros).filter(Terceros.id == venta_data.tercero_id).first()
    if not tercero:
        raise ValueError("El tercero especificado no existe")

    if tercero.tipo_tercero not in ('CLIENTE', 'AMBOS'):
        raise ValueError("El tercero no está marcado como cliente")

    # Generar número de venta
    numero_venta = generar_numero_secuencia(db, 'VENTAS')

    # Crear venta (sin totales, se calculan automáticamente)
    nueva_venta = Ventas(
        numero_venta=numero_venta,
        tercero_id=venta_data.tercero_id,
        fecha_venta=venta_data.fecha_venta,
        estado="PENDIENTE",
        observaciones=venta_data.observaciones
    )
    db.add(nueva_venta)
    db.flush()  # Genera el ID para usarlo en detalles

    # Crear detalles
    for detalle_data in venta_data.detalles:
        # Validar producto
        producto = db.query(Productos).filter(Productos.id == detalle_data.producto_id).first()
        if not producto:
            raise ValueError(f"Producto {detalle_data.producto_id} no existe")

        if not producto.estado:
            raise ValueError(f"Producto {producto.nombre} está inactivo")

        # Usar precio_venta del producto si no se especifica precio_unitario
        precio_unitario = detalle_data.precio_unitario
        if precio_unitario == Decimal("0.00"):
            precio_unitario = producto.precio_venta

        # Usar porcentaje_iva del producto si no se especifica
        porcentaje_iva = detalle_data.porcentaje_iva
        if porcentaje_iva == Decimal("0.00"):
            porcentaje_iva = producto.porcentaje_iva

        # Crear detalle (campos calculados se generan automáticamente via @hybrid_property)
        detalle = VentasDetalle(
            venta_id=nueva_venta.id,
            producto_id=detalle_data.producto_id,
            cantidad=detalle_data.cantidad,
            precio_unitario=precio_unitario,
            descuento=detalle_data.descuento,
            porcentaje_iva=porcentaje_iva
        )
        db.add(detalle)

    db.flush()  # Asegura que los detalles estén en la sesión

    # Los totales de la venta se calculan automáticamente via @hybrid_property
    # Al hacer db.refresh() o al acceder a nueva_venta.total_venta, se calculan dinámicamente

    logger.info(
        f"Venta {numero_venta} creada - "
        f"Tercero: {tercero.nombre}, "
        f"Items: {len(venta_data.detalles)}, "
        f"Total: ${nueva_venta.total_venta}"
    )

    return nueva_venta


def listar_ventas(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        tercero_id: UUID = None,
        estado: str = None
) -> List[Ventas]:
    """
    Lista ventas con filtros opcionales.

    Args:
        db: Sesión de base de datos
        skip: Número de registros a saltar (paginación)
        limit: Máximo de registros a retornar
        tercero_id: Filtrar por tercero (opcional)
        estado: Filtrar por estado (opcional)

    Returns:
        Lista de ventas que cumplen los criterios
    """
    query = db.query(Ventas)

    if tercero_id:
        query = query.filter(Ventas.tercero_id == tercero_id)

    if estado:
        query = query.filter(Ventas.estado == estado)

    return (
        query
        .order_by(Ventas.fecha_venta.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def obtener_venta(db: Session, venta_id: UUID) -> Ventas:
    """
    Obtiene una venta por ID con sus detalles.

    Args:
        db: Sesión de base de datos
        venta_id: UUID de la venta

    Returns:
        Venta con detalles cargados

    Raises:
        HTTPException: Si la venta no existe
    """
    venta = db.query(Ventas).filter(Ventas.id == venta_id).first()

    if not venta:
        raise HTTPException(
            status_code=404,
            detail=f"Venta con ID {venta_id} no encontrada"
        )

    return venta


def actualizar_venta(
        db: Session,
        venta_id: UUID,
        venta_data: VentasUpdate
) -> Ventas:
    """
    Actualiza una venta existente.
    Solo permite actualizar estado y observaciones (no detalles).

    Args:
        db: Sesión de base de datos
        venta_id: UUID de la venta
        venta_data: Datos a actualizar

    Returns:
        Venta actualizada

    Raises:
        HTTPException: Si la venta no existe
        ValueError: Si se intenta modificar una venta anulada
    """
    venta = obtener_venta(db, venta_id)

    if venta.estado == "ANULADA":
        raise ValueError("No se puede modificar una venta anulada")

    # Actualizar solo campos permitidos
    if venta_data.estado is not None:
        # Validar transición de estado
        if venta_data.estado == "ANULADA" and venta.estado == "FACTURADA":
            raise ValueError("No se puede anular una venta facturada")
        venta.estado = venta_data.estado

    if venta_data.observaciones is not None:
        venta.observaciones = venta_data.observaciones

    logger.info(f"Venta {venta.numero_venta} actualizada - Estado: {venta.estado}")

    return venta


def anular_venta(db: Session, venta_id: UUID, motivo: str = None) -> Ventas:
    """
    Anula una venta (cambio de estado a ANULADA).

    Args:
        db: Sesión de base de datos
        venta_id: UUID de la venta
        motivo: Motivo de la anulación (opcional)

    Returns:
        Venta anulada

    Raises:
        ValueError: Si la venta ya está anulada o facturada
    """
    venta = obtener_venta(db, venta_id)

    if venta.estado == "ANULADA":
        raise ValueError("La venta ya está anulada")

    if venta.estado == "FACTURADA":
        raise ValueError("No se puede anular una venta facturada")

    venta.estado = "ANULADA"

    if motivo:
        observacion_anulacion = f"ANULADA: {motivo}"
        if venta.observaciones:
            venta.observaciones += f"\n{observacion_anulacion}"
        else:
            venta.observaciones = observacion_anulacion

    logger.warning(f"Venta {venta.numero_venta} ANULADA - Motivo: {motivo or 'No especificado'}")

    return venta


def confirmar_venta(db: Session, venta_id: UUID) -> Ventas:
    """
    Confirma una venta (cambia estado de PENDIENTE a CONFIRMADA).

    Args:
        db: Sesión de base de datos
        venta_id: UUID de la venta

    Returns:
        Venta confirmada

    Raises:
        ValueError: Si la venta no está en estado PENDIENTE
    """
    venta = obtener_venta(db, venta_id)

    if venta.estado != "PENDIENTE":
        raise ValueError(f"Solo se pueden confirmar ventas en estado PENDIENTE. Estado actual: {venta.estado}")

    venta.estado = "CONFIRMADA"

    logger.info(f"Venta {venta.numero_venta} CONFIRMADA")

    return venta


def obtener_estadisticas_ventas(
        db: Session,
        fecha_inicio: datetime = None,
        fecha_fin: datetime = None
) -> dict:
    """
    Obtiene estadísticas de ventas en un rango de fechas.

    Args:
        db: Sesión de base de datos
        fecha_inicio: Fecha inicial (opcional)
        fecha_fin: Fecha final (opcional)

    Returns:
        Diccionario con estadísticas
    """
    query = db.query(Ventas).filter(Ventas.estado != "ANULADA")

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
            ventas_por_estado[estado] = {'cantidad': 0, 'monto': Decimal("0.00")}
        ventas_por_estado[estado]['cantidad'] += 1
        ventas_por_estado[estado]['monto'] += venta.total_venta

    return {
        'total_ventas': total_ventas,
        'total_monto': float(total_monto),
        'promedio_venta': float(total_monto / total_ventas) if total_ventas > 0 else 0,
        'por_estado': ventas_por_estado
    }