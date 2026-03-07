from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from ..datos.db import get_db
from ..datos.esquemas import AsientoContableCreate
from ..datos.modelos import AsientosContables
from ..servicios.servicio_contabilidad import ServicioContabilidad
from ..utils.logger import setup_logger
from ..utils.seguridad import UserContext, require_tenant_roles

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
    ctx: UserContext = Depends(require_tenant_roles("admin", "contador")),
):
    """Lista asientos contables del tenant con filtros."""
    query = (
        db.query(AsientosContables)
        .options(selectinload(AsientosContables.created_by_user), selectinload(AsientosContables.updated_by_user))
        .filter(AsientosContables.tenant_id == ctx.tenant_id)
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
    ctx: UserContext = Depends(require_tenant_roles("admin", "contador")),
):
    """Obtiene un asiento contable con sus detalles."""
    asiento = (
        db.query(AsientosContables)
        .options(selectinload(AsientosContables.created_by_user), selectinload(AsientosContables.updated_by_user))
        .filter(AsientosContables.id == asiento_id, AsientosContables.tenant_id == ctx.tenant_id)
        .first()
    )
    if not asiento:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    return asiento


@router.post("/asientos", status_code=status.HTTP_201_CREATED)
async def crear_asiento(
    data: AsientoContableCreate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "contador")),
):
    """
    Crea un asiento contable manual.
    Valida que la suma de débitos sea igual a la suma de créditos.
    """
    servicio = ServicioContabilidad(db, ctx.tenant_id)

    detalles = [
        {"cuenta_id": det.cuenta_id, "debito": det.debito, "credito": det.credito, "descripcion": det.descripcion}
        for det in data.detalles
    ]

    asiento = servicio.crear_asiento(
        fecha=data.fecha,
        tipo_asiento=data.tipo_asiento,
        concepto=data.concepto,
        detalles=detalles,
        documento_referencia=data.documento_referencia,
        tercero_id=data.tercero_id,
    )

    db.commit()
    db.refresh(asiento)
    return asiento


@router.get("/estado-resultados")
async def estado_resultados(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "contador")),
):
    """
    Estado de Resultados (P&L).
    Ingresos (4xxx), COGS (6xxx), Gastos Operacionales (5xxx).
    Retorna ingresos, gastos, utilidad_bruta y utilidad_neta.
    """
    servicio = ServicioContabilidad(db, ctx.tenant_id)
    return servicio.obtener_estado_resultados(fecha_inicio, fecha_fin)


@router.get("/balance-prueba")
async def balance_prueba(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    tipo: str = Query("acumulado", pattern="^(acumulado|movimientos)$"),
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "contador")),
):
    """
    Genera balance de prueba.
    tipo=acumulado (default): saldos históricos acumulados hasta fecha_fin.
    tipo=movimientos: solo movimientos del período fecha_inicio..fecha_fin.
    """
    servicio = ServicioContabilidad(db, ctx.tenant_id)
    resultados = servicio.obtener_balance_prueba(fecha_inicio, fecha_fin, tipo)

    # Totales
    total_debito = sum(Decimal(r["total_debito"]) for r in resultados)
    total_credito = sum(Decimal(r["total_credito"]) for r in resultados)
    diferencia = total_debito - total_credito

    return {
        "cuentas": resultados,
        "total_debito": str(total_debito),
        "total_credito": str(total_credito),
        "diferencia": str(diferencia),
        "balanceado": abs(diferencia) < Decimal("0.01"),
    }
