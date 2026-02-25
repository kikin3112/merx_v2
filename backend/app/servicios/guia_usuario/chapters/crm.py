"""
Capítulo 5: CRM - Gestión de Clientes
Gestión de clientes, retención de IVA y cliente mostradors.
"""

from typing import List

from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class CRMChapter:
    """
    Capítulo de CRM para la guía de usuario.
    Cubre gestión de clientes, retención IVA y cliente mostradors.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de CRM.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de CRM.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("5. CRM - Gestión de Clientes", self.style_dict)

        # Introducción
        chapter.add_intro(
            "Este capítulo te enseña a gestionar tus clientes en Chandelier. Aprende a registrar "
            "clientes, configurar retención de IVA y utilizar el cliente mostradors para ventas rápidas."
        )

        chapter.add_spacer(0.3)

        # Sección: Crear Cliente
        chapter.add_section("5.1 Crear Cliente", "Para registrar un nuevo cliente en el sistema:")

        chapter.add_step_list(
            [
                "Navega a Ventas > Clientes en el menú lateral",
                "Haz clic en el botón 'Nuevo Cliente' (+)",
                "Completa los datos del cliente: NIT, nombre, email, teléfono, dirección",
                "Configura 'Retención IVA' si aplica",
                "Haz clic en 'Guardar' para registrar el cliente",
            ],
            "Pasos para crear un cliente",
        )

        chapter.add_screenshot_placeholder("Formulario de creación de cliente")

        chapter.add_section(
            "5.1.1 Campos del Formulario",
            "• <b>NIT:</b> Identificación del cliente (único por empresa)\n"
            "• <b>Nombre:</b> Razón social o nombre del cliente\n"
            "• <b>Email:</b> Correo electrónico para notificaciones\n"
            "• <b>Teléfono:</b> Número de contacto\n"
            "• <b>Dirección:</b> Dirección de facturación/entrega\n"
            "• <b>Retención IVA:</b> Toggle para clientes que aplican retención",
        )

        chapter.add_spacer(0.3)

        # Sección: Retención IVA
        chapter.add_section(
            "5.2 Retención de IVA",
            "La retención de IVA es un mecanismo donde algunos clientes (generalmente grandes empresas) "
            "retienen el IVA al momento del pago, acting como agentes de retención.",
        )

        chapter.add_section(
            "5.2.1 Cómo Funciona",
            "Cuando <b>Retención IVA</b> está habilitada en un cliente:\n"
            "• El sistema <b>no cobrará IVA</b> en las facturas a ese cliente\n"
            "• El cliente será responsable de declarar y pagar el IVA\n"
            "• Esto aplica solo para clientes que tengan este toggle habilitado",
        )

        chapter.add_section(
            "5.2.2 Cuándo Usar",
            "Activa la retención de IVA para:\n"
            "• Empresas grandes que actúan como agentes de retención\n"
            "• Clientes que tienen autorización de la DIAN para auto-retenerse\n"
            "• Entidades gubernamentales (en algunos casos)\n"
            "\n"
            "Mantén deshabilitado para clientes normales que paguen el IVA completo.",
        )

        chapter.add_screenshot_placeholder("Toggle de retención IVA en formulario de cliente")

        chapter.add_spacer(0.3)

        # Sección: Cliente Mostradors
        chapter.add_section(
            "5.3 Cliente Mostradors",
            "El <b>Cliente Mostradors</b> es un cliente predefinido que se crea automáticamente "
            "al configurar tu empresa. Se usa para ventas rápidas en el punto de venta (POS).",
        )

        chapter.add_section(
            "5.3.1 Características del Cliente Mostradors",
            "• <b>NIT:</b> 222222222222 (genérico)\n"
            "• <b>Nombre:</b> Cliente Mostradors\n"
            "• <b>Propósito:</b> Ventas de mostrador donde no se requiere identificar al cliente\n"
            "• <b>Disponibilidad:</b> Siempre presente en el POS",
        )

        chapter.add_section(
            "5.3.2 Cuándo Usar",
            "Usa el Cliente Mostradors cuando:\n"
            "• Un cliente compra sin pedir factura o sin identificarse\n"
            "• Realizas ventas rápidas en la tienda física\n"
            "• No necesitas tracking de ventas por cliente específico\n"
            "\n"
            "Para ventas con factura, siempre busca o crea el cliente correcto.",
        )

        chapter.add_screenshot_placeholder("Selector de cliente en POS con Cliente Mostradors")

        chapter.add_spacer(0.3)

        # Sección: Funcionalidades CRM
        chapter.add_section(
            "5.4 Funcionalidades de CRM", "Chandelier ofrece las siguientes funcionalidades para gestión de clientes:"
        )

        chapter.add_feature_table(
            [
                {"name": "Gestión de clientes", "description": "Crear, editar, eliminar clientes", "available": True},
                {
                    "name": "Historial de compras",
                    "description": "Ver todas las facturas de un cliente",
                    "available": True,
                },
                {
                    "name": "Retención IVA",
                    "description": "Clientes que no pagan IVA (agentes de retención)",
                    "available": True,
                },
                {
                    "name": "Cliente Mostradors",
                    "description": "Cliente genérico para ventas rápidas",
                    "available": True,
                },
                {"name": "Búsqueda de clientes", "description": "Buscar por NIT o nombre", "available": True},
                {
                    "name": "Datos de contacto",
                    "description": "Email, teléfono, dirección por cliente",
                    "available": True,
                },
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        chapter.add_spacer(0.3)

        # Sección: Mejores prácticas
        chapter.add_section(
            "5.5 Mejores Prácticas",
            "• <b>Registra todos los clientes:</b> Incluso si no facturan, ten sus datos\n"
            "• <b>Verifica el NIT:</b> Asegúrate que el NIT sea correcto para evitar problemas fiscales\n"
            "• <b>Usa Cliente Mostradors:</b> Solo para ventas sin factura o clientes casuales\n"
            "• <b>Mantén datos actualizados:</b> Actualiza email y teléfono periódicamente",
        )

        return chapter.build()
