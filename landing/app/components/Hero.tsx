const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://app.chandelierp.com';

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-pink-50 via-purple-50 to-white" />
      <div className="absolute top-0 right-0 w-96 h-96 bg-pink-200/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-purple-200/30 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32 lg:py-40">
        <div className="max-w-3xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center px-4 py-1.5 rounded-full bg-pink-100 text-pink-700 text-sm font-medium mb-8">
            Hecho para candelerias colombianas
          </div>

          {/* Heading */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-gray-900 leading-tight">
            El ERP diseñado para{' '}
            <span className="bg-gradient-to-r from-pink-500 to-purple-600 bg-clip-text text-transparent">
              tu candelería
            </span>
          </h1>

          {/* Subheading */}
          <p className="mt-6 text-lg sm:text-xl text-gray-600 leading-relaxed max-w-2xl mx-auto">
            Gestiona inventario, produce con recetas, vende en POS y lleva la contabilidad.
            Todo en un solo lugar.
          </p>

          {/* CTAs */}
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href={`${APP_URL}/registro`}
              className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 rounded-xl bg-gradient-to-r from-pink-500 to-purple-600 text-white font-bold text-lg hover:from-pink-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            >
              Probar gratis 14 días
            </a>
            <a
              href="#video"
              className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 rounded-xl border-2 border-gray-200 text-gray-700 font-semibold text-lg hover:border-pink-300 hover:text-pink-600 transition-all"
            >
              Ver demo
            </a>
          </div>

          {/* Trust line */}
          <p className="mt-6 text-sm text-gray-400">
            Sin tarjeta de crédito. Sin compromiso. Cancela cuando quieras.
          </p>
        </div>
      </div>
    </section>
  );
}
