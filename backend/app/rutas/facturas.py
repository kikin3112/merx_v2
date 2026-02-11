from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import Usuarios
from ..utils.seguridad import get_current_user, get_tenant_id_from_token

router = APIRouter()


@router.get("/")
async def listar(
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Módulo de facturación - pendiente de implementación completa."""
    return {"message": "Módulo de facturación en desarrollo", "tenant_id": str(tenant_id)}
