import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recetas, productos } from '../api/endpoints';
import { formatCurrency } from '../utils/format';
import type { Receta, Producto, RecetaCosto } from '../types';

const UNIDADES = ['UNIDAD', 'GRAMO', 'KILOGRAMO', 'MILILITRO', 'LITRO', 'METRO', 'CENTIMETRO'] as const;

interface IngredienteForm {
  producto_id: string;
  nombre: string;
  cantidad: number;
  unidad: string;
  notas: string;
}

export default function RecetasPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [selectedReceta, setSelectedReceta] = useState<Receta | null>(null);
  const [costoInfo, setCostoInfo] = useState<RecetaCosto | null>(null);
  const [showProducir, setShowProducir] = useState(false);
  const [cantidadProducir, setCantidadProducir] = useState(1);
  const [obsProducir, setObsProducir] = useState('');

  // Form state
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [productoResultadoId, setProductoResultadoId] = useState('');
  const [cantidadResultado, setCantidadResultado] = useState(1);
  const [costoManoObra, setCostoManoObra] = useState(0);
  const [tiempoMinutos, setTiempoMinutos] = useState<number | ''>('');
  const [ingredientes, setIngredientes] = useState<IngredienteForm[]>([]);
  const [busquedaProducto, setBusquedaProducto] = useState('');
  const [busquedaIngrediente, setBusquedaIngrediente] = useState('');

  const { data: recetasList, isLoading } = useQuery<Receta[]>({
    queryKey: ['recetas'],
    queryFn: () => recetas.list().then((r) => r.data),
  });

  const { data: listaProductos } = useQuery<Producto[]>({
    queryKey: ['productos-recetas'],
    queryFn: () => productos.list({ estado: true }).then((r) => r.data),
    enabled: showForm || !!selectedReceta,
  });

  const crearMutation = useMutation({
    mutationFn: (data: unknown) => recetas.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recetas'] });
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => recetas.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recetas'] }),
  });

  const costoMutation = useMutation({
    mutationFn: (id: string) => recetas.calcularCosto(id),
    onSuccess: ({ data }) => setCostoInfo(data),
  });

  const producirMutation = useMutation({
    mutationFn: ({ id, cantidad, obs }: { id: string; cantidad: number; obs?: string }) =>
      recetas.producir(id, { cantidad, observaciones: obs || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recetas'] });
      queryClient.invalidateQueries({ queryKey: ['inventario'] });
      queryClient.invalidateQueries({ queryKey: ['productos'] });
      setShowProducir(false);
      setSelectedReceta(null);
      setCantidadProducir(1);
      setObsProducir('');
    },
  });

  const productosResultado = useMemo(() => {
    if (!listaProductos) return [];
    if (!busquedaProducto) return listaProductos.slice(0, 10);
    const q = busquedaProducto.toLowerCase();
    return listaProductos.filter(
      (p) => p.nombre.toLowerCase().includes(q) || p.codigo_interno.toLowerCase().includes(q)
    ).slice(0, 10);
  }, [listaProductos, busquedaProducto]);

  const productosIngrediente = useMemo(() => {
    if (!listaProductos) return [];
    if (!busquedaIngrediente) return listaProductos.slice(0, 10);
    const q = busquedaIngrediente.toLowerCase();
    return listaProductos.filter(
      (p) => p.nombre.toLowerCase().includes(q) || p.codigo_interno.toLowerCase().includes(q)
    ).slice(0, 10);
  }, [listaProductos, busquedaIngrediente]);

  const productoSeleccionado = listaProductos?.find((p) => p.id === productoResultadoId);

  function resetForm() {
    setShowForm(false);
    setNombre('');
    setDescripcion('');
    setProductoResultadoId('');
    setCantidadResultado(1);
    setCostoManoObra(0);
    setTiempoMinutos('');
    setIngredientes([]);
    setBusquedaProducto('');
    setBusquedaIngrediente('');
  }

  function handleCrear() {
    if (!nombre || !productoResultadoId || ingredientes.length === 0) return;
    crearMutation.mutate({
      nombre,
      descripcion: descripcion || null,
      producto_resultado_id: productoResultadoId,
      cantidad_resultado: cantidadResultado,
      costo_mano_obra: costoManoObra,
      tiempo_produccion_minutos: tiempoMinutos || null,
      ingredientes: ingredientes.map((i) => ({
        producto_id: i.producto_id,
        cantidad: i.cantidad,
        unidad: i.unidad,
        notas: i.notas || null,
      })),
    });
  }

  function agregarIngrediente(p: Producto) {
    if (ingredientes.some((i) => i.producto_id === p.id)) return;
    setIngredientes((prev) => [
      ...prev,
      { producto_id: p.id, nombre: p.nombre, cantidad: 1, unidad: 'GRAMO', notas: '' },
    ]);
    setBusquedaIngrediente('');
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Recetas de Produccion</h1>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors"
        >
          + Nueva Receta
        </button>
      </div>

      {/* List */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-200 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {recetasList?.map((r) => (
            <div
              key={r.id}
              className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-gray-900">{r.nombre}</h3>
                  {r.descripcion && (
                    <p className="text-xs text-gray-500 mt-0.5">{r.descripcion}</p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
                    <span>Rinde: <strong>{r.cantidad_resultado}</strong> uds</span>
                    <span>Ingredientes: <strong>{r.ingredientes.length}</strong></span>
                    {r.costo_unitario != null && (
                      <span>Costo unit.: <strong>{formatCurrency(r.costo_unitario)}</strong></span>
                    )}
                    {r.tiempo_produccion_minutos && (
                      <span>Tiempo: {r.tiempo_produccion_minutos} min</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1.5 ml-4">
                  <button
                    onClick={() => costoMutation.mutate(r.id)}
                    className="rounded px-2.5 py-1 text-xs font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
                  >
                    Calcular Costo
                  </button>
                  <button
                    onClick={() => { setSelectedReceta(r); setShowProducir(true); }}
                    className="rounded px-2.5 py-1 text-xs font-medium bg-green-50 text-green-700 hover:bg-green-100 transition-colors"
                  >
                    Producir
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`Eliminar receta "${r.nombre}"?`)) deleteMutation.mutate(r.id);
                    }}
                    className="rounded px-2.5 py-1 text-xs font-medium bg-red-50 text-red-700 hover:bg-red-100 transition-colors"
                  >
                    Eliminar
                  </button>
                </div>
              </div>

              {/* Ingredientes preview */}
              {r.ingredientes.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {r.ingredientes.map((ing) => (
                    <span
                      key={ing.id}
                      className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600"
                    >
                      {ing.cantidad} {ing.unidad.toLowerCase()}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}

          {recetasList?.length === 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
              <p className="text-lg mb-2">Sin recetas</p>
              <p className="text-sm">Define materias primas y crea tu primera receta</p>
            </div>
          )}
        </div>
      )}

      {/* Costo Modal */}
      {costoInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Costo: {costoInfo.receta_nombre}</h2>
              <button onClick={() => setCostoInfo(null)} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div className="p-6 space-y-4">
              <div className="space-y-2">
                {costoInfo.detalle_ingredientes.map((d, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="text-gray-600">{d.producto_nombre} ({d.cantidad} {d.unidad})</span>
                    <span className="font-medium">{formatCurrency(d.costo_linea)}</span>
                  </div>
                ))}
              </div>
              <div className="border-t border-gray-200 pt-3 space-y-1.5">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Costo ingredientes</span>
                  <span>{formatCurrency(costoInfo.costo_ingredientes)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Mano de obra</span>
                  <span>{formatCurrency(costoInfo.costo_mano_obra)}</span>
                </div>
                <div className="flex justify-between text-sm font-semibold">
                  <span>Costo total</span>
                  <span>{formatCurrency(costoInfo.costo_total)}</span>
                </div>
                <div className="flex justify-between text-sm font-semibold text-primary-700">
                  <span>Costo unitario</span>
                  <span>{formatCurrency(costoInfo.costo_unitario)}</span>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Precio venta actual</span>
                  <span>{formatCurrency(costoInfo.precio_venta_actual)}</span>
                </div>
                <div className="flex justify-between text-sm font-semibold">
                  <span>Margen</span>
                  <span className={costoInfo.margen_actual_porcentaje >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {costoInfo.margen_actual_porcentaje.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Producir Modal */}
      {showProducir && selectedReceta && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Producir</h2>
              <button onClick={() => { setShowProducir(false); setSelectedReceta(null); }} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-600">
                Receta: <strong>{selectedReceta.nombre}</strong>
                <br />
                Rinde: {selectedReceta.cantidad_resultado} uds por lote
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Lotes a producir</label>
                <input
                  type="number"
                  min={1}
                  value={cantidadProducir}
                  onChange={(e) => setCantidadProducir(Math.max(1, Number(e.target.value)))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Total producido: {cantidadProducir * selectedReceta.cantidad_resultado} unidades
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Observaciones</label>
                <textarea
                  value={obsProducir}
                  onChange={(e) => setObsProducir(e.target.value)}
                  rows={2}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                />
              </div>
              {producirMutation.isError && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-3 py-2">
                  {(producirMutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error al producir'}
                </div>
              )}
              <button
                onClick={() => producirMutation.mutate({ id: selectedReceta.id, cantidad: cantidadProducir, obs: obsProducir })}
                disabled={producirMutation.isPending}
                className="w-full rounded-lg bg-green-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {producirMutation.isPending ? 'Produciendo...' : 'Confirmar Produccion'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Form Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 overflow-y-auto py-8">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Nueva Receta</h2>
              <button onClick={resetForm} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div className="px-6 py-4 space-y-4 max-h-[70vh] overflow-y-auto">
              {/* Nombre */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre receta *</label>
                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Ej: Vela Aromatica Lavanda 200g"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descripcion</label>
                <textarea
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  rows={2}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Producto resultado */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Producto resultado *</label>
                {productoSeleccionado ? (
                  <div className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                    <div>
                      <p className="text-sm font-medium">{productoSeleccionado.nombre}</p>
                      <p className="text-xs text-gray-500">{productoSeleccionado.codigo_interno}</p>
                    </div>
                    <button onClick={() => setProductoResultadoId('')} className="text-xs text-red-500">Cambiar</button>
                  </div>
                ) : (
                  <div>
                    <input
                      type="text"
                      placeholder="Buscar producto terminado..."
                      value={busquedaProducto}
                      onChange={(e) => setBusquedaProducto(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                    {busquedaProducto && productosResultado.length > 0 && (
                      <div className="mt-1 border border-gray-200 rounded-lg max-h-40 overflow-y-auto bg-white shadow-md">
                        {productosResultado.map((p) => (
                          <button
                            key={p.id}
                            onClick={() => { setProductoResultadoId(p.id); setBusquedaProducto(''); }}
                            className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-50"
                          >
                            <span className="font-medium">{p.nombre}</span>
                            <span className="text-gray-500 ml-2 text-xs">{p.codigo_interno}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rendimiento (uds)</label>
                  <input
                    type="number"
                    min={1}
                    value={cantidadResultado}
                    onChange={(e) => setCantidadResultado(Math.max(1, Number(e.target.value)))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Costo mano obra</label>
                  <input
                    type="number"
                    min={0}
                    step={100}
                    value={costoManoObra}
                    onChange={(e) => setCostoManoObra(Number(e.target.value) || 0)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tiempo (min)</label>
                  <input
                    type="number"
                    min={0}
                    value={tiempoMinutos}
                    onChange={(e) => setTiempoMinutos(e.target.value ? Number(e.target.value) : '')}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Ingredientes */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">Ingredientes *</label>
                </div>

                <div className="mb-3">
                  <input
                    type="text"
                    placeholder="Buscar materia prima..."
                    value={busquedaIngrediente}
                    onChange={(e) => setBusquedaIngrediente(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                  {busquedaIngrediente && productosIngrediente.length > 0 && (
                    <div className="mt-1 border border-gray-200 rounded-lg max-h-40 overflow-y-auto bg-white shadow-md">
                      {productosIngrediente.map((p) => (
                        <button
                          key={p.id}
                          onClick={() => agregarIngrediente(p)}
                          className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-50"
                        >
                          <span className="font-medium">{p.nombre}</span>
                          <span className="text-gray-500 ml-2 text-xs">{p.codigo_interno}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {ingredientes.length > 0 ? (
                  <div className="space-y-2">
                    {ingredientes.map((ing, i) => (
                      <div key={i} className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2">
                        <span className="flex-1 text-sm font-medium text-gray-900 truncate">{ing.nombre}</span>
                        <input
                          type="number"
                          min={0.01}
                          step={0.01}
                          value={ing.cantidad}
                          onChange={(e) =>
                            setIngredientes((prev) =>
                              prev.map((item, idx) => (idx === i ? { ...item, cantidad: Number(e.target.value) || 0 } : item))
                            )
                          }
                          className="w-20 text-center rounded border border-gray-200 px-2 py-1 text-sm"
                        />
                        <select
                          value={ing.unidad}
                          onChange={(e) =>
                            setIngredientes((prev) =>
                              prev.map((item, idx) => (idx === i ? { ...item, unidad: e.target.value } : item))
                            )
                          }
                          className="rounded border border-gray-200 px-2 py-1 text-sm"
                        >
                          {UNIDADES.map((u) => (
                            <option key={u} value={u}>{u.toLowerCase()}</option>
                          ))}
                        </select>
                        <button
                          onClick={() => setIngredientes((prev) => prev.filter((_, idx) => idx !== i))}
                          className="text-red-400 hover:text-red-600 text-lg"
                        >
                          &times;
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="border border-dashed border-gray-300 rounded-lg py-6 text-center text-sm text-gray-400">
                    Busca y agrega materias primas
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-100">
              <button onClick={resetForm} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                Cancelar
              </button>
              <button
                onClick={handleCrear}
                disabled={!nombre || !productoResultadoId || ingredientes.length === 0 || crearMutation.isPending}
                className="px-5 py-2 text-sm font-semibold text-white bg-primary-500 rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50"
              >
                {crearMutation.isPending ? 'Creando...' : 'Crear Receta'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
