"""
Capítulo 4: Recetas (Lista de Materiales)
Gestión de fórmulas para productos terminados, simulación y ejecución de producción.
"""

from typing import List
from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class RecipesChapter:
    """
    Capítulo de Recetas (BOM) para la guía de usuario.
    Crea, simula y ejecuta la producción de productos terminados.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de recetas.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de recetas.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("4. Recetas (Lista de Materiales)", self.style_dict)

        # Introducción
        chapter.add_intro(
            "Este capítulo te guiará en la gestión de recetas (Bill of Materials - BOM). "
            "Aprenderás a crear fórmulas para tus productos terminados, simular la producción "
            "antes de ejecutarla y registrar automáticamente los movimientos de inventario."
        )

        chapter.add_spacer(0.3)

        # Sección: ¿Qué es una Receta?
        chapter.add_section(
            "4.1 ¿Qué es una Receta?",
            "Una receta (o Lista de Materiales - BOM) define los ingredientes necesarios "
            "para producir una unidad de producto terminado. En el contexto de velas, "
            "una receta especifica qué materias primas (cera, fragancia, colorante, pabilo) "
            "y en qué cantidades se necesitan para crear cada unidad.",
        )

        chapter.add_section(
            "4.1.1 Componentes de una Receta",
            "• <b>Producto terminado:</b> El producto final que se fabricará\n"
            "• <b>Rendimiento:</b> Número de unidades que se producen\n"
            "• <b>Materias primas:</b> Insumos necesarios con sus cantidades\n"
            "• <b>Unidad de medida:</b> gramos (g), mililitros (ml) o unidades (ud)",
        )

        chapter.add_screenshot_placeholder("Ejemplo de receta para vela de soja 200g")

        chapter.add_spacer(0.3)

        # Sección: Crear Receta
        chapter.add_section("4.2 Crear Receta", "Para crear una nueva receta, sigue estos pasos:")

        chapter.add_step_list(
            [
                "Navega a Inventario > Recetas en el menú lateral",
                "Haz clic en el botón 'Nueva Receta' (+)",
                "Selecciona el producto terminado (debe existir previamente)",
                "Define el rendimiento (unidades que produce la receta)",
                "Agrega las materias primas necesarias",
                "Para cada materia prima: selecciona el producto, especifica cantidad y unidad",
                "Revisa el consumo total y guarda la receta",
            ],
            "Pasos para crear una receta",
        )

        chapter.add_screenshot_placeholder("Formulario de creación de receta")

        chapter.add_section(
            "4.2.1 Campos del Formulario",
            "• <b>Producto terminado:</b> Selecciona de tus productos existentes (tipo: producto terminado)\n"
            "• <b>Rendimiento:</b> Cantidad de unidades que produce esta receta (ej: 1, 6, 12)\n"
            "• <b>Materia prima:</b> Selecciona de tus productos (tipo: materia prima)\n"
            "• <b>Cantidad:</b> Cantidad necesaria de esa materia prima\n"
            "• <b>Unidad:</b> g (gramos), ml (mililitros), ud (unidades)",
        )

        chapter.add_section(
            "4.2.2 Ejemplo: Receta para Vela de Soja 200g",
            "<b>Producto:</b> Vela Aromática Lavanda 200g\n"
            "<b>Rendimiento:</b> 1 unidad\n"
            "<br/><b>Materias primas:</b>\n"
            "• Cera de soja: 180 g\n"
            "• Fragancia lavanda: 18 ml\n"
            "• Pabilo de algodón: 1 ud\n"
            "• Colorante violeta (opcional): 0.5 g",
        )

        chapter.add_screenshot_placeholder("Lista de materias primas en la receta")

        chapter.add_spacer(0.3)

        # Sección: Simulador de Producción
        chapter.add_section(
            "4.3 Simulador de Producción",
            "Antes de ejecutar una producción, usa el simulador para verificar "
            "que tienes suficientes materias primas en inventario.",
        )

        chapter.add_section(
            "4.3.1 Cómo Usar el Simulador",
            "1. En la lista de recetas, selecciona la receta deseada\n"
            "2. Ingresa la cantidad de unidades que deseas producir\n"
            "3. El sistema calcula automáticamente:\n"
            "   - Materias primas necesarias para esa cantidad\n"
            "   - Stock disponible actualmente\n"
            "   - Indicador de disponibilidad (verde/amarillo/rojo)\n"
            "4. Si hay escasez, el sistema muestra alertas indicando cuánto falta",
        )

        chapter.add_screenshot_placeholder("Simulador de producción con cálculos")

        chapter.add_section(
            "4.3.2 Indicadores de Stock",
            "• <b>Verde (✓):</b> Stock suficiente disponible\n"
            "• <b>Amarillo (!):</b> Stock justo, menos del 20% sobre lo necesario\n"
            "• <b>Rojo (✗):</b> Stock insuficiente, falta material",
        )

        chapter.add_section(
            "4.3.3 Ejemplo de Simulación",
            "Producir 50 velas de 200g requiere:\n"
            "• Cera de soja: 9.0 kg (disponible: 5.2 kg) → ⚠️ FALTAN 3.8 kg\n"
            "• Fragancia lavanda: 900 ml (disponible: 850 ml) → ⚠️ FALTAN 50 ml\n"
            "• Pabilo: 50 ud (disponible: 200 ud) → ✓ SUFICIENTE\n"
            "<br/>Resultado: No se puede producir - Stock insuficiente",
        )

        chapter.add_spacer(0.3)

        # Sección: Producir
        chapter.add_section(
            "4.4 Producir",
            "Una vez verificado el stock, ejecuta la producción para registrar "
            "automáticamente los movimientos de inventario.",
        )

        chapter.add_section(
            "4.4.1 Pasos para Producir",
            "1. Desde la receta o simulador, haz clic en 'Producir Ahora'\n"
            "2. Ingresa la cantidad a producir\n"
            "3. El sistema valida que el stock sea suficiente\n"
            "4. Confirma la producción\n"
            "5. El sistema crea automáticamente:\n"
            "   - Movimiento de SALIDA por cada materia prima\n"
            "   - Movimiento de PRODUCCIÓN (entrada) para el producto terminado\n"
            "   - Actualiza el costo promedio ponderado",
        )

        chapter.add_screenshot_placeholder("Confirmación de producción")

        chapter.add_section(
            "4.4.2 Movimientos Automáticos",
            "Al producir 50 unidades con la receta del ejemplo:\n"
            "<br/><b>Movimientos de salida (materias primas):</b>\n"
            "• Cera de soja: -9.0 kg\n"
            "• Fragancia lavanda: -900 ml\n"
            "• Pabilo: -50 ud\n"
            "<br/><b>Movimiento de entrada (producto terminado):</b>\n"
            "• Vela Aromática Lavanda 200g: +50 ud",
        )

        chapter.add_spacer(0.3)

        # Sección: Validaciones
        chapter.add_section(
            "4.5 Validaciones",
            "El sistema realiza validaciones automáticas para garantizar la integridad del inventario:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Stock suficiente",
                    "description": "Valida que cada materia prima tenga stock >= cantidad necesaria",
                    "available": True,
                },
                {
                    "name": "Tipo de producto",
                    "description": "Solo permite materias primas en las recetas, no productos terminados",
                    "available": True,
                },
                {
                    "name": "Producto existente",
                    "description": "El producto terminado debe existir antes de crear la receta",
                    "available": True,
                },
                {
                    "name": "Costo promedio",
                    "description": "Recalcula automáticamente el costo promedio ponderado tras producción",
                    "available": True,
                },
            ],
            ["Validación", "Descripción", "Disponible"],
        )

        chapter.add_screenshot_placeholder("Mensaje de error por stock insuficiente")

        chapter.add_spacer(0.3)

        # Sección: Funcionalidades
        chapter.add_section(
            "4.6 Funcionalidades de Recetas",
            "Chandelier ofrece las siguientes funcionalidades para gestión de recetas:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Crear Receta",
                    "description": "Definir fórmula con producto terminado, rendimiento y materias primas",
                    "available": True,
                },
                {
                    "name": "Simulador de Producción",
                    "description": "Calcular所需材料 antes de producir, validar stock disponible",
                    "available": True,
                },
                {
                    "name": "Producción Automática",
                    "description": "Ejecutar producción con registro automático de movimientos",
                    "available": True,
                },
                {
                    "name": "Control de Stock",
                    "description": "Validar stock suficiente antes de permitir producción",
                    "available": True,
                },
                {
                    "name": "Valorización Automática",
                    "description": "Actualizar costos promedio ponderados tras cada producción",
                    "available": True,
                },
                {
                    "name": "Historial de Producciones",
                    "description": "Ver historial completo de producciones ejecutadas",
                    "available": True,
                },
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "4.7 Relación con Otros Módulos",
            "Las recetas se integran con los siguientes módulos:\n"
            "• <b>Productos:</b> Las materias primas se seleccionan del inventario de productos\n"
            "• <b>Movimientos de Stock:</b> Cada producción genera movimientos automáticos\n"
            "• <b>Contabilidad:</b> Los costos de producción afectan el asiento contable",
        )

        return chapter.build()
