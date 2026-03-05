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
import type { FacturaEvento } from '../stores/dashboardStore';
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
  Legend,
} from 'recharts';

function KPICard({ title, value, subtitle, color }: {
  title: string;
  value: string;
  subtitle: string;
  color: string;
}) {
  return (
    <div className="rounded-xl bg-white border border-gray-200 p-5">
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
      <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
    </div>
  );
}

function SSEIndicator({ connected }: { connected: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${
      connected ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'
    }`}>
      <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
      {connected ? 'En vivo' : 'Desconectado'}
    </span>
  );
}

function FacturaEventFeed({ events }: { events: FacturaEvento[] }) {
  if (events.length === 0) {
    return (
      <p className="text-xs text-gray-400 py-4 text-center">
        Sin actividad reciente. Los eventos aparecen en tiempo real.
      </p>
    );
  }
  const ESTADO_STYLES: Record<string, string> = {
    emitida: 'bg-green-100 text-green-700',
    anulada: 'bg-red-100 text-red-700',
    pagada: 'bg-blue-100 text-blue-700',
  };
  return (
    <ul className="space-y-2">
      {events.map((ev) => (
        <li key={`${ev.factura_id}-${ev.timestamp}`} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
          <div>
            <span className="text-sm font-medium text-gray-900">{ev.numero}</span>
            <span className={`ml-2 rounded-full px-2 py-0.5 text-xs font-medium ${ESTADO_STYLES[ev.estado] ?? 'bg-gray-100 text-gray-600'}`}>
              {ev.estado}
            </span>
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold text-gray-900">{formatCurrency(ev.total)}</p>
            <p className="text-xs text-gray-400">{new Date(ev.timestamp).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}</p>
          </div>
        </li>
      ))}
    </ul>
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

  // Determinar rol efectivo: impersonación > rol en tenant > rol global
  const effectiveRole = impersonation ? impersonation.rolEnTenant : (rolEnTenant ?? user?.rol);

  // Solo admin y contador pueden ver reportes detallados
  const canViewReports = effectiveRole === 'admin' || effectiveRole === 'contador';

  // SSE: tiempo real
  const { setSSEConnected, addFacturaEvento, addAlertaEvento, sseConnected, recentFacturaEvents } = useDashboardStore();
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
    enabled: canViewReports, // Solo ejecutar si tiene permisos
  });

  const { data: alertas } = useQuery<AlertaStock[]>({
    queryKey: ['alertas-stock'],
    queryFn: () => inventarios.alertas().then((r) => r.data),
  });

  const { data: ventasDiarias } = useQuery<VentaDiaria[]>({
    queryKey: ['ventas-diarias', dateParams],
    queryFn: () => reportes.ventasDiarias(dateParams).then((r) => r.data),
    enabled: canViewReports, // Solo ejecutar si tiene permisos
  });

  const { data: topProductos } = useQuery<ProductoMasVendido[]>({
    queryKey: ['productos-mas-vendidos', dateParams],
    queryFn: () => reportes.productosMasVendidos({ limite: 5, ...dateParams }).then((r) => r.data),
    enabled: canViewReports, // Solo ejecutar si tiene permisos
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
        <div className="h-8 w-48 bg-gray-200 rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-gray-200 rounded-xl" />
          ))}
        </div>
        <div className="h-64 bg-gray-200 rounded-xl" />
      </div>
    );
  }

  // Mensaje para usuarios sin permisos de reportes
  if (!canViewReports) {
    return (
      <div>
        <h1 className="text-xl font-bold text-gray-900 mb-6">Dashboard</h1>

        <div className="rounded-xl bg-blue-50 border border-blue-200 p-6 text-center">
          <svg className="w-16 h-16 mx-auto text-blue-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Bienvenido, {user?.nombre}</h2>
          <p className="text-gray-600 mb-4">
            Tu rol de <span className="font-medium text-blue-600">{effectiveRole}</span> te permite gestionar operaciones del día a día.
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Los reportes detallados están disponibles para roles de Admin y Contador.
            <br />
            Usa el menú lateral para acceder a tus funciones.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {effectiveRole === 'vendedor' && (
              <>
                <a href="/pos" className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors">
                  Ir al POS
                </a>
                <a href="/ventas" className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-200 transition-colors">
                  Ver ventas
                </a>
              </>
            )}
            {effectiveRole === 'operador' && (
              <>
                <a href="/productos" className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors">
                  Gestionar productos
                </a>
                <a href="/inventario" className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-200 transition-colors">
                  Ver inventario
                </a>
              </>
            )}
          </div>
        </div>

        {/* Alertas de stock - todos pueden verlas */}
        {alertas && alertas.length > 0 && (
          <div className="mt-6">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">⚠️ Alertas de stock</h2>
            <div className="space-y-2">
              {alertas.slice(0, 5).map((alerta) => (
                <div
                  key={alerta.producto_id}
                  className="flex items-center justify-between rounded-lg bg-red-50 border border-red-200 p-3"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{alerta.nombre}</p>
                    <p className="text-xs text-gray-500">
                      Stock: {alerta.stock_actual} / Mínimo: {alerta.stock_minimo}
                    </p>
                  </div>
                  <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700">
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
          <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
          <SSEIndicator connected={sseConnected} />
        </div>
        <PeriodSelector value={period} onChange={setPeriod} />
      </div>

      <NextActionsPanel />

      {/* KPI Cards - Row 1 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <KPICard
          title="Ventas en periodo"
          value={formatCurrency(kpis?.total_ventas ?? 0)}
          subtitle={`${kpis?.cantidad_ventas ?? 0} ventas`}
          color="text-primary-600"
        />
        <KPICard
          title="Ventas hoy"
          value={formatCurrency(kpis?.ventas_hoy ?? 0)}
          subtitle={`${kpis?.cantidad_hoy ?? 0} ventas`}
          color="text-green-600"
        />
        <KPICard
          title="Promedio por venta"
          value={formatCurrency(kpis?.promedio_venta ?? 0)}
          subtitle={`${kpis?.cantidad_ventas ?? 0} ventas en periodo`}
          color="text-blue-600"
        />
        <KPICard
          title="Alertas stock"
          value={String(kpis?.alertas_stock_bajo ?? 0)}
          subtitle="productos bajo minimo"
          color={kpis?.alertas_stock_bajo ? 'text-red-600' : 'text-gray-600'}
        />
      </div>

      {/* KPI Cards - Row 2 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KPICard
          title="Ventas últ. 30 días"
          value={formatCurrency(kpis?.ventas_mes ?? 0)}
          subtitle={`${kpis?.cantidad_mes ?? 0} ventas`}
          color="text-secondary-600"
        />
        <KPICard
          title="Facturas pendientes"
          value={formatCurrency(kpis?.facturas_pendientes ?? 0)}
          subtitle={`${kpis?.cantidad_facturas_pendientes ?? 0} facturas por cobrar`}
          color={kpis?.cantidad_facturas_pendientes ? 'text-orange-600' : 'text-gray-600'}
        />
      </div>

      {/* Chart: Ventas Diarias */}
      {ventasDiarias && ventasDiarias.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Ventas diarias ({period.label})</h2>
          <div className="h-52 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={ventasDiarias}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="fecha"
                  tickFormatter={formatShortDate}
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  width={55}
                />
                <Tooltip
                  formatter={(value: number | undefined) => [formatTooltipValue(value ?? 0), 'Ventas']}
                  labelFormatter={(label: unknown) => formatShortDate(String(label))}
                  contentStyle={{ fontSize: 13, borderRadius: 8, border: '1px solid #e5e7eb' }}
                />
                <Line
                  type="monotone"
                  dataKey="total"
                  stroke="#EC4899"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Gastos vs Ingresos */}
      {canViewReports && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-1">Ingresos vs gastos ({period.label})</h2>
          {gastosLoading ? (
            <div className="h-48 flex items-center justify-center text-sm text-gray-400">Cargando...</div>
          ) : gastosError ? (
            <div className="h-48 flex items-center justify-center text-sm text-red-400">No se pudieron cargar los datos financieros.</div>
          ) : gastosVsIngresos && (gastosVsIngresos.ingresos > 0 || gastosVsIngresos.gastos > 0) ? (
            <>
              <p className="text-xs text-gray-400 mb-4">
                Margen: <span className={gastosVsIngresos.margen >= 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                  {formatTooltipValue(gastosVsIngresos.margen)} ({gastosVsIngresos.margen_porcentaje}%)
                </span>
              </p>
              <div className="flex flex-col sm:flex-row items-center gap-6">
                <div className="h-48 w-full sm:w-64 shrink-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Ingresos', value: gastosVsIngresos.ingresos },
                          { name: 'Gastos', value: gastosVsIngresos.gastos },
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={52}
                        outerRadius={80}
                        dataKey="value"
                        startAngle={90}
                        endAngle={-270}
                      >
                        <Cell fill="#C17B2B" />
                        <Cell fill="#EF4444" />
                      </Pie>
                      <Tooltip
                        formatter={(value: number | undefined) => [formatTooltipValue(value ?? 0), '']}
                        contentStyle={{ fontSize: 13, borderRadius: 8, border: '1px solid #e5e7eb' }}
                      />
                      <Legend
                        iconType="circle"
                        iconSize={8}
                        formatter={(value: string) => <span style={{ fontSize: 12, color: '#374151' }}>{value}</span>}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex-1 space-y-3 w-full">
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <div className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full bg-[#C17B2B]" />
                      <span className="text-sm text-gray-600">Ingresos</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">{formatTooltipValue(gastosVsIngresos.ingresos)}</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <div className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full bg-red-500" />
                      <span className="text-sm text-gray-600">Gastos</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">{formatTooltipValue(gastosVsIngresos.gastos)}</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm font-medium text-gray-700">Margen neto</span>
                    <span className={`text-sm font-bold ${gastosVsIngresos.margen >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatTooltipValue(gastosVsIngresos.margen)}
                    </span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="h-48 flex items-center justify-center text-sm text-gray-400">Sin movimientos en este período.</div>
          )}
        </div>
      )}

      {/* Two columns: Top Productos + Top Clientes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Top Productos */}
        {topProductos && topProductos.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Top productos ({period.label})</h2>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topProductos} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                  <XAxis
                    type="number"
                    tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                  />
                  <YAxis
                    type="category"
                    dataKey="nombre"
                    width={100}
                    tick={{ fontSize: 11, fill: '#374151' }}
                  />
                  <Tooltip
                    formatter={(value: number | undefined) => [formatTooltipValue(value ?? 0), 'Ingresos']}
                    contentStyle={{ fontSize: 13, borderRadius: 8, border: '1px solid #e5e7eb' }}
                  />
                  <Bar dataKey="total_ingresos" fill="#8B5CF6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 space-y-1.5">
              {topProductos.map((p, i) => (
                <div key={p.producto_id} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">
                    <span className="font-medium text-gray-400 mr-2">{i + 1}.</span>
                    {p.nombre}
                  </span>
                  <span className="text-gray-900 font-medium">{formatNumber(p.total_cantidad)} uds</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top Clientes */}
        {topClientes && topClientes.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Top clientes ({period.label})</h2>
            <div className="space-y-3">
              {topClientes.map((c, i) => (
                <div key={c.tercero_id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-secondary-100 flex items-center justify-center">
                      <span className="text-secondary-700 text-xs font-semibold">{i + 1}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{c.nombre}</p>
                      <p className="text-xs text-gray-500">{c.cantidad_ventas} compras</p>
                    </div>
                  </div>
                  <p className="text-sm font-semibold text-gray-900">{formatCurrency(c.total_ventas)}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Alertas de stock */}
      {alertas && alertas.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Alertas de stock bajo</h2>
          <div className="space-y-2">
            {alertas.slice(0, 8).map((a) => (
              <div key={a.producto_id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <div>
                  <p className="text-sm font-medium text-gray-900">{a.nombre}</p>
                  <p className="text-xs text-gray-500">{a.codigo}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-red-600">{a.stock_actual}</p>
                  <p className="text-xs text-gray-400">min: {a.stock_minimo}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feed SSE de eventos en tiempo real */}
      <div className="mt-6 bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-900">Actividad en vivo</h2>
          <SSEIndicator connected={sseConnected} />
        </div>
        <FacturaEventFeed events={recentFacturaEvents} />
      </div>
    </div>
  );
}
