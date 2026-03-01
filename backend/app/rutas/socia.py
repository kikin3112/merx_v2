"""
Rutas de Socia — Gamificación y progreso de artesanas.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import SociaLogroResponse, SociaProgresoResponse
from ..datos.modelos import SociaProgress
from ..utils.logger import setup_logger
from ..utils.seguridad import UserContext, require_tenant_roles

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/progreso", response_model=SociaProgresoResponse)
async def obtener_progreso(
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador", "viewer")),
):
    """Obtiene el nivel y logros actuales de la usuaria."""
    registros = (
        db.query(SociaProgress)
        .filter(
            SociaProgress.tenant_id == ctx.tenant_id,
            SociaProgress.user_id == ctx.user.id,
            SociaProgress.deleted_at.is_(None),
        )
        .all()
    )

    logros = [r.logro_id for r in registros]
    nivel = registros[-1].nivel_actual if registros else "emprendedora"

    return SociaProgresoResponse(nivel_actual=nivel, logros=logros, total_logros=len(logros))


@router.post("/logro/{logro_id}", response_model=SociaLogroResponse, status_code=status.HTTP_201_CREATED)
async def registrar_logro(
    logro_id: str,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador", "viewer")),
):
    """
    Registra un logro desbloqueado por la usuaria.
    Idempotente: si el logro ya existe, retorna el existente sin error.
    """
    existente = (
        db.query(SociaProgress)
        .filter(
            SociaProgress.tenant_id == ctx.tenant_id,
            SociaProgress.user_id == ctx.user.id,
            SociaProgress.logro_id == logro_id,
            SociaProgress.deleted_at.is_(None),
        )
        .first()
    )
    if existente:
        return existente

    nivel = _calcular_nivel(logro_id, db, ctx.tenant_id, ctx.user.id)

    progreso = SociaProgress(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user.id,
        logro_id=logro_id,
        nivel_actual=nivel,
        desbloqueado_en=datetime.now(timezone.utc),
        created_by=ctx.user.id,
        updated_by=ctx.user.id,
    )
    db.add(progreso)
    db.commit()
    db.refresh(progreso)

    safe_logro_id = logro_id.replace("\n", "").replace("\r", "")
    logger.info("Logro desbloqueado", extra={"tenant_id": str(ctx.tenant_id), "logro_id": safe_logro_id})
    return progreso


def _calcular_nivel(nuevo_logro_id: str, db: Session, tenant_id: UUID, user_id: UUID) -> str:
    """Determina el nivel actual basado en los logros acumulados."""
    logros_existentes = {
        r.logro_id
        for r in db.query(SociaProgress.logro_id)
        .filter(
            SociaProgress.tenant_id == tenant_id, SociaProgress.user_id == user_id, SociaProgress.deleted_at.is_(None)
        )
        .all()
    }
    logros_existentes.add(nuevo_logro_id)

    NIVELES = [
        ("empresaria", {"equilibrio_real_mes", "exportar_analisis", "10_producciones"}),
        ("estratega", {"primer_escenario_precio", "primera_sensibilidad", "5_recetas_activas"}),
        ("conocedora", {"primer_cvu", "primer_punto_equilibrio", "primer_costo_indirecto"}),
        ("emprendedora", {"primera_receta", "primer_calculo_costo"}),
    ]

    for nivel, requeridos in NIVELES:
        if requeridos.issubset(logros_existentes):
            return nivel

    return "emprendedora"
