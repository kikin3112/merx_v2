from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import MediosPago, Usuarios
from ..utils.seguridad import get_current_user, get_tenant_id_from_token

router = APIRouter()


@router.get("/")
async def listar(
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Lista medios de pago activos del tenant."""
    return db.query(MediosPago).filter(
        MediosPago.tenant_id == tenant_id,
        MediosPago.estado == True
    ).all()
