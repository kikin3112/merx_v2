"""
Rutas de Facturación.
Las facturas son ventas formales (estado FACTURADA) con contabilidad automática.
Reutiliza el modelo Ventas con estados: borrador(PENDIENTE) -> emitida(FACTURADA) -> anulada(ANULADA).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
import io

from ..datos.db import get_db
from ..datos.modelos import (
    Ventas, VentasDetalle, Terceros, Productos, Usuarios, TipoMovimiento, Cartera
)
from ..datos.modelos_tenant import Tenants
from ..datos.esquemas import VentasCreate, VentasResponse
from ..utils.seguridad import get_current_user, get_tenant_id_from_token, require_tenant_roles, UserContext
from ..utils.secuencia_helper import generar_numero_secuencia
from ..servicios.servicio_inventario import ServicioInventario
from ..servicios.servicio_contabilidad import ServicioContabilidad
from ..servicios.servicio_pdf import ServicioPDF
from ..servicios.servicio_almacenamiento import ServicioAlmacenamiento
from ..utils.logger import setup_logger

from datetime import timedelta

router = APIRouter()
logger = setup_logger(__name__)


def _crear_cartera_cobrar(db: Session, factura: Ventas, tenant_id: UUID):
    """Crea un registro de cartera (cuenta por cobrar) para una factura emitida."""
    tercero = db.query(Terceros).filter(Terceros.id == factura.tercero_id).first()
    plazo = tercero.plazo_pago_dias if tercero and tercero.plazo_pago_dias else 30
    fecha_venc = factura.fecha_venta + timedelta(days=plazo)

    cartera = Cartera(
        tenant_id=tenant_id,
        tipo_cartera="COBRAR",
        documento_referencia=factura.numero_venta,
        tercero_id=factura.tercero_id,
        fecha_emision=factura.fecha_venta,
        fecha_vencimiento=fecha_venc,
        valor_total=factura.total_venta,
        saldo_pendiente=factura.total_venta,
        estado="PENDIENTE",
        observaciones=f"Factura {factura.numero_venta}",
    )
    db.add(cartera)
    logger.info(f"Cartera COBRAR creada para factura {factura.numero_venta}")


def _anular_cartera(db: Session, factura: Ventas, tenant_id: UUID):
    """Anula la cartera asociada a una factura."""
    cartera = db.query(Cartera).filter(
        Cartera.tenant_id == tenant_id,
        Cartera.documento_referencia == factura.numero_venta
    ).first()
    if cartera and cartera.estado != "ANULADA":
        cartera.estado = "ANULADA"
        cartera.saldo_pendiente = 0
        logger.info(f"Cartera anulada para factura {factura.numero_venta}")


def _get_tenant_info(db: Session, tenant_id: UUID) -> dict:
    """Obtiene info del tenant para el PDF."""
    tenant = db.query(Tenants).filter(Tenants.id == tenant_id).first()
    if not tenant:
        return {"nombre": "Empresa"}
    return {
        "nombre": tenant.nombre,
        "nit": tenant.nit,
        "email_contacto": tenant.email_contacto,
        "telefono": tenant.telefono,
        "direccion": tenant.direccion,
        "ciudad": tenant.ciudad,
        "departamento": tenant.departamento,
    }


def _get_cliente_info(tercero) -> dict:
    """Extrae info del cliente para el PDF."""
    return {
        "nombre": tercero.nombre,
        "tipo_documento": tercero.tipo_documento,
        "numero_documento": tercero.numero_documento,
        "direccion": tercero.direccion,
        "telefono": tercero.telefono,
        "email": tercero.email,
    }


def _get_detalles_pdf(detalles, db: Session, tenant_id: UUID) -> list:
    """Prepara los detalles para el PDF con nombres de producto."""
    result = []
    for det in detalles:
        producto = db.query(Productos).filter(
            Productos.id == det.producto_id,
            Productos.tenant_id == tenant_id
        ).first()
        result.append({
            "producto_nombre": producto.nombre if producto else "Producto",
            "cantidad": float(det.cantidad),
            "precio_unitario": float(det.precio_unitario),
            "descuento": float(det.descuento),
            "porcentaje_iva": float(det.porcentaje_iva),
        })
    return result


def _generar_pdf_factura(db: Session, factura: Ventas, tenant_id: UUID) -> bytes:
    """Genera el PDF de una factura."""
    tenant_info = _get_tenant_info(db, tenant_id)
    tercero = db.query(Terceros).filter(Terceros.id == factura.tercero_id).first()
    cliente_info = _get_cliente_info(tercero) if tercero else {"nombre": "Cliente"}
    detalles_pdf = _get_detalles_pdf(factura.detalles, db, tenant_id)

    servicio = ServicioPDF(tenant_info)
    return servicio.generar_factura_pdf(
        numero=factura.numero_venta,
        fecha=str(factura.fecha_venta),
        cliente=cliente_info,
        detalles=detalles_pdf,
        subtotal=factura.subtotal,
        descuento=factura.total_descuento,
        base_gravable=factura.base_gravable,
        total_iva=factura.total_iva,
        total=factura.total_venta,
        observaciones=factura.observaciones,
        descuento_global_pct=factura.descuento_global,
    )


@router.post("/pos", response_model=VentasResponse, status_code=status.HTTP_201_CREATED)
async def pos_factura(
    data: VentasCreate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles('admin', 'vendedor', 'operador'))
):
    """
    POS: Crea y emite una factura en un solo paso atómico.
    PENDIENTE -> FACTURADA con inventario + contabilidad + PDF.
    """
    tenant_id = ctx.tenant_id  # Compatibilidad con código existente
    # Validar tercero
    tercero = db.query(Terceros).filter(
        Terceros.id == data.tercero_id,
        Terceros.tenant_id == ctx.tenant_id
    ).first()
    if not tercero:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")

    if tercero.tipo_tercero not in ('CLIENTE', 'AMBOS'):
        raise HTTPException(
            status_code=400,
            detail="El tercero no está registrado como cliente"
        )

    # Generar número de factura (secuencia FACTURAS)
    numero = generar_numero_secuencia(db, 'FACTURAS', ctx.tenant_id)

    # Crear venta en estado PENDIENTE (transitorio)
    factura = Ventas(
        tenant_id=ctx.tenant_id,
        numero_venta=numero,
        tercero_id=data.tercero_id,
        fecha_venta=data.fecha_venta,
        estado="PENDIENTE",
        descuento_global=getattr(data, 'descuento_global', Decimal("0.00")) or Decimal("0.00"),
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

    db.flush()

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
                    observaciones=f"POS Factura {factura.numero_venta}"
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
        documento_referencia=factura.numero_venta,
        tercero_id=factura.tercero_id
    )

    # Generar PDF
    try:
        pdf_bytes = _generar_pdf_factura(db, factura, tenant_id)
        storage = ServicioAlmacenamiento()
        if storage.is_enabled:
            key = storage.subir_pdf(
                pdf_bytes, str(tenant_id),
                "facturas", factura.numero_venta
            )
            if key:
                factura.url_pdf = key
    except Exception as e:
        logger.warning(f"Error generando PDF para POS factura {factura.numero_venta}: {e}")

    factura.estado = "FACTURADA"

    # Crear cuenta por cobrar
    _crear_cartera_cobrar(db, factura, tenant_id)

    db.commit()
    db.refresh(factura)

    logger.info(f"POS Factura {factura.numero_venta} creada y emitida en un paso")
    return factura


@router.get("/", response_model=List[VentasResponse])
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


@router.post("/", response_model=VentasResponse, status_code=status.HTTP_201_CREATED)
async def crear_factura(
    data: VentasCreate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles('admin', 'vendedor', 'operador'))
):
    """
    Crea una nueva factura (venta en estado borrador/PENDIENTE).
    Usar POST /facturas/{id}/emitir para confirmar y descontar inventario.
    """
    tenant_id = ctx.tenant_id  # Compatibilidad con código existente
    # Validar tercero
    tercero = db.query(Terceros).filter(
        Terceros.id == data.tercero_id,
        Terceros.tenant_id == ctx.tenant_id
    ).first()
    if not tercero:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")

    if tercero.tipo_tercero not in ('CLIENTE', 'AMBOS'):
        raise HTTPException(
            status_code=400,
            detail="El tercero no está registrado como cliente"
        )

    # Generar número de factura
    numero = generar_numero_secuencia(db, 'FACTURAS', ctx.tenant_id)

    factura = Ventas(
        tenant_id=ctx.tenant_id,
        numero_venta=numero,
        tercero_id=data.tercero_id,
        fecha_venta=data.fecha_venta,
        estado="PENDIENTE",
        descuento_global=getattr(data, 'descuento_global', Decimal("0.00")) or Decimal("0.00"),
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


@router.get("/{factura_id}", response_model=VentasResponse)
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
    ctx: UserContext = Depends(require_tenant_roles('admin', 'vendedor', 'operador'))
):
    """
    Emite una factura:
    1. Valida estado = PENDIENTE
    2. Descuenta inventario de cada producto
    3. Crea asiento contable automático
    4. Genera PDF
    5. Cambia estado a FACTURADA
    """
    tenant_id = ctx.tenant_id  # Compatibilidad con código existente
    factura = db.query(Ventas).filter(
        Ventas.id == factura_id,
        Ventas.tenant_id == ctx.tenant_id
    ).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # Idempotente: si ya está facturada, retornar sin error
    if factura.estado == "FACTURADA":
        return {
            "factura": factura,
            "message": f"Factura {factura.numero_venta} ya estaba emitida"
        }

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
        documento_referencia=factura.numero_venta,
        tercero_id=factura.tercero_id
    )

    # Generar PDF y subir a S3 si está habilitado
    try:
        pdf_bytes = _generar_pdf_factura(db, factura, tenant_id)
        storage = ServicioAlmacenamiento()
        if storage.is_enabled:
            key = storage.subir_pdf(
                pdf_bytes, str(tenant_id),
                "facturas", factura.numero_venta
            )
            if key:
                factura.url_pdf = key
    except Exception as e:
        logger.warning(f"Error generando PDF para factura {factura.numero_venta}: {e}")

    factura.estado = "FACTURADA"

    # Crear cuenta por cobrar
    _crear_cartera_cobrar(db, factura, tenant_id)

    db.commit()
    db.refresh(factura)

    logger.info(f"Factura {factura.numero_venta} EMITIDA con inventario y contabilidad")

    return {
        "factura": factura,
        "message": f"Factura {factura.numero_venta} emitida exitosamente"
    }


@router.get("/{factura_id}/pdf")
async def descargar_pdf_factura(
    factura_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Descarga el PDF de una factura.
    Si hay S3 habilitado y url_pdf guardada, redirige a presigned URL.
    Sino, genera el PDF on-the-fly.
    """
    factura = db.query(Ventas).filter(
        Ventas.id == factura_id,
        Ventas.tenant_id == tenant_id
    ).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # Intentar S3 presigned URL
    if factura.url_pdf:
        storage = ServicioAlmacenamiento()
        if storage.is_enabled:
            url = storage.obtener_url_presigned(factura.url_pdf)
            if url:
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=url)

    # Generar on-the-fly
    pdf_bytes = _generar_pdf_factura(db, factura, tenant_id)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="factura-{factura.numero_venta}.pdf"'
        }
    )


@router.post("/{factura_id}/anular")
async def anular_factura(
    factura_id: UUID,
    motivo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles('admin'))
):
    """
    Anula una factura (SOLO ADMIN):
    1. Revierte movimientos de inventario (si estaba emitida)
    2. Crea asiento contable de reversión
    3. Cambia estado a ANULADA
    """
    tenant_id = ctx.tenant_id  # Compatibilidad con código existente
    factura = db.query(Ventas).filter(
        Ventas.id == factura_id,
        Ventas.tenant_id == ctx.tenant_id
    ).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # Idempotente: si ya está anulada, retornar sin error
    if factura.estado == "ANULADA":
        return {
            "factura": factura,
            "message": f"Factura {factura.numero_venta} ya estaba anulada"
        }

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
            documento_referencia=factura.numero_venta,
            tercero_id=factura.tercero_id
        )

    factura.estado = "ANULADA"
    if motivo:
        obs = f"ANULADA: {motivo}"
        factura.observaciones = f"{factura.observaciones}\n{obs}" if factura.observaciones else obs

    # Anular cartera asociada
    _anular_cartera(db, factura, tenant_id)

    db.commit()
    db.refresh(factura)

    logger.warning(f"Factura {factura.numero_venta} ANULADA - Motivo: {motivo or 'No especificado'}")

    return {
        "factura": factura,
        "message": f"Factura {factura.numero_venta} anulada"
    }
