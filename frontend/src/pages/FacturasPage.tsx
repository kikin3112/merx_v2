import { HelpPanel } from '../components/tutorial/HelpPanel';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { facturas } from '../api/endpoints';
import { trackInvoiceCreated } from '../hooks/useAnalytics';
import { formatCurrency, formatDate, statusColor } from '../utils/format';
import type { Factura } from '../types';
import DocumentForm from '../components/DocumentForm';
import type { DocumentFormData } from '../components/DocumentForm';
import DocumentDetail from '../components/DocumentDetail';
import DataCard from '../components/ui/DataCard';

export default function FacturasPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<Factura | null>(null);
  const [filtroEstado, setFiltroEstado] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const showError = (err: any, fallback: string) => {
    const msg = err?.response?.data?.detail || fallback;
    setError(msg);
    setTimeout(() => setError(null), 6000);
  };

  const { data, isLoading } = useQuery<Factura[]>({
    queryKey: ['facturas', filtroEstado],
    queryFn: () =>
      facturas
        .list(filtroEstado ? { estado: filtroEstado } : undefined)
        .then((r) => r.data),
  });

  const crearMutation = useMutation({
    mutationFn: (formData: DocumentFormData) =>
      facturas.create({
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
      queryClient.invalidateQueries({ queryKey: ['facturas'] });
      setShowForm(false);
    },
    onError: (err: any) => showError(err, 'Error al crear factura'),
  });

  const emitirMutation = useMutation({
    mutationFn: (id: string) => facturas.emitir(id),
    onSuccess: (response) => {
      trackInvoiceCreated(response.data.total_venta);
      queryClient.invalidateQueries({ queryKey: ['facturas'] });
    },
    onError: (err: any) => showError(err, 'Error al emitir factura'),
  });

  const anularMutation = useMutation({
    mutationFn: (id: string) => facturas.anular(id, 'Anulada desde frontend'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
    onError: (err: any) => showError(err, 'Error al anular factura'),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-brand text-xl font-medium cv-text">Facturas</h1>
        <button
          onClick={() => setShowForm(true)}
          className="cv-btn cv-btn-primary"
        >
          + Nueva factura
        </button>
      </div>

      {error && (
        <div className="mb-4 cv-alert-error px-4 py-3 flex items-center justify-between">
          <p className="text-sm">{error}</p>
          <button onClick={() => setError(null)} className="ml-3 cv-icon-btn p-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Filtros */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
        {['', 'PENDIENTE', 'CONFIRMADA', 'FACTURADA', 'ANULADA'].map((estado) => (
          <button
            key={estado}
            onClick={() => setFiltroEstado(estado)}
            className={`whitespace-nowrap cv-badge cursor-pointer transition-colors ${
              filtroEstado === estado
                ? 'cv-badge-primary'
                : 'cv-badge-neutral hover:cv-badge-accent'
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
                  <th className="text-right">Subtotal</th>
                  <th className="text-right">IVA</th>
                  <th className="text-right">Total</th>
                  <th className="text-center">Estado</th>
                  <th className="text-center">Acciones</th>
                </tr>
              </thead>
              <tbody className="cv-table-body">
                {data?.map((f) => (
                  <tr
                    key={f.id}
                    onClick={() => setSelectedDoc(f)}
                    className="cursor-pointer"
                  >
                    <td className="font-mono text-xs font-medium">
                      {f.numero_venta}
                    </td>
                    <td className="cv-muted">{formatDate(f.fecha_venta)}</td>
                    <td className="text-right cv-muted">
                      {formatCurrency(f.subtotal)}
                    </td>
                    <td className="text-right cv-muted">
                      {formatCurrency(f.total_iva)}
                    </td>
                    <td className="text-right font-semibold">
                      {formatCurrency(f.total_venta)}
                    </td>
                    <td className="text-center">
                      <span className={`cv-badge ${statusColor(f.estado)}`}>
                        {f.estado}
                      </span>
                    </td>
                    <td className="text-center" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-center gap-1">
                        {f.estado === 'PENDIENTE' && (
                          <button
                            onClick={() => emitirMutation.mutate(f.id)}
                            disabled={emitirMutation.isPending}
                            className="cv-btn cv-btn-secondary text-xs px-2 py-1"
                            style={{ color: 'var(--cv-positive)', borderColor: 'var(--cv-positive)' }}
                          >
                            Emitir
                          </button>
                        )}
                        {f.estado === 'FACTURADA' && (
                          <button
                            onClick={() => {
                              facturas.descargarPdf(f.id).then((res) => {
                                const url = window.URL.createObjectURL(new Blob([res.data]));
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = `factura-${f.numero_venta}.pdf`;
                                a.click();
                                window.URL.revokeObjectURL(url);
                              });
                            }}
                            className="cv-btn cv-btn-secondary text-xs px-2 py-1"
                          >
                            PDF
                          </button>
                        )}
                        {f.estado !== 'ANULADA' && (
                          <button
                            onClick={() => {
                              if (confirm('Anular esta factura?')) {
                                anularMutation.mutate(f.id);
                              }
                            }}
                            disabled={anularMutation.isPending}
                            className="cv-btn cv-btn-danger text-xs px-2 py-1"
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
                <p className="text-lg mb-2">Sin facturas</p>
                <p className="text-sm">Crea tu primera factura o emite una venta</p>
              </div>
            )}
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {data?.map((f) => (
              <DataCard
                key={f.id}
                title={f.numero_venta}
                subtitle={formatDate(f.fecha_venta)}
                badge={
                  <span className={`cv-badge ${statusColor(f.estado)}`}>
                    {f.estado}
                  </span>
                }
                fields={[
                  { label: 'Total', value: formatCurrency(f.total_venta) },
                  { label: 'IVA', value: formatCurrency(f.total_iva) },
                ]}
                onClick={() => setSelectedDoc(f)}
                actions={
                  <>
                    {f.estado === 'PENDIENTE' && (
                      <button
                        onClick={() => emitirMutation.mutate(f.id)}
                        disabled={emitirMutation.isPending}
                        className="cv-btn cv-btn-secondary text-xs px-3 py-1.5"
                        style={{ color: 'var(--cv-positive)' }}
                      >
                        Emitir
                      </button>
                    )}
                    {f.estado === 'FACTURADA' && (
                      <button
                        onClick={() => {
                          facturas.descargarPdf(f.id).then((res) => {
                            const url = window.URL.createObjectURL(new Blob([res.data]));
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `factura-${f.numero_venta}.pdf`;
                            a.click();
                            window.URL.revokeObjectURL(url);
                          });
                        }}
                        className="cv-btn cv-btn-secondary text-xs px-3 py-1.5"
                      >
                        PDF
                      </button>
                    )}
                    {f.estado !== 'ANULADA' && (
                      <button
                        onClick={() => { if (confirm('Anular esta factura?')) anularMutation.mutate(f.id); }}
                        disabled={anularMutation.isPending}
                        className="cv-btn cv-btn-danger text-xs px-3 py-1.5"
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
                <p className="text-lg mb-2">Sin facturas</p>
                <p className="text-sm">Crea tu primera factura o emite una venta</p>
              </div>
            )}
          </div>
        </>
      )}

      <DocumentForm
        tipo="factura"
        open={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={(data) => crearMutation.mutate(data)}
        loading={crearMutation.isPending}
      />

      <DocumentDetail
        tipo="factura"
        doc={selectedDoc}
        open={!!selectedDoc}
        onClose={() => setSelectedDoc(null)}
        onUpdated={() => {
          queryClient.invalidateQueries({ queryKey: ['facturas'] });
          setSelectedDoc(null);
        }}
      />
      <HelpPanel modulo="facturas" />
    </div>
  );
}
