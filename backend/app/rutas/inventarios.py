from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from ..datos.db import get_db
from ..datos.modelos import Inventarios, MovimientosInventario, Usuarios
from ..utils.seguridad import get_current_user

router = APIRouter()

@router.get("/")
async def listar(db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    return db.query(Inventarios).all()

@router.get("/producto/{producto_id}")
async def por_producto(producto_id: UUID, db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    inv = db.query(Inventarios).filter(Inventarios.producto_id == producto_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="No encontrado")
    return inv