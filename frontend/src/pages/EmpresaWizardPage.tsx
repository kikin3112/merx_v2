import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { registro } from '../api/endpoints';
import { useAuthStore } from '../stores/authStore';

/**
 * Wizard de empresa para usuarios que ya se autenticaron via Clerk
 * pero todavía no tienen ningún tenant.
 *
 * Ruta: /registro/empresa
 * Requiere: custom JWT (obtenido en /clerk-callback via clerkExchange)
 */

const DEPARTAMENTOS_CO = [
  'Amazonas', 'Antioquia', 'Arauca', 'Atlántico', 'Bolívar', 'Boyacá',
  'Caldas', 'Caquetá', 'Casanare', 'Cauca', 'Cesar', 'Chocó', 'Córdoba',
  'Cundinamarca', 'Guainía', 'Guaviare', 'Huila', 'La Guajira', 'Magdalena',
  'Meta', 'Nariño', 'Norte de Santander', 'Putumayo', 'Quindío', 'Risaralda',
  'San Andrés y Providencia', 'Santander', 'Sucre', 'Tolima', 'Valle del Cauca',
  'Vaupés', 'Vichada', 'Bogotá D.C.',
];

function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60);
}

type Step = 1 | 2;

function StepIndicator({ current }: { current: Step }) {
  const steps = [
    { num: 1, label: 'Empresa' },
    { num: 2, label: 'Confirmar' },
  ];
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {steps.map((s, i) => (
        <div key={s.num} className="flex items-center">
          <div
            className={`flex items-center justify-center h-8 w-8 rounded-full text-sm font-semibold transition-colors ${
              s.num === current
                ? 'bg-[var(--cv-primary)] text-white'
                : s.num < current
                  ? 'bg-[var(--cv-primary-dim)] text-[var(--cv-primary)]'
                  : 'cv-elevated cv-muted'
            }`}
          >
            {s.num < current ? '✓' : s.num}
          </div>
          <span className="ml-1.5 text-xs cv-muted hidden sm:inline">{s.label}</span>
          {i < steps.length - 1 && <div className="w-8 h-px bg-[var(--cv-divider)] mx-2" />}
        </div>
      ))}
    </div>
  );
}

export default function EmpresaWizardPage() {
  const navigate = useNavigate();
  const selectTenant = useAuthStore((s) => s.selectTenant);
  const token = useAuthStore((s) => s.token);
  const tenants = useAuthStore((s) => s.tenants);

  const [step, setStep] = useState<Step>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [nombreEmpresa, setNombreEmpresa] = useState('');
  const [slug, setSlug] = useState('');
  const [slugManual, setSlugManual] = useState(false);
  const [nit, setNit] = useState('');
  const [emailEmpresa, setEmailEmpresa] = useState('');
  const [telefono, setTelefono] = useState('');
  const [ciudad, setCiudad] = useState('');
  const [departamento, setDepartamento] = useState('');

  // Redirigir si no hay token (no pasó por clerk-callback)
  if (!token) {
    navigate('/registro', { replace: true });
    return null;
  }

  const inputClass = 'cv-input';

  const handleNombreChange = (value: string) => {
    setNombreEmpresa(value);
    if (!slugManual) setSlug(slugify(value));
  };

  const validateStep1 = (): string | null => {
    if (!nombreEmpresa.trim()) return 'El nombre de la empresa es requerido';
    if (!slug.trim() || !/^[a-z0-9-]+$/.test(slug))
      return 'El slug solo puede contener letras minúsculas, números y guiones';
    if (!emailEmpresa.trim()) return 'El email de la empresa es requerido';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailEmpresa)) return 'Email de empresa inválido';
    return null;
  };

  const handleNext = () => {
    setError('');
    const err = validateStep1();
    if (err) { setError(err); return; }
    setStep(2);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { data } = await registro.registerWithClerk({
        nombre_empresa: nombreEmpresa.trim(),
        slug: slug.trim(),
        nit: nit.trim() || undefined,
        email_empresa: emailEmpresa.trim(),
        telefono: telefono.trim() || undefined,
        ciudad: ciudad.trim() || undefined,
        departamento: departamento || undefined,
      });

      // Seleccionar el tenant recién creado
      await selectTenant(data.tenant.id);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Error al registrar la empresa. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--cv-bg)] px-4 py-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="flex items-center justify-center gap-2 mb-3">
            <img src="/logo.png" alt="ChandeliERP logo" className="h-10 w-10 rounded-full object-cover" />
            <span className="font-brand text-3xl font-medium text-[var(--cv-primary)]">ChandeliERP</span>
          </div>
          <h1 className="font-brand text-2xl font-medium cv-text">Registra tu empresa</h1>
          <p className="text-sm cv-muted mt-1">14 días de prueba gratuita</p>
        </div>

        <StepIndicator current={step} />

        <form
          onSubmit={step === 2 ? handleSubmit : (e) => { e.preventDefault(); handleNext(); }}
          className="cv-card p-6 space-y-4"
        >
          {error && (
            <div className="cv-alert-error px-3 py-2 text-sm">
              {error}
            </div>
          )}

          {step === 1 && (
            <>
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Nombre de la empresa *</label>
                <input
                  type="text"
                  value={nombreEmpresa}
                  onChange={(e) => handleNombreChange(e.target.value)}
                  required
                  className={inputClass}
                  placeholder="Mi Candelería"
                />
              </div>

              <div>
                <label className="block text-sm font-medium cv-text mb-1">
                  Slug (URL) *
                  <button
                    type="button"
                    onClick={() => setSlugManual(!slugManual)}
                    className="ml-2 text-xs text-[var(--cv-primary)] hover:underline"
                  >
                    {slugManual ? 'Auto-generar' : 'Editar manual'}
                  </button>
                </label>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => { setSlugManual(true); setSlug(e.target.value.toLowerCase()); }}
                  readOnly={!slugManual}
                  required
                  className={`${inputClass} ${!slugManual ? 'opacity-75' : ''}`}
                  placeholder="mi-candeleria"
                />
                <p className="text-xs cv-muted mt-1">Solo letras minúsculas, números y guiones</p>
              </div>

              <div>
                <label className="block text-sm font-medium cv-text mb-1">NIT</label>
                <input
                  type="text"
                  value={nit}
                  onChange={(e) => setNit(e.target.value)}
                  className={inputClass}
                  placeholder="900123456-7"
                />
              </div>

              <div>
                <label className="block text-sm font-medium cv-text mb-1">Email de la empresa *</label>
                <input
                  type="email"
                  value={emailEmpresa}
                  onChange={(e) => setEmailEmpresa(e.target.value)}
                  required
                  className={inputClass}
                  placeholder="info@micandeleria.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium cv-text mb-1">Teléfono</label>
                <input
                  type="tel"
                  value={telefono}
                  onChange={(e) => setTelefono(e.target.value)}
                  className={inputClass}
                  placeholder="301 234 5678"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium cv-text mb-1">Ciudad</label>
                  <input
                    type="text"
                    value={ciudad}
                    onChange={(e) => setCiudad(e.target.value)}
                    className={inputClass}
                    placeholder="Bogotá"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium cv-text mb-1">Departamento</label>
                  <select
                    value={departamento}
                    onChange={(e) => setDepartamento(e.target.value)}
                    className={inputClass}
                  >
                    <option value="">Seleccionar...</option>
                    {DEPARTAMENTOS_CO.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>
              </div>
            </>
          )}

          {step === 2 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold cv-text">Resumen de tu empresa</h3>

              <div className="cv-elevated rounded-lg p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="cv-muted">Empresa:</span>
                  <span className="font-medium cv-text">{nombreEmpresa}</span>
                </div>
                <div className="flex justify-between">
                  <span className="cv-muted">Slug:</span>
                  <span className="font-mono cv-text">{slug}</span>
                </div>
                {nit && (
                  <div className="flex justify-between">
                    <span className="cv-muted">NIT:</span>
                    <span className="cv-text">{nit}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="cv-muted">Email empresa:</span>
                  <span className="cv-text">{emailEmpresa}</span>
                </div>
                {ciudad && (
                  <div className="flex justify-between">
                    <span className="cv-muted">Ubicación:</span>
                    <span className="cv-text">{ciudad}{departamento ? `, ${departamento}` : ''}</span>
                  </div>
                )}
              </div>

              <div className="cv-elevated border border-[var(--cv-primary)]/30 rounded-lg p-3 text-sm cv-text">
                Se creará tu empresa con 14 días de prueba gratuita. Accederás inmediatamente.
              </div>
            </div>
          )}

          <div className="flex gap-3">
            {step > 1 && (
              <button
                type="button"
                onClick={() => { setError(''); setStep(1); }}
                className="cv-btn cv-btn-ghost flex-1"
              >
                Atrás
              </button>
            )}
            <button
              type="submit"
              disabled={loading}
              className="cv-btn cv-btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Registrando...' : step === 2 ? 'Crear empresa' : 'Siguiente'}
            </button>
          </div>
        </form>

        {tenants.length > 0 && (
          <p className="text-center text-sm cv-muted mt-4">
            ¿Ya tienes una empresa?{' '}
            <Link to="/select-tenant" className="text-[var(--cv-primary)] hover:underline font-medium">
              Seleccionarla
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
