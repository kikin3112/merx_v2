from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.modelos import AsientosContables, PeriodosContables
from ..servicios.servicio_audit import ServicioAuditLog
from ..utils.logger import setup_logger
from ..utils.seguridad import UserContext, require_tenant_roles

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/")
async def listar_periodos(
    db: Session = Depends(get_db), ctx: UserContext = Depends(require_tenant_roles("admin", "contador"))
):
    """Lista períodos contables del tenant con conteo de asientos."""
    periodos = (
        db.query(PeriodosContables, func.count(AsientosContables.id).label("total_asientos"))
        .outerjoin(
            AsientosContables,
            (AsientosContables.periodo_id == PeriodosContables.id) & (AsientosContables.estado == "ACTIVO"),
        )
        .filter(PeriodosContables.tenant_id == ctx.tenant_id)
        .group_by(PeriodosContables.id)
        .order_by(PeriodosContables.anio.desc(), PeriodosContables.mes.desc())
        .all()
    )

    result = []
    for periodo, total_asientos in periodos:
        result.append(
            {
                "id": periodo.id,
                "anio": periodo.anio,
                "mes": periodo.mes,
                "estado": periodo.estado,
                "fecha_cierre": periodo.fecha_cierre,
                "total_asientos": total_asientos,
                "created_at": periodo.created_at,
                "updated_at": periodo.updated_at,
            }
        )

    return result


@router.post("/{anio}/{mes}/cerrar")
async def cerrar_periodo(
    anio: int, mes: int, db: Session = Depends(get_db), ctx: UserContext = Depends(require_tenant_roles("admin"))
):
    """Cierra un período contable. Solo admin."""
    if mes < 1 or mes > 12:
        raise HTTPException(status_code=400, detail="Mes debe estar entre 1 y 12")

    periodo = (
        db.query(PeriodosContables)
        .filter(
            PeriodosContables.tenant_id == ctx.tenant_id, PeriodosContables.anio == anio, PeriodosContables.mes == mes
        )
        .first()
    )

    if not periodo:
        raise HTTPException(status_code=404, detail=f"Período {mes}/{anio} no encontrado")

    if periodo.estado == "CERRADO":
        raise HTTPException(status_code=400, detail=f"El período {mes}/{anio} ya está cerrado")

    periodo.estado = "CERRADO"
    periodo.fecha_cierre = datetime.now(timezone.utc)
    periodo.cerrado_por = ctx.user.id

    db.commit()
    db.refresh(periodo)

    total_asientos = (
        db.query(func.count(AsientosContables.id))
        .filter(AsientosContables.periodo_id == periodo.id, AsientosContables.estado == "ACTIVO")
        .scalar()
    )

    return {
        "id": periodo.id,
        "anio": periodo.anio,
        "mes": periodo.mes,
        "estado": periodo.estado,
        "fecha_cierre": periodo.fecha_cierre,
        "total_asientos": total_asientos,
        "created_at": periodo.created_at,
        "updated_at": periodo.updated_at,
    }


@router.post("/{anio}/{mes}/reabrir")
async def reabrir_periodo(
    anio: int, mes: int, db: Session = Depends(get_db), ctx: UserContext = Depends(require_tenant_roles("admin"))
):
    """Reabre un período contable cerrado. Solo admin."""
    if mes < 1 or mes > 12:
        raise HTTPException(status_code=400, detail="Mes debe estar entre 1 y 12")

    periodo = (
        db.query(PeriodosContables)
        .filter(
            PeriodosContables.tenant_id == ctx.tenant_id, PeriodosContables.anio == anio, PeriodosContables.mes == mes
        )
        .first()
    )

    if not periodo:
        raise HTTPException(status_code=404, detail=f"Período {mes}/{anio} no encontrado")

    if periodo.estado == "ABIERTO":
        raise HTTPException(status_code=400, detail=f"El período {mes}/{anio} ya está abierto")

    periodo.estado = "ABIERTO"
    periodo.fecha_cierre = None
    periodo.cerrado_por = None

    db.commit()
    db.refresh(periodo)

    # A-07: Registrar auditoría de reapertura
    svc_audit = ServicioAuditLog(db)
    svc_audit.registrar(
        actor_id=ctx.user.id,
        actor_email=ctx.user.email,
        action="REABRIR_PERIODO",
        resource_type="periodos_contables",
        resource_id=periodo.id,
        tenant_id=ctx.tenant_id,
        changes={"anio": anio, "mes": mes, "estado_nuevo": "ABIERTO"},
    )

    total_asientos = (
        db.query(func.count(AsientosContables.id))
        .filter(AsientosContables.periodo_id == periodo.id, AsientosContables.estado == "ACTIVO")
        .scalar()
    )

    return {
        "id": periodo.id,
        "anio": periodo.anio,
        "mes": periodo.mes,
        "estado": periodo.estado,
        "fecha_cierre": periodo.fecha_cierre,
        "total_asientos": total_asientos,
        "created_at": periodo.created_at,
        "updated_at": periodo.updated_at,
    }
