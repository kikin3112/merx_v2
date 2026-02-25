"""
Capítulo 14: Pagos Online (Wompi)
Sistema de suscripciones SaaS y pagos mediante Wompi para el servicio Chandelier.
"""

from typing import List

from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder


class PaymentsChapter:
    """
    Capítulo de Pagos para la guía de usuario.
    Cubre el sistema de suscripciones SaaS y pagos mediante Wompi.
    """

    def __init__(self, style_dict: dict):
        """
        Inicializa el capítulo de pagos.

        Args:
            style_dict: Diccionario de estilos de get_styles()
        """
        self.style_dict = style_dict

    def build(self) -> List:
        """
        Construye el contenido del capítulo de pagos.

        Returns:
            Lista de elementos Platypus
        """
        chapter = ChapterBuilder("14. Pagos Online (Wompi)", self.style_dict)

        # Introducción
        chapter.add_intro(
            "Este capítulo te explicará cómo Chandelier maneja los pagos de suscripción mediante Wompi, "
            "la plataforma de pagos en línea más utilizada en Colombia. Aprende sobre el flujo de pago, "
            "los estados de suscripción y la gestión automática de renovaciones."
        )

        chapter.add_spacer(0.3)

        # Sección: Suscripciones SaaS
        chapter.add_section(
            "14.1 Suscripciones SaaS",
            "Chandelier es un sistema SaaS (Software como Servicio) que requiere una suscripción mensual "
            "para funcionar. Los tenants pagan una mensualidad por acceder al sistema.",
        )

        chapter.add_section(
            "14.1.1 Modelos de Suscripción",
            "Chandelier ofrece diferentes planes según las necesidades de tu empresa:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Básico",
                    "description": "1 usuario, 100 facturas/mes",
                    "available": True,
                },
                {
                    "name": "Profesional",
                    "description": "3 usuarios, 500 facturas/mes",
                    "available": True,
                },
                {
                    "name": "Empresarial",
                    "description": "5+ usuarios, facturas ilimitadas",
                    "available": True,
                },
            ],
            ["Plan", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "14.1.2 Beneficios de la Suscripción",
            "• Acceso al sistema 24/7 desde cualquier dispositivo\n"
            "• Actualizaciones automáticas sin costo adicional\n"
            "• Soporte técnico incluido\n"
            "• Almacenamiento de documentos en la nube\n"
            "• Respaldo automático de datos",
        )

        chapter.add_screenshot_placeholder("Planes de suscripción disponibles")

        chapter.add_spacer(0.3)

        # Sección: Flujo de Pago
        chapter.add_section(
            "14.2 Flujo de Pago",
            "El proceso de pago está diseñado para ser simple y seguro. A continuación, el flujo completo:",
        )

        chapter.add_section(
            "14.2.1 Pasos del Proceso",
            "<b>Paso 1: Selección del Plan</b>\n"
            "• El usuario accede a la página de planes\n"
            "• Compara las características de cada plan\n"
            "• Selecciona el plan deseado\n\n"
            "<b>Paso 2: Redirección a Wompi</b>\n"
            "• El sistema genera un checkout en Wompi\n"
            "• Se muestra el monto a pagar\n"
            "• Se incluye la referencia única de la transacción\n\n"
            "<b>Paso 3: Datos de Pago</b>\n"
            "• El usuario ingresa datos de tarjeta\n"
            "• Wompi procesa la información de forma segura\n"
            "• No se almacenan datos de tarjeta en Chandelier\n\n"
            "<b>Paso 4: Procesamiento</b>\n"
            "• Wompi valida la transacción\n"
            "• Se verifica fondos y autenticación\n"
            "• Se confirma o rechaza el pago\n\n"
            "<b>Paso 5: Notificación (Webhook)</b>\n"
            "• Wompi notifica el resultado a Chandelier\n"
            "• El sistema actualiza el estado de la suscripción\n"
            "• Se envía email de confirmación al usuario\n\n"
            "<b>Paso 6: Acceso Activado</b>\n"
            "• Si el pago fue aprobado, se activa el servicio\n"
            "• Se define la fecha del próximo pago\n"
            "• El usuario puede acceder al sistema",
        )

        chapter.add_screenshot_placeholder("Pantalla de checkout Wompi")

        chapter.add_section(
            "14.2.2 Integración con Wompi",
            "Chandelier se integra con Wompi para procesar pagos de manera segura:\n"
            "• <b>Pasarela de pago:</b> Wompi maneja la transacción\n"
            "• <b>Seguridad:</b> Datos de tarjeta nunca tocan nuestros servidores\n"
            "• <b>Confirmación:</b> Notificaciones en tiempo real\n"
            "• <b>Multicanal:</b> Acepta múltiples tarjetas y métodos",
        )

        chapter.add_spacer(0.3)

        # Sección: Estados de Suscripción
        chapter.add_section(
            "14.3 Estados de Suscripción",
            "Una suscripción puede estar en diferentes estados a lo largo de su ciclo de vida:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Activa",
                    "description": "El servicio está disponible, pagos al día",
                    "available": True,
                },
                {
                    "name": "Suspendida",
                    "description": "Temporalmente sin acceso por falta de pago",
                    "available": True,
                },
                {
                    "name": "Cancelada",
                    "description": "El usuario solicitó cancelar la suscripción",
                    "available": True,
                },
                {
                    "name": "Vencida",
                    "description": "La fecha de renovación expiró sin pago",
                    "available": True,
                },
            ],
            ["Estado", "Descripción", "Acceso al Sistema"],
        )

        chapter.add_section(
            "14.3.1 Transiciones de Estado",
            "• <b>Activa → Suspendida:</b> Cuando falla el pago\n"
            "• <b>Activa → Cancelada:</b> Cuando el usuario cancela\n"
            "• <b>Suspendida → Activa:</b> Cuando se realiza el pago\n"
            "• <b>Cancelada → Activa:</b> Si el usuario reactiva\n"
            "• <b>Vencida → Activa:</b> Tras nuevo pago exitoso",
        )

        chapter.add_screenshot_placeholder("Estado de suscripción en el panel")

        chapter.add_spacer(0.3)

        # Sección: Webhook
        chapter.add_section(
            "14.4 Webhook de Wompi",
            "Chandelier recibe notificaciones automáticas de Wompi mediante webhooks para actualizar "
            "el estado de las suscripciones en tiempo real.",
        )

        chapter.add_section(
            "14.4.1 Cómo Funciona el Webhook",
            "1. <b>Evento:</b> Wompi procesa una transacción\n"
            "2. <b>Notificación:</b> Wompi envía solicitud POST a Chandelier\n"
            "3. <b>Validación:</b> Chandelier verifica la firma del mensaje\n"
            "4. <b>Procesamiento:</b> Se actualiza el estado de la suscripción\n"
            "5. <b>Confirmación:</b> Se envía email al usuario",
        )

        chapter.add_section(
            "14.4.2 Estados de Transacción Wompi",
            "Wompi puede reportar los siguientes estados:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "APPROVED",
                    "description": "Pago aprobado exitosamente",
                    "available": True,
                },
                {
                    "name": "DECLINED",
                    "description": "Pago rechazado por el banco",
                    "available": True,
                },
                {
                    "name": "VOIDED",
                    "description": "Transacción anulada",
                    "available": True,
                },
                {
                    "name": "PENDING",
                    "description": "Esperando confirmación",
                    "available": True,
                },
            ],
            ["Estado", "Descripción", "Acción en Chandelier"],
        )

        chapter.add_section(
            "14.4.3 Manejo de Pagos Rechazados",
            "Si un pago es rechazado:\n"
            "1. Se registra el intento fallido\n"
            "2. Se notifica al usuario por email\n"
            "3. Se da un período de gracia para pagar\n"
            "4. Si fallan 3 intentos → Suspensión automática",
        )

        chapter.add_spacer(0.3)

        # Sección: Renovación
        chapter.add_section(
            "14.5 Renovación Automática",
            "Chandelier gestiona las renovaciones de suscripción de forma automática:",
        )

        chapter.add_section(
            "14.5.1 Proceso de Renovación",
            "1. <b>Verificación Diaria:</b> El sistema verifica suscripciones próximas a vencer\n"
            "2. <b>Notificación:</b> Se recuerda al usuario 3 días antes\n"
            "3. <b>Procesamiento:</b> Se intenta cobrar automáticamente\n"
            "4. <b>Actualización:</b> Se extiende la fecha de vencimiento\n"
            "5. <b>Confirmación:</b> Email de renovación exitosa",
        )

        chapter.add_section(
            "14.5.2 Política de Suspensión",
            "Para proteger tanto al usuario como al sistema:\n"
            "• <b>1° intento fallido:</b> Notificación de aviso\n"
            "• <b>2° intento fallido:</b> Segunda notificación + período de gracia\n"
            "• <b>3° intento fallido:</b> Suspensión automática del servicio\n"
            "• <b>Reactivación:</b> Requiere pago manual + tarifa de reconexión",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Recordatorio 1",
                    "description": "7 días antes del vencimiento",
                    "available": True,
                },
                {
                    "name": "Recordatorio 2",
                    "description": "3 días antes del vencimiento",
                    "available": True,
                },
                {
                    "name": "Notificación de Mora",
                    "description": "Después de primer intento fallido",
                    "available": True,
                },
                {
                    "name": "Suspensión",
                    "description": "Después de 3 intentos fallidos",
                    "available": True,
                },
            ],
            ["Evento", "Timing", "Disponible"],
        )

        chapter.add_screenshot_placeholder("Panel de suscripción con fechas")

        chapter.add_spacer(0.3)

        # Sección: Métodos de Pago
        chapter.add_section(
            "14.6 Métodos de Pago Soportados",
            "Wompi acepta múltiples métodos de pago en Colombia:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Tarjetas Débito",
                    "description": "Visa Débito, Mastercard Débito",
                    "available": True,
                },
                {
                    "name": "Tarjetas Crédito",
                    "description": "Visa, Mastercard, American Express",
                    "available": True,
                },
                {
                    "name": "PSE",
                    "description": "Pagos desde banco en línea",
                    "available": True,
                },
                {
                    "name": "Efecty",
                    "description": "Pago en efectivo",
                    "available": True,
                },
            ],
            ["Método", "Descripción", "Disponible"],
        )

        chapter.add_spacer(0.3)

        # Sección: Configuración
        chapter.add_section(
            "14.7 Gestión de Suscripción",
            "Como administrador, puedes gestionar tu suscripción desde el panel:",
        )

        chapter.add_section(
            "14.7.1 Ver Estado de Suscripción",
            "Para ver el estado de tu suscripción:\n"
            "1. Ve a <b>Configuración > Suscripción</b>\n"
            "2. Verás el plan actual y sus límites\n"
            "3. Podrás ver la fecha de próximo cobro\n"
            "4. Historial de pagos recientes",
        )

        chapter.add_screenshot_placeholder("Panel de suscripción")

        chapter.add_section(
            "14.7.2 Cambiar de Plan",
            "Si necesitas más o menos recursos:\n"
            "1. Ve a <b>Configuración > Suscripción</b>\n"
            "2. Haz clic en <b>Cambiar Plan</b>\n"
            "3. Selecciona el nuevo plan\n"
            "4. Confirma el cambio\n"
            "5. Se ajustará el cobro prorrateado",
        )

        chapter.add_section(
            "14.7.3 Cancelar Suscripción",
            "Si decides cancelar:\n"
            "1. Ve a <b>Configuración > Suscripción</b>\n"
            "2. Haz clic en <b>Cancelar Suscripción</b>\n"
            "3. Confirma la cancelación\n"
            "4. Acceso hasta el final del período pagado\n"
            "5. Datos disponibles para exportación",
        )

        chapter.add_spacer(0.3)

        # Sección: Facturación
        chapter.add_section(
            "14.8 Facturación de Suscripción",
            "Chandelier genera comprobantes de pago:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Recibo de Pago",
                    "description": "Emitido por Wompi tras cada transacción",
                    "available": True,
                },
                {
                    "name": "Factura Electrónica",
                    "description": "Generada por Chandelier para accounting",
                    "available": True,
                },
                {
                    "name": "Certificado de Retención",
                    "description": "Si aplica retención en la fuente",
                    "available": True,
                },
            ],
            ["Documento", "Descripción", "Disponible"],
        )

        chapter.add_section(
            "14.8.1 Descargar Comprobantes",
            "Para descargar tus comprobantes:\n"
            "1. Ve a <b>Configuración > Suscripción</b>\n"
            "2. Busca la sección <b>Historial de Pagos</b>\n"
            "3. Haz clic en el icono de descargar\n"
            "4. Se generará el PDF correspondiente",
        )

        chapter.add_spacer(0.3)

        # Sección: Funcionalidades
        chapter.add_section(
            "14.9 Funcionalidades de Pagos",
            "Chandelier ofrece las siguientes funcionalidades:",
        )

        chapter.add_feature_table(
            [
                {
                    "name": "Pago con Wompi",
                    "description": "Pasarela de pagos segura en Colombia",
                    "available": True,
                },
                {
                    "name": "Webhook Automático",
                    "description": "Notificaciones en tiempo real de pagos",
                    "available": True,
                },
                {
                    "name": "Renovación Automática",
                    "description": "Cobro automático mensualmente",
                    "available": True,
                },
                {
                    "name": "Múltiples Métodos",
                    "description": "Tarjetas, PSE, Efecty",
                    "available": True,
                },
                {
                    "name": "Suspensión Automática",
                    "description": "Suspensión tras 3 pagos fallidos",
                    "available": True,
                },
                {
                    "name": "Cambio de Plan",
                    "description": "Upgrade/downgrade de plan",
                    "available": True,
                },
                {
                    "name": "Comprobantes PDF",
                    "description": "Recibos y facturas de pago",
                    "available": True,
                },
                {
                    "name": "Notificaciones Email",
                    "description": "Alertas de renovación y problemas",
                    "available": True,
                },
            ],
            ["Funcionalidad", "Descripción", "Disponible"],
        )

        chapter.add_spacer(0.3)

        # Sección: Solución de Problemas
        chapter.add_section(
            "14.10 Solución de Problemas",
            "Problemas comunes y cómo resolverlos:",
        )

        chapter.add_section(
            "14.10.1 Pago Rechazado",
            "Si tu pago fue rechazado:\n"
            "• Verifica que la tarjeta esté activa\n"
            "• Confirma que tienes fondos disponibles\n"
            "• Verifica que los datos sean correctos\n"
            "• Intenta con otro método de pago\n"
            "• Contacta a tu banco si persiste",
        )

        chapter.add_section(
            "14.10.2 No Recibí Confirmación",
            "Si no recibiste email de confirmación:\n"
            "• Verifica la carpeta de spam\n"
            "• Confirma que el email sea correcto\n"
            "• Revisa el historial de pagos\n"
            "• Contacta soporte si no aparece",
        )

        chapter.add_section(
            "14.10.3 Acceso Suspendido",
            "Si tu cuenta fue suspendida:\n"
            "• Realiza el pago pendiente\n"
            "• Usa el botón de pago manual\n"
            "• Tras el pago, acceso se reactiva\n"
            "• Puede haber tarifa de reconexión",
        )

        chapter.add_spacer(0.3)

        # Sección: Resumen
        chapter.add_section(
            "14.11 Resumen",
            "En este capítulo aprendiste:\n"
            "• Qué es una suscripción SaaS y los planes disponibles\n"
            "• El flujo completo de pago con Wompi\n"
            "• Los diferentes estados de una suscripción\n"
            "• Cómo funcionan los webhooks de notificación\n"
            "• El proceso de renovación automática\n"
            "• Cómo gestionar tu suscripción desde el panel\n"
            "• Cómo resolver problemas comunes de pago",
        )

        return chapter.build()
