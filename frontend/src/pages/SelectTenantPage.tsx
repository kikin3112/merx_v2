import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function SelectTenantPage() {
  const { tenants, selectTenant, user } = useAuthStore();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Superadmin doesn't need tenant selection — redirect to admin panel
  if (user?.es_superadmin) {
    return <Navigate to="/tenants" replace />;
  }

  const handleSelect = async (tenantId: string) => {
    setLoading(true);
    setError('');
    try {
      await selectTenant(tenantId);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al seleccionar empresa');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50 px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-xl font-bold text-gray-900 text-center mb-6">Selecciona tu empresa</h1>
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2 mb-4">{error}</div>
        )}
        <div className="space-y-3">
          {tenants.map((t) => (
            <button
              key={t.id}
              onClick={() => handleSelect(t.id)}
              disabled={loading}
              className="w-full rounded-xl bg-white border border-gray-200 p-4 text-left hover:border-primary-300 hover:shadow-sm transition-all disabled:opacity-50"
            >
              <p className="font-semibold text-gray-900">{t.nombre}</p>
              <p className="text-xs text-gray-500 mt-0.5">{t.slug}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
