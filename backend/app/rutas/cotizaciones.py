from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..datos.db import get_db
from ..datos.modelos import Cotizaciones, Usuarios
from ..utils.seguridad import get_current_user
from ..utils.secuencia_helper import generar_numero_secuencia

router = APIRouter()

@router.get("/")
async def listar(db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    return db.query(Cotizaciones).all()

@router.post("/")
async def crear(db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    numero = generar_numero_secuencia(db, 'COTIZACIONES')
    cot = Cotizaciones(numero_cotizacion=numero, estado="PENDIENTE")
    db.add(cot)
    db.commit()
    return cot