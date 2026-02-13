import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { terceros } from '../api/endpoints';
import { formatCurrency, formatDate, statusColor } from '../utils/format';
import Modal from '../components/ui/Modal';
import SearchInput from '../components/ui/SearchInput';
import type { Tercero, TerceroCreate, TerceroUpdate } from '../types';

const TIPOS_DOCUMENTO = ['CC', 'NIT', 'CE', 'PAS', 'TI'] as const;
const TIPOS_TERCERO = ['CLIENTE', 'PROVEEDOR', 'AMBOS'] as const;
const GRUPOS_CLIENTE = ['', 'VIP', 'Mayorista', 'Minorista', 'Corporativo'] as const;

const TIPO_DOC_LABELS: Record<string, string> = {
  CC: 'Cedula Ciudadania',
  NIT: 'NIT',
  CE: 'Cedula Extranjeria',
  PAS: 'Pasaporte',
  TI: 'Tarjeta Identidad',
};

function emptyForm(): TerceroCreate {
  return {
    tipo_documento: 'CC',
    numero_documento: '',
    nombre: '',
    tipo_tercero: 'CLIENTE',
    estado: true,
    limite_credito: 0,
    plazo_pago_dias: 0,
  };
}

interface HistorialItem {
  id: string;
  numero: string;
  fecha: string;
  total: number;
  estado: string;
}

interface HistorialData {
  ventas: HistorialItem[];
  cotizaciones: HistorialItem[];
}

export default function TercerosPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [filterTipo, setFilterTipo] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Tercero | null>(null);
  const [form, setForm] = useState<TerceroCreate>(emptyForm());
  const [error, setError] = useState('');
  const [selectedTercero, setSelectedTercero] = useState<Tercero | null>(null);
  const [detailTab, setDetailTab] = useState<'info' | 'historial' | 'notas'>('info');
  const [editingDetail, setEditingDetail] = useState(false);
  const [detailForm, setDetailForm] = useState<TerceroUpdate>({});

  const { data, isLoading } = useQuery<Tercero[]>({
    queryKey: ['terceros', { busqueda: search || undefined, tipo_tercero: filterTipo || undefined }],
    queryFn: () =>
      terceros
        .list({ busqueda: search || undefined, tipo_tercero: filterTipo || undefined })
        .then((r) => r.data),
  });

  const { data: historial } = useQuery<HistorialData>({
    queryKey: ['tercero-historial', selectedTercero?.id],
    queryFn: () => terceros.historial(selectedTercero!.id).then((r) => r.data),
    enabled: !!selectedTercero && detailTab === 'historial',
  });

  const createMut = useMutation({
    mutationFn: (data: TerceroCreate) => terceros.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['terceros'] });
      closeModal();
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Error al crear tercero'),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: TerceroUpdate }) => terceros.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['terceros'] });
      closeModal();
      setEditingDetail(false);
      // Refresh selected tercero
      if (selectedTercero) {
        terceros.get(selectedTercero.id).then((r) => setSelectedTercero(r.data));
      }
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Error al actualizar'),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => terceros.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['terceros'] });
      if (selectedTercero) setSelectedTercero(null);
    },
  });

  function openCreate() {
    setEditing(null);
    setForm(emptyForm());
    setError('');
    setModalOpen(true);
  }

  function openEdit(t: Tercero) {
    setEditing(t);
    setForm({
      tipo_documento: t.tipo_documento,
      numero_documento: t.numero_documento,
      nombre: t.nombre,
      tipo_tercero: t.tipo_tercero,
      direccion: t.direccion,
      telefono: t.telefono,
      email: t.email,
      estado: t.estado,
      notas: t.notas,
      limite_credito: t.limite_credito,
      plazo_pago_dias: t.plazo_pago_dias,
      persona_contacto: t.persona_contacto,
      sector_economico: t.sector_economico,
      grupo_cliente: t.grupo_cliente,
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
      updateMut.mutate({ id: editing.id, data: form as TerceroUpdate });
    } else {
      createMut.mutate(form);
    }
  }

  function openDetail(t: Tercero) {
    setSelectedTercero(t);
    setDetailTab('info');
    setEditingDetail(false);
  }

  function startEditDetail() {
    if (!selectedTercero) return;
    setDetailForm({
      nombre: selectedTercero.nombre,
      tipo_tercero: selectedTercero.tipo_tercero,
      direccion: selectedTercero.direccion,
      telefono: selectedTercero.telefono,
      email: selectedTercero.email,
      notas: selectedTercero.notas,
      limite_credito: selectedTercero.limite_credito,
      plazo_pago_dias: selectedTercero.plazo_pago_dias,
      persona_contacto: selectedTercero.persona_contacto,
      sector_economico: selectedTercero.sector_economico,
      grupo_cliente: selectedTercero.grupo_cliente,
    });
    setEditingDetail(true);
  }

  function saveDetail() {
    if (!selectedTercero) return;
    updateMut.mutate({ id: selectedTercero.id, data: detailForm });
  }

  const saving = createMut.isPending || updateMut.isPending;

  // Detail panel for selected tercero
  const detailPanel = selectedTercero && (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 overflow-y-auto py-8">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{selectedTercero.nombre}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-gray-500">
                {selectedTercero.tipo_documento}: {selectedTercero.numero_documento}
              </span>
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                  selectedTercero.tipo_tercero === 'CLIENTE'
                    ? 'bg-blue-100 text-blue-700'
                    : selectedTercero.tipo_tercero === 'PROVEEDOR'
                    ? 'bg-purple-100 text-purple-700'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                {selectedTercero.tipo_tercero}
              </span>
              {selectedTercero.grupo_cliente && (
                <span className="inline-block rounded-full px-2 py-0.5 text-xs font-medium bg-amber-100 text-amber-700">
                  {selectedTercero.grupo_cliente}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={() => setSelectedTercero(null)}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            &times;
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-100 px-6">
          {(['info', 'historial', 'notas'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setDetailTab(tab)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                detailTab === tab
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'info' ? 'Informacion' : tab === 'historial' ? 'Historial' : 'Notas'}
            </button>
          ))}
        </div>

        <div className="px-6 py-4 max-h-[60vh] overflow-y-auto">
          {/* Info Tab */}
          {detailTab === 'info' && !editingDetail && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <InfoField label="Telefono" value={selectedTercero.telefono} />
                <InfoField label="Email" value={selectedTercero.email} />
                <InfoField label="Direccion" value={selectedTercero.direccion} />
                <InfoField label="Persona de contacto" value={selectedTercero.persona_contacto} />
                <InfoField label="Sector economico" value={selectedTercero.sector_economico} />
                <InfoField label="Grupo" value={selectedTercero.grupo_cliente} />
                <InfoField label="Limite credito" value={formatCurrency(selectedTercero.limite_credito)} />
                <InfoField
                  label="Plazo pago"
                  value={
                    selectedTercero.plazo_pago_dias > 0
                      ? `${selectedTercero.plazo_pago_dias} dias`
                      : 'Contado'
                  }
                />
              </div>
              <InfoField
                label="Estado"
                value={selectedTercero.estado ? 'Activo' : 'Inactivo'}
              />
            </div>
          )}

          {/* Info Tab - Editing */}
          {detailTab === 'info' && editingDetail && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Telefono</label>
                  <input
                    type="text"
                    value={detailForm.telefono || ''}
                    onChange={(e) => setDetailForm({ ...detailForm, telefono: e.target.value || null })}
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Email</label>
                  <input
                    type="email"
                    value={detailForm.email || ''}
                    onChange={(e) => setDetailForm({ ...detailForm, email: e.target.value || null })}
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Direccion</label>
                  <input
                    type="text"
                    value={detailForm.direccion || ''}
                    onChange={(e) => setDetailForm({ ...detailForm, direccion: e.target.value || null })}
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Persona contacto</label>
                  <input
                    type="text"
                    value={detailForm.persona_contacto || ''}
                    onChange={(e) =>
                      setDetailForm({ ...detailForm, persona_contacto: e.target.value || null })
                    }
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Sector economico</label>
                  <input
                    type="text"
                    value={detailForm.sector_economico || ''}
                    onChange={(e) =>
                      setDetailForm({ ...detailForm, sector_economico: e.target.value || null })
                    }
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Grupo cliente</label>
                  <select
                    value={detailForm.grupo_cliente || ''}
                    onChange={(e) =>
                      setDetailForm({ ...detailForm, grupo_cliente: e.target.value || null })
                    }
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    {GRUPOS_CLIENTE.map((g) => (
                      <option key={g} value={g}>
                        {g || '(Sin grupo)'}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Limite credito</label>
                  <input
                    type="number"
                    min={0}
                    step={1000}
                    value={detailForm.limite_credito || 0}
                    onChange={(e) =>
                      setDetailForm({ ...detailForm, limite_credito: Number(e.target.value) })
                    }
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Plazo pago (dias)</label>
                  <input
                    type="number"
                    min={0}
                    value={detailForm.plazo_pago_dias || 0}
                    onChange={(e) =>
                      setDetailForm({ ...detailForm, plazo_pago_dias: Number(e.target.value) })
                    }
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Historial Tab */}
          {detailTab === 'historial' && (
            <div className="space-y-4">
              {historial?.ventas && historial.ventas.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Ventas / Facturas</h4>
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50 border-b border-gray-100">
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Numero</th>
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Fecha</th>
                          <th className="text-right px-3 py-2 font-medium text-gray-500">Total</th>
                          <th className="text-center px-3 py-2 font-medium text-gray-500">Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historial.ventas.map((v) => (
                          <tr key={v.id} className="border-b border-gray-50">
                            <td className="px-3 py-2 font-mono text-xs">{v.numero}</td>
                            <td className="px-3 py-2 text-gray-600">{formatDate(v.fecha)}</td>
                            <td className="px-3 py-2 text-right font-medium">{formatCurrency(v.total)}</td>
                            <td className="px-3 py-2 text-center">
                              <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${statusColor(v.estado)}`}>
                                {v.estado}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {historial?.cotizaciones && historial.cotizaciones.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Cotizaciones</h4>
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50 border-b border-gray-100">
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Numero</th>
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Fecha</th>
                          <th className="text-right px-3 py-2 font-medium text-gray-500">Total</th>
                          <th className="text-center px-3 py-2 font-medium text-gray-500">Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historial.cotizaciones.map((c) => (
                          <tr key={c.id} className="border-b border-gray-50">
                            <td className="px-3 py-2 font-mono text-xs">{c.numero}</td>
                            <td className="px-3 py-2 text-gray-600">{formatDate(c.fecha)}</td>
                            <td className="px-3 py-2 text-right font-medium">{formatCurrency(c.total)}</td>
                            <td className="px-3 py-2 text-center">
                              <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${statusColor(c.estado)}`}>
                                {c.estado}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {(!historial?.ventas?.length && !historial?.cotizaciones?.length) && (
                <p className="text-center text-gray-400 py-8 text-sm">Sin historial de transacciones</p>
              )}
            </div>
          )}

          {/* Notas Tab */}
          {detailTab === 'notas' && (
            <div>
              {editingDetail ? (
                <textarea
                  value={detailForm.notas || ''}
                  onChange={(e) => setDetailForm({ ...detailForm, notas: e.target.value || null })}
                  rows={6}
                  placeholder="Notas sobre este cliente..."
                  className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                />
              ) : (
                <div className="bg-gray-50 rounded-lg p-4 min-h-[120px]">
                  {selectedTercero.notas ? (
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{selectedTercero.notas}</p>
                  ) : (
                    <p className="text-sm text-gray-400">Sin notas</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
          <div className="flex gap-2">
            {!editingDetail ? (
              <button
                onClick={startEditDetail}
                className="rounded-lg px-4 py-2 text-sm font-medium bg-amber-50 text-amber-700 hover:bg-amber-100 transition-colors"
              >
                Editar
              </button>
            ) : (
              <>
                <button
                  onClick={saveDetail}
                  disabled={updateMut.isPending}
                  className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors disabled:opacity-50"
                >
                  {updateMut.isPending ? 'Guardando...' : 'Guardar'}
                </button>
                <button
                  onClick={() => setEditingDetail(false)}
                  className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  Cancelar
                </button>
              </>
            )}
          </div>
          <button
            onClick={() => setSelectedTercero(null)}
            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Terceros</h1>
        <button
          onClick={openCreate}
          className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors"
        >
          + Nuevo Tercero
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="flex-1 max-w-sm">
          <SearchInput value={search} onChange={setSearch} placeholder="Buscar por nombre o documento..." />
        </div>
        <select
          value={filterTipo}
          onChange={(e) => setFilterTipo(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">Todos los tipos</option>
          {TIPOS_TERCERO.map((t) => (
            <option key={t} value={t}>{t}</option>
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
                <th className="text-left px-4 py-3 font-medium text-gray-500">Nombre</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Documento</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Tipo</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Grupo</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Telefono</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Estado</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => openDetail(t)}
                  className="border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer"
                >
                  <td className="px-4 py-3 font-medium text-gray-900">{t.nombre}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">
                    <span className="text-gray-400 mr-1">{t.tipo_documento}</span>
                    {t.numero_documento}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        t.tipo_tercero === 'CLIENTE'
                          ? 'bg-blue-100 text-blue-700'
                          : t.tipo_tercero === 'PROVEEDOR'
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {t.tipo_tercero}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{t.grupo_cliente || '-'}</td>
                  <td className="px-4 py-3 text-gray-500">{t.telefono || '-'}</td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        t.estado ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {t.estado ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => openEdit(t)}
                      className="text-xs text-primary-600 hover:text-primary-800 font-medium mr-3"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Desactivar este tercero?')) deleteMut.mutate(t.id);
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
              <p className="text-lg mb-2">Sin terceros</p>
              <p className="text-sm">Crea tu primer cliente o proveedor</p>
            </div>
          )}
        </div>
      )}

      {/* Create / Edit Modal */}
      <Modal open={modalOpen} onClose={closeModal} title={editing ? 'Editar Tercero' : 'Nuevo Tercero'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2">
              {error}
            </div>
          )}

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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Documento *</label>
              <select
                value={form.tipo_documento}
                onChange={(e) => setForm({ ...form, tipo_documento: e.target.value })}
                disabled={!!editing}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100"
              >
                {TIPOS_DOCUMENTO.map((td) => (
                  <option key={td} value={td}>
                    {TIPO_DOC_LABELS[td]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Numero Documento *</label>
              <input
                type="text"
                required
                disabled={!!editing}
                value={form.numero_documento}
                onChange={(e) => setForm({ ...form, numero_documento: e.target.value })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Tercero *</label>
            <div className="flex gap-4">
              {TIPOS_TERCERO.map((tt) => (
                <label key={tt} className="flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="radio"
                    name="tipo_tercero"
                    value={tt}
                    checked={form.tipo_tercero === tt}
                    onChange={(e) => setForm({ ...form, tipo_tercero: e.target.value })}
                    className="text-primary-500 focus:ring-primary-500"
                  />
                  {tt}
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={form.email || ''}
                onChange={(e) => setForm({ ...form, email: e.target.value || null })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Telefono</label>
              <input
                type="text"
                value={form.telefono || ''}
                onChange={(e) => setForm({ ...form, telefono: e.target.value || null })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Direccion</label>
            <input
              type="text"
              value={form.direccion || ''}
              onChange={(e) => setForm({ ...form, direccion: e.target.value || null })}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* CRM fields */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Persona contacto</label>
              <input
                type="text"
                value={form.persona_contacto || ''}
                onChange={(e) => setForm({ ...form, persona_contacto: e.target.value || null })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Grupo cliente</label>
              <select
                value={form.grupo_cliente || ''}
                onChange={(e) => setForm({ ...form, grupo_cliente: e.target.value || null })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {GRUPOS_CLIENTE.map((g) => (
                  <option key={g} value={g}>
                    {g || '(Sin grupo)'}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Limite credito</label>
              <input
                type="number"
                min={0}
                step={1000}
                value={form.limite_credito || 0}
                onChange={(e) => setForm({ ...form, limite_credito: Number(e.target.value) })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Plazo pago (dias)</label>
              <input
                type="number"
                min={0}
                value={form.plazo_pago_dias || 0}
                onChange={(e) => setForm({ ...form, plazo_pago_dias: Number(e.target.value) })}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
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

      {detailPanel}
    </div>
  );
}

function InfoField({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className="text-sm text-gray-900">{value || '-'}</p>
    </div>
  );
}
