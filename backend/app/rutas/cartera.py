from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import Cartera, PagosCartera, Usuarios
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
