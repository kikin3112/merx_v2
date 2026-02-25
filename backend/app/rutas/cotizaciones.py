import io
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload

from ..datos.db import get_db
from ..datos.esquemas import CotizacionesCreate, CotizacionesResponse
from ..datos.modelos import Cotizaciones, CotizacionesDetalle, Productos, Terceros, Usuarios, Ventas, VentasDetalle
from ..datos.modelos_tenant import Tenants
from ..servicios.servicio_almacenamiento import ServicioAlmacenamiento
from ..servicios.servicio_pdf import ServicioPDF
from ..utils.logger import setup_logger
from ..utils.secuencia_helper import generar_numero_secuencia
from ..utils.seguridad import get_current_user, get_tenant_id_from_token

router = APIRouter()
logger = setup_logger(__name__)


def _generar_pdf_cotizacion(db: Session, cot: Cotizaciones, tenant_id: UUID) -> bytes:
    """Genera el PDF de una cotización."""
    tenant = db.query(Tenants).filter(Tenants.id == tenant_id).first()
    tenant_info = {
        "nombre": tenant.nombre if tenant else "Empresa",
        "nit": getattr(tenant, "nit", None),
        "email_contacto": getattr(tenant, "email_contacto", None),
        "telefono": getattr(tenant, "telefono", None),
        "direccion": getattr(tenant, "direccion", None),
        "ciudad": getattr(tenant, "ciudad", None),
        "departamento": getattr(tenant, "departamento", None),
    }

    tercero = db.query(Terceros).filter(Terceros.id == cot.tercero_id).first()
    cliente_info = {
        "nombre": tercero.nombre if tercero else "Cliente",
        "tipo_documento": getattr(tercero, "tipo_documento", ""),
        "numero_documento": getattr(tercero, "numero_documento", ""),
        "direccion": getattr(tercero, "direccion", None),
        "telefono": getattr(tercero, "telefono", None),
        "email": getattr(tercero, "email", None),
    }

    detalles_pdf = []
    for det in cot.detalles:
        producto = db.query(Productos).filter(Productos.id == det.producto_id, Productos.tenant_id == tenant_id).first()
        detalles_pdf.append(
            {
                "producto_nombre": producto.nombre if producto else "Producto",
                "cantidad": float(det.cantidad),
                "precio_unitario": float(det.precio_unitario),
                "descuento": float(det.descuento),
                "porcentaje_iva": float(det.porcentaje_iva),
            }
        )

    servicio = ServicioPDF(tenant_info)
    return servicio.generar_cotizacion_pdf(
        numero=cot.numero_cotizacion,
        fecha=str(cot.fecha_cotizacion),
        fecha_vencimiento=str(cot.fecha_vencimiento),
        cliente=cliente_info,
        detalles=detalles_pdf,
        subtotal=cot.subtotal,
        descuento=cot.total_descuento,
        base_gravable=cot.subtotal - cot.total_descuento,
        total_iva=cot.total_iva,
        total=cot.total_cotizacion,
        observaciones=cot.observaciones,
        descuento_global_pct=cot.descuento_global,
    )


@router.get("/", response_model=List[CotizacionesResponse])
async def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Lista cotizaciones del tenant."""
    query = (
        db.query(Cotizaciones)
        .options(selectinload(Cotizaciones.created_by_user), selectinload(Cotizaciones.updated_by_user))
        .filter(Cotizaciones.tenant_id == tenant_id)
    )
    if estado:
        query = query.filter(Cotizaciones.estado == estado)
    items = query.order_by(Cotizaciones.created_at.desc()).offset(skip).limit(limit).all()
    return items


@router.post("/", response_model=CotizacionesResponse, status_code=status.HTTP_201_CREATED)
async def crear(
    data: CotizacionesCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Crea una nueva cotización."""
    # Validar tercero
    tercero = db.query(Terceros).filter(Terceros.id == data.tercero_id, Terceros.tenant_id == tenant_id).first()
    if not tercero:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")

    numero = generar_numero_secuencia(db, "COTIZACIONES", tenant_id)
    cot = Cotizaciones(
        tenant_id=tenant_id,
        numero_cotizacion=numero,
        tercero_id=data.tercero_id,
        fecha_cotizacion=data.fecha_cotizacion,
        fecha_vencimiento=data.fecha_vencimiento,
        estado="VIGENTE",
        descuento_global=getattr(data, "descuento_global", Decimal("0.00")) or Decimal("0.00"),
        observaciones=data.observaciones,
    )
    db.add(cot)
    db.flush()

    for det in data.detalles:
        detalle = CotizacionesDetalle(
            tenant_id=tenant_id,
            cotizacion_id=cot.id,
            producto_id=det.producto_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
            descuento=det.descuento,
            porcentaje_iva=det.porcentaje_iva,
        )
        db.add(detalle)

    db.commit()
    db.refresh(cot)
    logger.info(f"Cotización creada: {cot.numero_cotizacion}")
    return cot


@router.get("/{cotizacion_id}", response_model=CotizacionesResponse)
async def obtener(
    cotizacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Obtiene una cotización por ID."""
    cot = (
        db.query(Cotizaciones)
        .options(selectinload(Cotizaciones.created_by_user), selectinload(Cotizaciones.updated_by_user))
        .filter(Cotizaciones.id == cotizacion_id, Cotizaciones.tenant_id == tenant_id)
        .first()
    )
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    return cot


@router.get("/{cotizacion_id}/pdf")
async def descargar_pdf_cotizacion(
    cotizacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Descarga el PDF de una cotización."""
    cot = db.query(Cotizaciones).filter(Cotizaciones.id == cotizacion_id, Cotizaciones.tenant_id == tenant_id).first()
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    # Intentar S3 presigned URL
    if cot.url_pdf:
        storage = ServicioAlmacenamiento()
        if storage.is_enabled:
            url = storage.obtener_url_presigned(cot.url_pdf)
            if url:
                from fastapi.responses import RedirectResponse

                return RedirectResponse(url=url)

    # Generar on-the-fly
    pdf_bytes = _generar_pdf_cotizacion(db, cot, tenant_id)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="cotizacion-{cot.numero_cotizacion}.pdf"'},
    )


@router.post("/{cotizacion_id}/convertir")
async def convertir_a_factura(
    cotizacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """
    Convierte una cotización a factura (borrador).
    1. Valida que la cotización está en estado VIGENTE o ACEPTADA
    2. Crea una nueva Venta (factura borrador) con los mismos detalles
    3. Marca la cotización como ACEPTADA
    """
    from datetime import date as date_type

    cot = db.query(Cotizaciones).filter(Cotizaciones.id == cotizacion_id, Cotizaciones.tenant_id == tenant_id).first()
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    # Idempotente: si ya fue convertida/aceptada previamente, retornar info existente
    if cot.estado == "ACEPTADA":
        # Buscar factura ya generada desde esta cotización
        factura_existente = (
            db.query(Ventas)
            .filter(Ventas.tenant_id == tenant_id, Ventas.observaciones.contains(cot.numero_cotizacion))
            .first()
        )
        if factura_existente:
            return {
                "cotizacion_id": str(cotizacion_id),
                "cotizacion_numero": cot.numero_cotizacion,
                "factura_id": str(factura_existente.id),
                "factura_numero": factura_existente.numero_venta,
                "message": f"Cotización ya fue convertida a factura {factura_existente.numero_venta}",
            }

    if cot.estado not in ("VIGENTE",):
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden convertir cotizaciones en estado VIGENTE. Estado actual: {cot.estado}",
        )

    # Generar número de factura
    numero_factura = generar_numero_secuencia(db, "FACTURAS", tenant_id)

    # Crear factura (venta en borrador)
    factura = Ventas(
        tenant_id=tenant_id,
        numero_venta=numero_factura,
        tercero_id=cot.tercero_id,
        fecha_venta=date_type.today(),
        estado="PENDIENTE",
        descuento_global=cot.descuento_global or Decimal("0.00"),
        observaciones=f"Generada desde cotización {cot.numero_cotizacion}",
    )
    db.add(factura)
    db.flush()

    # Copiar detalles
    for det in cot.detalles:
        detalle_factura = VentasDetalle(
            tenant_id=tenant_id,
            venta_id=factura.id,
            producto_id=det.producto_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
            descuento=det.descuento,
            porcentaje_iva=det.porcentaje_iva,
        )
        db.add(detalle_factura)

    # Actualizar estado cotización
    cot.estado = "ACEPTADA"

    db.commit()
    db.refresh(factura)

    logger.info(f"Cotización {cot.numero_cotizacion} convertida a factura {numero_factura}")

    return {
        "cotizacion_id": str(cotizacion_id),
        "cotizacion_numero": cot.numero_cotizacion,
        "factura_id": str(factura.id),
        "factura_numero": factura.numero_venta,
        "message": f"Cotización convertida a factura {numero_factura} (borrador)",
    }
