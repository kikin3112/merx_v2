import { useState } from 'react';
import { useEscenarios } from '../../hooks/useAnalisisPrecios';
import { formatCurrency } from '../../utils/format';
import { getViabilidadColor } from '../../socia/theme';
import type { EscenarioPrecio } from '../../types';

interface Props {
  recetaId: string;
}

const VIABILIDAD_LABEL: Record<string, string> = {
  VIABLE: '✓ Viable',
  CRITICO: '⚡ Crítico',
  NO_VIABLE: '✗ No viable',
};

export function EscenariosPrecios({ recetaId }: Props) {
  const [costosFijos, setCostosFijos] = useState(300000);
  const [volumen, setVolumen] = useState(50);
  const [precioMercado, setPrecioMercado] = useState('');
  const [escenarios, setEscenarios] = useState<EscenarioPrecio[] | null>(null);
  const [recetaNombre, setRecetaNombre] = useState('');

  const calcular = useEscenarios();

  function handleCalcular() {
    calcular.mutate(
      {
        receta_id: recetaId,
        costos_fijos: costosFijos,
        volumen,
        precio_mercado_referencia: precioMercado ? Number(precioMercado) : undefined,
      },
      {
        onSuccess: (data) => {
          setEscenarios(data.escenarios);
          setRecetaNombre(data.receta_nombre);
        },
      }
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-gray-900">Explora diferentes precios</h3>
        <p className="text-xs text-gray-500 mt-0.5">¿No sabes si cobrar más o menos? Mira qué pasaría en cada caso</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Gastos fijos/mes</label>
          <input
            type="number"
            min={0}
            step={10000}
            value={costosFijos}
            onChange={(e) => setCostosFijos(Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 focus:border-transparent"
          />
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
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Precio de mercado <span className="text-gray-400">(opcional)</span></label>
          <input
            type="number"
            min={0}
            step={500}
            placeholder="¿Cuánto cobran otras?"
            value={precioMercado}
            onChange={(e) => setPrecioMercado(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 focus:border-transparent"
          />
        </div>
      </div>

      <button
        onClick={handleCalcular}
        disabled={calcular.isPending}
        className="w-full rounded-lg bg-amber-500 text-white text-sm font-semibold py-2.5 hover:bg-amber-600 disabled:opacity-50 transition-colors"
      >
        {calcular.isPending ? 'Calculando...' : 'Ver escenarios de precio'}
      </button>

      {escenarios && escenarios.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-500">Escenarios para: <strong>{recetaNombre}</strong></p>
          <div className="grid grid-cols-1 gap-2">
            {escenarios.map((e) => (
              <EscenarioCard key={e.nombre} escenario={e} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function EscenarioCard({ escenario }: { escenario: EscenarioPrecio }) {
  const colorClass = getViabilidadColor(escenario.viabilidad);
  const isRecomendado = escenario.nombre === 'Objetivo' || escenario.nombre === 'Mercado';

  return (
    <div className={`border rounded-xl p-3 flex items-center justify-between ${
      isRecomendado ? 'border-amber-300 bg-amber-50' : 'border-gray-200 bg-white'
    }`}>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-900">{escenario.nombre}</span>
          {isRecomendado && <span className="text-xs bg-amber-200 text-amber-800 px-2 py-0.5 rounded-full font-medium">Recomendado</span>}
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-xs text-gray-500">PE: {Math.ceil(escenario.punto_equilibrio_unidades)} velas</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colorClass}`}>
            {VIABILIDAD_LABEL[escenario.viabilidad]}
          </span>
        </div>
      </div>
      <div className="text-right ml-4">
        <p className="text-lg font-bold text-gray-900">{formatCurrency(escenario.precio)}</p>
        <p className="text-xs text-gray-500">{escenario.margen_porcentaje.toFixed(0)}% de ganancia</p>
      </div>
    </div>
  );
}
