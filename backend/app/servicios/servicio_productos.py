"""
Servicio de Productos.
Incluye CalculadoraMargenes para analisis de costos y rentabilidad.
"""

from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from ..datos.modelos import (
    EstadoOrdenProduccion,
    Inventarios,
    OrdenesProduccion,
    ProductoEquivalenciaUnidad,
    Productos,
    Recetas,
    RecetasIngredientes,
)
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


_TABLA_CONVERSION_ESTANDAR: dict = {
    ("GRAMO", "KILOGRAMO"): Decimal("0.001"),
    ("KILOGRAMO", "GRAMO"): Decimal("1000"),
    ("MILILITRO", "LITRO"): Decimal("0.001"),
    ("LITRO", "MILILITRO"): Decimal("1000"),
    ("CENTIMETRO", "METRO"): Decimal("0.01"),
    ("METRO", "CENTIMETRO"): Decimal("100"),
    ("GRAMO", "GRAMO"): Decimal("1"),
    ("KILOGRAMO", "KILOGRAMO"): Decimal("1"),
    ("MILILITRO", "MILILITRO"): Decimal("1"),
    ("LITRO", "LITRO"): Decimal("1"),
    ("METRO", "METRO"): Decimal("1"),
    ("CENTIMETRO", "CENTIMETRO"): Decimal("1"),
    ("UNIDAD", "UNIDAD"): Decimal("1"),
}


class CalculadoraMargenes:
    """
    Calculadora de margenes y rentabilidad para productos.
    Permite calcular costos, precios sugeridos y margenes reales.
    """

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def resolver_factor_conversion(self, ing_unidad: str, producto: Productos) -> Optional[Decimal]:
        """
        Resuelve el factor de conversión entre unidad_receta y unidad_inventario.

        Orden de resolución:
        1. Misma unidad → 1.0 automático
        2. Par estándar conocido → automático sin configuración
        3. Equivalencia configurada por el tenant
        4. None → no encontrado (la ruta debe notificarlo)
        """
        prod_unidad = producto.unidad_medida

        # 1. Misma unidad → factor 1
        if ing_unidad == prod_unidad:
            return Decimal("1.000000")

        # 2. Par estándar
        par = (ing_unidad, prod_unidad)
        if par in _TABLA_CONVERSION_ESTANDAR:
            return _TABLA_CONVERSION_ESTANDAR[par]

        # 3. Equivalencia configurada
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

        # 4. No encontrado
        return None

    def _produccion_mensual_real(self, producto_id: UUID) -> Optional[Decimal]:
        """
        Suma las unidades producidas (COMPLETADA) en los últimos 30 días para este producto.
        Retorna None si no hay órdenes completadas en el período.
        """
        hace_30_dias = datetime.now(timezone.utc) - timedelta(days=30)
        total = (
            self.db.query(func.sum(OrdenesProduccion.cantidad_producir))
            .filter(
                OrdenesProduccion.tenant_id == self.tenant_id,
                OrdenesProduccion.producto_id == producto_id,
                OrdenesProduccion.estado == EstadoOrdenProduccion.COMPLETADA,
                OrdenesProduccion.deleted_at.is_(None),
                OrdenesProduccion.fecha_inicio >= hace_30_dias.date(),
            )
            .scalar()
        )
        return Decimal(str(total)) if total else None

    def calcular_costo_receta(
        self,
        receta_id: UUID,
        costo_indirecto: Optional[Decimal] = None,
        cif_fijo_mensual: Optional[Decimal] = None,
        cif_porcentaje: Optional[Decimal] = None,
    ) -> dict:
        """
        Calcula el costo total de una receta con estructura profesional de manufactura.

        Incluye:
        - Conversión de unidades automática (GRAMO → KILOGRAMO, etc.)
        - Estructura: Costo Primo, CIF, Costo de Conversión
        - Cobertura de stock: lotes_posibles_con_stock
        - Distribución del CIF fijo mensual entre producción real

        Args:
            receta_id: UUID de la receta
            costo_indirecto: CIF total (legacy — si se provee sin desglose, se trata todo como fijo mensual)
            cif_fijo_mensual: Monto fijo mensual a distribuir entre produccion_mensual
            cif_porcentaje: CIF ya proporcional al lote (% sobre costo base), se suma directo

        Returns:
            dict con desglose de costos (todos los valores son Decimal)
        """
        receta = (
            self.db.query(Recetas)
            .options(
                joinedload(Recetas.ingredientes).joinedload(RecetasIngredientes.producto),
                joinedload(Recetas.producto_resultado),
            )
            .filter(Recetas.id == receta_id, Recetas.tenant_id == self.tenant_id, Recetas.deleted_at.is_(None))
            .first()
        )

        if not receta:
            raise ValueError("Receta no encontrada")

        # Cargar inventarios en un solo query para todos los productos
        product_ids = [ing.producto_id for ing in receta.ingredientes]
        inventarios_map: dict = {}
        if product_ids:
            inventarios = (
                self.db.query(Inventarios)
                .filter(Inventarios.tenant_id == self.tenant_id, Inventarios.producto_id.in_(product_ids))
                .all()
            )
            inventarios_map = {inv.producto_id: inv for inv in inventarios}

        # ── Calcular costo de ingredientes con conversión de unidades ──
        costo_material_directo = Decimal("0.00")
        detalle_ingredientes = []
        # Para cobertura de stock
        lotes_posibles = None
        ingrediente_critico: Optional[str] = None

        for ing in receta.ingredientes:
            inv = inventarios_map.get(ing.producto_id)
            cpp = Decimal("0.00")
            unidad_inventario = ""
            if inv:
                cpp = inv.costo_promedio_ponderado or Decimal("0.00")
            if ing.producto:
                unidad_inventario = ing.producto.unidad_medida

            # Resolución del factor de conversión de unidades
            factor_conv = Decimal("1.000000")
            if ing.producto:
                resolved = self.resolver_factor_conversion(ing.unidad, ing.producto)
                if resolved is not None:
                    factor_conv = resolved
                # Si resolved es None, usamos 1.0 y el costo puede estar inflado
                # (la ruta de equivalencias debe haber informado al frontend)

            merma = getattr(ing, "porcentaje_merma", None) or Decimal("0.00")
            merma_factor = Decimal("1") - merma / Decimal("100")
            cantidad_bruta = (ing.cantidad / merma_factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            # costo_unitario_ing ya está en unidades de inventario; ajustar por factor
            costo_unitario_efectivo = (cpp * factor_conv).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            costo_linea = (cantidad_bruta * costo_unitario_efectivo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            costo_material_directo += costo_linea

            # Cobertura de stock: cuántos lotes completos podemos producir
            if inv and ing.cantidad > 0:
                cantidad_necesaria_por_lote = cantidad_bruta  # ya incluye merma
                if cantidad_necesaria_por_lote > 0:
                    stock_disponible = inv.cantidad_disponible or Decimal("0")
                    lotes_ing = int(stock_disponible / cantidad_necesaria_por_lote)
                    if lotes_posibles is None or lotes_ing < lotes_posibles:
                        lotes_posibles = lotes_ing
                        if lotes_ing == 0:
                            ingrediente_critico = ing.producto.nombre if ing.producto else str(ing.producto_id)

            detalle_ingredientes.append(
                {
                    "producto_id": str(ing.producto_id),
                    "producto_nombre": ing.producto.nombre if ing.producto else "N/A",
                    "cantidad": ing.cantidad,
                    "unidad": ing.unidad,
                    "porcentaje_merma": merma,
                    "cantidad_bruta": cantidad_bruta,
                    "costo_unitario": costo_unitario_efectivo,
                    "costo_linea": costo_linea,
                    "factor_aplicado": factor_conv,
                    "unidad_inventario": unidad_inventario,
                    "porcentaje_del_total": Decimal("0.00"),  # Calculado después
                }
            )

        # Calcular %_del_total por ingrediente
        for d in detalle_ingredientes:
            if costo_material_directo > 0:
                d["porcentaje_del_total"] = (d["costo_linea"] / costo_material_directo * 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

        # ── Estructura profesional de costos ──
        costo_mano_obra_directa = receta.costo_mano_obra
        costo_primo = costo_material_directo + costo_mano_obra_directa

        # ── Distribución CIF mensual fijo entre producción real ──
        # Determinar componentes CIF
        if cif_fijo_mensual is not None or cif_porcentaje is not None:
            _cif_fijo = cif_fijo_mensual or Decimal("0.00")
            _cif_porc = cif_porcentaje or Decimal("0.00")
        elif costo_indirecto is not None:
            # Modo legacy: todo el CIF se trata como fijo mensual a distribuir
            _cif_fijo = costo_indirecto
            _cif_porc = Decimal("0.00")
        else:
            _cif_fijo = Decimal("0.00")
            _cif_porc = Decimal("0.00")

        # Producción mensual: historial > esperado > lote (fallback)
        produccion_mensual_usada: Decimal
        fuente_produccion_mensual: str
        produccion_historico = self._produccion_mensual_real(receta.producto_resultado_id)
        if produccion_historico and produccion_historico > 0:
            produccion_mensual_usada = produccion_historico
            fuente_produccion_mensual = "historico"
        elif receta.produccion_mensual_esperada and receta.produccion_mensual_esperada > 0:
            produccion_mensual_usada = receta.produccion_mensual_esperada
            fuente_produccion_mensual = "esperado"
        else:
            produccion_mensual_usada = receta.cantidad_resultado
            fuente_produccion_mensual = "lote"

        # CIF fijo distribuido para este lote
        cif_por_unidad = (_cif_fijo / produccion_mensual_usada).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        cif_lote = (cif_por_unidad * receta.cantidad_resultado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        costo_indirecto_total = cif_lote + _cif_porc

        costo_conversion = costo_mano_obra_directa + costo_indirecto_total
        costo_total = costo_primo + costo_indirecto_total

        # Costo por unidad producida
        costo_unitario = Decimal("0.00")
        if receta.cantidad_resultado > 0:
            costo_unitario = (costo_total / receta.cantidad_resultado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Precio de venta y margen
        precio_venta = Decimal("0.00")
        margen_actual = Decimal("0.00")
        if receta.producto_resultado:
            precio_venta = receta.producto_resultado.precio_venta or Decimal("0.00")
            if precio_venta > 0 and costo_unitario >= 0:
                margen_actual = ((precio_venta - costo_unitario) / precio_venta * 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

        # Precio sugerido
        precio_sugerido = None
        margen_objetivo = getattr(receta, "margen_objetivo", None)
        if margen_objetivo and margen_objetivo > 0 and costo_unitario > 0:
            precio_sugerido = (costo_unitario / (1 - margen_objetivo / 100)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        return {
            "receta_id": str(receta_id),
            "receta_nombre": receta.nombre,
            "producto_resultado_id": str(receta.producto_resultado_id),
            "cantidad_resultado": receta.cantidad_resultado,
            # Estructura profesional
            "costo_material_directo": costo_material_directo,
            "costo_mano_obra_directa": costo_mano_obra_directa,
            "costo_primo": costo_primo,
            "costo_conversion": costo_conversion,
            "costo_indirecto": costo_indirecto_total,
            "costo_total": costo_total,
            "costo_unitario": costo_unitario,
            # Backwards-compat aliases
            "costo_ingredientes": costo_material_directo,
            "costo_mano_obra": costo_mano_obra_directa,
            # CIF distribuido por producción mensual
            "cif_fijo_mensual": _cif_fijo,
            "cif_por_unidad": cif_por_unidad,
            "cif_lote": cif_lote,
            "produccion_mensual_usada": produccion_mensual_usada,
            "fuente_produccion_mensual": fuente_produccion_mensual,
            # Cobertura de stock
            "lotes_posibles_con_stock": lotes_posibles if lotes_posibles is not None else 0,
            "ingrediente_critico": ingrediente_critico,
            # Precio/margen
            "precio_venta_actual": precio_venta,
            "margen_actual_porcentaje": margen_actual,
            "margen_objetivo": margen_objetivo,
            "precio_sugerido": precio_sugerido,
            "detalle_ingredientes": detalle_ingredientes,
        }

    def calcular_precio_sugerido(self, costo: Decimal, margen_deseado: Decimal) -> dict:
        """
        Calcula el precio de venta sugerido para un margen deseado.

        Formula: precio = costo / (1 - margen)

        Args:
            costo: Costo del producto
            margen_deseado: Margen deseado en porcentaje (ej. 60 para 60%)

        Returns:
            dict con precio sugerido y analisis
        """
        if margen_deseado >= 100:
            raise ValueError("El margen debe ser menor a 100%")

        if margen_deseado < 0:
            raise ValueError("El margen no puede ser negativo")

        margen_decimal = margen_deseado / Decimal("100")
        precio_sugerido = costo / (Decimal("1") - margen_decimal)
        utilidad = precio_sugerido - costo

        return {
            "costo": float(costo),
            "margen_deseado_porcentaje": float(margen_deseado),
            "precio_sugerido": float(precio_sugerido.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "utilidad_por_unidad": float(utilidad.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        }

    def calcular_margen_real(self, costo: Decimal, precio_venta: Decimal) -> dict:
        """
        Calcula el margen real dado un costo y precio de venta.

        Formula: margen = (precio - costo) / precio * 100

        Args:
            costo: Costo del producto
            precio_venta: Precio de venta

        Returns:
            dict con margen y utilidad
        """
        if precio_venta <= 0:
            raise ValueError("El precio de venta debe ser mayor a 0")

        utilidad = precio_venta - costo
        margen = (utilidad / precio_venta) * 100

        rentable = margen > 0

        return {
            "costo": float(costo),
            "precio_venta": float(precio_venta),
            "utilidad_por_unidad": float(utilidad.quantize(Decimal("0.01"))),
            "margen_porcentaje": float(margen.quantize(Decimal("0.01"))),
            "es_rentable": rentable,
        }

    def calcular_punto_equilibrio(
        self, costo_fijo: Decimal, costo_variable_unitario: Decimal, precio_venta: Decimal
    ) -> dict:
        """
        Calcula el punto de equilibrio en unidades.

        Formula: PE = Costos Fijos / (Precio - Costo Variable)

        Args:
            costo_fijo: Costos fijos totales
            costo_variable_unitario: Costo variable por unidad
            precio_venta: Precio de venta por unidad

        Returns:
            dict con punto de equilibrio
        """
        margen_contribucion = precio_venta - costo_variable_unitario

        if margen_contribucion <= 0:
            raise ValueError("El margen de contribucion debe ser positivo. El precio debe ser mayor al costo variable.")

        punto_equilibrio_unidades = costo_fijo / margen_contribucion
        punto_equilibrio_ventas = punto_equilibrio_unidades * precio_venta

        return {
            "costo_fijo": float(costo_fijo),
            "costo_variable_unitario": float(costo_variable_unitario),
            "precio_venta": float(precio_venta),
            "margen_contribucion": float(margen_contribucion),
            "punto_equilibrio_unidades": float(punto_equilibrio_unidades.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "punto_equilibrio_ventas": float(punto_equilibrio_ventas.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        }

    def analizar_rentabilidad_producto(self, producto_id: UUID) -> dict:
        """
        Analiza la rentabilidad completa de un producto.
        Incluye costo de produccion si tiene receta.
        """
        producto = (
            self.db.query(Productos)
            .filter(Productos.id == producto_id, Productos.tenant_id == self.tenant_id, Productos.deleted_at.is_(None))
            .first()
        )

        if not producto:
            raise ValueError("Producto no encontrado")

        # Obtener costo del inventario
        inventario = (
            self.db.query(Inventarios)
            .filter(Inventarios.tenant_id == self.tenant_id, Inventarios.producto_id == producto_id)
            .first()
        )

        costo_inventario = Decimal("0.00")
        if inventario:
            costo_inventario = inventario.costo_promedio_ponderado

        # Verificar si tiene receta
        receta = (
            self.db.query(Recetas)
            .filter(
                Recetas.tenant_id == self.tenant_id,
                Recetas.producto_resultado_id == producto_id,
                Recetas.deleted_at.is_(None),
                Recetas.estado,
            )
            .first()
        )

        costo_receta = None
        if receta:
            costo_receta_data = self.calcular_costo_receta(receta.id)
            costo_receta = Decimal(str(costo_receta_data["costo_unitario"]))

        # Usar costo de receta si existe, sino costo de inventario
        costo_usado = costo_receta if costo_receta is not None else costo_inventario
        precio_venta = producto.precio_venta

        # Calcular margen
        margen_info = None
        if precio_venta > 0:
            margen_info = self.calcular_margen_real(costo_usado, precio_venta)

        return {
            "producto_id": str(producto_id),
            "codigo": producto.codigo_interno,
            "nombre": producto.nombre,
            "categoria": producto.categoria,
            "precio_venta": float(precio_venta),
            "costo_inventario": float(costo_inventario),
            "costo_receta": float(costo_receta) if costo_receta else None,
            "costo_usado": float(costo_usado),
            "tiene_receta": receta is not None,
            "receta_id": str(receta.id) if receta else None,
            "analisis_margen": margen_info,
        }


class ServicioProductos:
    """
    Servicio para operaciones CRUD de productos.
    """

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.calculadora = CalculadoraMargenes(db, tenant_id)

    def obtener_producto(self, producto_id: UUID) -> Optional[Productos]:
        """Obtiene un producto por ID."""
        return (
            self.db.query(Productos)
            .filter(Productos.id == producto_id, Productos.tenant_id == self.tenant_id, Productos.deleted_at.is_(None))
            .first()
        )

    def listar_productos(
        self,
        buscar: Optional[str] = None,
        categoria: Optional[str] = None,
        solo_activos: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Productos]:
        """Lista productos con filtros opcionales."""
        query = self.db.query(Productos).filter(Productos.tenant_id == self.tenant_id, Productos.deleted_at.is_(None))

        if solo_activos:
            query = query.filter(Productos.estado)

        if categoria:
            query = query.filter(Productos.categoria == categoria)

        if buscar:
            buscar_like = f"%{buscar}%"
            query = query.filter(
                or_(
                    Productos.nombre.ilike(buscar_like),
                    Productos.codigo_interno.ilike(buscar_like),
                    Productos.codigo_barras.ilike(buscar_like),
                )
            )

        return query.order_by(Productos.nombre).offset(skip).limit(limit).all()

    def obtener_productos_con_stock(self) -> List[dict]:
        """Obtiene productos con su informacion de stock."""
        query = (
            self.db.query(Productos, Inventarios.cantidad_disponible, Inventarios.costo_promedio_ponderado)
            .outerjoin(Inventarios, Productos.id == Inventarios.producto_id)
            .filter(Productos.tenant_id == self.tenant_id, Productos.deleted_at.is_(None), Productos.maneja_inventario)
            .order_by(Productos.nombre)
        )

        resultados = []
        for producto, cantidad, costo in query.all():
            resultados.append(
                {
                    "id": str(producto.id),
                    "codigo_interno": producto.codigo_interno,
                    "nombre": producto.nombre,
                    "categoria": producto.categoria,
                    "precio_venta": float(producto.precio_venta),
                    "stock_disponible": float(cantidad) if cantidad else 0.0,
                    "costo_promedio": float(costo) if costo else 0.0,
                    "stock_minimo": float(producto.stock_minimo) if producto.stock_minimo else None,
                    "alerta_stock": (
                        cantidad is not None and producto.stock_minimo is not None and cantidad <= producto.stock_minimo
                    ),
                }
            )

        return resultados

    def calcular_margen_producto(self, producto_id: UUID, precio_venta: Optional[Decimal] = None) -> dict:
        """
        Calcula el margen de un producto.
        Si se proporciona precio_venta, calcula con ese precio.
        Si no, usa el precio actual del producto.
        """
        return self.calculadora.analizar_rentabilidad_producto(producto_id)
