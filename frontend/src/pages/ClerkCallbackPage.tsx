import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@clerk/clerk-react';
import { useAuthStore } from '../stores/authStore';

/**
 * Página de intercambio post-auth de Clerk.
 * 1. Obtiene el JWT de Clerk con useAuth().getToken()
 * 2. Lo intercambia por un custom JWT via POST /auth/clerk-exchange
 * 3. Redirige según tenants disponibles
 */
export default function ClerkCallbackPage() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const clerkExchange = useAuthStore((s) => s.clerkExchange);
  const navigate = useNavigate();
  const executed = useRef(false);

  useEffect(() => {
    if (!isLoaded) return;
    if (executed.current) return;
    executed.current = true;

    if (!isSignedIn) {
      navigate('/login', { replace: true });
      return;
    }

    const doExchange = async () => {
      try {
        const clerkToken = await getToken();
        if (!clerkToken) {
          navigate('/login', { replace: true });
          return;
        }

        const tenants = await clerkExchange(clerkToken);

        if (tenants.length === 0) {
          // Sin tenants: ir al wizard de registro de empresa
          navigate('/registro/empresa', { replace: true });
        } else if (tenants.length === 1) {
          // Ya fue auto-seleccionado en clerkExchange
          navigate('/', { replace: true });
        } else {
          // Múltiples tenants: selección manual
          navigate('/select-tenant', { replace: true });
        }
      } catch {
        navigate('/login', { replace: true });
      }
    };

    doExchange();
  }, [isLoaded, isSignedIn, getToken, clerkExchange, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500 mx-auto mb-3" />
        <p className="text-sm text-gray-500">Iniciando sesión...</p>
      </div>
    </div>
  );
}
