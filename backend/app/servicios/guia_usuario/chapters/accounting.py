"""
Capítulo 5: Contabilidad
PUC Colombia, asientos manuales, asientos automáticos y estados financieros.
"""

from typing import List
from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class AccountingChapter:
    """
    Capítulo de Contabilidad para la guía de usuario.
    Cubre PUC Colombia, asientos manuales, asientos automáticos y estados financieros.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de contabilidad.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de contabilidad.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("5. Contabilidad", self.style_dict)

        # Introducción
        chapter.add_intro(
            "Este capítulo te guiará en el módulo de contabilidad de Chandelier. "
            "Aprenderás sobre el PUC Colombia, cómo crear asientos contables, "
            "entender los asientos automáticos generados por el sistema "
            "y cómo generar estados financieros básicos."
        )

        chapter.add_spacer(0.3)

        # Sección: PUC Colombia
        chapter.add_section(
            "5.1 PUC Colombia",
            "El Plan Único de Cuentas (PUC) es el marco normativo que define "
            "la estructura de cuentas contables en Colombia. Chandelier incluye "
            "un PUC pre-configurado con las cuentas esenciales para tu negocio.",
        )

        chapter.add_section(
            "5.1.1 Estructura del PUC",
            "El PUC se organiza en niveles jerárquicos:\n"
            "• <b>Nivel 1:</b> Clase (1-Activo, 2-Pasivo, 3-Patrimonio, 4-Ingresos, 5-Gastos)\n"
            "• <b>Nivel 2:</b> Grupo\n"
            "• <b>Nivel 3:</b> Cuenta\n"
            "• <b>Nivel 4:</b> Subcuenta",
        )

        chapter.add_screenshot_placeholder("Lista de cuentas PUC con jerarquía")

        chapter.add_section(
            "5.1.2 Cuentas Principales",
            "Chandelier incluye ~40 cuentas pre-cargadas. Las más utilizadas son:",
        )

        chapter.add_feature_table(
            [
                {"name": "1105", "description": "Caja - Dinero en efectivo", "available": True},
                {"name": "1110", "description": "Bancos - Cuentas corrientes", "available": True},
                {"name": "1305", "description": "Clientes - Cuentas por cobrar", "available": True},
                {"name": "1435", "description": "Inventario PT - Productos terminados", "available": True},
                {"name": "1430", "description": "Inventario MP - Materias primas", "available": True},
                {"name": "2205", "description": "Proveedores - Cuentas por pagar", "available": True},
                {"name": "2408", "description": "IVA por pagar", "available": True},
                {"name": "2412", "description": "IVA descontable", "available": True},
                {"name": "4135", "description": "Comercio al por mayor/menor - Ventas", "available": True},
                {"name": "5105", "description": "Gastos de personal", "available": True},
                {"name": "5110", "description": "Gastos generales", "available": True},
                {"name": "6135", "description": "Costo de ventas", "available": True},
            ],
            ["Código", "Nombre", "Disponible"],
        )

        chapter.add_section(
            "5.1.3 Acceso al PUC",
            "Para ver el PUC completo:\n"
            "1. Navega a Contabilidad > PUC en el menú lateral\n"
            "2. Verás la lista de cuentas organizadas por clase\n"
            "3. Puedes buscar por código o nombre\n"
            "4. Las cuentas que aceptan movimientos están marcadas",
        )

        chapter.add_spacer(0.3)

        # Sección: Asientos Contables
        chapter.add_section(
            "5.2 Asientos Contables",
            "Un asiento contable registra una transacción financiera. "
            "Cada asiento tiene una fecha, descripción y una o más líneas "
            "que deben cuadrarse (total Debe = total Haber).",
        )

        chapter.add_section(
            "5.2.1 Crear Asiento Manual",
            "Para crear un asiento contable manual:",
        )

        chapter.add_step_list(
            [
                "Navega a Contabilidad > Asientos en el menú lateral",
                "Haz clic en el botón 'Nuevo Asiento' (+)",
                "Selecciona la fecha del asiento",
                "Agrega una descripción (ej: 'Compra mercancía', 'Pago servicios')",
                "Agrega las líneas del asiento:",
                "  - Selecciona la cuenta PUC",
                "  - Ingresa valor en Debe o en Haber (no ambos)",
                "  - Agrega descripción de la línea (opcional)",
                "Repite hasta completar todas las transacciones",
                "Verifica que el asiento esté cuadrado (Δ Debe = Δ Haber)",
                "Haz clic en 'Guardar'",
            ],
            "Pasos para crear un asiento contable",
        )

        chapter.add_screenshot_placeholder("Formulario de asiento contable")

        chapter.add_section(
            "5.2.2 Estructura de un Asiento",
            "• <b>Fecha:</b> Día de la transacción\n"
            "• <b>Descripción:</b> Resumen general del asiento\n"
            "• <b>Líneas:</b> Cada línea tiene cuenta, valor en Debe o Haber\n"
            "• <b>Debe:</b> Valores que entran al patrimonio (activo, gasto)\n"
            "• <b>Haber:</b> Valores que salen del patrimonio (pasivo, ingreso)",
        )

        chapter.add_section(
            "5.2.3 Ejemplo de Asiento",
            "Compra de mercancía por $500.000:\n"
            "<br/><b>Línea 1 (Debe):</b>\n"
            "• Cuenta: 1430 Inventario MP\n"
            "• Valor: $500.000 (Debe)\n"
            "<br/><b>Línea 2 (Haber):</b>\n"
            "• Cuenta: 1105 Caja\n"
            "• Valor: $500.000 (Haber)\n"
            "<br/><b>Total:</b> Debe $500.000 = Haber $500.000 ✓",
        )

        chapter.add_screenshot_placeholder("Asiento de compra con cuadratura")

        chapter.add_spacer(0.3)

        # Sección: Asientos Automáticos
        chapter.add_section(
            "5.3 Asientos Automáticos",
            "Chandelier genera automáticamente asientos contables "
            "cuando se realizan ciertas operaciones en el sistema.",
        )

        chapter.add_section(
            "5.3.1 Asiento de Venta",
            "Cuando se emite una factura, el sistema crea automáticamente:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Debe",
                    "description": "1105 Caja o 1305 Clientes",
                    "available": True,
                },
                {
                    "name": "Haber",
                    "description": "4135 Ventas (subtotal) + 2408 IVA por pagar",
                    "available": True,
                },
            ],
            ["Tipo", "Cuentas afectadas", "Disponible"],
        )

        chapter.add_section(
            "5.3.2 Asiento de Producción",
            "Cuando ejecutas una producción (receta), el sistema crea:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Debe",
                    "description": "1435 Inventario PT (productos terminados)",
                    "available": True,
                },
                {
                    "name": "Haber",
                    "description": "1430 Inventario MP (materias primas consumidas)",
                    "available": True,
                },
            ],
            ["Tipo", "Cuentas afectadas", "Disponible"],
        )

        chapter.add_section(
            "5.3.3 Asiento de Anulación",
            "Cuando se anula una factura, el sistema reversa automáticamente "
            "los asientos de venta, registrando valores negativos.",
        )

        chapter.add_screenshot_placeholder("Lista de asientos automáticos generados")

        chapter.add_spacer(0.3)

        # Sección: Estados Financieros
        chapter.add_section("5.4 Estados Financieros", "Chandelier permite generar reportes contables básicos.")

        chapter.add_section(
            "5.4.1 Balance de Comprobación",
            "Reporte que muestra el saldo de todas las cuentas en una fecha:\n"
            "• Columnas: Código, Nombre, Saldo Anterior, Débitos, Créditos, Saldo Actual\n"
            "• Permite verificar que los libros estén cuadrados\n"
            "• Filtros por rango de fechas",
        )

        chapter.add_screenshot_placeholder("Balance de comprobación")

        chapter.add_section(
            "5.4.2 Estado de Resultados",
            "Reporte de ingresos y gastos en un período:\n"
            "• Ventas netas\n"
            "• Costo de ventas\n"
            "• Utilidad bruta\n"
            "• Gastos operativos\n"
            "• Utilidad neta",
        )

        chapter.add_screenshot_placeholder("Estado de resultados")

        chapter.add_spacer(0.3)

        # Sección: Validaciones
        chapter.add_section(
            "5.5 Validaciones",
            "El sistema valida automáticamente:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Asiento cuadrado",
                    "description": "Total Debe debe ser igual a Total Haber",
                    "available": True,
                },
                {
                    "name": "Cuenta válida",
                    "description": "Solo permite cuentas que aceptan movimientos",
                    "available": True,
                },
                {
                    "name": "Fecha válida",
                    "description": "No permite fechas futuras",
                    "available": True,
                },
                {
                    "name": "Referencia linked",
                    "description": "Asientos automáticos vinculados a facturas/producciones",
                    "available": True,
                },
            ],
            ["Validación", "Descripción", "Disponible"],
        )

        chapter.add_spacer(0.3)

        # Sección: Funcionalidades
        chapter.add_section(
            "5.6 Funcionalidades de Contabilidad",
            "Chandelier ofrece las siguientes funcionalidades:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "PUC Pre-cargado",
                    "description": "~40 cuentas del PUC Colombia listas para usar",
                    "available": True,
                },
                {
                    "name": "Asientos Manuales",
                    "description": "Crear asientos contables personalizados",
                    "available": True,
                },
                {
                    "name": "Asientos Automáticos",
                    "description": "Generación automática en ventas y producciones",
                    "available": True,
                },
                {
                    "name": "Validación de Cuadratura",
                    "description": "Verifica que todo asiento esté cuadrado",
                    "available": True,
                },
                {
                    "name": "Balance de Comprobación",
                    "description": "Reporte de saldos por cuenta",
                    "available": True,
                },
                {
                    "name": "Estado de Resultados",
                    "description": "Reporte de ingresos y gastos",
                    "available": True,
                },
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "5.7 Relación con Otros Módulos",
            "La contabilidad se integra con:\n"
            "• <b>Facturación:</b> Asientos automáticos al emitir facturas\n"
            "• <b>Recetas:</b> Asientos automáticos al producir\n"
            "• <b>Inventario:</b> Movimiento de cuentas de inventario",
        )

        return chapter.build()
