from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from ..datos.db import get_db
from ..datos.esquemas import VentasCreate, VentasUpdate, VentasResponse
from ..datos.modelos import Usuarios, Terceros, Ventas, VentasDetalle, Productos
from ..servicios.servicio_ventas import (
    crear_venta,
    listar_ventas,
    obtener_venta,
    actualizar_venta,
    anular_venta,
    confirmar_venta,
    obtener_estadisticas_ventas
)
from ..servicios.servicio_contabilidad import ServicioContabilidad
from ..servicios.servicio_almacenamiento import ServicioAlmacenamiento
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/", response_model=VentasResponse, status_code=status.HTTP_201_CREATED)
async def crear_nueva_venta(
        venta_data: VentasCreate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Crea una nueva venta."""
    try:
        nueva_venta = crear_venta(db, venta_data, tenant_id)
        db.commit()

        logger.info(
            f"Venta creada: {nueva_venta.numero_venta}",
            extra={
                "venta_id": str(nueva_venta.id),
                "total": float(nueva_venta.total_venta),
                "user_id": str(current_user.id)
            }
        )

        return VentasResponse.model_validate(nueva_venta)

    except ValueError as e:
        logger.warning(f"Validación fallida al crear venta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error("Error creando venta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la venta"
        )


@router.get("/", response_model=List[VentasResponse])
async def listar_ventas_endpoint(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        tercero_id: Optional[UUID] = Query(None),
        estado: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Lista ventas con filtros opcionales."""
    ventas = listar_ventas(
        db,
        tenant_id=tenant_id,
        skip=skip,
        limit=limit,
        tercero_id=tercero_id,
        estado=estado
    )

    return [VentasResponse.model_validate(v) for v in ventas]


@router.get("/estadisticas", response_model=dict)
async def obtener_estadisticas(
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene estadísticas de ventas."""
    return obtener_estadisticas_ventas(db, tenant_id)


@router.get("/{venta_id}", response_model=VentasResponse)
async def obtener_venta_endpoint(
        venta_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene una venta por ID."""
    venta = obtener_venta(db, venta_id, tenant_id)
    return VentasResponse.model_validate(venta)


@router.patch("/{venta_id}", response_model=VentasResponse)
async def actualizar_venta_endpoint(
        venta_id: UUID,
        venta_data: VentasUpdate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Actualiza una venta existente."""
    try:
        venta = actualizar_venta(db, venta_id, venta_data, tenant_id)
        db.commit()

        logger.info(
            f"Venta actualizada: {venta.numero_venta}",
            extra={
                "venta_id": str(venta.id),
                "user_id": str(current_user.id)
            }
        )

        return VentasResponse.model_validate(venta)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error actualizando venta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar la venta"
        )


@router.put("/{venta_id}", response_model=VentasResponse)
async def reemplazar_venta(
        venta_id: UUID,
        data: VentasCreate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Reemplaza los detalles de una venta PENDIENTE.
    Borra los detalles existentes y los crea nuevos.
    Solo permite edición en estado PENDIENTE.
    """
    venta = obtener_venta(db, venta_id, tenant_id)

    if venta.estado != "PENDIENTE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se pueden editar ventas en estado PENDIENTE. Estado actual: {venta.estado}"
        )

    # Actualizar campos de cabecera
    venta.tercero_id = data.tercero_id
    venta.fecha_venta = data.fecha_venta
    venta.descuento_global = getattr(data, 'descuento_global', Decimal("0.00")) or Decimal("0.00")
    venta.observaciones = data.observaciones

    # Borrar detalles existentes
    db.query(VentasDetalle).filter(
        VentasDetalle.venta_id == venta_id,
        VentasDetalle.tenant_id == tenant_id
    ).delete()

    # Crear nuevos detalles
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
        if not producto.estado:
            raise HTTPException(
                status_code=400,
                detail=f"Producto {producto.nombre} está inactivo"
            )

        precio = det.precio_unitario if det.precio_unitario > 0 else producto.precio_venta
        iva = det.porcentaje_iva if det.porcentaje_iva > 0 else producto.porcentaje_iva

        detalle = VentasDetalle(
            tenant_id=tenant_id,
            venta_id=venta.id,
            producto_id=det.producto_id,
            cantidad=det.cantidad,
            precio_unitario=precio,
            descuento=det.descuento,
            porcentaje_iva=iva
        )
        db.add(detalle)

    db.commit()
    db.refresh(venta)

    logger.info(f"Venta {venta.numero_venta} editada - Items: {len(data.detalles)}")
    return VentasResponse.model_validate(venta)


@router.post("/{venta_id}/confirmar", response_model=VentasResponse)
async def confirmar_venta_endpoint(
        venta_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Confirma una venta (PENDIENTE -> CONFIRMADA). Descuenta inventario."""
    try:
        venta = confirmar_venta(db, venta_id, tenant_id)
        db.commit()

        logger.info(
            f"Venta confirmada: {venta.numero_venta}",
            extra={
                "venta_id": str(venta.id),
                "user_id": str(current_user.id)
            }
        )

        return VentasResponse.model_validate(venta)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error confirmando venta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al confirmar la venta"
        )


@router.post("/{venta_id}/anular", response_model=VentasResponse)
async def anular_venta_endpoint(
        venta_id: UUID,
        motivo: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Anula una venta. Revierte inventario si estaba confirmada."""
    try:
        venta = anular_venta(db, venta_id, tenant_id, motivo)
        db.commit()

        logger.warning(
            f"Venta anulada: {venta.numero_venta}",
            extra={
                "venta_id": str(venta.id),
                "motivo": motivo,
                "user_id": str(current_user.id)
            }
        )

        return VentasResponse.model_validate(venta)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error anulando venta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al anular la venta"
        )


@router.post("/{venta_id}/facturar", response_model=VentasResponse)
async def facturar_venta_endpoint(
        venta_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Factura una venta confirmada (CONFIRMADA -> FACTURADA).
    Agrega contabilidad + PDF. NO descuenta inventario (ya se hizo al confirmar).
    """
    venta = obtener_venta(db, venta_id, tenant_id)

    if venta.estado != "CONFIRMADA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se pueden facturar ventas en estado CONFIRMADA. Estado actual: {venta.estado}"
        )

    # Crear asiento contable automático
    servicio_cont = ServicioContabilidad(db, tenant_id)
    servicio_cont.crear_asiento_venta(
        fecha=venta.fecha_venta,
        subtotal=venta.subtotal,
        total_iva=venta.total_iva,
        total=venta.total_venta,
        documento_referencia=venta.numero_venta
    )

    # Generar PDF
    try:
        from ..rutas.facturas import _generar_pdf_factura
        pdf_bytes = _generar_pdf_factura(db, venta, tenant_id)
        storage = ServicioAlmacenamiento()
        if storage.is_enabled:
            key = storage.subir_pdf(
                pdf_bytes, str(tenant_id),
                "facturas", venta.numero_venta
            )
            if key:
                venta.url_pdf = key
    except Exception as e:
        logger.warning(f"Error generando PDF para venta {venta.numero_venta}: {e}")

    venta.estado = "FACTURADA"
    db.commit()
    db.refresh(venta)

    logger.info(f"Venta {venta.numero_venta} facturada con contabilidad y PDF")
    return VentasResponse.model_validate(venta)


@router.post("/pos", response_model=VentasResponse, status_code=status.HTTP_201_CREATED)
async def pos_venta_rapida(
        venta_data: VentasCreate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    POS: Crea y confirma una venta en un solo paso.
    Combina crear_venta() + confirmar_venta() para flujo rápido de punto de venta.
    """
    try:
        nueva_venta = crear_venta(db, venta_data, tenant_id)
        db.flush()

        venta_confirmada = confirmar_venta(db, nueva_venta.id, tenant_id)
        db.commit()

        logger.info(
            f"POS venta creada y confirmada: {venta_confirmada.numero_venta}",
            extra={
                "venta_id": str(venta_confirmada.id),
                "total": float(venta_confirmada.total_venta),
                "user_id": str(current_user.id)
            }
        )

        return VentasResponse.model_validate(venta_confirmada)

    except ValueError as e:
        db.rollback()
        logger.warning(f"POS validación fallida: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error en POS venta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la venta POS"
        )
