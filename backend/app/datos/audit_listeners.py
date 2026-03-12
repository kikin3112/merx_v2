"""
SQLAlchemy Event Listeners para auditoría automática.
Captura automáticamente created_by/updated_by desde el contexto del usuario.
"""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID

from sqlalchemy import event
from sqlalchemy.orm import Session

from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# ContextVar para almacenar el user_id del request actual
_current_user_id: ContextVar[Optional[UUID]] = ContextVar("current_user_id", default=None)


def get_current_user_id() -> Optional[UUID]:
    """
    Obtiene el user_id del contexto actual.
    Útil para acceder al usuario desde cualquier parte del código.
    """
    return _current_user_id.get()


def set_current_user_id(user_id: Optional[UUID]) -> None:
    """
    Establece el user_id en el contexto actual.
    """
    _current_user_id.set(user_id)


def clear_current_user_id() -> None:
    """
    Limpia el user_id del contexto actual.
    """
    _current_user_id.set(None)


def _auto_set_audit_fields(session: Session, flush_context, instances) -> None:
    """
    Event listener que auto-popula created_by/updated_by antes de flush.

    Se ejecuta automáticamente antes de cada flush de SQLAlchemy,
    capturando el user_id del ContextVar y asignándolo a los objetos modificados.

    Args:
        session: Sesión de SQLAlchemy
        flush_context: Contexto del flush
        instances: Instancias afectadas (no usado)
    """
    current_user_id = get_current_user_id()

    # Si no hay usuario en contexto, no hacer nada
    # (Esto puede pasar en seeders, migraciones, tareas Celery, etc.)
    if not current_user_id:
        logger.debug("No current_user_id in context, skipping audit field auto-population")
        return

    # Iterar sobre objetos nuevos (INSERT)
    for obj in session.new:
        if hasattr(obj, "created_by") and obj.created_by is None:
            obj.created_by = current_user_id
            logger.debug(f"Auto-set created_by={current_user_id} on new {obj.__class__.__name__}")

        if hasattr(obj, "updated_by") and obj.updated_by is None:
            obj.updated_by = current_user_id
            logger.debug(f"Auto-set updated_by={current_user_id} on new {obj.__class__.__name__}")

    # Iterar sobre objetos modificados (UPDATE)
    for obj in session.dirty:
        # Solo actualizar si el objeto tiene cambios reales
        if session.is_modified(obj, include_collections=False):
            if hasattr(obj, "updated_by"):
                obj.updated_by = current_user_id
                logger.debug(f"Auto-set updated_by={current_user_id} on modified {obj.__class__.__name__}")

    # Iterar sobre objetos eliminados (para soft delete)
    for obj in session.deleted:
        # Si el objeto tiene soft delete, ya se manejó en el método soft_delete()
        # Pero por si acaso, verificamos:
        if hasattr(obj, "deleted_by") and obj.deleted_by is None:
            obj.deleted_by = current_user_id
            logger.debug(f"Auto-set deleted_by={current_user_id} on deleted {obj.__class__.__name__}")


def register_audit_listeners(session_factory) -> None:
    """
    Registra los event listeners de auditoría en el session factory.

    Debe llamarse una vez al inicializar la aplicación, típicamente en db.py.

    Args:
        session_factory: SQLAlchemy sessionmaker o Session class

    Example:
        ```python
        from sqlalchemy.orm import sessionmaker
        from .audit_listeners import register_audit_listeners

        SessionLocal = sessionmaker(bind=engine)
        register_audit_listeners(SessionLocal)
        ```
    """
    # En SQLAlchemy 2.x, escuchar en Session (clase base) garantiza que el evento
    # se dispare en TODAS las sesiones, no solo las del factory específico.
    # event.listen(session_factory, ...) con una instancia de sessionmaker no propaga.
    event.listen(Session, "before_flush", _auto_set_audit_fields)
    logger.info("Audit event listeners registered successfully")
