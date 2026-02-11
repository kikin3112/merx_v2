from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..datos.db import get_db
from ..datos.modelos import CuentasContables, Usuarios
from ..utils.seguridad import get_current_user

router = APIRouter()

@router.get("/")
async def listar(db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    return db.query(CuentasContables).order_by(CuentasContables.codigo).all()