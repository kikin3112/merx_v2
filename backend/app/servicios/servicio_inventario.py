"""
Servicio de Inventario.
Maneja movimientos de stock, produccion desde recetas y costo promedio ponderado.
"""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from ..datos.modelos import (
    Inventarios,
    MovimientosInventario,
    ProductoEquivalenciaUnidad,
    Productos,
    Recetas,
    TipoMovimiento,
)
from ..utils.logger import setup_logger
from .servicio_productos import _TABLA_CONVERSION_ESTANDAR

logger = setup_logger(__name__)


class ServicioInventario:
    """
    Servicio para operaciones de inventario.
    """

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # CONSULTAS
    # ========================================================================

    def obtener_inventario_producto(self, producto_id: UUID, lock: bool = False) -> Optional[Inventarios]:
        """
        Obtiene el inventario de un producto.

        Args:
            producto_id: ID del producto
            lock: Si True, adquiere bloqueo FOR UPDATE (previene race conditions)

        Returns:
            Inventarios o None si no existe
        """
        query = self.db.query(Inventarios).filter(
            Inventarios.tenant_id == self.tenant_id, Inventarios.producto_id == producto_id
        )

        if lock:
            query = query.with_for_update()

        return query.first()

    def obtener_stock_disponible(self, producto_id: UUID) -> Decimal:
        """Obtiene la cantidad disponible de un producto."""
        inventario = self.obtener_inventario_producto(producto_id)
        return inventario.cantidad_disponible if inventario else Decimal("0.00")

    def obtener_costo_promedio(self, producto_id: UUID) -> Decimal:
        """Obtiene el costo promedio ponderado de un producto."""
        inventario = self.obtener_inventario_producto(producto_id)
        return inventario.costo_promedio_ponderado if inventario else Decimal("0.00")

    def listar_movimientos(
        self, producto_id: Optional[UUID] = None, tipo: Optional[TipoMovimiento] = None, limite: int = 100
    ) -> List[MovimientosInventario]:
        """Lista movimientos de inventario con filtros opcionales."""
        query = (
            self.db.query(MovimientosInventario)
            .options(
                selectinload(MovimientosInventario.created_by_user), selectinload(MovimientosInventario.updated_by_user)
            )
            .filter(MovimientosInventario.tenant_id == self.tenant_id)
        )

        if producto_id:
            query = query.filter(MovimientosInventario.producto_id == producto_id)

        if tipo:
            query = query.filter(MovimientosInventario.tipo_movimiento == tipo)

        return query.order_by(MovimientosInventario.fecha_movimiento.desc()).limit(limite).all()

    def obtener_inventario_valorizado(self) -> List[dict]:
        """Obtiene el inventario valorizado (stock * costo) por producto."""
        query = (
            self.db.query(
                Productos.id,
                Productos.codigo_interno,
                Productos.nombre,
                Inventarios.cantidad_disponible,
                Inventarios.costo_promedio_ponderado,
                Inventarios.valor_total,
            )
            .join(Inventarios, Productos.id == Inventarios.producto_id)
            .filter(
                Productos.tenant_id == self.tenant_id,
                Productos.deleted_at.is_(None),
                Inventarios.cantidad_disponible > 0,
            )
            .order_by(Productos.nombre)
        )

        resultados = []
        for row in query.all():
            resultados.append(
                {
                    "producto_id": str(row.id),
                    "codigo": row.codigo_interno,
                    "nombre": row.nombre,
                    "cantidad": float(row.cantidad_disponible),
                    "costo_promedio": float(row.costo_promedio_ponderado),
                    "valor_total": float(row.valor_total),
                }
            )

        return resultados

    # ========================================================================
    # MOVIMIENTOS DE INVENTARIO
    # ========================================================================

    def crear_movimiento(
        self,
        producto_id: UUID,
        tipo: TipoMovimiento,
        cantidad: Decimal,
        costo_unitario: Optional[Decimal] = None,
        documento_referencia: Optional[str] = None,
        observaciones: Optional[str] = None,
    ) -> MovimientosInventario:
        """
        Crea un movimiento de inventario y actualiza el stock.

        Args:
            producto_id: ID del producto
            tipo: Tipo de movimiento (ENTRADA, SALIDA, AJUSTE, etc.)
            cantidad: Cantidad (positiva para entradas, puede ser negativa para ajustes)
            costo_unitario: Costo por unidad (requerido para entradas)
            documento_referencia: Referencia al documento origen
            observaciones: Notas adicionales

        Returns:
            MovimientosInventario creado

        Raises:
            ValueError: Si no hay stock suficiente para salidas
        """
        # Obtener o crear inventario (con bloqueo para prevenir race conditions)
        inventario = self.obtener_inventario_producto(producto_id, lock=True)
        if not inventario:
            inventario = Inventarios(
                tenant_id=self.tenant_id,
                producto_id=producto_id,
                cantidad_disponible=Decimal("0.00"),
                costo_promedio_ponderado=Decimal("0.00"),
                valor_total=Decimal("0.00"),
            )
            self.db.add(inventario)
            self.db.flush()

        # Validar stock para salidas
        if tipo == TipoMovimiento.SALIDA:
            if inventario.cantidad_disponible < cantidad:
                raise ValueError(
                    f"Stock insuficiente. Disponible: {inventario.cantidad_disponible}, Requerido: {cantidad}"
                )

        # Calcular valor del movimiento
        if tipo == TipoMovimiento.ENTRADA and costo_unitario is not None:
            valor_movimiento = cantidad * costo_unitario
        elif tipo == TipoMovimiento.SALIDA:
            costo_unitario = inventario.costo_promedio_ponderado
            valor_movimiento = cantidad * costo_unitario
        else:
            valor_movimiento = Decimal("0.00")

        # Crear movimiento
        movimiento = MovimientosInventario(
            tenant_id=self.tenant_id,
            producto_id=producto_id,
            tipo_movimiento=tipo,
            cantidad=cantidad if tipo != TipoMovimiento.SALIDA else -cantidad,
            costo_unitario=costo_unitario,
            valor_total=valor_movimiento,
            documento_referencia=documento_referencia,
            observaciones=observaciones,
            fecha_movimiento=datetime.utcnow(),
        )
        self.db.add(movimiento)

        # Actualizar inventario
        if tipo == TipoMovimiento.ENTRADA:
            self._actualizar_costo_promedio_entrada(inventario, cantidad, costo_unitario)
            inventario.cantidad_disponible += cantidad
        elif tipo == TipoMovimiento.SALIDA:
            inventario.cantidad_disponible -= cantidad
        elif tipo == TipoMovimiento.AJUSTE:
            inventario.cantidad_disponible += cantidad  # cantidad puede ser negativa
        elif tipo == TipoMovimiento.PRODUCCION:
            inventario.cantidad_disponible += cantidad
            if costo_unitario:
                self._actualizar_costo_promedio_entrada(inventario, cantidad, costo_unitario)

        # Actualizar valor total
        inventario.valor_total = inventario.cantidad_disponible * inventario.costo_promedio_ponderado

        self.db.flush()

        logger.info(
            f"Movimiento creado: {tipo.value} {cantidad} de producto {producto_id}",
            extra={
                "tenant_id": str(self.tenant_id),
                "producto_id": str(producto_id),
                "tipo": tipo.value,
                "cantidad": str(cantidad),
            },
        )

        return movimiento

    def _actualizar_costo_promedio_entrada(
        self, inventario: Inventarios, cantidad_entrada: Decimal, costo_unitario_entrada: Decimal
    ) -> None:
        """
        Actualiza el costo promedio ponderado al recibir una entrada.

        Formula: CPP = (Stock_ant * Costo_ant + Entrada * Costo_entrada) / (Stock_ant + Entrada)
        """
        stock_anterior = inventario.cantidad_disponible
        costo_anterior = inventario.costo_promedio_ponderado

        valor_anterior = stock_anterior * costo_anterior
        valor_entrada = cantidad_entrada * costo_unitario_entrada
        nuevo_stock = stock_anterior + cantidad_entrada

        if nuevo_stock > 0:
            inventario.costo_promedio_ponderado = (valor_anterior + valor_entrada) / nuevo_stock
        else:
            inventario.costo_promedio_ponderado = costo_unitario_entrada

    # ========================================================================
    # PRODUCCION DESDE RECETAS
    # ========================================================================

    def _resolver_factor_conversion(self, ing_unidad: str, producto: Productos) -> Decimal:
        """Retorna factor para convertir cantidad en unidad_receta a unidad_inventario. Default 1."""
        prod_unidad = producto.unidad_medida
        if ing_unidad == prod_unidad:
            return Decimal("1")
        par = (ing_unidad, prod_unidad)
        if par in _TABLA_CONVERSION_ESTANDAR:
            return _TABLA_CONVERSION_ESTANDAR[par]
        eq = (
            self.db.query(ProductoEquivalenciaUnidad)
            .filter(
                ProductoEquivalenciaUnidad.tenant_id == self.tenant_id,
                ProductoEquivalenciaUnidad.producto_id == producto.id,
                ProductoEquivalenciaUnidad.unidad_receta == ing_unidad,
            )
            .first()
        )
        if eq:
            return eq.factor
        return Decimal("1")

    def validar_stock_receta(self, receta: Recetas, cantidad_producir: Decimal) -> List[dict]:
        """
        Valida si hay stock suficiente para producir la cantidad indicada.

        Returns:
            Lista de ingredientes faltantes (vacia si hay stock suficiente)
        """
        faltantes = []

        for ingrediente in receta.ingredientes:
            merma = getattr(ingrediente, "porcentaje_merma", None) or Decimal("0.00")
            factor = Decimal("1") - merma / Decimal("100")
            cantidad_bruta = (ingrediente.cantidad / factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            cantidad_requerida_receta = cantidad_bruta * cantidad_producir
            factor_conv = self._resolver_factor_conversion(ingrediente.unidad, ingrediente.producto)
            cantidad_requerida = (cantidad_requerida_receta * factor_conv).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            stock_disponible = self.obtener_stock_disponible(ingrediente.producto_id)

            if stock_disponible < cantidad_requerida:
                faltantes.append(
                    {
                        "producto_id": str(ingrediente.producto_id),
                        "producto_nombre": ingrediente.producto.nombre if ingrediente.producto else "N/A",
                        "cantidad_requerida": float(cantidad_requerida),
                        "stock_disponible": float(stock_disponible),
                        "faltante": float(cantidad_requerida - stock_disponible),
                    }
                )

        return faltantes

    def producir_desde_receta(
        self,
        receta_id: UUID,
        cantidad_producir: Decimal,
        usuario_id: Optional[UUID] = None,
        observaciones: Optional[str] = None,
    ) -> dict:
        """
        Produce productos terminados desde una receta.

        1. Valida stock de ingredientes
        2. Crea movimientos de SALIDA por cada ingrediente
        3. Crea movimiento de PRODUCCION para el producto terminado
        4. Recalcula costo promedio del producto terminado

        Args:
            receta_id: ID de la receta a producir
            cantidad_producir: Cantidad de productos a producir
            usuario_id: ID del usuario que realiza la produccion
            observaciones: Notas adicionales

        Returns:
            dict con resultado de la produccion

        Raises:
            ValueError: Si no hay stock suficiente o la receta no existe
        """
        # Obtener receta
        receta = (
            self.db.query(Recetas)
            .filter(Recetas.id == receta_id, Recetas.tenant_id == self.tenant_id, Recetas.deleted_at.is_(None))
            .first()
        )

        if not receta:
            raise ValueError("Receta no encontrada")

        if not receta.estado:
            raise ValueError("Receta inactiva")

        if not receta.ingredientes:
            raise ValueError("La receta no tiene ingredientes")

        # Prevenir deadlocks: Adquirir bloqueos de inventario en orden consistente
        # Ordenar IDs de ingredientes y bloquear todos de una vez
        ingredient_ids = sorted([ing.producto_id for ing in receta.ingredientes])
        if ingredient_ids:
            self.db.query(Inventarios).filter(
                Inventarios.tenant_id == self.tenant_id, Inventarios.producto_id.in_(ingredient_ids)
            ).with_for_update().all()

        # También bloquear el inventario del producto resultado
        self.db.query(Inventarios).filter(
            Inventarios.tenant_id == self.tenant_id, Inventarios.producto_id == receta.producto_resultado_id
        ).with_for_update().first()

        # Validar stock
        faltantes = self.validar_stock_receta(receta, cantidad_producir)
        if faltantes:
            raise ValueError(f"Stock insuficiente para producir. Faltantes: {faltantes}")

        # Calcular costo total de produccion
        costo_total_ingredientes = Decimal("0.00")
        documento_ref = f"PROD-{receta_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Descontar ingredientes usando cantidad_bruta (incluye merma)
        for ingrediente in receta.ingredientes:
            merma = getattr(ingrediente, "porcentaje_merma", None) or Decimal("0.00")
            factor = Decimal("1") - merma / Decimal("100")
            cantidad_bruta_unitaria = (ingrediente.cantidad / factor).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            cantidad_requerida_receta = cantidad_bruta_unitaria * cantidad_producir
            factor_conv = self._resolver_factor_conversion(ingrediente.unidad, ingrediente.producto)
            cantidad_requerida = (cantidad_requerida_receta * factor_conv).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            costo_unitario_ing = self.obtener_costo_promedio(ingrediente.producto_id)
            costo_total_ingredientes += (cantidad_requerida * costo_unitario_ing).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            self.crear_movimiento(
                producto_id=ingrediente.producto_id,
                tipo=TipoMovimiento.SALIDA,
                cantidad=cantidad_requerida,
                documento_referencia=documento_ref,
                observaciones=f"Consumo para produccion de {receta.nombre}",
            )

        # Agregar costo mano de obra proporcional
        costo_mano_obra_total = receta.costo_mano_obra * cantidad_producir

        # Costos indirectos (sobre costo_base POR LOTE — así FIJO escala correctamente)
        # Si se calcula sobre la base total (×N lotes), FIJO no multiplicaría por N → bug
        costo_base_por_lote = (costo_total_ingredientes + costo_mano_obra_total) / cantidad_producir
        from .servicio_costos_indirectos import ServicioCostosIndirectos

        svc_indirectos = ServicioCostosIndirectos(self.db, self.tenant_id)
        costo_indirecto_por_lote, _ = svc_indirectos.calcular_total_para_costo_base(costo_base_por_lote)
        costo_indirecto_total = (costo_indirecto_por_lote * cantidad_producir).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        costo_total_produccion = (costo_total_ingredientes + costo_mano_obra_total) + costo_indirecto_total

        # Calcular cantidad de producto terminado a producir
        cantidad_terminada = receta.cantidad_resultado * cantidad_producir
        costo_unitario_producido = (costo_total_produccion / cantidad_terminada).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Crear entrada de producto terminado
        movimiento_produccion = self.crear_movimiento(
            producto_id=receta.producto_resultado_id,
            tipo=TipoMovimiento.PRODUCCION,
            cantidad=cantidad_terminada,
            costo_unitario=costo_unitario_producido,
            documento_referencia=documento_ref,
            observaciones=observaciones or f"Produccion desde receta: {receta.nombre}",
        )

        self.db.commit()

        logger.info(
            f"Produccion completada: {cantidad_terminada} unidades de {receta.producto_resultado_id}",
            extra={
                "tenant_id": str(self.tenant_id),
                "receta_id": str(receta_id),
                "cantidad_producida": str(cantidad_terminada),
                "costo_total": str(costo_total_produccion),
            },
        )

        return {
            "receta_id": str(receta_id),
            "receta_nombre": receta.nombre,
            "producto_resultado_id": str(receta.producto_resultado_id),
            "cantidad_producida": cantidad_terminada,
            "costo_ingredientes": costo_total_ingredientes,
            "costo_mano_obra": costo_mano_obra_total,
            "costo_indirecto": costo_indirecto_total,
            "costo_total": costo_total_produccion,
            "costo_unitario": costo_unitario_producido,
            "documento_referencia": documento_ref,
            "movimiento_id": str(movimiento_produccion.id),
        }

    # ========================================================================
    # AJUSTES DE INVENTARIO
    # ========================================================================

    def ajustar_inventario(
        self, producto_id: UUID, cantidad_nueva: Decimal, motivo: str, usuario_id: Optional[UUID] = None
    ) -> MovimientosInventario:
        """
        Ajusta el inventario a una cantidad especifica.

        Args:
            producto_id: ID del producto
            cantidad_nueva: Nueva cantidad a establecer
            motivo: Razon del ajuste
            usuario_id: ID del usuario que realiza el ajuste

        Returns:
            MovimientosInventario del ajuste
        """
        stock_actual = self.obtener_stock_disponible(producto_id)
        diferencia = cantidad_nueva - stock_actual

        if diferencia == 0:
            raise ValueError("La cantidad actual ya es igual a la nueva")

        movimiento = self.crear_movimiento(
            producto_id=producto_id,
            tipo=TipoMovimiento.AJUSTE,
            cantidad=diferencia,
            documento_referencia=f"AJUSTE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            observaciones=motivo,
        )

        self.db.commit()

        logger.info(
            f"Ajuste de inventario: {producto_id} de {stock_actual} a {cantidad_nueva}",
            extra={
                "tenant_id": str(self.tenant_id),
                "producto_id": str(producto_id),
                "diferencia": str(diferencia),
                "motivo": motivo,
            },
        )

        return movimiento

    # ========================================================================
    # ALERTAS DE STOCK
    # ========================================================================

    def obtener_alertas_stock_bajo(self) -> List[dict]:
        """Obtiene productos con stock por debajo del minimo."""
        query = (
            self.db.query(
                Productos.id,
                Productos.codigo_interno,
                Productos.nombre,
                Productos.stock_minimo,
                Inventarios.cantidad_disponible,
            )
            .join(Inventarios, Productos.id == Inventarios.producto_id)
            .filter(
                Productos.tenant_id == self.tenant_id,
                Productos.deleted_at.is_(None),
                Productos.maneja_inventario,
                Productos.stock_minimo.isnot(None),
                Inventarios.cantidad_disponible <= Productos.stock_minimo,
            )
            .order_by((Inventarios.cantidad_disponible - Productos.stock_minimo))
        )

        alertas = []
        for row in query.all():
            alertas.append(
                {
                    "producto_id": str(row.id),
                    "codigo": row.codigo_interno,
                    "nombre": row.nombre,
                    "stock_minimo": float(row.stock_minimo),
                    "stock_actual": float(row.cantidad_disponible),
                    "diferencia": float(row.cantidad_disponible - row.stock_minimo),
                }
            )

        return alertas
