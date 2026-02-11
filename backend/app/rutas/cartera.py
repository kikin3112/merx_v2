from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..datos.db import get_db
from ..datos.modelos import CuentasPorCobrar, CuentasPorPagar, Usuarios
from ..utils.seguridad import get_current_user

router = APIRouter()

@router.get("/cuentas-por-cobrar")
async def listar_cxc(db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    return db.query(CuentasPorCobrar).all()

@router.get("/cuentas-por-pagar")
async def listar_cxp(db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    return db.query(CuentasPorPagar).all()