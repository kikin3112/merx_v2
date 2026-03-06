import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { trackTenantSelect } from '../hooks/useAnalytics';

export default function SelectTenantPage() {
  const { tenants, selectTenant, user } = useAuthStore();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Superadmin doesn't need tenant selection — redirect to admin panel
  if (user?.es_superadmin) {
    return <Navigate to="/tenants" replace />;
  }

  // New user with no tenants — redirect to company creation wizard
  if (tenants.length === 0) {
    return <Navigate to="/registro/empresa" replace />;
  }

  const handleSelect = async (tenantId: string) => {
    setLoading(true);
    setError('');
    try {
      await selectTenant(tenantId);
      const tenant = tenants.find((t) => t.id === tenantId);
      trackTenantSelect(tenant?.nombre ?? tenantId);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al seleccionar empresa');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--cv-bg)] px-4">
      <div className="w-full max-w-sm">
        <h1 className="font-brand text-xl font-medium cv-text text-center mb-6">Selecciona tu empresa</h1>
        {error && (
          <div className="cv-alert-error px-4 py-2 text-sm mb-4">{error}</div>
        )}
        <div className="space-y-3">
          {tenants.map((t) => (
            <button
              key={t.id}
              onClick={() => handleSelect(t.id)}
              disabled={loading}
              className="cv-card w-full p-4 text-left hover:border-[var(--cv-primary)] hover:shadow-sm transition-all disabled:opacity-50"
            >
              <p className="font-semibold cv-text">{t.nombre}</p>
              <p className="text-xs cv-muted mt-0.5">{t.slug}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
