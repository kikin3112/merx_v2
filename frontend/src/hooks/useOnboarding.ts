import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { productos } from '../api/endpoints';
import { useAuthStore } from '../stores/authStore';

interface OnboardingState {
  completedSteps: number[];
  dismissed: boolean;
}

const TOTAL_STEPS = 5;

function getStorageKey(tenantId: string): string {
  return `chandelier-onboarding-${tenantId}`;
}

function loadState(tenantId: string): OnboardingState {
  try {
    const raw = localStorage.getItem(getStorageKey(tenantId));
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return { completedSteps: [], dismissed: false };
}

function saveState(tenantId: string, state: OnboardingState) {
  localStorage.setItem(getStorageKey(tenantId), JSON.stringify(state));
}

export function useOnboarding() {
  const tenantId = useAuthStore((s) => s.tenantId);
  const user = useAuthStore((s) => s.user);
  const effectiveRole = user?.rol;

  // Only show for admin users
  const isAdmin = effectiveRole === 'admin';

  const [state, setState] = useState<OnboardingState>({ completedSteps: [], dismissed: false });

  // Check if tenant has any products (new tenant indicator)
  const { data: existingProducts, isLoading } = useQuery({
    queryKey: ['onboarding-check', tenantId],
    queryFn: () => productos.list({ limit: 1 }).then((r) => r.data),
    enabled: !!tenantId && isAdmin,
    staleTime: 60_000,
  });

  const isNewTenant = !isLoading && existingProducts && existingProducts.length === 0;

  useEffect(() => {
    if (tenantId) {
      setState(loadState(tenantId));
    }
  }, [tenantId]);

  const completeStep = useCallback((step: number) => {
    if (!tenantId) return;
    setState((prev) => {
      const next = {
        ...prev,
        completedSteps: [...new Set([...prev.completedSteps, step])],
      };
      saveState(tenantId, next);
      return next;
    });
  }, [tenantId]);

  const dismiss = useCallback(() => {
    if (!tenantId) return;
    setState((prev) => {
      const next = { ...prev, dismissed: true };
      saveState(tenantId, next);
      return next;
    });
  }, [tenantId]);

  const shouldShow = isAdmin && isNewTenant && !state.dismissed;
  const currentStep = (() => {
    for (let i = 1; i <= TOTAL_STEPS; i++) {
      if (!state.completedSteps.includes(i)) return i;
    }
    return TOTAL_STEPS + 1; // All done
  })();

  const allCompleted = state.completedSteps.length >= TOTAL_STEPS;

  return {
    shouldShow,
    currentStep,
    completedSteps: state.completedSteps,
    totalSteps: TOTAL_STEPS,
    completeStep,
    dismiss,
    allCompleted,
    isLoading,
  };
}
