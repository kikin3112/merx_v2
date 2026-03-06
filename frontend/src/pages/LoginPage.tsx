import { useState, useEffect, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { SignIn, useAuth } from '@clerk/clerk-react';
import { useAuthStore } from '../stores/authStore';

const CLERK_PUB_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;

interface LegacyFormProps {
  onBack?: () => void;
}

function LegacyLoginForm({ onBack }: LegacyFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const tenants = await login(email, password);
      if (tenants.length === 1) {
        navigate('/');
      } else {
        navigate('/select-tenant');
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Error al iniciar sesión';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const formContent = (
    <div className="w-full max-w-sm">
      <div className="text-center mb-8">
        <div className="mx-auto h-14 w-14 rounded-2xl bg-primary-500 flex items-center justify-center mb-4">
          <span className="text-white text-2xl font-bold">C</span>
        </div>
        <h1 className="font-brand text-2xl font-medium cv-text">chandelierp</h1>
        <p className="text-sm cv-muted mt-1">ERP para cerer@s hecho con &lt;3</p>
      </div>

      <form onSubmit={handleSubmit} className="cv-card p-6 space-y-4">
        {error && (
          <div className="cv-alert-error px-3 py-2 text-sm">{error}</div>
        )}

        <div>
          <label className="block text-sm font-medium cv-muted mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="cv-input"
            placeholder="correo@ejemplo.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium cv-muted mb-1">Contraseña</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="cv-input"
            placeholder="*******"
          />
        </div>

        <button type="submit" disabled={loading} className="cv-btn cv-btn-primary w-full">
          {loading ? 'Ingresando...' : 'Ingresar'}
        </button>
      </form>

      <div className="mt-4 space-y-2 text-center">
        {onBack && (
          <button onClick={onBack} className="block w-full text-sm cv-primary font-medium">
            ← Volver a opciones de inicio de sesión
          </button>
        )}
        <p className="text-sm cv-muted">
          ¿No tienes cuenta?{' '}
          <Link to="/registro" className="cv-primary font-medium">
            Regístrate gratis
          </Link>
        </p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--cv-bg)] px-4">
      {formContent}
    </div>
  );
}

function ClerkLoginView() {
  const { isSignedIn, isLoaded } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      navigate('/clerk-callback', { replace: true });
    }
  }, [isLoaded, isSignedIn, navigate]);

  if (!isLoaded || isSignedIn) return null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--cv-bg)] px-4">
      <SignIn
        routing="path"
        path="/login"
        forceRedirectUrl="/clerk-callback"
        appearance={{
          variables: {
            colorPrimary: '#C17B2B',
          },
        }}
      />
    </div>
  );
}

export default function LoginPage() {
  if (CLERK_PUB_KEY) {
    return <ClerkLoginView />;
  }
  return <LegacyLoginForm />;
}
