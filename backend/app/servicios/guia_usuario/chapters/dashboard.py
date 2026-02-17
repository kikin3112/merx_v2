"""
Capítulo 6: Dashboard y Reportes
KPIs, gráficos visuales y reportes avanzados para la toma de decisiones.
"""

from typing import List
from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class DashboardChapter:
    """
    Capítulo de Dashboard y Reportes para la guía de usuario.
    Cubre KPIs, gráficos visuales y reportes avanzados.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de dashboard.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de dashboard.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("6. Dashboard y Reportes", self.style_dict)

        # Introducción
        chapter.add_intro(
            "Este capítulo te guiará en el módulo de Dashboard y Reportes de Chandelier. "
            "Aprenderás a interpretar los indicadores clave de rendimiento (KPIs), "
            "visualizar datos mediante gráficos y utilizar los reportes avanzados "
            "para la toma de decisiones estratégicas."
        )

        chapter.add_spacer(0.3)

        # Sección: Dashboard Principal
        chapter.add_section(
            "6.1 Dashboard Principal",
            "El dashboard es la página principal que ves al iniciar sesión. "
            "Muestra una visión general del negocio con indicadores clave y tendencias.",
        )

        chapter.add_section(
            "6.1.1 KPIs del Dashboard",
            "Los indicadores clave de rendimiento (KPIs) muestran métricas esenciales:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Ventas Hoy",
                    "description": "Valor total de ventas del día actual",
                    "available": True,
                },
                {
                    "name": "Stock Bajo",
                    "description": "Cantidad de productos con stock por debajo del mínimo",
                    "available": True,
                },
                {
                    "name": "Pendientes de Cobro",
                    "description": "Valor total de facturas emitidas no pagadas",
                    "available": True,
                },
                {
                    "name": "Clientes Nuevos",
                    "description": "Clientes registrados en el período seleccionado",
                    "available": True,
                },
            ],
            ["KPI", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "6.1.2 Indicadores de Tendencia",
            "Cada KPI incluye un indicador de tendencia:\n"
            "• <b>▲ Verde:</b> Aumento vs período anterior\n"
            "• <b>▼ Rojo:</b> Disminución vs período anterior\n"
            "• <b>─ Gris:</b> Sin cambio significativo\n"
            "• <b>%:</b> Porcentaje de cambio (ej: +15.3%, -8.2%)",
        )

        chapter.add_screenshot_placeholder("Dashboard con KPIs y tendencias")

        chapter.add_section(
            "6.1.3 Selector de Período",
            "Los KPIs y gráficos muestran datos según el período seleccionado:\n"
            "• Hoy\n"
            "• Esta semana\n"
            "• Este mes\n"
            "• Este año\n"
            "• Personalizado (rango de fechas)",
        )

        chapter.add_spacer(0.3)

        # Sección: Gráficos
        chapter.add_section("6.2 Gráficos", "El dashboard incluye visualizaciones gráficas para analizar tendencias.")

        chapter.add_section(
            "6.2.1 Gráfico de Ventas (Línea)",
            "Muestra la evolución de las ventas en el tiempo:\n"
            "• Eje X: Período (días, semanas, meses)\n"
            "• Eje Y: Valor de ventas $\n"
            "• Interactivo: Hover muestra valores específicos\n"
            "• Leyenda: Identifica múltiples series de datos",
        )

        chapter.add_screenshot_placeholder("Gráfico de línea con ventas últimos 7 días")

        chapter.add_section(
            "6.2.2 Gráfico de Productos (Barras)",
            "Muestra los productos más vendidos:\n"
            "• Top 5 o Top 10 productos\n"
            "• Barras horizontales o verticales\n"
            "• Muestra cantidad Vendida y Valor total\n"
            "• Click en barra drilling-down al detalle",
        )

        chapter.add_screenshot_placeholder("Gráfico de barras con top productos")

        chapter.add_section(
            "6.2.3 Otros Gráficos",
            "Dependiendo de tu configuración, puedes encontrar:\n"
            "• <b>Gráfico de pastel:</b> Distribución por categoría\n"
            "• <b>Gráfico de área:</b> Acumulado en el tiempo\n"
            "• <b>Sparklines:</b> Mini gráficos en KPIs",
        )

        chapter.add_spacer(0.3)

        # Sección: Reportes Avanzados
        chapter.add_section(
            "6.3 Reportes Avanzados",
            "Más allá del dashboard básico, Chandelier ofrece reportes avanzados para análisis profundo del negocio.",
        )

        chapter.add_section(
            "6.3.1 Rentabilidad por Producto",
            "Analiza la ganancia por cada producto:\n"
            "• Lista todos los productos con ventas\n"
            "• Calcula: Ingresos - Costo = Utilidad\n"
            "• Porcentaje de margen: (Utilidad/Ingresos) × 100\n"
            "• Filtros: Período, Categoría, Cliente",
        )

        chapter.add_screenshot_placeholder("Reporte de rentabilidad por producto")

        chapter.add_section(
            "6.3.2 Rentabilidad por Categoría",
            "Agrupa la rentabilidad por categoría de productos:\n"
            "• Compara rendimiento entre categorías\n"
            "• Identifica categorías más/menos rentables\n"
            "• Útil para decisiones de inventario",
        )

        chapter.add_section(
            "6.3.3 Rentabilidad por Período",
            "Compara rentabilidad entre períodos:\n"
            "• Este mes vs mes anterior\n"
            "• Este año vs año anterior\n"
            "• Tendencias estacionales",
        )

        chapter.add_spacer(0.3)

        chapter.add_section(
            "6.4 Análisis ABC de Inventario",
            "Clasifica productos según su importancia en ventas:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Categoría A",
                    "description": "20% productos = 80% ventas (alta rotación)",
                    "available": True,
                },
                {
                    "name": "Categoría B",
                    "description": "30% productos = 15% ventas (mediana rotación)",
                    "available": True,
                },
                {
                    "name": "Categoría C",
                    "description": "50% productos = 5% ventas (baja rotación)",
                    "available": True,
                },
            ],
            ["Clase", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "6.4.1 Usos del Análisis ABC",
            "• <b>Gestión de inventario:</b> Priorizar control de categoría A\n"
            "• <b>Compras:</b> Negociar mejores precios con proveedores A\n"
            "• <b>Marketing:</b> Promocionar productos categoría B y C",
        )

        chapter.add_screenshot_placeholder("Análisis ABC con gráfico de Pareto")

        chapter.add_spacer(0.3)

        chapter.add_section(
            "6.5 Proyección de Flujo de Caja",
            "Estima la liquidez futura basándose en:\n"
            "• Cuentas por cobrar (facturas pendientes)\n"
            "• Cuentas por pagar (compromisos)\n"
            "• Ventas proyectadas\n"
            "• Gastos fijos estimados",
        )

        chapter.add_screenshot_placeholder("Proyección de flujo de caja a 30 días")

        chapter.add_spacer(0.3)

        chapter.add_section(
            "6.6 Comparativas de Período",
            "Compara el rendimiento entre períodos:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Mes a Mes (MoM)",
                    "description": "Este mes vs mes anterior",
                    "available": True,
                },
                {
                    "name": "Año a Año (YoY)",
                    "description": "Este año vs año anterior",
                    "available": True,
                },
                {
                    "name": "Acumulado vs Meta",
                    "description": "Ventas actuales vs objetivo",
                    "available": True,
                },
            ],
            ["Tipo", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "6.6.1 Qué Comparar",
            "• Ventas totales (unidades y valor)\n"
            "• Número de transacciones\n"
            "• Ticket promedio\n"
            "• Clientes nuevos vs recurrentes\n"
            "• Margen de ganancia",
        )

        chapter.add_spacer(0.3)

        chapter.add_section(
            "6.7 Top Clientes por Ventas",
            "Identifica tus mejores clientes:\n"
            "• Lista de clientes ordenada por valor total de compras\n"
            "• Muestra: Nombre, NIT, Total compras, Última compra\n"
            "• Porcentaje del total de ventas\n"
            "• Útil para programas de fidelización",
        )

        chapter.add_screenshot_placeholder("Top 10 clientes por ventas")

        chapter.add_spacer(0.3)

        chapter.add_section(
            "6.8 Análisis de Márgenes por Línea",
            "Compara márgenes por línea de producto:\n"
            "• Margen por categoría\n"
            "• Margen por tipo de producto\n"
            "• Tendencia del margen en el tiempo\n"
            "• Identificar líneas suboptimizadas",
        )

        chapter.add_screenshot_placeholder("Análisis de márgenes por línea")

        chapter.add_spacer(0.3)

        # Sección: Filtros
        chapter.add_section(
            "6.9 Filtros",
            "Todos los reportes y gráficos aceptan filtros:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Rango de Fechas",
                    "description": "Período específico para el análisis",
                    "available": True,
                },
                {
                    "name": "Categoría",
                    "description": "Filtrar por categoría de producto",
                    "available": True,
                },
                {
                    "name": "Cliente",
                    "description": "Análisis por cliente específico",
                    "available": True,
                },
                {
                    "name": "Producto",
                    "description": "Reporte de producto específico",
                    "available": True,
                },
            ],
            ["Filtro", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "6.9.1 Guardar Vistas",
            "Si usas frecuentemente los mismos filtros:\n"
            "1. Configura los filtros deseados\n"
            "2. Haz clic en 'Guardar Vista'\n"
            "3. Asigna un nombre\n"
            "4. Accede rápidamente desde el menú",
        )

        chapter.add_spacer(0.3)

        # Sección: Exportar
        chapter.add_section("6.10 Exportar Reportes", "Comparte los reportes fuera del sistema:")

        chapter.add_feature_table(
            [
                {
                    "name": "Excel (.xlsx)",
                    "description": "Exporta datos tabulares con formato",
                    "available": True,
                },
                {
                    "name": "PDF",
                    "description": "Exporta reporte con gráficos",
                    "available": True,
                },
                {
                    "name": "CSV",
                    "description": "Datos en formato plano",
                    "available": True,
                },
            ],
            ["Formato", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "6.10.1 Cómo Exportar",
            "1. Genera el reporte deseado\n"
            "2. Busca el botón 'Exportar' (habitualmente arriba/derecha)\n"
            "3. Selecciona el formato\n"
            "4. El archivo se descarga automáticamente",
        )

        chapter.add_spacer(0.3)

        # Sección: Funcionalidades
        chapter.add_section(
            "6.11 Funcionalidades de Dashboard",
            "Chandelier ofrece las siguientes funcionalidades:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "KPIs",
                    "description": "Indicadores clave de rendimiento con tendencias",
                    "available": True,
                },
                {
                    "name": "Gráficos",
                    "description": "Visualizaciones interactivas de datos",
                    "available": True,
                },
                {
                    "name": "Reportes Avanzados",
                    "description": "Análisis profundo más allá del dashboard",
                    "available": True,
                },
                {
                    "name": "Análisis ABC",
                    "description": "Clasificación de inventario por importancia",
                    "available": True,
                },
                {
                    "name": "Flujo de Caja",
                    "description": "Proyección de liquidez",
                    "available": True,
                },
                {
                    "name": "Comparativas",
                    "description": "MoM, YoY y vs metas",
                    "available": True,
                },
                {
                    "name": "Top Clientes",
                    "description": "Mejores clientes por ventas",
                    "available": True,
                },
                {
                    "name": "Exportar Excel",
                    "description": "Descarga reportes en formato Excel",
                    "available": True,
                },
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "6.12 Relación con Otros Módulos",
            "El dashboard integra datos de:\n"
            "• <b>Facturación:</b> Ventas, cobros, facturas\n"
            "• <b>Inventario:</b> Stock, alertas, rotación\n"
            "• <b>Clientes:</b> Nuevos, recurrentes, top\n"
            "• <b>Contabilidad:</b> Ingresos, gastos, rentabilidad",
        )

        return chapter.build()
