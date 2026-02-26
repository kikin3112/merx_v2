import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportes } from '../api/endpoints';
import { formatCurrency } from '../utils/format';
import PeriodSelector, { getDefaultPeriod } from '../components/PeriodSelector';
import type { PeriodValue } from '../components/PeriodSelector';
import type {
  ComparativaMensual,
  RentabilidadCategoria,
  ProyeccionFlujoCaja,
  MargenCategoria,
} from '../types';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

type Tab = 'comparativa' | 'rentabilidad' | 'flujo' | 'margenes';

function KpiCard({ label, value, variacion }: { label: string; value: string; variacion?: number }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <p className="text-xs font-medium text-gray-500 mb-1">{label}</p>
      <p className="text-xl font-bold text-gray-900">{value}</p>
      {variacion !== undefined && (
        <p className={`text-xs font-medium mt-1 ${variacion >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {variacion >= 0 ? '+' : ''}{variacion}% vs mes anterior
        </p>
      )}
    </div>
  );
}

function ComparativaTab({ period }: { period: PeriodValue }) {
  // Use the last day of the period as reference month
  const { data, isLoading } = useQuery<ComparativaMensual>({
    queryKey: ['reportes', 'comparativa', period.fecha_fin],
    queryFn: () => reportes.comparativaMensual({ fecha_referencia: period.fecha_fin }).then(r => r.data),
  });

  if (isLoading) return <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />;
  if (!data) return <p className="text-gray-400 text-center py-8">Sin datos</p>;

  const chartData = [
    { name: 'Mes Anterior', ventas: data.mes_anterior.total_ventas, cantidad: data.mes_anterior.cantidad_ventas },
    { name: 'Mes Actual', ventas: data.mes_actual.total_ventas, cantidad: data.mes_actual.cantidad_ventas },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard
          label="Total Ventas"
          value={formatCurrency(data.mes_actual.total_ventas)}
          variacion={data.variacion.total_ventas}
        />
        <KpiCard
          label="Cantidad Ventas"
          value={String(data.mes_actual.cantidad_ventas)}
          variacion={data.variacion.cantidad_ventas}
        />
        <KpiCard
          label="Promedio Venta"
          value={formatCurrency(data.mes_actual.promedio_venta)}
          variacion={data.variacion.promedio_venta}
        />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Comparativa mensual</h3>
        <div className="text-xs text-gray-500 mb-2">
          {data.mes_actual.periodo}
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" fontSize={12} />
            <YAxis fontSize={12} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
            <Tooltip formatter={(v) => formatCurrency(Number(v ?? 0))} />
            <Legend />
            <Bar dataKey="ventas" name="Total Ventas" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function RentabilidadTab() {
  const { data, isLoading } = useQuery<RentabilidadCategoria[]>({
    queryKey: ['reportes', 'rentabilidad-categoria'],
    queryFn: () => reportes.rentabilidadCategoria().then(r => r.data),
  });

  if (isLoading) return <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />;
  if (!data?.length) return <p className="text-gray-400 text-center py-8">Sin datos</p>;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Margen por categoría (%)</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" fontSize={12} unit="%" />
            <YAxis dataKey="categoria" type="category" fontSize={11} width={100} />
            <Tooltip formatter={(v) => `${Number(v ?? 0)}%`} />
            <Bar dataKey="margen_promedio" name="Margen %" fill="#EC4899" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Desktop table */}
      <div className="hidden md:block bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-gray-500">Categoría</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Productos</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Precio prom.</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Costo prom.</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Margen (%)</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Valor invertido</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.categoria} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{row.categoria}</td>
                <td className="px-4 py-3 text-right text-gray-600">{row.cantidad_productos}</td>
                <td className="px-4 py-3 text-right text-gray-600">{formatCurrency(row.precio_promedio)}</td>
                <td className="px-4 py-3 text-right text-gray-600">{formatCurrency(row.costo_promedio)}</td>
                <td className={`px-4 py-3 text-right font-medium ${row.margen_promedio >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {row.margen_promedio}%
                </td>
                <td className="px-4 py-3 text-right text-gray-900 font-semibold">{formatCurrency(row.valor_inventario)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden space-y-3">
        {data.map((row) => (
          <div key={row.categoria} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-900">{row.categoria}</h4>
              <span className={`text-sm font-bold ${row.margen_promedio >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {row.margen_promedio}%
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div><span className="text-gray-500">Productos:</span> <span className="font-medium">{row.cantidad_productos}</span></div>
              <div><span className="text-gray-500">Precio prom:</span> <span className="font-medium">{formatCurrency(row.precio_promedio)}</span></div>
              <div><span className="text-gray-500">Costo prom:</span> <span className="font-medium">{formatCurrency(row.costo_promedio)}</span></div>
              <div><span className="text-gray-500">Valor invertido</span> <span className="font-semibold">{formatCurrency(row.valor_inventario)}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FlujoCajaTab() {
  const { data, isLoading } = useQuery<ProyeccionFlujoCaja>({
    queryKey: ['reportes', 'flujo-caja'],
    queryFn: () => reportes.proyeccionFlujoCaja(30).then(r => r.data),
  });

  if (isLoading) return <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />;
  if (!data) return <p className="text-gray-400 text-center py-8">Sin datos</p>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard label="Promedio Diario" value={formatCurrency(data.promedio_diario)} />
        <KpiCard label="Por Cobrar" value={formatCurrency(data.total_por_cobrar)} />
        <KpiCard label="Proyectado (30d)" value={formatCurrency(data.total_proyectado)} />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Proyección acumulada (30 días)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.proyeccion}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="fecha"
              fontSize={11}
              tickFormatter={(v) => v.slice(5)}
              interval={4}
            />
            <YAxis fontSize={12} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
            <Tooltip formatter={(v) => formatCurrency(Number(v ?? 0))} />
            <Line
              type="monotone"
              dataKey="acumulado"
              name="Acumulado"
              stroke="#8B5CF6"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function MargenesTab({ period }: { period: PeriodValue }) {
  const dateParams = { fecha_inicio: period.fecha_inicio, fecha_fin: period.fecha_fin };

  const { data, isLoading } = useQuery<MargenCategoria[]>({
    queryKey: ['reportes', 'margenes-categoria', dateParams],
    queryFn: () => reportes.margenesCategoria(dateParams).then(r => r.data),
  });

  if (isLoading) return <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />;
  if (!data?.length) return <p className="text-gray-400 text-center py-8">Sin datos de ventas en el periodo seleccionado</p>;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Ingresos vs costo por categoría</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="categoria" fontSize={11} />
            <YAxis fontSize={12} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
            <Tooltip formatter={(v) => formatCurrency(Number(v ?? 0))} />
            <Legend />
            <Bar dataKey="ingresos" name="Ingresos" fill="#10B981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="costo" name="Costo" fill="#EF4444" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Desktop table */}
      <div className="hidden md:block bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-gray-500">Categoría</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Ingresos</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Costo</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Margen</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Margen (%)</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Items</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.categoria} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{row.categoria}</td>
                <td className="px-4 py-3 text-right text-green-600">{formatCurrency(row.ingresos)}</td>
                <td className="px-4 py-3 text-right text-red-600">{formatCurrency(row.costo)}</td>
                <td className="px-4 py-3 text-right font-semibold text-gray-900">{formatCurrency(row.margen)}</td>
                <td className={`px-4 py-3 text-right font-medium ${row.margen_porcentaje >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {row.margen_porcentaje}%
                </td>
                <td className="px-4 py-3 text-right text-gray-600">{row.cantidad_items}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden space-y-3">
        {data.map((row) => (
          <div key={row.categoria} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-900">{row.categoria}</h4>
              <span className={`text-sm font-bold ${row.margen_porcentaje >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {row.margen_porcentaje}%
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div><span className="text-gray-500">Ingresos:</span> <span className="font-medium text-green-600">{formatCurrency(row.ingresos)}</span></div>
              <div><span className="text-gray-500">Costo:</span> <span className="font-medium text-red-600">{formatCurrency(row.costo)}</span></div>
              <div><span className="text-gray-500">Margen:</span> <span className="font-semibold">{formatCurrency(row.margen)}</span></div>
              <div><span className="text-gray-500">Items:</span> <span className="font-medium">{row.cantidad_items}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const tabs: { key: Tab; label: string }[] = [
  { key: 'comparativa', label: 'Comparativa MoM' },
  { key: 'rentabilidad', label: 'Rentabilidad' },
  { key: 'flujo', label: 'Flujo Caja' },
  { key: 'margenes', label: 'Margenes' },
];

export default function ReportesPage() {
  const [activeTab, setActiveTab] = useState<Tab>('comparativa');
  const [period, setPeriod] = useState<PeriodValue>(getDefaultPeriod);

  const showPeriodSelector = activeTab === 'comparativa' || activeTab === 'margenes';

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <h1 className="text-xl font-bold text-gray-900">Reportes avanzados</h1>
        {showPeriodSelector && (
          <PeriodSelector value={period} onChange={setPeriod} />
        )}
      </div>

      {/* Tabs */}
      <div className="overflow-x-auto pb-1 mb-6">
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-max">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {activeTab === 'comparativa' && <ComparativaTab period={period} />}
      {activeTab === 'rentabilidad' && <RentabilidadTab />}
      {activeTab === 'flujo' && <FlujoCajaTab />}
      {activeTab === 'margenes' && <MargenesTab period={period} />}
    </div>
  );
}
