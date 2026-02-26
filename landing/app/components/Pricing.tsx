import { CheckIcon } from '@heroicons/react/24/outline';

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://app.chandelierp.com';

const includedFeatures = [
  'Hasta 3 usuarios',
  'Todos los módulos',
  'Soporte WhatsApp',
  '14 días gratis',
];

export function Pricing() {
  return (
    <section id="precios" className="py-20 sm:py-28 bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Precios transparentes
          </h2>
          <p className="mt-4 text-lg text-gray-500">
            Un solo plan con todo incluido. Paga lo que puedas.
          </p>
        </div>

        {/* Pricing card */}
        <div className="max-w-lg mx-auto">
          <div className="relative rounded-3xl border-2 border-amber-300 bg-white p-8 sm:p-10 shadow-xl">
            {/* Badge */}
            <div className="absolute -top-4 left-1/2 -translate-x-1/2">
              <span className="inline-flex items-center px-4 py-1 rounded-full bg-amber-500 text-white text-sm font-bold shadow-md">
                Recomendado
              </span>
            </div>

            {/* Plan name */}
            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900">
                Plan Único — Paga lo que puedas
              </h3>

              {/* Price */}
              <div className="mt-6 flex items-baseline justify-center gap-2">
                <span className="text-sm text-gray-500">Desde</span>
                <span className="text-5xl font-extrabold text-gray-900">$29.800</span>
                <span className="text-lg text-gray-500">COP/mes</span>
              </div>
            </div>

            {/* Features list */}
            <ul className="mt-8 space-y-4">
              {includedFeatures.map((feature) => (
                <li key={feature} className="flex items-center gap-3">
                  <CheckIcon className="h-5 w-5 text-amber-500 shrink-0" />
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>

            {/* CTA */}
            <a
              href={`${APP_URL}/registro`}
              className="mt-8 block w-full text-center px-8 py-4 rounded-xl bg-amber-500 text-white font-bold text-lg hover:bg-amber-600 transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            >
              Comenzar prueba gratuita
            </a>

            {/* Subtext */}
            <p className="mt-4 text-center text-sm text-gray-400">
              Sin tarjeta de crédito. Sin compromiso.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
