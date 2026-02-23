"""
Servicio SSE (Server-Sent Events) para actualizaciones en tiempo real.

Implementa un event bus interno usando asyncio.Queue por conexión.
Cuando un endpoint modifica el estado de una factura (u otro evento relevante),
llama a sse_manager.emit_event(tenant_id, event_type, data) para notificar a todos
los clientes conectados de ese tenant.

Escalabilidad:
- Diseño actual: in-process, single worker.
- Mejora futura: PostgreSQL LISTEN/NOTIFY para multi-process.
"""

import asyncio
from typing import Dict, List

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SSEManager:
    """
    Gestiona conexiones SSE organizadas por tenant_id.
    Cada conexión recibe su propia asyncio.Queue.
    """

    def __init__(self) -> None:
        # tenant_id (str) -> lista de queues activas para ese tenant
        self._queues: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, tenant_id: str) -> "asyncio.Queue[dict]":
        """Registra una nueva conexión SSE y devuelve su queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        if tenant_id not in self._queues:
            self._queues[tenant_id] = []
        self._queues[tenant_id].append(queue)
        count = len(self._queues[tenant_id])
        logger.info(f"SSE: nueva suscripción tenant={tenant_id} (total conexiones: {count})")
        return queue

    def unsubscribe(self, tenant_id: str, queue: "asyncio.Queue[dict]") -> None:
        """Elimina la queue cuando la conexión se cierra."""
        queues = self._queues.get(tenant_id, [])
        try:
            queues.remove(queue)
        except ValueError:
            pass
        if not queues and tenant_id in self._queues:
            del self._queues[tenant_id]
        logger.info(f"SSE: suscripción cerrada tenant={tenant_id} (restantes: {len(queues)})")

    def emit_event(self, tenant_id: str, event_type: str, data: dict) -> None:
        """
        Emite un evento a todas las conexiones activas del tenant.

        Usa put_nowait para no bloquear. Si una queue está llena (cliente lento),
        descarta el evento para esa conexión específica.

        Args:
            tenant_id: UUID del tenant como string.
            event_type: Tipo de evento (ej. "factura_estado_cambiado", "alerta_stock").
            data: Payload del evento.
        """
        tenant_key = str(tenant_id)
        queues = list(self._queues.get(tenant_key, []))
        if not queues:
            return

        payload = {"type": event_type, "data": data}
        dropped = 0
        for queue in queues:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                dropped += 1

        if dropped:
            logger.warning(f"SSE: {dropped} evento(s) descartado(s) para tenant={tenant_key} (queues llenas)")

    @property
    def connection_count(self) -> int:
        """Total de conexiones SSE activas en todos los tenants."""
        return sum(len(qs) for qs in self._queues.values())


# Singleton global compartido por toda la aplicación FastAPI
sse_manager = SSEManager()
