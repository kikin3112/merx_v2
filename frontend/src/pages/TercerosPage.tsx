import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { terceros } from '../api/endpoints';
import { formatCurrency, formatDate, statusColor } from '../utils/format';
import Modal from '../components/ui/Modal';
import SearchInput from '../components/ui/SearchInput';
import DataCard from '../components/ui/DataCard';
import type { Tercero, TerceroCreate, TerceroUpdate } from '../types';

const TIPOS_DOCUMENTO = ['CC', 'NIT', 'CE', 'PAS', 'TI'] as const;
const TIPOS_TERCERO = ['CLIENTE', 'PROVEEDOR', 'AMBOS'] as const;
const GRUPOS_CLIENTE = ['', 'VIP', 'Mayorista', 'Minorista', 'Corporativo'] as const;

const TIPO_DOC_LABELS: Record<string, string> = {
  CC: 'Cedula de ciudadania',
  NIT: 'NIT',
  CE: 'Cedula de extranjeria',
  PAS: 'Pasaporte',
  TI: 'Tarjeta de identidad',
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
      <div className="cv-card shadow-xl w-full max-w-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b cv-divider">
          <div>
            <h2 className="text-lg font-semibold cv-text">{selectedTercero.nombre}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs cv-muted">
                {selectedTercero.tipo_documento}: {selectedTercero.numero_documento}
              </span>
              <span
                className={`cv-badge ${
                  selectedTercero.tipo_tercero === 'CLIENTE'
                    ? 'cv-badge-primary'
                    : selectedTercero.tipo_tercero === 'PROVEEDOR'
                    ? 'cv-badge-accent'
                    : 'cv-badge-neutral'
                }`}
              >
                {selectedTercero.tipo_tercero}
              </span>
              {selectedTercero.grupo_cliente && (
                <span className="cv-badge cv-badge-accent">
                  {selectedTercero.grupo_cliente}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={() => setSelectedTercero(null)}
            className="cv-icon-btn text-xl leading-none p-1"
          >
            &times;
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b cv-divider px-6">
          {(['info', 'historial', 'notas'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setDetailTab(tab)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                detailTab === tab
                  ? 'border-[var(--cv-primary)] text-[var(--cv-primary)]'
                  : 'border-transparent cv-muted'
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="cv-label mb-1">Teléfono</label>
                  <input
                    type="text"
                    value={detailForm.telefono || ''}
                    onChange={(e) => setDetailForm({ ...detailForm, telefono: e.target.value || null })}
                    className="cv-input"
                  />
                </div>
                <div>
                  <label className="cv-label mb-1">Email</label>
                  <input
                    type="email"
                    value={detailForm.email || ''}
                    onChange={(e) => setDetailForm({ ...detailForm, email: e.target.value || null })}
                    className="cv-input"
                  />
                </div>
                <div>
                  <label className="cv-label mb-1">Dirección</label>
                  <input
                    type="text"
                    value={detailForm.direccion || ''}
                    onChange={(e) => setDetailForm({ ...detailForm, direccion: e.target.value || null })}
                    className="cv-input"
                  />
                </div>
                <div>
                  <label className="cv-label mb-1">Persona contacto</label>
                  <input
                    type="text"
                    value={detailForm.persona_contacto || ''}
                    onChange={(e) =>
                      setDetailForm({ ...detailForm, persona_contacto: e.target.value || null })
                    }
                    className="cv-input"
                  />
                </div>
                <div>
                  <label className="cv-label mb-1">Sector económico</label>
                  <input
                    type="text"
                    value={detailForm.sector_economico || ''}
                    onChange={(e) =>
                      setDetailForm({ ...detailForm, sector_economico: e.target.value || null })
                    }
                    className="cv-input"
                  />
                </div>
                <div>
                  <label className="cv-label mb-1">Grupo cliente</label>
                  <select
                    value={detailForm.grupo_cliente || ''}
                    onChange={(e) =>
                      setDetailForm({ ...detailForm, grupo_cliente: e.target.value || null })
                    }
                    className="cv-input"
                  >
                    {GRUPOS_CLIENTE.map((g) => (
                      <option key={g} value={g}>
                        {g || '(Sin grupo)'}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="cv-label mb-1">Limite credito</label>
                  <input
                    type="number"
                    min={0}
                    step={1000}
                    value={detailForm.limite_credito || 0}
                    onChange={(e) =>
                      setDetailForm({ ...detailForm, limite_credito: Number(e.target.value) })
                    }
                    className="cv-input"
                  />
                </div>
                <div>
                  <label className="cv-label mb-1">Plazo pago (días)</label>
                  <input
                    type="number"
                    min={0}
                    value={detailForm.plazo_pago_dias || 0}
                    onChange={(e) =>
                      setDetailForm({ ...detailForm, plazo_pago_dias: Number(e.target.value) })
                    }
                    className="cv-input"
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
                  <h4 className="text-sm font-medium cv-text mb-2">Ventas / Facturas</h4>
                  <div className="cv-card overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="cv-table-header">
                        <tr>
                          <th className="text-left">Numero</th>
                          <th className="text-left">Fecha</th>
                          <th className="text-right">Total</th>
                          <th className="text-center">Estado</th>
                        </tr>
                      </thead>
                      <tbody className="cv-table-body">
                        {historial.ventas.map((v) => (
                          <tr key={v.id}>
                            <td className="font-mono text-xs">{v.numero}</td>
                            <td className="cv-muted">{formatDate(v.fecha)}</td>
                            <td className="text-right font-medium">{formatCurrency(v.total)}</td>
                            <td className="text-center">
                              <span className={`cv-badge ${statusColor(v.estado)}`}>{v.estado}</span>
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
                  <h4 className="text-sm font-medium cv-text mb-2">Cotizaciones</h4>
                  <div className="cv-card overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="cv-table-header">
                        <tr>
                          <th className="text-left">Numero</th>
                          <th className="text-left">Fecha</th>
                          <th className="text-right">Total</th>
                          <th className="text-center">Estado</th>
                        </tr>
                      </thead>
                      <tbody className="cv-table-body">
                        {historial.cotizaciones.map((c) => (
                          <tr key={c.id}>
                            <td className="font-mono text-xs">{c.numero}</td>
                            <td className="cv-muted">{formatDate(c.fecha)}</td>
                            <td className="text-right font-medium">{formatCurrency(c.total)}</td>
                            <td className="text-center">
                              <span className={`cv-badge ${statusColor(c.estado)}`}>{c.estado}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {(!historial?.ventas?.length && !historial?.cotizaciones?.length) && (
                <p className="text-center cv-muted py-8 text-sm">Sin historial de transacciones</p>
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
                  className="cv-input resize-none"
                />
              ) : (
                <div className="cv-elevated rounded-lg p-4 min-h-[120px]">
                  {selectedTercero.notas ? (
                    <p className="text-sm cv-text whitespace-pre-wrap">{selectedTercero.notas}</p>
                  ) : (
                    <p className="text-sm cv-muted">Sin notas</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t cv-divider">
          <div className="flex gap-2">
            {!editingDetail ? (
              <button
                onClick={startEditDetail}
                className="cv-btn rounded-lg px-4 py-2 text-sm font-medium bg-[var(--cv-accent-dim)] text-[var(--cv-accent)] hover:opacity-80 transition-opacity"
              >
                Editar
              </button>
            ) : (
              <>
                <button
                  onClick={saveDetail}
                  disabled={updateMut.isPending}
                  className="cv-btn cv-btn-primary"
                >
                  {updateMut.isPending ? 'Guardando...' : 'Guardar'}
                </button>
                <button
                  onClick={() => setEditingDetail(false)}
                  className="cv-btn cv-btn-secondary"
                >
                  Cancelar
                </button>
              </>
            )}
          </div>
          <button
            onClick={() => setSelectedTercero(null)}
            className="cv-btn cv-btn-secondary"
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
        <h1 className="font-brand text-xl font-medium cv-text">Terceros</h1>
        <button onClick={openCreate} className="cv-btn cv-btn-primary">
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
          className="cv-input w-auto"
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
            <div key={i} className="h-16 cv-elevated rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block cv-card overflow-hidden">
            <table className="w-full text-sm">
              <thead className="cv-table-header">
                <tr>
                  <th className="text-left">Nombre</th>
                  <th className="text-left">Documento</th>
                  <th className="text-left">Tipo</th>
                  <th className="text-left">Grupo</th>
                  <th className="text-left">Teléfono</th>
                  <th className="text-center">Estado</th>
                  <th className="text-center">Acciones</th>
                </tr>
              </thead>
              <tbody className="cv-table-body">
                {data?.map((t) => (
                  <tr
                    key={t.id}
                    onClick={() => openDetail(t)}
                    className="cursor-pointer"
                  >
                    <td className="font-medium cv-text">{t.nombre}</td>
                    <td className="font-mono text-xs cv-muted">
                      <span className="opacity-60 mr-1">{t.tipo_documento}</span>
                      {t.numero_documento}
                    </td>
                    <td>
                      <span className={`cv-badge ${
                        t.tipo_tercero === 'CLIENTE' ? 'cv-badge-primary'
                        : t.tipo_tercero === 'PROVEEDOR' ? 'cv-badge-accent'
                        : 'cv-badge-neutral'
                      }`}>
                        {t.tipo_tercero}
                      </span>
                    </td>
                    <td className="cv-muted text-xs">{t.grupo_cliente || '-'}</td>
                    <td className="cv-muted">{t.telefono || '-'}</td>
                    <td className="text-center">
                      <span className={`cv-badge ${t.estado ? 'cv-badge-positive' : 'cv-badge-negative'}`}>
                        {t.estado ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="text-center" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => openEdit(t)}
                        className="text-xs text-[var(--cv-primary)] hover:opacity-70 font-medium mr-3"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => {
                          if (confirm('Desactivar este tercero?')) deleteMut.mutate(t.id);
                        }}
                        className="text-xs cv-negative font-medium"
                      >
                        Eliminar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data?.length === 0 && (
              <div className="text-center py-12 cv-muted">
                <p className="text-lg mb-2">Sin terceros</p>
                <p className="text-sm">Crea tu primer cliente o proveedor</p>
              </div>
            )}
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {data?.map((t) => (
              <DataCard
                key={t.id}
                title={t.nombre}
                subtitle={`${TIPO_DOC_LABELS[t.tipo_documento] || t.tipo_documento}: ${t.numero_documento}`}
                badge={
                  <span className={`cv-badge ${t.estado ? 'cv-badge-positive' : 'cv-badge-negative'}`}>
                    {t.estado ? 'Activo' : 'Inactivo'}
                  </span>
                }
                fields={[
                  {
                    label: 'Tipo',
                    value: (
                      <span className={`cv-badge ${
                        t.tipo_tercero === 'CLIENTE' ? 'cv-badge-primary'
                        : t.tipo_tercero === 'PROVEEDOR' ? 'cv-badge-accent'
                        : 'cv-badge-neutral'
                      }`}>
                        {t.tipo_tercero}
                      </span>
                    ),
                  },
                  { label: 'Contacto', value: t.telefono || t.email || '-' },
                ]}
                onClick={() => openDetail(t)}
                actions={
                  <>
                    <button
                      onClick={() => openEdit(t)}
                      className="flex-1 text-center py-2 text-sm font-medium text-[var(--cv-primary)] hover:opacity-70 rounded-lg transition-opacity"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Desactivar este tercero?')) deleteMut.mutate(t.id);
                      }}
                      className="flex-1 text-center py-2 text-sm font-medium cv-negative rounded-lg"
                    >
                      Eliminar
                    </button>
                  </>
                }
              />
            ))}
            {data?.length === 0 && (
              <div className="text-center py-12 cv-muted">
                <p className="text-lg mb-2">Sin terceros</p>
                <p className="text-sm">Crea tu primer cliente o proveedor</p>
              </div>
            )}
          </div>
        </>
      )}

      {/* Create / Edit Modal */}
      <Modal open={modalOpen} onClose={closeModal} title={editing ? 'Editar Tercero' : 'Nuevo Tercero'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="cv-alert-error px-4 py-2 text-sm">{error}</div>}

          <div>
            <label className="cv-label mb-1">Nombre *</label>
            <input
              type="text"
              required
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              className="cv-input"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="cv-label mb-1">Tipo de documento *</label>
              <select
                value={form.tipo_documento}
                onChange={(e) => setForm({ ...form, tipo_documento: e.target.value })}
                disabled={!!editing}
                className="cv-input disabled:opacity-50"
              >
                {TIPOS_DOCUMENTO.map((td) => (
                  <option key={td} value={td}>{TIPO_DOC_LABELS[td]}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="cv-label mb-1">Numero de documento *</label>
              <input
                type="text"
                required
                disabled={!!editing}
                value={form.numero_documento}
                onChange={(e) => setForm({ ...form, numero_documento: e.target.value })}
                className="cv-input disabled:opacity-50"
              />
            </div>
          </div>

          <div>
            <label className="cv-label mb-1">Tipo de tercero *</label>
            <div className="flex gap-4">
              {TIPOS_TERCERO.map((tt) => (
                <label key={tt} className="flex items-center gap-2 text-sm cv-text">
                  <input
                    type="radio"
                    name="tipo_tercero"
                    value={tt}
                    checked={form.tipo_tercero === tt}
                    onChange={(e) => setForm({ ...form, tipo_tercero: e.target.value })}
                    className="text-[var(--cv-primary)] focus:ring-[var(--cv-primary)]"
                  />
                  {tt}
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="cv-label mb-1">Email</label>
              <input type="email" value={form.email || ''} onChange={(e) => setForm({ ...form, email: e.target.value || null })} className="cv-input" />
            </div>
            <div>
              <label className="cv-label mb-1">Teléfono</label>
              <input type="text" value={form.telefono || ''} onChange={(e) => setForm({ ...form, telefono: e.target.value || null })} className="cv-input" />
            </div>
          </div>

          <div>
            <label className="cv-label mb-1">Dirección</label>
            <input type="text" value={form.direccion || ''} onChange={(e) => setForm({ ...form, direccion: e.target.value || null })} className="cv-input" />
          </div>

          {/* CRM fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="cv-label mb-1">Persona contacto</label>
              <input type="text" value={form.persona_contacto || ''} onChange={(e) => setForm({ ...form, persona_contacto: e.target.value || null })} className="cv-input" />
            </div>
            <div>
              <label className="cv-label mb-1">Grupo cliente</label>
              <select value={form.grupo_cliente || ''} onChange={(e) => setForm({ ...form, grupo_cliente: e.target.value || null })} className="cv-input">
                {GRUPOS_CLIENTE.map((g) => <option key={g} value={g}>{g || '(Sin grupo)'}</option>)}
              </select>
            </div>
            <div>
              <label className="cv-label mb-1">Limite credito</label>
              <input type="number" min={0} step={1000} value={form.limite_credito || 0} onChange={(e) => setForm({ ...form, limite_credito: Number(e.target.value) })} className="cv-input" />
            </div>
            <div>
              <label className="cv-label mb-1">Plazo pago (días)</label>
              <input type="number" min={0} value={form.plazo_pago_dias || 0} onChange={(e) => setForm({ ...form, plazo_pago_dias: Number(e.target.value) })} className="cv-input" />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm cv-text">
              <input
                type="checkbox"
                checked={form.estado ?? true}
                onChange={(e) => setForm({ ...form, estado: e.target.checked })}
                className="rounded text-[var(--cv-primary)] focus:ring-[var(--cv-primary)]"
              />
              Activo
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t cv-divider">
            <button type="button" onClick={closeModal} className="cv-btn cv-btn-secondary">
              Cancelar
            </button>
            <button type="submit" disabled={saving} className="cv-btn cv-btn-primary">
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
      <p className="text-xs cv-muted mb-0.5">{label}</p>
      <p className="text-sm cv-text">{value || '-'}</p>
    </div>
  );
}
