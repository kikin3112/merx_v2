/**
 * Store Zustand normalizado para productos.
 * Estructura { ids, entities } garantiza fuente única de verdad:
 * una sola mutación actualiza todas las vistas suscritas.
 */
import { create } from 'zustand';
import type { Producto } from '../types';

interface ProductState {
  ids: string[];
  entities: Record<string, Producto>;
  nextCursor: string | null;
  hasMore: boolean;
  isLoading: boolean;

  setProducts: (products: Producto[], nextCursor: string | null, hasMore: boolean) => void;
  appendProducts: (products: Produto[], nextCursor: string | null, hasMore: boolean) => void;
  upsertProduct: (product: Produto) => void;
  removeProduct: (id: string) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

// Alias to fix TS strict — Produto is the same as Produto from types
type Produto = Producto;

const initialState = {
  ids: [] as string[],
  entities: {} as Record<string, Produto>,
  nextCursor: null as string | null,
  hasMore: false,
  isLoading: false,
};

export const useProductStore = create<ProductState>((set) => ({
  ...initialState,

  setProducts: (products, nextCursor, hasMore) =>
    set(() => {
      const entities: Record<string, Produto> = {};
      const ids: string[] = [];
      for (const p of products) {
        entities[p.id] = p;
        ids.push(p.id);
      }
      return { ids, entities, nextCursor, hasMore, isLoading: false };
    }),

  appendProducts: (products, nextCursor, hasMore) =>
    set((state) => {
      const entities = { ...state.entities };
      const ids = [...state.ids];
      for (const p of products) {
        if (!entities[p.id]) ids.push(p.id);
        entities[p.id] = p;
      }
      return { ids, entities, nextCursor, hasMore, isLoading: false };
    }),

  upsertProduct: (product) =>
    set((state) => {
      const entities = { ...state.entities, [product.id]: product };
      const ids = state.ids.includes(product.id) ? state.ids : [...state.ids, product.id];
      return { entities, ids };
    }),

  removeProduct: (id) =>
    set((state) => ({
      ids: state.ids.filter((i) => i !== id),
      entities: Object.fromEntries(Object.entries(state.entities).filter(([k]) => k !== id)),
    })),

  setLoading: (isLoading) => set({ isLoading }),

  reset: () => set(initialState),
}));
