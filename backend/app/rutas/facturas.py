"""
Rutas de Facturación.
Las facturas son ventas formales (estado FACTURADA) con contabilidad automática.
Reutiliza el modelo Ventas con estados: borrador(PENDIENTE) -> emitida(FACTURADA) -> anulada(ANULADA).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import date

from ..datos.db import get_db
from ..datos.modelos import (
    Ventas, VentasDetalle, Terceros, Productos, Usuarios, TipoMovimiento
)
from ..datos.esquemas import VentasCreate, VentasResponse
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..utils.secuencia_helper import generar_numero_secuencia
from ..servicios.servicio_inventario import ServicioInventario
from ..servicios.servicio_contabilidad import ServicioContabilidad
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/")
async def listar_facturas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    estado: Optional[str] = Query(None),
    tercero_id: Optional[UUID] = Query(None),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Lista facturas del tenant.
    Las facturas son ventas con estado CONFIRMADA, FACTURADA o ANULADA.
    """
    query = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.deleted_at.is_(None)
    )

    if estado:
        query = query.filter(Ventas.estado == estado)

    if tercero_id:
        query = query.filter(Ventas.tercero_id == tercero_id)

    if fecha_inicio:
        query = query.filter(Ventas.fecha_venta >= fecha_inicio)

    if fecha_fin:
        query = query.filter(Ventas.fecha_venta <= fecha_fin)

    items = (
        query.order_by(Ventas.fecha_venta.desc(), Ventas.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return items


@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_factura(
    data: VentasCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Crea una nueva factura (venta en estado borrador/PENDIENTE).
    Usar POST /facturas/{id}/emitir para confirmar y descontar inventario.
    """
    from decimal import Decimal

    # Validar tercero
    tercero = db.query(Terceros).filter(
        Terceros.id == data.tercero_id,
        Terceros.tenant_id == tenant_id
    ).first()
    if not tercero:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")

    if tercero.tipo_tercero not in ('CLIENTE', 'AMBOS'):
        raise HTTPException(
            status_code=400,
            detail="El tercero no está registrado como cliente"
        )

    # Generar número de factura
    numero = generar_numero_secuencia(db, 'FACTURAS', tenant_id)

    factura = Ventas(
        tenant_id=tenant_id,
        numero_venta=numero,
        tercero_id=data.tercero_id,
        fecha_venta=data.fecha_venta,
        estado="PENDIENTE",
        observaciones=data.observaciones
    )
    db.add(factura)
    db.flush()

    for det in data.detalles:
        producto = db.query(Productos).filter(
            Productos.id == det.producto_id,
            Productos.tenant_id == tenant_id
        ).first()
        if not producto:
            raise HTTPException(
                status_code=404,
                detail=f"Producto {det.producto_id} no encontrado"
            )

        precio = det.precio_unitario if det.precio_unitario > 0 else producto.precio_venta
        iva = det.porcentaje_iva if det.porcentaje_iva > 0 else producto.porcentaje_iva

        detalle = VentasDetalle(
            tenant_id=tenant_id,
            venta_id=factura.id,
            producto_id=det.producto_id,
            cantidad=det.cantidad,
            precio_unitario=precio,
            descuento=det.descuento,
            porcentaje_iva=iva
        )
        db.add(detalle)

    db.commit()
    db.refresh(factura)
    logger.info(f"Factura {numero} creada (borrador)")
    return factura


@router.get("/{factura_id}")
async def obtener_factura(
    factura_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene una factura por ID con sus detalles."""
    factura = db.query(Ventas).filter(
        Ventas.id == factura_id,
        Ventas.tenant_id == tenant_id
    ).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura


@router.post("/{factura_id}/emitir")
async def emitir_factura(
    factura_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Emite una factura:
    1. Valida estado = PENDIENTE
    2. Descuenta inventario de cada producto
    3. Crea asiento contable automático
    4. Cambia estado a FACTURADA
    """
    factura = db.query(Ventas).filter(
        Ventas.id == factura_id,
        Ventas.tenant_id == tenant_id
    ).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if factura.estado != "PENDIENTE":
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden emitir facturas en estado PENDIENTE. Estado actual: {factura.estado}"
        )

    # Descontar inventario
    servicio_inv = ServicioInventario(db, tenant_id)
    for detalle in factura.detalles:
        producto = db.query(Productos).filter(
            Productos.id == detalle.producto_id
        ).first()
        if producto and producto.maneja_inventario:
            try:
                servicio_inv.crear_movimiento(
                    producto_id=detalle.producto_id,
                    tipo=TipoMovimiento.SALIDA,
                    cantidad=detalle.cantidad,
                    documento_referencia=f"FAC-{factura.numero_venta}",
                    observaciones=f"Factura {factura.numero_venta}"
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error de inventario para {producto.nombre}: {str(e)}"
                )

    # Crear asiento contable automático
    servicio_cont = ServicioContabilidad(db, tenant_id)
    servicio_cont.crear_asiento_venta(
        fecha=factura.fecha_venta,
        subtotal=factura.subtotal,
        total_iva=factura.total_iva,
        total=factura.total_venta,
        documento_referencia=factura.numero_venta
    )

    factura.estado = "FACTURADA"
    db.commit()
    db.refresh(factura)

    logger.info(f"Factura {factura.numero_venta} EMITIDA con inventario y contabilidad")

    return {
        "factura": factura,
        "message": f"Factura {factura.numero_venta} emitida exitosamente"
    }


@router.post("/{factura_id}/anular")
async def anular_factura(
    factura_id: UUID,
    motivo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Anula una factura:
    1. Revierte movimientos de inventario (si estaba emitida)
    2. Crea asiento contable de reversión
    3. Cambia estado a ANULADA
    """
    factura = db.query(Ventas).filter(
        Ventas.id == factura_id,
        Ventas.tenant_id == tenant_id
    ).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if factura.estado == "ANULADA":
        raise HTTPException(status_code=400, detail="La factura ya está anulada")

    # Si estaba facturada, revertir inventario y contabilidad
    if factura.estado == "FACTURADA":
        servicio_inv = ServicioInventario(db, tenant_id)
        for detalle in factura.detalles:
            producto = db.query(Productos).filter(
                Productos.id == detalle.producto_id
            ).first()
            if producto and producto.maneja_inventario:
                servicio_inv.crear_movimiento(
                    producto_id=detalle.producto_id,
                    tipo=TipoMovimiento.ENTRADA,
                    cantidad=detalle.cantidad,
                    costo_unitario=servicio_inv.obtener_costo_promedio(detalle.producto_id),
                    documento_referencia=f"ANUL-{factura.numero_venta}",
                    observaciones=f"Reversión por anulación factura {factura.numero_venta}"
                )

        # Asiento contable de reversión
        servicio_cont = ServicioContabilidad(db, tenant_id)
        servicio_cont.crear_asiento_anulacion_venta(
            fecha=factura.fecha_venta,
            subtotal=factura.subtotal,
            total_iva=factura.total_iva,
            total=factura.total_venta,
            documento_referencia=factura.numero_venta
        )

    factura.estado = "ANULADA"
    if motivo:
        obs = f"ANULADA: {motivo}"
        factura.observaciones = f"{factura.observaciones}\n{obs}" if factura.observaciones else obs

    db.commit()
    db.refresh(factura)

    logger.warning(f"Factura {factura.numero_venta} ANULADA - Motivo: {motivo or 'No especificado'}")

    return {
        "factura": factura,
        "message": f"Factura {factura.numero_venta} anulada"
    }
