import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Tenant } from '../types';
import { auth } from '../api/endpoints';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  tenants: Tenant[];
  tenantId: string | null;
  tenantName: string | null;

  login: (email: string, password: string) => Promise<Tenant[]>;
  selectTenant: (tenantId: string) => Promise<void>;
  refresh: () => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,
      tenants: [],
      tenantId: null,
      tenantName: null,

      login: async (email: string, password: string) => {
        const { data } = await auth.login(email, password);
        set({
          token: data.access_token,
          refreshToken: data.refresh_token,
          user: data.user,
          tenants: data.tenants,
        });
        // Auto-select if only one tenant
        if (data.tenants.length === 1) {
          try {
            await get().selectTenant(data.tenants[0].id);
          } catch {
            // Si falla, el usuario sera redirigido a SelectTenantPage
          }
        }
        return data.tenants;
      },

      selectTenant: async (tenantId: string) => {
        const { data } = await auth.selectTenant(tenantId);
        set({
          token: data.access_token,
          refreshToken: data.refresh_token,
          user: data.user,
          tenantId: data.tenant.id,
          tenantName: data.tenant.nombre,
        });
      },

      refresh: async () => {
        const rt = get().refreshToken;
        const tid = get().tenantId;
        if (!rt) throw new Error('No refresh token');
        const { data } = await auth.refresh(rt, tid);
        set({
          token: data.access_token,
          refreshToken: data.refresh_token,
        });
      },

      logout: () => {
        set({
          token: null,
          refreshToken: null,
          user: null,
          tenants: [],
          tenantId: null,
          tenantName: null,
        });
      },

      fetchUser: async () => {
        const { data } = await auth.me();
        set({ user: data });
      },
    }),
    {
      name: 'chandelier-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        tenants: state.tenants,
        tenantId: state.tenantId,
        tenantName: state.tenantName,
      }),
    }
  )
);
