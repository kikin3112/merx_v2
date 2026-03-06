import { useState } from 'react';
import { useCostosIndirectos, useCrearCostoIndirecto, useEliminarCostoIndirecto } from '../../hooks/useCostosIndirectos';
import { formatCurrency } from '../../utils/format';

export function CostoIndirectoManager() {
  const { data: lista, isLoading } = useCostosIndirectos();
  const crear = useCrearCostoIndirecto();
  const eliminar = useEliminarCostoIndirecto();

  const [nombre, setNombre] = useState('');
  const [monto, setMonto] = useState('');
  const [tipo, setTipo] = useState<'FIJO' | 'PORCENTAJE'>('FIJO');
  const [showForm, setShowForm] = useState(false);

  function handleCrear() {
    if (!nombre || !monto) return;
    crear.mutate(
      { nombre, monto: Number(monto), tipo },
      { onSuccess: () => { setNombre(''); setMonto(''); setShowForm(false); } }
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold cv-text">Gastos adicionales</h3>
          <p className="text-xs cv-muted mt-0.5">Gas, empaques, electricidad... se reparten automáticamente en cada unidad producida</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="cv-btn cv-btn-secondary"
        >
          + Agregar
        </button>
      </div>

      {showForm && (
        <div className="cv-elevated rounded-xl p-4 space-y-3">
          <div>
            <label className="block text-xs font-medium cv-text mb-1">Nombre del gasto</label>
            <input
              type="text"
              placeholder="Ej: Gas, Empaques, Electricidad..."
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              className="cv-input"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium cv-text mb-1">
                {tipo === 'FIJO' ? 'Monto COP' : '% del costo base'}
              </label>
              <input
                type="number"
                min={0}
                step={tipo === 'FIJO' ? 100 : 0.1}
                placeholder={tipo === 'FIJO' ? '50000' : '10'}
                value={monto}
                onChange={(e) => setMonto(e.target.value)}
                className="cv-input"
              />
            </div>
            <div>
              <label className="block text-xs font-medium cv-text mb-1">Tipo</label>
              <select
                value={tipo}
                onChange={(e) => setTipo(e.target.value as 'FIJO' | 'PORCENTAJE')}
                className="cv-input"
              >
                <option value="FIJO">Fijo por unidad (COP)</option>
                <option value="PORCENTAJE">% del costo base</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCrear}
              disabled={!nombre || !monto || crear.isPending}
              className="cv-btn cv-btn-primary flex-1 disabled:opacity-50"
            >
              {crear.isPending ? 'Guardando...' : 'Guardar gasto'}
            </button>
            <button onClick={() => setShowForm(false)} className="cv-btn cv-btn-ghost">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2].map((i) => <div key={i} className="h-12 cv-elevated rounded-lg animate-pulse" />)}
        </div>
      ) : lista && lista.length > 0 ? (
        <div className="space-y-2">
          {lista.filter((c) => c.activo).map((costo) => (
            <div key={costo.id} className="cv-card flex items-center justify-between px-3 py-2.5">
              <div>
                <span className="text-sm font-medium cv-text">{costo.nombre}</span>
                <span className="ml-2 text-xs cv-muted">
                  {costo.tipo === 'FIJO'
                    ? `${formatCurrency(costo.monto)} por unidad`
                    : `${costo.monto}% del costo base`}
                </span>
              </div>
              <button
                onClick={() => { if (confirm(`Eliminar "${costo.nombre}"?`)) eliminar.mutate(costo.id); }}
                className="cv-muted hover:cv-negative text-sm ml-2 transition-colors"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-6 border border-dashed cv-border rounded-xl cv-elevated">
          <p className="text-sm cv-text">Sin gastos adicionales todavía</p>
          <p className="text-xs cv-muted mt-1">Agrégalos para que el costo de cada producto sea más preciso</p>
        </div>
      )}
    </div>
  );
}
