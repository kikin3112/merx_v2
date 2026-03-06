import { CheckIcon } from '@heroicons/react/24/outline';

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://app.chandelierp.com';

const includedFeatures = [
  '2 usuarios',
  'Todos los módulos',
  'Soporte WhatsApp',
  '14 días gratis',
];

export function Pricing() {
  return (
    <section id="precios" className="py-20 sm:py-28" style={{ background: 'var(--surface)' }}>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center mb-16">
          <p
            className="text-xs font-semibold tracking-[0.18em] uppercase mb-4"
            style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary)' }}
          >
            Precios
          </p>
          <h2
            className="text-3xl sm:text-4xl leading-tight"
            style={{ fontFamily: 'var(--font-brand)', fontWeight: 500, color: 'var(--text)' }}
          >
            Precios transparentes
          </h2>
          <p className="mt-4 text-base" style={{ color: 'var(--text-muted)' }}>
            Un solo plan con todo incluido. Bueno, bonito y barato.
          </p>
        </div>

        {/* Pricing card */}
        <div className="max-w-lg mx-auto">
          <div
            className="relative rounded-2xl p-8 sm:p-10"
            style={{
              background: 'var(--bg)',
              border: '1px solid rgba(255,155,101,0.3)',
              boxShadow: '0 0 60px rgba(255,155,101,0.08)',
            }}
          >
            {/* Badge */}
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
              <span
                className="inline-flex items-center px-4 py-1 rounded-full text-xs font-bold tracking-wide"
                style={{ background: 'var(--primary)', color: '#1A1A1A', fontFamily: 'var(--font-mono)' }}
              >
                TODO INCLUIDO
              </span>
            </div>

            {/* Plan name */}
            <div className="text-center pt-2">
              <h3
                className="text-xl font-medium"
                style={{ fontFamily: 'var(--font-brand)', color: 'var(--text)' }}
              >
                3B — Bueno, bonito y barato
              </h3>

              {/* Price */}
              <div className="mt-6 flex items-baseline justify-center gap-2">
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Desde</span>
                <span
                  className="text-3xl sm:text-4xl md:text-5xl font-bold"
                  style={{ fontFamily: 'var(--font-brand)', color: 'var(--primary)' }}
                >
                  $15.000
                </span>
                <span className="text-base" style={{ color: 'var(--text-muted)' }}>COP/mes</span>
              </div>
            </div>

            {/* Features list */}
            <ul className="mt-8 space-y-3">
              {includedFeatures.map((feature) => (
                <li key={feature} className="flex items-center gap-3">
                  <span style={{ color: 'var(--positive)' }}>✓</span>
                  <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{feature}</span>
                </li>
              ))}
            </ul>

            {/* CTA */}
            <a
              href={`${APP_URL}/registro`}
              className="mt-8 block w-full text-center px-8 py-4 rounded-xl font-bold text-base transition-all hover:-translate-y-0.5"
              style={{
                background: 'var(--primary)',
                color: '#1A1A1A',
                boxShadow: '0 4px 24px rgba(255,155,101,0.25)',
              }}
            >
              Comenzar prueba gratuita
            </a>

            {/* Subtext */}
            <p
              className="mt-4 text-center text-xs"
              style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
            >
              Sin tarjeta de crédito · Sin compromiso
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
