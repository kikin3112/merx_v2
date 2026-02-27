import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Tenant, ImpersonationResponse } from '../types';
import { auth, clerkAuth } from '../api/endpoints';

interface ImpersonationState {
  token: string;            // token de impersonación (15 min)
  originalToken: string;    // token original del superadmin
  originalRefresh: string;  // refresh token del superadmin
  userName: string;         // nombre del usuario impersonado
  userEmail: string;
  tenantId: string;
  tenantName: string;
  rolEnTenant: string;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  tenants: Tenant[];
  tenantId: string | null;
  tenantName: string | null;
  tenantLogo: string | null;
  rolEnTenant: string | null;
  impersonation: ImpersonationState | null;

  login: (email: string, password: string) => Promise<Tenant[]>;
  clerkExchange: (clerkToken: string) => Promise<Tenant[]>;
  selectTenant: (tenantId: string) => Promise<void>;
  refresh: () => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  startImpersonation: (data: ImpersonationResponse, tenantName: string) => void;
  endImpersonation: () => void;
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
      tenantLogo: null,
      rolEnTenant: null,
      impersonation: null,

      login: async (email: string, password: string) => {
        const { data } = await auth.login(email, password);
        set({
          token: data.access_token,
          refreshToken: data.refresh_token,
          user: data.user,
          tenants: data.tenants,
          impersonation: null,
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

      clerkExchange: async (clerkToken: string) => {
        const { data } = await clerkAuth.exchange(clerkToken);
        set({
          token: data.access_token,
          refreshToken: data.refresh_token,
          user: data.user,
          tenants: data.tenants,
          tenantId: null,
          tenantName: null,
          tenantLogo: null,
          rolEnTenant: null,
          impersonation: null,
        });
        if (data.tenants.length === 1) {
          try {
            await get().selectTenant(data.tenants[0].id);
          } catch {
            // Redirigir a SelectTenantPage
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
          tenantLogo: data.tenant.url_logo ?? null,
          rolEnTenant: data.rol_en_tenant,
        });
      },

      refresh: async () => {
        // No refrescar durante impersonación (token de 15 min, sin refresh)
        const { impersonation } = get();
        if (impersonation) return;

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
          tenantLogo: null,
          rolEnTenant: null,
          impersonation: null,
        });
      },

      fetchUser: async () => {
        const { data } = await auth.me();
        set({ user: data });
      },

      startImpersonation: (data: ImpersonationResponse, tenantName: string) => {
        const state = get();
        set({
          impersonation: {
            token: data.access_token,
            originalToken: state.token ?? '',
            originalRefresh: state.refreshToken ?? '',
            userName: data.impersonated_user.nombre,
            userEmail: data.impersonated_user.email,
            tenantId: data.tenant_id,
            tenantName,
            rolEnTenant: data.rol_en_tenant,
          },
          // Reemplazar token activo con el de impersonación
          token: data.access_token,
          tenantId: data.tenant_id,
          tenantName,
        });
      },

      endImpersonation: () => {
        const { impersonation } = get();
        if (!impersonation) return;
        // Restaurar tokens originales del superadmin
        set({
          token: impersonation.originalToken,
          refreshToken: impersonation.originalRefresh,
          tenantId: null,
          tenantName: null,
          tenantLogo: null,
          rolEnTenant: null,
          impersonation: null,
        });
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
        tenantLogo: state.tenantLogo,
        rolEnTenant: state.rolEnTenant,
        impersonation: state.impersonation,
      }),
    }
  )
);
