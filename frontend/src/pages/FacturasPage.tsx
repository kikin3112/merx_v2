import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { facturas } from '../api/endpoints';
import { formatCurrency, formatDate, statusColor } from '../utils/format';
import type { Factura } from '../types';
import DocumentForm from '../components/DocumentForm';
import type { DocumentFormData } from '../components/DocumentForm';
import DocumentDetail from '../components/DocumentDetail';

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
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
    onError: (err: any) => showError(err, 'Error al emitir factura'),
  });

  const anularMutation = useMutation({
    mutationFn: (id: string) => facturas.anular(id, 'Anulada desde frontend'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
    onError: (err: any) => showError(err, 'Error al anular factura'),
  });

  // Removed facturarMutation - "facturar" flow belongs on VentasPage only

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Facturas</h1>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors"
        >
          + Nueva Factura
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 flex items-center justify-between">
          <p className="text-sm text-red-700">{error}</p>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 ml-3">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Filtros */}
      <div className="flex gap-2 mb-4">
        {['', 'PENDIENTE', 'CONFIRMADA', 'FACTURADA', 'ANULADA'].map((estado) => (
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
                <th className="text-right px-4 py-3 font-medium text-gray-500">Subtotal</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">IVA</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Total</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Estado</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((f) => (
                <tr
                  key={f.id}
                  onClick={() => setSelectedDoc(f)}
                  className="border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer"
                >
                  <td className="px-4 py-3 font-mono text-xs font-medium text-gray-900">
                    {f.numero_venta}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{formatDate(f.fecha_venta)}</td>
                  <td className="px-4 py-3 text-right text-gray-600">
                    {formatCurrency(f.subtotal)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600">
                    {formatCurrency(f.total_iva)}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-900">
                    {formatCurrency(f.total_venta)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(f.estado)}`}
                    >
                      {f.estado}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-center gap-1">
                      {f.estado === 'PENDIENTE' && (
                        <button
                          onClick={() => emitirMutation.mutate(f.id)}
                          disabled={emitirMutation.isPending}
                          className="rounded px-2 py-1 text-xs font-medium bg-green-50 text-green-700 hover:bg-green-100 transition-colors"
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
                          className="rounded px-2 py-1 text-xs font-medium bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors"
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
                          className="rounded px-2 py-1 text-xs font-medium bg-red-50 text-red-700 hover:bg-red-100 transition-colors"
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
            <div className="text-center py-12 text-gray-400">
              <p className="text-lg mb-2">Sin facturas</p>
              <p className="text-sm">Crea tu primera factura o emite una venta</p>
            </div>
          )}
        </div>
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
    </div>
  );
}
