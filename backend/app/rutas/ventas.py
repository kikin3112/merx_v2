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
from ..utils.seguridad import get_current_user
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/", response_model=VentasResponse, status_code=status.HTTP_201_CREATED)
async def crear_nueva_venta(
        venta_data: VentasCreate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Crea una nueva venta.

    **Validaciones automáticas:**
    - Tercero existe y es cliente
    - Productos existen y están activos
    - Inventario suficiente (si aplica)

    **Cálculos automáticos:**
    - Subtotales, descuentos, IVA, total
    - No enviar estos campos en el request

    **Ejemplo request:**
    ```json
    {
        "tercero_id": "uuid-del-cliente",
        "fecha_venta": "2026-01-29",
        "detalles": [
            {
                "producto_id": "uuid-del-producto",
                "cantidad": 5,
                "precio_unitario": 10000,
                "descuento": 500,
                "porcentaje_iva": 19
            }
        ]
    }
    ```
    """
    try:
        nueva_venta = crear_venta(db, venta_data)
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
        skip: int = Query(0, ge=0, description="Registros a saltar"),
        limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
        tercero_id: Optional[UUID] = Query(None, description="Filtrar por cliente"),
        estado: Optional[str] = Query(None, description="Filtrar por estado"),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Lista ventas con filtros opcionales.

    **Filtros disponibles:**
    - `tercero_id`: Ventas de un cliente específico
    - `estado`: PENDIENTE, CONFIRMADA, FACTURADA, ANULADA

    **Paginación:**
    - `skip`: Número de registros a saltar (default: 0)
    - `limit`: Máximo de registros (default: 100, max: 1000)
    """
    ventas = listar_ventas(
        db,
        skip=skip,
        limit=limit,
        tercero_id=tercero_id,
        estado=estado
    )

    return [VentasResponse.model_validate(v) for v in ventas]


@router.get("/estadisticas", response_model=dict)
async def obtener_estadisticas(
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Obtiene estadísticas de ventas.

    **Retorna:**
    ```json
    {
        "total_ventas": 150,
        "total_monto": 5000000.00,
        "promedio_venta": 33333.33,
        "por_estado": {
            "CONFIRMADA": {"cantidad": 120, "monto": 4200000.00},
            "PENDIENTE": {"cantidad": 30, "monto": 800000.00}
        }
    }
    ```
    """
    # TODO: Agregar filtros de fecha cuando sea necesario
    return obtener_estadisticas_ventas(db)


@router.get("/{venta_id}", response_model=VentasResponse)
async def obtener_venta_endpoint(
        venta_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Obtiene una venta por ID.

    **Incluye:**
    - Datos completos de la venta
    - Detalles con productos
    - Totales calculados
    """
    venta = obtener_venta(db, venta_id)
    return VentasResponse.model_validate(venta)


@router.patch("/{venta_id}", response_model=VentasResponse)
async def actualizar_venta_endpoint(
        venta_id: UUID,
        venta_data: VentasUpdate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Actualiza una venta existente.

    **Campos actualizables:**
    - `estado`: Cambiar estado de la venta
    - `observaciones`: Modificar observaciones

    **Restricciones:**
    - No se puede modificar una venta anulada
    - No se puede anular una venta facturada (usar endpoint específico)
    """
    try:
        venta = actualizar_venta(db, venta_id, venta_data)
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
        logger.warning(f"Validación fallida al actualizar venta: {str(e)}")
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
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Confirma una venta (PENDIENTE → CONFIRMADA).

    **Efectos:**
    - Cambia estado a CONFIRMADA
    - Genera movimientos de inventario
    - Registra asiento contable (si aplica)
    """
    try:
        venta = confirmar_venta(db, venta_id)
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
        motivo: Optional[str] = Query(None, description="Motivo de anulación"),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Anula una venta.

    **Efectos:**
    - Cambia estado a ANULADA
    - Revierte movimientos de inventario
    - Registra asiento contable de anulación (si aplica)

    **Restricciones:**
    - No se puede anular una venta facturada
    - Requiere motivo (recomendado)
    """
    try:
        venta = anular_venta(db, venta_id, motivo)
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