from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import Productos, Usuarios
from ..datos.esquemas import ProductoCreate, ProductoUpdate, ProductoResponse
from ..utils.seguridad import get_current_user
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto(
        producto_data: ProductoCreate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Crea un nuevo producto.

    **Validaciones:**
    - Código interno único
    - Código de barras único (si se proporciona)
    - Categoría válida: Insumo, Producto_Propio, Producto_Tercero, Servicio

    **Permisos:** Solo admin y operador
    """
    # Validar permisos
    if current_user.rol not in ['admin', 'operador']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear productos"
        )

    # Validar código interno único
    existing = db.query(Productos).filter(
        Productos.codigo_interno == producto_data.codigo_interno
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un producto con código interno '{producto_data.codigo_interno}'"
        )

    # Validar código de barras único (si se proporciona)
    if producto_data.codigo_barras:
        existing_barcode = db.query(Productos).filter(
            Productos.codigo_barras == producto_data.codigo_barras
        ).first()

        if existing_barcode:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto con código de barras '{producto_data.codigo_barras}'"
            )

    try:
        # Crear producto
        nuevo_producto = Productos(**producto_data.model_dump())
        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)

        logger.info(
            f"Producto creado: {nuevo_producto.nombre}",
            extra={
                "producto_id": str(nuevo_producto.id),
                "codigo": nuevo_producto.codigo_interno,
                "user_id": str(current_user.id)
            }
        )

        return ProductoResponse.model_validate(nuevo_producto)

    except Exception as e:
        db.rollback()
        logger.error("Error creando producto", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el producto"
        )


@router.get("/", response_model=List[ProductoResponse])
async def listar_productos(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        categoria: Optional[str] = Query(None, description="Insumo, Producto_Propio, Producto_Tercero, Servicio"),
        estado: Optional[bool] = Query(None),
        maneja_inventario: Optional[bool] = Query(None),
        busqueda: Optional[str] = Query(None, min_length=2, description="Buscar por nombre o código"),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Lista productos con filtros y búsqueda.

    **Filtros:**
    - `categoria`: Filtrar por categoría
    - `estado`: true (activos) / false (inactivos)
    - `maneja_inventario`: true / false
    - `busqueda`: Busca en nombre y código interno

    **Paginación:**
    - `skip`: Registros a saltar
    - `limit`: Máximo de registros (default 100, max 1000)
    """
    query = db.query(Productos)

    # Aplicar filtros
    if categoria:
        query = query.filter(Productos.categoria == categoria)

    if estado is not None:
        query = query.filter(Productos.estado == estado)

    if maneja_inventario is not None:
        query = query.filter(Productos.maneja_inventario == maneja_inventario)

    if busqueda:
        search_pattern = f"%{busqueda}%"
        query = query.filter(
            (Productos.nombre.ilike(search_pattern)) |
            (Productos.codigo_interno.ilike(search_pattern))
        )

    # Ordenar y paginar
    productos = (
        query
        .order_by(Productos.nombre)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [ProductoResponse.model_validate(p) for p in productos]


@router.get("/categorias/{categoria}", response_model=List[ProductoResponse])
async def listar_por_categoria(
        categoria: str,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        solo_activos: bool = Query(True),
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Lista productos de una categoría específica.

    **Categorías válidas:**
    - Insumo
    - Producto_Propio
    - Producto_Tercero
    - Servicio

    **Uso común:**
    - `/productos/categorias/Insumo` - Para ordenes de producción
    - `/productos/categorias/Producto_Propio` - Para ventas
    """
    # Validar categoría
    categorias_validas = ['Insumo', 'Producto_Propio', 'Producto_Tercero', 'Servicio']
    if categoria not in categorias_validas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoría inválida. Válidas: {', '.join(categorias_validas)}"
        )

    query = db.query(Productos).filter(Productos.categoria == categoria)

    if solo_activos:
        query = query.filter(Productos.estado == True)

    productos = (
        query
        .order_by(Productos.nombre)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [ProductoResponse.model_validate(p) for p in productos]


@router.get("/{producto_id}", response_model=ProductoResponse)
async def obtener_producto(
        producto_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Obtiene un producto por ID.

    **Incluye:**
    - Datos completos del producto
    - Información de inventario (si aplica)
    """
    producto = db.query(Productos).filter(Productos.id == producto_id).first()

    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )

    return ProductoResponse.model_validate(producto)


@router.patch("/{producto_id}", response_model=ProductoResponse)
async def actualizar_producto(
        producto_id: UUID,
        producto_data: ProductoUpdate,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Actualiza un producto existente.

    **Campos actualizables:**
    - Todos excepto `codigo_interno` y `categoria`

    **Permisos:** Solo admin y operador
    """
    # Validar permisos
    if current_user.rol not in ['admin', 'operador']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar productos"
        )

    # Buscar producto
    producto = db.query(Productos).filter(Productos.id == producto_id).first()

    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )

    try:
        # Actualizar solo campos proporcionados
        update_data = producto_data.model_dump(exclude_unset=True)

        # Validar código de barras único (si se está cambiando)
        if 'codigo_barras' in update_data and update_data['codigo_barras']:
            existing = db.query(Productos).filter(
                Productos.codigo_barras == update_data['codigo_barras'],
                Productos.id != producto_id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Código de barras '{update_data['codigo_barras']}' ya existe en otro producto"
                )

        for field, value in update_data.items():
            setattr(producto, field, value)

        db.commit()
        db.refresh(producto)

        logger.info(
            f"Producto actualizado: {producto.nombre}",
            extra={
                "producto_id": str(producto.id),
                "user_id": str(current_user.id)
            }
        )

        return ProductoResponse.model_validate(producto)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error actualizando producto", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar el producto"
        )


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_producto(
        producto_id: UUID,
        db: Session = Depends(get_db),
        current_user: Usuarios = Depends(get_current_user)
):
    """
    Elimina un producto (soft delete).

    **Nota:** No se elimina físicamente, solo se marca como inactivo.

    **Permisos:** Solo admin
    """
    # Solo admin puede eliminar
    if current_user.rol != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar productos"
        )

    producto = db.query(Productos).filter(Productos.id == producto_id).first()

    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )

    try:
        # Soft delete
        producto.estado = False
        db.commit()

        logger.warning(
            f"Producto eliminado (soft): {producto.nombre}",
            extra={
                "producto_id": str(producto.id),
                "user_id": str(current_user.id)
            }
        )

    except Exception as e:
        db.rollback()
        logger.error("Error eliminando producto", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar el producto"
        )