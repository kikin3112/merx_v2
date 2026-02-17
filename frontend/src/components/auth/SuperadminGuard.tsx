import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

interface SuperadminGuardProps {
  children: ReactNode;
}

/**
 * Route guard for superadmin-only routes.
 * Blocks impersonation tokens and non-superadmin users.
 */
export default function SuperadminGuard({ children }: SuperadminGuardProps) {
  const { user, impersonation } = useAuthStore();

  // Block impersonation from superadmin routes
  if (impersonation) {
    return <Navigate to="/" replace />;
  }

  if (!user?.es_superadmin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
