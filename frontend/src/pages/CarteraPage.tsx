import { HelpPanel } from '../components/tutorial/HelpPanel';
import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cartera, terceros } from '../api/endpoints';
import { formatCurrency, formatDate } from '../utils/format';
import DataCard from '../components/ui/DataCard';
import type { CarteraItem, Tercero, MedioPago } from '../types';

const ESTADOS = ['', 'PENDIENTE', 'PARCIAL', 'PAGADA', 'VENCIDA', 'ANULADA'];
const TABS = ['COBRAR', 'PAGAR'] as const;

export default function CarteraPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'COBRAR' | 'PAGAR'>('COBRAR');
  const [filtroEstado, setFiltroEstado] = useState('');
  const [selectedItem, setSelectedItem] = useState<CarteraItem | null>(null);
  const [showPagoModal, setShowPagoModal] = useState(false);

  const { data: carteraData, isLoading } = useQuery({
    queryKey: ['cartera', tab, filtroEstado],
    queryFn: () => cartera.list({
      tipo_cartera: tab,
      ...(filtroEstado ? { estado: filtroEstado } : {}),
    }).then(r => r.data),
  });

  const { data: resumen } = useQuery({
    queryKey: ['cartera-resumen'],
    queryFn: () => cartera.resumen().then(r => r.data),
  });

  const { data: tercerosData } = useQuery<Tercero[]>({
    queryKey: ['terceros'],
    queryFn: () => terceros.list().then(r => r.data),
  });

  const terceroMap = useMemo(() => {
    const map: Record<string, string> = {};
    tercerosData?.forEach(t => { map[t.id] = t.nombre; });
    return map;
  }, [tercerosData]);

  const hoy = new Date().toISOString().split('T')[0];

  const isVencida = (item: CarteraItem) => {
    return item.fecha_vencimiento < hoy && ['PENDIENTE', 'PARCIAL'].includes(item.estado);
  };

  const estadoBadge = (item: CarteraItem) => {
    const vencida = isVencida(item);
    const estado = vencida ? 'VENCIDA' : item.estado;
    const colors: Record<string, string> = {
      PENDIENTE: 'cv-badge-accent',
      PARCIAL: 'cv-badge-primary',
      PAGADA: 'cv-badge-positive',
      VENCIDA: 'cv-badge-negative',
      ANULADA: 'cv-badge-neutral',
    };
    return (
      <span className={`cv-badge ${colors[estado] || 'cv-badge-neutral'}`}>{estado}</span>
    );
  };

  return (
    <div className="space-y-6">
      <h1 className="font-brand text-2xl font-medium cv-text">Cartera</h1>

      {/* Summary cards */}
      {resumen && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard label="Por cobrar" value={formatCurrency(resumen.total_por_cobrar)} sub={`${resumen.cantidad_pendientes} pendientes`} color="blue" />
          <SummaryCard label="Vencido" value={formatCurrency(resumen.total_vencido)} sub={`${resumen.cantidad_vencidas} vencidas`} color="red" />
          <SummaryCard label="Al dia" value={formatCurrency(resumen.total_por_cobrar - resumen.total_vencido)} sub="Sin vencer" color="green" />
          <SummaryCard label="% Vencido" value={resumen.total_por_cobrar > 0 ? `${((resumen.total_vencido / resumen.total_por_cobrar) * 100).toFixed(1)}%` : '0%'} sub="Del total" color="amber" />
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-4 border-b cv-divider overflow-x-auto pb-1">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => { setTab(t); setSelectedItem(null); }}
            className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              tab === t ? 'border-primary-500 text-primary-600' : 'border-transparent cv-muted'
            }`}
          >
            Cuentas por {t === 'COBRAR' ? 'Cobrar' : 'Pagar'}
          </button>
        ))}
        <div className="ml-auto">
          <select
            value={filtroEstado}
            onChange={e => setFiltroEstado(e.target.value)}
            className="cv-input w-auto"
          >
            <option value="">Todos los estados</option>
            {ESTADOS.filter(e => e).map(e => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-center py-8 cv-muted">Cargando...</div>
      ) : !carteraData?.length ? (
        <div className="text-center py-12 cv-muted">
          <p className="text-lg mb-1">Sin registros</p>
          <p className="text-sm">Las cuentas por {tab === 'COBRAR' ? 'cobrar' : 'pagar'} se crean automaticamente al facturar</p>
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block cv-card overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="cv-table-header">
                <tr>
                  <th className="text-left">Documento</th>
                  <th className="text-left">Tercero</th>
                  <th className="text-left">Emision</th>
                  <th className="text-left">Vencimiento</th>
                  <th className="text-right">Total</th>
                  <th className="text-right">Saldo</th>
                  <th className="text-center">Estado</th>
                  <th className="text-center">Acciones</th>
                </tr>
              </thead>
              <tbody className="cv-table-body">
                {carteraData.map(item => (
                  <tr
                    key={item.id}
                    className={`cursor-pointer ${isVencida(item) ? 'bg-[var(--cv-negative-dim)]' : ''}`}
                    onClick={() => setSelectedItem(item)}
                  >
                    <td className="font-medium">{item.documento_referencia}</td>
                    <td className="cv-muted">{terceroMap[item.tercero_id] || '-'}</td>
                    <td className="cv-muted">{formatDate(item.fecha_emision)}</td>
                    <td className={isVencida(item) ? 'cv-negative font-medium' : 'cv-muted'}>
                      {formatDate(item.fecha_vencimiento)}
                    </td>
                    <td className="text-right">{formatCurrency(item.valor_total)}</td>
                    <td className="text-right font-medium">{formatCurrency(item.saldo_pendiente)}</td>
                    <td className="text-center">{estadoBadge(item)}</td>
                    <td className="text-center" onClick={e => e.stopPropagation()}>
                      {['PENDIENTE', 'PARCIAL'].includes(item.estado) && (
                        <button
                          onClick={() => { setSelectedItem(item); setShowPagoModal(true); }}
                          className="text-xs font-medium text-primary-600 hover:text-primary-800"
                        >
                          Registrar pago
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {carteraData.map(item => (
              <DataCard
                key={item.id}
                title={item.documento_referencia}
                subtitle={terceroMap[item.tercero_id] || '-'}
                badge={estadoBadge(item)}
                fields={[
                  { label: 'Total', value: formatCurrency(item.valor_total) },
                  { label: 'Saldo', value: <span className="font-bold text-primary-600">{formatCurrency(item.saldo_pendiente)}</span> },
                  { label: 'Vencimiento', value: <span className={isVencida(item) ? 'cv-negative font-medium' : ''}>{formatDate(item.fecha_vencimiento)}</span> },
                ]}
                onClick={() => setSelectedItem(item)}
                actions={
                  ['PENDIENTE', 'PARCIAL'].includes(item.estado) ? (
                    <button
                      onClick={() => { setSelectedItem(item); setShowPagoModal(true); }}
                      className="text-xs font-medium text-primary-600 hover:text-primary-700"
                    >
                      Registrar pago
                    </button>
                  ) : undefined
                }
              />
            ))}
          </div>
        </>
      )}

      {/* Detail panel */}
      {selectedItem && !showPagoModal && (
        <DetailPanel
          item={selectedItem}
          terceroNombre={terceroMap[selectedItem.tercero_id] || '-'}
          onClose={() => setSelectedItem(null)}
          onRegistrarPago={() => setShowPagoModal(true)}
        />
      )}

      {/* Pago modal */}
      {showPagoModal && selectedItem && (
        <PagoModal
          item={selectedItem}
          terceroNombre={terceroMap[selectedItem.tercero_id] || '-'}
          onClose={() => { setShowPagoModal(false); }}
          onSuccess={() => {
            setShowPagoModal(false);
            setSelectedItem(null);
            queryClient.invalidateQueries({ queryKey: ['cartera'] });
            queryClient.invalidateQueries({ queryKey: ['cartera-resumen'] });
          }}
        />
      )}
    </div>
  );
}

function SummaryCard({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
  const colors: Record<string, string> = {
    blue: 'bg-[var(--cv-primary-dim)] border-[var(--cv-primary)]',
    red: 'bg-[var(--cv-negative-dim)] border-[var(--cv-negative)]',
    green: 'bg-[var(--cv-positive-dim)] border-[var(--cv-positive)]',
    amber: 'bg-[var(--cv-accent-dim)] border-[var(--cv-accent)]',
  };
  return (
    <div className={`rounded-xl border p-4 ${colors[color] || 'cv-card'}`}>
      <p className="text-xs font-medium cv-muted mb-1">{label}</p>
      <p className="text-xl font-bold cv-text">{value}</p>
      <p className="text-xs cv-muted mt-0.5">{sub}</p>
    </div>
  );
}

function DetailPanel({ item, terceroNombre, onClose, onRegistrarPago }: {
  item: CarteraItem;
  terceroNombre: string;
  onClose: () => void;
  onRegistrarPago: () => void;
}) {
  const { data: pagos } = useQuery({
    queryKey: ['cartera-pagos', item.id],
    queryFn: () => cartera.pagos(item.id).then(r => r.data),
  });

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="cv-card shadow-xl max-w-lg w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold cv-text">Detalle Cartera</h3>
            <button onClick={onClose} className="cv-icon-btn p-1">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div><span className="cv-muted">Documento:</span> <span className="font-medium">{item.documento_referencia}</span></div>
            <div><span className="cv-muted">Tercero:</span> <span className="font-medium">{terceroNombre}</span></div>
            <div><span className="cv-muted">Emision:</span> <span>{formatDate(item.fecha_emision)}</span></div>
            <div><span className="cv-muted">Vencimiento:</span> <span>{formatDate(item.fecha_vencimiento)}</span></div>
            <div><span className="cv-muted">Total:</span> <span className="font-medium">{formatCurrency(item.valor_total)}</span></div>
            <div><span className="cv-muted">Saldo:</span> <span className="font-bold text-primary-600">{formatCurrency(item.saldo_pendiente)}</span></div>
          </div>

          {/* Pagos history */}
          {pagos && pagos.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold cv-text mb-2">Pagos registrados</h4>
              <div className="space-y-2">
                {pagos.map(p => (
                  <div key={p.id} className="flex items-center justify-between bg-[var(--cv-positive-dim)] rounded-lg px-3 py-2 text-sm">
                    <div>
                      <span className="font-medium cv-positive">{formatCurrency(p.valor_pago)}</span>
                      <span className="cv-muted ml-2">{formatDate(p.fecha_pago)}</span>
                    </div>
                    {p.numero_referencia && <span className="text-xs cv-muted">Ref: {p.numero_referencia}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {['PENDIENTE', 'PARCIAL'].includes(item.estado) && (
            <button onClick={onRegistrarPago} className="cv-btn cv-btn-primary w-full">
              Registrar Pago
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function PagoModal({ item, terceroNombre, onClose, onSuccess }: {
  item: CarteraItem;
  terceroNombre: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [valorPago, setValorPago] = useState(item.saldo_pendiente);
  const [fechaPago, setFechaPago] = useState(new Date().toISOString().split('T')[0]);
  const [medioPagoId, setMedioPagoId] = useState('');
  const [referencia, setReferencia] = useState('');
  const [observaciones, setObservaciones] = useState('');

  const { data: mediosPago } = useQuery<MedioPago[]>({
    queryKey: ['medios-pago'],
    queryFn: () => cartera.mediosPago().then(r => r.data),
  });

  // Auto-select first medio pago
  if (mediosPago?.length && !medioPagoId) {
    setMedioPagoId(mediosPago[0].id);
  }

  const mutation = useMutation({
    mutationFn: () =>
      cartera.registrarPago(item.id, {
        cartera_id: item.id,
        fecha_pago: fechaPago,
        valor_pago: valorPago,
        medio_pago_id: medioPagoId,
        numero_referencia: referencia || undefined,
        observaciones: observaciones || undefined,
      }),
    onSuccess,
  });

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="cv-card shadow-xl max-w-md w-full" onClick={e => e.stopPropagation()}>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold cv-text">Registrar Pago</h3>
            <button onClick={onClose} className="cv-icon-btn p-1">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="cv-elevated rounded-lg p-3 text-sm">
            <p className="font-medium cv-text">{item.documento_referencia}</p>
            <p className="cv-muted">{terceroNombre}</p>
            <p className="cv-muted">Saldo pendiente: <span className="font-bold text-[var(--cv-primary)]">{formatCurrency(item.saldo_pendiente)}</span></p>
          </div>

          <div className="space-y-3">
            <div>
              <label className="cv-label mb-1">Valor del pago *</label>
              <input
                type="number"
                step="0.01"
                min={0.01}
                max={item.saldo_pendiente}
                value={valorPago}
                onChange={e => setValorPago(Number(e.target.value))}
                className="cv-input"
              />
            </div>
            <div>
              <label className="cv-label mb-1">Fecha de pago *</label>
              <input
                type="date"
                value={fechaPago}
                onChange={e => setFechaPago(e.target.value)}
                className="cv-input"
              />
            </div>
            <div>
              <label className="cv-label mb-1">Medio de pago *</label>
              <select
                value={medioPagoId}
                onChange={e => setMedioPagoId(e.target.value)}
                className="cv-input"
              >
                {[...(mediosPago ?? [])].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es')).map(m => <option key={m.id} value={m.id}>{m.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="cv-label mb-1">Referencia</label>
              <input
                type="text"
                placeholder="No. transferencia, recibo, etc."
                value={referencia}
                onChange={e => setReferencia(e.target.value)}
                className="cv-input"
              />
            </div>
            <div>
              <label className="cv-label mb-1">Observaciones</label>
              <textarea
                rows={2}
                value={observaciones}
                onChange={e => setObservaciones(e.target.value)}
                className="cv-input"
              />
            </div>
          </div>

          {mutation.isError && (
            <p className="text-sm cv-negative">
              {(mutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error registrando pago'}
            </p>
          )}

          <div className="flex gap-3">
            <button onClick={onClose} className="cv-btn cv-btn-secondary flex-1">
              Cancelar
            </button>
            <button
              onClick={() => mutation.mutate()}
              disabled={!valorPago || valorPago <= 0 || valorPago > item.saldo_pendiente || !medioPagoId || mutation.isPending}
              className="cv-btn cv-btn-primary flex-1"
            >
              {mutation.isPending ? 'Procesando...' : `Pagar ${formatCurrency(valorPago)}`}
            </button>
          </div>
        </div>
      </div>
      <HelpPanel modulo="cartera" />
    </div>
  );
}
