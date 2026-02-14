"""
Sistema de logging centralizado y estructurado.
Soporta formato JSON para producción y texto legible para desarrollo.
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

# ============================================================================
# CONTEXT VARS PARA REQUEST TRACKING
# ============================================================================

# Variables de contexto para rastrear requests a través del stack
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


# ============================================================================
# FORMATEADORES
# ============================================================================

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Formateador JSON personalizado que agrega campos de contexto.
    Incluye: timestamp, level, logger, message, request_id, user_id, exception.
    """

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """
        Agrega campos personalizados al log record.
        """
        super().add_fields(log_record, record, message_dict)

        # Timestamp en formato ISO 8601 con timezone UTC
        if not log_record.get('timestamp'):
            now = datetime.now(timezone.utc).isoformat()
            log_record['timestamp'] = now

        # Nivel de log en mayúsculas
        log_record['level'] = record.levelname.upper()

        # Nombre del logger (módulo)
        log_record['logger'] = record.name

        # Información de contexto de request (si existe)
        request_id = request_id_var.get()
        if request_id:
            log_record['request_id'] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_record['user_id'] = user_id

        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_record['correlation_id'] = correlation_id

        # Información de ubicación del código
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

        # Excepción (si existe)
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


class CustomTextFormatter(logging.Formatter):
    """
    Formateador de texto para desarrollo.
    Más legible que JSON cuando se trabaja localmente.
    """

    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el log con colores y estructura legible.
        """
        # Color según nivel
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        # Contexto de request (si existe)
        context_parts = []
        request_id = request_id_var.get()
        if request_id:
            context_parts.append(f"req={request_id[:8]}")

        user_id = user_id_var.get()
        if user_id:
            context_parts.append(f"user={user_id[:8]}")

        context = f" [{', '.join(context_parts)}]" if context_parts else ""

        # Mensaje base
        base_msg = f"{timestamp} {color}{record.levelname:8}{reset} {record.name:30} {record.getMessage()}{context}"

        # Excepción (si existe)
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            return f"{base_msg}\n{exc_text}"

        return base_msg


# ============================================================================
# CONFIGURACIÓN DE LOGGER
# ============================================================================

def setup_logger(
        name: str,
        level: Optional[str] = None,
        format_type: Optional[str] = None
) -> logging.Logger:
    """
    Configura y retorna un logger con el formato adecuado.

    Args:
        name: Nombre del logger (usualmente __name__ del módulo)
        level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Si es None, intenta leer de settings.LOG_LEVEL
        format_type: Tipo de formato ('json' o 'text')
                     Si es None, intenta leer de settings.LOG_FORMAT

    Returns:
        Logger configurado

    Ejemplo:
        logger = setup_logger(__name__)
        logger.info("Servidor iniciado", extra={"port": 8000})
    """
    logger = logging.getLogger(name)

    # Evitar duplicación de handlers si se llama múltiples veces
    if logger.handlers:
        return logger

    # Evitar propagación al root logger (evita duplicados)
    logger.propagate = False

    # Determinar nivel de log
    if level is None:
        try:
            from ..config import settings
            level = settings.LOG_LEVEL
        except ImportError:
            level = "INFO"

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Determinar formato
    if format_type is None:
        try:
            from ..config import settings
            format_type = settings.LOG_FORMAT
        except ImportError:
            format_type = "text"

    # Handler para STDOUT (recomendado para Docker/Kubernetes)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)

    # Aplicar formateador
    if format_type == "json":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = CustomTextFormatter()

    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # ========================================================================
    # FILE HANDLER - Logs rotativos en archivos
    # ========================================================================
    try:
        # Crear directorio de logs si no existe
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Handler de archivo con rotación automática
        # - Rota cuando el archivo alcanza 10MB
        # - Mantiene 5 archivos de backup (app.log.1, app.log.2, etc.)
        # - Total storage: ~50MB de logs
        file_handler = RotatingFileHandler(
            filename=log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)

        # Logs de archivo SIEMPRE en formato JSON (más fácil de parsear)
        json_formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

    except Exception as e:
        # Si falla la creación del file handler, solo log a stdout
        # (no queremos que falle el servidor por esto)
        logger.warning(f"No se pudo crear file handler para logs: {e}")

    return logger


# ============================================================================
# HELPERS PARA CONTEXTO DE REQUEST
# ============================================================================

def set_request_context(
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
) -> None:
    """
    Establece el contexto de request para logging.
    Debe llamarse al inicio de cada request (middleware).

    Args:
        request_id: ID único del request
        user_id: ID del usuario autenticado (si aplica)
        correlation_id: ID para rastrear requests relacionados

    Ejemplo:
        # En middleware de FastAPI
        @app.middleware("http")
        async def logging_middleware(request: Request, call_next):
            request_id = str(uuid.uuid4())
            set_request_context(request_id=request_id)
            response = await call_next(request)
            return response
    """
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if correlation_id:
        correlation_id_var.set(correlation_id)


def clear_request_context() -> None:
    """
    Limpia el contexto de request.
    Debe llamarse al final de cada request (middleware).
    """
    request_id_var.set(None)
    user_id_var.set(None)
    correlation_id_var.set(None)


def get_request_context() -> Dict[str, Optional[str]]:
    """
    Obtiene el contexto actual de request.

    Returns:
        Diccionario con request_id, user_id, correlation_id
    """
    return {
        'request_id': request_id_var.get(),
        'user_id': user_id_var.get(),
        'correlation_id': correlation_id_var.get()
    }


# ============================================================================
# LOGGER GLOBAL DE LA APLICACIÓN
# ============================================================================

# Logger principal de la aplicación
app_logger = setup_logger("app")


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def log_exception(
        logger: logging.Logger,
        exc: Exception,
        message: str = "Excepción capturada",
        **extra_context
) -> None:
    """
    Loguea una excepción con contexto adicional.

    Args:
        logger: Logger a usar
        exc: Excepción capturada
        message: Mensaje descriptivo
        **extra_context: Contexto adicional como kwargs

    Ejemplo:
        try:
            result = risky_operation()
        except ValueError as e:
            log_exception(logger, e, "Error en operación riesgosa", user_id=123)
    """
    logger.error(
        message,
        exc_info=exc,
        extra=extra_context
    )


def log_performance(
        logger: logging.Logger,
        operation: str,
        duration_ms: float,
        **extra_context
) -> None:
    """
    Loguea métricas de performance.

    Args:
        logger: Logger a usar
        operation: Nombre de la operación
        duration_ms: Duración en milisegundos
        **extra_context: Contexto adicional

    Ejemplo:
        start = time.time()
        result = expensive_operation()
        duration = (time.time() - start) * 1000
        log_performance(logger, "expensive_operation", duration, result_count=len(result))
    """
    logger.info(
        f"Performance: {operation}",
        extra={
            'operation': operation,
            'duration_ms': duration_ms,
            'metric_type': 'performance',
            **extra_context
        }
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configurar logger
    logger = setup_logger(__name__, level="DEBUG", format_type="text")

    # Establecer contexto
    set_request_context(
        request_id="req-12345",
        user_id="user-67890"
    )

    # Ejemplos de logging
    logger.debug("Mensaje de debug")
    logger.info("Servidor iniciado", extra={"port": 8000})
    logger.warning("Advertencia de ejemplo")
    logger.error("Error de ejemplo")

    try:
        raise ValueError("Error de prueba")
    except ValueError as e:
        log_exception(logger, e, "Ejemplo de excepción")

    # Limpiar contexto
    clear_request_context()