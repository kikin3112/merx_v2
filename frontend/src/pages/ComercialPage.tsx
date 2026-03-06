import { HelpPanel } from '../components/tutorial/HelpPanel';
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
const ESTADO_BADGE: Record<string, string> = {
  VIGENTE: 'cv-badge-accent',
  PENDIENTE: 'cv-badge-primary',
  CONFIRMADA: 'cv-badge-accent',
  FACTURADA: 'cv-badge-positive',
  ACEPTADA: 'cv-badge-positive',
  RECHAZADA: 'cv-badge-negative',
  ANULADA: 'cv-badge-neutral',
};

function EstadoBadge({ estado }: { estado: string }) {
  return (
    <span className={`cv-badge ${ESTADO_BADGE[estado] || 'cv-badge-neutral'}`}>
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
      className="cv-card-hover p-3 cursor-pointer group"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <p className="text-sm font-semibold cv-text group-hover:cv-primary transition-colors">
          {numero}
        </p>
        <EstadoBadge estado={estado} />
      </div>
      <p className="text-base font-bold cv-text mb-1">{formatCurrency(Number(total))}</p>
      <p className="text-xs cv-muted mb-3">{formatDate(fecha)}</p>
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
  headerClass: string;
  children: React.ReactNode;
}

function PipelineColumn({ title, count, total, headerClass, children }: ColumnProps) {
  return (
    <div className="flex-1 min-w-[160px] sm:min-w-[200px] md:min-w-[220px] max-w-xs">
      <div className={`flex items-center justify-between px-3 py-2 rounded-xl mb-3 ${headerClass}`}>
        <span className="text-sm font-semibold cv-text">{title}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs opacity-70">{formatCurrency(total)}</span>
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-black/10 text-xs font-bold">
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

  const sendWhatsApp = (venta: Venta) => {
    const phone = import.meta.env.VITE_WHATSAPP_PHONE || '573019365537';
    const msg = `Hola, aquí está tu factura ${venta.numero_venta} por ${formatCurrency(Number(venta.total_venta))}.`;
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(msg)}`, '_blank');
  };

  // ─── Render ───────────────────────────────
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--cv-primary)]" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-brand text-2xl font-medium cv-text">Comercial</h1>
          <p className="text-sm cv-muted mt-0.5">Pipeline unificado de cotizaciones, ventas y facturas</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowForm('cotizacion')}
            className="cv-btn cv-btn-secondary"
          >
            + Cotización
          </button>
          <button
            onClick={() => setShowForm('venta')}
            className="cv-btn cv-btn-primary"
          >
            + Venta
          </button>
        </div>
      </div>

      {/* Error toast */}
      {error && (
        <div className="cv-alert-error p-3 text-sm">
          {error}
        </div>
      )}

      {/* KPI summary */}
      {resumen && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'En cotización', value: resumen.total_cotizado, colorClass: 'cv-accent' },
            { label: 'Por cobrar', value: resumen.por_cobrar, colorClass: 'cv-primary' },
            { label: 'Facturado este mes', value: resumen.facturado_mes, colorClass: 'cv-positive' },
          ].map((kpi) => (
            <div key={kpi.label} className="bento-cell">
              <div className="bento-kpi-label">{kpi.label}</div>
              <div className={`bento-kpi-val ${kpi.colorClass}`}>{formatCurrency(Number(kpi.value))}</div>
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
          headerClass="cv-badge-accent"
        >
          {cotizacionesList.length === 0 && (
            <p className="text-xs text-center cv-muted py-4">Sin cotizaciones activas</p>
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
                      className="flex-1 cv-btn cv-btn-primary py-1.5 text-xs"
                    >
                      Convertir a venta
                    </button>
                  )}
                  {cot.estado !== 'RECHAZADA' && cot.estado !== 'ACEPTADA' && (
                    <>
                      <button
                        onClick={() => renovarMutation.mutate(cot.id)}
                        disabled={renovarMutation.isPending}
                        className="cv-btn cv-btn-secondary px-2.5 py-1.5 text-xs"
                      >
                        +15d
                      </button>
                      <button
                        onClick={() => rechazarMutation.mutate(cot.id)}
                        disabled={rechazarMutation.isPending}
                        className="cv-btn cv-btn-danger px-2.5 py-1.5 text-xs"
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
          headerClass="cv-badge-primary"
        >
          {ventasPendientes.length === 0 && (
            <p className="text-xs text-center cv-muted py-4">Sin ventas pendientes</p>
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
                  className="w-full cv-btn cv-btn-primary py-1.5 text-xs"
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
          headerClass="cv-badge-accent"
        >
          {ventasConfirmadas.length === 0 && (
            <p className="text-xs text-center cv-muted py-4">Sin ventas confirmadas</p>
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
                  className="w-full cv-btn cv-btn-primary py-1.5 text-xs"
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
          headerClass="cv-badge-positive"
        >
          {facturasRecientes.length === 0 && (
            <p className="text-xs text-center cv-muted py-4">Sin facturas recientes</p>
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
                  className="w-full cv-btn cv-btn-secondary py-1.5 text-xs flex items-center justify-center gap-1.5"
                  style={{ color: 'var(--cv-positive)', borderColor: 'var(--cv-positive)' }}
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
      <HelpPanel modulo="comercial" />
    </div>
  );
}
