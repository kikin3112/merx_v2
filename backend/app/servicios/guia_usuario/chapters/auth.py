"""
Capítulo 2: Autenticación y Multi-tenancy
Explica el sistema de autenticación JWT, roles de usuario y cómo gestionar múltiples empresas.
"""

from typing import List
from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class AuthChapter:
    """
    Capítulo de Autenticación y Multi-tenancy para la guía de usuario.
    Explica JWT, roles, y cambio de tenant.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de autenticación.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de autenticación.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("2. Autenticación y Multi-tenancy", self.style_dict)

        # Introducción
        chapter.add_intro(
            "Este capítulo describe el sistema de seguridad de Chandelier, incluyendo cómo funciona "
            "la autenticación con JWT, los roles de usuario disponibles y cómo gestionar el acceso "
            "a múltiples empresas (tenants) desde una misma cuenta."
        )

        chapter.add_spacer(0.3)

        # Sección: ¿Qué es JWT?
        chapter.add_section(
            "2.1 ¿Qué es JWT?",
            "JWT (JSON Web Token) es un estándar abierto para la transmisión segura de información "
            "entre partes como un objeto JSON. En Chandelier, los tokens JWT se utilizan para:\n"
            "<br/>• <b>Autenticación:</b> Verificar la identidad del usuario en cada solicitud\n"
            "<br/>• <b>Seguridad:</b> Los tokens tienen expiración automática (1 hora)\n"
            "<br/>• <b>Stateless:</b> No requieren almacenamiento en servidor",
        )

        chapter.add_section(
            "2.1.1 Refresh Tokens",
            "Además del token de acceso (válido por 1 hora), Chandelier utiliza refresh tokens "
            "(válidos por 7 días) para mantener la sesión activa sin necesidad de volver a "
            "ingresar credenciales. El sistema renueva automáticamente el token de acceso.",
        )

        chapter.add_spacer(0.3)

        # Sección: Roles de Usuario
        chapter.add_section(
            "2.2 Roles de Usuario", "Chandelier define tres roles principales, cada uno con permisos específicos:"
        )

        # Tabla de roles
        chapter.add_feature_table(
            [
                {
                    "name": "Administrador",
                    "description": "Acceso completo: gestionar usuarios, configuración, productos, facturas, reportes",
                    "available": True,
                },
                {
                    "name": "Vendedor",
                    "description": "Acceso a POS, ventas, clientes, consultas de inventario",
                    "available": True,
                },
                {
                    "name": "Contador",
                    "description": "Acceso a contabilidad, asientos, reportes financieros, configuración de facturas",
                    "available": True,
                },
            ],
            ["Rol", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "2.2.1 Permisos por Rol",
            "• <b>Administrador:</b> Crear/edit/eliminar productos, gestionar usuarios, configurar tenant, emitir facturas\n"
            "• <b>Vendedor:</b> Usar POS, crear facturas, gestionar clientes (solo propia empresa)\n"
            "• <b>Contador:</b> Ver/mover asientos contables, generar reportes financieros",
        )

        chapter.add_spacer(0.3)

        # Sección: Multi-tenancy
        chapter.add_section(
            "2.3 Gestión de Multi-tenancy",
            "Chandelier es un sistema multi-tenant, lo que significa que una misma cuenta de usuario "
            "puede acceder a varias empresas. Cada empresa (tenant) tiene sus propios datos aislados.",
        )

        chapter.add_section(
            "2.3.1 ¿Qué es un Tenant?",
            "Un tenant representa una empresa o negocio independiente dentro de Chandelier. "
            "Cada tenant tiene su propio:\n"
            "<br/>• Inventario de productos\n"
            "<br/>• Clientes y facturas\n"
            "<br/>• Configuración (prefijo de facturas, IVA, resolución DIAN)\n"
            "<br/>• Usuarios con roles específicos",
        )

        chapter.add_section(
            "2.3.2 Cambiar de Tenant",
            "Para cambiar entre empresas:\n"
            "1. Haz clic en el selector de tenant ubicado en la barra superior\n"
            "2. Selecciona la empresa deseada del dropdown\n"
            "3. El sistema cargará los datos de esa empresa",
        )

        chapter.add_screenshot_placeholder("Selector de tenant en la barra superior")

        chapter.add_spacer(0.3)

        # Sección: Cerrar Sesión
        chapter.add_section(
            "2.4 Cerrar Sesión",
            "Por seguridad, siempre cierra tu sesión cuando termines de usar Chandelier, "
            "especialmente si compartes computadora. Para cerrar sesión:\n"
            "1. Haz clic en tu avatar/usuario en la esquina inferior izquierda\n"
            "2. Selecciona 'Cerrar sesión'\n"
            "3. Serás redirigido a la pantalla de login",
        )

        chapter.add_section(
            "2.4.1 Mejores Prácticas de Seguridad",
            "• No compartas tus credenciales con otros usuarios\n"
            "• Usa contraseñas robustas (mínimo 8 caracteres)\n"
            "• Cambia tu contraseña periódicamente\n"
            "• No guards la sesión en equipos compartidos",
        )

        chapter.add_spacer(0.3)

        # Tabla de características de autenticación
        chapter.add_section(
            "2.5 Características de Seguridad", "Chandelier implementa las siguientes características de seguridad:"
        )

        chapter.add_feature_table(
            [
                {"name": "JWT con expiración 1h", "description": "Token de acceso expira en 1 hora", "available": True},
                {"name": "Refresh tokens 7 días", "description": "Renovación automática de sesión", "available": True},
                {
                    "name": "RLS PostgreSQL",
                    "description": "Aislamiento de datos por tenant en base de datos",
                    "available": True,
                },
                {
                    "name": "Roles por tenant",
                    "description": "El mismo usuario puede tener rol diferente en cada empresa",
                    "available": True,
                },
                {
                    "name": "Hash de contraseñas bcrypt",
                    "description": "Contraseñas hasheadas con salt",
                    "available": True,
                },
                {
                    "name": "Header X-Tenant-ID",
                    "description": "Identificador de tenant en cada request",
                    "available": True,
                },
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        return chapter.build()
