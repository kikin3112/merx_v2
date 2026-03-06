"""
Capítulo 3: Productos e Inventario
Gestión de productos, tipos, valorización y alertas de stock.
"""

from typing import List

from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class ProductsChapter:
    """
    Capítulo de Productos e Inventario para la guía de usuario.
    Cubre CRUD de productos, tipos, valorización y alertas.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de productos.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de productos.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("3. Productos e Inventario", self.style_dict)

        # Introducción
        chapter.add_intro(
            "Este capítulo te guiará en la gestión de productos y el control de inventario. "
            "Aprenderás a crear productos, diferenciar entre tipos, configurar alertas de stock "
            "y entender el sistema de valorización de inventario."
        )

        chapter.add_spacer(0.3)

        # Sección: Crear Producto
        chapter.add_section("3.1 Crear Producto", "Para crear un nuevo producto en el inventario, sigue estos pasos:")

        chapter.add_step_list(
            [
                "Navega a Inventario > Productos en el menú lateral",
                "Haz clic en el botón 'Nuevo Producto' (+)",
                "Completa los campos del formulario: SKU, nombre, tipo, categoría, precio, costo, stock inicial, IVA",
                "Configura la alerta de stock mínimo (opcional)",
                "Haz clic en 'Guardar' para crear el producto",
            ],
            "Pasos para crear un producto",
        )

        chapter.add_screenshot_placeholder("Formulario de creación de producto con campos")

        chapter.add_section(
            "3.1.1 Campos del Formulario",
            "• <b>SKU:</b> Código único del producto (ej: PROD-001)\n"
            "• <b>Nombre:</b> Nombre descriptivo del producto\n"
            "• <b>Tipo:</b> Producto terminado o Materia prima\n"
            "• <b>Categoría:</b> Clasificación del producto (opcional)\n"
            "• <b>Precio de venta:</b> Precio al que vendes el producto\n"
            "• <b>Precio de costo:</b> Costo de adquisición/producción\n"
            "• <b>Stock inicial:</b> Cantidad actual en inventario\n"
            "• <b>Tarifa IVA:</b> Porcentaje de IVA aplicable (default 19%)",
        )

        chapter.add_spacer(0.3)

        # Sección: Tipos de Producto
        chapter.add_section("3.2 Tipos de Producto", "Chandelier distingue entre dos tipos de productos:")

        chapter.add_feature_table(
            [
                {
                    "name": "Producto Terminado",
                    "description": "Artículos listos para venta (ej: Crema Corporal 200ml, Pack regalo)",
                    "available": True,
                },
                {
                    "name": "Materia Prima",
                    "description": "Insumos para producción (ej: Harina de trigo, Mantequilla, Saborizante)",
                    "available": True,
                },
            ],
            ["Tipo", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "3.2.1 Diferencias Clave",
            "• Los <b>productos terminados</b> pueden tener recetas (BOM) asociadas\n"
            "• Las <b>materias primas</b> se consumen al producir productos terminados\n"
            "• El sistema valida que una receta solo use materias primas como ingredientes",
        )

        chapter.add_spacer(0.3)

        # Sección: Valorización de Inventario
        chapter.add_section(
            "3.3 Valorización de Inventario",
            "Chandelier utiliza el método de <b>Costo Promedio Ponderado (CPP)</b> "
            "para valorar el inventario. Este método promedia el costo de todas las entradas.",
        )

        chapter.add_section(
            "3.3.1 Fórmula del Costo Promedio Ponderado",
            "CPP = (Stock actual × Costo actual + Entrada × Costo nuevo) / (Stock actual + Entrada)",
        )

        chapter.add_section(
            "3.3.2 Ejemplo Práctico",
            "Supongamos que tienes 10 unidades de un producto a $10.000 c/u:\n"
            "<br/><b>Stock actual:</b> 10 unidades\n"
            "<br/><b>Costo actual:</b> $10.000\n"
            "<br/><b>Entrada nueva:</b> 5 unidades a $12.000 c/u\n"
            "<br/><br/>"
            "CPP = (10 × 10.000 + 5 × 12.000) / (10 + 5)\n"
            "CPP = (100.000 + 60.000) / 15\n"
            "CPP = $160.000 / 15 = $10.667 por unidad",
        )

        chapter.add_screenshot_placeholder("Historial de movimientos de stock con costos")

        chapter.add_spacer(0.3)

        # Sección: Alertas de Stock
        chapter.add_section(
            "3.4 Alertas de Stock",
            "Configura alertas para recibir notificaciones cuando el inventario baje de cierto nivel.",
        )

        chapter.add_section(
            "3.4.1 Configurar Alerta de Stock",
            "1. Al crear/editar un producto, ingresa el valor en 'Alerta stock mínimo'\n"
            "2. Cuando el stock caiga por debajo, aparecerá en la sección 'Alertas de Stock'\n"
            "3. El dashboard también mostrará el conteo de productos con stock bajo",
        )

        chapter.add_screenshot_placeholder("Lista de productos con stock bajo (resaltado en amarillo)")

        chapter.add_section(
            "3.4.2 Ejemplo de Alerta",
            "Si configuras 'Alerta stock mínimo' = 5, el sistema te alertará cuando "
            "queden 4 o menos unidades. Esto te permite reponer a tiempo.",
        )

        chapter.add_spacer(0.3)

        # Sección: Movimientos de Stock
        chapter.add_section(
            "3.5 Movimientos de Stock", "Cada operación que modifica el inventario queda registrada como un movimiento:"
        )

        chapter.add_feature_table(
            [
                {"name": "Entrada", "description": "Compra o recepción de mercancía", "available": True},
                {"name": "Salida", "description": "Venta o consumo de materiales", "available": True},
                {"name": "Ajuste", "description": "Corrección de inventario (sobrante/faltante)", "available": True},
                {
                    "name": "Producción",
                    "description": "Creación de productos terminados desde materias primas",
                    "available": True,
                },
            ],
            ["Tipo", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "3.5.1 Ver Historial de Movimientos",
            "Para ver el historial:\n"
            "1. Ve a Inventario > Movimientos\n"
            "2. Filtra por producto, tipo de movimiento o fecha\n"
            "3. Cada movimiento muestra: fecha, tipo, cantidad, costo unitario, referencia",
        )

        chapter.add_screenshot_placeholder("Tabla de movimientos de stock con filtros")

        chapter.add_spacer(0.3)

        # Sección: Resumen de funcionalidades
        chapter.add_section(
            "3.6 Funcionalidades de Productos",
            "Chandelier ofrece las siguientes funcionalidades para gestión de productos:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "CRUD Productos",
                    "description": "Crear, leer, actualizar, eliminar productos",
                    "available": True,
                },
                {"name": "Categorías", "description": "Agrupar productos por categoría", "available": True},
                {
                    "name": "Alertas de Stock",
                    "description": "Notificaciones cuando el stock baje del mínimo",
                    "available": True,
                },
                {
                    "name": "Costo Promedio Ponderado",
                    "description": "Valorización automática del inventario",
                    "available": True,
                },
                {
                    "name": "Historial de Movimientos",
                    "description": "Trazabilidad completa del inventario",
                    "available": True,
                },
                {"name": "Recetas (BOM)", "description": "Definir配方 para productos terminados", "available": True},
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        return chapter.build()
