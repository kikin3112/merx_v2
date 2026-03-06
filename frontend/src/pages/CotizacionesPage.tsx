import { HelpPanel } from '../components/tutorial/HelpPanel';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cotizaciones } from '../api/endpoints';
import { formatCurrency, formatDate, formatDateTime, statusColor } from '../utils/format';
import type { Cotizacion } from '../types';
import DocumentForm from '../components/DocumentForm';
import type { DocumentFormData } from '../components/DocumentForm';
import DocumentDetail from '../components/DocumentDetail';
import DataCard from '../components/ui/DataCard';

export default function CotizacionesPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<Cotizacion | null>(null);
  const [filtroEstado, setFiltroEstado] = useState<string>('');

  const { data, isLoading } = useQuery<Cotizacion[]>({
    queryKey: ['cotizaciones', filtroEstado],
    queryFn: () =>
      cotizaciones
        .list(filtroEstado ? { estado: filtroEstado } : undefined)
        .then((r) => r.data),
  });

  const crearMutation = useMutation({
    mutationFn: (formData: DocumentFormData) =>
      cotizaciones.create({
        tercero_id: formData.tercero_id,
        fecha_cotizacion: formData.fecha,
        fecha_vencimiento: formData.fecha_vencimiento,
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
      queryClient.invalidateQueries({ queryKey: ['cotizaciones'] });
      setShowForm(false);
    },
  });

  const convertirMutation = useMutation({
    mutationFn: (id: string) => cotizaciones.convertir(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cotizaciones'] });
      queryClient.invalidateQueries({ queryKey: ['facturas'] });
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-brand text-xl font-medium cv-text">Cotizaciones</h1>
        <button
          onClick={() => setShowForm(true)}
          className="cv-btn cv-btn-primary"
        >
          + Nueva Cotizacion
        </button>
      </div>

      {/* Filtros */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
        {['', 'VIGENTE', 'PENDIENTE', 'ACEPTADA', 'RECHAZADA', 'VENCIDA'].map((estado) => (
          <button
            key={estado}
            onClick={() => setFiltroEstado(estado)}
            className={`whitespace-nowrap cv-badge cursor-pointer transition-opacity ${
              filtroEstado === estado ? 'cv-badge-primary' : 'cv-badge-neutral'
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
                  <th className="text-left">Vencimiento</th>
                  <th className="text-right">Total</th>
                  <th className="text-center">Estado</th>
                  <th className="text-left">Creado Por</th>
                  <th className="text-center">Acciones</th>
                </tr>
              </thead>
              <tbody className="cv-table-body">
                {data?.map((c) => (
                  <tr key={c.id} onClick={() => setSelectedDoc(c)} className="cursor-pointer">
                    <td className="font-mono text-xs font-medium">{c.numero_cotizacion}</td>
                    <td className="cv-muted">{formatDate(c.fecha_cotizacion)}</td>
                    <td className="cv-muted">{formatDate(c.fecha_vencimiento)}</td>
                    <td className="text-right font-semibold">{formatCurrency(c.total_cotizacion)}</td>
                    <td className="text-center">
                      <span className={`cv-badge ${statusColor(c.estado)}`}>{c.estado}</span>
                    </td>
                    <td>
                      <div className="text-sm">{c.created_by?.nombre || 'Sistema'}</div>
                      <div className="text-xs cv-muted">{formatDateTime(c.created_at)}</div>
                    </td>
                    <td className="text-center" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => {
                            cotizaciones.descargarPdf(c.id).then((res) => {
                              const url = window.URL.createObjectURL(new Blob([res.data]));
                              const a = document.createElement('a');
                              a.href = url;
                              a.download = `cotizacion-${c.numero_cotizacion}.pdf`;
                              a.click();
                              window.URL.revokeObjectURL(url);
                            });
                          }}
                          className="rounded px-2 py-1 text-xs font-medium bg-[var(--cv-accent-dim)] text-[var(--cv-accent)] hover:opacity-80 transition-opacity"
                        >
                          PDF
                        </button>
                        {['VIGENTE', 'PENDIENTE', 'ACEPTADA'].includes(c.estado) && (
                          <button
                            onClick={() => {
                              if (confirm('Convertir esta cotizacion a factura?')) {
                                convertirMutation.mutate(c.id);
                              }
                            }}
                            disabled={convertirMutation.isPending}
                            className="rounded px-2 py-1 text-xs font-medium bg-[var(--cv-primary-dim)] text-[var(--cv-primary)] hover:opacity-80 transition-opacity"
                          >
                            Convertir
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
                <p className="text-lg mb-2">Sin cotizaciones</p>
                <p className="text-sm">Crea tu primera cotizacion</p>
              </div>
            )}
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {data?.map((c) => (
              <DataCard
                key={c.id}
                title={c.numero_cotizacion}
                subtitle={formatDate(c.fecha_cotizacion)}
                badge={<span className={`cv-badge ${statusColor(c.estado)}`}>{c.estado}</span>}
                fields={[
                  { label: 'Total', value: formatCurrency(c.total_cotizacion) },
                  { label: 'Vence', value: formatDate(c.fecha_vencimiento) },
                ]}
                onClick={() => setSelectedDoc(c)}
                actions={
                  <>
                    <button
                      onClick={() => {
                        cotizaciones.descargarPdf(c.id).then((res) => {
                          const url = window.URL.createObjectURL(new Blob([res.data]));
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `cotizacion-${c.numero_cotizacion}.pdf`;
                          a.click();
                          window.URL.revokeObjectURL(url);
                        });
                      }}
                      className="rounded-lg px-3 py-1.5 text-xs font-medium bg-[var(--cv-accent-dim)] text-[var(--cv-accent)]"
                    >
                      PDF
                    </button>
                    {['VIGENTE', 'PENDIENTE', 'ACEPTADA'].includes(c.estado) && (
                      <button
                        onClick={() => { if (confirm('Convertir a factura?')) convertirMutation.mutate(c.id); }}
                        disabled={convertirMutation.isPending}
                        className="rounded-lg px-3 py-1.5 text-xs font-medium bg-[var(--cv-primary-dim)] text-[var(--cv-primary)]"
                      >
                        Convertir
                      </button>
                    )}
                  </>
                }
              />
            ))}
            {data?.length === 0 && (
              <div className="text-center py-12 cv-muted">
                <p className="text-lg mb-2">Sin cotizaciones</p>
                <p className="text-sm">Crea tu primera cotizacion</p>
              </div>
            )}
          </div>
        </>
      )}

      <DocumentForm
        tipo="cotizacion"
        open={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={(data) => crearMutation.mutate(data)}
        loading={crearMutation.isPending}
      />

      <DocumentDetail
        tipo="cotizacion"
        doc={selectedDoc}
        open={!!selectedDoc}
        onClose={() => setSelectedDoc(null)}
        onUpdated={() => {
          queryClient.invalidateQueries({ queryKey: ['cotizaciones'] });
          setSelectedDoc(null);
        }}
      />
      <HelpPanel modulo="cotizaciones" />
    </div>
  );
}
