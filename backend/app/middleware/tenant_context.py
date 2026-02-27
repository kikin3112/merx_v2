"""
Middleware para contexto de tenant en PostgreSQL RLS.
Establece la variable de sesión app.tenant_id_actual para Row Level Security.
"""

import time
from contextvars import ContextVar
from typing import Optional
from uuid import UUID

from fastapi import Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..utils.logger import setup_logger

# ---------------------------------------------------------------------------
# Maintenance Mode cache — {str(tenant_id): (estado: str, timestamp: float)}
# TTL: 60 seconds to avoid DB hit on every write request
# ---------------------------------------------------------------------------
_MAINTENANCE_CACHE: dict = {}
_MAINTENANCE_CACHE_TTL = 60.0  # seconds


def _is_tenant_in_maintenance(tenant_id: UUID) -> bool:
    """
    Checks if a tenant is in 'mantenimiento' state.
    Results are cached for 60 seconds to avoid a DB hit per request.
    """
    key = str(tenant_id)
    now = time.monotonic()

    if key in _MAINTENANCE_CACHE:
        estado, ts = _MAINTENANCE_CACHE[key]
        if now - ts < _MAINTENANCE_CACHE_TTL:
            return estado == "mantenimiento"

    # Cache miss — query DB synchronously (short query, acceptable latency)
    try:
        from ..datos.db import SessionLocal
        from ..datos.modelos_tenant import Tenants

        db = SessionLocal()
        try:
            row = db.query(Tenants.estado).filter(Tenants.id == tenant_id).first()
            estado = row[0] if row else "activo"
            _MAINTENANCE_CACHE[key] = (estado, now)
            return estado == "mantenimiento"
        finally:
            db.close()
    except Exception:
        return False  # On error, allow request through


def invalidate_maintenance_cache(tenant_id: UUID) -> None:
    """Call this when tenant estado changes to ensure fresh reads."""
    _MAINTENANCE_CACHE.pop(str(tenant_id), None)


logger = setup_logger(__name__)

# ContextVar para almacenar el tenant_id del request actual
_current_tenant_id: ContextVar[Optional[UUID]] = ContextVar("current_tenant_id", default=None)


def get_current_tenant_id() -> Optional[UUID]:
    """
    Obtiene el tenant_id del contexto actual.
    Útil para acceder al tenant desde cualquier parte del código.
    """
    return _current_tenant_id.get()


def set_current_tenant_id(tenant_id: Optional[UUID]) -> None:
    """
    Establece el tenant_id en el contexto actual.
    """
    _current_tenant_id.set(tenant_id)


def clear_current_tenant_id() -> None:
    """
    Limpia el tenant_id del contexto actual.
    """
    _current_tenant_id.set(None)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware que extrae el tenant_id del header X-Tenant-ID
    y lo establece en el contexto de PostgreSQL para RLS.
    """

    # Rutas que no requieren tenant_id
    EXCLUDED_PATHS = {
        "/",
        "/health",
        "/health/ready",
        "/health/startup",
        "/api/v1/docs",
        "/api/v1/redoc",
        "/api/v1/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/select-tenant",
        "/api/v1/auth/me",
        "/api/v1/auth/change-password",
        "/api/v1/auth/logout",
        "/api/v1/tenants/register",  # Registro público de nuevos tenants
        "/api/v1/admin/seed",
        "/api/v1/auth/clerk-exchange",  # Clerk: no tiene tenant aún al intercambiar token
        "/api/v1/auth/clerk-webhook",  # Clerk: webhook del sistema, sin tenant
    }

    # Prefijos que no requieren tenant_id
    EXCLUDED_PREFIXES = (
        "/api/v1/superadmin/",  # Rutas de superadmin
        "/api/v1/tenants/",  # Tenant management (superadmin + public routes)
        "/api/v1/sse/",  # SSE: EventSource no soporta headers custom; tenant validado vía JWT
    )

    async def dispatch(self, request: Request, call_next):
        """
        Procesa cada request:
        1. Extrae X-Tenant-ID del header
        2. Valida el formato UUID
        3. Establece el contexto para RLS
        """
        path = request.url.path

        # Allow OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Verificar si la ruta está excluida
        if self._is_excluded_path(path):
            return await call_next(request)

        # Extraer tenant_id del header
        tenant_id_header = request.headers.get("X-Tenant-ID")

        if not tenant_id_header:
            # Para rutas no excluidas, el header es requerido
            logger.warning(f"Request sin X-Tenant-ID: {request.method} {path}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Header X-Tenant-ID es requerido"},
            )

        # Validar formato UUID
        try:
            tenant_id = UUID(tenant_id_header)
        except ValueError:
            logger.warning(f"X-Tenant-ID inválido: {tenant_id_header}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Tenant-ID debe ser un UUID válido"},
            )

        # Establecer en ContextVar
        set_current_tenant_id(tenant_id)

        # Guardar en request.state para acceso fácil
        request.state.tenant_id = tenant_id

        # --- Maintenance Mode: block writes ---
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if _is_tenant_in_maintenance(tenant_id):
                clear_current_tenant_id()
                logger.info(f"Escritura bloqueada por mantenimiento: {request.method} {path} tenant={tenant_id}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "El tenant está en modo mantenimiento. "
                        "Las escrituras están temporalmente bloqueadas. Intente más tarde."
                    },
                )

        try:
            logger.debug(f"Tenant context establecido: {tenant_id}")
            response = await call_next(request)
            return response
        finally:
            # Limpiar contexto al terminar
            clear_current_tenant_id()

    def _is_excluded_path(self, path: str) -> bool:
        """
        Verifica si la ruta está excluida del requerimiento de tenant_id.
        """
        # Verificar rutas exactas
        if path in self.EXCLUDED_PATHS:
            return True

        # Verificar prefijos
        if path.startswith(self.EXCLUDED_PREFIXES):
            return True

        return False


def set_tenant_context_for_session(db: Session, tenant_id: UUID) -> None:
    """
    Establece el tenant_id en la sesión de PostgreSQL para RLS.
    Debe llamarse al inicio de cada transacción que requiera aislamiento.

    Args:
        db: Sesión de SQLAlchemy
        tenant_id: UUID del tenant

    Ejemplo:
        ```python
        def get_productos(db: Session, tenant_id: UUID):
            set_tenant_context_for_session(db, tenant_id)
            return db.query(Productos).all()  # RLS filtra automáticamente
        ```
    """
    try:
        db.execute(text("SET LOCAL app.tenant_id_actual = :tenant_id"), {"tenant_id": str(tenant_id)})
        logger.debug(f"PostgreSQL tenant context establecido: {tenant_id}")
    except Exception as e:
        logger.error(f"Error estableciendo tenant context: {e}")
        raise


def get_tenant_id_from_session(db: Session) -> Optional[str]:
    """
    Obtiene el tenant_id actual configurado en la sesión de PostgreSQL.
    Útil para debugging y validación.
    """
    try:
        result = db.execute(text("SELECT current_setting('app.tenant_id_actual', true)"))
        row = result.fetchone()
        return row[0] if row and row[0] else None
    except Exception as e:
        logger.error(f"Error obteniendo tenant context: {e}")
        return None


# SQL para crear las políticas RLS (para referencia en migraciones)
RLS_POLICIES_SQL = """
-- Habilitar RLS en tablas de negocio
-- Ejecutar después de agregar tenant_id a cada tabla

-- Ejemplo para tabla productos:
ALTER TABLE productos ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_productos ON productos
    USING (tenant_id::text = current_setting('app.tenant_id_actual', true));

-- Política para INSERT (nuevos registros)
CREATE POLICY tenant_insert_productos ON productos
    FOR INSERT
    WITH CHECK (tenant_id::text = current_setting('app.tenant_id_actual', true));

-- Política para UPDATE
CREATE POLICY tenant_update_productos ON productos
    FOR UPDATE
    USING (tenant_id::text = current_setting('app.tenant_id_actual', true));

-- Política para DELETE
CREATE POLICY tenant_delete_productos ON productos
    FOR DELETE
    USING (tenant_id::text = current_setting('app.tenant_id_actual', true));

-- IMPORTANTE: El usuario de la aplicación NO debe ser superuser
-- Los superusers bypasean RLS automáticamente
"""
