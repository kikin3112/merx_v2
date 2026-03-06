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
    <section id="funciones" className="py-20 sm:py-28" style={{ background: 'var(--surface)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p
            className="text-xs font-semibold tracking-[0.18em] uppercase mb-4"
            style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary)' }}
          >
            Módulos
          </p>
          <h2
            className="text-3xl sm:text-4xl leading-tight"
            style={{ fontFamily: 'var(--font-brand)', fontWeight: 500, color: 'var(--text)' }}
          >
            Todo lo que necesitas para tu negocio
          </h2>
          <p className="mt-4 text-base" style={{ color: 'var(--text-muted)' }}>
            Diseñado para el flujo de trabajo real de solopreneurs — desde la producción hasta la cobranza.
          </p>
        </div>

        {/* Feature grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.name}
                className="feature-card group p-7 rounded-2xl border"
                style={{
                  background: 'var(--bg)',
                  borderColor: 'var(--border)',
                }}
              >
                {/* Icon */}
                <div
                  className="inline-flex items-center justify-center w-10 h-10 rounded-lg mb-5"
                  style={{ background: 'var(--primary-dim)' }}
                >
                  <Icon className="h-5 w-5" style={{ color: 'var(--primary)' }} />
                </div>

                {/* Content */}
                <h3
                  className="text-base font-semibold mb-2"
                  style={{ color: 'var(--text)' }}
                >
                  {feature.name}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
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
