import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@clerk/clerk-react';
import { useAuthStore } from '../stores/authStore';
import { trackLogin } from '../hooks/useAnalytics';

/**
 * Página de intercambio post-auth de Clerk.
 * 1. Obtiene el JWT de Clerk con useAuth().getToken()
 * 2. Lo intercambia por un custom JWT via POST /auth/clerk-exchange
 * 3. Redirige según tenants disponibles
 */
export default function ClerkCallbackPage() {
  const { getToken, isLoaded, isSignedIn, signOut } = useAuth();
  const clerkExchange = useAuthStore((s) => s.clerkExchange);
  const navigate = useNavigate();
  const executed = useRef(false);
  const isSignedInRef = useRef(isSignedIn);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // Keep ref current so async catch blocks read the latest value, not a stale closure.
  useEffect(() => {
    isSignedInRef.current = isSignedIn;
  }, [isSignedIn]);

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
          // Token unavailable — likely mid-logout. Redirect silently.
          navigate('/login', { replace: true });
          return;
        }

        const tenants = await clerkExchange(clerkToken);
        trackLogin('clerk');

        if (tenants.length === 0) {
          navigate('/registro/empresa', { replace: true });
        } else if (tenants.length === 1) {
          navigate('/', { replace: true });
        } else {
          navigate('/select-tenant', { replace: true });
        }
      } catch (err: unknown) {
        // Use ref (not stale closure) to check current sign-in state mid-flight.
        if (!isSignedInRef.current) {
          navigate('/login', { replace: true });
          return;
        }
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          'Error al conectar con el servidor. Verifica tu conexión.';
        setError(msg);
      }
    };

    doExchange();
  }, [isLoaded, isSignedIn, getToken, clerkExchange, navigate, retryCount]);

  // Error during logout (race condition: isSignedIn stale in closure) — navigate silently
  useEffect(() => {
    if (error && !isSignedIn) {
      navigate('/login', { replace: true });
    }
  }, [error, isSignedIn, navigate]);

  if (error && isSignedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--cv-bg)] px-4">
        <div className="text-center max-w-sm">
          <div className="rounded-full h-12 w-12 bg-[var(--cv-surface)] border border-[var(--cv-negative)]/30 flex items-center justify-center mx-auto mb-4">
            <span className="text-[var(--cv-negative)] text-xl">!</span>
          </div>
          <h2 className="text-lg font-semibold cv-text mb-2">Error al iniciar sesión</h2>
          <p className="text-sm cv-muted mb-6">{error}</p>
          <div className="space-y-2">
            <button
              onClick={() => {
                executed.current = false;
                setError(null);
                setRetryCount((c) => c + 1);
              }}
              className="cv-btn cv-btn-primary w-full"
            >
              Reintentar
            </button>
            <button
              onClick={() => signOut().then(() => navigate('/login', { replace: true }))}
              className="cv-btn cv-btn-ghost w-full"
            >
              Cerrar sesión e intentar de nuevo
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--cv-bg)]">
      <div className="text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[var(--cv-primary)] mx-auto mb-3" />
        <p className="text-sm cv-muted">Iniciando sesión...</p>
      </div>
    </div>
  );
}
