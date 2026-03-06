import { HelpPanel } from '../components/tutorial/HelpPanel';
import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { crm } from '../api/endpoints';
import { formatCurrency } from '../utils/format';
import Modal from '../components/ui/Modal';
import SearchInput from '../components/ui/SearchInput';
import type { CrmDeal, CrmDealCreate } from '../types';

// Set to false to restore full CRM functionality
const CRM_UNDER_CONSTRUCTION = true;

function emptyForm(): CrmDealCreate {
  return {
    nombre: '',
    tercero_id: '',
    pipeline_id: '',
    stage_id: '',
    valor_estimado: 0,
  };
}

export default function CRMPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [filterEstado, setFilterEstado] = useState('ABIERTO');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState<CrmDeal | null>(null);
  const [form, setForm] = useState<CrmDealCreate>(emptyForm());
  const [error, setError] = useState('');

  // Fetch pipelines
  const { data: pipelines } = useQuery({
    queryKey: ['crm-pipelines'],
    queryFn: () => crm.pipelines.list().then((r) => r.data),
  });

  // Get default pipeline - memoized to prevent recalculation on every render
  const defaultPipeline = useMemo(
    () => pipelines?.find((p) => p.es_default) || pipelines?.[0],
    [pipelines]
  );

  // Fetch deals
  const { data: deals, isLoading } = useQuery({
    queryKey: ['crm-deals', filterEstado],
    queryFn: () =>
      crm.deals
        .list({
          pipeline_id: defaultPipeline?.id,
          estado_cierre: filterEstado || undefined,
        })
        .then((r) => r.data),
    enabled: !!defaultPipeline,
  });

  // Create deal mutation
  const createMut = useMutation({
    mutationFn: (data: CrmDealCreate) => crm.deals.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm-deals'] });
      closeModal();
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Error al crear deal'),
  });

  // Move deal mutation
  const moveDealMut = useMutation({
    mutationFn: ({ dealId, stageId }: { dealId: string; stageId: string }) =>
      crm.deals.moveStage(dealId, stageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm-deals'] });
    },
  });

  // Close deal mutation
  const closeDealMut = useMutation({
    mutationFn: ({ dealId, estado }: { dealId: string; estado: string }) =>
      crm.deals.close(dealId, estado),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm-deals'] });
      setDetailModalOpen(false);
    },
  });

  function openCreate() {
    setForm(emptyForm());
    setError('');
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setError('');
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.nombre || !form.tercero_id || !form.stage_id) {
      setError('Complete todos los campos requeridos');
      return;
    }
    // Create a new object instead of mutating state
    const dealData = {
      ...form,
      pipeline_id: defaultPipeline!.id,
    };
    createMut.mutate(dealData);
  }

  function handleDealClick(deal: CrmDeal) {
    setSelectedDeal(deal);
    setDetailModalOpen(true);
  }

  function handleCloseDeal(estado: 'GANADO' | 'PERDIDO' | 'ABANDONADO') {
    if (!selectedDeal) return;
    if (confirm(`¿Marcar este deal como ${estado}?`)) {
      closeDealMut.mutate({ dealId: selectedDeal.id, estado });
    }
  }

  // Drag & Drop handlers
  const [mobileStageFilter, setMobileStageFilter] = useState<string>('');
  const [draggedDealId, setDraggedDealId] = useState<string | null>(null);

  function handleDragStart(dealId: string) {
    setDraggedDealId(dealId);
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
  }

  function handleDrop(stageId: string) {
    if (draggedDealId) {
      moveDealMut.mutate({ dealId: draggedDealId, stageId });
      setDraggedDealId(null);
    }
  }

  // Filter deals by search
  const filteredDeals = deals?.filter((d) =>
    d.nombre.toLowerCase().includes(search.toLowerCase()) ||
    d.tercero_nombre?.toLowerCase().includes(search.toLowerCase())
  ) || [];

  // Group deals by stage
  const dealsByStage = defaultPipeline?.etapas.reduce((acc, stage) => {
    acc[stage.id] = filteredDeals.filter((d) => d.stage_id === stage.id);
    return acc;
  }, {} as Record<string, CrmDeal[]>) || {};

  const saving = createMut.isPending;

  if (CRM_UNDER_CONSTRUCTION) {
    return (
      <div>
        <h1 className="font-brand text-xl font-medium cv-text mb-6">CRM</h1>
        <div className="cv-card p-12 text-center cv-muted">
          <p className="text-lg mb-2">Módulo CRM</p>
          <p className="text-sm">Próximamente: pipelines, negocios y seguimiento de clientes</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-brand text-xl font-medium cv-text">Conversión de Ventas</h1>
        <button onClick={openCreate} className="cv-btn cv-btn-primary">
          + Nuevo Deal
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="flex-1 max-w-sm">
          <SearchInput value={search} onChange={setSearch} placeholder="Buscar deal o cliente..." />
        </div>
        <select
          value={filterEstado}
          onChange={(e) => setFilterEstado(e.target.value)}
          className="cv-input w-auto"
        >
          <option value="">Todos los estados</option>
          <option value="ABIERTO">Abierto</option>
          <option value="GANADO">Ganado</option>
          <option value="PERDIDO">Perdido</option>
          <option value="ABANDONADO">Abandonado</option>
        </select>
      </div>

      {/* Kanban Board */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 cv-elevated rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          {/* Desktop: Kanban columns */}
          <div className="hidden md:block cv-card p-4 overflow-x-auto">
            <div className="flex gap-4 min-w-max">
              {defaultPipeline?.etapas
                .sort((a, b) => a.orden - b.orden)
                .map((stage) => (
                  <div
                    key={stage.id}
                    className="flex-shrink-0 w-72"
                    onDragOver={handleDragOver}
                    onDrop={() => handleDrop(stage.id)}
                  >
                    {/* Stage Header */}
                    <div className="mb-3 pb-2 border-b cv-divider">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold cv-text">{stage.nombre}</h3>
                        <span className="text-xs cv-muted">
                          {dealsByStage[stage.id]?.length || 0}
                        </span>
                      </div>
                      <p className="text-xs cv-muted mt-1">Prob: {stage.probabilidad}%</p>
                    </div>

                    {/* Deals */}
                    <div className="space-y-2">
                      {dealsByStage[stage.id]?.length === 0 ? (
                        <p className="text-xs cv-muted text-center py-4">Sin deals</p>
                      ) : (
                        dealsByStage[stage.id]?.map((deal) => (
                          <div
                            key={deal.id}
                            draggable
                            onDragStart={() => handleDragStart(deal.id)}
                            onClick={() => handleDealClick(deal)}
                            className={`cv-card-elevated rounded-lg p-3 border cv-divider cursor-move hover:border-[var(--cv-primary)] hover:shadow-sm transition-all ${
                              draggedDealId === deal.id ? 'opacity-50' : ''
                            }`}
                          >
                            <h4 className="text-sm font-medium cv-text mb-1 line-clamp-1">
                              {deal.nombre}
                            </h4>
                            {deal.tercero_nombre && (
                              <p className="text-xs cv-muted mb-2">{deal.tercero_nombre}</p>
                            )}
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-semibold cv-primary">
                                {formatCurrency(deal.valor_estimado)}
                              </span>
                              {deal.estado_cierre !== 'ABIERTO' && (
                                <span className={`cv-badge ${deal.estado_cierre === 'GANADO' ? 'cv-badge-positive' : 'cv-badge-negative'}`}>
                                  {deal.estado_cierre}
                                </span>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Mobile: Stage filter + vertical list */}
          <div className="md:hidden space-y-3">
            {/* Stage filter tabs */}
            <div className="overflow-x-auto pb-1">
              <div className="flex gap-1.5 cv-elevated p-1 rounded-lg w-max">
                <button
                  onClick={() => setMobileStageFilter('')}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                    !mobileStageFilter ? 'cv-surface cv-text shadow-sm' : 'cv-muted'
                  }`}
                >
                  Todas ({filteredDeals.length})
                </button>
                {defaultPipeline?.etapas
                  .sort((a, b) => a.orden - b.orden)
                  .map((stage) => (
                    <button
                      key={stage.id}
                      onClick={() => setMobileStageFilter(stage.id)}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                        mobileStageFilter === stage.id ? 'cv-surface cv-text shadow-sm' : 'cv-muted'
                      }`}
                    >
                      {stage.nombre} ({dealsByStage[stage.id]?.length || 0})
                    </button>
                  ))}
              </div>
            </div>

            {/* Deal cards */}
            {(mobileStageFilter
              ? filteredDeals.filter((d) => d.stage_id === mobileStageFilter)
              : filteredDeals
            ).length === 0 ? (
              <div className="cv-card p-8 text-center text-sm cv-muted">
                Sin deals en esta etapa
              </div>
            ) : (
              (mobileStageFilter
                ? filteredDeals.filter((d) => d.stage_id === mobileStageFilter)
                : filteredDeals
              ).map((deal) => (
                <div
                  key={deal.id}
                  onClick={() => handleDealClick(deal)}
                  className="cv-card p-4 cursor-pointer active:opacity-80 transition-opacity"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-semibold cv-text truncate">{deal.nombre}</h4>
                      {deal.tercero_nombre && (
                        <p className="text-xs cv-muted mt-0.5">{deal.tercero_nombre}</p>
                      )}
                    </div>
                    <span className="text-sm font-bold cv-primary ml-3">
                      {formatCurrency(deal.valor_estimado)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="cv-badge cv-badge-neutral">
                      {deal.stage_nombre}
                    </span>
                    {deal.estado_cierre !== 'ABIERTO' && (
                      <span className={`cv-badge ${deal.estado_cierre === 'GANADO' ? 'cv-badge-positive' : 'cv-badge-negative'}`}>
                        {deal.estado_cierre}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}

      {/* Create/Edit Modal */}
      <Modal open={modalOpen} onClose={closeModal} title="Nuevo Deal" maxWidth="max-w-lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="cv-alert-error px-4 py-2 text-sm">{error}</div>
          )}

          <div>
            <label className="block text-sm font-medium cv-muted mb-1">
              Nombre del Deal *
            </label>
            <input
              type="text"
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              className="cv-input"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium cv-muted mb-1">
              Cliente (ID) *
            </label>
            <input
              type="text"
              value={form.tercero_id}
              onChange={(e) => setForm({ ...form, tercero_id: e.target.value })}
              placeholder="UUID del tercero"
              className="cv-input"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium cv-muted mb-1">Etapa *</label>
            <select
              value={form.stage_id}
              onChange={(e) => setForm({ ...form, stage_id: e.target.value })}
              className="cv-input"
              required
            >
              <option value="">Seleccione etapa</option>
              {defaultPipeline?.etapas.map((stage) => (
                <option key={stage.id} value={stage.id}>
                  {stage.nombre}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium cv-muted mb-1">
              Valor Estimado
            </label>
            <input
              type="number"
              value={form.valor_estimado}
              onChange={(e) => setForm({ ...form, valor_estimado: Number(e.target.value) })}
              className="cv-input"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button type="button" onClick={closeModal} className="cv-btn cv-btn-secondary flex-1">
              Cancelar
            </button>
            <button type="submit" disabled={saving} className="cv-btn cv-btn-primary flex-1">
              {saving ? 'Guardando...' : 'Crear Deal'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Detail Modal */}
      {selectedDeal && (
        <Modal
          open={detailModalOpen}
          onClose={() => setDetailModalOpen(false)}
          title={selectedDeal.nombre}
          maxWidth="max-w-2xl"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="cv-muted">Cliente</p>
                <p className="font-medium cv-text">{selectedDeal.tercero_nombre || 'N/A'}</p>
              </div>
              <div>
                <p className="cv-muted">Valor</p>
                <p className="font-semibold cv-primary">
                  {formatCurrency(selectedDeal.valor_estimado)}
                </p>
              </div>
              <div>
                <p className="cv-muted">Etapa</p>
                <p className="font-medium cv-text">{selectedDeal.stage_nombre}</p>
              </div>
              <div>
                <p className="cv-muted">Estado</p>
                <span className={`cv-badge ${
                  selectedDeal.estado_cierre === 'ABIERTO'
                    ? 'cv-badge-primary'
                    : selectedDeal.estado_cierre === 'GANADO'
                    ? 'cv-badge-positive'
                    : 'cv-badge-negative'
                }`}>
                  {selectedDeal.estado_cierre}
                </span>
              </div>
              {selectedDeal.usuario_nombre && (
                <div>
                  <p className="cv-muted">Asignado a</p>
                  <p className="font-medium cv-text">{selectedDeal.usuario_nombre}</p>
                </div>
              )}
              {selectedDeal.fecha_cierre_estimada && (
                <div>
                  <p className="cv-muted">Cierre estimado</p>
                  <p className="font-medium cv-text">
                    {new Date(selectedDeal.fecha_cierre_estimada).toLocaleDateString('es-CO')}
                  </p>
                </div>
              )}
            </div>

            {selectedDeal.estado_cierre === 'ABIERTO' && (
              <div className="flex flex-col sm:flex-row gap-2 pt-4 border-t cv-divider">
                <button
                  onClick={() => handleCloseDeal('GANADO')}
                  disabled={closeDealMut.isPending}
                  className="cv-btn flex-1 bg-[var(--cv-positive)] text-[#1A1A1A] hover:opacity-85 disabled:opacity-50"
                >
                  Marcar Ganado
                </button>
                <button
                  onClick={() => handleCloseDeal('PERDIDO')}
                  disabled={closeDealMut.isPending}
                  className="cv-btn cv-btn-danger flex-1"
                >
                  Marcar Perdido
                </button>
              </div>
            )}
          </div>
        </Modal>
      )}
      <HelpPanel modulo="comercial" />
    </div>
  );
}
