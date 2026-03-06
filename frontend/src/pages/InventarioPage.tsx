import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventarios, productos } from '../api/endpoints';
import { formatCurrency, formatNumber, formatDate, formatDateTime } from '../utils/format';
import Modal from '../components/ui/Modal';
import DataCard from '../components/ui/DataCard';
import type { Inventario, MovimientoInventario, Producto } from '../types';

type Tab = 'valorizado' | 'movimientos' | 'alertas' | 'jerarquia';

const TIPO_MOV_LABELS: Record<string, { label: string; color: string }> = {
  ENTRADA: { label: 'Entrada', color: 'cv-badge-positive' },
  SALIDA: { label: 'Salida', color: 'cv-badge-negative' },
  AJUSTE: { label: 'Ajuste', color: 'cv-badge-accent' },
  PRODUCCION: { label: 'Produccion', color: 'cv-badge-primary' },
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
          <h1 className="font-brand text-xl font-medium cv-text">Inventario</h1>
          <p className="text-sm cv-muted mt-0.5">
            Valor total: <span className="font-semibold cv-text">{formatCurrency(totalValor)}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => { setError(''); setEntradaOpen(true); }}
            className="cv-btn cv-btn-primary"
          >
            + Entrada
          </button>
          <button
            onClick={() => { setError(''); setAjusteOpen(true); }}
            className="cv-btn cv-btn-secondary"
          >
            Ajuste
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b cv-divider overflow-x-auto pb-1">
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
                ? 'border-[var(--cv-primary)] cv-primary'
                : 'border-transparent cv-muted'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Valorizado Tab */}
      {tab === 'valorizado' && (
        loadingVal ? (
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-16 cv-elevated rounded-lg animate-pulse" />)}</div>
        ) : (
          <>
            <div className="hidden md:block cv-card overflow-hidden">
              <table className="w-full text-sm">
                <thead className="cv-table-header">
                  <tr>
                    <th className="text-left">Codigo</th>
                    <th className="text-left">Producto</th>
                    <th className="text-right">Cantidad</th>
                    <th className="text-right">Costo promedio</th>
                    <th className="text-right">Valor total</th>
                  </tr>
                </thead>
                <tbody className="cv-table-body">
                  {valorizado?.map((inv) => (
                    <tr key={inv.producto_id}>
                      <td className="font-mono text-xs cv-muted">{inv.codigo}</td>
                      <td className="font-medium">{inv.nombre}</td>
                      <td className="text-right">{formatNumber(inv.cantidad)}</td>
                      <td className="text-right cv-muted">{formatCurrency(inv.costo_promedio)}</td>
                      <td className="text-right font-semibold">{formatCurrency(inv.valor_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {valorizado?.length === 0 && (
                <div className="text-center py-12 cv-muted">
                  <p className="text-lg mb-2">Sin inventario</p>
                  <p className="text-sm">Registra entradas para ver el inventario valorizado</p>
                </div>
              )}
            </div>
            <div className="md:hidden space-y-3">
              {valorizado?.length === 0 ? (
                <div className="text-center py-12 cv-muted">
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
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-16 cv-elevated rounded-lg animate-pulse" />)}</div>
        ) : (
          <>
            <div className="hidden md:block cv-card overflow-hidden">
              <table className="w-full text-sm">
                <thead className="cv-table-header">
                  <tr>
                    <th className="text-left">Fecha</th>
                    <th className="text-left">Tipo</th>
                    <th className="text-right">Cantidad</th>
                    <th className="text-right">Costo unit.</th>
                    <th className="text-left">Referencia</th>
                    <th className="text-left">Observaciones</th>
                    <th className="text-left">Creado por</th>
                  </tr>
                </thead>
                <tbody className="cv-table-body">
                  {movimientos?.map((m) => {
                    const info = TIPO_MOV_LABELS[m.tipo_movimiento] || { label: m.tipo_movimiento, color: 'cv-badge-neutral' };
                    return (
                      <tr key={m.id}>
                        <td className="cv-muted text-xs">{formatDate(m.fecha_movimiento)}</td>
                        <td>
                          <span className={`cv-badge ${info.color}`}>{info.label}</span>
                        </td>
                        <td className={`text-right font-medium ${m.cantidad >= 0 ? 'cv-positive' : 'cv-negative'}`}>
                          {m.cantidad >= 0 ? '+' : ''}{formatNumber(m.cantidad)}
                        </td>
                        <td className="text-right cv-muted">
                          {m.costo_unitario != null ? formatCurrency(m.costo_unitario) : '-'}
                        </td>
                        <td className="font-mono text-xs cv-muted">{m.documento_referencia || '-'}</td>
                        <td className="text-xs cv-muted max-w-48 truncate">{m.observaciones || '-'}</td>
                        <td>
                          <div className="text-sm">{m.created_by?.nombre || 'Sistema'}</div>
                          <div className="text-xs cv-muted">{formatDateTime(m.created_at)}</div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {movimientos?.length === 0 && (
                <div className="text-center py-12 cv-muted">
                  <p className="text-lg mb-2">Sin movimientos</p>
                  <p className="text-sm">Los movimientos aparecen al registrar entradas, ventas o ajustes</p>
                </div>
              )}
            </div>
            <div className="md:hidden space-y-3">
              {movimientos?.length === 0 ? (
                <div className="text-center py-12 cv-muted">
                  <p className="text-lg mb-2">Sin movimientos</p>
                  <p className="text-sm">Los movimientos aparecen al registrar entradas, ventas o ajustes</p>
                </div>
              ) : (
                movimientos?.map((m) => {
                  const info = TIPO_MOV_LABELS[m.tipo_movimiento] || { label: m.tipo_movimiento, color: 'cv-badge-neutral' };
                  return (
                    <DataCard
                      key={m.id}
                      title={m.documento_referencia || 'Movimiento'}
                      subtitle={formatDate(m.fecha_movimiento)}
                      badge={<span className={`cv-badge ${info.color}`}>{info.label}</span>}
                      fields={[
                        {
                          label: 'Cantidad',
                          value: (
                            <span className={m.cantidad >= 0 ? 'cv-positive' : 'cv-negative'}>
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
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-16 cv-elevated rounded-lg animate-pulse" />)}</div>
        ) : (
          <>
            <div className="hidden md:block cv-card overflow-hidden">
              {alertas && alertas.length > 0 ? (
                <div className="divide-y cv-divider">
                  {alertas.map((a) => (
                    <div key={a.producto_id} className="flex items-center justify-between px-4 py-3 hover:bg-[var(--cv-elevated)] transition-colors">
                      <div>
                        <p className="text-sm font-medium">{a.nombre}</p>
                        <p className="text-xs cv-muted">{a.codigo}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold cv-negative">{formatNumber(a.stock_actual)}</p>
                        <p className="text-xs cv-muted">min: {formatNumber(a.stock_minimo)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 cv-muted">
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
                    badge={<span className="cv-badge cv-badge-negative">Bajo stock</span>}
                    fields={[
                      { label: 'Stock Actual', value: <span className="cv-negative font-semibold">{formatNumber(a.stock_actual)}</span> },
                      { label: 'Stock Minimo', value: formatNumber(a.stock_minimo) },
                      { label: 'Deficit', value: <span className="cv-negative">-{formatNumber(a.stock_minimo - a.stock_actual)}</span> },
                    ]}
                  />
                ))
              ) : (
                <div className="text-center py-12 cv-muted">
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
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-20 cv-elevated rounded-lg animate-pulse" />)}</div>
        ) : (
          <div>
            {jerarquia && (
              <div className="flex gap-4 mb-4 flex-wrap">
                <div className="bento-cell flex-1 min-w-40">
                  <div className="bento-kpi-label">Total productos</div>
                  <div className="bento-kpi-val">{jerarquia.total_productos}</div>
                </div>
                <div className="bento-cell flex-1 min-w-40">
                  <div className="bento-kpi-label">Valor total</div>
                  <div className="bento-kpi-val cv-primary">{formatCurrency(jerarquia.valor_total)}</div>
                </div>
              </div>
            )}
            <div className="space-y-3">
              {jerarquia?.productos.map((p) => (
                <JerarquiaProductoCard key={p.producto_id} producto={p} />
              ))}
              {jerarquia?.productos.length === 0 && (
                <div className="text-center py-12 cv-muted">
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
    <div className={`cv-card overflow-hidden ${producto.alerta ? 'border-[var(--cv-negative)]' : ''}`}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-[var(--cv-elevated)] transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          {producto.alerta && (
            <span className="h-2 w-2 rounded-full bg-[var(--cv-negative)] flex-shrink-0" title="Stock bajo" />
          )}
          <div>
            <p className="text-sm font-medium cv-text">{producto.nombre}</p>
            <p className="text-xs cv-muted font-mono">{producto.codigo}</p>
          </div>
        </div>
        <div className="flex items-center gap-4 flex-shrink-0">
          <div className="text-right">
            <p className={`text-sm font-semibold ${producto.alerta ? 'cv-negative' : 'cv-text'}`}>
              {formatNumber(producto.cantidad)} uds
            </p>
            <p className="text-xs cv-muted">{formatCurrency(producto.valor_total)}</p>
          </div>
          <svg
            className={`h-4 w-4 cv-muted transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="border-t cv-divider px-4 py-3 cv-elevated">
          <div className="flex gap-4 mb-3 text-xs cv-muted flex-wrap">
            <span>Costo promedio: <strong className="cv-text">{formatCurrency(producto.costo_promedio)}</strong></span>
            {producto.stock_minimo != null && (
              <span>Stock mínimo: <strong className={producto.alerta ? 'cv-negative' : 'cv-text'}>{formatNumber(producto.stock_minimo)}</strong></span>
            )}
          </div>
          {producto.ultimos_movimientos.length > 0 ? (
            <>
              <p className="text-xs font-medium cv-muted mb-2">Últimos movimientos</p>
              <div className="space-y-1.5">
                {producto.ultimos_movimientos.map((m) => (
                  <div key={m.id} className="flex items-center justify-between text-xs">
                    <span className={`font-medium ${m.cantidad >= 0 ? 'cv-positive' : 'cv-negative'}`}>
                      {m.cantidad >= 0 ? '+' : ''}{formatNumber(m.cantidad)} — {m.tipo}
                    </span>
                    <span className="cv-muted">
                      {m.fecha ? formatDate(m.fecha) : '-'}
                      {m.referencia && ` · ${m.referencia}`}
                    </span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-xs cv-muted">Sin movimientos recientes</p>
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
      {error && <div className="cv-alert-error px-4 py-2 text-sm">{error}</div>}

      <div>
        <label className="block text-sm font-medium cv-muted mb-1">Producto *</label>
        <select
          required
          value={productoId}
          onChange={(e) => setProductoId(e.target.value)}
          className="cv-input"
        >
          <option value="">Seleccionar producto...</option>
          {[...productos].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es')).map((p) => (
            <option key={p.id} value={p.id}>{p.codigo_interno} - {p.nombre}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium cv-muted mb-1">Cantidad *</label>
          <input type="number" required min={0.01} step={0.01} value={cantidad} onChange={(e) => setCantidad(e.target.value)}
            className="cv-input" />
        </div>
        <div>
          <label className="block text-sm font-medium cv-muted mb-1">Costo unitario *</label>
          <input type="number" required min={0} step={0.01} value={costoUnitario} onChange={(e) => setCostoUnitario(e.target.value)}
            className="cv-input" />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium cv-muted mb-1">Documento referencia</label>
        <input type="text" value={docRef} onChange={(e) => setDocRef(e.target.value)}
          placeholder="Ej: FACTURA-001, REMISION-023"
          className="cv-input" />
      </div>

      <div>
        <label className="block text-sm font-medium cv-muted mb-1">Observaciones</label>
        <textarea rows={2} value={obs} onChange={(e) => setObs(e.target.value)}
          className="cv-input" />
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t cv-divider">
        <button type="button" onClick={onCancel} className="cv-btn cv-btn-secondary">
          Cancelar
        </button>
        <button type="submit" disabled={saving} className="cv-btn cv-btn-primary">
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
      {error && <div className="cv-alert-error px-4 py-2 text-sm">{error}</div>}

      <div>
        <label className="block text-sm font-medium cv-muted mb-1">Producto *</label>
        <select
          required
          value={productoId}
          onChange={(e) => setProductoId(e.target.value)}
          className="cv-input"
        >
          <option value="">Seleccionar producto...</option>
          {[...productos].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es')).map((p) => (
            <option key={p.id} value={p.id}>{p.codigo_interno} - {p.nombre}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium cv-muted mb-1">Cantidad nueva *</label>
        <input type="number" required min={0} step={0.01} value={cantidadNueva} onChange={(e) => setCantidadNueva(e.target.value)}
          className="cv-input" />
        <p className="text-xs cv-muted mt-1">Se ajustara el stock a esta cantidad exacta</p>
      </div>

      <div>
        <label className="block text-sm font-medium cv-muted mb-1">Motivo *</label>
        <textarea rows={2} required value={motivo} onChange={(e) => setMotivo(e.target.value)}
          placeholder="Ej: Conteo fisico, merma, daño..."
          className="cv-input" />
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t cv-divider">
        <button type="button" onClick={onCancel} className="cv-btn cv-btn-secondary">
          Cancelar
        </button>
        <button type="submit" disabled={saving} className="cv-btn cv-btn-primary">
          {saving ? 'Ajustando...' : 'Ajustar Inventario'}
        </button>
      </div>
    </form>
  );
}
