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
        <h3 className="text-sm font-semibold cv-text">Explora diferentes precios</h3>
        <p className="text-xs cv-muted mt-0.5">¿No sabes si cobrar más o menos? Mira qué pasaría en cada caso</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium cv-text mb-1">Gastos fijos/mes</label>
          <input
            type="number"
            min={0}
            step={10000}
            value={costosFijos}
            onChange={(e) => setCostosFijos(Number(e.target.value))}
            className="cv-input"
          />
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
        </div>
        <div>
          <label className="block text-xs font-medium cv-text mb-1">Precio de mercado <span className="cv-muted">(opcional)</span></label>
          <input
            type="number"
            min={0}
            step={500}
            placeholder="¿Cuánto cobran otros?"
            value={precioMercado}
            onChange={(e) => setPrecioMercado(e.target.value)}
            className="cv-input"
          />
        </div>
      </div>

      <button
        onClick={handleCalcular}
        disabled={calcular.isPending}
        className="cv-btn cv-btn-primary w-full disabled:opacity-50"
      >
        {calcular.isPending ? 'Calculando...' : 'Ver escenarios de precio'}
      </button>

      {escenarios && escenarios.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs cv-muted">Escenarios para: <strong className="cv-text">{recetaNombre}</strong></p>
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
    <div className={`cv-card rounded-xl p-3 flex items-center justify-between ${
      isRecomendado ? 'border-[var(--cv-primary)]' : ''
    }`} style={isRecomendado ? { background: 'var(--cv-primary-dim)' } : {}}>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold cv-text">{escenario.nombre}</span>
          {isRecomendado && <span className="cv-badge cv-badge-primary">Recomendado</span>}
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-xs cv-muted">PE: {Math.ceil(escenario.punto_equilibrio_unidades)} uds.</span>
          <span className={`cv-badge ${colorClass}`}>
            {VIABILIDAD_LABEL[escenario.viabilidad]}
          </span>
        </div>
      </div>
      <div className="text-right ml-4">
        <p className="text-lg font-bold cv-text">{formatCurrency(escenario.precio)}</p>
        <p className="text-xs cv-muted">{escenario.margen_porcentaje.toFixed(0)}% de ganancia</p>
      </div>
    </div>
  );
}
