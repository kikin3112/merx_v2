import { useAuthStore } from '../stores/authStore';
import { useNavigate } from 'react-router-dom';

export default function ImpersonationBanner() {
  const impersonation = useAuthStore((s) => s.impersonation);
  const endImpersonation = useAuthStore((s) => s.endImpersonation);
  const navigate = useNavigate();

  if (!impersonation) return null;

  const handleEnd = () => {
    endImpersonation();
    navigate('/tenants');
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        backgroundColor: '#F59E0B',
        color: '#78350F',
        padding: '8px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '14px',
        fontWeight: 500,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '16px' }}>⚠️</span>
        <span>
          <strong>Modo Impersonación:</strong> actuando como{' '}
          <strong>{impersonation.userName}</strong> ({impersonation.userEmail}) —
          rol <strong>{impersonation.rolEnTenant}</strong> en{' '}
          <strong>{impersonation.tenantName}</strong>
        </span>
      </div>
      <button
        onClick={handleEnd}
        style={{
          backgroundColor: '#92400E',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          padding: '4px 12px',
          cursor: 'pointer',
          fontWeight: 600,
          fontSize: '13px',
          whiteSpace: 'nowrap',
        }}
      >
        Terminar sesión
      </button>
    </div>
  );
}
