import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ventas } from '../api/endpoints';
import { formatCurrency, formatDate, formatDateTime, statusColor } from '../utils/format';
import type { Venta } from '../types';
import DocumentForm from '../components/DocumentForm';
import type { DocumentFormData } from '../components/DocumentForm';
import DocumentDetail from '../components/DocumentDetail';
import DataCard from '../components/ui/DataCard';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';

// ── Analytics helpers ──────────────────────────────────────────────
const DIAS_SEMANA = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

const FRANJAS = [
  { key: 'madrugada', label: 'Madrugada', range: '0–5h',  horas: [0,1,2,3,4,5] },
  { key: 'mañana',    label: 'Mañana',    range: '6–11h', horas: [6,7,8,9,10,11] },
  { key: 'mediodía',  label: 'Mediodía',  range: '12–14h',horas: [12,13,14] },
  { key: 'tarde',     label: 'Tarde',     range: '15–18h',horas: [15,16,17,18] },
  { key: 'noche',     label: 'Noche',     range: '19–23h',horas: [19,20,21,22,23] },
];

function useVentasAnalytics(data: Venta[] | undefined) {
  return useMemo(() => {
    if (!data || data.length === 0) return null;

    const activas = data.filter((v) => v.estado !== 'ANULADA');
    const facturadas = data.filter((v) => v.estado === 'FACTURADA');

    const tasaFacturacion = data.length > 0
      ? Math.round((facturadas.length / data.length) * 100)
      : 0;

    const ticketPromedio = activas.length > 0
      ? activas.reduce((s, v) => s + Number(v.total_venta), 0) / activas.length
      : 0;

    // ① Por día de semana (Lun–Dom), usando fecha_venta
    const diaMap = Array(7).fill(null).map((_, i) => ({
      dia: DIAS_SEMANA[i], total: 0, count: 0,
    }));
    for (const v of activas) {
      const dow = new Date(v.fecha_venta + 'T12:00:00').getDay();
      diaMap[dow].total += Number(v.total_venta);
      diaMap[dow].count++;
    }
    // Ordenar Lun(1)→Dom(0)
    const porDia = [...diaMap.slice(1), diaMap[0]];
    const mejorDia = [...porDia].sort((a, b) => b.total - a.total)[0]?.dia ?? '—';

    // ② Por franja horaria, usando created_at (tiene timestamp real)
    const franjaMap: Record<string, { label: string; range: string; total: number; count: number }> = {};
    for (const f of FRANJAS) franjaMap[f.key] = { label: f.label, range: f.range, total: 0, count: 0 };
    for (const v of activas) {
      const hora = new Date(v.created_at).getHours();
      const franja = FRANJAS.find((f) => f.horas.includes(hora));
      if (franja) {
        franjaMap[franja.key].total += Number(v.total_venta);
        franjaMap[franja.key].count++;
      }
    }
    const porFranja = FRANJAS.map((f) => franjaMap[f.key]);
    const mejorFranja = [...porFranja].sort((a, b) => b.total - a.total)[0]?.label ?? '—';

    // ③ Por categoría de producto (de detalles)
    const catMap: Record<string, { nombre: string; total: number; cantidad: number }> = {};
    for (const v of activas) {
      for (const d of v.detalles) {
        const cat = d.categoria || 'Sin categoría';
        if (!catMap[cat]) catMap[cat] = { nombre: cat, total: 0, cantidad: 0 };
        catMap[cat].total += Number(d.total_linea);
        catMap[cat].cantidad += Number(d.cantidad);
      }
    }
    const porCategoria = Object.values(catMap)
      .sort((a, b) => b.total - a.total)
      .slice(0, 6);
    const topCategoria = porCategoria[0]?.nombre ?? '—';

    return {
      tasaFacturacion, ticketPromedio,
      mejorDia, mejorFranja, topCategoria,
      porDia, porFranja, porCategoria,
    };
  }, [data]);
}

export default function VentasPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<Venta | null>(null);
  const [filtroEstado, setFiltroEstado] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(true);

  const showError = (err: any, fallback: string) => {
    const msg = err?.response?.data?.detail || fallback;
    setError(msg);
    setTimeout(() => setError(null), 6000);
  };

  // Carga TODAS las ventas para analytics; el filtro actúa solo en la tabla
  const { data: allData, isLoading } = useQuery<Venta[]>({
    queryKey: ['ventas'],
    queryFn: () => ventas.list().then((r) => r.data),
  });

  const data = filtroEstado
    ? allData?.filter((v) => v.estado === filtroEstado)
    : allData;

  const analytics = useVentasAnalytics(allData);

  const crearMutation = useMutation({
    mutationFn: (formData: DocumentFormData) =>
      ventas.create({
        tercero_id: formData.tercero_id,
        fecha_venta: formData.fecha,
        observaciones: formData.observaciones || null,
        descuento_global: formData.descuento_global || 0,
        detalles: formData.detalles.map((d) => ({
          producto_id: d.producto_id,
          cantidad: d.cantidad,
          precio_unitario: d.precio_unitario,
          descuento: d.descuento,
          porcentaje_iva: d.porcentaje_iva,
        })),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ventas'] });
      setShowForm(false);
      setSelectedDoc(null);
    },
    onError: (err: any) => showError(err, 'Error al crear venta'),
  });

  const confirmarMutation = useMutation({
    mutationFn: (id: string) => ventas.confirmar(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ventas'] }),
    onError: (err: any) => showError(err, 'Error al confirmar venta'),
  });

  const anularMutation = useMutation({
    mutationFn: (id: string) => ventas.anular(id, 'Anulada desde frontend'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ventas'] }),
    onError: (err: any) => showError(err, 'Error al anular venta'),
  });

  const facturarMutation = useMutation({
    mutationFn: (id: string) => ventas.facturar(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ventas'] });
      queryClient.invalidateQueries({ queryKey: ['facturas'] });
    },
    onError: (err: any) => showError(err, 'Error al facturar venta'),
  });

  const registrarEnvioMutation = useMutation({
    mutationFn: ({ id, canal, destinatario }: { id: string; canal: string; destinatario: string }) =>
      ventas.registrarEnvio(id, { canal, destinatario }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ventas'] }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h1 className="font-brand text-xl font-medium cv-text">Ventas</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAnalytics((v) => !v)}
            className="cv-icon-btn p-2 text-xs font-mono hidden sm:flex items-center gap-1.5"
            title="Mostrar/ocultar análisis"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Análisis
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="cv-btn cv-btn-primary text-sm"
          >
            + Nueva venta
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 cv-alert-error px-4 py-3 flex items-center justify-between">
          <p className="text-sm">{error}</p>
          <button onClick={() => setError(null)} className="cv-icon-btn ml-3 p-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* ── Analytics ──────────────────────────────── */}
      {showAnalytics && analytics && (
        <div className="mb-6 space-y-4">
          {/* KPI strip: 3 insights clave */}
          <div className="grid grid-cols-3 gap-3">
            <div className="cv-card p-4">
              <p className="text-[10px] font-mono uppercase tracking-wider cv-muted mb-1">Ticket promedio</p>
              <p className="text-xl font-bold cv-primary">{formatCurrency(analytics.ticketPromedio)}</p>
              <p className="text-[10px] cv-muted mt-0.5">{analytics.tasaFacturacion}% facturadas</p>
            </div>
            <div className="cv-card p-4">
              <p className="text-[10px] font-mono uppercase tracking-wider cv-muted mb-1">Mejor día</p>
              <p className="text-xl font-bold cv-text">{analytics.mejorDia}</p>
              <p className="text-[10px] cv-muted mt-0.5">mayor ingreso semanal</p>
            </div>
            <div className="cv-card p-4">
              <p className="text-[10px] font-mono uppercase tracking-wider cv-muted mb-1">Hora pico</p>
              <p className="text-xl font-bold cv-text">{analytics.mejorFranja}</p>
              <p className="text-[10px] cv-muted mt-0.5">franja con más ventas</p>
            </div>
          </div>

          {/* Charts — 3 gráficos de nicho */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

            {/* ① Días de la semana */}
            <div className="cv-card p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-xs font-semibold cv-text">¿Qué días vendes más?</p>
                  <p className="text-[10px] cv-muted mt-0.5">Ingresos por día de la semana</p>
                </div>
              </div>
              <div className="h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.porDia} margin={{ left: -20, right: 4, top: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--cv-border)" vertical={false} />
                    <XAxis dataKey="dia" tick={{ fontSize: 10, fill: 'var(--cv-muted)' }} />
                    <YAxis tick={{ fontSize: 9, fill: 'var(--cv-muted)' }} tickFormatter={(v: number) => `${(v/1e6).toFixed(0)}M`} />
                    <Tooltip
                      formatter={(v: number | undefined) => [formatCurrency(v ?? 0), 'Ingresos']}
                      labelFormatter={(l: unknown) => `${l}`}
                      contentStyle={{ fontSize: 11, borderRadius: 8, backgroundColor: 'var(--cv-surface)', border: '1px solid var(--cv-border-mid)', color: 'var(--cv-text)' }}
                    />
                    <Bar dataKey="total" radius={[3, 3, 0, 0]}>
                      {analytics.porDia.map((d, i) => {
                        const maxTotal = Math.max(...analytics.porDia.map((x) => x.total));
                        return (
                          <Cell
                            key={i}
                            fill={d.total === maxTotal ? 'var(--cv-primary)' : 'var(--cv-elevated)'}
                          />
                        );
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* ② Franja horaria */}
            <div className="cv-card p-4">
              <div className="mb-3">
                <p className="text-xs font-semibold cv-text">¿A qué hora compran?</p>
                <p className="text-[10px] cv-muted mt-0.5">Ingresos por franja del día</p>
              </div>
              <div className="h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.porFranja} margin={{ left: -20, right: 4, top: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--cv-border)" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 9, fill: 'var(--cv-muted)' }} />
                    <YAxis tick={{ fontSize: 9, fill: 'var(--cv-muted)' }} tickFormatter={(v: number) => `${(v/1e6).toFixed(0)}M`} />
                    <Tooltip
                      formatter={(v: number | undefined, _: unknown, props: { payload?: { range?: string } }) => [
                        formatCurrency(v ?? 0),
                        props.payload?.range ?? '',
                      ]}
                      contentStyle={{ fontSize: 11, borderRadius: 8, backgroundColor: 'var(--cv-surface)', border: '1px solid var(--cv-border-mid)', color: 'var(--cv-text)' }}
                    />
                    <Bar dataKey="total" radius={[3, 3, 0, 0]}>
                      {analytics.porFranja.map((f, i) => {
                        const maxTotal = Math.max(...analytics.porFranja.map((x) => x.total));
                        return (
                          <Cell
                            key={i}
                            fill={f.total === maxTotal ? 'var(--cv-accent)' : 'var(--cv-elevated)'}
                          />
                        );
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* ③ Por categoría — proxy de nicho */}
            <div className="cv-card p-4">
              <div className="mb-3">
                <p className="text-xs font-semibold cv-text">¿Qué categorías lideran?</p>
                <p className="text-[10px] cv-muted mt-0.5">Ingresos por categoría de producto</p>
              </div>
              {analytics.porCategoria.length > 0 ? (
                <div className="space-y-2">
                  {analytics.porCategoria.map((cat, i) => {
                    const maxTotal = analytics.porCategoria[0].total;
                    const pct = maxTotal > 0 ? (cat.total / maxTotal) * 100 : 0;
                    return (
                      <div key={cat.nombre}>
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="text-[10px] cv-text truncate max-w-[120px]">{cat.nombre}</span>
                          <span className="text-[10px] font-mono cv-muted">{formatCurrency(cat.total)}</span>
                        </div>
                        <div className="h-1.5 rounded-full" style={{ backgroundColor: 'var(--cv-elevated)' }}>
                          <div
                            className="h-1.5 rounded-full transition-all duration-500"
                            style={{
                              width: `${pct}%`,
                              backgroundColor: i === 0 ? 'var(--cv-positive)' : 'var(--cv-primary)',
                              opacity: 1 - i * 0.12,
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs cv-muted text-center py-6">Los detalles de venta no tienen categoría asignada</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
        {['', 'PENDIENTE', 'CONFIRMADA', 'FACTURADA', 'ANULADA'].map((estado) => (
          <button
            key={estado}
            onClick={() => setFiltroEstado(estado)}
            className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              filtroEstado === estado
                ? 'cv-badge-primary'
                : 'cv-badge-neutral'
            }`}
          >
            {estado || 'Todas'}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 cv-elevated rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block cv-card overflow-hidden">
            <table className="w-full text-sm">
              <thead className="cv-table-header">
                <tr>
                  <th className="text-left">Numero</th>
                  <th className="text-left">Fecha</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-500">Total</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-500">Estado</th>
                  <th className="text-left">Creado Por</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-500">Acciones</th>
                </tr>
              </thead>
              <tbody className="cv-table-body">
                {data?.map((v) => (
                  <tr key={v.id} onClick={() => setSelectedDoc(v)} className="cursor-pointer">
                    <td className="font-mono text-xs font-medium">{v.numero_venta}</td>
                    <td className="cv-muted">{formatDate(v.fecha_venta)}</td>
                    <td className="text-right font-semibold">{formatCurrency(v.total_venta)}</td>
                    <td className="text-center">
                      <span className={`cv-badge ${statusColor(v.estado)}`}>{v.estado}</span>
                    </td>
                    <td>
                      <div className="text-sm">{v.created_by?.nombre || 'Sistema'}</div>
                      <div className="text-xs cv-muted">{formatDateTime(v.created_at)}</div>
                    </td>
                    <td className="text-center" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-center gap-1">
                        {v.estado === 'PENDIENTE' && (
                          <>
                            <button
                              onClick={() => confirmarMutation.mutate(v.id)}
                              disabled={confirmarMutation.isPending}
                              className="rounded px-2 py-1 text-xs font-medium bg-[var(--cv-primary-dim)] text-[var(--cv-primary)] hover:opacity-80 transition-opacity"
                            >
                              Confirmar
                            </button>
                            <button
                              onClick={() => facturarMutation.mutate(v.id)}
                              disabled={facturarMutation.isPending}
                              className="rounded px-2 py-1 text-xs font-medium bg-[var(--cv-positive-dim)] text-[var(--cv-positive)] hover:opacity-80 transition-opacity"
                            >
                              {facturarMutation.isPending ? 'Facturando...' : 'Facturar'}
                            </button>
                          </>
                        )}
                        {v.estado === 'CONFIRMADA' && (
                          <button
                            onClick={() => facturarMutation.mutate(v.id)}
                            disabled={facturarMutation.isPending}
                            className="rounded px-2 py-1 text-xs font-medium bg-[var(--cv-positive-dim)] text-[var(--cv-positive)] hover:opacity-80 transition-opacity"
                          >
                            {facturarMutation.isPending ? 'Facturando...' : 'Facturar'}
                          </button>
                        )}
                        {v.estado === 'FACTURADA' && v.url_pdf && (
                          <>
                            <a
                              href={v.url_pdf}
                              target="_blank"
                              rel="noreferrer"
                              className="rounded px-2 py-1 text-xs font-medium bg-[var(--cv-primary-dim)] text-[var(--cv-primary)] hover:opacity-80 transition-opacity"
                            >
                              PDF
                            </a>
                            <a
                              href={`https://wa.me/${v.tercero?.telefono?.replace(/\D/g, '') || ''}?text=${encodeURIComponent(`Hola! Te comparto tu factura ${v.numero_venta}: ${v.url_pdf}`)}`}
                              target="_blank"
                              rel="noreferrer"
                              onClick={() => registrarEnvioMutation.mutate({ id: v.id, canal: 'whatsapp', destinatario: v.tercero?.telefono || 'desconocido' })}
                              className="rounded px-2 py-1 text-xs font-medium bg-[var(--cv-positive-dim)] text-[var(--cv-positive)] hover:opacity-80 transition-opacity"
                            >
                              WA
                            </a>
                            <a
                              href={`mailto:${v.tercero?.email || ''}?subject=${encodeURIComponent(`Factura ${v.numero_venta}`)}&body=${encodeURIComponent(`Hola! Adjunto tu factura ${v.numero_venta}.\n\nDescargar: ${v.url_pdf}`)}`}
                              onClick={() => registrarEnvioMutation.mutate({ id: v.id, canal: 'email', destinatario: v.tercero?.email || 'desconocido' })}
                              className="rounded px-2 py-1 text-xs font-medium bg-[var(--cv-elevated)] cv-muted hover:opacity-80 transition-opacity"
                            >
                              Email
                            </a>
                          </>
                        )}
                        {v.estado !== 'ANULADA' && v.estado !== 'FACTURADA' && (
                          <button
                            onClick={() => {
                              if (confirm('Anular esta venta?')) {
                                anularMutation.mutate(v.id);
                              }
                            }}
                            disabled={anularMutation.isPending}
                            className="rounded px-2 py-1 text-xs font-medium bg-[var(--cv-negative-dim)] text-[var(--cv-negative)] hover:opacity-80 transition-opacity"
                          >
                            Anular
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data?.length === 0 && (
              <div className="text-center py-12 cv-muted">
                <p className="text-lg mb-2">Sin ventas</p>
                <p className="text-sm">Crea tu primera venta</p>
              </div>
            )}
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {data?.map((v) => (
              <DataCard
                key={v.id}
                title={v.numero_venta}
                subtitle={formatDate(v.fecha_venta)}
                badge={<span className={`cv-badge ${statusColor(v.estado)}`}>{v.estado}</span>}
                fields={[
                  { label: 'Total', value: formatCurrency(v.total_venta) },
                  { label: 'Creado por', value: v.created_by?.nombre || 'Sistema' },
                ]}
                onClick={() => setSelectedDoc(v)}
                actions={
                  <>
                    {v.estado === 'PENDIENTE' && (
                      <>
                        <button
                          onClick={() => confirmarMutation.mutate(v.id)}
                          disabled={confirmarMutation.isPending}
                          className="rounded-lg px-3 py-1.5 text-xs font-medium bg-[var(--cv-primary-dim)] text-[var(--cv-primary)]"
                        >
                          Confirmar
                        </button>
                        <button
                          onClick={() => facturarMutation.mutate(v.id)}
                          disabled={facturarMutation.isPending}
                          className="rounded-lg px-3 py-1.5 text-xs font-medium bg-[var(--cv-positive-dim)] text-[var(--cv-positive)]"
                        >
                          Facturar
                        </button>
                      </>
                    )}
                    {v.estado === 'CONFIRMADA' && (
                      <button
                        onClick={() => facturarMutation.mutate(v.id)}
                        disabled={facturarMutation.isPending}
                        className="rounded-lg px-3 py-1.5 text-xs font-medium bg-[var(--cv-positive-dim)] text-[var(--cv-positive)]"
                      >
                        Facturar
                      </button>
                    )}
                    {v.estado === 'FACTURADA' && v.url_pdf && (
                      <>
                        <a
                          href={v.url_pdf}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-lg px-3 py-1.5 text-xs font-medium bg-[var(--cv-primary-dim)] text-[var(--cv-primary)]"
                        >
                          PDF
                        </a>
                        <a
                          href={`https://wa.me/${v.tercero?.telefono?.replace(/\D/g, '') || ''}?text=${encodeURIComponent(`Hola! Te comparto tu factura ${v.numero_venta}: ${v.url_pdf}`)}`}
                          target="_blank"
                          rel="noreferrer"
                          onClick={() => registrarEnvioMutation.mutate({ id: v.id, canal: 'whatsapp', destinatario: v.tercero?.telefono || 'desconocido' })}
                          className="rounded-lg px-3 py-1.5 text-xs font-medium bg-[var(--cv-positive-dim)] text-[var(--cv-positive)]"
                        >
                          WA
                        </a>
                      </>
                    )}
                    {v.estado !== 'ANULADA' && v.estado !== 'FACTURADA' && (
                      <button
                        onClick={() => { if (confirm('Anular esta venta?')) anularMutation.mutate(v.id); }}
                        disabled={anularMutation.isPending}
                        className="rounded-lg px-3 py-1.5 text-xs font-medium bg-[var(--cv-negative-dim)] text-[var(--cv-negative)]"
                      >
                        Anular
                      </button>
                    )}
                  </>
                }
              />
            ))}
            {data?.length === 0 && (
              <div className="text-center py-12 cv-muted">
                <p className="text-lg mb-2">Sin ventas</p>
                <p className="text-sm">Crea tu primera venta</p>
              </div>
            )}
          </div>
        </>
      )}

      <DocumentForm
        tipo="venta"
        open={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={(data) => crearMutation.mutate(data)}
        loading={crearMutation.isPending}
      />

      <DocumentDetail
        tipo="venta"
        doc={selectedDoc}
        open={!!selectedDoc}
        onClose={() => setSelectedDoc(null)}
        onUpdated={() => {
          queryClient.invalidateQueries({ queryKey: ['ventas'] });
          setSelectedDoc(null);
        }}
      />
    </div>
  );
}
