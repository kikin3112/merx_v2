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
        <h3 className="text-sm font-semibold text-gray-900">¿Cuántas velas necesitas vender?</h3>
        <TutorialTooltip concepto="puntoEquilibrio" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
            Precio de venta <TutorialTooltip concepto="precioSugerido" />
          </label>
          <input
            type="number"
            min={0}
            step={500}
            value={precioVenta}
            onChange={(e) => setPrecioVenta(Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 focus:border-transparent"
          />
          <p className="text-xs text-gray-400 mt-1">¿Cuánto cobras por vela?</p>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
            Gastos fijos del mes <TutorialTooltip concepto="puntoEquilibrio" />
          </label>
          <input
            type="number"
            min={0}
            step={10000}
            value={costosFijos}
            onChange={(e) => setCostosFijos(Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 focus:border-transparent"
          />
          <p className="text-xs text-gray-400 mt-1">Arriendo, internet, etc.</p>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Velas esperadas/mes</label>
          <input
            type="number"
            min={1}
            value={volumen}
            onChange={(e) => setVolumen(Math.max(1, Number(e.target.value)))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 focus:border-transparent"
          />
          <p className="text-xs text-gray-400 mt-1">¿Cuántas planeas vender?</p>
        </div>
      </div>

      <button
        onClick={calcular}
        disabled={cvu.isPending}
        className="w-full rounded-lg bg-amber-500 text-white text-sm font-semibold py-2.5 hover:bg-amber-600 disabled:opacity-50 transition-colors"
      >
        {cvu.isPending ? 'Calculando...' : 'Calcular punto de equilibrio'}
      </button>

      {resultado && (
        <div className="space-y-3 pt-2">
          {/* Resultado principal */}
          <div className={`rounded-xl p-4 text-center ${
            resultado.margen_seguridad_unidades >= 0 ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <p className="text-xs text-gray-500 mb-1">Necesitas vender al menos</p>
            <p className={`text-3xl font-bold ${resultado.margen_seguridad_unidades >= 0 ? 'text-green-700' : 'text-red-700'}`}>
              {Math.ceil(resultado.punto_equilibrio_unidades)} velas
            </p>
            <p className="text-xs text-gray-500 mt-1">para no perder dinero este mes</p>
            {resultado.margen_seguridad_unidades >= 0 ? (
              <p className="text-sm font-medium text-green-600 mt-2">
                ¡Tienes un colchón de {Math.floor(resultado.margen_seguridad_unidades)} velas extra!
              </p>
            ) : (
              <p className="text-sm font-medium text-red-600 mt-2">
                ⚡ Tu plan actual no alcanza el equilibrio
              </p>
            )}
          </div>

          {/* Métricas */}
          <div className="grid grid-cols-2 gap-2">
            <MetricCard
              label="Lo que te queda por vela"
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
              sub={`si vendes ${volumen} velas`}
            />
            <MetricCard
              label="Margen de seguridad"
              value={`${resultado.margen_seguridad_porcentaje.toFixed(1)}%`}
              tooltip={TUTORIALES.margenSeguridad.explicacion}
              sub={`${Math.floor(resultado.margen_seguridad_unidades)} velas de colchón`}
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
    <div className="bg-gray-50 rounded-lg p-3 relative group">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-sm font-bold mt-0.5 ${
        highlight === 'green' ? 'text-green-700' : highlight === 'red' ? 'text-red-700' : 'text-gray-900'
      }`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      {tooltip && (
        <div className="absolute bottom-full left-0 mb-1 hidden group-hover:block z-10 w-48 bg-gray-800 text-white text-xs rounded-lg p-2 shadow-lg">
          {tooltip}
        </div>
      )}
    </div>
  );
}
