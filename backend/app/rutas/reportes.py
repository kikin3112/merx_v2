from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..datos.db import get_db
from ..datos.modelos import Ventas, Compras, Usuarios
from ..utils.seguridad import get_current_user

router = APIRouter()

@router.get("/ventas")
async def reporte_ventas(db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    total = db.query(func.sum(Ventas.total_venta)).scalar() or 0
    count = db.query(func.count(Ventas.id)).scalar() or 0
    return {"total_ventas": float(total), "cantidad": count}

@router.get("/compras")
async def reporte_compras(db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    total = db.query(func.sum(Compras.total_compra)).scalar() or 0
    count = db.query(func.count(Compras.id)).scalar() or 0
    return {"total_compras": float(total), "cantidad": count}