"""
Endpoint SSE (Server-Sent Events) para actualizaciones del dashboard en tiempo real.

Protocolo SSE:
- Cliente conecta: GET /api/v1/sse/dashboard?token=<JWT>
- Servidor envía heartbeats cada 25s para mantener la conexión viva
- Servidor emite eventos cuando facturas cambian de estado
- EventSource del navegador reconecta automáticamente (retry: 5000ms)

Seguridad:
- Token JWT obligatorio como query param (EventSource API no soporta headers custom)
- El token debe contener tenant_id (usuario debe haber seleccionado tenant)
- Filtrado automático por tenant_id del token
- Validación del tipo de token (access token, no refresh)
"""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..servicios.servicio_sse import sse_manager
from ..utils.logger import setup_logger
from ..utils.seguridad import decode_access_token

router = APIRouter()
logger = setup_logger(__name__)

HEARTBEAT_INTERVAL_SECONDS = 25


def _sse_event(event_type: str, data: dict, retry_ms: int = 5000) -> str:
    """Formatea un evento SSE según la especificación W3C."""
    data_str = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {data_str}\nretry: {retry_ms}\n\n"


def _sse_heartbeat() -> str:
    """Comentario SSE para mantener la conexión viva sin disparar onmessage."""
    return ": heartbeat\n\n"


async def _stream_events(tenant_id: str, queue: "asyncio.Queue[dict]") -> AsyncGenerator[str, None]:
    """
    Generador asíncrono de eventos SSE para un cliente conectado.

    1. Emite evento 'connected' al conectarse.
    2. Espera eventos de la queue del tenant.
    3. Emite heartbeat si no hay eventos en HEARTBEAT_INTERVAL_SECONDS.
    4. Termina limpiamente en CancelledError (cliente desconectado).
    """
    # Evento inicial de confirmación de conexión
    yield _sse_event("connected", {"status": "ok", "tenant_id": tenant_id})

    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_INTERVAL_SECONDS)
            yield _sse_event(event["type"], event["data"])
        except asyncio.TimeoutError:
            yield _sse_heartbeat()
        except (asyncio.CancelledError, GeneratorExit):
            break
        except Exception as e:
            logger.error(f"SSE: error en stream para tenant={tenant_id}: {e}")
            break


@router.get("/dashboard")
async def sse_dashboard(
    token: str = Query(..., description="JWT access token del usuario autenticado"),
    _db: Session = Depends(get_db),
):
    """
    Stream SSE para el dashboard de facturación.

    Eventos emitidos:
    - **connected**: Confirmación de conexión.
    - **factura_estado_cambiado**: Cuando una factura cambia de estado (PENDIENTE→FACTURADA, etc.).
    - **alerta_stock**: Cuando un producto cae por debajo del stock mínimo.

    El cliente debe reconectar automáticamente (EventSource lo hace por defecto).
    """
    # Validar token JWT
    try:
        payload = decode_access_token(token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token SSE inválido o expirado",
        )

    # El token debe tener contexto de tenant
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token sin contexto de tenant. Selecciona un tenant antes de conectar.",
        )

    user_id = payload.get("sub", "unknown")
    logger.info(f"SSE: cliente conectado tenant={tenant_id} user={user_id}")

    queue = sse_manager.subscribe(tenant_id)

    async def generate_and_cleanup() -> AsyncGenerator[str, None]:
        try:
            async for chunk in _stream_events(tenant_id, queue):
                yield chunk
        finally:
            sse_manager.unsubscribe(tenant_id, queue)
            logger.info(f"SSE: cliente desconectado tenant={tenant_id} user={user_id}")

    return StreamingResponse(
        generate_and_cleanup(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Desactiva buffering en nginx/Railway
        },
    )


@router.get("/status")
async def sse_status():
    """
    Estado del servicio SSE.
    Útil para monitoreo y debugging.
    """
    return {
        "status": "ok",
        "active_connections": sse_manager.connection_count,
    }
