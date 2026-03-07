from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from ..datos.db import get_db
from ..datos.esquemas import ComprasCreate, ComprasResponse
from ..datos.modelos import Compras, ComprasDetalle, EstadoCompra, Productos, Terceros, TipoMovimiento, Usuarios
from ..servicios.servicio_contabilidad import ServicioContabilidad
from ..servicios.servicio_inventario import ServicioInventario
from ..utils.logger import setup_logger
from ..utils.secuencia_helper import generar_numero_secuencia
from ..utils.seguridad import get_current_user, get_tenant_id_from_token

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/", response_model=ComprasResponse, status_code=status.HTTP_201_CREATED)
async def crear_compra(
    compra_data: ComprasCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Crea una nueva compra."""
    tercero = db.query(Terceros).filter(Terceros.id == compra_data.tercero_id, Terceros.tenant_id == tenant_id).first()
    if not tercero or tercero.tipo_tercero not in ("PROVEEDOR", "AMBOS"):
        raise HTTPException(status_code=400, detail="Tercero debe ser proveedor")
    try:
        numero = generar_numero_secuencia(db, "COMPRAS", tenant_id)
        compra = Compras(
            tenant_id=tenant_id,
            numero_compra=numero,
            tercero_id=compra_data.tercero_id,
            fecha_compra=compra_data.fecha_compra,
            estado="PENDIENTE",
        )
        db.add(compra)
        db.flush()
        for det in compra_data.detalles:
            detalle = ComprasDetalle(
                tenant_id=tenant_id,
                compra_id=compra.id,
                producto_id=det.producto_id,
                cantidad=det.cantidad,
                precio_unitario=det.precio_unitario,
                descuento=det.descuento or 0,
                porcentaje_iva=det.porcentaje_iva or 0,
            )
            db.add(detalle)
        db.commit()
        db.refresh(compra)
        logger.info(f"Compra creada: {compra.numero_compra}")
        return ComprasResponse.model_validate(compra)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error creando compra", exc_info=e)
        raise HTTPException(status_code=500, detail="Error interno")


@router.get("/", response_model=List[ComprasResponse])
async def listar_compras(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Lista compras del tenant."""
    compras = (
        db.query(Compras)
        .options(selectinload(Compras.created_by_user), selectinload(Compras.updated_by_user))
        .filter(Compras.tenant_id == tenant_id)
        .order_by(Compras.fecha_compra.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [ComprasResponse.model_validate(c) for c in compras]


@router.get("/{compra_id}", response_model=ComprasResponse)
async def obtener_compra(
    compra_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Obtiene una compra por ID."""
    compra = (
        db.query(Compras)
        .options(
            selectinload(Compras.created_by_user), selectinload(Compras.updated_by_user), selectinload(Compras.detalles)
        )
        .filter(Compras.id == compra_id, Compras.tenant_id == tenant_id)
        .first()
    )
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    return ComprasResponse.model_validate(compra)


@router.put("/{compra_id}/recibir", response_model=ComprasResponse)
async def recibir_compra(
    compra_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """
    Recibe una compra PENDIENTE:
    - Transiciona estado PENDIENTE → RECIBIDA
    - Crea movimiento ENTRADA en inventario por cada detalle (actualiza CPP)
    - Crea asiento contable COMPRA_CONTADO (DEBE: 1435 Inventario / HABER: 1105 Caja)
    """
    compra = (
        db.query(Compras)
        .options(
            selectinload(Compras.detalles).selectinload(ComprasDetalle.producto),
        )
        .filter(Compras.id == compra_id, Compras.tenant_id == tenant_id)
        .first()
    )
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")

    if compra.estado != EstadoCompra.PENDIENTE:
        raise HTTPException(
            status_code=400,
            detail=f"La compra no puede recibirse en estado '{compra.estado.value}'. Solo compras PENDIENTE.",
        )

    svc_inv = ServicioInventario(db, tenant_id)

    for detalle in compra.detalles:
        producto: Productos = detalle.producto
        if not producto or not producto.maneja_inventario:
            continue

        descuento = detalle.descuento or Decimal("0")
        costo_neto = detalle.precio_unitario * (1 - descuento / Decimal("100"))

        try:
            svc_inv.crear_movimiento(
                producto_id=detalle.producto_id,
                tipo=TipoMovimiento.ENTRADA,
                cantidad=detalle.cantidad,
                costo_unitario=costo_neto,
                documento_referencia=compra.numero_compra,
                observaciones=f"Recepción compra {compra.numero_compra}",
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Accounting entry — COMPRA_CONTADO config must exist; skip gracefully if not
    try:
        svc_cont = ServicioContabilidad(db, tenant_id)
        svc_cont.crear_asiento_compra(
            fecha=compra.fecha_compra,
            base_gravable=compra.base_gravable,
            documento_referencia=compra.numero_compra,
            tercero_id=compra.tercero_id,
        )
    except ValueError as e:
        logger.warning(f"Asiento COMPRA_CONTADO no creado para {compra.numero_compra}: {e}")

    compra.estado = EstadoCompra.RECIBIDA
    db.commit()
    db.refresh(compra)
    logger.info(f"Compra recibida: {compra.numero_compra}")
    return ComprasResponse.model_validate(compra)
