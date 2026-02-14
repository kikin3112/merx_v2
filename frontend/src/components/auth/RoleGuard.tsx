import { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

interface RoleGuardProps {
  children: ReactNode;
  allowedRoles: string[];
  fallback?: string;
}

/**
 * Route guard that checks if user has required role in current tenant.
 * Superadmin bypasses role checks when NOT impersonating.
 */
export default function RoleGuard({
  children,
  allowedRoles,
  fallback = '/'
}: RoleGuardProps) {
  const { user, impersonation } = useAuthStore();

  // Determine effective role
  const effectiveRole = impersonation
    ? impersonation.rolEnTenant
    : user?.rol;

  // Superadmin bypasses all role checks (when not impersonating)
  if (user?.es_superadmin && !impersonation) {
    return <>{children}</>;
  }

  if (!effectiveRole || !allowedRoles.includes(effectiveRole)) {
    return <Navigate to={fallback} replace />;
  }

  return <>{children}</>;
}
