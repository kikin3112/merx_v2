import {
  BeakerIcon,
  CubeIcon,
  ShoppingCartIcon,
  ChartBarIcon,
  UserGroupIcon,
  BanknotesIcon,
} from '@heroicons/react/24/outline';

interface Feature {
  name: string;
  description: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

const features: Feature[] = [
  {
    name: 'Producción y BOM',
    description: 'Define fórmulas de producción con ingredientes y costos automáticos.',
    icon: BeakerIcon,
  },
  {
    name: 'Inventario Inteligente',
    description: 'Control de stock en tiempo real con alertas automáticas.',
    icon: CubeIcon,
  },
  {
    name: 'Punto de Venta (POS)',
    description: 'Vende rápido con interfaz optimizada para solopreneurs.',
    icon: ShoppingCartIcon,
  },
  {
    name: 'Dashboard en Vivo',
    description: 'KPIs y métricas actualizadas en tiempo real via SSE.',
    icon: ChartBarIcon,
  },
  {
    name: 'CRM Integrado',
    description: 'Pipeline de ventas conectado directamente a tu facturación.',
    icon: UserGroupIcon,
  },
  {
    name: 'Cartera y Contabilidad',
    description: 'Cuentas por cobrar, asientos contables y balance de prueba.',
    icon: BanknotesIcon,
  },
];

export function Features() {
  return (
    <section id="funciones" className="py-20 sm:py-28 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Todo lo que necesitas para tu negocio
          </h2>
          <p className="mt-4 text-lg text-gray-500">
            Módulos diseñados para el flujo de trabajo real de solopreneurs — desde la producción hasta la venta.
          </p>
        </div>

        {/* Feature grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.name}
                className="group relative p-8 rounded-2xl border border-gray-100 bg-white hover:border-amber-200 hover:shadow-lg transition-all duration-300"
              >
                {/* Icon */}
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-amber-100 group-hover:bg-amber-200 transition-colors">
                  <Icon className="h-6 w-6 text-amber-600" />
                </div>

                {/* Content */}
                <h3 className="mt-5 text-lg font-bold text-gray-900">
                  {feature.name}
                </h3>
                <p className="mt-2 text-gray-500 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
