import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { comercial, cotizaciones, ventas } from '../api/endpoints';
import { formatCurrency, formatDate } from '../utils/format';
import type { Cotizacion, Venta } from '../types';
import DocumentForm from '../components/DocumentForm';
import type { DocumentFormData } from '../components/DocumentForm';
import DocumentDetail from '../components/DocumentDetail';

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────
interface PipelineData {
  cotizaciones: Cotizacion[];
  ventas_pendientes: Venta[];
  ventas_confirmadas: Venta[];
  facturas_recientes: Venta[];
  resumen: {
    total_cotizado: string;
    por_cobrar: string;
    facturado_mes: string;
  };
}

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────
const ESTADO_COLORS: Record<string, string> = {
  VIGENTE: 'bg-blue-50 text-blue-700',
  PENDIENTE: 'bg-yellow-50 text-yellow-700',
  CONFIRMADA: 'bg-purple-50 text-purple-700',
  FACTURADA: 'bg-green-50 text-green-700',
  ACEPTADA: 'bg-teal-50 text-teal-700',
  RECHAZADA: 'bg-red-50 text-red-700',
  ANULADA: 'bg-gray-100 text-gray-500',
};

function EstadoBadge({ estado }: { estado: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${ESTADO_COLORS[estado] || 'bg-gray-100 text-gray-600'}`}>
      {estado}
    </span>
  );
}

// ─────────────────────────────────────────────
// Document card
// ─────────────────────────────────────────────
interface DocCardProps {
  numero: string;
  estado: string;
  total: number | string;
  fecha: string;
  onClick: () => void;
  action?: React.ReactNode;
}

function DocCard({ numero, estado, total, fecha, onClick, action }: DocCardProps) {
  return (
    <div
      className="bg-white rounded-xl border border-gray-100 p-3 shadow-sm hover:shadow-md transition-shadow cursor-pointer group"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <p className="text-sm font-semibold text-gray-900 group-hover:text-primary-700 transition-colors">
          {numero}
        </p>
        <EstadoBadge estado={estado} />
      </div>
      <p className="text-base font-bold text-gray-900 mb-1">{formatCurrency(Number(total))}</p>
      <p className="text-xs text-gray-400 mb-3">{formatDate(fecha)}</p>
      {action && (
        <div onClick={(e) => e.stopPropagation()}>
          {action}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Pipeline column
// ─────────────────────────────────────────────
interface ColumnProps {
  title: string;
  count: number;
  total: number;
  colorClass: string;
  children: React.ReactNode;
}

function PipelineColumn({ title, count, total, colorClass, children }: ColumnProps) {
  return (
    <div className="flex-1 min-w-[220px] max-w-xs">
      <div className={`flex items-center justify-between px-3 py-2 rounded-xl mb-3 ${colorClass}`}>
        <span className="text-sm font-semibold">{title}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs opacity-70">{formatCurrency(total)}</span>
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-white/50 text-xs font-bold">
            {count}
          </span>
        </div>
      </div>
      <div className="space-y-2">
        {children}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────
export default function ComercialPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState<'venta' | 'cotizacion' | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<Venta | Cotizacion | null>(null);
  const [docType, setDocType] = useState<'venta' | 'cotizacion' | null>(null);
  const [error, setError] = useState<string | null>(null);

  const showError = (err: unknown, fallback: string) => {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || fallback;
    setError(msg);
    setTimeout(() => setError(null), 6000);
  };

  // ─── Data ────────────────────────────────
  const { data: pipeline, isLoading } = useQuery<PipelineData>({
    queryKey: ['comercial-pipeline'],
    queryFn: () => comercial.pipeline().then((r) => r.data),
    refetchInterval: 60_000,
  });

  // ─── Mutations ───────────────────────────
  const crearVentaMutation = useMutation({
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
          descuento: d.descuento || 0,
          porcentaje_iva: d.porcentaje_iva || 0,
        })),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comercial-pipeline'] });
      setShowForm(null);
    },
    onError: (err) => showError(err, 'Error al crear venta'),
  });

  const crearCotizacionMutation = useMutation({
    mutationFn: (formData: DocumentFormData) =>
      cotizaciones.create({
        tercero_id: formData.tercero_id,
        fecha_cotizacion: formData.fecha,
        fecha_vencimiento: formData.fecha_vencimiento || formData.fecha,
        observaciones: formData.observaciones || null,
        descuento_global: formData.descuento_global || 0,
        detalles: formData.detalles.map((d) => ({
          producto_id: d.producto_id,
          cantidad: d.cantidad,
          precio_unitario: d.precio_unitario,
          descuento: d.descuento || 0,
          porcentaje_iva: d.porcentaje_iva || 0,
        })),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comercial-pipeline'] });
      setShowForm(null);
    },
    onError: (err) => showError(err, 'Error al crear cotización'),
  });

  const convertirMutation = useMutation({
    mutationFn: (id: string) => cotizaciones.convertir(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comercial-pipeline'] });
      setSelectedDoc(null);
    },
    onError: (err) => showError(err, 'Error al convertir cotización'),
  });

  const renovarMutation = useMutation({
    mutationFn: (id: string) => cotizaciones.renovar(id, 15),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['comercial-pipeline'] }),
    onError: (err) => showError(err, 'Error al renovar cotización'),
  });

  const rechazarMutation = useMutation({
    mutationFn: (id: string) => cotizaciones.rechazar(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['comercial-pipeline'] }),
    onError: (err) => showError(err, 'Error al rechazar cotización'),
  });

  const facturarMutation = useMutation({
    mutationFn: (id: string) => ventas.facturar(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comercial-pipeline'] });
      setSelectedDoc(null);
    },
    onError: (err) => showError(err, 'Error al facturar'),
  });

  // ─── Derived data ─────────────────────────
  const cotizacionesList = pipeline?.cotizaciones ?? [];
  const ventasPendientes = pipeline?.ventas_pendientes ?? [];
  const ventasConfirmadas = pipeline?.ventas_confirmadas ?? [];
  const facturasRecientes = pipeline?.facturas_recientes ?? [];
  const resumen = pipeline?.resumen;

  const sumTotal = (items: Array<{ total_venta?: number; total_cotizacion?: number }>) =>
    items.reduce((s, i) => s + Number(i.total_venta ?? i.total_cotizacion ?? 0), 0);

  // WhatsApp helper
  const sendWhatsApp = (venta: Venta) => {
    const phone = import.meta.env.VITE_WHATSAPP_PHONE || '573019365537';
    const msg = `Hola, aquí está tu factura ${venta.numero_venta} por ${formatCurrency(Number(venta.total_venta))}.`;
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(msg)}`, '_blank');
  };

  // ─── Render ───────────────────────────────
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Comercial</h1>
          <p className="text-sm text-gray-500 mt-0.5">Pipeline unificado de cotizaciones, ventas y facturas</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowForm('cotizacion')}
            className="px-3 py-2 text-sm font-medium rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            + Cotización
          </button>
          <button
            onClick={() => setShowForm('venta')}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors"
          >
            + Venta
          </button>
        </div>
      </div>

      {/* Error toast */}
      {error && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* KPI summary */}
      {resumen && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'En cotización', value: resumen.total_cotizado, color: 'text-blue-600' },
            { label: 'Por cobrar', value: resumen.por_cobrar, color: 'text-amber-600' },
            { label: 'Facturado este mes', value: resumen.facturado_mes, color: 'text-green-600' },
          ].map((kpi) => (
            <div key={kpi.label} className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <p className="text-xs font-medium text-gray-500 mb-1">{kpi.label}</p>
              <p className={`text-xl font-bold ${kpi.color}`}>{formatCurrency(Number(kpi.value))}</p>
            </div>
          ))}
        </div>
      )}

      {/* Pipeline kanban */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {/* Col 1: Cotizaciones */}
        <PipelineColumn
          title="Cotizaciones"
          count={cotizacionesList.length}
          total={sumTotal(cotizacionesList)}
          colorClass="bg-blue-50 text-blue-700"
        >
          {cotizacionesList.length === 0 && (
            <p className="text-xs text-center text-gray-400 py-4">Sin cotizaciones activas</p>
          )}
          {cotizacionesList.map((cot) => (
            <DocCard
              key={cot.id}
              numero={cot.numero_cotizacion}
              estado={cot.estado}
              total={cot.total_cotizacion}
              fecha={cot.fecha_cotizacion}
              onClick={() => { setSelectedDoc(cot as unknown as Cotizacion); setDocType('cotizacion'); }}
              action={
                <div className="flex gap-1.5 flex-wrap">
                  {cot.estado === 'VIGENTE' && (
                    <button
                      onClick={() => convertirMutation.mutate(cot.id)}
                      disabled={convertirMutation.isPending}
                      className="flex-1 py-1.5 text-xs font-semibold rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 transition-colors"
                    >
                      Convertir a venta
                    </button>
                  )}
                  {cot.estado !== 'RECHAZADA' && cot.estado !== 'ACEPTADA' && (
                    <>
                      <button
                        onClick={() => renovarMutation.mutate(cot.id)}
                        disabled={renovarMutation.isPending}
                        className="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-50 transition-colors"
                      >
                        +15d
                      </button>
                      <button
                        onClick={() => rechazarMutation.mutate(cot.id)}
                        disabled={rechazarMutation.isPending}
                        className="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-red-100 text-red-500 hover:bg-red-50 disabled:opacity-50 transition-colors"
                      >
                        ✕
                      </button>
                    </>
                  )}
                </div>
              }
            />
          ))}
        </PipelineColumn>

        {/* Col 2: En proceso */}
        <PipelineColumn
          title="En proceso"
          count={ventasPendientes.length}
          total={sumTotal(ventasPendientes)}
          colorClass="bg-yellow-50 text-yellow-700"
        >
          {ventasPendientes.length === 0 && (
            <p className="text-xs text-center text-gray-400 py-4">Sin ventas pendientes</p>
          )}
          {ventasPendientes.map((v) => (
            <DocCard
              key={v.id}
              numero={v.numero_venta}
              estado={v.estado}
              total={v.total_venta}
              fecha={v.fecha_venta}
              onClick={() => { setSelectedDoc(v); setDocType('venta'); }}
              action={
                <button
                  onClick={() => facturarMutation.mutate(v.id)}
                  disabled={facturarMutation.isPending}
                  className="w-full py-1.5 text-xs font-semibold rounded-lg bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50 transition-colors"
                >
                  Facturar ahora
                </button>
              }
            />
          ))}
        </PipelineColumn>

        {/* Col 3: Por facturar */}
        <PipelineColumn
          title="Por facturar"
          count={ventasConfirmadas.length}
          total={sumTotal(ventasConfirmadas)}
          colorClass="bg-purple-50 text-purple-700"
        >
          {ventasConfirmadas.length === 0 && (
            <p className="text-xs text-center text-gray-400 py-4">Sin ventas confirmadas</p>
          )}
          {ventasConfirmadas.map((v) => (
            <DocCard
              key={v.id}
              numero={v.numero_venta}
              estado={v.estado}
              total={v.total_venta}
              fecha={v.fecha_venta}
              onClick={() => { setSelectedDoc(v); setDocType('venta'); }}
              action={
                <button
                  onClick={() => facturarMutation.mutate(v.id)}
                  disabled={facturarMutation.isPending}
                  className="w-full py-1.5 text-xs font-semibold rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 transition-colors"
                >
                  Emitir factura
                </button>
              }
            />
          ))}
        </PipelineColumn>

        {/* Col 4: Cobrar */}
        <PipelineColumn
          title="Cobrar"
          count={facturasRecientes.length}
          total={sumTotal(facturasRecientes)}
          colorClass="bg-green-50 text-green-700"
        >
          {facturasRecientes.length === 0 && (
            <p className="text-xs text-center text-gray-400 py-4">Sin facturas recientes</p>
          )}
          {facturasRecientes.map((v) => (
            <DocCard
              key={v.id}
              numero={v.numero_venta}
              estado={v.estado}
              total={v.total_venta}
              fecha={v.fecha_venta}
              onClick={() => { setSelectedDoc(v); setDocType('venta'); }}
              action={
                <button
                  onClick={() => sendWhatsApp(v)}
                  className="w-full py-1.5 text-xs font-semibold rounded-lg bg-green-500 text-white hover:bg-green-600 transition-colors flex items-center justify-center gap-1.5"
                >
                  <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 fill-current shrink-0">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                  </svg>
                  Enviar por WhatsApp
                </button>
              }
            />
          ))}
        </PipelineColumn>
      </div>

      {/* Document form modal */}
      <DocumentForm
        tipo={showForm === 'cotizacion' ? 'cotizacion' : 'venta'}
        open={!!showForm}
        onSubmit={(data) => {
          if (showForm === 'cotizacion') crearCotizacionMutation.mutate(data);
          else crearVentaMutation.mutate(data);
        }}
        onClose={() => setShowForm(null)}
        loading={crearVentaMutation.isPending || crearCotizacionMutation.isPending}
      />

      {/* Document detail modal */}
      <DocumentDetail
        tipo={docType ?? 'venta'}
        doc={selectedDoc as Venta | null}
        open={!!selectedDoc && !!docType}
        onClose={() => { setSelectedDoc(null); setDocType(null); }}
        onUpdated={() => queryClient.invalidateQueries({ queryKey: ['comercial-pipeline'] })}
      />
    </div>
  );
}
