/**
 * Módulo unificado Producto+Inventario.
 * Permite crear un producto y registrar su inventario inicial en un solo flujo,
 * sin cambiar de URL. Usa virtualización para listas grandes.
 */
import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useCursorPagination } from '../../hooks/useCursorPagination';
import { VirtualList } from '../virtualized/VirtualList';
import { FadeIn, SuccessBadge } from '../ui/SpringTransition';
import Modal from '../ui/Modal';
import SearchInput from '../ui/SearchInput';
import { productos, inventarios } from '../../api/endpoints';
import { formatCurrency } from '../../utils/format';
import type { Producto, ProductoCreate } from '../../types';
import { useMutation } from '@tanstack/react-query';

const CATEGORIAS = ['Insumo', 'Producto_Propio', 'Producto_Tercero', 'Servicio'] as const;
const UNIDADES = ['UNIDAD', 'KILOGRAMO', 'GRAMO', 'LITRO', 'METRO', 'CAJA', 'SET'] as const;
const CAT_LABELS: Record<string, string> = {
  Insumo: 'Insumo', Producto_Propio: 'Producto Propio',
  Producto_Tercero: 'Producto Tercero', Servicio: 'Servicio',
};

function emptyForm(): ProductoCreate {
  return {
    codigo_interno: '', nombre: '', categoria: 'Producto_Propio',
    unidad_medida: 'UNIDAD', tipo_iva: 'Excluido', porcentaje_iva: 0,
    precio_venta: 0, maneja_inventario: true, stock_minimo: 5, estado: true,
  };
}

export default function ProductInventoryModule() {
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Produto | null>(null);
  const [form, setForm] = useState<ProductoCreate>(emptyForm());
  const [error, setError] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  // Step 2: initial inventory after product creation
  const [newProductId, setNewProductId] = useState<string | null>(null);
  const [invStep, setInvStep] = useState(false);
  const [invForm, setInvForm] = useState({ cantidad: '', costo_unitario: '', observaciones: '' });

  type Produto = Producto;

  const params: Record<string, unknown> = {};
  if (search) params.busqueda = search;
  if (filterCat) params.categoria = filterCat;

  const { allItems, isLoading, hasMore, loadMore } = useCursorPagination<Produto>(
    '/productos/paginado', ['productos-cursor'], params,
  );

  const createMut = useMutation({
    mutationFn: (data: ProductoCreate) => productos.create(data),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['productos-cursor'] });
      const created = res.data as Produto;
      if (form.maneja_inventario) {
        setNewProductId(created.id);
        setInvStep(true);
      } else {
        flash();
        closeModal();
      }
    },
    onError: (err: unknown) => setError((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? 'Error al crear'),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ProductoCreate> }) => productos.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['productos-cursor'] }); flash(); closeModal(); },
    onError: (err: unknown) => setError((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? 'Error al actualizar'),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => productos.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['productos-cursor'] }),
  });

  const entradaMut = useMutation({
    mutationFn: (data: { producto_id: string; cantidad: number; costo_unitario: number; observaciones?: string }) =>
      inventarios.entrada(data),
    onSuccess: () => { flash(); closeModal(); },
    onError: (err: unknown) => setError((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? 'Error al registrar inventario inicial'),
  });

  function flash() {
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
  }

  function openCreate() {
    setEditing(null); setForm(emptyForm()); setError(''); setModalOpen(true); setInvStep(false); setNewProductId(null);
    productos.siguienteCodigo('Producto_Propio').then((r) => setForm((f) => ({ ...f, codigo_interno: r.data.codigo_interno }))).catch(() => {});
  }

  function openEdit(p: Produto) {
    setEditing(p);
    setForm({ codigo_interno: p.codigo_interno, nombre: p.nombre, descripcion: p.descripcion ?? undefined, categoria: p.categoria, unidad_medida: p.unidad_medida, tipo_iva: p.tipo_iva, porcentaje_iva: p.porcentaje_iva, precio_venta: p.precio_venta, maneja_inventario: p.maneja_inventario, stock_minimo: p.stock_minimo ?? undefined, stock_maximo: p.stock_maximo ?? undefined, estado: p.estado });
    setError(''); setModalOpen(true); setInvStep(false);
  }

  function closeModal() { setModalOpen(false); setEditing(null); setError(''); setInvStep(false); setNewProductId(null); }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (editing) updateMut.mutate({ id: editing.id, data: form });
    else createMut.mutate(form);
  }

  function handleInvSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!newProductId) return;
    entradaMut.mutate({ producto_id: newProductId, cantidad: parseFloat(invForm.cantidad), costo_unitario: parseFloat(invForm.costo_unitario), observaciones: invForm.observaciones || undefined });
  }

  const saving = createMut.isPending || updateMut.isPending;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold cv-text font-brand">Productos</h1>
        <div className="flex items-center gap-3">
          <SuccessBadge show={showSuccess} message="Guardado" />
          <button onClick={openCreate} className="cv-btn cv-btn-primary">
            + Nuevo producto
          </button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="flex-1 max-w-sm">
          <SearchInput value={search} onChange={setSearch} placeholder="Buscar por nombre o código..." />
        </div>
        <select value={filterCat} onChange={(e) => setFilterCat(e.target.value)} className="cv-input">
          <option value="">Todas las categorías</option>
          {CATEGORIAS.map((c) => <option key={c} value={c}>{CAT_LABELS[c]}</option>)}
        </select>
      </div>

      {/* Desktop virtualized table */}
      <div className="hidden md:block">
        <div className="cv-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="cv-table-header">
              <tr>
                <th className="text-left">Código</th>
                <th className="text-left">Nombre</th>
                <th className="text-left">Categoría</th>
                <th className="text-right">Precio</th>
                <th className="text-center">Estado</th>
                <th className="text-center">Acciones</th>
              </tr>
            </thead>
          </table>
          <VirtualList<Produto>
            items={allItems}
            itemHeight={52}
            height={Math.min(480, Math.max(allItems.length * 52, 120))}
            isLoading={isLoading}
            emptyMessage="Sin productos"
            hasMore={hasMore}
            onLoadMore={() => { void loadMore(); }}
            renderRow={(p, _i, style) => (
              <div key={p.id} style={style} className="flex items-center border-b border-[var(--cv-border)] hover:bg-[var(--cv-elevated)] transition-colors px-4 text-sm">
                <span className="w-28 font-mono text-xs cv-muted shrink-0">{p.codigo_interno}</span>
                <span className="flex-1 font-medium cv-text truncate pr-4">{p.nombre}</span>
                <span className="w-32 cv-muted shrink-0 hidden lg:block">{CAT_LABELS[p.categoria] ?? p.categoria}</span>
                <span className="w-28 text-right cv-text shrink-0">{formatCurrency(p.precio_venta)}</span>
                <span className="w-20 text-center shrink-0">
                  <span className={`cv-badge ${p.estado ? 'cv-badge-positive' : 'cv-badge-negative'}`}>
                    {p.estado ? 'Activo' : 'Inactivo'}
                  </span>
                </span>
                <span className="w-24 text-center shrink-0">
                  <button onClick={() => openEdit(p)} className="text-xs font-medium mr-2" style={{ color: 'var(--cv-primary)' }}>Editar</button>
                  <button onClick={() => { if (confirm('¿Desactivar este producto?')) deleteMut.mutate(p.id); }} className="text-xs font-medium" style={{ color: 'var(--cv-negative)' }}>Eliminar</button>
                </span>
              </div>
            )}
          />
        </div>
        {hasMore && (
          <div className="text-center mt-3">
            <button onClick={() => { void loadMore(); }} className="text-sm font-medium" style={{ color: 'var(--cv-primary)' }}>
              Cargar más productos…
            </button>
          </div>
        )}
      </div>

      {/* Mobile cards */}
      <div className="md:hidden">
        {isLoading ? (
          <div className="space-y-3">{[1,2,3].map((i) => <div key={i} className="h-20 cv-elevated rounded-lg animate-pulse" />)}</div>
        ) : allItems.length === 0 ? (
          <div className="text-center py-12 cv-muted">Sin productos</div>
        ) : (
          <div className="space-y-3">
            {allItems.map((p) => (
              <FadeIn key={p.id}>
                <div className="cv-card p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <p className="font-medium cv-text">{p.nombre}</p>
                      <p className="text-xs cv-muted font-mono">{p.codigo_interno}</p>
                    </div>
                    <span className={`cv-badge ${p.estado ? 'cv-badge-positive' : 'cv-badge-negative'}`}>{p.estado ? 'Activo' : 'Inactivo'}</span>
                  </div>
                  <div className="flex gap-4 text-sm cv-muted mb-3">
                    <span>{formatCurrency(p.precio_venta)}</span>
                    <span>{CAT_LABELS[p.categoria] ?? p.categoria}</span>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => openEdit(p)} className="flex-1 py-1.5 text-xs font-medium rounded-lg bg-[var(--cv-primary-dim)] text-[var(--cv-primary)]">Editar</button>
                    <button onClick={() => { if (confirm('¿Desactivar?')) deleteMut.mutate(p.id); }} className="flex-1 py-1.5 text-xs font-medium rounded-lg bg-[var(--cv-negative-dim)] text-[var(--cv-negative)]">Eliminar</button>
                  </div>
                </div>
              </FadeIn>
            ))}
            {hasMore && (
              <button onClick={() => { void loadMore(); }} className="w-full py-3 text-sm font-medium" style={{ color: 'var(--cv-primary)' }}>Cargar más…</button>
            )}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Modal open={modalOpen} onClose={closeModal} title={invStep ? 'Inventario Inicial (Opcional)' : editing ? 'Editar Producto' : 'Nuevo Producto'} maxWidth="max-w-xl">
        {!invStep ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && <div className="cv-alert-error px-4 py-2 text-sm">{error}</div>}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Código interno *</label>
                <input type="text" required disabled value={form.codigo_interno} className="cv-input opacity-50" />
              </div>
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Código de barras</label>
                <input type="text" value={form.codigo_barras ?? ''} onChange={(e) => setForm({ ...form, codigo_barras: e.target.value || null })} className="cv-input" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium cv-text mb-1">Nombre *</label>
              <input type="text" required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="cv-input" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Categoría *</label>
                <select value={form.categoria} onChange={(e) => { setForm({ ...form, categoria: e.target.value }); if (!editing) productos.siguienteCodigo(e.target.value).then((r) => setForm((f) => ({ ...f, codigo_interno: r.data.codigo_interno }))).catch(() => {}); }} className="cv-input">
                  {CATEGORIAS.map((c) => <option key={c} value={c}>{CAT_LABELS[c]}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Unidad *</label>
                <select value={form.unidad_medida} onChange={(e) => setForm({ ...form, unidad_medida: e.target.value })} className="cv-input">
                  {UNIDADES.map((u) => <option key={u} value={u}>{u}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Tipo de IVA</label>
                <select value={form.tipo_iva} onChange={(e) => setForm({ ...form, tipo_iva: e.target.value, porcentaje_iva: e.target.value === 'Gravado' ? 19 : 0 })} className="cv-input">
                  {['Excluido','Exento','Gravado'].map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium cv-text mb-1">IVA (%)</label>
                <input type="number" inputMode="decimal" min={0} max={100} step={0.01} value={form.porcentaje_iva ?? 0} onChange={(e) => setForm({ ...form, porcentaje_iva: parseFloat(e.target.value) || 0 })} disabled={form.tipo_iva !== 'Gravado'} className="cv-input disabled:opacity-50" />
              </div>
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Precio de venta</label>
                <input type="number" inputMode="decimal" min={0} step={0.01} value={form.precio_venta ?? 0} onChange={(e) => setForm({ ...form, precio_venta: parseFloat(e.target.value) || 0 })} className="cv-input" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Stock mínimo</label>
                <input type="number" inputMode="numeric" min={0} value={form.stock_minimo ?? ''} onChange={(e) => setForm({ ...form, stock_minimo: e.target.value ? parseFloat(e.target.value) : null })} className="cv-input" />
              </div>
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Stock máximo</label>
                <input type="number" inputMode="numeric" min={0} value={form.stock_maximo ?? ''} onChange={(e) => setForm({ ...form, stock_maximo: e.target.value ? parseFloat(e.target.value) : null })} className="cv-input" />
              </div>
              <div className="flex flex-col gap-2 justify-end pb-2">
                <label className="flex items-center gap-2 text-sm cv-text">
                  <input type="checkbox" checked={form.maneja_inventario ?? true} onChange={(e) => setForm({ ...form, maneja_inventario: e.target.checked })} className="rounded" />
                  Inventario
                </label>
                <label className="flex items-center gap-2 text-sm cv-text">
                  <input type="checkbox" checked={form.estado ?? true} onChange={(e) => setForm({ ...form, estado: e.target.checked })} className="rounded" />
                  Activo
                </label>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t cv-divider">
              <button type="button" onClick={closeModal} className="cv-btn cv-btn-ghost">Cancelar</button>
              <button type="submit" disabled={saving} className="cv-btn cv-btn-primary disabled:opacity-50">
                {saving ? 'Guardando...' : editing ? 'Actualizar' : form.maneja_inventario ? 'Crear y configurar inventario →' : 'Crear'}
              </button>
            </div>
          </form>
        ) : (
          /* Step 2: Initial inventory */
          <form onSubmit={handleInvSubmit} className="space-y-4">
            {error && <div className="cv-alert-error px-4 py-2 text-sm">{error}</div>}
            <div className="cv-alert-positive px-4 py-3 text-sm">
              ✓ Producto creado. Ahora registra el inventario inicial (puedes omitirlo).
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Cantidad inicial *</label>
                <input type="number" inputMode="decimal" required min={0.01} step={0.01} value={invForm.cantidad} onChange={(e) => setInvForm({ ...invForm, cantidad: e.target.value })} className="cv-input" />
              </div>
              <div>
                <label className="block text-sm font-medium cv-text mb-1">Costo unitario *</label>
                <input type="number" inputMode="decimal" required min={0} step={0.01} value={invForm.costo_unitario} onChange={(e) => setInvForm({ ...invForm, costo_unitario: e.target.value })} className="cv-input" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium cv-text mb-1">Observaciones</label>
              <input type="text" value={invForm.observaciones} onChange={(e) => setInvForm({ ...invForm, observaciones: e.target.value })} placeholder="Ej. Stock inicial de apertura" className="cv-input" />
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t cv-divider">
              <button type="button" onClick={() => { flash(); closeModal(); }} className="cv-btn cv-btn-ghost">Omitir</button>
              <button type="submit" disabled={entradaMut.isPending} className="cv-btn cv-btn-primary disabled:opacity-50">
                {entradaMut.isPending ? 'Registrando...' : 'Registrar inventario'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
