from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import (
    Cotizaciones, CotizacionesDetalle, Terceros, Productos, Usuarios,
    Ventas, VentasDetalle
)
from ..datos.esquemas import CotizacionesCreate, CotizacionesResponse
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..utils.secuencia_helper import generar_numero_secuencia
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/")
async def listar(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        estado: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Lista cotizaciones del tenant."""
    query = db.query(Cotizaciones).filter(Cotizaciones.tenant_id == tenant_id)
    if estado:
        query = query.filter(Cotizaciones.estado == estado)
    items = query.order_by(Cotizaciones.created_at.desc()).offset(skip).limit(limit).all()
    return items


@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear(
        data: CotizacionesCreate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Crea una nueva cotización."""
    # Validar tercero
    tercero = db.query(Terceros).filter(
        Terceros.id == data.tercero_id,
        Terceros.tenant_id == tenant_id
    ).first()
    if not tercero:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")

    numero = generar_numero_secuencia(db, 'COTIZACIONES', tenant_id)
    cot = Cotizaciones(
        tenant_id=tenant_id,
        numero_cotizacion=numero,
        tercero_id=data.tercero_id,
        fecha_cotizacion=data.fecha_cotizacion,
        fecha_vencimiento=data.fecha_vencimiento,
        estado="PENDIENTE",
        observaciones=data.observaciones
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
            porcentaje_iva=det.porcentaje_iva
        )
        db.add(detalle)

    db.commit()
    db.refresh(cot)
    logger.info(f"Cotización creada: {cot.numero_cotizacion}")
    return cot


@router.get("/{cotizacion_id}")
async def obtener(
        cotizacion_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene una cotización por ID."""
    cot = db.query(Cotizaciones).filter(
        Cotizaciones.id == cotizacion_id,
        Cotizaciones.tenant_id == tenant_id
    ).first()
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    return cot


@router.post("/{cotizacion_id}/convertir")
async def convertir_a_factura(
        cotizacion_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Convierte una cotización a factura (borrador).
    1. Valida que la cotización está en estado VIGENTE o ACEPTADA
    2. Crea una nueva Venta (factura borrador) con los mismos detalles
    3. Marca la cotización como ACEPTADA
    """
    from datetime import date as date_type

    cot = db.query(Cotizaciones).filter(
        Cotizaciones.id == cotizacion_id,
        Cotizaciones.tenant_id == tenant_id
    ).first()
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    if cot.estado not in ("VIGENTE", "ACEPTADA", "PENDIENTE"):
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden convertir cotizaciones en estado VIGENTE, ACEPTADA o PENDIENTE. Estado actual: {cot.estado}"
        )

    # Generar número de factura
    numero_factura = generar_numero_secuencia(db, 'FACTURAS', tenant_id)

    # Crear factura (venta en borrador)
    factura = Ventas(
        tenant_id=tenant_id,
        numero_venta=numero_factura,
        tercero_id=cot.tercero_id,
        fecha_venta=date_type.today(),
        estado="PENDIENTE",
        observaciones=f"Generada desde cotización {cot.numero_cotizacion}"
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
            porcentaje_iva=det.porcentaje_iva
        )
        db.add(detalle_factura)

    # Actualizar estado cotización
    cot.estado = "ACEPTADA"

    db.commit()
    db.refresh(factura)

    logger.info(
        f"Cotización {cot.numero_cotizacion} convertida a factura {numero_factura}"
    )

    return {
        "cotizacion_id": str(cotizacion_id),
        "cotizacion_numero": cot.numero_cotizacion,
        "factura_id": str(factura.id),
        "factura_numero": factura.numero_venta,
        "message": f"Cotización convertida a factura {numero_factura} (borrador)"
    }
