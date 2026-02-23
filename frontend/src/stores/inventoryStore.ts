/**
 * Store Zustand normalizado para inventario.
 * Expone vista jerárquica: total → por producto → movimientos recientes.
 */
import { create } from 'zustand';
import type { Inventario, AlertaStock } from '../types';

interface InventoryState {
  ids: string[];
  entities: Record<string, Inventario>;
  alertas: AlertaStock[];
  isLoading: boolean;

  setInventory: (items: Inventario[]) => void;
  setAlertas: (alertas: AlertaStock[]) => void;
  upsertItem: (item: Inventario) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

const initialState = {
  ids: [] as string[],
  entities: {} as Record<string, Inventario>,
  alertas: [] as AlertaStock[],
  isLoading: false,
};

export const useInventoryStore = create<InventoryState>((set) => ({
  ...initialState,

  setInventory: (items) =>
    set(() => {
      const entities: Record<string, Inventario> = {};
      const ids: string[] = [];
      for (const item of items) {
        entities[item.producto_id] = item;
        ids.push(item.producto_id);
      }
      return { ids, entities, isLoading: false };
    }),

  setAlertas: (alertas) => set({ alertas }),

  upsertItem: (item) =>
    set((state) => {
      const entities = { ...state.entities, [item.producto_id]: item };
      const ids = state.ids.includes(item.producto_id)
        ? state.ids
        : [...state.ids, item.producto_id];
      return { entities, ids };
    }),

  setLoading: (isLoading) => set({ isLoading }),

  reset: () => set(initialState),
}));
