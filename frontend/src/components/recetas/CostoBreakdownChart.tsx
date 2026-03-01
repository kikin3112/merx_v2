import { formatCurrency } from '../../utils/format';
import type { RecetaCosto } from '../../types';

interface Props {
  costo: RecetaCosto;
}

export function CostoBreakdownChart({ costo }: Props) {
  const total = costo.costo_total || 1;
  const pctIng = Math.round((costo.costo_ingredientes / total) * 100);
  const pctMO = Math.round((costo.costo_mano_obra / total) * 100);
  const pctInd = Math.round((costo.costo_indirecto / total) * 100);

  const segments = [
    { label: 'Ingredientes', valor: costo.costo_ingredientes, pct: pctIng, color: 'bg-amber-400' },
    { label: 'Mano de obra', valor: costo.costo_mano_obra, pct: pctMO, color: 'bg-violet-400' },
    { label: 'Gastos adicionales', valor: costo.costo_indirecto, pct: pctInd, color: 'bg-teal-400' },
  ].filter((s) => s.valor > 0);

  return (
    <div className="space-y-3">
      {/* Barra horizontal stacked */}
      <div className="flex rounded-full overflow-hidden h-4 bg-gray-100">
        {segments.map((s) => (
          <div
            key={s.label}
            className={`${s.color} transition-all`}
            style={{ width: `${s.pct}%` }}
            title={`${s.label}: ${s.pct}%`}
          />
        ))}
      </div>

      {/* Leyenda */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {segments.map((s) => (
          <div key={s.label} className="flex items-start gap-2">
            <div className={`w-3 h-3 rounded-sm mt-0.5 flex-shrink-0 ${s.color}`} />
            <div>
              <p className="text-xs text-gray-500">{s.label}</p>
              <p className="text-sm font-semibold text-gray-900">{formatCurrency(s.valor)}</p>
              <p className="text-xs text-gray-400">{s.pct}%</p>
            </div>
          </div>
        ))}
      </div>

      {/* Totales clave */}
      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-100">
        <div className="bg-gray-50 rounded-lg p-2.5">
          <p className="text-xs text-gray-500">Costo unitario</p>
          <p className="text-base font-bold text-gray-900">{formatCurrency(costo.costo_unitario)}</p>
          <p className="text-xs text-gray-400">por unidad producida</p>
        </div>
        <div className={`rounded-lg p-2.5 ${
          costo.margen_actual_porcentaje >= 50 ? 'bg-green-50' :
          costo.margen_actual_porcentaje >= 30 ? 'bg-yellow-50' : 'bg-red-50'
        }`}>
          <p className="text-xs text-gray-500">Margen actual</p>
          <p className={`text-base font-bold ${
            costo.margen_actual_porcentaje >= 50 ? 'text-green-700' :
            costo.margen_actual_porcentaje >= 30 ? 'text-yellow-700' : 'text-red-700'
          }`}>{costo.margen_actual_porcentaje.toFixed(1)}%</p>
          <p className="text-xs text-gray-400">sobre precio de venta</p>
        </div>
      </div>

      {costo.precio_sugerido && costo.margen_objetivo && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center justify-between">
          <div>
            <p className="text-xs text-amber-700 font-medium">Tu Socia te sugiere</p>
            <p className="text-lg font-bold text-amber-900">{formatCurrency(costo.precio_sugerido)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-amber-600">Para ganar el {costo.margen_objetivo}%</p>
            <p className="text-xs text-amber-500">de cada venta</p>
          </div>
        </div>
      )}
    </div>
  );
}
