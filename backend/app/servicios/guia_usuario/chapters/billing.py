"""
Capítulo 7: Facturación
Gestión de facturas, generación de PDF, numeración por tenant y asientos contables.
"""

from typing import List
from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class BillingChapter:
    """
    Capítulo de Facturación para la guía de usuario.
    Crea, emite, y gestiona facturas con PDF y contabilidad automática.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de Facturación.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de Facturación.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("7. Facturación", self.style_dict)

        # Introducción
        chapter.add_intro(
            "El módulo de facturación de Chandelier te permite crear y gestionar facturas de venta. "
            "El sistema genera automáticamente el PDF, guarda el documento en storage (S3/R2), "
            "actualiza el inventario y crea los asientos contables correspondientes."
        )

        chapter.add_spacer(0.3)

        # Sección: Crear Factura
        chapter.add_section("7.1 Crear Factura", "Para crear una nueva factura en el sistema:")

        chapter.add_step_list(
            [
                "Navega a Ventas > Facturas en el menú lateral",
                "Haz clic en el botón 'Nueva Factura' (+)",
                "Selecciona el cliente (requerido - si no existe, créalo primero en CRM)",
                "Agrega los productos con cantidad del catálogo",
                "El sistema calcula automáticamente: subtotal, IVA, total",
                "Opcional: Agrega notas o comentarios a la factura",
                "Guarda la factura como Borrador para revisión",
            ],
            "Pasos para crear una factura",
        )

        chapter.add_screenshot_placeholder("Formulario de creación de factura")

        chapter.add_section(
            "7.1.1 Validación de Stock",
            "Al agregar productos a una factura:\n"
            "• El sistema <b>valida el stock disponible</b> en tiempo real\n"
            "• Si no hay suficiente stock, muestra advertencia\n"
            "• Puedes proceder de todas formas (para productos sin inventario)\n"
            "• El stock se descuenta al <b>emitir</b> la factura, no al crear",
        )

        chapter.add_section(
            "7.1.2 Cálculos Automáticos",
            "El sistema calcula automáticamente:\n"
            "• <b>Subtotal:</b> Suma de (precio × cantidad - descuento) por línea\n"
            "• <b>IVA:</b> Calculado según la tarifa de IVA de cada producto\n"
            "• <b>Retención IVA:</b> Si el cliente tiene retención habilitada, no se cobra IVA\n"
            "• <b>Total:</b> Subtotal + IVA (menos retención si aplica)",
        )

        chapter.add_spacer(0.3)

        # Sección: Emitir Factura
        chapter.add_section(
            "7.2 Emitir Factura",
            "Emitir una factura es el paso final que la hace oficial y genera efectos contables:",
        )

        chapter.add_step_list(
            [
                "Asegúrate de que la factura esté en estado 'Borrador'",
                "Revisa todos los datos: cliente, productos, precios, cantidades",
                "Haz clic en el botón 'Emitir Factura'",
                "Confirma la emisión en el diálogo de confirmación",
                "El sistema ejecuta automáticamente:",
                "  - Genera el PDF de la factura",
                "  - Sube el PDF a storage (S3/R2)",
                "  - Crea movimientos de stock (salida)",
                "  - Genera asiento contable automático",
                "La factura cambia a estado 'Emitida'",
            ],
            "Pasos para emitir una factura",
        )

        chapter.add_screenshot_placeholder("Dialog de confirmación de emisión")

        chapter.add_section(
            "7.2.1 Proceso Automático al Emitir",
            "Cuando emitted una factura, Chandelier ejecuta automáticamente:\n\n"
            "<b>1. Generación de PDF:</b>\n"
            "• El sistema genera un PDF profesional con los datos de la factura\n"
            "• El PDF incluye: datos del tenant, cliente, items, totales\n"
            "• Se guarda en storage con nombre: {tenant_id}/facturas/{uuid}.pdf\n\n"
            "<b>2. Actualización de Inventario:</b>\n"
            "• Se crea un movimiento de stock de <b>salida</b> por cada producto\n"
            "• La cantidad salida = cantidad en la factura\n"
            "• El stock se descuenta automáticamente\n\n"
            "<b>3. Asiento Contable:</b>\n"
            "• Se genera automáticamente un asiento contable\n"
            "• DEBE: 1105 (Caja) por el total facturado\n"
            "• HABER: 4135 (Ventas) por el subtotal\n"
            "• HABER: 2408 (IVA por pagar) por el IVA",
        )

        chapter.add_screenshot_placeholder("Factura PDF generada")

        chapter.add_spacer(0.3)

        # Sección: Numeración
        chapter.add_section(
            "7.3 Numeración de Facturas",
            "Cada tenant tiene su propia secuencia de numeración:",
        )

        chapter.add_section(
            "7.3.1 Formato de Numeración",
            "El formato de número de factura es:\n"
            "<b>{prefijo}-{número}</b>\n\n"
            "Ejemplos:\n"
            "• FAC-001, FAC-002, FAC-003\n"
            "• INV-001, INV-002 (si cambias el prefijo)\n"
            "• 0001, 0002 (sin prefijo)",
        )

        chapter.add_section(
            "7.3.2 Configurar Prefijo",
            "El prefijo se configura en Configuración > Empresa:\n"
            "• <b>Prefijo:</b> Texto antes del número (default: FAC)\n"
            "• <b>Número siguiente:</b> Controla el próximo número\n"
            "• <b>Ejemplo:</b> Si pones prefijo 'FAC-' y siguiente 1, la primera factura será FAC-001",
        )

        chapter.add_section(
            "7.3.3 Requisitos",
            "• El número es <b>único por tenant</b> (no hay dos facturas con el mismo número)\n"
            "• La numeración es <b>secuencial</b> (no puedes saltarte números)\n"
            "• Al crear una nueva factura, usa el siguiente número disponible\n"
            "• No puedes editar el número manualmente una vez creada la factura",
        )

        chapter.add_screenshot_placeholder("Configuración de numeración en Settings")

        chapter.add_spacer(0.3)

        # Sección: Estados de Factura
        chapter.add_section(
            "7.4 Estados de Factura",
            "Las facturas tienen los siguientes estados:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Borrador",
                    "description": "Factura en elaboración, no tiene efectos contables",
                    "available": True,
                },
                {
                    "name": "Emitida",
                    "description": "Factura oficial, PDF generado, stock afectado, asiento contable creado",
                    "available": True,
                },
                {
                    "name": "Pagada",
                    "description": "El cliente pagó la factura (solo seguimiento, no afecta contabilidad)",
                    "available": True,
                },
                {
                    "name": "Anulada",
                    "description": "Factura cancelada, stock y asientos se reversan",
                    "available": True,
                },
            ],
            ["Estado", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "7.4.1 Cambios de Estado",
            "• <b>Borrador → Emitida:</b> Al hacer clic en 'Emitir'\n"
            "• <b>Emitida → Pagada:</b> Al registrar el pago del cliente\n"
            "• <b>Emitida → Anulada:</b> Al anular la factura (requiere justificación)\n"
            "• <b>Pagada → Anulada:</b> Solo con reversión del pago",
        )

        chapter.add_screenshot_placeholder("Lista de facturas con estados")

        chapter.add_spacer(0.3)

        # Sección: Anular Factura
        chapter.add_section(
            "7.5 Anular Factura",
            "Si necesitas cancelar una factura emitida, puedes anularla:",
        )

        chapter.add_step_list(
            [
                "Abre la factura en estado 'Emitida' o 'Pagada'",
                "Haz clic en el botón 'Anular Factura'",
                "Proporciona una justificación de la anulación",
                "Confirma la anulación",
                "El sistema reversa automáticamente:",
                "  - Restaura el stock (movimientos de entrada)",
                "  - Crea asiento de reversión (invierte debe/haber)",
                "La factura se marca como 'Anulada'",
            ],
            "Pasos para anular una factura",
        )

        chapter.add_section(
            "7.5.1 Consideraciones",
            "• <b>Solo se pueden anular</b> facturas en estado Emitida o Pagada\n"
            "• <b>La anulación es irreversible</b> - se crea una nueva factura si es necesario\n"
            "• <b>Justificación requerida:</b> Debes indicar por qué se anula\n"
            "• <b>Asientos de reversión:</b> Se crean automáticamente para mantener平衡 contable",
        )

        chapter.add_screenshot_placeholder("Dialog de anulación de factura")

        chapter.add_spacer(0.3)

        # Sección: PDF y Storage
        chapter.add_section(
            "7.6 PDF y Almacenamiento",
            "Chandelier genera y almacena las facturas automáticamente:",
        )

        chapter.add_section(
            "7.6.1 Contenido del PDF",
            "El PDF de factura incluye:\n"
            "• <b>Encabezado:</b> Logo del tenant, datos de la empresa\n"
            "• <b>Datos factura:</b> Número, fecha de emisión, fecha de vencimiento\n"
            "• <b>Cliente:</b> NIT, nombre, dirección\n"
            "• <b>Detalles:</b> Tabla con productos, cantidades, precios, descuentos, IVA\n"
            "• <b>Totales:</b> Subtotal, IVA, retención, total\n"
            "• <b>Pie:</b> Información de contacto, términos",
        )

        chapter.add_section(
            "7.6.2 Almacenamiento",
            "• Los PDFs se guardan en <b>S3/R2</b> (storage cloud)\n"
            "• <b>URL del PDF:</b> Se guarda en la base de datos\n"
            "• <b>Nombre del archivo:</b> {tenant_id}/facturas/{uuid}.pdf\n"
            "• <b>Acceso:</b> Los PDFs se descargan vía URL prefirmada (24h de validez)",
        )

        chapter.add_screenshot_placeholder("Factura PDF completa")

        chapter.add_spacer(0.3)

        # Sección: Funcionalidades
        chapter.add_section(
            "7.7 Funcionalidades de Facturación",
            "Chandelier ofrece las siguientes funcionalidades:",
        )

        chapter.add_feature_table(
            [
                {"name": "Crear Factura", "description": "Crear facturas con productos y precios", "available": True},
                {
                    "name": "Emitir Factura",
                    "description": "Finalizar factura, generar PDF y afectar inventario",
                    "available": True,
                },
                {"name": "Generación PDF", "description": "PDF automático profesional", "available": True},
                {"name": "Numeración automática", "description": "Sequential numbering per tenant", "available": True},
                {"name": "Estados", "description": "Borrador, Emitida, Pagada, Anulada", "available": True},
                {"name": "Anular Factura", "description": "Reversión de stock y asientos contables", "available": True},
                {"name": "Asiento contable", "description": "Generación automática de asientos", "available": True},
                {"name": "Stock automático", "description": "Salida de inventario al emitir", "available": True},
                {"name": "Retención IVA", "description": "Respetar retención del cliente", "available": True},
                {"name": "Notas", "description": "Agregar observaciones a la factura", "available": True},
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        chapter.add_spacer(0.3)

        # Sección: Mejores prácticas
        chapter.add_section(
            "7.8 Mejores Prácticas",
            "• <b>Revisa antes de emitir:</b> Verifica productos, precios y cliente\n"
            "• <b>Usa clientes correctos:</b> Selecciona el cliente real, no Mostrador\n"
            "• <b>Emite a tiempo:</b> La numeración es secuencial, no hay saltos\n"
            "• <b>No anules innecesariamente:</b> Mejor crear nota crédito si hay error\n"
            "• <b>Guarda los PDFs:</b> Se guardan automáticamente, descarga backups periódicos\n"
            "• <b>Configura tu prefijo:</b> En Configuración > Empresa antes de facturar",
        )

        return chapter.build()
