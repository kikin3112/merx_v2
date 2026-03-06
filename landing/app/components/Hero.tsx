import { TypewriterText } from './TypewriterText';

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://app.chandelierp.com';

export function Hero() {
  return (
    <section className="relative overflow-hidden" style={{ background: 'var(--bg)' }}>
      {/* Glow orbs */}
      <div
        className="absolute top-0 right-0 w-[600px] h-[600px] rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(255,155,101,0.12) 0%, transparent 70%)',
          transform: 'translate(30%, -30%)',
        }}
      />
      <div
        className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(255,230,128,0.07) 0%, transparent 70%)',
          transform: 'translate(-30%, 30%)',
        }}
      />

      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-28 sm:py-36 lg:py-44">
        <div className="text-center">
          {/* Eyebrow mono label */}
          <p
            className="inline-block text-xs font-semibold tracking-[0.18em] uppercase mb-8 px-3 py-1 rounded"
            style={{
              fontFamily: 'var(--font-mono)',
              color: 'var(--primary)',
              background: 'var(--primary-dim)',
            }}
          >
            Para emprendedor@s solitari@s
          </p>

          {/* Heading */}
          <h1
            className="text-5xl sm:text-6xl lg:text-7xl leading-[1.05] mb-6 animate-fade-up"
            style={{ fontFamily: 'var(--font-brand)', fontWeight: 500, color: 'var(--text)' }}
          >
            Tu negocio,
            <TypewriterText />
          </h1>

          {/* Subheading */}
          <p
            className="text-lg sm:text-xl leading-relaxed max-w-2xl mx-auto mb-10 animate-fade-up delay-1"
            style={{ color: 'var(--text-muted)' }}
          >
            Inventario, recetas de producción, POS, facturación y contabilidad.
            Todo conectado. Sin caos.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-up delay-2">
            <a
              href={`${APP_URL}/registro`}
              className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 rounded-xl font-bold text-base transition-all hover:-translate-y-0.5"
              style={{
                background: 'var(--primary)',
                color: '#1A1A1A',
                boxShadow: '0 4px 24px rgba(255,155,101,0.25)',
              }}
            >
              Probar gratis 14 días →
            </a>
            <a
              href="#video"
              className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 rounded-xl font-semibold text-base transition-all hover:opacity-80"
              style={{
                border: '1px solid rgba(255,255,255,0.14)',
                color: 'var(--text-muted)',
                background: 'var(--surface)',
              }}
            >
              Ver demo
            </a>
          </div>

          {/* Trust */}
          <p
            className="mt-6 text-xs animate-fade-up delay-3"
            style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
          >
            Sin tarjeta de crédito · Sin compromiso · Cancela cuando quieras
          </p>

          {/* Stats strip */}
          <div
            className="mt-20 grid grid-cols-3 gap-px rounded-2xl overflow-hidden animate-fade-up delay-4"
            style={{ background: 'rgba(255,255,255,0.06)' }}
          >
            {[
              { val: '14 días', label: 'prueba gratis' },
              { val: '$5.000', label: 'desde / mes COP' },
              { val: '6+', label: 'módulos integrados' },
            ].map(({ val, label }) => (
              <div
                key={label}
                className="py-6 px-4"
                style={{ background: 'var(--surface)' }}
              >
                <p
                  className="text-2xl font-bold mb-1"
                  style={{ fontFamily: 'var(--font-brand)', color: 'var(--primary)' }}
                >
                  {val}
                </p>
                <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
