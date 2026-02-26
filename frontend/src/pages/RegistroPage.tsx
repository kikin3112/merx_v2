import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { registro } from '../api/endpoints';
import { useAuthStore } from '../stores/authStore';
import type { TenantRegisterRequest } from '../types';

type Step = 1 | 2 | 3;

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

function StepIndicator({ current }: { current: Step }) {
  const steps = [
    { num: 1, label: 'Empresa' },
    { num: 2, label: 'Administrador(a)' },
    { num: 3, label: 'Confirmar' },
  ];
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {steps.map((s, i) => (
        <div key={s.num} className="flex items-center">
          <div
            className={`flex items-center justify-center h-8 w-8 rounded-full text-sm font-semibold transition-colors ${
              s.num === current
                ? 'bg-primary-500 text-white'
                : s.num < current
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-400'
            }`}
          >
            {s.num < current ? '✓' : s.num}
          </div>
          <span className="ml-1.5 text-xs text-gray-500 hidden sm:inline">{s.label}</span>
          {i < steps.length - 1 && <div className="w-8 h-px bg-gray-200 mx-2" />}
        </div>
      ))}
    </div>
  );
}

export default function RegistroPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  const [step, setStep] = useState<Step>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 1: Empresa
  const [nombreEmpresa, setNombreEmpresa] = useState('');
  const [slug, setSlug] = useState('');
  const [slugManual, setSlugManual] = useState(false);
  const [nit, setNit] = useState('');
  const [emailEmpresa, setEmailEmpresa] = useState('');
  const [telefono, setTelefono] = useState('');
  const [ciudad, setCiudad] = useState('');
  const [departamento, setDepartamento] = useState('');

  // Step 2: Admin
  const [adminNombre, setAdminNombre] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleNombreChange = (value: string) => {
    setNombreEmpresa(value);
    if (!slugManual) {
      setSlug(slugify(value));
    }
  };

  const validateStep1 = (): string | null => {
    if (!nombreEmpresa.trim()) return 'El nombre de la empresa es requerido';
    if (!slug.trim() || !/^[a-z0-9-]+$/.test(slug)) return 'El slug solo puede contener letras minúsculas, números y guiones';
    if (!emailEmpresa.trim()) return 'El email de la empresa es requerido';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailEmpresa)) return 'Email de empresa inválido';
    return null;
  };

  const validateStep2 = (): string | null => {
    if (!adminNombre.trim()) return 'El nombre del administrador es requerido';
    if (!adminEmail.trim()) return 'El email del administrador es requerido';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(adminEmail)) return 'Email de admin inválido';
    if (adminPassword.length < 8) return 'La contraseña debe tener mínimo 8 caracteres';
    if (adminPassword !== confirmPassword) return 'Las contraseñas no coinciden';
    return null;
  };

  const handleNext = () => {
    setError('');
    if (step === 1) {
      const err = validateStep1();
      if (err) { setError(err); return; }
      setStep(2);
    } else if (step === 2) {
      const err = validateStep2();
      if (err) { setError(err); return; }
      setStep(3);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const data: TenantRegisterRequest = {
      nombre_empresa: nombreEmpresa.trim(),
      slug: slug.trim(),
      nit: nit.trim() || null,
      email_empresa: emailEmpresa.trim(),
      telefono: telefono.trim() || null,
      ciudad: ciudad.trim() || null,
      departamento: departamento || null,
      admin_nombre: adminNombre.trim(),
      admin_email: adminEmail.trim(),
      admin_password: adminPassword,
    };

    try {
      await registro.register(data);
      // Auto-login con las credenciales del admin recién creado
      const tenants = await login(adminEmail.trim(), adminPassword);
      if (tenants.length === 1) {
        navigate('/');
      } else {
        navigate('/select-tenant');
      }
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Error al registrar. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50 px-4 py-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="flex items-center justify-center gap-2 mb-3">
            <img src="/logo.png" alt="ChandeliERP logo" className="h-10 w-10 rounded-full object-cover" />
            <span className="text-3xl font-bold text-amber-500">ChandeliERP</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">¡Crea tu cuenta!</h1>
          <p className="text-sm text-gray-500 mt-1">14 días de prueba, ¡gratis!</p>
        </div>

        <StepIndicator current={step} />

        <form
          onSubmit={step === 3 ? handleSubmit : (e) => { e.preventDefault(); handleNext(); }}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4"
        >
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Step 1: Info Empresa */}
          {step === 1 && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de la empresa *</label>
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
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Slug (URL) *
                  <button
                    type="button"
                    onClick={() => setSlugManual(!slugManual)}
                    className="ml-2 text-xs text-primary-500 hover:underline"
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
                  className={`${inputClass} ${!slugManual ? 'bg-gray-50' : ''}`}
                  placeholder="mi-candeleria"
                />
                <p className="text-xs text-gray-400 mt-1">Solo letras minúsculas, números y guiones</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">NIT</label>
                <input
                  type="text"
                  value={nit}
                  onChange={(e) => setNit(e.target.value)}
                  className={inputClass}
                  placeholder="900123456-7"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email de la empresa *</label>
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
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
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ciudad</label>
                  <input
                    type="text"
                    value={ciudad}
                    onChange={(e) => setCiudad(e.target.value)}
                    className={inputClass}
                    placeholder="Bogotá"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Departamento</label>
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

          {/* Step 2: Admin */}
          {step === 2 && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre completo *</label>
                <input
                  type="text"
                  value={adminNombre}
                  onChange={(e) => setAdminNombre(e.target.value)}
                  required
                  className={inputClass}
                  placeholder="Juan Pérez"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email de acceso *</label>
                <input
                  type="email"
                  value={adminEmail}
                  onChange={(e) => setAdminEmail(e.target.value)}
                  required
                  className={inputClass}
                  placeholder="juan@micandeleria.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña *</label>
                <input
                  type="password"
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  required
                  minLength={8}
                  className={inputClass}
                  placeholder="Mínimo 8 caracteres"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirmar contraseña *</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className={inputClass}
                  placeholder="Repetir contraseña"
                />
              </div>
            </>
          )}

          {/* Step 3: Resumen */}
          {step === 3 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-900">Resumen de tu registro</h3>

              <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Empresa:</span>
                  <span className="font-medium text-gray-900">{nombreEmpresa}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Slug:</span>
                  <span className="font-mono text-gray-700">{slug}</span>
                </div>
                {nit && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">NIT:</span>
                    <span className="text-gray-700">{nit}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">Email empresa:</span>
                  <span className="text-gray-700">{emailEmpresa}</span>
                </div>
                {ciudad && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Ubicación:</span>
                    <span className="text-gray-700">{ciudad}{departamento ? `, ${departamento}` : ''}</span>
                  </div>
                )}
              </div>

              <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Admin:</span>
                  <span className="font-medium text-gray-900">{adminNombre}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Email acceso:</span>
                  <span className="text-gray-700">{adminEmail}</span>
                </div>
              </div>

              <div className="bg-primary-50 rounded-lg p-3 text-sm text-primary-700">
                Se creará tu cuenta con 14 días de prueba gratuita. Podrás acceder inmediatamente después del registro.
              </div>
            </div>
          )}

          {/* Navigation buttons */}
          <div className="flex gap-3">
            {step > 1 && (
              <button
                type="button"
                onClick={() => { setError(''); setStep((step - 1) as Step); }}
                className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Atrás
              </button>
            )}
            <button
              type="submit"
              disabled={loading}
              className="flex-1 rounded-lg bg-primary-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-600 focus:ring-2 focus:ring-primary-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Registrando...' : step === 3 ? 'Crear cuenta' : 'Siguiente'}
            </button>
          </div>
        </form>

        <p className="text-center text-sm text-gray-500 mt-4">
          ¿Ya tienes cuenta?{' '}
          <Link to="/login" className="text-primary-500 hover:text-primary-600 font-medium">
            Iniciar sesión
          </Link>
        </p>
      </div>
    </div>
  );
}
