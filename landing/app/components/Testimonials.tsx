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
        <span key={n} className={n <= count ? 'text-amber-400' : 'text-gray-300'}>
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
    <section id="testimonios" className="py-20 sm:py-28 bg-[#faf7f2]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Encabezado */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Lo que dicen nuestros clientes
          </h2>
          <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto">
            Empresas reales usando ChandeliERP todos los días.
          </p>
        </div>

        {/* Grid de testimonios */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonios.map((t, i) => (
            <div
              key={i}
              className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex flex-col gap-3"
            >
              <Stars count={t.estrellas} />

              {t.titulo && (
                <p className="font-semibold text-gray-900 text-base leading-snug">{t.titulo}</p>
              )}

              {t.comentario && (
                <p className="text-gray-600 text-sm leading-relaxed flex-1">&ldquo;{t.comentario}&rdquo;</p>
              )}

              <div className="pt-2 border-t border-gray-100 flex items-center justify-between">
                <span className="text-sm font-medium text-gray-800">{t.nombre_empresa}</span>
                <span className="text-xs text-gray-400">{formatDate(t.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
