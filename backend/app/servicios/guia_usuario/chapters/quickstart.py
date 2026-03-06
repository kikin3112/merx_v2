"""
Capítulo 1: Quick Start (Inicio Rápido)
Ayuda a nuevos usuarios a comenzar con chandelierp en menos de 5 minutos.
"""

from typing import List

from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class QuickStartChapter:
    """
    Capítulo de Inicio Rápido para la guía de usuario.
    Incluye introducción, primer inicio de sesión y tour del dashboard.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de inicio rápido.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de inicio rápido.

        Returns:
            Lista de elementos Platypus (Paragraph, Spacer, Table)
        """
        chapter = ChapterBuilder("1. Inicio Rápido", self.style_dict)

        # Introducción
        chapter.add_intro(
            "Este capítulo te guiará para comenzar a usar chandelierp en menos de 5 minutos. "
            "Aprenderás a acceder al sistema, iniciar sesión y navegar por el dashboard principal."
        )

        chapter.add_spacer(0.3)

        # Sección 1: ¿Qué es chandelierp?
        chapter.add_section(
            "1.1 ¿Qué es chandelierp?",
            "chandelierp es un sistema ERP/POS diseñado para microempresarios y emprendedores en Colombia — "
            "velas, confites, ropa, alimentos, artesanías, servicios de belleza y más. Incluye gestión de "
            "productos, inventario, facturas, cotizaciones, clientes y contabilidad básica. El sistema es "
            "multi-tenant, lo que significa que cada empresa tiene su propio espacio de trabajo seguro.",
        )

        chapter.add_section(
            "1.2 Requisitos del Sistema",
            "Para usar chandelierp necesitas:\n"
            "<br/>• Navegador web actualizado (Chrome, Firefox, Edge o Safari)\n"
            "<br/>• Conexión a internet estable\n"
            "<br/>• Credenciales de acceso proporcionadas por tu administrador",
        )

        chapter.add_spacer(0.3)

        # Sección 2: Primer Inicio de Sesión
        chapter.add_section("1.3 Primer Inicio de Sesión", "Sigue estos pasos para acceder al sistema por primera vez:")

        chapter.add_step_list(
            [
                "Abre tu navegador e ingresa la URL de chandelierp proporcionada por tu empresa",
                "En la pantalla de login, ingresa tu correo electrónico y contraseña",
                "Si perteneces a varias empresas, selecciona el tenant (empresa) al que deseas acceder",
                "Una vez autenticado, verás el dashboard principal",
            ],
            "Pasos para iniciar sesión",
        )

        chapter.add_screenshot_placeholder("Pantalla de inicio de sesión con campos de email y contraseña")

        chapter.add_spacer(0.3)

        # Sección 3: Tour del Dashboard
        chapter.add_section(
            "1.4 Tour del Dashboard",
            "El dashboard es la pantalla principal que te da una visión general de tu negocio. "
            "Aquí encontrarás los indicadores clave de rendimiento (KPIs) y acceso rápido a las funciones principales.",
        )

        chapter.add_section(
            "1.4.1 Indicadores Clave de Rendimiento (KPIs)",
            "En la parte superior del dashboard verás tarjetas con información importante:\n"
            "<br/>• <b>Ventas Hoy:</b> Total de ventas del día actual\n"
            "<br/>• <b>Stock Bajo:</b> Productos que requieren reposición\n"
            "<br/>• <b>Pendientes de Cobro:</b> Facturas pendientes de pago",
        )

        chapter.add_section(
            "1.4.2 Navegación Principal",
            "La barra lateral izquierda contiene el menú de navegación:\n"
            "<br/>• <b>Dashboard:</b> Vista general del negocio\n"
            "<br/>• <b>Ventas:</b> Punto de venta (POS), facturas, cotizaciones\n"
            "<br/>• <b>Inventario:</b> Productos, recetas, movimientos de stock\n"
            "<br/>• <b>Contabilidad:</b> Asientos contables y PUC\n"
            "<br/>• <b>Configuración:</b> Datos de la empresa y usuarios",
        )

        chapter.add_screenshot_placeholder("Dashboard con anotaciones indicando KPIs y navegación")

        chapter.add_spacer(0.3)

        # Tips adicionales
        chapter.add_section(
            "1.5 Consejos Útiles",
            "• Usa el selector de tenant en la parte superior para cambiar entre empresas\n"
            "• El botón de búsqueda (o Ctrl+K) te permite encontrar productos rápidamente\n"
            "• Cada sección tiene su propio menú contextual en el engranaje (⚙️)",
        )

        return chapter.build()
