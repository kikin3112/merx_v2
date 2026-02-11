from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import AsientosContables, Usuarios
from ..utils.seguridad import get_current_user, get_tenant_id_from_token

router = APIRouter()


@router.get("/asientos")
async def listar_asientos(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Lista asientos contables del tenant."""
    return db.query(AsientosContables).filter(
        AsientosContables.tenant_id == tenant_id
    ).order_by(AsientosContables.fecha.desc()).offset(skip).limit(limit).all()
