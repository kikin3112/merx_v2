from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import Compras, ComprasDetalle, Terceros, Productos, Usuarios
from ..datos.esquemas import ComprasCreate, ComprasUpdate, ComprasResponse
from ..utils.seguridad import get_current_user
from ..utils.logger import setup_logger
from ..utils.secuencia_helper import generar_numero_secuencia

router = APIRouter()
logger = setup_logger(__name__)

@router.post("/", response_model=ComprasResponse, status_code=status.HTTP_201_CREATED)
async def crear_compra(compra_data: ComprasCreate, db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    tercero = db.query(Terceros).filter(Terceros.id == compra_data.tercero_id).first()
    if not tercero or tercero.tipo_tercero not in ('PROVEEDOR', 'AMBOS'):
        raise HTTPException(status_code=400, detail="Tercero debe ser proveedor")
    try:
        numero = generar_numero_secuencia(db, 'COMPRAS')
        compra = Compras(numero_compra=numero, tercero_id=compra_data.tercero_id, fecha_compra=compra_data.fecha_compra, estado="PENDIENTE")
        db.add(compra)
        db.flush()
        for det in compra_data.detalles:
            detalle = ComprasDetalle(compra_id=compra.id, producto_id=det.producto_id, cantidad=det.cantidad, precio_unitario=det.precio_unitario, descuento=det.descuento or 0, porcentaje_iva=det.porcentaje_iva or 0)
            db.add(detalle)
        db.commit()
        db.refresh(compra)
        logger.info(f"Compra creada: {compra.numero_compra}")
        return ComprasResponse.model_validate(compra)
    except Exception as e:
        db.rollback()
        logger.error("Error creando compra", exc_info=e)
        raise HTTPException(status_code=500, detail="Error interno")

@router.get("/", response_model=List[ComprasResponse])
async def listar_compras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    return [ComprasResponse.model_validate(c) for c in db.query(Compras).offset(skip).limit(limit).all()]

@router.get("/{compra_id}", response_model=ComprasResponse)
async def obtener_compra(compra_id: UUID, db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)):
    compra = db.query(Compras).filter(Compras.id == compra_id).first()
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    return ComprasResponse.model_validate(compra)