from typing import Optional, Generator
from uuid import UUID

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import Pool

# IMPORTANTE: Import relativo para hacer el módulo portable
from ..config import settings
from ..utils.logger import setup_logger
from ..middleware.tenant_context import get_current_tenant_id

logger = setup_logger(__name__)

# Configuración del Engine
# Nota: No usamos event listeners manuales. pool_pre_ping ya maneja la verificación de conexión.
engine = create_engine(
    str(settings.DB_URL),
    pool_pre_ping=True,  # Verifica conexión antes de usar (Reemplaza el listener manual)
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=3600,  # Recicla conexiones cada hora
    pool_timeout=30,  # Timeout de 30 segundos para obtener conexión
    echo=settings.DEBUG  # SQL logging solo en desarrollo
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# ============================================================================
# AUTO-SET TENANT CONTEXT ON TRANSACTION BEGIN (RLS)
# ============================================================================

@event.listens_for(Session, "after_begin")
def _set_tenant_on_transaction_begin(session, transaction, connection):
    """
    Cada vez que una sesión inicia una transacción (incluyendo después de commit),
    establece SET LOCAL app.tenant_id_actual si el ContextVar tiene valor.
    Esto garantiza que RLS funcione automáticamente sin cambios en los servicios.
    """
    tenant_id = get_current_tenant_id()
    if tenant_id:
        connection.execute(
            text("SET LOCAL app.tenant_id_actual = :tid"),
            {"tid": str(tenant_id)}
        )


# ============================================================================
# FUNCIONES PARA CONTEXTO DE TENANT (RLS)
# ============================================================================

def set_tenant_context(db: Session, tenant_id: UUID) -> None:
    """
    Establece el tenant_id en la sesión de PostgreSQL para RLS.
    Usa SET LOCAL para que solo aplique a la transacción actual.

    Args:
        db: Sesión de SQLAlchemy
        tenant_id: UUID del tenant

    Ejemplo:
        ```python
        def crear_producto(db: Session, tenant_id: UUID, data: ProductoCreate):
            set_tenant_context(db, tenant_id)
            producto = Productos(tenant_id=tenant_id, **data.dict())
            db.add(producto)
            db.commit()
            return producto
        ```
    """
    try:
        db.execute(
            text("SET LOCAL app.tenant_id_actual = :tenant_id"),
            {"tenant_id": str(tenant_id)}
        )
        logger.debug(f"Tenant context establecido: {tenant_id}")
    except Exception as e:
        logger.error(f"Error estableciendo tenant context: {e}")
        raise


def clear_tenant_context(db: Session) -> None:
    """
    Limpia el tenant_id de la sesión de PostgreSQL.
    """
    try:
        db.execute(text("RESET app.tenant_id_actual"))
    except Exception:
        pass  # Ignorar errores al limpiar


def get_current_tenant_from_session(db: Session) -> Optional[str]:
    """
    Obtiene el tenant_id actual de la sesión de PostgreSQL.
    Útil para debugging.
    """
    try:
        result = db.execute(
            text("SELECT current_setting('app.tenant_id_actual', true)")
        )
        row = result.fetchone()
        return row[0] if row and row[0] else None
    except Exception:
        return None


# ============================================================================
# DEPENDENCIAS DE FASTAPI
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependencia de FastAPI para inyección de sesión DB.
    Maneja automáticamente el commit/rollback y cierre.

    Uso básico (sin tenant):
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
        # Nota: El commit debe hacerse explícitamente en el Servicio (Service Layer),
        # no aquí, para mantener el control transaccional.
    except Exception as e:
        logger.error(f"Error en sesión de base de datos: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_with_tenant(tenant_id: UUID) -> Generator[Session, None, None]:
    """
    Factory para crear una dependencia de DB con contexto de tenant.

    Uso:
        def get_tenant_db(
            tenant_id: UUID = Depends(get_tenant_id_from_header)
        ):
            return get_db_with_tenant(tenant_id)
    """
    db = SessionLocal()
    try:
        set_tenant_context(db, tenant_id)
        yield db
    except Exception as e:
        logger.error(f"Error en sesión de base de datos: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


class TenantSession:
    """
    Context manager para sesiones con tenant.

    Uso:
        with TenantSession(tenant_id) as db:
            productos = db.query(Productos).all()
    """

    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
        self.db: Optional[Session] = None

    def __enter__(self) -> Session:
        self.db = SessionLocal()
        set_tenant_context(self.db, self.tenant_id)
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            if exc_type:
                self.db.rollback()
            self.db.close()
        return False