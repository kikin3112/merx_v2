export function VideoEmbed() {
  return (
    <section id="video" className="py-20 sm:py-28 bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Mira ChandeliERP en acción
          </h2>
          <p className="mt-4 text-lg text-gray-500">
            Conoce la plataforma en menos de 5 minutos.
          </p>
        </div>

        {/* Video container */}
        <div className="relative w-full rounded-2xl overflow-hidden shadow-2xl border border-gray-200">
          <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
            <iframe
              className="absolute inset-0 w-full h-full"
              src="https://www.youtube.com/embed/dQw4w9WgXcQ"
              title="Demo de ChandeliERP"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </div>
      </div>
    </section>
  );
}
