from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.esquemas import VentasCreate, VentasUpdate, VentasResponse
from ..datos.modelos import Usuarios
from ..servicios.servicio_ventas import (
    crear_venta,
    listar_ventas,
    obtener_venta,
    actualizar_venta,
    anular_venta,
    confirmar_venta,
    obtener_estadisticas_ventas
)
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/", response_model=VentasResponse, status_code=status.HTTP_201_CREATED)
async def crear_nueva_venta(
        venta_data: VentasCreate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Crea una nueva venta."""
    try:
        nueva_venta = crear_venta(db, venta_data, tenant_id)
        db.commit()

        logger.info(
            f"Venta creada: {nueva_venta.numero_venta}",
            extra={
                "venta_id": str(nueva_venta.id),
                "total": float(nueva_venta.total_venta),
                "user_id": str(current_user.id)
            }
        )

        return VentasResponse.model_validate(nueva_venta)

    except ValueError as e:
        logger.warning(f"Validación fallida al crear venta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error("Error creando venta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la venta"
        )


@router.get("/", response_model=List[VentasResponse])
async def listar_ventas_endpoint(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        tercero_id: Optional[UUID] = Query(None),
        estado: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Lista ventas con filtros opcionales."""
    ventas = listar_ventas(
        db,
        tenant_id=tenant_id,
        skip=skip,
        limit=limit,
        tercero_id=tercero_id,
        estado=estado
    )

    return [VentasResponse.model_validate(v) for v in ventas]


@router.get("/estadisticas", response_model=dict)
async def obtener_estadisticas(
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene estadísticas de ventas."""
    return obtener_estadisticas_ventas(db, tenant_id)


@router.get("/{venta_id}", response_model=VentasResponse)
async def obtener_venta_endpoint(
        venta_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Obtiene una venta por ID."""
    venta = obtener_venta(db, venta_id, tenant_id)
    return VentasResponse.model_validate(venta)


@router.patch("/{venta_id}", response_model=VentasResponse)
async def actualizar_venta_endpoint(
        venta_id: UUID,
        venta_data: VentasUpdate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Actualiza una venta existente."""
    try:
        venta = actualizar_venta(db, venta_id, venta_data, tenant_id)
        db.commit()

        logger.info(
            f"Venta actualizada: {venta.numero_venta}",
            extra={
                "venta_id": str(venta.id),
                "user_id": str(current_user.id)
            }
        )

        return VentasResponse.model_validate(venta)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error actualizando venta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar la venta"
        )


@router.post("/{venta_id}/confirmar", response_model=VentasResponse)
async def confirmar_venta_endpoint(
        venta_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Confirma una venta (PENDIENTE -> CONFIRMADA). Descuenta inventario."""
    try:
        venta = confirmar_venta(db, venta_id, tenant_id)
        db.commit()

        logger.info(
            f"Venta confirmada: {venta.numero_venta}",
            extra={
                "venta_id": str(venta.id),
                "user_id": str(current_user.id)
            }
        )

        return VentasResponse.model_validate(venta)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error confirmando venta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al confirmar la venta"
        )


@router.post("/{venta_id}/anular", response_model=VentasResponse)
async def anular_venta_endpoint(
        venta_id: UUID,
        motivo: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user),
        tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Anula una venta. Revierte inventario si estaba confirmada."""
    try:
        venta = anular_venta(db, venta_id, tenant_id, motivo)
        db.commit()

        logger.warning(
            f"Venta anulada: {venta.numero_venta}",
            extra={
                "venta_id": str(venta.id),
                "motivo": motivo,
                "user_id": str(current_user.id)
            }
        )

        return VentasResponse.model_validate(venta)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error anulando venta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al anular la venta"
        )
