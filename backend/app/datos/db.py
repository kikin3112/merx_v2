from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# IMPORTANTE: Import relativo para hacer el módulo portable
from ..config import settings
from ..utils.logger import setup_logger

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


def get_db():
    """
    Dependencia de FastAPI para inyección de sesión DB.
    Maneja automáticamente el commit/rollback y cierre.
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