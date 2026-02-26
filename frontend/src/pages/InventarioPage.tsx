import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventarios, productos } from '../api/endpoints';
import { formatCurrency, formatNumber, formatDate, formatDateTime } from '../utils/format';
import Modal from '../components/ui/Modal';
import DataCard from '../components/ui/DataCard';
import type { Inventario, MovimientoInventario, Producto } from '../types';

type Tab = 'valorizado' | 'movimientos' | 'alertas' | 'jerarquia';

const TIPO_MOV_LABELS: Record<string, { label: string; color: string }> = {
  ENTRADA: { label: 'Entrada', color: 'bg-green-100 text-green-700' },
  SALIDA: { label: 'Salida', color: 'bg-red-100 text-red-700' },
  AJUSTE: { label: 'Ajuste', color: 'bg-amber-100 text-amber-700' },
  PRODUCCION: { label: 'Produccion', color: 'bg-blue-100 text-blue-700' },
};

export default function InventarioPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>('valorizado');
  const [entradaOpen, setEntradaOpen] = useState(false);
  const [ajusteOpen, setAjusteOpen] = useState(false);
  const [error, setError] = useState('');

  // Data
  const { data: valorizado, isLoading: loadingVal } = useQuery<Inventario[]>({
    queryKey: ['inventario-valorizado'],
    queryFn: () => inventarios.valorizado().then((r) => r.data),
  });

  const { data: movimientos, isLoading: loadingMov } = useQuery<MovimientoInventario[]>({
    queryKey: ['inventario-movimientos'],
    queryFn: () => inventarios.movimientos().then((r) => r.data),
    enabled: tab === 'movimientos',
  });

  const { data: alertas, isLoading: loadingAlertas } = useQuery({
    queryKey: ['inventario-alertas'],
    queryFn: () => inventarios.alertas().then((r) => r.data),
    enabled: tab === 'alertas',
  });

  const { data: jerarquia, isLoading: loadingJerarquia } = useQuery({
    queryKey: ['inventario-jerarquia'],
    queryFn: () => inventarios.jerarquia().then((r) => r.data),
    enabled: tab === 'jerarquia',
  });

  const { data: productosList } = useQuery<Producto[]>({
    queryKey: ['productos-inventario'],
    queryFn: () => productos.list({ limit: 500 }).then((r) => r.data),
    enabled: entradaOpen || ajusteOpen,
  });

  const totalValor = valorizado?.reduce((sum, i) => sum + i.valor_total, 0) ?? 0;

  // Mutations
  const entradaMut = useMutation({
    mutationFn: inventarios.entrada,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventario-valorizado'] });
      queryClient.invalidateQueries({ queryKey: ['inventario-movimientos'] });
      queryClient.invalidateQueries({ queryKey: ['inventario-alertas'] });
      setEntradaOpen(false);
      setError('');
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Error al registrar entrada'),
  });

  const ajusteMut = useMutation({
    mutationFn: inventarios.ajuste,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventario-valorizado'] });
      queryClient.invalidateQueries({ queryKey: ['inventario-movimientos'] });
      queryClient.invalidateQueries({ queryKey: ['inventario-alertas'] });
      setAjusteOpen(false);
      setError('');
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Error al ajustar inventario'),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Inventario</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Valor total: <span className="font-semibold text-gray-900">{formatCurrency(totalValor)}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => { setError(''); setEntradaOpen(true); }}
            className="rounded-lg bg-green-500 px-4 py-2 text-sm font-semibold text-white hover:bg-green-600 transition-colors"
          >
            + Entrada
          </button>
          <button
            onClick={() => { setError(''); setAjusteOpen(true); }}
            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600 transition-colors"
          >
            Ajuste
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-gray-200 overflow-x-auto pb-1">
        {([
          { key: 'valorizado', label: 'Valorizado' },
          { key: 'movimientos', label: 'Movimientos' },
          { key: 'alertas', label: 'Alertas Stock' },
          { key: 'jerarquia', label: 'Jerarquía' },
        ] as const).map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap ${
              tab === t.key
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Valorizado Tab */}
      {tab === 'valorizado' && (
        loadingVal ? (
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-16 bg-gray-200 rounded-lg animate-pulse" />)}</div>
        ) : (
          <>
            <div className="hidden md:block bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Codigo</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Producto</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Cantidad</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Costo promedio</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Valor total</th>
                  </tr>
                </thead>
                <tbody>
                  {valorizado?.map((inv) => (
                    <tr key={inv.producto_id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-gray-600">{inv.codigo}</td>
                      <td className="px-4 py-3 font-medium text-gray-900">{inv.nombre}</td>
                      <td className="px-4 py-3 text-right text-gray-900">{formatNumber(inv.cantidad)}</td>
                      <td className="px-4 py-3 text-right text-gray-500">{formatCurrency(inv.costo_promedio)}</td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-900">{formatCurrency(inv.valor_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {valorizado?.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg mb-2">Sin inventario</p>
                  <p className="text-sm">Registra entradas para ver el inventario valorizado</p>
                </div>
              )}
            </div>
            <div className="md:hidden space-y-3">
              {valorizado?.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg mb-2">Sin inventario</p>
                  <p className="text-sm">Registra entradas para ver el inventario valorizado</p>
                </div>
              ) : (
                valorizado?.map((inv) => (
                  <DataCard
                    key={inv.producto_id}
                    title={inv.nombre}
                    subtitle={inv.codigo}
                    fields={[
                      { label: 'Stock', value: formatNumber(inv.cantidad) },
                      { label: 'Costo promedio', value: formatCurrency(inv.costo_promedio) },
                      { label: 'Valor total', value: formatCurrency(inv.valor_total) },
                    ]}
                  />
                ))
              )}
            </div>
          </>
        )
      )}

      {/* Movimientos Tab */}
      {tab === 'movimientos' && (
        loadingMov ? (
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-16 bg-gray-200 rounded-lg animate-pulse" />)}</div>
        ) : (
          <>
            <div className="hidden md:block bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Fecha</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Tipo</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Cantidad</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Costo unit.</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Referencia</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Observaciones</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Creado por</th>
                  </tr>
                </thead>
                <tbody>
                  {movimientos?.map((m) => {
                    const info = TIPO_MOV_LABELS[m.tipo_movimiento] || { label: m.tipo_movimiento, color: 'bg-gray-100 text-gray-700' };
                    return (
                      <tr key={m.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 text-gray-600 text-xs">{formatDate(m.fecha_movimiento)}</td>
                        <td className="px-4 py-3">
                          <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${info.color}`}>
                            {info.label}
                          </span>
                        </td>
                        <td className={`px-4 py-3 text-right font-medium ${m.cantidad >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {m.cantidad >= 0 ? '+' : ''}{formatNumber(m.cantidad)}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-500">
                          {m.costo_unitario != null ? formatCurrency(m.costo_unitario) : '-'}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-gray-500">{m.documento_referencia || '-'}</td>
                        <td className="px-4 py-3 text-xs text-gray-500 max-w-48 truncate">{m.observaciones || '-'}</td>
                        <td className="px-4 py-3">
                          <div className="text-sm text-gray-900">{m.created_by?.nombre || 'Sistema'}</div>
                          <div className="text-xs text-gray-400">{formatDateTime(m.created_at)}</div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {movimientos?.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg mb-2">Sin movimientos</p>
                  <p className="text-sm">Los movimientos aparecen al registrar entradas, ventas o ajustes</p>
                </div>
              )}
            </div>
            <div className="md:hidden space-y-3">
              {movimientos?.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg mb-2">Sin movimientos</p>
                  <p className="text-sm">Los movimientos aparecen al registrar entradas, ventas o ajustes</p>
                </div>
              ) : (
                movimientos?.map((m) => {
                  const info = TIPO_MOV_LABELS[m.tipo_movimiento] || { label: m.tipo_movimiento, color: 'bg-gray-100 text-gray-700' };
                  return (
                    <DataCard
                      key={m.id}
                      title={m.documento_referencia || 'Movimiento'}
                      subtitle={formatDate(m.fecha_movimiento)}
                      badge={
                        <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${info.color}`}>
                          {info.label}
                        </span>
                      }
                      fields={[
                        {
                          label: 'Cantidad',
                          value: (
                            <span className={m.cantidad >= 0 ? 'text-green-600' : 'text-red-600'}>
                              {m.cantidad >= 0 ? '+' : ''}{formatNumber(m.cantidad)}
                            </span>
                          ),
                        },
                        {
                          label: 'Costo Unit.',
                          value: m.costo_unitario != null ? formatCurrency(m.costo_unitario) : '-',
                        },
                        { label: 'Usuario', value: m.created_by?.nombre || 'Sistema' },
                        { label: 'Hora', value: formatDateTime(m.created_at) },
                      ]}
                    />
                  );
                })
              )}
            </div>
          </>
        )
      )}

      {/* Alertas Tab */}
      {tab === 'alertas' && (
        loadingAlertas ? (
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-16 bg-gray-200 rounded-lg animate-pulse" />)}</div>
        ) : (
          <>
            <div className="hidden md:block bg-white rounded-xl border border-gray-200 overflow-hidden">
              {alertas && alertas.length > 0 ? (
                <div className="divide-y divide-gray-50">
                  {alertas.map((a) => (
                    <div key={a.producto_id} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{a.nombre}</p>
                        <p className="text-xs text-gray-500">{a.codigo}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-red-600">{formatNumber(a.stock_actual)}</p>
                        <p className="text-xs text-gray-400">min: {formatNumber(a.stock_minimo)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg mb-2">Sin alertas</p>
                  <p className="text-sm">Todos los productos tienen stock por encima del minimo</p>
                </div>
              )}
            </div>
            <div className="md:hidden space-y-3">
              {alertas && alertas.length > 0 ? (
                alertas.map((a: any) => (
                  <DataCard
                    key={a.producto_id}
                    title={a.nombre}
                    subtitle={a.codigo}
                    badge={
                      <span className="inline-block rounded-full px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700">
                        Bajo stock
                      </span>
                    }
                    fields={[
                      { label: 'Stock Actual', value: <span className="text-red-600 font-semibold">{formatNumber(a.stock_actual)}</span> },
                      { label: 'Stock Minimo', value: formatNumber(a.stock_minimo) },
                      { label: 'Deficit', value: <span className="text-red-600">-{formatNumber(a.stock_minimo - a.stock_actual)}</span> },
                    ]}
                  />
                ))
              ) : (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg mb-2">Sin alertas</p>
                  <p className="text-sm">Todos los productos tienen stock por encima del minimo</p>
                </div>
              )}
            </div>
          </>
        )
      )}

      {/* Jerarquía Tab */}
      {tab === 'jerarquia' && (
        loadingJerarquia ? (
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-20 bg-gray-200 rounded-lg animate-pulse" />)}</div>
        ) : (
          <div>
            {jerarquia && (
              <div className="flex gap-4 mb-4 flex-wrap">
                <div className="rounded-xl bg-white border border-gray-200 p-4 flex-1 min-w-40">
                  <p className="text-xs text-gray-500">Total productos</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{jerarquia.total_productos}</p>
                </div>
                <div className="rounded-xl bg-white border border-gray-200 p-4 flex-1 min-w-40">
                  <p className="text-xs text-gray-500">Valor total</p>
                  <p className="text-2xl font-bold text-primary-600 mt-1">{formatCurrency(jerarquia.valor_total)}</p>
                </div>
              </div>
            )}
            <div className="space-y-3">
              {jerarquia?.productos.map((p) => (
                <JerarquiaProductoCard key={p.producto_id} producto={p} />
              ))}
              {jerarquia?.productos.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg mb-2">Sin datos de inventario</p>
                  <p className="text-sm">Registra entradas para ver la jerarquía</p>
                </div>
              )}
            </div>
          </div>
        )
      )}

      {/* Entrada Modal */}
      <Modal open={entradaOpen} onClose={() => setEntradaOpen(false)} title="Entrada de Mercancia">
        <EntradaForm
          productos={productosList || []}
          error={error}
          saving={entradaMut.isPending}
          onSubmit={(data) => entradaMut.mutate(data)}
          onCancel={() => setEntradaOpen(false)}
        />
      </Modal>

      {/* Ajuste Modal */}
      <Modal open={ajusteOpen} onClose={() => setAjusteOpen(false)} title="Ajuste de Inventario">
        <AjusteForm
          productos={productosList || []}
          error={error}
          saving={ajusteMut.isPending}
          onSubmit={(data) => ajusteMut.mutate(data)}
          onCancel={() => setAjusteOpen(false)}
        />
      </Modal>
    </div>
  );
}

// ---- Jerarquía Card ----

type JerarquiaProducto = {
  producto_id: string;
  nombre: string;
  codigo: string;
  cantidad: number;
  costo_promedio: number;
  valor_total: number;
  stock_minimo: number | null;
  alerta: boolean;
  ultimos_movimientos: Array<{
    id: string;
    tipo: string;
    cantidad: number;
    fecha: string | null;
    referencia: string | null;
  }>;
};

function JerarquiaProductoCard({ producto }: { producto: JerarquiaProducto }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`rounded-xl border bg-white overflow-hidden ${producto.alerta ? 'border-red-300' : 'border-gray-200'}`}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          {producto.alerta && (
            <span className="h-2 w-2 rounded-full bg-red-500 flex-shrink-0" title="Stock bajo" />
          )}
          <div>
            <p className="text-sm font-medium text-gray-900">{producto.nombre}</p>
            <p className="text-xs text-gray-500 font-mono">{producto.codigo}</p>
          </div>
        </div>
        <div className="flex items-center gap-4 flex-shrink-0">
          <div className="text-right">
            <p className={`text-sm font-semibold ${producto.alerta ? 'text-red-600' : 'text-gray-900'}`}>
              {formatNumber(producto.cantidad)} uds
            </p>
            <p className="text-xs text-gray-400">{formatCurrency(producto.valor_total)}</p>
          </div>
          <svg
            className={`h-4 w-4 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-100 px-4 py-3 bg-gray-50">
          <div className="flex gap-4 mb-3 text-xs text-gray-500 flex-wrap">
            <span>Costo promedio: <strong className="text-gray-700">{formatCurrency(producto.costo_promedio)}</strong></span>
            {producto.stock_minimo != null && (
              <span>Stock mínimo: <strong className={producto.alerta ? 'text-red-600' : 'text-gray-700'}>{formatNumber(producto.stock_minimo)}</strong></span>
            )}
          </div>
          {producto.ultimos_movimientos.length > 0 ? (
            <>
              <p className="text-xs font-medium text-gray-500 mb-2">Últimos movimientos</p>
              <div className="space-y-1.5">
                {producto.ultimos_movimientos.map((m) => (
                  <div key={m.id} className="flex items-center justify-between text-xs">
                    <span className={`font-medium ${m.cantidad >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {m.cantidad >= 0 ? '+' : ''}{formatNumber(m.cantidad)} — {m.tipo}
                    </span>
                    <span className="text-gray-400">
                      {m.fecha ? formatDate(m.fecha) : '-'}
                      {m.referencia && ` · ${m.referencia}`}
                    </span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-xs text-gray-400">Sin movimientos recientes</p>
          )}
        </div>
      )}
    </div>
  );
}

// ---- Entrada Form ----

function EntradaForm({ productos, error, saving, onSubmit, onCancel }: {
  productos: Producto[];
  error: string;
  saving: boolean;
  onSubmit: (data: { producto_id: string; cantidad: number; costo_unitario: number; documento_referencia?: string; observaciones?: string }) => void;
  onCancel: () => void;
}) {
  const [productoId, setProductoId] = useState('');
  const [cantidad, setCantidad] = useState('');
  const [costoUnitario, setCostoUnitario] = useState('');
  const [docRef, setDocRef] = useState('');
  const [obs, setObs] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      producto_id: productoId,
      cantidad: parseFloat(cantidad),
      costo_unitario: parseFloat(costoUnitario),
      documento_referencia: docRef || undefined,
      observaciones: obs || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2">{error}</div>}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Producto *</label>
        <select
          required
          value={productoId}
          onChange={(e) => setProductoId(e.target.value)}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">Seleccionar producto...</option>
          {[...productos].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es')).map((p) => (
            <option key={p.id} value={p.id}>{p.codigo_interno} - {p.nombre}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cantidad *</label>
          <input type="number" required min={0.01} step={0.01} value={cantidad} onChange={(e) => setCantidad(e.target.value)}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Costo unitario *</label>
          <input type="number" required min={0} step={0.01} value={costoUnitario} onChange={(e) => setCostoUnitario(e.target.value)}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Documento referencia</label>
        <input type="text" value={docRef} onChange={(e) => setDocRef(e.target.value)}
          placeholder="Ej: FACTURA-001, REMISION-023"
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Observaciones</label>
        <textarea rows={2} value={obs} onChange={(e) => setObs(e.target.value)}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
        <button type="button" onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
          Cancelar
        </button>
        <button type="submit" disabled={saving}
          className="px-4 py-2 text-sm font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50">
          {saving ? 'Registrando...' : 'Registrar Entrada'}
        </button>
      </div>
    </form>
  );
}

// ---- Ajuste Form ----

function AjusteForm({ productos, error, saving, onSubmit, onCancel }: {
  productos: Producto[];
  error: string;
  saving: boolean;
  onSubmit: (data: { producto_id: string; cantidad_nueva: number; motivo: string }) => void;
  onCancel: () => void;
}) {
  const [productoId, setProductoId] = useState('');
  const [cantidadNueva, setCantidadNueva] = useState('');
  const [motivo, setMotivo] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      producto_id: productoId,
      cantidad_nueva: parseFloat(cantidadNueva),
      motivo,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2">{error}</div>}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Producto *</label>
        <select
          required
          value={productoId}
          onChange={(e) => setProductoId(e.target.value)}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">Seleccionar producto...</option>
          {[...productos].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es')).map((p) => (
            <option key={p.id} value={p.id}>{p.codigo_interno} - {p.nombre}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Cantidad nueva *</label>
        <input type="number" required min={0} step={0.01} value={cantidadNueva} onChange={(e) => setCantidadNueva(e.target.value)}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
        <p className="text-xs text-gray-400 mt-1">Se ajustara el stock a esta cantidad exacta</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Motivo *</label>
        <textarea rows={2} required value={motivo} onChange={(e) => setMotivo(e.target.value)}
          placeholder="Ej: Conteo fisico, merma, daño..."
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" />
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
        <button type="button" onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
          Cancelar
        </button>
        <button type="submit" disabled={saving}
          className="px-4 py-2 text-sm font-semibold text-white bg-amber-500 rounded-lg hover:bg-amber-600 transition-colors disabled:opacity-50">
          {saving ? 'Ajustando...' : 'Ajustar Inventario'}
        </button>
      </div>
    </form>
  );
}
