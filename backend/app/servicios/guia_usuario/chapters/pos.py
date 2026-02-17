"""
Capítulo 8: Punto de Venta (POS)
Interfaz móvil-first para ventas rápidas con grid de productos y carrito.
"""

from typing import List
from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class POSChapter:
    """
    Capítulo de POS (Punto de Venta) para la guía de usuario.
    Interfaz móvil-first optimizada para ventas rápidas en tienda.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de POS.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de POS.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("8. Punto de Venta (POS)", self.style_dict)

        # Introducción
        chapter.add_intro(
            "El Punto de Venta (POS) de Chandelier está diseñado para ser <b>mobile-first</b>, "
            "optimizado para ventas rápidas en tienda física. La interfaz muestra un grid de productos "
            "y un carrito lateral, permitiendo completar ventas en segundos."
        )

        chapter.add_spacer(0.3)

        # Sección: Interfaz POS
        chapter.add_section(
            "8.1 Interfaz del POS",
            "La interfaz del POS está dividida en dos paneles principales:",
        )

        chapter.add_section(
            "8.1.1 Panel Izquierdo - Grid de Productos",
            "El panel izquierdo muestra el catálogo de productos:\n\n"
            "• <b>Grid de productos:</b> Visualización en cards o lista\n"
            "• <b>Imagen:</b> Foto del producto\n"
            "• <b>Nombre:</b> Título del producto\n"
            "• <b>Precio:</b> Precio de venta\n"
            "• <b>Stock:</b> Cantidad disponible (si está bajo, muestra alerta)\n"
            "• <b>Buscar:</b> Campo de búsqueda para filtrar productos\n"
            "• <b>Categorías:</b> Filtro por categoría de producto",
        )

        chapter.add_section(
            "8.1.2 Panel Derecho - Carrito de Compras",
            "El panel derecho muestra el carrito:\n\n"
            "• <b>Cliente:</b> Selector de cliente (opcional)\n"
            "• <b>Items:</b> Productos agregados con cantidad\n"
            "• <b>Controles:</b> Ajustar cantidad (+/-), eliminar item\n"
            "• <b>Subtotal:</b> Suma de productos\n"
            "• <b>IVA:</b> Impuesto calculado\n"
            "• <b>TOTAL:</b> Total a pagar (destacado)\n"
            "• <b>Botón Cobrar:</b> Botón principal para finalizar",
        )

        chapter.add_screenshot_placeholder("Interfaz completa del POS (desktop)")

        chapter.add_spacer(0.3)

        # Sección: Flujo de Venta
        chapter.add_section(
            "8.2 Flujo de Venta",
            "El proceso de venta en el POS está optimizado para rapidez:",
        )

        chapter.add_step_list(
            [
                "Accede al POS desde el menú lateral: Ventas > POS",
                "Opcional: Busca o filtra productos por categoría",
                "Click en el producto para agregarlo al carrito",
                "En el carrito, ajusta las cantidades (+/-) según necesidad",
                "Opcional: Selecciona un cliente específico (o usa Cliente Mostrador)",
                "Click en 'Cobrar' para iniciar el cobro",
                "Selecciona el método de pago (efectivo, transferencia, etc.)",
                "Confirma el pago - el sistema genera la factura automáticamente",
                "¡Listo! La venta está completa y el stock se actualizó",
            ],
            "Pasos para realizar una venta en el POS",
        )

        chapter.add_screenshot_placeholder("Carrito con productos")

        chapter.add_section(
            "8.2.1 Agregar Productos",
            "Hay varias formas de agregar productos al carrito:\n\n"
            "• <b>Click en producto:</b> Agrega 1 unidad al hacer click\n"
            "• <b>Click largo:</b> Abre diálogo para especificar cantidad\n"
            "• <b>Buscar + agregar:</b> Busca y selecciona directamente\n"
            "• <b>Escáner:</b> Si tienes código de barras, escanea y agrega",
        )

        chapter.add_section(
            "8.2.2 Ajustar Carrito",
            "En el carrito puedes:\n\n"
            "• <b>Aumentar cantidad:</b> Click en botón (+)\n"
            "• <b>Disminuir cantidad:</b> Click en botón (-)\n"
            "• <b>Eliminar producto:</b> Click en ícono de papelera\n"
            "• <b>Vaciar carrito:</b> Botón para cancelar todo\n"
            "• <b>Ver totales:</b> Subtotal, IVA y Total siempre visibles",
        )

        chapter.add_spacer(0.3)

        # Sección: Cliente Mostrador
        chapter.add_section(
            "8.3 Cliente Mostrador",
            "El POS utiliza el Cliente Mostrador por defecto cuando no seleccionas un cliente específico.",
        )

        chapter.add_section(
            "8.3.1 Características del Cliente Mostrador",
            "• <b>NIT:</b> 222222222222\n"
            "• <b>Nombre:</b> Cliente Mostrador\n"
            "• <b>Propósito:</b> Ventas rápidas sin identificar al cliente\n"
            "• <b>IVA:</b> Se cobra normalmente (no tiene retención)\n"
            "• <b>Disponibilidad:</b> Siempre disponible, no se puede eliminar",
        )

        chapter.add_section(
            "8.3.2 Cuándo Usar",
            "Usa el Cliente Mostrador cuando:\n"
            "• El cliente no requiere factura\n"
            "• Es una venta de mostrador rápida\n"
            "• El cliente no se identifica\n"
            "• No necesitas tracking de ventas por cliente\n\n"
            "<b>Para facturación:</b> Siempre selecciona el cliente real antes de cobrar.",
        )

        chapter.add_screenshot_placeholder("Selector de cliente en POS")

        chapter.add_spacer(0.3)

        # Sección: Consideraciones Móvil
        chapter.add_section(
            "8.4 Diseño Mobile-First",
            "Chandelier POS está diseñado pensando en dispositivos móviles:",
        )

        chapter.add_section(
            "8.4.1 Características Responsive",
            "• <b>Diseño adaptativo:</b> Se ajusta a cualquier tamaño de pantalla\n"
            "• <b>Desktop:</b> Dos paneles (productos + carrito) lado a lado\n"
            "• <b>Tablet:</b> Panels colapsables, más espacio para productos\n"
            "• <b>Móvil:</b> Un panel a la vez, navegación por tabs",
        )

        chapter.add_section(
            "8.4.2 Touch-Friendly",
            "• <b>Botones grandes:</b> Mínimo 48x48px para fácil touch\n"
            "• <b>Espaciado:</b> Espacio suficiente entre elementos clickeables\n"
            "• <b>Gestos:</b> Soporte para swipe en móviles\n"
            "• <b>Bottom navigation:</b> Tabs en la parte inferior para móvil",
        )

        chapter.add_section(
            "8.4.3 Navegación Mobile",
            "En dispositivos móviles:\n\n"
            "• <b>Tab 1 - Productos:</b> Grid de productos para seleccionar\n"
            "• <b>Tab 2 - Carrito:</b> Ver y editar el carrito\n"
            "• <b>Tab 3 - Más:</b> Configuración y otras opciones\n"
            "• <b>FAB:</b> Floating Action Button para acceder al carrito rápidamente",
        )

        chapter.add_screenshot_placeholder("POS en dispositivo móvil")

        chapter.add_spacer(0.3)

        # Sección: Cobro y Facturación
        chapter.add_section(
            "8.5 Proceso de Cobro",
            "El cobro en el POS genera una factura automáticamente:",
        )

        chapter.add_step_list(
            [
                "Una vez con los productos en el carrito, click en 'Cobrar'",
                "Selecciona el método de pago: Efectivo, Tarjeta, Transferencia",
                "Si es efectivo, ingresa el monto recibido",
                "El sistema calcula el cambio a devolver",
                "Confirma el pago",
                "El sistema:",
                "  - Genera la factura automáticamente",
                "  - Actualiza el inventario",
                "  - Crea el asiento contable",
                "Muestra ticket o opción de enviar PDF al cliente",
            ],
            "Pasos para cobrar en el POS",
        )

        chapter.add_section(
            "8.5.1 Métodos de Pago",
            "El POS soporta los siguientes métodos de pago:\n\n"
            "• <b>Efectivo:</b> Ingresa monto recibido, calcula cambio\n"
            "• <b>Tarjeta:</b> Simulación (en MVP, solo registra método)\n"
            "• <b>Transferencia:</b> Registra número de referencia\n"
            "• <b>Mixto:</b> Combina varios métodos de pago",
        )

        chapter.add_screenshot_placeholder("Dialog de cobro con método de pago")

        chapter.add_spacer(0.3)

        # Sección: Funcionalidades
        chapter.add_section(
            "8.6 Funcionalidades del POS",
            "Chandelier POS ofrece las siguientes funcionalidades:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Grid de productos",
                    "description": "Visualización rápida de productos disponibles",
                    "available": True,
                },
                {"name": "Búsqueda", "description": "Buscar productos por nombre o SKU", "available": True},
                {
                    "name": "Filtro por categoría",
                    "description": "Ver productos de una categoría específica",
                    "available": True,
                },
                {
                    "name": "Carrito de compras",
                    "description": "Agregar, ajustar, eliminar productos",
                    "available": True,
                },
                {"name": "Cálculo automático", "description": "Subtotal, IVA, total en tiempo real", "available": True},
                {
                    "name": "Cliente Mostrador",
                    "description": "Cliente por defecto para ventas rápidas",
                    "available": True,
                },
                {
                    "name": "Selección de cliente",
                    "description": "Elegir cliente específico si requiere factura",
                    "available": True,
                },
                {"name": "Factura automática", "description": "Genera factura al cobrar", "available": True},
                {"name": "Stock en tiempo real", "description": "Muestra disponibilidad actual", "available": True},
                {"name": "Diseño responsive", "description": "Funciona en desktop, tablet y móvil", "available": True},
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        chapter.add_spacer(0.3)

        # Sección: Mejores prácticas
        chapter.add_section(
            "8.7 Mejores Prácticas",
            "• <b>Mantén el POS abierto:</b> Es la forma más rápida de vender\n"
            "• <b>Revisa el stock:</b> Mira las alertas de stock bajo\n"
            "• <b>Usa Cliente Mostrador:</b> Para ventas sin factura es más rápido\n"
            "• <b>Selecciona cliente:</b> Si el cliente pide factura, selecciónalo antes de cobrar\n"
            "• <b>Verifica el cambio:</b> Siempre muestra el cambio al cliente\n"
            "• <b>Envía el PDF:</b> Ofrece enviar la factura por email\n"
            "• <b>Mantén actualizado:</b> Agrega nuevos productos al catálogo",
        )

        chapter.add_section(
            "8.7.1 Tips para流畅 Ventas",
            "• <b>Organiza productos:</b> Pon los más vendidos al inicio\n"
            "• <b>Usa categorías:</b> Facilita encontrar productos rápidamente\n"
            "• <b>Atajos de teclado:</b> En desktop, usa shortcuts para agregar productos\n"
            "• <b>Revisa antes de cobrar:</b> Un último vistazo evita errores",
        )

        chapter.add_screenshot_placeholder("POS en uso - ventas exitosa")

        return chapter.build()
