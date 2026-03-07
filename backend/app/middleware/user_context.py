"""
Middleware para contexto de usuario.
Extrae el user_id del token JWT y lo establece en ContextVar para auditoría automática.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..datos.audit_listeners import clear_current_user_id
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware que extrae el user_id del request.state (establecido por get_current_user)
    y lo guarda en ContextVar para que los event listeners de auditoría lo usen.
    """

    # Rutas que no requieren user_id (públicas, no autenticadas)
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
        "/api/v1/tenants/register",
    }

    async def dispatch(self, request: Request, call_next):
        """
        Procesa cada request:
        1. Ejecuta el request (el dependency get_current_user establece el ContextVar)
        2. Limpia el contexto al finalizar

        A-11: El ContextVar ya es establecido por get_current_user/get_current_user_with_tenant
        en seguridad.py — más confiable que leer request.state antes de call_next.
        """
        try:
            response = await call_next(request)
            return response
        finally:
            # Limpiar siempre al terminar el request
            clear_current_user_id()

    def _is_excluded_path(self, path: str) -> bool:
        """
        Verifica si la ruta está excluida del requerimiento de user_id.
        """
        # Verificar rutas exactas
        if path in self.EXCLUDED_PATHS:
            return True

        # Verificar prefijos (para rutas públicas como /api/v1/admin/seed)
        public_prefixes = ("/api/v1/admin/", "/api/v1/superadmin/")
        if path.startswith(public_prefixes):
            return True

        return False
