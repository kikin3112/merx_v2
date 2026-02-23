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
      PENDIENTE: 'bg-yellow-100 text-yellow-700',
      PARCIAL: 'bg-blue-100 text-blue-700',
      PAGADA: 'bg-green-100 text-green-700',
      VENCIDA: 'bg-red-100 text-red-700',
      ANULADA: 'bg-gray-100 text-gray-500',
    };
    return (
      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors[estado] || 'bg-gray-100 text-gray-600'}`}>
        {estado}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Cartera</h1>

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
      <div className="flex items-center gap-4 border-b border-gray-200 overflow-x-auto pb-1">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => { setTab(t); setSelectedItem(null); }}
            className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              tab === t ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Cuentas por {t === 'COBRAR' ? 'Cobrar' : 'Pagar'}
          </button>
        ))}
        <div className="ml-auto">
          <select
            value={filtroEstado}
            onChange={e => setFiltroEstado(e.target.value)}
            className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Todos los estados</option>
            {ESTADOS.filter(e => e).map(e => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-400">Cargando...</div>
      ) : !carteraData?.length ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg mb-1">Sin registros</p>
          <p className="text-sm">Las cuentas por {tab === 'COBRAR' ? 'cobrar' : 'pagar'} se crean automaticamente al facturar</p>
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Documento</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tercero</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Emision</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vencimiento</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Saldo</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {carteraData.map(item => (
                  <tr
                    key={item.id}
                    className={`hover:bg-gray-50 cursor-pointer transition-colors ${isVencida(item) ? 'bg-red-50/50' : ''}`}
                    onClick={() => setSelectedItem(item)}
                  >
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{item.documento_referencia}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{terceroMap[item.tercero_id] || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatDate(item.fecha_emision)}</td>
                    <td className={`px-4 py-3 text-sm ${isVencida(item) ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
                      {formatDate(item.fecha_vencimiento)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(item.valor_total)}</td>
                    <td className="px-4 py-3 text-sm text-right font-medium text-gray-900">{formatCurrency(item.saldo_pendiente)}</td>
                    <td className="px-4 py-3 text-center">{estadoBadge(item)}</td>
                    <td className="px-4 py-3 text-center" onClick={e => e.stopPropagation()}>
                      {['PENDIENTE', 'PARCIAL'].includes(item.estado) && (
                        <button
                          onClick={() => { setSelectedItem(item); setShowPagoModal(true); }}
                          className="text-xs font-medium text-primary-600 hover:text-primary-700"
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
                  { label: 'Vencimiento', value: <span className={isVencida(item) ? 'text-red-600 font-medium' : ''}>{formatDate(item.fecha_vencimiento)}</span> },
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
    blue: 'bg-blue-50 border-blue-200',
    red: 'bg-red-50 border-red-200',
    green: 'bg-green-50 border-green-200',
    amber: 'bg-amber-50 border-amber-200',
  };
  return (
    <div className={`rounded-xl border p-4 ${colors[color] || 'bg-gray-50 border-gray-200'}`}>
      <p className="text-xs font-medium text-gray-500 mb-1">{label}</p>
      <p className="text-xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{sub}</p>
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
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-gray-900">Detalle Cartera</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div><span className="text-gray-500">Documento:</span> <span className="font-medium">{item.documento_referencia}</span></div>
            <div><span className="text-gray-500">Tercero:</span> <span className="font-medium">{terceroNombre}</span></div>
            <div><span className="text-gray-500">Emision:</span> <span>{formatDate(item.fecha_emision)}</span></div>
            <div><span className="text-gray-500">Vencimiento:</span> <span>{formatDate(item.fecha_vencimiento)}</span></div>
            <div><span className="text-gray-500">Total:</span> <span className="font-medium">{formatCurrency(item.valor_total)}</span></div>
            <div><span className="text-gray-500">Saldo:</span> <span className="font-bold text-primary-600">{formatCurrency(item.saldo_pendiente)}</span></div>
          </div>

          {/* Pagos history */}
          {pagos && pagos.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Pagos registrados</h4>
              <div className="space-y-2">
                {pagos.map(p => (
                  <div key={p.id} className="flex items-center justify-between bg-green-50 rounded-lg px-3 py-2 text-sm">
                    <div>
                      <span className="font-medium text-green-700">{formatCurrency(p.valor_pago)}</span>
                      <span className="text-gray-500 ml-2">{formatDate(p.fecha_pago)}</span>
                    </div>
                    {p.numero_referencia && <span className="text-xs text-gray-400">Ref: {p.numero_referencia}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {['PENDIENTE', 'PARCIAL'].includes(item.estado) && (
            <button
              onClick={onRegistrarPago}
              className="w-full py-2.5 rounded-lg bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 transition-colors"
            >
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
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full" onClick={e => e.stopPropagation()}>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-gray-900">Registrar Pago</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="bg-gray-50 rounded-lg p-3 text-sm">
            <p className="font-medium text-gray-900">{item.documento_referencia}</p>
            <p className="text-gray-500">{terceroNombre}</p>
            <p className="text-gray-500">Saldo pendiente: <span className="font-bold text-primary-600">{formatCurrency(item.saldo_pendiente)}</span></p>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Valor del pago *</label>
              <input
                type="number"
                step="0.01"
                min={0.01}
                max={item.saldo_pendiente}
                value={valorPago}
                onChange={e => setValorPago(Number(e.target.value))}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Fecha de pago *</label>
              <input
                type="date"
                value={fechaPago}
                onChange={e => setFechaPago(e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Medio de pago *</label>
              <select
                value={medioPagoId}
                onChange={e => setMedioPagoId(e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {[...(mediosPago ?? [])].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es')).map(m => <option key={m.id} value={m.id}>{m.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Referencia</label>
              <input
                type="text"
                placeholder="No. transferencia, recibo, etc."
                value={referencia}
                onChange={e => setReferencia(e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Observaciones</label>
              <textarea
                rows={2}
                value={observaciones}
                onChange={e => setObservaciones(e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {mutation.isError && (
            <p className="text-sm text-red-600">
              {(mutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error registrando pago'}
            </p>
          )}

          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={() => mutation.mutate()}
              disabled={!valorPago || valorPago <= 0 || valorPago > item.saldo_pendiente || !medioPagoId || mutation.isPending}
              className="flex-1 py-2.5 rounded-lg bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {mutation.isPending ? 'Procesando...' : `Pagar ${formatCurrency(valorPago)}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
