import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cotizaciones } from '../api/endpoints';
import { formatCurrency, formatDate, statusColor } from '../utils/format';
import type { Cotizacion } from '../types';
import DocumentForm from '../components/DocumentForm';
import type { DocumentFormData } from '../components/DocumentForm';
import DocumentDetail from '../components/DocumentDetail';

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
        <h1 className="text-xl font-bold text-gray-900">Cotizaciones</h1>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors"
        >
          + Nueva Cotizacion
        </button>
      </div>

      {/* Filtros */}
      <div className="flex gap-2 mb-4">
        {['', 'VIGENTE', 'PENDIENTE', 'ACEPTADA', 'RECHAZADA', 'VENCIDA'].map((estado) => (
          <button
            key={estado}
            onClick={() => setFiltroEstado(estado)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              filtroEstado === estado
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {estado || 'Todas'}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-500">Numero</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Fecha</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Vencimiento</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Total</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Estado</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => setSelectedDoc(c)}
                  className="border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer"
                >
                  <td className="px-4 py-3 font-mono text-xs font-medium text-gray-900">
                    {c.numero_cotizacion}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{formatDate(c.fecha_cotizacion)}</td>
                  <td className="px-4 py-3 text-gray-600">{formatDate(c.fecha_vencimiento)}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-900">
                    {formatCurrency(c.total_cotizacion)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(c.estado)}`}
                    >
                      {c.estado}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center" onClick={(e) => e.stopPropagation()}>
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
                        className="rounded px-2 py-1 text-xs font-medium bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors"
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
                          className="rounded px-2 py-1 text-xs font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
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
            <div className="text-center py-12 text-gray-400">
              <p className="text-lg mb-2">Sin cotizaciones</p>
              <p className="text-sm">Crea tu primera cotizacion</p>
            </div>
          )}
        </div>
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
    </div>
  );
}
