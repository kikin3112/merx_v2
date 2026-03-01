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
          <h3 className="text-sm font-semibold text-gray-900">Gastos adicionales</h3>
          <p className="text-xs text-gray-500 mt-0.5">Gas, empaques, electricidad... se reparten automáticamente en cada vela</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="text-xs px-3 py-1.5 rounded-lg bg-amber-100 text-amber-800 font-medium hover:bg-amber-200 transition-colors"
        >
          + Agregar
        </button>
      </div>

      {showForm && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Nombre del gasto</label>
            <input
              type="text"
              placeholder="Ej: Gas, Empaques, Electricidad..."
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              className="w-full rounded-lg border border-amber-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 focus:border-transparent"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                {tipo === 'FIJO' ? 'Monto COP' : '% del costo base'}
              </label>
              <input
                type="number"
                min={0}
                step={tipo === 'FIJO' ? 100 : 0.1}
                placeholder={tipo === 'FIJO' ? '50000' : '10'}
                value={monto}
                onChange={(e) => setMonto(e.target.value)}
                className="w-full rounded-lg border border-amber-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Tipo</label>
              <select
                value={tipo}
                onChange={(e) => setTipo(e.target.value as 'FIJO' | 'PORCENTAJE')}
                className="w-full rounded-lg border border-amber-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400"
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
              className="flex-1 rounded-lg bg-amber-500 text-white text-sm font-semibold py-2 hover:bg-amber-600 disabled:opacity-50 transition-colors"
            >
              {crear.isPending ? 'Guardando...' : 'Guardar gasto'}
            </button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2].map((i) => <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />)}
        </div>
      ) : lista && lista.length > 0 ? (
        <div className="space-y-2">
          {lista.filter((c) => c.activo).map((costo) => (
            <div key={costo.id} className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-3 py-2.5">
              <div>
                <span className="text-sm font-medium text-gray-900">{costo.nombre}</span>
                <span className="ml-2 text-xs text-gray-500">
                  {costo.tipo === 'FIJO'
                    ? `${formatCurrency(costo.monto)} por unidad`
                    : `${costo.monto}% del costo base`}
                </span>
              </div>
              <button
                onClick={() => { if (confirm(`Eliminar "${costo.nombre}"?`)) eliminar.mutate(costo.id); }}
                className="text-red-400 hover:text-red-600 text-sm ml-2"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-6 border border-dashed border-amber-200 rounded-xl bg-amber-50/50">
          <p className="text-sm text-amber-700">Sin gastos adicionales todavía</p>
          <p className="text-xs text-amber-600 mt-1">Agrégalos para que el costo de cada vela sea más preciso</p>
        </div>
      )}
    </div>
  );
}
