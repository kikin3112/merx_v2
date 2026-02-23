/**
 * Store Zustand para el dashboard en tiempo real.
 * Recibe eventos del servidor vía SSE y los expone a los componentes suscritos.
 * Todas las mutaciones usan spread (inmutabilidad garantizada).
 */
import { create } from 'zustand';

export interface FacturaEvento {
  factura_id: string;
  numero: string;
  estado: string;
  total: number;
  timestamp: number;
}

export interface AlertaEvento {
  producto_id: string;
  nombre: string;
  stock_actual: number;
  stock_minimo: number;
}

interface DashboardState {
  // Estado de conexión SSE
  sseConnected: boolean;

  // Últimos 20 eventos de facturas recibidos vía SSE
  recentFacturaEvents: FacturaEvento[];

  // Alertas de stock recibidas vía SSE (deduplicadas por producto_id)
  alertasSSE: AlertaEvento[];

  // Acciones
  setSSEConnected: (connected: boolean) => void;
  addFacturaEvento: (evento: Omit<FacturaEvento, 'timestamp'>) => void;
  addAlertaEvento: (alerta: AlertaEvento) => void;
  clearEvents: () => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  sseConnected: false,
  recentFacturaEvents: [],
  alertasSSE: [],

  setSSEConnected: (connected) => set({ sseConnected: connected }),

  addFacturaEvento: (evento) =>
    set((state) => ({
      recentFacturaEvents: [
        { ...evento, timestamp: Date.now() },
        ...state.recentFacturaEvents,
      ].slice(0, 20),
    })),

  addAlertaEvento: (alerta) =>
    set((state) => {
      const idx = state.alertasSSE.findIndex((a) => a.producto_id === alerta.producto_id);
      if (idx >= 0) {
        const updated = [...state.alertasSSE];
        updated[idx] = alerta;
        return { alertasSSE: updated };
      }
      return { alertasSSE: [...state.alertasSSE, alerta] };
    }),

  clearEvents: () => set({ recentFacturaEvents: [], alertasSSE: [] }),
}));
