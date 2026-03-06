import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recetas, productos } from '../api/endpoints';
import { formatCurrency } from '../utils/format';
import type { Receta, Producto, RecetaCosto, CostoEstandar } from '../types';
import { useAuthStore } from '../stores/authStore';
import { useTutorial } from '../hooks/useTutorial';
import { CostoIndirectoManager } from '../components/recetas/CostoIndirectoManager';
import { CostoBreakdownChart } from '../components/recetas/CostoBreakdownChart';
import { PuntoEquilibrioPanel } from '../components/recetas/PuntoEquilibrioPanel';
import { EscenariosPrecios } from '../components/recetas/EscenariosPrecios';
import { MargenIndicator } from '../components/recetas/MargenIndicator';
import { TutorialTooltip } from '../components/tutorial/TutorialTooltip';
import { TutorialGuide } from '../components/tutorial/TutorialGuide';
import { HelpPanel } from '../components/tutorial/HelpPanel';
import { SociaOnboarding } from '../socia/components/SociaOnboarding';
import { AsistenteCosteoPanel } from '../components/recetas/AsistenteCosteoPanel';

type Tab = 'recetas' | 'analisis' | 'indirectos';

const UNIDADES = ['UNIDAD', 'GRAMO', 'KILOGRAMO', 'MILILITRO', 'LITRO', 'METRO', 'CENTIMETRO'] as const;

interface IngredienteForm {
  producto_id: string;
  nombre: string;
  cantidad: number;
  unidad: string;
  porcentaje_merma: number;
  notas: string;
}

export default function RecetasPage() {
  const queryClient = useQueryClient();
  const auth = useAuthStore();
  const userId = (auth as { user?: { id?: string } }).user?.id ?? 'anon';
  const tenantId = (auth as { tenantId?: string }).tenantId ?? 'default';

  const tutorial = useTutorial(userId, tenantId);
  const [showOnboarding, setShowOnboarding] = useState(() => tutorial.debesMostrar);
  const [showTour, setShowTour] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('recetas');
  const [showForm, setShowForm] = useState(false);
  const [selectedReceta, setSelectedReceta] = useState<Receta | null>(null);
  const [costoInfo, setCostoInfo] = useState<RecetaCosto | null>(null);
  const [costoEstandar, setCostoEstandar] = useState<CostoEstandar | null>(null);
  const [showProducir, setShowProducir] = useState(false);
  const [showSocia, setShowSocia] = useState(false);
  const [cantidadProducir, setCantidadProducir] = useState(1);
  const [obsProducir, setObsProducir] = useState('');

  // Form state
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [productoResultadoId, setProductoResultadoId] = useState('');
  const [cantidadResultado, setCantidadResultado] = useState(1);
  const [costoManoObra, setCostoManoObra] = useState(0);
  const [tiempoMinutos, setTiempoMinutos] = useState<number | ''>('');
  const [margenObjetivo, setMargenObjetivo] = useState<number | ''>('');
  const [produccionMensualEsperada, setProduccionMensualEsperada] = useState<number | ''>('');
  const [ingredientes, setIngredientes] = useState<IngredienteForm[]>([]);
  const [busquedaProducto, setBusquedaProducto] = useState('');
  const [busquedaIngrediente, setBusquedaIngrediente] = useState('');

  const { data: recetasList, isLoading } = useQuery<Receta[]>({
    queryKey: ['recetas'],
    queryFn: () => recetas.list().then((r) => r.data),
  });

  const { data: listaProductos } = useQuery<Producto[]>({
    queryKey: ['productos-recetas'],
    queryFn: () => productos.list({ estado: true, limit: 500 }).then((r) => r.data),
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
    onSuccess: ({ data: raw }) => {
      const data: RecetaCosto = {
        receta_id: raw.receta_id,
        receta_nombre: raw.receta_nombre,
        producto_resultado_id: raw.producto_resultado_id,
        cantidad_resultado: Number(raw.cantidad_resultado),
        costo_material_directo: Number(raw.costo_material_directo ?? raw.costo_ingredientes ?? 0),
        costo_mano_obra_directa: Number(raw.costo_mano_obra_directa ?? raw.costo_mano_obra ?? 0),
        costo_primo: Number(raw.costo_primo ?? 0),
        costo_conversion: Number(raw.costo_conversion ?? 0),
        costo_indirecto: Number(raw.costo_indirecto),
        costo_total: Number(raw.costo_total),
        costo_unitario: Number(raw.costo_unitario),
        costo_ingredientes: Number(raw.costo_ingredientes ?? raw.costo_material_directo ?? 0),
        costo_mano_obra: Number(raw.costo_mano_obra ?? raw.costo_mano_obra_directa ?? 0),
        cif_fijo_mensual: Number(raw.cif_fijo_mensual ?? 0),
        cif_por_unidad: Number(raw.cif_por_unidad ?? 0),
        cif_lote: Number(raw.cif_lote ?? 0),
        produccion_mensual_usada: Number(raw.produccion_mensual_usada ?? 0),
        fuente_produccion_mensual: raw.fuente_produccion_mensual ?? 'lote',
        lotes_posibles_con_stock: raw.lotes_posibles_con_stock ?? 0,
        ingrediente_critico: raw.ingrediente_critico ?? null,
        precio_venta_actual: Number(raw.precio_venta_actual),
        margen_actual_porcentaje: Number(raw.margen_actual_porcentaje),
        margen_objetivo: raw.margen_objetivo != null ? Number(raw.margen_objetivo) : null,
        precio_sugerido: raw.precio_sugerido != null ? Number(raw.precio_sugerido) : null,
        detalle_ingredientes: (raw.detalle_ingredientes ?? []).map((d: Record<string, unknown>) => ({
          producto_id: d.producto_id as string,
          producto_nombre: d.producto_nombre as string,
          unidad: d.unidad as string,
          unidad_inventario: (d.unidad_inventario as string) ?? '',
          cantidad: Number(d.cantidad),
          porcentaje_merma: Number(d.porcentaje_merma),
          cantidad_bruta: Number(d.cantidad_bruta),
          costo_unitario: Number(d.costo_unitario),
          costo_linea: Number(d.costo_linea),
          factor_aplicado: Number(d.factor_aplicado ?? 1),
          porcentaje_del_total: Number(d.porcentaje_del_total ?? 0),
        })),
      };
      setCostoInfo(data);
      setSelectedReceta(recetasList?.find((r) => r.id === data.receta_id) ?? null);
    },
  });

  const fijarCostoMutation = useMutation({
    mutationFn: (id: string) =>
      recetas.fijarCosto(id, { vigente_desde: new Date().toISOString().slice(0, 10) }),
    onSuccess: ({ data }) => {
      setCostoEstandar(data);
    },
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
    setMargenObjetivo('');
    setProduccionMensualEsperada('');
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
      margen_objetivo: margenObjetivo || null,
      produccion_mensual_esperada: produccionMensualEsperada || null,
      ingredientes: ingredientes.map((i) => ({
        producto_id: i.producto_id,
        cantidad: i.cantidad,
        unidad: i.unidad,
        porcentaje_merma: i.porcentaje_merma || 0,
        notas: i.notas || null,
      })),
    });
  }

  function agregarIngrediente(p: Producto) {
    if (ingredientes.some((i) => i.producto_id === p.id)) return;
    setIngredientes((prev) => [
      ...prev,
      { producto_id: p.id, nombre: p.nombre, cantidad: 1, unidad: 'GRAMO', porcentaje_merma: 0, notas: '' },
    ]);
    setBusquedaIngrediente('');
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="font-brand text-xl font-medium cv-text">Producción</h1>
          <p className="text-xs cv-muted mt-0.5">Costos, precios y análisis con tu Socia</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowTour(true)}
            className="text-xs px-3 py-1.5 rounded-lg cv-badge cv-badge-primary flex items-center gap-1 cursor-pointer"
          >
            📖 Tutorial
          </button>
          <button
            id="btn-nueva-receta"
            onClick={() => setShowForm(true)}
            className="cv-btn cv-btn-primary"
          >
            + Nueva producción
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b cv-divider mb-4 gap-1 overflow-x-auto">
        {([
          { id: 'recetas', label: '🏭 Producción' },
          { id: 'analisis', label: '📊 Análisis' },
          { id: 'indirectos', label: '💡 Gastos' },
        ] as const).map((tab) => (
          <button
            key={tab.id}
            id={tab.id === 'analisis' ? 'tab-analisis' : tab.id === 'indirectos' ? 'tab-indirectos' : undefined}
            onClick={() => setActiveTab(tab.id)}
            className={`whitespace-nowrap px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-[var(--cv-primary)] cv-primary'
                : 'border-transparent cv-muted hover:cv-text'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* === TAB: Recetas === */}
      {activeTab === 'recetas' && (
        isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="h-20 cv-elevated rounded-lg animate-pulse" />)}
          </div>
        ) : (
          <div className="space-y-3">
            {recetasList?.map((r) => (
              <div key={r.id} className="cv-card-hover p-4">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-sm font-semibold cv-text">{r.nombre}</h3>
                      {r.margen_objetivo != null && (
                        <MargenIndicator margen={r.margen_objetivo} />
                      )}
                    </div>
                    {r.descripcion && <p className="text-xs cv-muted mt-0.5">{r.descripcion}</p>}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs cv-muted">
                      <span>Rinde: <strong>{r.cantidad_resultado}</strong> uds</span>
                      <span>Ingredientes: <strong>{r.ingredientes.length}</strong></span>
                      {r.tiempo_produccion_minutos && (
                        <span>Tiempo: {r.tiempo_produccion_minutos} min</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <button
                      onClick={() => costoMutation.mutate(r.id)}
                      disabled={costoMutation.isPending}
                      className="cv-btn cv-btn-secondary"
                    >
                      {costoMutation.isPending ? '...' : 'Calcular costo'}
                    </button>
                    <button
                      onClick={() => { setSelectedReceta(r); setShowProducir(true); }}
                      className="cv-btn cv-btn-secondary"
                    >
                      Producir
                    </button>
                    <button
                      onClick={() => { if (confirm(`Eliminar receta "${r.nombre}"?`)) deleteMutation.mutate(r.id); }}
                      className="cv-btn cv-btn-danger"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
                {r.ingredientes.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {r.ingredientes.map((ing) => (
                      <span key={ing.id} className="cv-badge cv-badge-neutral">
                        {ing.producto_nombre ? `${ing.producto_nombre} · ` : ''}{ing.cantidad} {ing.unidad.toLowerCase()}
                        {ing.porcentaje_merma > 0 && <span className="cv-muted ml-1">({ing.porcentaje_merma}% merma)</span>}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {recetasList?.length === 0 && (
              <div className="cv-card p-12 text-center cv-muted">
                <p className="text-lg mb-2">🏭 Sin producciones todavía</p>
                <p className="text-sm">Define materias primas y crea tu primera producción</p>
              </div>
            )}
          </div>
        )
      )}

      {/* === TAB: Análisis === */}
      {activeTab === 'analisis' && (
        <div className="space-y-6">
          {recetasList && recetasList.length > 0 ? (
            <>
              {/* Selector de receta */}
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Selecciona una receta para analizar</label>
                <select
                  value={selectedReceta?.id ?? ''}
                  onChange={(e) => setSelectedReceta(recetasList.find((r) => r.id === e.target.value) ?? null)}
                  className="cv-input"
                >
                  <option value="">— Elige una receta —</option>
                  {recetasList.map((r) => (
                    <option key={r.id} value={r.id}>{r.nombre}</option>
                  ))}
                </select>
              </div>

              {selectedReceta ? (
                <div className="space-y-6">
                  {/* Costo breakdown si ya se calculó */}
                  {costoInfo && costoInfo.receta_id === selectedReceta.id && (
                    <div className="cv-card p-4">
                      <div className="flex items-center gap-2 mb-4">
                        <h3 className="text-sm font-semibold cv-text">Desglose de costos</h3>
                        <TutorialTooltip concepto="costoIngredientes" />
                      </div>
                      <CostoBreakdownChart
                        costo={costoInfo}
                        costoEstandar={costoEstandar}
                        onFijarCosto={() => fijarCostoMutation.mutate(costoInfo.receta_id)}
                        fijarLoading={fijarCostoMutation.isPending}
                      />
                    </div>
                  )}
                  {!costoInfo && (
                    <div className="cv-card cv-alert-accent p-4 text-center">
                      <p className="text-sm mb-3">Primero calcula el costo de esta receta para ver el desglose completo</p>
                      <button
                        onClick={() => costoMutation.mutate(selectedReceta.id)}
                        disabled={costoMutation.isPending}
                        className="cv-btn cv-btn-primary"
                      >
                        {costoMutation.isPending ? 'Calculando...' : 'Calcular costo ahora'}
                      </button>
                    </div>
                  )}

                  {/* Punto de equilibrio */}
                  <div className="cv-card p-4">
                    <PuntoEquilibrioPanel
                      recetaId={selectedReceta.id}
                      precioVentaDefault={costoInfo?.precio_venta_actual ?? 0}
                    />
                  </div>

                  {/* Escenarios de precio */}
                  <div className="cv-card p-4">
                    <EscenariosPrecios recetaId={selectedReceta.id} />
                  </div>

                  {/* Socia — asistente IA de costeo */}
                  <button
                    onClick={() => setShowSocia(true)}
                    className="cv-btn cv-btn-primary w-full"
                  >
                    Consultar a Socia
                  </button>
                </div>
              ) : (
                <div className="cv-card text-center py-12 cv-muted">
                  <p className="text-lg mb-2">📊</p>
                  <p className="text-sm">Selecciona una receta para ver su análisis de precios</p>
                </div>
              )}
            </>
          ) : (
            <div className="cv-card text-center py-12 cv-muted">
              <p className="text-lg mb-2">🏭</p>
              <p className="text-sm">Crea tu primera producción para acceder al análisis de precios</p>
            </div>
          )}
        </div>
      )}

      {/* === TAB: Costos Indirectos === */}
      {activeTab === 'indirectos' && (
        <div className="cv-card p-4">
          <CostoIndirectoManager />
        </div>
      )}

      {/* === Modal: Costo calculado === */}
      {costoInfo && activeTab === 'recetas' && (
        <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/50">
          <div className="cv-card w-full h-full md:h-auto md:max-h-[90vh] md:rounded-xl shadow-xl md:max-w-md md:mx-4 flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 border-b cv-divider">
              <h2 className="text-lg font-semibold cv-text">Costo: {costoInfo.receta_nombre}</h2>
              <button onClick={() => setCostoInfo(null)} className="cv-icon-btn p-2 -mr-1 text-xl">&times;</button>
            </div>
            <div className="p-4 md:p-6 overflow-y-auto flex-1">
              <CostoBreakdownChart
                        costo={costoInfo}
                        costoEstandar={costoEstandar}
                        onFijarCosto={() => fijarCostoMutation.mutate(costoInfo.receta_id)}
                        fijarLoading={fijarCostoMutation.isPending}
                      />
              <div className="mt-4 border-t cv-divider pt-3 space-y-1.5">
                {costoInfo.detalle_ingredientes.map((d, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="cv-muted">
                      {d.producto_nombre}
                      {' '}({d.cantidad_bruta.toFixed(4)} {d.unidad.toLowerCase()}
                      {d.porcentaje_merma > 0 && <span className="cv-muted ml-1">+{d.porcentaje_merma}% merma</span>})
                    </span>
                    <span className="font-medium">{formatCurrency(d.costo_linea)}</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => { setActiveTab('analisis'); setCostoInfo(costoInfo); }}
                  className="flex-1 cv-btn cv-btn-primary"
                >
                  Ver análisis completo →
                </button>
                <button onClick={() => setCostoInfo(null)} className="cv-btn cv-btn-ghost">
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* === Modal: Producir === */}
      {showProducir && selectedReceta && (
        <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/50">
          <div className="cv-card w-full h-full md:h-auto md:rounded-xl shadow-xl md:max-w-sm md:mx-4 flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 border-b cv-divider">
              <h2 className="text-lg font-semibold cv-text">Producir</h2>
              <button onClick={() => { setShowProducir(false); setSelectedReceta(null); }} className="cv-icon-btn p-2 -mr-1 text-xl">&times;</button>
            </div>
            <div className="p-4 md:p-6 space-y-4 overflow-y-auto flex-1">
              <p className="text-sm cv-muted">
                Receta: <strong className="cv-text">{selectedReceta.nombre}</strong><br />
                Rinde: {selectedReceta.cantidad_resultado} uds por lote
              </p>
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Lotes a producir</label>
                <input
                  type="number"
                  min={1}
                  value={cantidadProducir}
                  onChange={(e) => setCantidadProducir(Math.max(1, Number(e.target.value)))}
                  className="cv-input"
                />
                <p className="text-xs cv-muted mt-1">Total: {cantidadProducir * selectedReceta.cantidad_resultado} unidades</p>
              </div>
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Observaciones</label>
                <textarea
                  value={obsProducir}
                  onChange={(e) => setObsProducir(e.target.value)}
                  rows={2}
                  className="cv-input resize-none"
                />
              </div>
              {producirMutation.isError && (
                <div className="cv-alert-error text-sm px-3 py-2">
                  {(producirMutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error al producir'}
                </div>
              )}
              <button
                onClick={() => producirMutation.mutate({ id: selectedReceta.id, cantidad: cantidadProducir, obs: obsProducir })}
                disabled={producirMutation.isPending}
                className="cv-btn cv-btn-primary w-full"
              >
                {producirMutation.isPending ? 'Produciendo...' : 'Confirmar Produccion'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* === Modal: Crear receta === */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-end md:items-start justify-center bg-black/50 md:overflow-y-auto md:py-8">
          <div className="cv-card w-full h-full md:h-auto md:rounded-xl shadow-xl md:max-w-2xl md:mx-4 flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 border-b cv-divider">
              <h2 className="text-lg font-semibold cv-text">Nueva receta</h2>
              <button onClick={resetForm} className="cv-icon-btn p-2 -mr-1 text-xl">&times;</button>
            </div>
            <div className="px-4 py-4 md:px-6 space-y-4 overflow-y-auto flex-1">
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Nombre receta *</label>
                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Ej: Crema Corporal 200ml"
                  className="cv-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Descripcion</label>
                <textarea
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  rows={2}
                  className="cv-input resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium cv-text mb-1">Producto resultado *</label>
                {productoSeleccionado ? (
                  <div className="flex items-center justify-between cv-elevated rounded-lg px-3 py-2">
                    <div>
                      <p className="text-sm font-medium cv-text">{productoSeleccionado.nombre}</p>
                      <p className="text-xs cv-muted">{productoSeleccionado.codigo_interno}</p>
                    </div>
                    <button onClick={() => setProductoResultadoId('')} className="text-xs text-[var(--cv-negative)]">Cambiar</button>
                  </div>
                ) : (
                  <div>
                    <input
                      type="text"
                      placeholder="Buscar producto terminado..."
                      value={busquedaProducto}
                      onChange={(e) => setBusquedaProducto(e.target.value)}
                      className="cv-input"
                    />
                    {busquedaProducto && productosResultado.length > 0 && (
                      <div className="mt-1 cv-card max-h-40 overflow-y-auto shadow-md">
                        {productosResultado.map((p) => (
                          <button key={p.id} onClick={() => { setProductoResultadoId(p.id); setBusquedaProducto(''); }}
                            className="w-full text-left px-3 py-2 text-sm cv-nav-item border-b cv-divider last:border-0">
                            <span className="font-medium cv-text">{p.nombre}</span>
                            <span className="cv-muted ml-2 text-xs">{p.codigo_interno}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <label className="block text-xs font-medium cv-text mb-1">Rendimiento (uds)</label>
                  <input type="number" min={1} value={cantidadResultado}
                    onChange={(e) => setCantidadResultado(Math.max(1, Number(e.target.value)))}
                    className="cv-input" />
                </div>
                <div>
                  <label className="block text-xs font-medium cv-text mb-1 flex items-center gap-1">
                    Mano de obra <TutorialTooltip concepto="costoManoObra" />
                  </label>
                  <input type="number" min={0} step={100} value={costoManoObra}
                    onChange={(e) => setCostoManoObra(Number(e.target.value) || 0)}
                    className="cv-input" />
                </div>
                <div>
                  <label className="block text-xs font-medium cv-text mb-1">Tiempo (min)</label>
                  <input type="number" min={0} value={tiempoMinutos}
                    onChange={(e) => setTiempoMinutos(e.target.value ? Number(e.target.value) : '')}
                    className="cv-input" />
                </div>
                <div>
                  <label className="block text-xs font-medium cv-text mb-1 flex items-center gap-1">
                    Margen (%) <TutorialTooltip concepto="margenObjetivo" />
                  </label>
                  <input type="number" min={1} max={99} step={1} placeholder="60"
                    value={margenObjetivo}
                    onChange={(e) => setMargenObjetivo(e.target.value ? Number(e.target.value) : '')}
                    className="cv-input" />
                </div>
                <div>
                  <label className="block text-xs font-medium cv-text mb-1">
                    Prod. mensual (uds)
                  </label>
                  <input type="number" min={1} step={1} placeholder="200"
                    value={produccionMensualEsperada}
                    onChange={(e) => setProduccionMensualEsperada(e.target.value ? Number(e.target.value) : '')}
                    className="cv-input" />
                  <p className="text-xs cv-muted mt-0.5">Para distribuir CIF fijo mensual</p>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium cv-text mb-2 flex items-center gap-1">
                  Ingredientes * <TutorialTooltip concepto="costoIngredientes" />
                </label>
                <div className="mb-3">
                  <input type="text" placeholder="Buscar materia prima..." value={busquedaIngrediente}
                    onChange={(e) => setBusquedaIngrediente(e.target.value)}
                    className="cv-input" />
                  {busquedaIngrediente && productosIngrediente.length > 0 && (
                    <div className="mt-1 cv-card max-h-40 overflow-y-auto shadow-md">
                      {productosIngrediente.map((p) => (
                        <button key={p.id} onClick={() => agregarIngrediente(p)}
                          className="w-full text-left px-3 py-2 text-sm cv-nav-item border-b cv-divider last:border-0">
                          <span className="font-medium cv-text">{p.nombre}</span>
                          <span className="cv-muted ml-2 text-xs">{p.codigo_interno}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {ingredientes.length > 0 ? (
                  <div className="space-y-2">
                    {ingredientes.map((ing, i) => (
                      <div key={i} className="flex flex-wrap items-center gap-2 cv-elevated rounded-lg px-3 py-2">
                        <span className="flex-1 min-w-[120px] text-sm font-medium cv-text truncate">{ing.nombre}</span>
                        <input type="number" min={0.01} step={0.01} value={ing.cantidad}
                          onChange={(e) => setIngredientes((prev) => prev.map((item, idx) => idx === i ? { ...item, cantidad: Number(e.target.value) || 0 } : item))}
                          className="w-20 text-center cv-input px-2 py-1 text-sm"
                          title="Cantidad neta" />
                        <select value={ing.unidad}
                          onChange={(e) => setIngredientes((prev) => prev.map((item, idx) => idx === i ? { ...item, unidad: e.target.value } : item))}
                          className="cv-input px-2 py-1 text-sm w-auto">
                          {UNIDADES.map((u) => <option key={u} value={u}>{u.toLowerCase()}</option>)}
                        </select>
                        <div className="flex items-center gap-1">
                          <input type="number" min={0} max={99.99} step={0.1} value={ing.porcentaje_merma}
                            onChange={(e) => setIngredientes((prev) => prev.map((item, idx) => idx === i ? { ...item, porcentaje_merma: Math.min(99.99, Math.max(0, Number(e.target.value) || 0)) } : item))}
                            className="w-14 text-center cv-input px-2 py-1 text-sm"
                            title="Merma (%)" />
                          <span className="text-xs cv-muted">%</span>
                        </div>
                        <button onClick={() => setIngredientes((prev) => prev.filter((_, idx) => idx !== i))}
                          className="cv-muted hover:cv-negative text-lg transition-colors">&times;</button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="border border-dashed rounded-lg py-6 text-center text-sm cv-muted" style={{ borderColor: 'var(--cv-border-mid)' }}>
                    Busca y agrega materias primas
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 px-4 py-4 md:px-6 border-t cv-divider">
              <button onClick={resetForm} className="cv-btn cv-btn-ghost">Cancelar</button>
              <button
                onClick={handleCrear}
                disabled={!nombre || !productoResultadoId || ingredientes.length === 0 || crearMutation.isPending}
                className="cv-btn cv-btn-primary"
              >
                {crearMutation.isPending ? 'Creando...' : 'Crear Producción'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* === Tutorial: Onboarding inicial === */}
      {showOnboarding && (
        <SociaOnboarding
          onCompletar={() => {
            tutorial.completar();
            setShowOnboarding(false);
          }}
        />
      )}

      {/* === Tutorial: Tour paso a paso === */}
      {showTour && !showOnboarding && (
        <TutorialGuide
          paso={tutorial.state.pasoActual}
          onAvanzar={tutorial.avanzar}
          onOmitir={() => { tutorial.omitir(); setShowTour(false); }}
          onCompletar={() => { tutorial.completar(); setShowTour(false); }}
        />
      )}

      {/* === Modal: Socia — Asistente IA === */}
      {showSocia && selectedReceta && (
        <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/50">
          <div className="cv-card w-full h-full md:h-auto md:rounded-xl shadow-xl md:max-w-lg md:mx-4 flex flex-col" style={{ maxHeight: '90vh' }}>
            <div className="flex items-center justify-between px-4 py-3 border-b cv-divider flex-shrink-0">
              <h2 className="text-lg font-semibold cv-text">Socia</h2>
              <button
                onClick={() => setShowSocia(false)}
                className="cv-icon-btn p-2 -mr-1 text-xl"
              >
                &times;
              </button>
            </div>
            <AsistenteCosteoPanel
              key={selectedReceta.id}
              recetaId={selectedReceta.id}
              onClose={() => setShowSocia(false)}
            />
          </div>
        </div>
      )}

      {/* === Help Panel flotante === */}
      <HelpPanel />
    </div>
  );
}
