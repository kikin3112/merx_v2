"""
Capítulo 6: Cotizaciones
Gestión de cotizaciones, estados y conversión a facturas.
"""

from typing import List

from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class QuotationsChapter:
    """
    Capítulo de Cotizaciones para la guía de usuario.
    Cubre el ciclo completo de cotizaciones: creación, estados, edición y conversión.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de Cotizaciones.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de Cotizaciones.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("6. Cotizaciones", self.style_dict)

        # Introducción
        chapter.add_intro(
            "Las cotizaciones en Chandelier te permiten preparar propuestas comerciales para tus clientes. "
            "Una cotización incluye productos, precios, descuentos y fecha de validez. Puedes enviarla al cliente "
            "y, una vez aceptada, convertirla directamente en factura."
        )

        chapter.add_spacer(0.3)

        # Sección: Crear Cotización
        chapter.add_section("6.1 Crear Cotización", "Para crear una nueva cotización en el sistema:")

        chapter.add_step_list(
            [
                "Navega a Ventas > Cotizaciones en el menú lateral",
                "Haz clic en el botón 'Nueva Cotización' (+)",
                "Selecciona el cliente de la lista o crea uno nuevo (ver Capítulo 5: CRM)",
                "Agrega los productos con cantidad y precio unitario",
                "Aplica descuentos si es necesario (por línea o global)",
                "Define la fecha de validez de la cotización",
                "Guarda como borrador o envíala directamente al cliente",
            ],
            "Pasos para crear una cotización",
        )

        chapter.add_screenshot_placeholder("Formulario de creación de cotización")

        chapter.add_section(
            "6.1.1 Detalles de Productos",
            "Al agregar productos a una cotización:\n"
            "• <b>Producto:</b> Selecciona de tu catálogo de productos\n"
            "• <b>Cantidad:</b> Número de unidades\n"
            "• <b>Precio Unitario:</b> Precio de venta (puede diferir del precio base)\n"
            "• <b>Descuento:</b> Descuento opcional por línea (porcentaje o valor)\n"
            "• <b>IVA:</b> Se calcula automáticamente según la tarifa del producto",
        )

        chapter.add_spacer(0.3)

        # Sección: Estados de Cotización
        chapter.add_section(
            "6.2 Estados de Cotización",
            "Las cotizaciones pasan por diferentes estados a lo largo de su ciclo de vida:",
        )

        chapter.add_section(
            "6.2.1 Diagrama de Estados",
            "<b>Borrador</b> → <b>Enviada</b> → <b>Aceptada</b> o <b>Rechazada</b>\n\n"
            "• <b>Borrador:</b> Cotización en elaboración, no visible para el cliente\n"
            "• <b>Enviada:</b> Cotización enviada al cliente para revisión\n"
            "• <b>Aceptada:</b> Cliente aprobó la cotización, lista para facturar\n"
            "• <b>Rechazada:</b> Cliente no aceptó la cotización\n"
            "• <b>Convertida:</b> Se convirtió en factura (ver sección 6.4)",
        )

        chapter.add_screenshot_placeholder("Lista de cotizaciones con estados")

        chapter.add_section(
            "6.2.2 Cambios de Estado",
            "• <b>Guardar:</b> Crea la cotización como Borrador\n"
            "• <b>Enviar:</b> Marca como Enviada y notifica al cliente (si tiene email)\n"
            "• <b>Aceptar:</b> Marca como Aceptada cuando el cliente confirma\n"
            "• <b>Rechazar:</b> Marca como Rechazada si el cliente Decline\n"
            "• <b>Convertir:</b> Crea una factura a partir de la cotización",
        )

        chapter.add_spacer(0.3)

        # Sección: Editar Cotización
        chapter.add_section(
            "6.3 Editar Cotización",
            "Puedes modificar una cotización dependiendo de su estado:\n\n"
            "• <b>Borrador:</b> Editing completo - puedes modificar todo\n"
            "• <b>Enviada:</b> Editing limitado - solo ajustes menores\n"
            "• <b>Aceptada:</b> Editing muy limitado - solo si el cliente autoriza\n"
            "• <b>Rechazada/Convertida:</b> No se puede editar",
        )

        chapter.add_screenshot_placeholder("Edición de cotización existente")

        chapter.add_spacer(0.3)

        # Sección: Convertir a Factura
        chapter.add_section(
            "6.4 Convertir a Factura",
            "Una vez que el cliente acepta una cotización, puedes convertirla en factura con un solo clic.",
        )

        chapter.add_step_list(
            [
                "Abre la cotización en estado 'Aceptada'",
                "Haz clic en el botón 'Convertir a Factura'",
                "El sistema crea una nueva factura con los mismos datos",
                "La cotización se marca como 'Convertida'",
                "La factura se crea en estado 'Borrador' para revisión",
                "Emite la factura cuando estés listo",
            ],
            "Pasos para convertir cotización a factura",
        )

        chapter.add_section(
            "6.4.1 Qué se copia a la Factura",
            "Al convertir una cotización a factura se transfieren:\n"
            "• Todos los productos y cantidades\n"
            "• Precios unitarios y descuentos\n"
            "• Cliente seleccionado\n"
            "• Notas y comentarios\n"
            "• La numeración es independiente (nuevo número de factura)",
        )

        chapter.add_screenshot_placeholder("Dialog de conversión de cotización a factura")

        chapter.add_spacer(0.3)

        # Sección: Validez de Precios
        chapter.add_section(
            "6.5 Validez de Precios",
            "La fecha de validez de una cotización es crucial porque:\n\n"
            "• <b>Precios:</b> Los precios de la cotización son válidos hasta la fecha de vencimiento\n"
            "• <b>Stock:</b> El stock no se reserva hasta convertir en factura\n"
            "• <b>提醒:</b> El sistema puede notificarte cuando la cotización esté por vencer\n"
            "• <b>Vencida:</b> Una cotización vencida puede requerir actualización de precios",
        )

        chapter.add_section(
            "6.5.1 Mejores Prácticas",
            "• <b>Define validez razonable:</b> 15-30 días es recomendado\n"
            "• <b>Incluye nota de validez:</b> Indica que precios pueden cambiar después de la fecha\n"
            "• <b>Revisa antes de convertir:</b> Verifica precios y disponibilidad actuales\n"
            "• <b>Actualiza precios vencidos:</b> Crea nueva cotización si los precios cambiaron",
        )

        chapter.add_spacer(0.3)

        # Sección: Funcionalidades
        chapter.add_section(
            "6.6 Funcionalidades de Cotizaciones",
            "Chandelier ofrece las siguientes funcionalidades para gestión de cotizaciones:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Crear Cotización",
                    "description": "Crear nuevas cotizaciones con productos y precios",
                    "available": True,
                },
                {
                    "name": "Editar Cotización",
                    "description": "Modificar cotizaciones según su estado",
                    "available": True,
                },
                {"name": "Duplicar", "description": "Crear copia de cotización existente", "available": True},
                {
                    "name": "Enviar por Email",
                    "description": "Enviar cotización al cliente por correo",
                    "available": True,
                },
                {
                    "name": "Convertir a Factura",
                    "description": "Transformar cotización aceptada en factura",
                    "available": True,
                },
                {
                    "name": "Estados",
                    "description": "Borrador, Enviada, Aceptada, Rechazada, Convertida",
                    "available": True,
                },
                {"name": "Descuentos", "description": "Descuentos por línea o global", "available": True},
                {"name": "Fecha de validez", "description": "Control de vencimiento de precios", "available": True},
                {"name": "Notas", "description": "Agregar observaciones a la cotización", "available": True},
                {"name": "Historial", "description": "Ver todas las versiones de una cotización", "available": True},
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        chapter.add_spacer(0.3)

        # Sección: Mejores prácticas
        chapter.add_section(
            "6.7 Mejores Prácticas",
            "• <b>Usa descripciones claras:</b> Incluye nombre completo del producto\n"
            "• <b>Agrega validez razonable:</b> 15-30 días es un buen rango\n"
            "• <b>Incluye términos:</b> Nota sobre validez de precios y disponibilidad\n"
            "• <b>Sigue el estado:</b> Actualiza a 'Enviada' al enviar al cliente\n"
            "• <b>Convierte rápidamente:</b> No esperes - convierte cuando el cliente acepte\n"
            "• <b>Revisa antes de emitir:</b> Verifica la factura antes de generarla",
        )

        return chapter.build()
