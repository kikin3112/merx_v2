import { HelpPanel } from '../components/tutorial/HelpPanel';
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
        className="border-b cv-divider hover:bg-[var(--cv-elevated)] transition-colors cursor-pointer"
      >
        <td className="px-4 py-3 font-mono text-xs font-medium">
          <span className="inline-flex items-center gap-1.5">
            <svg
              className={`w-3.5 h-3.5 cv-muted transition-transform ${expanded ? 'rotate-90' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            {asiento.numero_asiento}
          </span>
        </td>
        <td className="px-4 py-3 cv-muted">{formatDate(asiento.fecha)}</td>
        <td className="px-4 py-3 cv-muted">{asiento.tipo_asiento}</td>
        <td className="px-4 py-3">{asiento.concepto}</td>
        <td className="px-4 py-3 cv-muted font-mono text-xs">{asiento.documento_referencia || '-'}</td>
        <td className="px-4 py-3 text-right cv-muted font-mono text-xs">{formatCurrency(totalDebito)}</td>
        <td className="px-4 py-3 text-center">
          <span className={`cv-badge ${statusColor(asiento.estado)}`}>{asiento.estado}</span>
        </td>
      </tr>
      {expanded && asiento.detalles && asiento.detalles.length > 0 && (
        <tr>
          <td colSpan={7} className="px-0 py-0">
            <div className="cv-elevated border-y cv-divider px-8 py-3">
              <table className="w-full text-xs">
                <thead>
                  <tr className="cv-muted">
                    <th className="text-left pb-2 font-medium">Codigo</th>
                    <th className="text-left pb-2 font-medium">Cuenta</th>
                    <th className="text-left pb-2 font-medium">Descripcion</th>
                    <th className="text-right pb-2 font-medium">Debito</th>
                    <th className="text-right pb-2 font-medium">Credito</th>
                  </tr>
                </thead>
                <tbody>
                  {asiento.detalles.map((d) => (
                    <tr key={d.id} className="border-t cv-divider">
                      <td className="py-1.5 font-mono cv-muted">{d.cuenta_codigo || '-'}</td>
                      <td className="py-1.5">{d.cuenta_nombre || '-'}</td>
                      <td className="py-1.5 cv-muted">{d.descripcion || '-'}</td>
                      <td className="py-1.5 text-right font-mono cv-muted">
                        {d.debito > 0 ? formatCurrency(d.debito) : '-'}
                      </td>
                      <td className="py-1.5 text-right font-mono cv-muted">
                        {d.credito > 0 ? formatCurrency(d.credito) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t cv-divider font-semibold cv-text">
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
          <span className={`cv-badge ${statusColor(asiento.estado)}`}>{asiento.estado}</span>
        }
        fields={[
          { label: 'Concepto', value: asiento.concepto || '-' },
          { label: 'Total debito', value: formatCurrency(totalDebito) },
          { label: 'Referencia', value: asiento.documento_referencia || '-' },
          { label: 'Total credito', value: formatCurrency(totalCredito) },
        ]}
        onClick={() => setExpanded(!expanded)}
      />
      {expanded && asiento.detalles && asiento.detalles.length > 0 && (
        <div className="mx-2 -mt-1 cv-elevated rounded-b-xl border border-t-0 cv-divider px-4 py-3 space-y-2">
          <p className="cv-label">Detalle lineas</p>
          {asiento.detalles.map((d) => (
            <div key={d.id} className="flex items-start justify-between gap-2 text-xs border-t cv-divider pt-2">
              <div className="min-w-0 flex-1">
                <p className="font-mono cv-muted">{d.cuenta_codigo || '-'}</p>
                <p className="font-medium">{d.cuenta_nombre || '-'}</p>
                {d.descripcion && <p className="cv-muted">{d.descripcion}</p>}
              </div>
              <div className="text-right shrink-0">
                {d.debito > 0 && <p className="font-mono">D: {formatCurrency(d.debito)}</p>}
                {d.credito > 0 && <p className="font-mono">C: {formatCurrency(d.credito)}</p>}
              </div>
            </div>
          ))}
          <div className="flex items-center justify-between text-xs font-semibold cv-text border-t cv-divider pt-2">
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
      <h1 className="font-brand text-xl font-medium cv-text mb-6">Contabilidad</h1>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b cv-divider overflow-x-auto pb-1 whitespace-nowrap">
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
                ? 'border-[var(--cv-primary)] cv-text'
                : 'border-transparent cv-muted'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Asientos */}
      {tab === 'asientos' && (
        <div className="cv-card overflow-hidden">
          {loadingAsientos ? (
            <div className="p-8 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 cv-elevated rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <>
              {/* Desktop table */}
              <div className="hidden md:block">
                <table className="w-full text-sm">
                  <thead className="cv-table-header">
                    <tr>
                      <th className="text-left">Numero</th>
                      <th className="text-left">Fecha</th>
                      <th className="text-left">Tipo</th>
                      <th className="text-left">Concepto</th>
                      <th className="text-left">Referencia</th>
                      <th className="text-right">Valor</th>
                      <th className="text-center">Estado</th>
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
                <div className="text-center py-12 cv-muted">
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
        <div className="cv-card overflow-hidden">
          {loadingBalance ? (
            <div className="p-8 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 cv-elevated rounded-lg animate-pulse" />
              ))}
            </div>
          ) : balance ? (
            <>
              {/* Summary */}
              <div className="flex flex-wrap items-center gap-4 px-4 py-3 cv-elevated border-b cv-divider">
                <div className="flex-1 min-w-[100px]">
                  <span className="text-xs cv-muted">Total Debito</span>
                  <p className="font-semibold cv-text">{formatCurrency(balance.total_debito)}</p>
                </div>
                <div className="flex-1 min-w-[100px]">
                  <span className="text-xs cv-muted">Total Credito</span>
                  <p className="font-semibold cv-text">{formatCurrency(balance.total_credito)}</p>
                </div>
                <div className="flex-1 min-w-[100px]">
                  <span className={`cv-badge ${balance.balanceado ? 'cv-badge-positive' : 'cv-badge-negative'}`}>
                    {balance.balanceado ? 'Balanceado' : `Diferencia: ${formatCurrency(balance.diferencia)}`}
                  </span>
                </div>
              </div>

              {/* Desktop table */}
              <div className="hidden md:block">
                <table className="w-full text-sm">
                  <thead className="cv-table-header">
                    <tr>
                      <th className="text-left">Codigo</th>
                      <th className="text-left">Cuenta</th>
                      <th className="text-left">Tipo</th>
                      <th className="text-right">Debito</th>
                      <th className="text-right">Credito</th>
                      <th className="text-right">Saldo</th>
                    </tr>
                  </thead>
                  <tbody className="cv-table-body">
                    {balance.cuentas.map((c) => (
                      <tr key={c.cuenta_id}>
                        <td className="font-mono text-xs font-medium">{c.codigo}</td>
                        <td>{c.nombre}</td>
                        <td className="text-xs cv-muted">{c.tipo_cuenta}</td>
                        <td className="text-right cv-muted">{formatCurrency(c.total_debito)}</td>
                        <td className="text-right cv-muted">{formatCurrency(c.total_credito)}</td>
                        <td className={`text-right font-semibold ${c.saldo >= 0 ? '' : 'cv-negative'}`}>
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
                      <span className={`cv-badge font-mono ${c.saldo >= 0 ? 'cv-badge-neutral' : 'cv-badge-negative'}`}>
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
                <div className="text-center py-12 cv-muted">
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
        <div className="cv-card overflow-hidden">
          {loadingConfigs ? (
            <div className="p-8 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 cv-elevated rounded-lg animate-pulse" />
              ))}
            </div>
          ) : configs && configs.length > 0 ? (
            <>
              <div className="px-4 py-3 cv-elevated border-b cv-divider">
                <p className="text-sm cv-muted">
                  Cuentas configuradas para asientos automaticos
                </p>
              </div>
              <table className="w-full text-sm">
                <thead className="cv-table-header">
                  <tr>
                    <th className="text-left">Concepto</th>
                    <th className="text-left">Cuenta Debito</th>
                    <th className="text-left">Cuenta Credito</th>
                    <th className="text-left">Descripcion</th>
                  </tr>
                </thead>
                <tbody className="cv-table-body">
                  {configs.map((c) => (
                    <tr key={c.id}>
                      <td className="font-medium">{c.concepto}</td>
                      <td className="cv-muted">
                        {c.cuenta_debito_codigo ? `${c.cuenta_debito_codigo} - ${c.cuenta_debito_nombre}` : '-'}
                      </td>
                      <td className="cv-muted">
                        {c.cuenta_credito_codigo ? `${c.cuenta_credito_codigo} - ${c.cuenta_credito_nombre}` : '-'}
                      </td>
                      <td className="text-xs cv-muted">{c.descripcion || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <div className="text-center py-12 px-4">
              <p className="text-lg mb-2 cv-muted">Configuracion contable no inicializada</p>
              <p className="text-sm cv-muted mb-4">
                Inicializa las cuentas contables para habilitar la contabilidad automatica
              </p>
              <button
                onClick={() => inicializarMutation.mutate()}
                disabled={inicializarMutation.isPending}
                className="cv-btn cv-btn-primary"
              >
                {inicializarMutation.isPending ? 'Inicializando...' : 'Inicializar Configuracion'}
              </button>
              {inicializarMutation.isError && (
                <p className="mt-3 text-sm cv-negative">
                  Error al inicializar. Intenta de nuevo.
                </p>
              )}
            </div>
          )}
        </div>
      )}
      <HelpPanel modulo="contabilidad" />
    </div>
  );
}
