/**
 * FASE 07 SLOT — Plan limits hook for Freemium gating (Phase 6 of roadmap).
 * Currently returns unlimited for all features (no gating yet).
 * Phase 6 will populate limits from Clerk publicMetadata.
 */

export interface PlanLimits {
  maxProductos: number;
  maxVentasMes: number;
  maxUsuarios: number;
  canUsePipeline: boolean;
  canUseReportes: boolean;
  canUseIA: boolean;
  canUseWhatsApp: boolean;
  planNombre: string;
  isFreemium: boolean;
}

const UNLIMITED: PlanLimits = {
  maxProductos: Infinity,
  maxVentasMes: Infinity,
  maxUsuarios: Infinity,
  canUsePipeline: true,
  canUseReportes: true,
  canUseIA: true,
  canUseWhatsApp: true,
  planNombre: 'Pro',
  isFreemium: false,
};

export function usePlanLimits(): PlanLimits {
  // TODO Phase 6: Read plan from Clerk publicMetadata JWT claim
  // const user = useAuthStore(s => s.user);
  // const plan = user?.plan ?? 'free';
  // return PLAN_LIMITS[plan];
  return UNLIMITED;
}
