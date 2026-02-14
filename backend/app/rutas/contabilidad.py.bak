from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import date

from ..datos.db import get_db
from ..datos.modelos import AsientosContables, DetallesAsiento, CuentasContables, Usuarios
from ..datos.esquemas import AsientoContableCreate
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..servicios.servicio_contabilidad import ServicioContabilidad
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/asientos")
async def listar_asientos(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        tipo_asiento: Optional[str] = Query(None),
        fecha_inicio: Optional[date] = Query(None),
        fecha_fin: Optional[date] = Query(None),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Lista asientos contables del tenant con filtros."""
    query = db.query(AsientosContables).filter(
        AsientosContables.tenant_id == tenant_id
    )

    if tipo_asiento:
        query = query.filter(AsientosContables.tipo_asiento == tipo_asiento)

    if fecha_inicio:
        query = query.filter(AsientosContables.fecha >= fecha_inicio)

    if fecha_fin:
        query = query.filter(AsientosContables.fecha <= fecha_fin)

    return query.order_by(AsientosContables.fecha.desc()).offset(skip).limit(limit).all()


@router.get("/asientos/{asiento_id}")
async def obtener_asiento(
        asiento_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene un asiento contable con sus detalles."""
    asiento = db.query(AsientosContables).filter(
        AsientosContables.id == asiento_id,
        AsientosContables.tenant_id == tenant_id
    ).first()
    if not asiento:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    return asiento


@router.post("/asientos", status_code=status.HTTP_201_CREATED)
async def crear_asiento(
        data: AsientoContableCreate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Crea un asiento contable manual.
    Valida que la suma de débitos sea igual a la suma de créditos.
    """
    servicio = ServicioContabilidad(db, tenant_id)

    detalles = [
        {
            "cuenta_id": det.cuenta_id,
            "debito": det.debito,
            "credito": det.credito,
            "descripcion": det.descripcion
        }
        for det in data.detalles
    ]

    asiento = servicio.crear_asiento(
        fecha=data.fecha,
        tipo_asiento=data.tipo_asiento,
        concepto=data.concepto,
        detalles=detalles,
        documento_referencia=data.documento_referencia
    )

    db.commit()
    db.refresh(asiento)
    return asiento


@router.get("/balance-prueba")
async def balance_prueba(
        fecha_inicio: Optional[date] = Query(None),
        fecha_fin: Optional[date] = Query(None),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Genera balance de prueba.
    Muestra por cada cuenta con movimiento: total débito, total crédito y saldo.
    """
    servicio = ServicioContabilidad(db, tenant_id)
    resultados = servicio.obtener_balance_prueba(fecha_inicio, fecha_fin)

    # Totales
    total_debito = sum(r["total_debito"] for r in resultados)
    total_credito = sum(r["total_credito"] for r in resultados)

    return {
        "cuentas": resultados,
        "total_debito": total_debito,
        "total_credito": total_credito,
        "diferencia": total_debito - total_credito,
        "balanceado": abs(total_debito - total_credito) < 0.01
    }
