import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productos } from '../api/endpoints';
import { formatCurrency, formatDateTime } from '../utils/format';
import Modal from '../components/ui/Modal';
import SearchInput from '../components/ui/SearchInput';
import type { Producto, ProductoCreate, ProductoUpdate } from '../types';

const CATEGORIAS = ['Insumo', 'Producto_Propio', 'Producto_Tercero', 'Servicio'] as const;
const UNIDADES = ['UNIDAD', 'KILOGRAMO', 'GRAMO', 'LITRO', 'METRO', 'CAJA', 'SET'] as const;
const TIPOS_IVA = ['Excluido', 'Exento', 'Gravado'] as const;

const CATEGORIA_LABELS: Record<string, string> = {
  Insumo: 'Insumo',
  Producto_Propio: 'Producto Propio',
  Producto_Tercero: 'Producto Tercero',
  Servicio: 'Servicio',
};

function emptyForm(): ProductoCreate {
  return {
    codigo_interno: '',
    nombre: '',
    categoria: 'Producto_Propio',
    unidad_medida: 'UNIDAD',
    tipo_iva: 'Gravado',
    porcentaje_iva: 19,
    precio_venta: 0,
    maneja_inventario: true,
    stock_minimo: 5,
    estado: true,
  };
}

export default function ProductosPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Producto | null>(null);
  const [form, setForm] = useState<ProductoCreate>(emptyForm());
  const [error, setError] = useState('');

  const { data, isLoading } = useQuery<Producto[]>({
    queryKey: ['productos', { busqueda: search || undefined, categoria: filterCat || undefined }],
    queryFn: () =>
      productos
        .list({ busqueda: search || undefined, categoria: filterCat || undefined })
        .then((r) => r.data),
  });

  const createMut = useMutation({
    mutationFn: (data: ProductoCreate) => productos.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productos'] });
      closeModal();
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Error al crear producto'),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProductoUpdate }) => productos.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productos'] });
      closeModal();
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Error al actualizar producto'),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => productos.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['productos'] }),
  });

  function openCreate() {
    setEditing(null);
    setForm(emptyForm());
    setError('');
    setModalOpen(true);
  }

  function openEdit(p: Producto) {
    setEditing(p);
    setForm({
      codigo_interno: p.codigo_interno,
      nombre: p.nombre,
      descripcion: p.descripcion,
      categoria: p.categoria,
      unidad_medida: p.unidad_medida,
      tipo_iva: p.tipo_iva,
      porcentaje_iva: p.porcentaje_iva,
      precio_venta: p.precio_venta,
      maneja_inventario: p.maneja_inventario,
      stock_minimo: p.stock_minimo,
      stock_maximo: p.stock_maximo,
      codigo_barras: p.codigo_barras,
      estado: p.estado,
    });
    setError('');
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setEditing(null);
    setError('');
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (editing) {
      const updates: ProductoUpdate = {};
      if (form.nombre !== editing.nombre) updates.nombre = form.nombre;
      if (form.descripcion !== editing.descripcion) updates.descripcion = form.descripcion;
      if (form.categoria !== editing.categoria) updates.categoria = form.categoria;
      if (form.unidad_medida !== editing.unidad_medida) updates.unidad_medida = form.unidad_medida;
      if (form.tipo_iva !== editing.tipo_iva) updates.tipo_iva = form.tipo_iva;
      if (form.porcentaje_iva !== editing.porcentaje_iva) updates.porcentaje_iva = form.porcentaje_iva;
      if (form.precio_venta !== editing.precio_venta) updates.precio_venta = form.precio_venta;
      if (form.maneja_inventario !== editing.maneja_inventario) updates.maneja_inventario = form.maneja_inventario;
      if (form.stock_minimo !== editing.stock_minimo) updates.stock_minimo = form.stock_minimo;
      if (form.stock_maximo !== editing.stock_maximo) updates.stock_maximo = form.stock_maximo;
      if (form.codigo_barras !== editing.codigo_barras) updates.codigo_barras = form.codigo_barras;
      if (form.estado !== editing.estado) updates.estado = form.estado;
      updateMut.mutate({ id: editing.id, data: updates });
    } else {
      createMut.mutate(form);
    }
  }

  const saving = createMut.isPending || updateMut.isPending;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Productos</h1>
        <button
          onClick={openCreate}
          className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors"
        >
          + Nuevo Producto
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="flex-1 max-w-sm">
          <SearchInput value={search} onChange={setSearch} placeholder="Buscar por nombre o codigo..." />
        </div>
        <select
          value={filterCat}
          onChange={(e) => setFilterCat(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">Todas las categorias</option>
          {CATEGORIAS.map((c) => (
            <option key={c} value={c}>{CATEGORIA_LABELS[c]}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-500">Codigo</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Nombre</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Categoria</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Precio Venta</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Estado</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Creado Por</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((p) => (
                <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">{p.codigo_interno}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{p.nombre}</td>
                  <td className="px-4 py-3 text-gray-600">{CATEGORIA_LABELS[p.categoria] || p.categoria}</td>
                  <td className="px-4 py-3 text-right text-gray-900">{formatCurrency(p.precio_venta)}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                      p.estado ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {p.estado ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">{p.created_by?.nombre || 'Sistema'}</div>
                    <div className="text-xs text-gray-400">{formatDateTime(p.created_at)}</div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => openEdit(p)}
                      className="text-xs text-primary-600 hover:text-primary-800 font-medium mr-3"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Desactivar este producto?')) deleteMut.mutate(p.id);
                      }}
                      className="text-xs text-red-500 hover:text-red-700 font-medium"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data?.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <p className="text-lg mb-2">Sin productos</p>
              <p className="text-sm">Crea tu primer producto para empezar</p>
            </div>
          )}
        </div>
      )}

      {/* Create / Edit Modal */}
      <Modal open={modalOpen} onClose={closeModal} title={editing ? 'Editar Producto' : 'Nuevo Producto'} maxWidth="max-w-xl">
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2">{error}</div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Codigo Interno *</label>
              <input
                type="text"
                required
                disabled={!!editing}
                value={form.codigo_interno}
                onChange={(e) => setForm({ ...form, codigo_interno: e.target.value })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Codigo Barras</label>
              <input
                type="text"
                value={form.codigo_barras || ''}
                onChange={(e) => setForm({ ...form, codigo_barras: e.target.value || null })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
            <input
              type="text"
              required
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Descripcion</label>
            <textarea
              rows={2}
              value={form.descripcion || ''}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value || null })}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Categoria *</label>
              <select
                value={form.categoria}
                onChange={(e) => setForm({ ...form, categoria: e.target.value })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {CATEGORIAS.map((c) => (
                  <option key={c} value={c}>{CATEGORIA_LABELS[c]}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Unidad Medida *</label>
              <select
                value={form.unidad_medida}
                onChange={(e) => setForm({ ...form, unidad_medida: e.target.value })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {UNIDADES.map((u) => (
                  <option key={u} value={u}>{u}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo IVA *</label>
              <select
                value={form.tipo_iva}
                onChange={(e) => {
                  const tipoIva = e.target.value;
                  setForm({
                    ...form,
                    tipo_iva: tipoIva,
                    porcentaje_iva: tipoIva === 'Gravado' ? 19 : 0,
                  });
                }}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {TIPOS_IVA.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">% IVA</label>
              <input
                type="number"
                min={0}
                max={100}
                step={0.01}
                value={form.porcentaje_iva ?? 0}
                onChange={(e) => setForm({ ...form, porcentaje_iva: parseFloat(e.target.value) || 0 })}
                disabled={form.tipo_iva !== 'Gravado'}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Precio Venta</label>
              <input
                type="number"
                min={0}
                step={0.01}
                value={form.precio_venta ?? 0}
                onChange={(e) => setForm({ ...form, precio_venta: parseFloat(e.target.value) || 0 })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stock Minimo</label>
              <input
                type="number"
                min={0}
                value={form.stock_minimo ?? ''}
                onChange={(e) => setForm({ ...form, stock_minimo: e.target.value ? parseFloat(e.target.value) : null })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stock Maximo</label>
              <input
                type="number"
                min={0}
                value={form.stock_maximo ?? ''}
                onChange={(e) => setForm({ ...form, stock_maximo: e.target.value ? parseFloat(e.target.value) : null })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div className="flex items-end pb-2 gap-4">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.maneja_inventario ?? true}
                  onChange={(e) => setForm({ ...form, maneja_inventario: e.target.checked })}
                  className="rounded border-gray-300 text-primary-500 focus:ring-primary-500"
                />
                Inventario
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.estado ?? true}
                  onChange={(e) => setForm({ ...form, estado: e.target.checked })}
                  className="rounded border-gray-300 text-primary-500 focus:ring-primary-500"
                />
                Activo
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={closeModal}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 text-sm font-semibold text-white bg-primary-500 rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50"
            >
              {saving ? 'Guardando...' : editing ? 'Actualizar' : 'Crear'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
