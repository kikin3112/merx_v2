/**
 * Hook genérico para conexión SSE con reconexión automática y fallback a polling.
 *
 * - EventSource reconecta automáticamente si el servidor cierra la conexión.
 * - Si EventSource no está disponible, activa polling como fallback.
 * - Los callbacks se almacenan en refs para no forzar reconexión en cada render.
 * - Solo reconecta cuando cambian token o tenantId.
 *
 * Seguridad: Token enviado como query param (EventSource no soporta headers custom).
 */
import { useEffect, useRef } from 'react';
import { useAuthStore } from '../stores/authStore';

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api/v1';
const HEARTBEAT_TIMEOUT_MS = 60_000; // 60s sin heartbeat = reconectar manualmente
const POLL_FALLBACK_MS = 30_000;

export interface SSECallbacks {
  onEvent?: (type: string, data: unknown) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useSSE(callbacks: SSECallbacks = {}) {
  const token = useAuthStore((s) => s.token);
  const tenantId = useAuthStore((s) => s.tenantId);

  // Store callbacks in refs so changing them doesn't trigger reconnect
  const cbRef = useRef(callbacks);
  useEffect(() => {
    cbRef.current = callbacks;
  });

  const isConnectedRef = useRef(false);
  const esRef = useRef<EventSource | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const heartbeatTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!token || !tenantId) return;

    // Clear any existing connection
    function cleanup() {
      esRef.current?.close();
      esRef.current = null;
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
      if (heartbeatTimerRef.current) { clearTimeout(heartbeatTimerRef.current); heartbeatTimerRef.current = null; }
      if (isConnectedRef.current) {
        isConnectedRef.current = false;
        cbRef.current.onDisconnect?.();
      }
    }

    // Fallback polling if SSE not available
    if (typeof EventSource === 'undefined') {
      pollRef.current = setInterval(() => {
        cbRef.current.onEvent?.('poll_tick', {});
      }, POLL_FALLBACK_MS);
      return cleanup;
    }

    function resetHeartbeatTimer() {
      if (heartbeatTimerRef.current) clearTimeout(heartbeatTimerRef.current);
      heartbeatTimerRef.current = setTimeout(() => {
        // No heartbeat received → reconnect
        cleanup();
        connect(); // eslint-disable-line @typescript-eslint/no-use-before-define
      }, HEARTBEAT_TIMEOUT_MS);
    }

    function connect() {
      const url = `${API_BASE}/sse/dashboard?token=${encodeURIComponent(token!)}`;
      const es = new EventSource(url);
      esRef.current = es;

      es.addEventListener('connected', () => {
        isConnectedRef.current = true;
        cbRef.current.onConnect?.();
        resetHeartbeatTimer();
      });

      const TYPED_EVENTS = ['factura_estado_cambiado', 'alerta_stock'] as const;
      for (const evtType of TYPED_EVENTS) {
        es.addEventListener(evtType, (evt: Event) => {
          resetHeartbeatTimer();
          try {
            const data = JSON.parse((evt as MessageEvent).data as string) as unknown;
            cbRef.current.onEvent?.(evtType, data);
          } catch { /* ignore parse errors */ }
        });
      }

      es.onerror = () => {
        // EventSource reconnects automatically; update connection state
        if (isConnectedRef.current) {
          isConnectedRef.current = false;
          cbRef.current.onDisconnect?.();
        }
        // Activate polling fallback while reconnecting
        if (!pollRef.current) {
          pollRef.current = setInterval(() => {
            if (!isConnectedRef.current) {
              cbRef.current.onEvent?.('poll_tick', {});
            } else {
              // Reconnected — clear polling
              if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
            }
          }, POLL_FALLBACK_MS);
        }
      };
    }

    connect();
    return cleanup;
  }, [token, tenantId]); // Only reconnect when auth changes

  return { isConnected: isConnectedRef.current };
}
