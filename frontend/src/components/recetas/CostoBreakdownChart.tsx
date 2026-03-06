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
    cif_fijo_mensual: Number(raw.cif_fijo_mensual ?? 0),
    cif_por_unidad: Number(raw.cif_por_unidad ?? 0),
    cif_lote: Number(raw.cif_lote ?? 0),
    produccion_mensual_usada: Number(raw.produccion_mensual_usada ?? 0),
    fuente_produccion_mensual: raw.fuente_produccion_mensual ?? 'lote',
  };

  const total = c.costo_total || 1;
  const pctMat = Math.round((c.costo_material_directo / total) * 100);
  const pctMO = Math.round((c.costo_mano_obra_directa / total) * 100);
  const pctInd = Math.round((c.costo_indirecto / total) * 100);

  const segments = [
    { label: 'Material directo', valor: c.costo_material_directo, pct: pctMat, color: 'bg-[var(--cv-primary)]' },
    { label: 'Mano de obra', valor: c.costo_mano_obra_directa, pct: pctMO, color: 'bg-[var(--cv-accent)]' },
    { label: 'Gastos adicionales', valor: c.costo_indirecto, pct: pctInd, color: 'bg-[var(--cv-positive)]' },
  ].filter((s) => s.valor > 0);

  // Diferencia vs costo estándar
  const diferenciaPct = costoEstandar
    ? ((c.costo_unitario - Number(costoEstandar.costo_unitario)) / Number(costoEstandar.costo_unitario)) * 100
    : null;

  return (
    <div className="space-y-3">
      {/* Barra horizontal stacked */}
      <div className="flex rounded-full overflow-hidden h-4 cv-elevated">
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
              <p className="text-xs cv-muted">{s.label}</p>
              <p className="text-sm font-semibold cv-text">{formatCurrency(s.valor)}</p>
              <p className="text-xs cv-muted">{s.pct}%</p>
            </div>
          </div>
        ))}
      </div>

      {/* Estructura profesional */}
      <div className="cv-elevated rounded-lg p-3 space-y-1.5 text-sm">
        <div className="flex justify-between">
          <span className="cv-muted">Costo Primo (MD + MOD)</span>
          <span className="font-semibold cv-text">{formatCurrency(c.costo_primo)}</span>
        </div>
        <div className="flex justify-between">
          <span className="cv-muted">Gastos adicionales (CIF)</span>
          <span className="font-semibold cv-text">{formatCurrency(c.costo_indirecto)}</span>
        </div>
        {c.cif_fijo_mensual > 0 && (
          <div className="ml-3 text-xs cv-muted space-y-0.5">
            <div className="flex justify-between">
              <span>CIF fijo mensual</span>
              <span>{formatCurrency(c.cif_fijo_mensual)}</span>
            </div>
            <div className="flex justify-between">
              <span>
                ÷ {Math.round(c.produccion_mensual_usada)} uds/mes
                {c.fuente_produccion_mensual === 'historico' && ' (historial)'}
                {c.fuente_produccion_mensual === 'esperado' && ' (esperado)'}
                {c.fuente_produccion_mensual === 'lote' && ' (⚠ solo lote)'}
              </span>
              <span>= {formatCurrency(c.cif_por_unidad)}/ud</span>
            </div>
          </div>
        )}
        <div className="flex justify-between border-t cv-divider pt-1.5 font-bold cv-text">
          <span>Costo Total Manufactura</span>
          <span>{formatCurrency(c.costo_total)}</span>
        </div>
      </div>

      {/* Cobertura de stock */}
      {c.lotes_posibles_con_stock !== undefined && (
        <div className={`cv-card rounded-lg px-3 py-2 flex items-center justify-between text-sm ${
          c.lotes_posibles_con_stock === 0 ? 'cv-alert-error' :
          c.lotes_posibles_con_stock <= 2 ? 'cv-alert-accent' :
          'cv-alert-positive'
        }`}>
          <span className={`font-medium ${
            c.lotes_posibles_con_stock === 0 ? 'cv-negative' :
            c.lotes_posibles_con_stock <= 2 ? 'cv-accent' : 'cv-positive'
          }`}>
            {c.lotes_posibles_con_stock === 0
              ? `Sin stock${c.ingrediente_critico ? ` — falta: ${c.ingrediente_critico}` : ''}`
              : `${c.lotes_posibles_con_stock} lote${c.lotes_posibles_con_stock !== 1 ? 's' : ''} posible${c.lotes_posibles_con_stock !== 1 ? 's' : ''} con stock actual`}
          </span>
        </div>
      )}

      {/* Totales clave */}
      <div className="grid grid-cols-2 gap-3 pt-2 border-t cv-divider">
        <div className="cv-elevated rounded-lg p-2.5">
          <p className="text-xs cv-muted">Costo unitario</p>
          <p className="text-base font-bold cv-text">{formatCurrency(c.costo_unitario)}</p>
          <p className="text-xs cv-muted">por unidad producida</p>
        </div>
        <div className={`rounded-lg p-2.5 cv-elevated`}>
          <p className="text-xs cv-muted">Margen actual</p>
          <p className={`text-base font-bold ${
            c.margen_actual_porcentaje >= 50 ? 'cv-positive' :
            c.margen_actual_porcentaje >= 30 ? 'cv-accent' : 'cv-negative'
          }`}>{c.margen_actual_porcentaje.toFixed(1)}%</p>
          <p className="text-xs cv-muted">sobre precio de venta</p>
        </div>
      </div>

      {c.precio_sugerido && c.margen_objetivo && (
        <div className="cv-card p-3 flex items-center justify-between" style={{ background: 'var(--cv-primary-dim)', borderColor: 'var(--cv-primary)' }}>
          <div>
            <p className="text-xs cv-primary font-medium">Tu Socia te sugiere</p>
            <p className="text-lg font-bold cv-text">{formatCurrency(c.precio_sugerido)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs cv-muted">Para ganar el {c.margen_objetivo}%</p>
            <p className="text-xs cv-muted">de cada venta</p>
          </div>
        </div>
      )}

      {/* Costo estándar vigente + diferencia */}
      {costoEstandar && (
        <div className="cv-card p-3 text-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs cv-primary font-medium">Costo estándar vigente</p>
              <p className="font-bold cv-text">{formatCurrency(Number(costoEstandar.costo_unitario))}</p>
              <p className="text-xs cv-muted">
                Fijado por {costoEstandar.confirmado_por_nombre ?? 'Admin'} · {new Date(costoEstandar.confirmado_en).toLocaleDateString('es-CO')}
              </p>
            </div>
            {diferenciaPct !== null && Math.abs(diferenciaPct) > 1 && (
              <span className={`cv-badge ${diferenciaPct > 0 ? 'cv-badge-negative' : 'cv-badge-positive'}`}>
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
          className="cv-btn cv-btn-secondary w-full disabled:opacity-50"
        >
          {fijarLoading ? 'Fijando...' : 'Fijar como costo estándar'}
        </button>
      )}
    </div>
  );
}
