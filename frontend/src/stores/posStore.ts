import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Producto } from '../types';

interface CartItem {
  producto: Producto;
  cantidad: number;
}

interface POSState {
  cart: CartItem[];
  clienteId: string;
  descuentoGlobal: number;
  /** Tenant this cart belongs to — used to detect cross-tenant stale state */
  cartTenantId: string;

  addToCart: (producto: Producto) => void;
  removeFromCart: (productoId: string) => void;
  updateQuantity: (productoId: string, cantidad: number) => void;
  setCliente: (clienteId: string) => void;
  setDescuento: (descuento: number) => void;
  clearCart: () => void;
  reset: () => void;
  setCartTenant: (tenantId: string) => void;
}

export const usePOSStore = create<POSState>()(
  persist(
    (set) => ({
      cart: [],
      clienteId: '',
      descuentoGlobal: 0,
      cartTenantId: '',

      addToCart: (producto) => set((state) => {
        const existing = state.cart.find(i => i.producto.id === producto.id);
        if (existing) {
          return {
            cart: state.cart.map(i =>
              i.producto.id === producto.id
                ? { ...i, cantidad: i.cantidad + 1 }
                : i
            )
          };
        }
        return { cart: [...state.cart, { producto, cantidad: 1 }] };
      }),

      removeFromCart: (productoId) => set((state) => ({
        cart: state.cart.filter(i => i.producto.id !== productoId)
      })),

      updateQuantity: (productoId, cantidad) => set((state) => {
        if (cantidad <= 0) {
          return { cart: state.cart.filter(i => i.producto.id !== productoId) };
        }
        return {
          cart: state.cart.map(i =>
            i.producto.id === productoId ? { ...i, cantidad } : i
          )
        };
      }),

      setCliente: (clienteId) => set({ clienteId }),
      setDescuento: (descuento) => set({ descuentoGlobal: descuento }),
      clearCart: () => set({ cart: [], clienteId: '', descuentoGlobal: 0 }),
      reset: () => set({ cart: [], clienteId: '', descuentoGlobal: 0, cartTenantId: '' }),
      setCartTenant: (tenantId) => set({ cartTenantId: tenantId }),
    }),
    {
      name: 'chandelier-pos',
      partialize: (state) => ({
        cart: state.cart,
        clienteId: state.clienteId,
        descuentoGlobal: state.descuentoGlobal,
        cartTenantId: state.cartTenantId,
      })
    }
  )
);
