import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportes, inventarios } from '../api/endpoints';
import { formatCurrency, formatNumber } from '../utils/format';
import PeriodSelector, { getDefaultPeriod } from '../components/PeriodSelector';
import type { PeriodValue } from '../components/PeriodSelector';
import type { DashboardKPIs, AlertaStock, VentaDiaria, ProductoMasVendido, TopCliente } from '../types';
import { useAuthStore } from '../stores/authStore';
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
  const { user, impersonation } = useAuthStore();

  // Determinar rol efectivo
  const effectiveRole = impersonation ? impersonation.rolEnTenant : user?.rol;

  // Solo admin y contador pueden ver reportes detallados
  const canViewReports = effectiveRole === 'admin' || effectiveRole === 'contador';

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
    enabled: canViewReports, // Solo ejecutar si tiene permisos
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
                  Ver Ventas
                </a>
              </>
            )}
            {effectiveRole === 'operador' && (
              <>
                <a href="/productos" className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors">
                  Gestionar Productos
                </a>
                <a href="/inventario" className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-200 transition-colors">
                  Ver Inventario
                </a>
              </>
            )}
          </div>
        </div>

        {/* Alertas de stock - todos pueden verlas */}
        {alertas && alertas.length > 0 && (
          <div className="mt-6">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">⚠️ Alertas de Stock</h2>
            <div className="space-y-2">
              {alertas.slice(0, 5).map((alerta) => (
                <div
                  key={alerta.producto_id}
                  className="flex items-center justify-between rounded-lg bg-red-50 border border-red-200 p-3"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{alerta.nombre_producto}</p>
                    <p className="text-xs text-gray-500">
                      Stock: {alerta.cantidad_disponible} / Mínimo: {alerta.stock_minimo}
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
        <PeriodSelector value={period} onChange={setPeriod} />
      </div>

      {/* KPI Cards - Row 1 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <KPICard
          title="Ventas en Periodo"
          value={formatCurrency(kpis?.total_ventas ?? 0)}
          subtitle={`${kpis?.cantidad_ventas ?? 0} ventas`}
          color="text-primary-600"
        />
        <KPICard
          title="Ventas Hoy"
          value={formatCurrency(kpis?.ventas_hoy ?? 0)}
          subtitle={`${kpis?.cantidad_hoy ?? 0} ventas`}
          color="text-green-600"
        />
        <KPICard
          title="Promedio por Venta"
          value={formatCurrency(kpis?.promedio_venta ?? 0)}
          subtitle={`${kpis?.cantidad_ventas ?? 0} ventas en periodo`}
          color="text-blue-600"
        />
        <KPICard
          title="Alertas Stock"
          value={String(kpis?.alertas_stock_bajo ?? 0)}
          subtitle="productos bajo minimo"
          color={kpis?.alertas_stock_bajo ? 'text-red-600' : 'text-gray-600'}
        />
      </div>

      {/* KPI Cards - Row 2 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KPICard
          title="Ventas Ult. 30 dias"
          value={formatCurrency(kpis?.ventas_mes ?? 0)}
          subtitle={`${kpis?.cantidad_mes ?? 0} ventas`}
          color="text-secondary-600"
        />
        <KPICard
          title="Facturas Pendientes"
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

      {/* Two columns: Top Productos + Top Clientes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Top Productos */}
        {topProductos && topProductos.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Top Productos ({period.label})</h2>
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
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Top Clientes ({period.label})</h2>
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
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Alertas de Stock Bajo</h2>
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
    </div>
  );
}
