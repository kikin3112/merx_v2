import base64
import json
import re
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from ..datos.db import get_db
from ..datos.esquemas import (
    EquivalenciaUnidadCreate,
    EquivalenciaUnidadResponse,
    ProductoCreate,
    ProductoResponse,
    ProductoUpdate,
)
from ..datos.modelos import ProductoEquivalenciaUnidad, Productos, Usuarios
from ..utils.logger import setup_logger
from ..utils.seguridad import UserContext, get_current_user, get_tenant_id_from_token, require_tenant_roles

router = APIRouter()
logger = setup_logger(__name__)

SKU_PREFIXES = {
    "Insumo": "INS",
    "Producto_Propio": "PPRO",
    "Producto_Tercero": "PTER",
    "Servicio": "SERV",
}


@router.get("/siguiente-codigo")
async def obtener_siguiente_codigo(
    categoria: str = Query(..., description="Categoría del producto"),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Genera el siguiente código interno disponible para una categoría."""
    categorias_validas = ["Insumo", "Producto_Propio", "Producto_Tercero", "Servicio"]
    if categoria not in categorias_validas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoría inválida. Válidas: {', '.join(categorias_validas)}",
        )

    prefix = SKU_PREFIXES.get(categoria, "INS")

    ultimo_producto = (
        db.query(Productos.codigo_interno)
        .filter(Productos.tenant_id == tenant_id, Productos.codigo_interno.like(f"{prefix}-%"))
        .order_by(Productos.codigo_interno.desc())
        .first()
    )

    siguiente_numero = 1
    if ultimo_producto:
        match = re.search(r"(\d+)$", ultimo_producto[0])
        if match:
            siguiente_numero = int(match.group(1)) + 1

    nuevo_codigo = f"{prefix}-{siguiente_numero:04d}"

    return {"codigo_interno": nuevo_codigo}


@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    producto_data: ProductoCreate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """Crea un nuevo producto."""
    # Validar código interno único dentro del tenant
    existing = (
        db.query(Productos)
        .filter(Productos.tenant_id == ctx.tenant_id, Productos.codigo_interno == producto_data.codigo_interno)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un producto con código interno '{producto_data.codigo_interno}'",
        )

    # Validar código de barras único dentro del tenant
    if producto_data.codigo_barras:
        existing_barcode = (
            db.query(Productos)
            .filter(Productos.tenant_id == ctx.tenant_id, Productos.codigo_barras == producto_data.codigo_barras)
            .first()
        )

        if existing_barcode:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto con código de barras '{producto_data.codigo_barras}'",
            )

    try:
        nuevo_producto = Productos(tenant_id=ctx.tenant_id, **producto_data.model_dump())
        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)

        logger.info(
            f"Producto creado: {nuevo_producto.nombre}",
            extra={
                "producto_id": str(nuevo_producto.id),
                "codigo": nuevo_producto.codigo_interno,
                "user_id": str(ctx.user.id),
            },
        )

        return ProductoResponse.model_validate(nuevo_producto)

    except Exception as e:
        db.rollback()
        logger.error("Error creando producto", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear el producto"
        )


@router.get("/", response_model=List[ProductoResponse])
async def listar_productos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    categoria: Optional[str] = Query(None),
    estado: Optional[bool] = Query(None),
    maneja_inventario: Optional[bool] = Query(None),
    busqueda: Optional[str] = Query(None, min_length=2),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Lista productos con filtros y búsqueda."""
    query = (
        db.query(Productos)
        .options(selectinload(Productos.created_by_user), selectinload(Productos.updated_by_user))
        .filter(Productos.tenant_id == tenant_id)
    )

    if categoria:
        query = query.filter(Productos.categoria == categoria)

    if estado is not None:
        query = query.filter(Productos.estado == estado)

    if maneja_inventario is not None:
        query = query.filter(Productos.maneja_inventario == maneja_inventario)

    if busqueda:
        search_pattern = f"%{busqueda}%"
        query = query.filter(
            (Productos.nombre.ilike(search_pattern)) | (Productos.codigo_interno.ilike(search_pattern))
        )

    productos = query.order_by(Productos.nombre).offset(skip).limit(limit).all()

    return [ProductoResponse.model_validate(p) for p in productos]


@router.get("/categorias/{categoria}", response_model=List[ProductoResponse])
async def listar_por_categoria(
    categoria: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Lista productos de una categoría específica."""
    categorias_validas = ["Insumo", "Producto_Propio", "Producto_Tercero", "Servicio"]
    if categoria not in categorias_validas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoría inválida. Válidas: {', '.join(categorias_validas)}",
        )

    query = (
        db.query(Productos)
        .options(selectinload(Productos.created_by_user), selectinload(Productos.updated_by_user))
        .filter(Productos.tenant_id == tenant_id, Productos.categoria == categoria)
    )

    if solo_activos:
        query = query.filter(Productos.estado)

    productos = query.order_by(Productos.nombre).offset(skip).limit(limit).all()

    return [ProductoResponse.model_validate(p) for p in productos]


@router.get("/paginado", response_model=dict)
async def listar_productos_cursor(
    cursor: Optional[str] = Query(None, description="Cursor opaco de paginación (base64)"),
    limit: int = Query(50, ge=1, le=200),
    categoria: Optional[str] = Query(None),
    estado: Optional[bool] = Query(None),
    busqueda: Optional[str] = Query(None, min_length=2),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """
    Lista productos con paginación por cursor (keyset pagination).
    Garantiza consistencia al insertar/eliminar registros concurrentemente.

    El cursor codifica la posición (nombre, id) del último ítem retornado.
    Retorna: { items: [...], next_cursor: str | null, has_more: bool }
    """
    query = (
        db.query(Productos).options(selectinload(Productos.created_by_user)).filter(Productos.tenant_id == tenant_id)
    )

    if categoria:
        query = query.filter(Productos.categoria == categoria)
    if estado is not None:
        query = query.filter(Productos.estado == estado)
    if busqueda:
        pattern = f"%{busqueda}%"
        query = query.filter((Productos.nombre.ilike(pattern)) | (Productos.codigo_interno.ilike(pattern)))

    # Decodificar cursor si existe
    if cursor:
        try:
            raw = base64.urlsafe_b64decode(cursor.encode()).decode()
            pos = json.loads(raw)
            cursor_nombre = pos["nombre"]
            cursor_id = pos["id"]
            # Keyset: (nombre > cursor_nombre) OR (nombre == cursor_nombre AND id > cursor_id)
            from sqlalchemy import and_, or_

            query = query.filter(
                or_(
                    Productos.nombre > cursor_nombre,
                    and_(Productos.nombre == cursor_nombre, Productos.id > cursor_id),
                )
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Cursor inválido")

    items = query.order_by(Productos.nombre, Productos.id).limit(limit + 1).all()

    has_more = len(items) > limit
    page_items = items[:limit]

    next_cursor = None
    if has_more and page_items:
        last = page_items[-1]
        pos = {"nombre": last.nombre, "id": str(last.id)}
        next_cursor = base64.urlsafe_b64encode(json.dumps(pos).encode()).decode()

    return {
        "items": [ProductoResponse.model_validate(p) for p in page_items],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get("/{producto_id}", response_model=ProductoResponse)
async def obtener_producto(
    producto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Obtiene un producto por ID."""
    producto = (
        db.query(Productos)
        .options(selectinload(Productos.created_by_user), selectinload(Productos.updated_by_user))
        .filter(Productos.id == producto_id, Productos.tenant_id == tenant_id)
        .first()
    )

    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto con ID {producto_id} no encontrado"
        )

    return ProductoResponse.model_validate(producto)


@router.patch("/{producto_id}", response_model=ProductoResponse)
async def actualizar_producto(
    producto_id: UUID,
    producto_data: ProductoUpdate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """Actualiza un producto existente."""
    producto = db.query(Productos).filter(Productos.id == producto_id, Productos.tenant_id == ctx.tenant_id).first()

    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto con ID {producto_id} no encontrado"
        )

    try:
        update_data = producto_data.model_dump(exclude_unset=True)

        if "codigo_barras" in update_data and update_data["codigo_barras"]:
            existing = (
                db.query(Productos)
                .filter(
                    Productos.tenant_id == ctx.tenant_id,
                    Productos.codigo_barras == update_data["codigo_barras"],
                    Productos.id != producto_id,
                )
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Código de barras '{update_data['codigo_barras']}' ya existe en otro producto",
                )

        for field, value in update_data.items():
            setattr(producto, field, value)

        db.commit()
        db.refresh(producto)

        logger.info(
            f"Producto actualizado: {producto.nombre}",
            extra={"producto_id": str(producto.id), "user_id": str(ctx.user.id)},
        )

        return ProductoResponse.model_validate(producto)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error actualizando producto", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al actualizar el producto"
        )


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_producto(
    producto_id: UUID, db: Session = Depends(get_db), ctx: UserContext = Depends(require_tenant_roles("admin"))
):
    """Elimina un producto (soft delete). Solo admin."""
    producto = db.query(Productos).filter(Productos.id == producto_id, Productos.tenant_id == ctx.tenant_id).first()

    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto con ID {producto_id} no encontrado"
        )

    try:
        producto.estado = False
        db.commit()

        logger.warning(
            f"Producto eliminado (soft): {producto.nombre}",
            extra={"producto_id": str(producto.id), "user_id": str(ctx.user.id)},
        )

    except Exception as e:
        db.rollback()
        logger.error("Error eliminando producto", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al eliminar el producto"
        )


# ============================================================================
# EQUIVALENCIAS DE UNIDAD POR PRODUCTO
# ============================================================================


@router.get("/{producto_id}/equivalencias", response_model=List[EquivalenciaUnidadResponse])
async def listar_equivalencias(
    producto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Lista todas las equivalencias de unidad configuradas para un producto."""
    producto = (
        db.query(Productos)
        .filter(Productos.id == producto_id, Productos.tenant_id == tenant_id, Productos.deleted_at.is_(None))
        .first()
    )
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    equivalencias = (
        db.query(ProductoEquivalenciaUnidad)
        .filter(
            ProductoEquivalenciaUnidad.tenant_id == tenant_id,
            ProductoEquivalenciaUnidad.producto_id == producto_id,
        )
        .all()
    )
    return [EquivalenciaUnidadResponse.model_validate(e) for e in equivalencias]


@router.post(
    "/{producto_id}/equivalencias",
    response_model=EquivalenciaUnidadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_equivalencia(
    producto_id: UUID,
    data: EquivalenciaUnidadCreate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Crea o actualiza (upsert) la equivalencia unidad_receta → unidad_inventario para un producto.
    Si ya existe para esa unidad, actualiza el factor.
    """
    producto = (
        db.query(Productos)
        .filter(Productos.id == producto_id, Productos.tenant_id == ctx.tenant_id, Productos.deleted_at.is_(None))
        .first()
    )
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    if data.unidad_receta == producto.unidad_medida:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unidad_receta '{data.unidad_receta}' es la misma que la unidad de inventario — factor sería 1.0 automático",
        )

    # Upsert
    existente = (
        db.query(ProductoEquivalenciaUnidad)
        .filter(
            ProductoEquivalenciaUnidad.tenant_id == ctx.tenant_id,
            ProductoEquivalenciaUnidad.producto_id == producto_id,
            ProductoEquivalenciaUnidad.unidad_receta == data.unidad_receta,
        )
        .first()
    )

    if existente:
        existente.factor = data.factor
        existente.notas = data.notas
        db.commit()
        db.refresh(existente)
        return EquivalenciaUnidadResponse.model_validate(existente)

    nueva = ProductoEquivalenciaUnidad(
        tenant_id=ctx.tenant_id,
        producto_id=producto_id,
        unidad_receta=data.unidad_receta,
        factor=data.factor,
        notas=data.notas,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return EquivalenciaUnidadResponse.model_validate(nueva)


@router.delete("/{producto_id}/equivalencias/{equivalencia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_equivalencia(
    producto_id: UUID,
    equivalencia_id: UUID,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """Elimina una equivalencia de unidad."""
    eq = (
        db.query(ProductoEquivalenciaUnidad)
        .filter(
            ProductoEquivalenciaUnidad.id == equivalencia_id,
            ProductoEquivalenciaUnidad.tenant_id == ctx.tenant_id,
            ProductoEquivalenciaUnidad.producto_id == producto_id,
        )
        .first()
    )
    if not eq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equivalencia no encontrada")
    db.delete(eq)
    db.commit()
