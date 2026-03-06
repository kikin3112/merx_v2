interface CalificacionPublica {
  estrellas: number;
  titulo: string | null;
  comentario: string | null;
  nombre_empresa: string;
  created_at: string;
}

async function getTestimonios(): Promise<CalificacionPublica[]> {
  const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return [];

  try {
    const res = await fetch(`${apiUrl}/calificaciones/publicas?limit=6`, {
      next: { revalidate: 3600 }, // Revalidar cada hora
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

function Stars({ count }: { count: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} style={{ color: n <= count ? 'var(--accent)' : 'var(--border-mid)', fontSize: '13px' }}>
          ★
        </span>
      ))}
    </div>
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('es-CO', { month: 'long', year: 'numeric' });
}

export async function Testimonials() {
  const testimonios = await getTestimonios();
  if (testimonios.length === 0) return null;

  return (
    <section id="testimonios" className="py-20 sm:py-28" style={{ background: 'var(--bg)' }}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Encabezado */}
        <div className="text-center mb-16">
          <p
            className="text-xs font-semibold tracking-[0.18em] uppercase mb-4"
            style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary)' }}
          >
            Clientes
          </p>
          <h2
            className="text-3xl sm:text-4xl leading-tight"
            style={{ fontFamily: 'var(--font-brand)', fontWeight: 500, color: 'var(--text)' }}
          >
            Lo que dicen nuestros clientes
          </h2>
          <p className="mt-4 text-base max-w-2xl mx-auto" style={{ color: 'var(--text-muted)' }}>
            Negocios reales usando chandelierp todos los días.
          </p>
        </div>

        {/* Grid de testimonios */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {testimonios.map((t, i) => (
            <div
              key={i}
              className="rounded-xl p-6 border flex flex-col gap-3"
              style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
            >
              <Stars count={t.estrellas} />

              {t.titulo && (
                <p className="font-semibold text-sm leading-snug" style={{ color: 'var(--text)' }}>
                  {t.titulo}
                </p>
              )}

              {t.comentario && (
                <p className="text-sm leading-relaxed flex-1" style={{ color: 'var(--text-muted)' }}>
                  &ldquo;{t.comentario}&rdquo;
                </p>
              )}

              <div
                className="pt-3 border-t flex items-center justify-between"
                style={{ borderColor: 'var(--border)' }}
              >
                <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                  {t.nombre_empresa}
                </span>
                <span className="text-xs" style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {formatDate(t.created_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
