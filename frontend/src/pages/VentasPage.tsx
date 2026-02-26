import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ventas } from '../api/endpoints';
import { formatCurrency, formatDate, formatDateTime, statusColor } from '../utils/format';
import type { Venta } from '../types';
import DocumentForm from '../components/DocumentForm';
import type { DocumentFormData } from '../components/DocumentForm';
import DocumentDetail from '../components/DocumentDetail';
import DataCard from '../components/ui/DataCard';

export default function VentasPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<Venta | null>(null);
  const [filtroEstado, setFiltroEstado] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const showError = (err: any, fallback: string) => {
    const msg = err?.response?.data?.detail || fallback;
    setError(msg);
    setTimeout(() => setError(null), 6000);
  };

  const { data, isLoading } = useQuery<Venta[]>({
    queryKey: ['ventas', filtroEstado],
    queryFn: () =>
      ventas.list(filtroEstado ? { estado: filtroEstado } : undefined).then((r) => r.data),
  });

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

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Ventas</h1>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors"
        >
          + Nueva venta
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
      <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
        {['', 'PENDIENTE', 'CONFIRMADA', 'FACTURADA', 'ANULADA'].map((estado) => (
          <button
            key={estado}
            onClick={() => setFiltroEstado(estado)}
            className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium transition-colors ${
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
        <>
          {/* Desktop table */}
          <div className="hidden md:block bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Numero</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Fecha</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-500">Total</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-500">Estado</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Creado Por</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-500">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {data?.map((v) => (
                  <tr key={v.id} onClick={() => setSelectedDoc(v)} className="border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer">
                    <td className="px-4 py-3 font-mono text-xs font-medium text-gray-900">{v.numero_venta}</td>
                    <td className="px-4 py-3 text-gray-600">{formatDate(v.fecha_venta)}</td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-900">{formatCurrency(v.total_venta)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(v.estado)}`}>
                        {v.estado}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-gray-900">{v.created_by?.nombre || 'Sistema'}</div>
                      <div className="text-xs text-gray-400">{formatDateTime(v.created_at)}</div>
                    </td>
                    <td className="px-4 py-3 text-center" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-center gap-1">
                        {v.estado === 'PENDIENTE' && (
                          <>
                            <button
                              onClick={() => confirmarMutation.mutate(v.id)}
                              disabled={confirmarMutation.isPending}
                              className="rounded px-2 py-1 text-xs font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
                            >
                              Confirmar
                            </button>
                            <button
                              onClick={() => facturarMutation.mutate(v.id)}
                              disabled={facturarMutation.isPending}
                              className="rounded px-2 py-1 text-xs font-medium bg-green-50 text-green-700 hover:bg-green-100 transition-colors"
                            >
                              {facturarMutation.isPending ? 'Facturando...' : 'Facturar'}
                            </button>
                          </>
                        )}
                        {v.estado === 'CONFIRMADA' && (
                          <button
                            onClick={() => facturarMutation.mutate(v.id)}
                            disabled={facturarMutation.isPending}
                            className="rounded px-2 py-1 text-xs font-medium bg-green-50 text-green-700 hover:bg-green-100 transition-colors"
                          >
                            {facturarMutation.isPending ? 'Facturando...' : 'Facturar'}
                          </button>
                        )}
                        {v.estado !== 'ANULADA' && v.estado !== 'FACTURADA' && (
                          <button
                            onClick={() => {
                              if (confirm('Anular esta venta?')) {
                                anularMutation.mutate(v.id);
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
                badge={
                  <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(v.estado)}`}>
                    {v.estado}
                  </span>
                }
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
                          className="rounded-lg px-3 py-1.5 text-xs font-medium bg-blue-50 text-blue-700 active:bg-blue-100"
                        >
                          Confirmar
                        </button>
                        <button
                          onClick={() => facturarMutation.mutate(v.id)}
                          disabled={facturarMutation.isPending}
                          className="rounded-lg px-3 py-1.5 text-xs font-medium bg-green-50 text-green-700 active:bg-green-100"
                        >
                          Facturar
                        </button>
                      </>
                    )}
                    {v.estado === 'CONFIRMADA' && (
                      <button
                        onClick={() => facturarMutation.mutate(v.id)}
                        disabled={facturarMutation.isPending}
                        className="rounded-lg px-3 py-1.5 text-xs font-medium bg-green-50 text-green-700 active:bg-green-100"
                      >
                        Facturar
                      </button>
                    )}
                    {v.estado !== 'ANULADA' && v.estado !== 'FACTURADA' && (
                      <button
                        onClick={() => { if (confirm('Anular esta venta?')) anularMutation.mutate(v.id); }}
                        disabled={anularMutation.isPending}
                        className="rounded-lg px-3 py-1.5 text-xs font-medium bg-red-50 text-red-700 active:bg-red-100"
                      >
                        Anular
                      </button>
                    )}
                  </>
                }
              />
            ))}
            {data?.length === 0 && (
              <div className="text-center py-12 text-gray-400">
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
