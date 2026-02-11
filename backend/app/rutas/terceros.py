from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import Terceros, Usuarios
from ..datos.esquemas import TerceroCreate, TerceroUpdate, TerceroResponse
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/", response_model=TerceroResponse, status_code=status.HTTP_201_CREATED)
async def crear_tercero(
        tercero_data: TerceroCreate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Crea un nuevo tercero."""
    if current_user.rol not in ['admin', 'operador']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos")

    existing = db.query(Terceros).filter(
        Terceros.tenant_id == tenant_id,
        Terceros.numero_documento == tercero_data.numero_documento
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Documento {tercero_data.numero_documento} ya existe"
        )

    try:
        nuevo_tercero = Terceros(tenant_id=tenant_id, **tercero_data.model_dump())
        db.add(nuevo_tercero)
        db.commit()
        db.refresh(nuevo_tercero)
        logger.info(f"Tercero creado: {nuevo_tercero.nombre}", extra={"tercero_id": str(nuevo_tercero.id)})
        return TerceroResponse.model_validate(nuevo_tercero)
    except Exception as e:
        db.rollback()
        logger.error("Error creando tercero", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno")


@router.get("/", response_model=List[TerceroResponse])
async def listar_terceros(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        tipo_tercero: Optional[str] = Query(None),
        estado: Optional[bool] = Query(None),
        busqueda: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Lista terceros con filtros opcionales."""
    query = db.query(Terceros).filter(Terceros.tenant_id == tenant_id)
    if tipo_tercero:
        query = query.filter(Terceros.tipo_tercero == tipo_tercero)
    if estado is not None:
        query = query.filter(Terceros.estado == estado)
    if busqueda:
        search = f"%{busqueda}%"
        query = query.filter((Terceros.nombre.ilike(search)) | (Terceros.numero_documento.ilike(search)))
    return [TerceroResponse.model_validate(t) for t in query.order_by(Terceros.nombre).offset(skip).limit(limit).all()]


@router.get("/{tercero_id}", response_model=TerceroResponse)
async def obtener_tercero(
        tercero_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene un tercero por ID."""
    tercero = db.query(Terceros).filter(
        Terceros.id == tercero_id,
        Terceros.tenant_id == tenant_id
    ).first()
    if not tercero:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tercero no encontrado")
    return TerceroResponse.model_validate(tercero)


@router.patch("/{tercero_id}", response_model=TerceroResponse)
async def actualizar_tercero(
        tercero_id: UUID,
        tercero_data: TerceroUpdate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Actualiza un tercero existente."""
    if current_user.rol not in ['admin', 'operador']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos")

    tercero = db.query(Terceros).filter(
        Terceros.id == tercero_id,
        Terceros.tenant_id == tenant_id
    ).first()
    if not tercero:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tercero no encontrado")

    try:
        for field, value in tercero_data.model_dump(exclude_unset=True).items():
            setattr(tercero, field, value)
        db.commit()
        db.refresh(tercero)
        logger.info(f"Tercero actualizado: {tercero.nombre}")
        return TerceroResponse.model_validate(tercero)
    except Exception as e:
        db.rollback()
        logger.error("Error actualizando tercero", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno")


@router.delete("/{tercero_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_tercero(
        tercero_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Elimina un tercero (soft delete)."""
    if current_user.rol != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo admin")
    tercero = db.query(Terceros).filter(
        Terceros.id == tercero_id,
        Terceros.tenant_id == tenant_id
    ).first()
    if not tercero:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tercero no encontrado")
    tercero.estado = False
    db.commit()
    logger.warning(f"Tercero eliminado: {tercero.nombre}")
