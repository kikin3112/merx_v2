import { formatCurrency } from '../../utils/format';
import type { RecetaCosto, CostoEstandar } from '../../types';

interface Props {
  costo: RecetaCosto;
  costoEstandar?: CostoEstandar | null;
  onFijarCosto?: () => void;
  fijarLoading?: boolean;
}

export function CostoBreakdownChart({ costo: raw, costoEstandar, onFijarCosto, fijarLoading }: Props) {
  const c = {
    costo_material_directo: Number(raw.costo_material_directo ?? raw.costo_ingredientes ?? 0),
    costo_mano_obra_directa: Number(raw.costo_mano_obra_directa ?? raw.costo_mano_obra ?? 0),
    costo_primo: Number(raw.costo_primo ?? 0),
    costo_conversion: Number(raw.costo_conversion ?? 0),
    costo_indirecto: Number(raw.costo_indirecto ?? 0),
    costo_total: Number(raw.costo_total ?? 0),
    costo_unitario: Number(raw.costo_unitario ?? 0),
    margen_actual_porcentaje: Number(raw.margen_actual_porcentaje ?? 0),
    precio_sugerido: raw.precio_sugerido != null ? Number(raw.precio_sugerido) : null,
    margen_objetivo: raw.margen_objetivo != null ? Number(raw.margen_objetivo) : null,
    lotes_posibles_con_stock: raw.lotes_posibles_con_stock ?? 0,
    ingrediente_critico: raw.ingrediente_critico ?? null,
  };

  const total = c.costo_total || 1;
  const pctMat = Math.round((c.costo_material_directo / total) * 100);
  const pctMO = Math.round((c.costo_mano_obra_directa / total) * 100);
  const pctInd = Math.round((c.costo_indirecto / total) * 100);

  const segments = [
    { label: 'Material directo', valor: c.costo_material_directo, pct: pctMat, color: 'bg-amber-400' },
    { label: 'Mano de obra', valor: c.costo_mano_obra_directa, pct: pctMO, color: 'bg-violet-400' },
    { label: 'Gastos adicionales', valor: c.costo_indirecto, pct: pctInd, color: 'bg-teal-400' },
  ].filter((s) => s.valor > 0);

  // Diferencia vs costo estándar
  const diferenciaPct = costoEstandar
    ? ((c.costo_unitario - Number(costoEstandar.costo_unitario)) / Number(costoEstandar.costo_unitario)) * 100
    : null;

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

      {/* Estructura profesional */}
      <div className="bg-gray-50 rounded-lg p-3 space-y-1.5 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">Costo Primo (MD + MOD)</span>
          <span className="font-semibold">{formatCurrency(c.costo_primo)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Gastos adicionales (CIF)</span>
          <span className="font-semibold">{formatCurrency(c.costo_indirecto)}</span>
        </div>
        <div className="flex justify-between border-t border-gray-200 pt-1.5 font-bold">
          <span>Costo Total Manufactura</span>
          <span>{formatCurrency(c.costo_total)}</span>
        </div>
      </div>

      {/* Cobertura de stock */}
      {c.lotes_posibles_con_stock !== undefined && (
        <div className={`rounded-lg px-3 py-2 flex items-center justify-between text-sm ${
          c.lotes_posibles_con_stock === 0 ? 'bg-red-50 border border-red-200' :
          c.lotes_posibles_con_stock <= 2 ? 'bg-yellow-50 border border-yellow-200' :
          'bg-green-50 border border-green-200'
        }`}>
          <span className={`font-medium ${
            c.lotes_posibles_con_stock === 0 ? 'text-red-700' :
            c.lotes_posibles_con_stock <= 2 ? 'text-yellow-700' : 'text-green-700'
          }`}>
            {c.lotes_posibles_con_stock === 0
              ? `Sin stock${c.ingrediente_critico ? ` — falta: ${c.ingrediente_critico}` : ''}`
              : `${c.lotes_posibles_con_stock} lote${c.lotes_posibles_con_stock !== 1 ? 's' : ''} posible${c.lotes_posibles_con_stock !== 1 ? 's' : ''} con stock actual`}
          </span>
        </div>
      )}

      {/* Totales clave */}
      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-100">
        <div className="bg-gray-50 rounded-lg p-2.5">
          <p className="text-xs text-gray-500">Costo unitario</p>
          <p className="text-base font-bold text-gray-900">{formatCurrency(c.costo_unitario)}</p>
          <p className="text-xs text-gray-400">por unidad producida</p>
        </div>
        <div className={`rounded-lg p-2.5 ${
          c.margen_actual_porcentaje >= 50 ? 'bg-green-50' :
          c.margen_actual_porcentaje >= 30 ? 'bg-yellow-50' : 'bg-red-50'
        }`}>
          <p className="text-xs text-gray-500">Margen actual</p>
          <p className={`text-base font-bold ${
            c.margen_actual_porcentaje >= 50 ? 'text-green-700' :
            c.margen_actual_porcentaje >= 30 ? 'text-yellow-700' : 'text-red-700'
          }`}>{c.margen_actual_porcentaje.toFixed(1)}%</p>
          <p className="text-xs text-gray-400">sobre precio de venta</p>
        </div>
      </div>

      {c.precio_sugerido && c.margen_objetivo && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center justify-between">
          <div>
            <p className="text-xs text-amber-700 font-medium">Tu Socia te sugiere</p>
            <p className="text-lg font-bold text-amber-900">{formatCurrency(c.precio_sugerido)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-amber-600">Para ganar el {c.margen_objetivo}%</p>
            <p className="text-xs text-amber-500">de cada venta</p>
          </div>
        </div>
      )}

      {/* Costo estándar vigente + diferencia */}
      {costoEstandar && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs text-blue-600 font-medium">Costo estándar vigente</p>
              <p className="font-bold text-blue-900">{formatCurrency(Number(costoEstandar.costo_unitario))}</p>
              <p className="text-xs text-blue-500">
                Fijado por {costoEstandar.confirmado_por_nombre ?? 'Admin'} · {new Date(costoEstandar.confirmado_en).toLocaleDateString('es-CO')}
              </p>
            </div>
            {diferenciaPct !== null && Math.abs(diferenciaPct) > 1 && (
              <span className={`text-xs font-bold px-2 py-1 rounded ${
                diferenciaPct > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
              }`}>
                {diferenciaPct > 0 ? '+' : ''}{diferenciaPct.toFixed(1)}% vs estándar
              </span>
            )}
          </div>
        </div>
      )}

      {/* Botón fijar costo */}
      {onFijarCosto && (
        <button
          onClick={onFijarCosto}
          disabled={fijarLoading}
          className="w-full py-2 text-sm font-semibold rounded-lg border-2 border-blue-500 text-blue-700 hover:bg-blue-50 transition-colors disabled:opacity-50"
        >
          {fijarLoading ? 'Fijando...' : 'Fijar como costo estándar'}
        </button>
      )}
    </div>
  );
}
