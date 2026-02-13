"""
Rate limiter global usando slowapi.
Módulo separado para evitar imports circulares (main ↔ rutas).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    enabled=settings.RATE_LIMIT_ENABLED,
)
