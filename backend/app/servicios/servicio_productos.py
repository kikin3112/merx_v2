"""
Servicio de Productos.
Incluye CalculadoraMargenes para analisis de costos y rentabilidad.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..datos.modelos import Inventarios, Productos, Recetas
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class CalculadoraMargenes:
    """
    Calculadora de margenes y rentabilidad para productos.
    Permite calcular costos, precios sugeridos y margenes reales.
    """

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def calcular_costo_receta(self, receta_id: UUID) -> dict:
        """
        Calcula el costo total de una receta.

        Returns:
            dict con desglose de costos
        """
        receta = (
            self.db.query(Recetas)
            .filter(Recetas.id == receta_id, Recetas.tenant_id == self.tenant_id, Recetas.deleted_at.is_(None))
            .first()
        )

        if not receta:
            raise ValueError("Receta no encontrada")

        # Calcular costo de ingredientes
        costo_ingredientes = Decimal("0.00")
        detalle_ingredientes = []

        for ing in receta.ingredientes:
            # Obtener costo promedio del inventario
            inventario = (
                self.db.query(Inventarios)
                .filter(Inventarios.tenant_id == self.tenant_id, Inventarios.producto_id == ing.producto_id)
                .first()
            )

            costo_unitario = Decimal("0.00")
            if inventario:
                costo_unitario = inventario.costo_promedio_ponderado

            costo_linea = ing.cantidad * costo_unitario
            costo_ingredientes += costo_linea

            detalle_ingredientes.append(
                {
                    "producto_id": str(ing.producto_id),
                    "producto_nombre": ing.producto.nombre if ing.producto else "N/A",
                    "cantidad": float(ing.cantidad),
                    "unidad": ing.unidad,
                    "costo_unitario": float(costo_unitario),
                    "costo_linea": float(costo_linea),
                }
            )

        # Costo total (ingredientes + mano obra)
        costo_total = costo_ingredientes + receta.costo_mano_obra

        # Costo por unidad producida
        costo_unitario = Decimal("0.00")
        if receta.cantidad_resultado > 0:
            costo_unitario = costo_total / receta.cantidad_resultado

        # Obtener precio de venta del producto resultado
        precio_venta = Decimal("0.00")
        margen_actual = Decimal("0.00")
        if receta.producto_resultado:
            precio_venta = receta.producto_resultado.precio_venta
            if precio_venta > 0:
                margen_actual = ((precio_venta - costo_unitario) / precio_venta) * 100

        return {
            "receta_id": str(receta_id),
            "receta_nombre": receta.nombre,
            "producto_resultado_id": str(receta.producto_resultado_id),
            "cantidad_resultado": float(receta.cantidad_resultado),
            "costo_ingredientes": float(costo_ingredientes),
            "costo_mano_obra": float(receta.costo_mano_obra),
            "costo_total": float(costo_total),
            "costo_unitario": float(costo_unitario),
            "precio_venta_actual": float(precio_venta),
            "margen_actual_porcentaje": float(margen_actual.quantize(Decimal("0.01"))),
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
            raise ValueError(
                "El margen de contribucion debe ser positivo. " "El precio debe ser mayor al costo variable."
            )

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
