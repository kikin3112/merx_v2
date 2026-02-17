"""
Capítulo 4: Calculadora de Márgenes
Herramienta para calcular precios de venta basados en costo y margen deseado.
"""

from typing import List
from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class MarginCalculatorChapter:
    """
    Capítulo de Calculadora de Márgenes para la guía de usuario.
    Explica cómo calcular el precio de venta óptimo.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de calculadora de márgenes.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de calculadora de márgenes.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("4. Calculadora de Márgenes", self.style_dict)

        # Introducción
        chapter.add_intro(
            "La Calculadora de Márgenes es una herramienta integrada en el formulario de productos "
            "que te ayuda a determinar el precio de venta óptimo basándote en el costo y el margen "
            "de ganancia deseado. Esto asegura que tus productos sean rentables."
        )

        chapter.add_spacer(0.3)

        # Sección: ¿Cómo funciona?
        chapter.add_section(
            "4.1 ¿Cómo Funciona la Calculadora?",
            "La calculadora utiliza una fórmula simple pero poderosa para determinar el precio:",
        )

        chapter.add_section(
            "4.1.1 Fórmula del Margen",
            "<b>Precio de Venta = Costo / (1 - Margen / 100)</b>\n"
            "\n"
            "Donde:\n"
            "• <b>Costo:</b> Precio de adquisición o producción del producto\n"
            "• <b>Margen:</b> Porcentaje de ganancia deseado (0-99%)",
        )

        chapter.add_section(
            "4.1.2 Ejemplo Práctico",
            "Supongamos que tienes un producto con las siguientes características:\n"
            "<br/>• <b>Costo:</b> $1.614\n"
            "• <b>Margen deseado:</b> 60%\n"
            "<br/><br/>"
            "<b>Cálculo:</b>\n"
            "Precio = 1.614 / (1 - 60/100)\n"
            "Precio = 1.614 / 0.40\n"
            "<b>Precio = $4.035</b>\n"
            "<br/><br/>"
            "Con un costo de $1.614 y un margen del 60%, el precio de venta sugerido es $4.035",
        )

        chapter.add_screenshot_placeholder("Calculadora de márgenes en formulario de producto")

        chapter.add_spacer(0.3)

        # Sección: Usar la calculadora
        chapter.add_section(
            "4.2 Cómo Usar la Calculadora", "Sigue estos pasos para utilizar la calculadora de márgenes:"
        )

        chapter.add_step_list(
            [
                "Al crear o editar un producto, ingresa el 'Precio de costo'",
                "En el campo 'Margen (%)', ingresa el porcentaje de ganancia deseado",
                "La calculadora mostrará automáticamente el 'Precio de venta sugerido'",
                "Puedes aceptar el precio sugerido o ajustarlo manualmente",
                "Guarda el producto con el precio final",
            ],
            "Pasos para usar la calculadora",
        )

        chapter.add_section(
            "4.2.1 Ejemplo en el Formulario",
            "En el formulario de producto verás una sección como esta:\n"
            "<br/><b>Costo:</b> [1.614]\n"
            "<br/><b>Margen (%):</b> [60]\n"
            "<br/><b>→ Precio sugerido:</b> $4.035\n"
            "<br/><br/>"
            "La calculadora se actualiza en tiempo real mientras escribes.",
        )

        chapter.add_spacer(0.3)

        # Sección: Consideraciones
        chapter.add_section(
            "4.3 Consideraciones Importantes",
            "• <b>Margen vs Ganancia:</b> El margen es el porcentaje del precio de venta, no del costo\n"
            "• <b>Límites:</b> El margen debe estar entre 0% y 99% (99% significaría casi todo es ganancia)\n"
            "• <b>IVA:</b> El precio sugerido no incluye IVA; este se suma al precio final\n"
            "• <b>Competencia:</b> Considera los precios de tu competencia al ajustar el margen",
        )

        chapter.add_section(
            "4.3.1 Relación entre Margen y Ganancia",
            "Es importante entender la diferencia:\n"
            "<br/>• <b>Margen del 50%:</b> Ganas $1 por cada $1 de costo (precio $2)\n"
            "<br/>• <b>Margen del 60%:</b> Ganas $1.50 por cada $1 de costo (precio $2.50)\n"
            "<br/>• <b>Margen del 70%:</b> Ganas $2.33 por cada $1 de costo (precio $3.33)\n"
            "\n"
            "A mayor margen, mayor ganancia por unidad vendida.",
        )

        chapter.add_spacer(0.3)

        # Sección: Beneficios
        chapter.add_section(
            "4.4 Beneficios de Usar la Calculadora",
            "• <b>Consistencia:</b> Aplica el mismo margen a todos tus productos\n"
            "• <b>Rentabilidad:</b> Asegura que cada venta genere la ganancia esperada\n"
            "• <b>Rapidez:</b> Calcula precios mentalmente en segundos\n"
            "• <b>Decisiones informadas:</b> Ajusta márgenes según tus objetivos de negocio",
        )

        return chapter.build()
