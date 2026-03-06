import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportes, inventarios } from '../api/endpoints';
import { formatCurrency, formatNumber } from '../utils/format';
import PeriodSelector, { getDefaultPeriod } from '../components/PeriodSelector';
import type { PeriodValue } from '../components/PeriodSelector';
import type { DashboardKPIs, AlertaStock, VentaDiaria, ProductoMasVendido, TopCliente, GastosVsIngresos } from '../types';
import { useAuthStore } from '../stores/authStore';
import { useSSE } from '../hooks/useSSE';
import { useDashboardStore } from '../stores/dashboardStore';
import { useOnboarding } from '../hooks/useOnboarding';
import OnboardingWizard from '../components/onboarding/OnboardingWizard';
import NextActionsPanel from '../components/dashboard/NextActionsPanel';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

function KPICard({ title, value, subtitle, color }: {
  title: string;
  value: string;
  subtitle: string;
  color: string;
}) {
  return (
    <div className="cv-card p-5">
      <p className="text-sm font-medium cv-muted">{title}</p>
      <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
      <p className="text-xs cv-muted mt-1">{subtitle}</p>
    </div>
  );
}

function SSEIndicator({ connected }: { connected: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${
      connected ? 'cv-badge-positive' : 'cv-badge-neutral'
    }`}>
      <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-[var(--cv-positive)] animate-pulse' : 'bg-[var(--cv-muted)]'}`} />
      {connected ? 'En vivo' : 'Desconectado'}
    </span>
  );
}


function formatShortDate(fecha: string): string {
  const d = new Date(fecha + 'T00:00:00');
  return d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' });
}

function formatTooltipValue(value: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export default function DashboardPage() {
  const [period, setPeriod] = useState<PeriodValue>(getDefaultPeriod);
  const { user, impersonation, rolEnTenant } = useAuthStore();
  const onboarding = useOnboarding();

  const effectiveRole = impersonation ? impersonation.rolEnTenant : (rolEnTenant ?? user?.rol);
  const canViewReports = effectiveRole === 'admin' || effectiveRole === 'contador';

  const { setSSEConnected, addFacturaEvento, addAlertaEvento, sseConnected } = useDashboardStore();
  useSSE({
    onConnect: () => setSSEConnected(true),
    onDisconnect: () => setSSEConnected(false),
    onEvent: (type, data) => {
      if (type === 'factura_estado_cambiado') addFacturaEvento(data as Parameters<typeof addFacturaEvento>[0]);
      if (type === 'alerta_stock') addAlertaEvento(data as Parameters<typeof addAlertaEvento>[0]);
    },
  });

  const dateParams = { fecha_inicio: period.fecha_inicio, fecha_fin: period.fecha_fin };

  const { data: kpis, isLoading: kpisLoading } = useQuery<DashboardKPIs>({
    queryKey: ['dashboard-kpis', dateParams],
    queryFn: () => reportes.dashboard(dateParams).then((r) => r.data),
    enabled: canViewReports,
  });

  const { data: alertas } = useQuery<AlertaStock[]>({
    queryKey: ['alertas-stock'],
    queryFn: () => inventarios.alertas().then((r) => r.data),
  });

  const { data: ventasDiarias } = useQuery<VentaDiaria[]>({
    queryKey: ['ventas-diarias', dateParams],
    queryFn: () => reportes.ventasDiarias(dateParams).then((r) => r.data),
    enabled: canViewReports,
  });

  const { data: topProductos } = useQuery<ProductoMasVendido[]>({
    queryKey: ['productos-mas-vendidos', dateParams],
    queryFn: () => reportes.productosMasVendidos({ limite: 5, ...dateParams }).then((r) => r.data),
    enabled: canViewReports,
  });

  const { data: topClientes } = useQuery<TopCliente[]>({
    queryKey: ['top-clientes', dateParams],
    queryFn: () => reportes.topClientes({ limite: 5, ...dateParams }).then((r) => r.data),
    enabled: canViewReports,
  });

  const { data: gastosVsIngresos, isLoading: gastosLoading, isError: gastosError } = useQuery<GastosVsIngresos>({
    queryKey: ['gastos-vs-ingresos', dateParams],
    queryFn: () => reportes.gastosVsIngresos(dateParams).then((r) => r.data),
    enabled: canViewReports,
  });

  if (kpisLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 w-48 cv-elevated rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 cv-elevated rounded-xl" />
          ))}
        </div>
        <div className="h-64 cv-elevated rounded-xl" />
      </div>
    );
  }

  if (!canViewReports) {
    return (
      <div>
        <h1 className="font-brand text-xl font-medium cv-text mb-6">Dashboard</h1>

        <div className="cv-card cv-alert-accent p-6 text-center">
          <svg className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--cv-accent)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-lg font-semibold cv-text mb-2">Bienvenido, {user?.nombre}</h2>
          <p className="cv-muted mb-4">
            Tu rol de <span className="font-medium cv-primary">{effectiveRole}</span> te permite gestionar operaciones del día a día.
          </p>
          <p className="text-sm cv-muted mb-6">
            Los reportes detallados están disponibles para roles de Admin y Contador.
            <br />
            Usa el menú lateral para acceder a tus funciones.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {effectiveRole === 'vendedor' && (
              <>
                <a href="/pos" className="cv-btn cv-btn-primary">
                  Ir al POS
                </a>
                <a href="/ventas" className="cv-btn cv-btn-secondary">
                  Ver ventas
                </a>
              </>
            )}
            {effectiveRole === 'operador' && (
              <>
                <a href="/productos" className="cv-btn cv-btn-primary">
                  Gestionar productos
                </a>
                <a href="/inventario" className="cv-btn cv-btn-secondary">
                  Ver inventario
                </a>
              </>
            )}
          </div>
        </div>

        {alertas && alertas.length > 0 && (
          <div className="mt-6">
            <h2 className="text-sm font-semibold cv-text mb-3">⚠️ Alertas de stock</h2>
            <div className="space-y-2">
              {alertas.slice(0, 5).map((alerta) => (
                <div
                  key={alerta.producto_id}
                  className="flex items-center justify-between rounded-lg cv-alert-error p-3"
                >
                  <div>
                    <p className="text-sm font-medium cv-text">{alerta.nombre}</p>
                    <p className="text-xs cv-muted">
                      Stock: {alerta.stock_actual} / Mínimo: {alerta.stock_minimo}
                    </p>
                  </div>
                  <span className="cv-badge cv-badge-negative">
                    Bajo stock
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      {onboarding.shouldShow && (
        <OnboardingWizard
          currentStep={onboarding.currentStep}
          completedSteps={onboarding.completedSteps}
          totalSteps={onboarding.totalSteps}
          onCompleteStep={onboarding.completeStep}
          onDismiss={onboarding.dismiss}
        />
      )}

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <h1 className="font-brand text-xl font-medium cv-text">Dashboard</h1>
          <SSEIndicator connected={sseConnected} />
        </div>
        <PeriodSelector value={period} onChange={setPeriod} />
      </div>

      <NextActionsPanel />

      {/* KPI Cards + Ingresos vs Gastos — desktop: 2/3 + 1/3 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
        {/* KPI 2×3 */}
        <div className="lg:col-span-2 grid grid-cols-2 gap-4">
          <KPICard
            title="Ventas en periodo"
            value={formatCurrency(kpis?.total_ventas ?? 0)}
            subtitle={`${kpis?.cantidad_ventas ?? 0} ventas`}
            color="cv-primary"
          />
          <KPICard
            title="Ventas hoy"
            value={formatCurrency(kpis?.ventas_hoy ?? 0)}
            subtitle={`${kpis?.cantidad_hoy ?? 0} ventas`}
            color="text-[var(--cv-positive)]"
          />
          <KPICard
            title="Promedio por venta"
            value={formatCurrency(kpis?.promedio_venta ?? 0)}
            subtitle={`${kpis?.cantidad_ventas ?? 0} ventas en periodo`}
            color="text-[var(--cv-accent)]"
          />
          <KPICard
            title="Alertas stock"
            value={String(kpis?.alertas_stock_bajo ?? 0)}
            subtitle="productos bajo minimo"
            color={kpis?.alertas_stock_bajo ? 'text-[var(--cv-negative)]' : 'cv-muted'}
          />
          <KPICard
            title="Ventas últ. 30 días"
            value={formatCurrency(kpis?.ventas_mes ?? 0)}
            subtitle={`${kpis?.cantidad_mes ?? 0} ventas`}
            color="cv-text"
          />
          <KPICard
            title="Facturas pendientes"
            value={formatCurrency(kpis?.facturas_pendientes ?? 0)}
            subtitle={`${kpis?.cantidad_facturas_pendientes ?? 0} facturas por cobrar`}
            color={kpis?.cantidad_facturas_pendientes ? 'text-[var(--cv-primary)]' : 'cv-muted'}
          />
        </div>

        {/* Ingresos vs Gastos — columna derecha */}
        {canViewReports && (
          <div className="cv-card p-5 flex flex-col">
            <h2 className="text-sm font-semibold cv-text mb-1">Ingresos vs gastos</h2>
            {gastosLoading ? (
              <div className="flex-1 flex items-center justify-center text-sm cv-muted">Cargando...</div>
            ) : gastosError ? (
              <div className="flex-1 flex items-center justify-center text-sm text-[var(--cv-negative)]">Sin datos financieros.</div>
            ) : gastosVsIngresos && (gastosVsIngresos.ingresos > 0 || gastosVsIngresos.gastos > 0) ? (
              <>
                <div className="h-44">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Ingresos', value: gastosVsIngresos.ingresos },
                          { name: 'Gastos', value: gastosVsIngresos.gastos },
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={48}
                        outerRadius={72}
                        dataKey="value"
                        startAngle={90}
                        endAngle={-270}
                      >
                        <Cell fill="#FF9B65" />
                        <Cell fill="#FF7A7A" />
                      </Pie>
                      <Tooltip
                        formatter={(value: number | undefined) => [formatTooltipValue(value ?? 0), '']}
                        contentStyle={{ fontSize: 12, borderRadius: 8, backgroundColor: 'var(--cv-surface)', border: '1px solid var(--cv-border-mid)', color: 'var(--cv-text)' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-2 mt-2">
                  <div className="flex items-center justify-between py-1.5 border-b cv-divider">
                    <div className="flex items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ backgroundColor: '#FF9B65' }} />
                      <span className="text-xs cv-muted">Ingresos</span>
                    </div>
                    <span className="text-xs font-semibold cv-text">{formatTooltipValue(gastosVsIngresos.ingresos)}</span>
                  </div>
                  <div className="flex items-center justify-between py-1.5 border-b cv-divider">
                    <div className="flex items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ backgroundColor: '#FF7A7A' }} />
                      <span className="text-xs cv-muted">Gastos</span>
                    </div>
                    <span className="text-xs font-semibold cv-text">{formatTooltipValue(gastosVsIngresos.gastos)}</span>
                  </div>
                  <div className="flex items-center justify-between py-1.5">
                    <span className="text-xs font-medium cv-text">Margen neto</span>
                    <span className={`text-xs font-bold ${gastosVsIngresos.margen >= 0 ? 'text-[var(--cv-positive)]' : 'text-[var(--cv-negative)]'}`}>
                      {formatTooltipValue(gastosVsIngresos.margen)}
                    </span>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-sm cv-muted">Sin movimientos en este período.</div>
            )}
          </div>
        )}
      </div>

      {/* Chart: Ventas Diarias */}
      {ventasDiarias && ventasDiarias.length > 0 && (() => {
        const TICK_COUNT = 7;
        const n = ventasDiarias.length;
        const evenTicks = Array.from({ length: Math.min(TICK_COUNT, n) }, (_, i) =>
          ventasDiarias[Math.round(i * (n - 1) / (Math.min(TICK_COUNT, n) - 1))]?.fecha
        ).filter(Boolean);
        return (
        <div className="cv-card p-5 mb-6">
          <h2 className="text-sm font-semibold cv-text mb-4">Ventas diarias ({period.label})</h2>
          <div className="h-52 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={ventasDiarias}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--cv-border-mid)" />
                <XAxis
                  dataKey="fecha"
                  tickFormatter={formatShortDate}
                  tick={{ fontSize: 11, fill: 'var(--cv-muted)' }}
                  ticks={evenTicks}
                />
                <YAxis
                  tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                  tick={{ fontSize: 11, fill: 'var(--cv-muted)' }}
                  width={55}
                />
                <Tooltip
                  formatter={(value: number | undefined) => [formatTooltipValue(value ?? 0), 'Ventas']}
                  labelFormatter={(label: unknown) => formatShortDate(String(label))}
                  contentStyle={{ fontSize: 13, borderRadius: 8, backgroundColor: 'var(--cv-surface)', border: '1px solid var(--cv-border-mid)', color: 'var(--cv-text)' }}
                />
                <Line
                  type="monotone"
                  dataKey="total"
                  stroke="var(--cv-primary)"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        );
      })()}


      {/* Two columns: Top Productos + Top Clientes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {topProductos && topProductos.length > 0 && (
          <div className="cv-card p-5">
            <h2 className="text-sm font-semibold cv-text mb-4">Top productos ({period.label})</h2>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topProductos} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--cv-border)" horizontal={false} />
                  <XAxis
                    type="number"
                    tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                    tick={{ fontSize: 11, fill: 'var(--cv-muted)' }}
                  />
                  <YAxis
                    type="category"
                    dataKey="nombre"
                    width={100}
                    tick={{ fontSize: 11, fill: 'var(--cv-text)' }}
                  />
                  <Tooltip
                    formatter={(value: number | undefined) => [formatTooltipValue(value ?? 0), 'Ingresos']}
                    contentStyle={{ fontSize: 13, borderRadius: 8, backgroundColor: 'var(--cv-surface)', border: '1px solid var(--cv-border-mid)', color: 'var(--cv-text)' }}
                  />
                  <Bar dataKey="total_ingresos" fill="var(--cv-accent)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 space-y-1.5">
              {topProductos.map((p, i) => (
                <div key={p.producto_id} className="flex items-center justify-between text-sm">
                  <span className="cv-muted">
                    <span className="font-medium mr-2">{i + 1}.</span>
                    {p.nombre}
                  </span>
                  <span className="cv-text font-medium">{formatNumber(p.total_cantidad)} uds</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {topClientes && topClientes.length > 0 && (
          <div className="cv-card p-5">
            <h2 className="text-sm font-semibold cv-text mb-4">Top clientes ({period.label})</h2>
            <div className="space-y-3">
              {topClientes.map((c, i) => (
                <div key={c.tercero_id} className="flex items-center justify-between py-2 border-b cv-divider last:border-0">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full cv-elevated flex items-center justify-center">
                      <span className="cv-primary text-xs font-semibold">{i + 1}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium cv-text">{c.nombre}</p>
                      <p className="text-xs cv-muted">{c.cantidad_ventas} compras</p>
                    </div>
                  </div>
                  <p className="text-sm font-semibold cv-text">{formatCurrency(c.total_ventas)}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Alertas de stock */}
      {alertas && alertas.length > 0 && (
        <div className="cv-card p-5">
          <h2 className="text-sm font-semibold cv-text mb-3">Alertas de stock bajo</h2>
          <div className="space-y-2">
            {alertas.slice(0, 8).map((a) => (
              <div key={a.producto_id} className="flex items-center justify-between py-2 border-b cv-divider last:border-0">
                <div>
                  <p className="text-sm font-medium cv-text">{a.nombre}</p>
                  <p className="text-xs cv-muted">{a.codigo}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-[var(--cv-negative)]">{a.stock_actual}</p>
                  <p className="text-xs cv-muted">min: {a.stock_minimo}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
