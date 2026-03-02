"""
Rutas para gestion de Recetas (BOM) y produccion.
"""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from ..datos.db import get_db
from ..datos.esquemas import (
    CostoEstandarResponse,
    EquivalenciaUnidadResponse,
    FijarCostoRequest,
    ProduccionRequest,
    ProduccionResponse,
    RecetaCostoResponse,
    RecetaCreate,
    RecetaIngredienteCreate,
    RecetaResponse,
    RecetaUpdate,
)
from ..datos.modelos import (
    Productos,
    RecetaCostoHistorico,
    Recetas,
    RecetasIngredientes,
    Usuarios,
)
from ..servicios.servicio_costos_indirectos import ServicioCostosIndirectos
from ..servicios.servicio_inventario import ServicioInventario
from ..servicios.servicio_productos import CalculadoraMargenes
from ..utils.logger import setup_logger
from ..utils.seguridad import UserContext, get_current_user, get_tenant_id_from_token, require_tenant_roles

router = APIRouter()
logger = setup_logger(__name__)


# ============================================================================
# CRUD RECETAS
# ============================================================================


@router.post("/", response_model=RecetaResponse, status_code=status.HTTP_201_CREATED)
async def crear_receta(
    receta_data: RecetaCreate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Crea una nueva receta con sus ingredientes.

    **Validaciones:**
    - Nombre unico por tenant
    - Producto resultado debe existir
    - Ingredientes deben existir y ser diferentes al producto resultado
    """
    tenant_id = ctx.tenant_id
    # Validar nombre unico
    existente = (
        db.query(Recetas)
        .filter(Recetas.tenant_id == tenant_id, Recetas.nombre == receta_data.nombre, Recetas.deleted_at.is_(None))
        .first()
    )

    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ya existe una receta con el nombre '{receta_data.nombre}'"
        )

    # Validar producto resultado
    producto_resultado = (
        db.query(Productos)
        .filter(
            Productos.id == receta_data.producto_resultado_id,
            Productos.tenant_id == tenant_id,
            Productos.deleted_at.is_(None),
        )
        .first()
    )

    if not producto_resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto resultado no encontrado")

    try:
        # Crear receta
        receta = Recetas(
            tenant_id=tenant_id,
            nombre=receta_data.nombre,
            descripcion=receta_data.descripcion,
            producto_resultado_id=receta_data.producto_resultado_id,
            cantidad_resultado=receta_data.cantidad_resultado,
            costo_mano_obra=receta_data.costo_mano_obra,
            tiempo_produccion_minutos=receta_data.tiempo_produccion_minutos,
            margen_objetivo=receta_data.margen_objetivo,
            notas=receta_data.notas,
            estado=True,
        )
        db.add(receta)
        db.flush()

        # Agregar ingredientes
        for ing_data in receta_data.ingredientes:
            # Validar que el ingrediente no sea el producto resultado
            if ing_data.producto_id == receta_data.producto_resultado_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El producto resultado no puede ser ingrediente de si mismo",
                )

            # Validar que el producto exista
            producto_ing = (
                db.query(Productos)
                .filter(
                    Productos.id == ing_data.producto_id,
                    Productos.tenant_id == tenant_id,
                    Productos.deleted_at.is_(None),
                )
                .first()
            )

            if not producto_ing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ingrediente con ID {ing_data.producto_id} no encontrado",
                )

            ingrediente = RecetasIngredientes(
                receta_id=receta.id,
                producto_id=ing_data.producto_id,
                cantidad=ing_data.cantidad,
                unidad=ing_data.unidad,
                notas=ing_data.notas,
            )
            db.add(ingrediente)

        db.commit()
        db.refresh(receta)

        logger.info(
            f"Receta creada: {receta.nombre}",
            extra={"tenant_id": str(tenant_id), "receta_id": str(receta.id), "user_id": str(ctx.user.id)},
        )

        return RecetaResponse.model_validate(receta)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error creando receta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear la receta"
        )


@router.get("/equivalencia", response_model=Optional[EquivalenciaUnidadResponse])
async def consultar_equivalencia_top(
    producto_id: UUID = Query(...),
    unidad: str = Query(...),
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Consulta si existe un factor de conversión para un producto+unidad.
    Incluye detección automática de pares estándar (GRAMO↔KILOGRAMO, etc.).
    Retorna null si no existe (el frontend mostrará el mini-modal de configuración).
    """
    from ..servicios.servicio_productos import CalculadoraMargenes

    producto = (
        db.query(Productos)
        .filter(Productos.id == producto_id, Productos.tenant_id == ctx.tenant_id, Productos.deleted_at.is_(None))
        .first()
    )
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    calc = CalculadoraMargenes(db, ctx.tenant_id)
    factor = calc.resolver_factor_conversion(unidad, producto)

    if factor is None:
        return None  # FastAPI serializa como null → frontend muestra modal

    import uuid as _uuid

    return EquivalenciaUnidadResponse(
        id=_uuid.UUID("00000000-0000-0000-0000-000000000000"),
        producto_id=producto_id,
        unidad_receta=unidad,
        factor=factor,
        notas="Auto-detectado" if unidad != producto.unidad_medida else "Misma unidad",
        created_at=__import__("datetime").datetime.utcnow(),
    )


@router.get("/", response_model=List[RecetaResponse])
async def listar_recetas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    solo_activas: bool = Query(True),
    busqueda: Optional[str] = Query(None, min_length=2),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """
    Lista recetas con filtros opcionales.
    """
    query = (
        db.query(Recetas)
        .options(
            selectinload(Recetas.created_by_user),
            selectinload(Recetas.updated_by_user),
            selectinload(Recetas.ingredientes).selectinload(RecetasIngredientes.producto),
        )
        .filter(Recetas.tenant_id == tenant_id, Recetas.deleted_at.is_(None))
    )

    if solo_activas:
        query = query.filter(Recetas.estado)

    if busqueda:
        query = query.filter(Recetas.nombre.ilike(f"%{busqueda}%"))

    recetas = query.order_by(Recetas.nombre).offset(skip).limit(limit).all()
    return [RecetaResponse.model_validate(r) for r in recetas]


@router.get("/{receta_id}", response_model=RecetaResponse)
async def obtener_receta(
    receta_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """
    Obtiene una receta por ID con sus ingredientes.
    """
    receta = (
        db.query(Recetas)
        .options(
            selectinload(Recetas.created_by_user),
            selectinload(Recetas.updated_by_user),
            selectinload(Recetas.ingredientes).selectinload(RecetasIngredientes.producto),
        )
        .filter(Recetas.id == receta_id, Recetas.tenant_id == tenant_id, Recetas.deleted_at.is_(None))
        .first()
    )

    if not receta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receta no encontrada")

    return RecetaResponse.model_validate(receta)


@router.put("/{receta_id}", response_model=RecetaResponse)
async def actualizar_receta(
    receta_id: UUID,
    receta_data: RecetaUpdate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Actualiza una receta existente.
    """
    tenant_id = ctx.tenant_id
    receta = (
        db.query(Recetas)
        .options(selectinload(Recetas.created_by_user), selectinload(Recetas.updated_by_user))
        .filter(Recetas.id == receta_id, Recetas.tenant_id == tenant_id, Recetas.deleted_at.is_(None))
        .first()
    )

    if not receta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receta no encontrada")

    # Validar nombre unico si se cambia
    if receta_data.nombre and receta_data.nombre != receta.nombre:
        existente = (
            db.query(Recetas)
            .filter(
                Recetas.tenant_id == tenant_id,
                Recetas.nombre == receta_data.nombre,
                Recetas.id != receta_id,
                Recetas.deleted_at.is_(None),
            )
            .first()
        )

        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una receta con el nombre '{receta_data.nombre}'",
            )

    try:
        # Actualizar campos
        update_data = receta_data.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            setattr(receta, campo, valor)

        db.commit()
        db.refresh(receta)

        logger.info(f"Receta actualizada: {receta.nombre}")
        return RecetaResponse.model_validate(receta)

    except Exception as e:
        db.rollback()
        logger.error("Error actualizando receta", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al actualizar la receta"
        )


@router.delete("/{receta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_receta(
    receta_id: UUID,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Elimina una receta (soft delete).
    """
    tenant_id = ctx.tenant_id
    from datetime import datetime

    receta = (
        db.query(Recetas)
        .options(selectinload(Recetas.created_by_user), selectinload(Recetas.updated_by_user))
        .filter(Recetas.id == receta_id, Recetas.tenant_id == tenant_id, Recetas.deleted_at.is_(None))
        .first()
    )

    if not receta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receta no encontrada")

    receta.deleted_at = datetime.utcnow()
    db.commit()

    logger.info(f"Receta eliminada: {receta.nombre}")


# ============================================================================
# INGREDIENTES
# ============================================================================


@router.post("/{receta_id}/ingredientes", response_model=RecetaResponse)
async def agregar_ingrediente(
    receta_id: UUID,
    ingrediente_data: RecetaIngredienteCreate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Agrega un ingrediente a una receta existente.
    """
    tenant_id = ctx.tenant_id
    receta = (
        db.query(Recetas)
        .options(selectinload(Recetas.created_by_user), selectinload(Recetas.updated_by_user))
        .filter(Recetas.id == receta_id, Recetas.tenant_id == tenant_id, Recetas.deleted_at.is_(None))
        .first()
    )

    if not receta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receta no encontrada")

    # Validar que el ingrediente no sea el producto resultado
    if ingrediente_data.producto_id == receta.producto_resultado_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El producto resultado no puede ser ingrediente de si mismo"
        )

    # Validar que no exista el ingrediente
    existente = (
        db.query(RecetasIngredientes)
        .filter(
            RecetasIngredientes.receta_id == receta_id, RecetasIngredientes.producto_id == ingrediente_data.producto_id
        )
        .first()
    )

    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este ingrediente ya existe en la receta")

    # Validar producto
    producto = (
        db.query(Productos)
        .filter(
            Productos.id == ingrediente_data.producto_id,
            Productos.tenant_id == tenant_id,
            Productos.deleted_at.is_(None),
        )
        .first()
    )

    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto ingrediente no encontrado")

    ingrediente = RecetasIngredientes(
        receta_id=receta_id,
        producto_id=ingrediente_data.producto_id,
        cantidad=ingrediente_data.cantidad,
        unidad=ingrediente_data.unidad,
        notas=ingrediente_data.notas,
    )
    db.add(ingrediente)
    db.commit()
    db.refresh(receta)

    return RecetaResponse.model_validate(receta)


@router.delete("/{receta_id}/ingredientes/{ingrediente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_ingrediente(
    receta_id: UUID,
    ingrediente_id: UUID,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Elimina un ingrediente de una receta.
    """
    tenant_id = ctx.tenant_id
    # Verificar receta
    receta = (
        db.query(Recetas)
        .options(selectinload(Recetas.created_by_user), selectinload(Recetas.updated_by_user))
        .filter(Recetas.id == receta_id, Recetas.tenant_id == tenant_id, Recetas.deleted_at.is_(None))
        .first()
    )

    if not receta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receta no encontrada")

    ingrediente = (
        db.query(RecetasIngredientes)
        .filter(RecetasIngredientes.id == ingrediente_id, RecetasIngredientes.receta_id == receta_id)
        .first()
    )

    if not ingrediente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingrediente no encontrado")

    db.delete(ingrediente)
    db.commit()


# ============================================================================
# CALCULAR COSTO
# ============================================================================


@router.post("/{receta_id}/calcular-costo", response_model=RecetaCostoResponse)
async def calcular_costo_receta(
    receta_id: UUID,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Calcula el costo detallado de una receta.

    Retorna:
    - Costo de cada ingrediente
    - Costo total de ingredientes
    - Costo de mano de obra
    - Costo total
    - Costo unitario por producto resultado
    - Margen actual si tiene precio de venta
    """
    calculadora = CalculadoraMargenes(db, ctx.tenant_id)
    svc_indirectos = ServicioCostosIndirectos(db=db, tenant_id=ctx.tenant_id)

    try:
        # Calcular costos indirectos basados en costos variables de la receta
        # Primero hacemos un cálculo sin indirectos para obtener el costo base
        resultado_base = calculadora.calcular_costo_receta(receta_id)
        costo_base = resultado_base["costo_ingredientes"] + resultado_base["costo_mano_obra"]
        costo_indirecto, _ = svc_indirectos.calcular_total_para_costo_base(costo_base)

        # Recalcular con indirectos
        resultado = calculadora.calcular_costo_receta(receta_id, costo_indirecto=costo_indirecto)
        return RecetaCostoResponse(**resultado)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# PRODUCIR
# ============================================================================


@router.post("/{receta_id}/producir", response_model=ProduccionResponse)
async def producir_desde_receta(
    receta_id: UUID,
    produccion_data: ProduccionRequest,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Produce productos terminados desde una receta.

    **Proceso:**
    1. Valida stock de todos los ingredientes
    2. Descuenta ingredientes del inventario
    3. Crea producto terminado en inventario
    4. Calcula costo de produccion

    **Requiere:** Stock suficiente de todos los ingredientes
    """
    tenant_id = ctx.tenant_id  # Compatibilidad
    servicio = ServicioInventario(db, tenant_id)

    try:
        resultado = servicio.producir_desde_receta(
            receta_id=receta_id,
            cantidad_producir=produccion_data.cantidad,
            usuario_id=ctx.user.id,
            observaciones=produccion_data.observaciones,
        )
        return ProduccionResponse(**resultado)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{receta_id}/validar-stock")
async def validar_stock_receta(
    receta_id: UUID,
    cantidad: Decimal = Query(..., gt=0, description="Cantidad a producir"),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """
    Valida si hay stock suficiente para producir la cantidad indicada.

    Retorna lista de ingredientes faltantes (vacia si hay stock suficiente).
    """
    # Obtener receta
    receta = (
        db.query(Recetas)
        .options(selectinload(Recetas.created_by_user), selectinload(Recetas.updated_by_user))
        .filter(Recetas.id == receta_id, Recetas.tenant_id == tenant_id, Recetas.deleted_at.is_(None))
        .first()
    )

    if not receta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receta no encontrada")

    servicio = ServicioInventario(db, tenant_id)
    faltantes = servicio.validar_stock_receta(receta, cantidad)

    return {
        "receta_id": str(receta_id),
        "cantidad_solicitada": float(cantidad),
        "stock_suficiente": len(faltantes) == 0,
        "ingredientes_faltantes": faltantes,
    }


# ============================================================================
# FIJAR COSTO ESTÁNDAR
# ============================================================================


@router.post("/{receta_id}/fijar-costo", response_model=CostoEstandarResponse, status_code=status.HTTP_201_CREATED)
async def fijar_costo_estandar(
    receta_id: UUID,
    request: FijarCostoRequest,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Fija el costo calculado como costo estándar vigente para la receta.
    Guarda snapshot del cálculo para auditoría futura.
    """
    import datetime
    import json

    from ..servicios.servicio_costos_indirectos import ServicioCostosIndirectos
    from ..servicios.servicio_productos import CalculadoraMargenes

    receta = (
        db.query(Recetas)
        .filter(Recetas.id == receta_id, Recetas.tenant_id == ctx.tenant_id, Recetas.deleted_at.is_(None))
        .first()
    )
    if not receta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receta no encontrada")

    calc = CalculadoraMargenes(db, ctx.tenant_id)
    svc_ind = ServicioCostosIndirectos(db=db, tenant_id=ctx.tenant_id)

    try:
        resultado_base = calc.calcular_costo_receta(receta_id)
        costo_base = resultado_base["costo_ingredientes"] + resultado_base["costo_mano_obra"]
        costo_ind, _ = svc_ind.calcular_total_para_costo_base(costo_base)
        resultado = calc.calcular_costo_receta(receta_id, costo_indirecto=costo_ind)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Serializar snapshot (convertir Decimal a str para JSON)
    def _decimal_default(obj: object) -> str:
        from decimal import Decimal

        if isinstance(obj, Decimal):
            return str(obj)
        raise TypeError

    snapshot_json = json.dumps(resultado, default=_decimal_default)

    historico = RecetaCostoHistorico(
        tenant_id=ctx.tenant_id,
        receta_id=receta_id,
        costo_unitario=resultado["costo_unitario"],
        precio_sugerido=resultado.get("precio_sugerido"),
        confirmado_por=ctx.user.id,
        confirmado_en=datetime.datetime.utcnow(),
        snapshot_detalle=snapshot_json,
        vigente_desde=request.vigente_desde,
        notas_confirmacion=request.notas,
    )
    db.add(historico)
    db.commit()
    db.refresh(historico)

    nombre_usuario = ctx.user.nombre if hasattr(ctx.user, "nombre") else None

    return CostoEstandarResponse(
        id=historico.id,
        receta_id=historico.receta_id,
        costo_unitario=historico.costo_unitario,
        precio_sugerido=historico.precio_sugerido,
        confirmado_por_nombre=nombre_usuario,
        confirmado_en=historico.confirmado_en,
        vigente_desde=historico.vigente_desde,
        notas_confirmacion=historico.notas_confirmacion,
    )


@router.get("/{receta_id}/costo-estandar", response_model=Optional[CostoEstandarResponse])
async def obtener_costo_estandar(
    receta_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """
    Obtiene el último costo estándar fijado para la receta (o null si nunca se ha fijado).
    """
    from sqlalchemy.orm import joinedload

    historico = (
        db.query(RecetaCostoHistorico)
        .options(joinedload(RecetaCostoHistorico.usuario_confirma))
        .filter(RecetaCostoHistorico.tenant_id == tenant_id, RecetaCostoHistorico.receta_id == receta_id)
        .order_by(RecetaCostoHistorico.confirmado_en.desc())
        .first()
    )

    if not historico:
        return None

    nombre_usuario = historico.usuario_confirma.nombre if historico.usuario_confirma else None

    return CostoEstandarResponse(
        id=historico.id,
        receta_id=historico.receta_id,
        costo_unitario=historico.costo_unitario,
        precio_sugerido=historico.precio_sugerido,
        confirmado_por_nombre=nombre_usuario,
        confirmado_en=historico.confirmado_en,
        vigente_desde=historico.vigente_desde,
        notas_confirmacion=historico.notas_confirmacion,
    )
