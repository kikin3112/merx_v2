"""
Rutas para gestión de Costos Indirectos — módulo Socia.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import CostoIndirectoCreate, CostoIndirectoResponse, CostoIndirectoUpdate
from ..datos.modelos import TipoCostoIndirecto
from ..servicios.servicio_costos_indirectos import ServicioCostosIndirectos
from ..utils.logger import setup_logger
from ..utils.seguridad import UserContext, require_tenant_roles

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/", response_model=List[CostoIndirectoResponse])
async def listar_costos_indirectos(
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """Lista todos los costos indirectos del tenant."""
    servicio = ServicioCostosIndirectos(db=db, tenant_id=ctx.tenant_id)
    return servicio.listar(solo_activos=solo_activos)


@router.post("/", response_model=CostoIndirectoResponse, status_code=status.HTTP_201_CREATED)
async def crear_costo_indirecto(
    data: CostoIndirectoCreate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin")),
):
    """Crea un nuevo costo indirecto."""
    servicio = ServicioCostosIndirectos(db=db, tenant_id=ctx.tenant_id)
    tipo = TipoCostoIndirecto(data.tipo)
    return servicio.crear(nombre=data.nombre, monto=data.monto, tipo=tipo, user_id=ctx.user.id)


@router.get("/{costo_id}", response_model=CostoIndirectoResponse)
async def obtener_costo_indirecto(
    costo_id: UUID,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """Obtiene un costo indirecto por ID."""
    servicio = ServicioCostosIndirectos(db=db, tenant_id=ctx.tenant_id)
    costo = servicio.obtener(costo_id)
    if not costo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Costo indirecto no encontrado")
    return costo


@router.put("/{costo_id}", response_model=CostoIndirectoResponse)
async def actualizar_costo_indirecto(
    costo_id: UUID,
    data: CostoIndirectoUpdate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin")),
):
    """Actualiza un costo indirecto existente."""
    servicio = ServicioCostosIndirectos(db=db, tenant_id=ctx.tenant_id)
    tipo = TipoCostoIndirecto(data.tipo) if data.tipo else None
    try:
        return servicio.actualizar(
            costo_id=costo_id,
            nombre=data.nombre,
            monto=data.monto,
            tipo=tipo,
            activo=data.activo,
            user_id=ctx.user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{costo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_costo_indirecto(
    costo_id: UUID,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin")),
):
    """Elimina (soft delete) un costo indirecto."""
    servicio = ServicioCostosIndirectos(db=db, tenant_id=ctx.tenant_id)
    try:
        servicio.eliminar(costo_id=costo_id, user_id=ctx.user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
