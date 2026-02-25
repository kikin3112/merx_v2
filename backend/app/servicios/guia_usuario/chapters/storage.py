"""
Capítulo 13: Almacenamiento (Storage)
Gestión de archivos en la nube mediante S3/R2 para logos, facturas y cotizaciones.
"""

from typing import List

from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class StorageChapter:
    """
    Capítulo de Almacenamiento para la guía de usuario.
    Cubre el sistema de almacenamiento S3/R2 para archivos del sistema.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de almacenamiento.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de almacenamiento.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("13. Almacenamiento (Storage)", self.style_dict)

        # Introducción
        chapter.add_intro(
            "Este capítulo te explicará cómo Chandelier gestiona el almacenamiento de archivos "
            "en la nube. El sistema utiliza almacenamiento compatible con Amazon S3 (como Cloudflare R2 "
            "o DigitalOcean Spaces) para guardar de forma segura los logos de tu empresa, "
            "facturas en PDF y cotizaciones."
        )

        chapter.add_spacer(0.3)

        # Sección: ¿Qué se almacena?
        chapter.add_section(
            "13.1 ¿Qué se almacena?",
            "Chandelier almacena diferentes tipos de archivos según su naturaleza:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Logos de Tenant",
                    "description": "Logotipo de tu empresa usado en facturas y documentos",
                    "available": True,
                },
                {
                    "name": "PDFs de Facturas",
                    "description": "Documentos de facturas emitidas en formato PDF",
                    "available": True,
                },
                {
                    "name": "PDFs de Cotizaciones",
                    "description": "Documentos de cotizaciones generadas",
                    "available": True,
                },
            ],
            ["Tipo de Archivo", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "13.1.1 Importancia del Almacenamiento",
            "• <b>Logos:</b> Identidad visual en todos los documentos generados\n"
            "• <b>Facturas:</b> Cumplimiento legal y respaldo de transacciones\n"
            "• <b>Cotizaciones:</b> Historial de propuestas comerciales",
        )

        chapter.add_spacer(0.3)

        # Sección: S3/R2
        chapter.add_section(
            "13.2 S3/Almacenamiento en la Nube",
            "Chandelier utiliza almacenamiento compatible con Amazon S3, lo que permite flexibilidad "
            "en la elección del proveedor de almacenamiento.",
        )

        chapter.add_section(
            "13.2.1 Proveedores Soportados",
            "Puedes utilizar cualquiera de estos proveedores de almacenamiento:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Amazon S3",
                    "description": "El servicio original de AWS",
                    "available": True,
                },
                {
                    "name": "Cloudflare R2",
                    "description": "Sin cargos por transferencia de datos",
                    "available": True,
                },
                {
                    "name": "DigitalOcean Spaces",
                    "description": "Alternativa económica",
                    "available": True,
                },
            ],
            ["Proveedor", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "13.2.2 Estructura de Buckets",
            "Chandelier utiliza dos buckets con diferentes configuraciones de acceso:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "chandelier-logos",
                    "description": "Almacena logos de tenants. Acceso público de lectura.",
                    "available": True,
                },
                {
                    "name": "chandelier-facturas",
                    "description": "Almacena PDFs de facturas y cotizaciones. Acceso privado.",
                    "available": True,
                },
            ],
            ["Bucket", "Descripción", "Tipo de Acceso"],
        )

        chapter.add_section(
            "13.2.3 Convenciones de Nombres",
            "Los archivos se organizan siguiendo esta estructura:\n"
            "<b>{tenant_id}/{tipo}/{uuid}.{ext}</b>\n\n"
            "Ejemplos:\n"
            "• Logo: <i>a1b2c3d4-.../logos/abc123.pdf</i>\n"
            "• Factura: <i>a1b2c3d4-.../facturas/fac-001.pdf</i>\n"
            "• Cotización: <i>a1b2c3d4-.../cotizaciones/cot-001.pdf</i>",
        )

        chapter.add_screenshot_placeholder("Configuración de storage en el panel de administración")

        chapter.add_spacer(0.3)

        # Sección: URLs de Acceso
        chapter.add_section(
            "13.3 URLs de Acceso",
            "Dependiendo del tipo de archivo, el acceso se maneja de manera diferente:",
        )

        chapter.add_section(
            "13.3.1 Logos - URL Pública",
            "Los logos de tenant se configuran como accesibles públicamente:\n"
            "1. Se suben al bucket <i>chandelier-logos</i>\n"
            "2. El bucket tiene permisos de lectura pública\n"
            "3. Se accede directamente mediante URL\n"
            "4. Se cachea en CDN para mejor rendimiento",
        )

        chapter.add_section(
            "13.3.2 Facturas y Cotizaciones - Presigned URLs",
            "Los documentos sensibles se protegen con URLs firmadas:\n"
            "1. Los PDFs se almacenan en bucket privado\n"
            "2. Al solicitar un documento, el sistema genera una URL temporal\n"
            "3. La URL expira después de 24 horas por seguridad\n"
            "4. Solo usuarios autorizados pueden acceder",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "URL Directa",
                    "description": "Acceso público e ilimitado (solo logos)",
                    "available": True,
                },
                {
                    "name": "Presigned URL",
                    "description": "URL temporal con expiración (facturas/cotizaciones)",
                    "available": True,
                },
            ],
            ["Tipo", "Descripción", "Caso de Uso"],
        )

        chapter.add_screenshot_placeholder("Ejemplo de URL de descarga de factura")

        chapter.add_spacer(0.3)

        # Sección: Límites
        chapter.add_section(
            "13.4 Límites de Almacenamiento",
            "Chandelier impone límites por tipo de archivo para optimizar el rendimiento:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Logos",
                    "description": "2 MB máximo",
                    "available": True,
                },
                {
                    "name": "Facturas PDF",
                    "description": "5 MB máximo",
                    "available": True,
                },
                {
                    "name": "Cotizaciones PDF",
                    "description": "5 MB máximo",
                    "available": True,
                },
                {
                    "name": "Retención",
                    "description": "Los PDFs se mantienen mientras la suscripción esté activa",
                    "available": True,
                },
            ],
            ["Tipo", "Límite", "Notas"],
        )

        chapter.add_section(
            "13.4.1 Recomendaciones",
            "Para optimizar el almacenamiento y rendimiento:\n"
            "• <b>Logos:</b> Usa formato PNG con fondo transparente, máximo 500x500px\n"
            "• <b>PDFs:</b> Genera PDFs optimizados, sin imágenes de alta resolución\n"
            "• <b>Compresión:</b> El sistema comprime automáticamente las imágenes",
        )

        chapter.add_spacer(0.3)

        # Sección: Configuración
        chapter.add_section(
            "13.5 Configuración de Storage",
            "Como administrador, puedes gestionar el almacenamiento desde Configuración:",
        )

        chapter.add_section(
            "13.5.1 Subir Logo",
            "Pasos para configurar el logo de tu empresa:\n"
            "1. Ve a <b>Configuración > Empresa</b>\n"
            "2. Busca la sección <b>Logo</b>\n"
            "3. Haz clic en <b>Subir Logo</b>\n"
            "4. Selecciona un archivo (máx 2MB, PNG/JPG)\n"
            "5. El logo aparecerá en vistas previas\n"
            "6. Guarda los cambios",
        )

        chapter.add_screenshot_placeholder("Panel de subida de logo")

        chapter.add_section(
            "13.5.2 Descargar Facturas",
            "Para acceder a tus facturas guardadas:\n"
            "1. Ve a <b>Facturas</b>\n"
            "2. Busca la factura deseada\n"
            "3. Haz clic en el botón <b>Descargar PDF</b>\n"
            "4. Se generará una URL temporal\n"
            "5. El archivo se descargará automáticamente\n"
            "6. La URL es válida por 24 horas",
        )

        chapter.add_screenshot_placeholder("Botón de descarga en lista de facturas")

        chapter.add_spacer(0.3)

        # Sección: Funcionalidades
        chapter.add_section(
            "13.6 Funcionalidades de Almacenamiento",
            "Chandelier ofrece las siguientes funcionalidades:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Almacenamiento S3",
                    "description": "Compatible con AWS S3, R2, DigitalOcean",
                    "available": True,
                },
                {
                    "name": "Presigned URLs",
                    "description": "Acceso seguro temporal a documentos",
                    "available": True,
                },
                {
                    "name": "Límites por Tipo",
                    "description": "2MB logos, 5MB PDFs",
                    "available": True,
                },
                {
                    "name": "CDN para Logos",
                    "description": "Distribución geográfica para logos públicos",
                    "available": True,
                },
                {
                    "name": "Compresión Automática",
                    "description": "Optimización de imágenes al subir",
                    "available": True,
                },
                {
                    "name": "Organización por Tenant",
                    "description": "Aislamiento total entre empresas",
                    "available": True,
                },
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        chapter.add_spacer(0.3)

        # Sección: Relación con otros módulos
        chapter.add_section(
            "13.7 Relación con Otros Módulos",
            "El almacenamiento está integrado con varios módulos del sistema:",
        )

        chapter.add_section(
            "13.7.1 Módulos que Usan Storage",
            "• <b>Configuración:</b> Logo de la empresa\n"
            "• <b>Facturación:</b> PDFs de facturas emitidas\n"
            "• <b>Cotizaciones:</b> PDFs de cotizaciones generadas\n"
            "• <b>Dashboard:</b> Gráficos exportados en PDF",
        )

        chapter.add_section(
            "13.7.2 Flujo de Archivos",
            "1. <b>Subida:</b> Usuario sube logo o sistema genera PDF\n"
            "2. <b>Procesamiento:</b> Sistema comprime y organiza archivos\n"
            "3. <b>Almacenamiento:</b> Se guarda en bucket correspondiente\n"
            "4. <b>Acceso:</b> URLs públicas o presigned según tipo\n"
            "5. <b>Descarga:</b> Usuario accede via URL o desde el sistema",
        )

        chapter.add_spacer(0.3)

        # Sección: Seguridad
        chapter.add_section(
            "13.8 Seguridad del Almacenamiento",
            "Chandelier implementa múltiples capas de seguridad:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Aislamiento por Tenant",
                    "description": "Cada empresa tiene su propio directorio",
                    "available": True,
                },
                {
                    "name": "Buckets Privados",
                    "description": "Facturas no son accesibles públicamente",
                    "available": True,
                },
                {
                    "name": "Presigned URLs",
                    "description": "Tokens temporales con expiración",
                    "available": True,
                },
                {
                    "name": "Encriptación",
                    "description": "Datos encriptados en reposo (AES-256)",
                    "available": True,
                },
                {
                    "name": "Logs de Acceso",
                    "description": "Registro de quién descargó cada documento",
                    "available": True,
                },
            ],
            ["Medida", "Descripción", "Estado"],
        )

        chapter.add_section(
            "13.8.1 Buenas Prácticas",
            "• No compartas las presigned URLs públicamente\n"
            "• Los enlaces de descarga tienen vigencia limitada\n"
            "• Revisa periódicamente los logs de acceso\n"
            "• Mantén el logo en formato optimizado",
        )

        chapter.add_spacer(0.3)

        # Resumen
        chapter.add_section(
            "13.9 Resumen",
            "En este capítulo aprendiste:\n"
            "• Los tipos de archivos que almacena Chandelier\n"
            "• Cómo funciona el almacenamiento S3/R2\n"
            "• La diferencia entre URLs públicas y presigned\n"
            "• Los límites de tamaño por tipo de archivo\n"
            "• Cómo configurar y gestionar tus archivos\n"
            "• Las medidas de seguridad implementadas",
        )

        return chapter.build()
