import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contabilidad, configuracionContable } from '../api/endpoints';
import { formatCurrency, formatDate, statusColor } from '../utils/format';
import DataCard from '../components/ui/DataCard';
import type { AsientoContable, BalancePrueba, ConfiguracionContable } from '../types';

function AsientoRow({ asiento }: { asiento: AsientoContable }) {
  const [expanded, setExpanded] = useState(false);

  const totalDebito = asiento.detalles?.reduce((sum, d) => sum + d.debito, 0) ?? 0;
  const totalCredito = asiento.detalles?.reduce((sum, d) => sum + d.credito, 0) ?? 0;

  return (
    <>
      <tr
        onClick={() => setExpanded(!expanded)}
        className="border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer"
      >
        <td className="px-4 py-3 font-mono text-xs font-medium text-gray-900">
          <span className="inline-flex items-center gap-1.5">
            <svg
              className={`w-3.5 h-3.5 text-gray-400 transition-transform ${expanded ? 'rotate-90' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            {asiento.numero_asiento}
          </span>
        </td>
        <td className="px-4 py-3 text-gray-600">{formatDate(asiento.fecha)}</td>
        <td className="px-4 py-3 text-gray-600">{asiento.tipo_asiento}</td>
        <td className="px-4 py-3 text-gray-900">{asiento.concepto}</td>
        <td className="px-4 py-3 text-gray-500 font-mono text-xs">{asiento.documento_referencia || '-'}</td>
        <td className="px-4 py-3 text-right text-gray-600 font-mono text-xs">{formatCurrency(totalDebito)}</td>
        <td className="px-4 py-3 text-center">
          <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(asiento.estado)}`}>
            {asiento.estado}
          </span>
        </td>
      </tr>
      {expanded && asiento.detalles && asiento.detalles.length > 0 && (
        <tr>
          <td colSpan={7} className="px-0 py-0">
            <div className="bg-gray-50 border-y border-gray-100 px-8 py-3">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-500">
                    <th className="text-left pb-2 font-medium">Codigo</th>
                    <th className="text-left pb-2 font-medium">Cuenta</th>
                    <th className="text-left pb-2 font-medium">Descripcion</th>
                    <th className="text-right pb-2 font-medium">Debito</th>
                    <th className="text-right pb-2 font-medium">Credito</th>
                  </tr>
                </thead>
                <tbody>
                  {asiento.detalles.map((d) => (
                    <tr key={d.id} className="border-t border-gray-100">
                      <td className="py-1.5 font-mono text-gray-700">{d.cuenta_codigo || '-'}</td>
                      <td className="py-1.5 text-gray-900">{d.cuenta_nombre || '-'}</td>
                      <td className="py-1.5 text-gray-500">{d.descripcion || '-'}</td>
                      <td className="py-1.5 text-right font-mono text-gray-700">
                        {d.debito > 0 ? formatCurrency(d.debito) : '-'}
                      </td>
                      <td className="py-1.5 text-right font-mono text-gray-700">
                        {d.credito > 0 ? formatCurrency(d.credito) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t border-gray-200 font-semibold text-gray-900">
                    <td colSpan={3} className="py-1.5 text-right">Totales:</td>
                    <td className="py-1.5 text-right font-mono">{formatCurrency(totalDebito)}</td>
                    <td className="py-1.5 text-right font-mono">{formatCurrency(totalCredito)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function AsientoMobileCard({ asiento }: { asiento: AsientoContable }) {
  const [expanded, setExpanded] = useState(false);

  const totalDebito = asiento.detalles?.reduce((sum, d) => sum + d.debito, 0) ?? 0;
  const totalCredito = asiento.detalles?.reduce((sum, d) => sum + d.credito, 0) ?? 0;

  return (
    <div>
      <DataCard
        title={`Asiento #${asiento.numero_asiento}`}
        subtitle={`${formatDate(asiento.fecha)} · ${asiento.tipo_asiento}`}
        badge={
          <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(asiento.estado)}`}>
            {asiento.estado}
          </span>
        }
        fields={[
          { label: 'Concepto', value: asiento.concepto || '-' },
          { label: 'Total Debito', value: formatCurrency(totalDebito) },
          { label: 'Referencia', value: asiento.documento_referencia || '-' },
          { label: 'Total Credito', value: formatCurrency(totalCredito) },
        ]}
        onClick={() => setExpanded(!expanded)}
      />
      {expanded && asiento.detalles && asiento.detalles.length > 0 && (
        <div className="mx-2 -mt-1 bg-gray-50 rounded-b-xl border border-t-0 border-gray-200 px-4 py-3 space-y-2">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Detalle lineas</p>
          {asiento.detalles.map((d) => (
            <div key={d.id} className="flex items-start justify-between gap-2 text-xs border-t border-gray-100 pt-2">
              <div className="min-w-0 flex-1">
                <p className="font-mono text-gray-700">{d.cuenta_codigo || '-'}</p>
                <p className="text-gray-900 font-medium">{d.cuenta_nombre || '-'}</p>
                {d.descripcion && <p className="text-gray-500">{d.descripcion}</p>}
              </div>
              <div className="text-right shrink-0">
                {d.debito > 0 && <p className="text-gray-700 font-mono">D: {formatCurrency(d.debito)}</p>}
                {d.credito > 0 && <p className="text-gray-700 font-mono">C: {formatCurrency(d.credito)}</p>}
              </div>
            </div>
          ))}
          <div className="flex items-center justify-between text-xs font-semibold text-gray-900 border-t border-gray-200 pt-2">
            <span>Totales</span>
            <div className="text-right font-mono">
              <span className="mr-3">D: {formatCurrency(totalDebito)}</span>
              <span>C: {formatCurrency(totalCredito)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ContabilidadPage() {
  const [tab, setTab] = useState<'asientos' | 'balance' | 'configuracion'>('asientos');
  const queryClient = useQueryClient();

  const { data: asientos, isLoading: loadingAsientos } = useQuery<AsientoContable[]>({
    queryKey: ['asientos'],
    queryFn: () => contabilidad.asientos().then((r) => r.data),
    enabled: tab === 'asientos',
  });

  const { data: balance, isLoading: loadingBalance } = useQuery<BalancePrueba>({
    queryKey: ['balance-prueba'],
    queryFn: () => contabilidad.balancePrueba().then((r) => r.data),
    enabled: tab === 'balance',
  });

  const { data: configs, isLoading: loadingConfigs } = useQuery<ConfiguracionContable[]>({
    queryKey: ['configuracion-contable'],
    queryFn: () => configuracionContable.list().then((r) => r.data),
    enabled: tab === 'configuracion',
  });

  const inicializarMutation = useMutation({
    mutationFn: () => configuracionContable.inicializar(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configuracion-contable'] });
    },
  });

  return (
    <div>
      <h1 className="text-xl font-bold text-gray-900 mb-6">Contabilidad</h1>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-gray-200 overflow-x-auto pb-1 whitespace-nowrap">
        {[
          { id: 'asientos' as const, label: 'Asientos Contables' },
          { id: 'balance' as const, label: 'Balance de Prueba' },
          { id: 'configuracion' as const, label: 'Configuracion' },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t.id
                ? 'border-primary-500 text-primary-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Asientos */}
      {tab === 'asientos' && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loadingAsientos ? (
            <div className="p-8 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-gray-200 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <>
              {/* Desktop table */}
              <div className="hidden md:block">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50">
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Numero</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Fecha</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Tipo</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Concepto</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Referencia</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-500">Valor</th>
                      <th className="text-center px-4 py-3 font-medium text-gray-500">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {asientos?.map((a) => (
                      <AsientoRow key={a.id} asiento={a} />
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile cards */}
              <div className="md:hidden space-y-3 p-3">
                {asientos?.map((a) => (
                  <AsientoMobileCard key={a.id} asiento={a} />
                ))}
              </div>

              {asientos?.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg mb-2">Sin asientos contables</p>
                  <p className="text-sm">Los asientos se crean automaticamente al emitir facturas</p>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Balance de Prueba */}
      {tab === 'balance' && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loadingBalance ? (
            <div className="p-8 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-gray-200 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : balance ? (
            <>
              {/* Summary */}
              <div className="flex flex-wrap items-center gap-4 px-4 py-3 bg-gray-50 border-b border-gray-100">
                <div className="flex-1 min-w-[100px]">
                  <span className="text-xs text-gray-500">Total Debito</span>
                  <p className="font-semibold text-gray-900">{formatCurrency(balance.total_debito)}</p>
                </div>
                <div className="flex-1 min-w-[100px]">
                  <span className="text-xs text-gray-500">Total Credito</span>
                  <p className="font-semibold text-gray-900">{formatCurrency(balance.total_credito)}</p>
                </div>
                <div className="flex-1 min-w-[100px]">
                  <span
                    className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${
                      balance.balanceado
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {balance.balanceado ? 'Balanceado' : `Diferencia: ${formatCurrency(balance.diferencia)}`}
                  </span>
                </div>
              </div>

              {/* Desktop table */}
              <div className="hidden md:block">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50">
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Codigo</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Cuenta</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Tipo</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-500">Debito</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-500">Credito</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-500">Saldo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {balance.cuentas.map((c) => (
                      <tr key={c.cuenta_id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-mono text-xs font-medium text-gray-900">{c.codigo}</td>
                        <td className="px-4 py-3 text-gray-900">{c.nombre}</td>
                        <td className="px-4 py-3 text-gray-500 text-xs">{c.tipo_cuenta}</td>
                        <td className="px-4 py-3 text-right text-gray-600">{formatCurrency(c.total_debito)}</td>
                        <td className="px-4 py-3 text-right text-gray-600">{formatCurrency(c.total_credito)}</td>
                        <td className={`px-4 py-3 text-right font-semibold ${c.saldo >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                          {formatCurrency(c.saldo)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile cards */}
              <div className="md:hidden space-y-3 p-3">
                {balance.cuentas.map((c) => (
                  <DataCard
                    key={c.cuenta_id}
                    title={c.nombre}
                    subtitle={`${c.codigo} · ${c.tipo_cuenta}`}
                    badge={
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold font-mono ${
                        c.saldo >= 0 ? 'bg-gray-100 text-gray-900' : 'bg-red-100 text-red-700'
                      }`}>
                        {formatCurrency(c.saldo)}
                      </span>
                    }
                    fields={[
                      { label: 'Debito', value: formatCurrency(c.total_debito) },
                      { label: 'Credito', value: formatCurrency(c.total_credito) },
                    ]}
                  />
                ))}
              </div>

              {balance.cuentas.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg mb-2">Sin movimientos contables</p>
                  <p className="text-sm">Emite facturas para generar asientos automaticos</p>
                </div>
              )}
            </>
          ) : null}
        </div>
      )}

      {/* Configuracion Contable */}
      {tab === 'configuracion' && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loadingConfigs ? (
            <div className="p-8 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-gray-200 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : configs && configs.length > 0 ? (
            <>
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
                <p className="text-sm text-gray-600">
                  Cuentas configuradas para asientos automaticos
                </p>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Concepto</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Cuenta Debito</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Cuenta Credito</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Descripcion</th>
                  </tr>
                </thead>
                <tbody>
                  {configs.map((c) => (
                    <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-medium text-gray-900">{c.concepto}</td>
                      <td className="px-4 py-3 text-gray-600">
                        {c.cuenta_debito_codigo ? `${c.cuenta_debito_codigo} - ${c.cuenta_debito_nombre}` : '-'}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {c.cuenta_credito_codigo ? `${c.cuenta_credito_codigo} - ${c.cuenta_credito_nombre}` : '-'}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{c.descripcion || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <div className="text-center py-12 px-4">
              <p className="text-lg mb-2 text-gray-600">Configuracion contable no inicializada</p>
              <p className="text-sm text-gray-400 mb-4">
                Inicializa las cuentas contables para habilitar la contabilidad automatica
              </p>
              <button
                onClick={() => inicializarMutation.mutate()}
                disabled={inicializarMutation.isPending}
                className="inline-flex items-center px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {inicializarMutation.isPending ? 'Inicializando...' : 'Inicializar Configuracion'}
              </button>
              {inicializarMutation.isError && (
                <p className="mt-3 text-sm text-red-600">
                  Error al inicializar. Intenta de nuevo.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
