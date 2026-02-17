"""
Middleware para contexto de usuario.
Extrae el user_id del token JWT y lo establece en ContextVar para auditoría automática.
"""

from typing import Optional
from uuid import UUID

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..datos.audit_listeners import set_current_user_id, clear_current_user_id
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
        1. Verifica si la ruta está excluida
        2. Extrae user_id del request.state (si existe)
        3. Lo establece en ContextVar para auditoría
        4. Limpia el contexto al finalizar
        """
        path = request.url.path

        # Verificar si la ruta está excluida
        if self._is_excluded_path(path):
            return await call_next(request)

        try:
            # Intentar extraer user_id del request.state
            # (get_current_user dependency lo establece)
            user_id = None

            # El user_id se establece en request.state.current_user cuando
            # el dependency get_current_user se ejecuta en las rutas protegidas
            if hasattr(request.state, "current_user"):
                user = request.state.current_user
                if hasattr(user, "id"):
                    user_id = user.id
                elif isinstance(user, dict) and "id" in user:
                    user_id = user["id"]

            # Establecer en ContextVar si existe
            if user_id:
                set_current_user_id(user_id)
                logger.debug(f"User context establecido: {user_id}")

            # Procesar request
            response = await call_next(request)
            return response

        finally:
            # Siempre limpiar contexto al terminar
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
