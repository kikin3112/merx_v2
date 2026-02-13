from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from typing import List, Optional
from uuid import UUID
from datetime import date

from ..datos.db import get_db
from ..datos.modelos import Cartera, PagosCartera, Usuarios, MediosPago
from ..datos.esquemas import CarteraCreate, CarteraResponse, PagoCarteraCreate, PagoCarteraResponse
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/", response_model=List[CarteraResponse])
async def listar_cartera(
    tipo_cartera: Optional[str] = Query(None, pattern="^(COBRAR|PAGAR)$"),
    estado: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    query = db.query(Cartera).filter(Cartera.tenant_id == tenant_id)
    if tipo_cartera:
        query = query.filter(Cartera.tipo_cartera == tipo_cartera)
    if estado:
        query = query.filter(Cartera.estado == estado)
    items = query.order_by(Cartera.fecha_vencimiento).offset(skip).limit(limit).all()
    return [CarteraResponse.model_validate(c) for c in items]


@router.post("/", response_model=CarteraResponse, status_code=status.HTTP_201_CREATED)
async def crear_cartera(
    data: CarteraCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    cartera = Cartera(tenant_id=tenant_id, **data.model_dump())
    db.add(cartera)
    db.commit()
    db.refresh(cartera)
    return CarteraResponse.model_validate(cartera)


@router.get("/resumen/totales")
async def resumen_cartera(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Resumen de totales de cartera por cobrar."""
    hoy = date.today()

    total_pendiente = db.query(sqlfunc.coalesce(sqlfunc.sum(Cartera.saldo_pendiente), 0)).filter(
        Cartera.tenant_id == tenant_id,
        Cartera.tipo_cartera == "COBRAR",
        Cartera.estado.in_(["PENDIENTE", "PARCIAL"])
    ).scalar()

    total_vencido = db.query(sqlfunc.coalesce(sqlfunc.sum(Cartera.saldo_pendiente), 0)).filter(
        Cartera.tenant_id == tenant_id,
        Cartera.tipo_cartera == "COBRAR",
        Cartera.estado.in_(["PENDIENTE", "PARCIAL"]),
        Cartera.fecha_vencimiento < hoy
    ).scalar()

    cantidad_pendientes = db.query(sqlfunc.count(Cartera.id)).filter(
        Cartera.tenant_id == tenant_id,
        Cartera.tipo_cartera == "COBRAR",
        Cartera.estado.in_(["PENDIENTE", "PARCIAL"])
    ).scalar()

    cantidad_vencidas = db.query(sqlfunc.count(Cartera.id)).filter(
        Cartera.tenant_id == tenant_id,
        Cartera.tipo_cartera == "COBRAR",
        Cartera.estado.in_(["PENDIENTE", "PARCIAL"]),
        Cartera.fecha_vencimiento < hoy
    ).scalar()

    return {
        "total_por_cobrar": float(total_pendiente),
        "total_vencido": float(total_vencido),
        "cantidad_pendientes": cantidad_pendientes,
        "cantidad_vencidas": cantidad_vencidas,
    }


@router.get("/medios-pago/list")
async def listar_medios_pago(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Lista medios de pago del tenant para el formulario de registro de pagos."""
    medios = db.query(MediosPago).filter(
        MediosPago.tenant_id == tenant_id,
        MediosPago.estado == True
    ).order_by(MediosPago.nombre).all()
    return [{"id": str(m.id), "nombre": m.nombre, "tipo": m.tipo} for m in medios]


@router.get("/{cartera_id}", response_model=CarteraResponse)
async def obtener_cartera(
    cartera_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    item = db.query(Cartera).filter(
        Cartera.id == cartera_id, Cartera.tenant_id == tenant_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Registro de cartera no encontrado")
    return CarteraResponse.model_validate(item)


@router.post("/{cartera_id}/pagos", response_model=PagoCarteraResponse, status_code=status.HTTP_201_CREATED)
async def registrar_pago(
    cartera_id: UUID,
    data: PagoCarteraCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    cartera = db.query(Cartera).filter(
        Cartera.id == cartera_id, Cartera.tenant_id == tenant_id
    ).first()
    if not cartera:
        raise HTTPException(status_code=404, detail="Registro de cartera no encontrado")

    if cartera.estado in ("PAGADA", "ANULADA"):
        raise HTTPException(status_code=400, detail=f"No se pueden registrar pagos en cartera con estado {cartera.estado}")

    if data.valor_pago > cartera.saldo_pendiente:
        raise HTTPException(status_code=400, detail=f"El valor del pago ({data.valor_pago}) excede el saldo pendiente ({cartera.saldo_pendiente})")

    pago = PagosCartera(
        tenant_id=tenant_id,
        cartera_id=cartera_id,
        fecha_pago=data.fecha_pago,
        valor_pago=data.valor_pago,
        medio_pago_id=data.medio_pago_id,
        numero_referencia=data.numero_referencia,
        observaciones=data.observaciones
    )
    db.add(pago)

    cartera.saldo_pendiente -= data.valor_pago
    if cartera.saldo_pendiente <= 0:
        cartera.saldo_pendiente = 0
        cartera.estado = "PAGADA"
    elif cartera.saldo_pendiente < cartera.valor_total:
        cartera.estado = "PARCIAL"

    db.commit()
    db.refresh(pago)
    return PagoCarteraResponse.model_validate(pago)


@router.get("/{cartera_id}/pagos", response_model=List[PagoCarteraResponse])
async def listar_pagos_cartera(
    cartera_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    cartera = db.query(Cartera).filter(
        Cartera.id == cartera_id, Cartera.tenant_id == tenant_id
    ).first()
    if not cartera:
        raise HTTPException(status_code=404, detail="Registro de cartera no encontrado")
    pagos = db.query(PagosCartera).filter(
        PagosCartera.cartera_id == cartera_id,
        PagosCartera.tenant_id == tenant_id
    ).order_by(PagosCartera.fecha_pago.desc()).all()
    return [PagoCarteraResponse.model_validate(p) for p in pagos]
