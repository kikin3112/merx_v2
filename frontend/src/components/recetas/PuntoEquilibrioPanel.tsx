import { useState, useEffect } from 'react';
import { useAnalisisCVU } from '../../hooks/useAnalisisPrecios';
import { formatCurrency } from '../../utils/format';
import type { CVUResponse } from '../../types';
import { TUTORIALES } from '../../data/tutorial-content';
import { TutorialTooltip } from '../tutorial/TutorialTooltip';

interface Props {
  recetaId: string;
  precioVentaDefault: number;
}

export function PuntoEquilibrioPanel({ recetaId, precioVentaDefault }: Props) {
  const [precioVenta, setPrecioVenta] = useState(precioVentaDefault);

  // Sync precio when parent provides a real value (e.g. after costo calculation)
  useEffect(() => {
    if (precioVentaDefault > 0) {
      setPrecioVenta(precioVentaDefault);
    }
  }, [precioVentaDefault]);
  const [costosFijos, setCostosFijos] = useState(300000);
  const [volumen, setVolumen] = useState(50);
  const [resultado, setResultado] = useState<CVUResponse | null>(null);

  const cvu = useAnalisisCVU();

  function calcular() {
    cvu.mutate(
      { receta_id: recetaId, precio_venta: precioVenta, costos_fijos_periodo: costosFijos, volumen_esperado: volumen },
      { onSuccess: (data) => setResultado(data) }
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold cv-text">¿Cuántas unidades necesitas vender?</h3>
        <TutorialTooltip concepto="puntoEquilibrio" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium cv-text mb-1 flex items-center gap-1">
            Precio de venta <TutorialTooltip concepto="precioSugerido" />
          </label>
          <input
            type="number"
            min={0}
            step={500}
            value={precioVenta}
            onChange={(e) => setPrecioVenta(Number(e.target.value))}
            className="cv-input"
          />
          <p className="text-xs cv-muted mt-1">¿Cuánto cobras por unidad?</p>
        </div>
        <div>
          <label className="block text-xs font-medium cv-text mb-1 flex items-center gap-1">
            Gastos fijos del mes <TutorialTooltip concepto="puntoEquilibrio" />
          </label>
          <input
            type="number"
            min={0}
            step={10000}
            value={costosFijos}
            onChange={(e) => setCostosFijos(Number(e.target.value))}
            className="cv-input"
          />
          <p className="text-xs cv-muted mt-1">Arriendo, internet, etc.</p>
        </div>
        <div>
          <label className="block text-xs font-medium cv-text mb-1">Unidades esperadas/mes</label>
          <input
            type="number"
            min={1}
            value={volumen}
            onChange={(e) => setVolumen(Math.max(1, Number(e.target.value)))}
            className="cv-input"
          />
          <p className="text-xs cv-muted mt-1">¿Cuántas planeas vender?</p>
        </div>
      </div>

      <button
        onClick={calcular}
        disabled={cvu.isPending}
        className="cv-btn cv-btn-primary w-full disabled:opacity-50"
      >
        {cvu.isPending ? 'Calculando...' : 'Calcular punto de equilibrio'}
      </button>

      {resultado && (
        <div className="space-y-3 pt-2">
          {/* Resultado principal */}
          <div className={`cv-card rounded-xl p-4 text-center ${
            resultado.margen_seguridad_unidades >= 0 ? 'cv-alert-positive' : 'cv-alert-error'
          }`}>
            <p className="text-xs cv-muted mb-1">Necesitas vender al menos</p>
            <p className={`text-3xl font-bold ${resultado.margen_seguridad_unidades >= 0 ? 'cv-positive' : 'cv-negative'}`}>
              {Math.ceil(resultado.punto_equilibrio_unidades)} uds.
            </p>
            <p className="text-xs cv-muted mt-1">para no perder dinero este mes</p>
            {resultado.margen_seguridad_unidades >= 0 ? (
              <p className="text-sm font-medium cv-positive mt-2">
                ¡Tienes un colchón de {Math.floor(resultado.margen_seguridad_unidades)} uds. extra!
              </p>
            ) : (
              <p className="text-sm font-medium cv-negative mt-2">
                ⚡ Tu plan actual no alcanza el equilibrio
              </p>
            )}
          </div>

          {/* Métricas */}
          <div className="grid grid-cols-2 gap-2">
            <MetricCard
              label="Lo que te queda por unidad"
              value={formatCurrency(resultado.margen_contribucion_unitario)}
              tooltip={TUTORIALES.margenContribucion.explicacion}
              sub={`${resultado.ratio_margen_contribucion.toFixed(1)}% del precio`}
            />
            <MetricCard
              label="Ingresos de equilibrio"
              value={formatCurrency(resultado.punto_equilibrio_ingresos)}
              sub="ventas mínimas del mes"
            />
            <MetricCard
              label="Utilidad esperada"
              value={formatCurrency(resultado.utilidad_esperada)}
              highlight={resultado.utilidad_esperada > 0 ? 'green' : 'red'}
              sub={`si vendes ${volumen} uds.`}
            />
            <MetricCard
              label="Margen de seguridad"
              value={`${resultado.margen_seguridad_porcentaje.toFixed(1)}%`}
              tooltip={TUTORIALES.margenSeguridad.explicacion}
              sub={`${Math.floor(resultado.margen_seguridad_unidades)} uds. de colchón`}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({
  label, value, sub, highlight, tooltip,
}: {
  label: string;
  value: string;
  sub?: string;
  highlight?: 'green' | 'red';
  tooltip?: string;
}) {
  return (
    <div className="cv-elevated rounded-lg p-3 relative group">
      <p className="text-xs cv-muted">{label}</p>
      <p className={`text-sm font-bold mt-0.5 ${
        highlight === 'green' ? 'cv-positive' : highlight === 'red' ? 'cv-negative' : 'cv-text'
      }`}>{value}</p>
      {sub && <p className="text-xs cv-muted mt-0.5">{sub}</p>}
      {tooltip && (
        <div className="absolute bottom-full left-0 mb-1 hidden group-hover:block z-10 w-48 cv-card text-xs rounded-lg p-2 shadow-lg cv-text">
          {tooltip}
        </div>
      )}
    </div>
  );
}
