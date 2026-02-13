import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tenants } from '../api/endpoints';
import { formatCurrency, formatDate } from '../utils/format';
import Modal from '../components/ui/Modal';
import type {
  TenantDetail,
  PlanWithStats,
  PlanCreate,
  PlanUpdate,
  SaaSDashboardKPIs,
  TenantMetricas,
  Suscripcion,
  PagoHistorial,
  UsuarioTenantDetail,
} from '../types';

// ============================================================================
// HELPERS
// ============================================================================

const estadoColor: Record<string, string> = {
  activo: 'bg-green-100 text-green-700',
  trial: 'bg-blue-100 text-blue-700',
  suspendido: 'bg-red-100 text-red-700',
  cancelado: 'bg-gray-200 text-gray-600',
  pendiente: 'bg-yellow-100 text-yellow-700',
};

const pagoEstadoColor: Record<string, string> = {
  pendiente: 'bg-yellow-100 text-yellow-700',
  aprobado: 'bg-green-100 text-green-700',
  rechazado: 'bg-red-100 text-red-700',
  reembolsado: 'bg-purple-100 text-purple-700',
};

const ROLES = ['admin', 'operador', 'contador', 'vendedor', 'readonly'];

function ProgressBar({ value, max, label }: { value: number; max: number; label: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  const color = pct < 70 ? 'bg-green-500' : pct < 90 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium text-gray-900">{value} / {max}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function TenantsPage() {
  const qc = useQueryClient();

  // --- State ---
  const [activeTab, setActiveTab] = useState<'tenants' | 'planes'>('tenants');
  const [filtroEstado, setFiltroEstado] = useState('');
  const [busqueda, setBusqueda] = useState('');

  // Tenant detail modal
  const [selectedTenant, setSelectedTenant] = useState<TenantDetail | null>(null);
  const [detailTab, setDetailTab] = useState<'info' | 'usuarios' | 'suscripcion' | 'metricas'>('info');

  // Plan modal
  const [planModal, setPlanModal] = useState(false);
  const [editingPlan, setEditingPlan] = useState<PlanWithStats | null>(null);

  // Error banner
  const [error, setError] = useState<string | null>(null);

  function showError(msg: string) {
    setError(msg);
    setTimeout(() => setError(null), 6000);
  }

  // --- Queries ---
  const { data: kpis } = useQuery<SaaSDashboardKPIs>({
    queryKey: ['saas-dashboard'],
    queryFn: () => tenants.dashboard().then((r) => r.data),
  });

  const { data: tenantsList, isLoading } = useQuery<TenantDetail[]>({
    queryKey: ['tenants', filtroEstado, busqueda],
    queryFn: () =>
      tenants.list({
        ...(filtroEstado ? { estado: filtroEstado } : {}),
        ...(busqueda ? { busqueda } : {}),
      }).then((r) => r.data),
  });

  const { data: planes, isLoading: loadingPlanes } = useQuery<PlanWithStats[]>({
    queryKey: ['planes-admin'],
    queryFn: () => tenants.planes.list().then((r) => r.data),
  });

  // Detail queries (enabled when modal open)
  const { data: usuarios, isLoading: loadingUsuarios } = useQuery<UsuarioTenantDetail[]>({
    queryKey: ['tenant-usuarios', selectedTenant?.id],
    queryFn: () => tenants.usuarios(selectedTenant!.id).then((r) => r.data),
    enabled: !!selectedTenant && detailTab === 'usuarios',
  });

  const { data: metricas } = useQuery<TenantMetricas>({
    queryKey: ['tenant-metricas', selectedTenant?.id],
    queryFn: () => tenants.metricas(selectedTenant!.id).then((r) => r.data),
    enabled: !!selectedTenant && detailTab === 'metricas',
  });

  const { data: suscripciones } = useQuery<Suscripcion[]>({
    queryKey: ['tenant-suscripciones', selectedTenant?.id],
    queryFn: () => tenants.suscripciones(selectedTenant!.id).then((r) => r.data),
    enabled: !!selectedTenant && detailTab === 'suscripcion',
  });

  const { data: pagos } = useQuery<PagoHistorial[]>({
    queryKey: ['tenant-pagos', selectedTenant?.id],
    queryFn: () => tenants.pagos(selectedTenant!.id).then((r) => r.data),
    enabled: !!selectedTenant && detailTab === 'suscripcion',
  });

  // --- Mutations ---
  const invalidateAll = () => {
    qc.invalidateQueries({ queryKey: ['tenants'] });
    qc.invalidateQueries({ queryKey: ['saas-dashboard'] });
    qc.invalidateQueries({ queryKey: ['planes-admin'] });
  };

  const suspenderMut = useMutation({
    mutationFn: (id: string) => tenants.suspender(id),
    onSuccess: () => { invalidateAll(); setSelectedTenant(null); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al suspender'),
  });

  const reactivarMut = useMutation({
    mutationFn: (id: string) => tenants.reactivar(id),
    onSuccess: () => { invalidateAll(); setSelectedTenant(null); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al reactivar'),
  });

  const cancelarMut = useMutation({
    mutationFn: (id: string) => tenants.cancelar(id),
    onSuccess: () => { invalidateAll(); setSelectedTenant(null); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al cancelar'),
  });

  const cambiarPlanMut = useMutation({
    mutationFn: ({ id, plan_id }: { id: string; plan_id: string }) =>
      tenants.cambiarPlan(id, plan_id),
    onSuccess: () => { invalidateAll(); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al cambiar plan'),
  });

  const extenderTrialMut = useMutation({
    mutationFn: ({ id, dias }: { id: string; dias: number }) =>
      tenants.extenderTrial(id, dias),
    onSuccess: () => { invalidateAll(); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al extender trial'),
  });

  const updateTenantMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      tenants.update(id, data),
    onSuccess: () => { invalidateAll(); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al actualizar'),
  });

  const cambiarRolMut = useMutation({
    mutationFn: ({ tid, uid, rol }: { tid: string; uid: string; rol: string }) =>
      tenants.cambiarRolUsuario(tid, uid, rol),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['tenant-usuarios'] }); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al cambiar rol'),
  });

  const removeUsuarioMut = useMutation({
    mutationFn: ({ tid, uid }: { tid: string; uid: string }) =>
      tenants.removeUsuario(tid, uid),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['tenant-usuarios'] }); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al remover usuario'),
  });

  // Plan mutations
  const crearPlanMut = useMutation({
    mutationFn: (data: PlanCreate) => tenants.planes.create(data),
    onSuccess: () => { invalidateAll(); setPlanModal(false); setEditingPlan(null); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al crear plan'),
  });

  const updatePlanMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: PlanUpdate }) =>
      tenants.planes.update(id, data),
    onSuccess: () => { invalidateAll(); setPlanModal(false); setEditingPlan(null); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al actualizar plan'),
  });

  const deletePlanMut = useMutation({
    mutationFn: (id: string) => tenants.planes.delete(id),
    onSuccess: () => { invalidateAll(); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al desactivar plan'),
  });

  // --- Helpers ---
  function getPlanNombre(planId: string): string {
    return planes?.find((p) => p.id === planId)?.nombre || 'N/A';
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div>
      {/* Error banner */}
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 ml-4">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      )}

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Centro de Control SaaS</h1>
        <p className="text-sm text-gray-500 mt-1">Panel de SuperAdmin</p>
      </div>

      {/* KPI Cards */}
      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <KPICard
            title="Total Tenants"
            value={String(kpis.total_tenants)}
            subtitle={`${kpis.tenants_activos} activos`}
          />
          <KPICard
            title="MRR"
            value={formatCurrency(kpis.mrr)}
            subtitle="Ingreso recurrente mensual"
          />
          <KPICard
            title="Nuevos (30d)"
            value={String(kpis.nuevos_ultimos_30_dias)}
            subtitle={`${kpis.tenants_trial} en trial`}
          />
          <KPICard
            title="Churn"
            value={`${kpis.churn_rate}%`}
            subtitle={`${kpis.tenants_cancelados} cancelados`}
            negative={kpis.churn_rate > 5}
          />
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-4">
        {(['tenants', 'planes'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'tenants' ? 'Tenants' : 'Planes'}
          </button>
        ))}
      </div>

      {/* TAB: Tenants */}
      {activeTab === 'tenants' && (
        <>
          <div className="flex flex-col sm:flex-row gap-3 mb-4">
            <input
              type="text"
              placeholder="Buscar por nombre, slug, NIT o email..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <div className="flex gap-2 flex-wrap">
              {['', 'activo', 'trial', 'suspendido', 'cancelado'].map((estado) => (
                <button
                  key={estado}
                  onClick={() => setFiltroEstado(estado)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                    filtroEstado === estado
                      ? 'bg-primary-500 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {estado || 'Todos'}
                </button>
              ))}
            </div>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-14 bg-gray-200 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Tenant</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500 hidden md:table-cell">Plan</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500 hidden sm:table-cell">Email</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500 hidden lg:table-cell">Creado</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-500">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {tenantsList?.map((t) => (
                    <tr
                      key={t.id}
                      onClick={() => { setSelectedTenant(t); setDetailTab('info'); }}
                      className="border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer"
                    >
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{t.nombre}</p>
                        <p className="text-xs text-gray-500">{t.slug}</p>
                      </td>
                      <td className="px-4 py-3 text-gray-600 hidden md:table-cell">
                        {getPlanNombre(t.plan_id)}
                      </td>
                      <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{t.email_contacto}</td>
                      <td className="px-4 py-3 text-gray-600 hidden lg:table-cell">{formatDate(t.created_at)}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${estadoColor[t.estado] || 'bg-gray-100 text-gray-600'}`}>
                          {t.estado}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {tenantsList?.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg mb-2">Sin tenants</p>
                  <p className="text-sm">No se encontraron tenants con los filtros aplicados</p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* TAB: Planes */}
      {activeTab === 'planes' && (
        <>
          <div className="flex justify-end mb-4">
            <button
              onClick={() => { setEditingPlan(null); setPlanModal(true); }}
              className="rounded-lg bg-primary-500 text-white px-4 py-2 text-sm font-medium hover:bg-primary-600 transition-colors"
            >
              + Nuevo Plan
            </button>
          </div>

          {loadingPlanes ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 bg-gray-200 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Nombre</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Precio/mes</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-500 hidden md:table-cell">Limites</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-500">Tenants</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-500">Estado</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-500">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {planes?.map((p) => (
                    <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{p.nombre}</p>
                        {p.descripcion && <p className="text-xs text-gray-500 truncate max-w-[200px]">{p.descripcion}</p>}
                      </td>
                      <td className="px-4 py-3 text-right font-medium">{formatCurrency(p.precio_mensual)}</td>
                      <td className="px-4 py-3 text-center hidden md:table-cell">
                        <span className="text-xs text-gray-500">
                          {p.max_usuarios}u / {p.max_productos}p / {p.max_facturas_mes}f
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center font-medium">{p.tenant_count}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${p.esta_activo ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-500'}`}>
                          {p.esta_activo ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={() => { setEditingPlan(p); setPlanModal(true); }}
                            className="rounded px-2 py-1 text-xs font-medium bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors"
                          >
                            Editar
                          </button>
                          {p.esta_activo && (
                            <button
                              onClick={() => {
                                if (confirm(`Desactivar plan "${p.nombre}"?`)) {
                                  deletePlanMut.mutate(p.id);
                                }
                              }}
                              className="rounded px-2 py-1 text-xs font-medium bg-red-50 text-red-700 hover:bg-red-100 transition-colors"
                            >
                              Desactivar
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Revenue por plan */}
          {kpis && kpis.revenue_por_plan.length > 0 && (
            <div className="mt-6 bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Revenue por Plan</h3>
              <div className="space-y-2">
                {kpis.revenue_por_plan.map((rp) => (
                  <div key={rp.plan_id} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-900">{rp.plan_nombre}</span>
                      <span className="text-xs text-gray-500">{rp.tenant_count} tenants</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">{formatCurrency(rp.revenue)}/mes</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* ================================================================== */}
      {/* TENANT DETAIL MODAL */}
      {/* ================================================================== */}
      <Modal
        open={!!selectedTenant}
        onClose={() => setSelectedTenant(null)}
        title={selectedTenant?.nombre || ''}
        maxWidth="max-w-3xl"
      >
        {selectedTenant && (
          <TenantDetailPanel
            tenant={selectedTenant}
            detailTab={detailTab}
            setDetailTab={setDetailTab}
            planes={planes || []}
            usuarios={usuarios}
            loadingUsuarios={loadingUsuarios}
            metricas={metricas}
            suscripciones={suscripciones}
            pagos={pagos}
            onSuspender={() => { if (confirm('Suspender este tenant?')) suspenderMut.mutate(selectedTenant.id); }}
            onReactivar={() => reactivarMut.mutate(selectedTenant.id)}
            onCancelar={() => { if (confirm('CANCELAR este tenant? Esta accion es permanente.')) cancelarMut.mutate(selectedTenant.id); }}
            onCambiarPlan={(planId) => cambiarPlanMut.mutate({ id: selectedTenant.id, plan_id: planId })}
            onExtenderTrial={(dias) => extenderTrialMut.mutate({ id: selectedTenant.id, dias })}
            onUpdateTenant={(data) => updateTenantMut.mutate({ id: selectedTenant.id, data })}
            onCambiarRol={(uid, rol) => cambiarRolMut.mutate({ tid: selectedTenant.id, uid, rol })}
            onRemoveUsuario={(uid) => {
              if (confirm('Remover usuario del tenant?')) removeUsuarioMut.mutate({ tid: selectedTenant.id, uid });
            }}
            isPending={suspenderMut.isPending || reactivarMut.isPending || cancelarMut.isPending}
          />
        )}
      </Modal>

      {/* ================================================================== */}
      {/* PLAN MODAL */}
      {/* ================================================================== */}
      <Modal
        open={planModal}
        onClose={() => { setPlanModal(false); setEditingPlan(null); }}
        title={editingPlan ? `Editar: ${editingPlan.nombre}` : 'Nuevo Plan'}
        maxWidth="max-w-lg"
      >
        <PlanForm
          plan={editingPlan}
          onSubmit={(data) => {
            if (editingPlan) {
              updatePlanMut.mutate({ id: editingPlan.id, data });
            } else {
              crearPlanMut.mutate(data as PlanCreate);
            }
          }}
          isPending={crearPlanMut.isPending || updatePlanMut.isPending}
        />
      </Modal>
    </div>
  );
}

// ============================================================================
// KPI CARD
// ============================================================================

function KPICard({ title, value, subtitle, negative }: {
  title: string; value: string; subtitle: string; negative?: boolean;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{title}</p>
      <p className={`text-2xl font-bold mt-1 ${negative ? 'text-red-600' : 'text-gray-900'}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  );
}

// ============================================================================
// TENANT DETAIL PANEL
// ============================================================================

function TenantDetailPanel({
  tenant,
  detailTab,
  setDetailTab,
  planes,
  usuarios,
  loadingUsuarios,
  metricas,
  suscripciones,
  pagos,
  onSuspender,
  onReactivar,
  onCancelar,
  onCambiarPlan,
  onExtenderTrial,
  onUpdateTenant,
  onCambiarRol,
  onRemoveUsuario,
  isPending,
}: {
  tenant: TenantDetail;
  detailTab: string;
  setDetailTab: (t: 'info' | 'usuarios' | 'suscripcion' | 'metricas') => void;
  planes: PlanWithStats[];
  usuarios?: UsuarioTenantDetail[];
  loadingUsuarios: boolean;
  metricas?: TenantMetricas;
  suscripciones?: Suscripcion[];
  pagos?: PagoHistorial[];
  onSuspender: () => void;
  onReactivar: () => void;
  onCancelar: () => void;
  onCambiarPlan: (planId: string) => void;
  onExtenderTrial: (dias: number) => void;
  onUpdateTenant: (data: any) => void;
  onCambiarRol: (uid: string, rol: string) => void;
  onRemoveUsuario: (uid: string) => void;
  isPending: boolean;
}) {
  const [trialDias, setTrialDias] = useState(7);

  // Editable info
  const [editNombre, setEditNombre] = useState(tenant.nombre);
  const [editEmail, setEditEmail] = useState(tenant.email_contacto);
  const [editTelefono, setEditTelefono] = useState(tenant.telefono || '');
  const [editCiudad, setEditCiudad] = useState(tenant.ciudad || '');

  const tabs = [
    { key: 'info', label: 'Info' },
    { key: 'usuarios', label: 'Usuarios' },
    { key: 'suscripcion', label: 'Suscripcion' },
    { key: 'metricas', label: 'Metricas' },
  ] as const;

  return (
    <div>
      {/* Status badge + slug */}
      <div className="flex items-center gap-2 mb-4">
        <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${estadoColor[tenant.estado] || 'bg-gray-100 text-gray-600'}`}>
          {tenant.estado}
        </span>
        <span className="text-xs text-gray-500 font-mono">{tenant.slug}</span>
        {tenant.nit && <span className="text-xs text-gray-500">NIT: {tenant.nit}</span>}
      </div>

      {/* Sub-tabs */}
      <div className="flex border-b border-gray-200 mb-4">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setDetailTab(tab.key)}
            className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
              detailTab === tab.key
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ---- INFO TAB ---- */}
      {detailTab === 'info' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Nombre</label>
              <input
                value={editNombre}
                onChange={(e) => setEditNombre(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Email</label>
              <input
                value={editEmail}
                onChange={(e) => setEditEmail(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Telefono</label>
              <input
                value={editTelefono}
                onChange={(e) => setEditTelefono(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Ciudad</label>
              <input
                value={editCiudad}
                onChange={(e) => setEditCiudad(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Plan selector */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Plan</label>
            <div className="flex gap-2">
              <select
                value={tenant.plan_id}
                onChange={(e) => onCambiarPlan(e.target.value)}
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {planes.filter(p => p.esta_activo).map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre} - {formatCurrency(p.precio_mensual)}/mes
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Fechas */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-xs text-gray-500">Inicio suscripcion</span>
              <p className="font-medium">{tenant.fecha_inicio_suscripcion ? formatDate(tenant.fecha_inicio_suscripcion) : '-'}</p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Fin suscripcion</span>
              <p className="font-medium">{tenant.fecha_fin_suscripcion ? formatDate(tenant.fecha_fin_suscripcion) : '-'}</p>
            </div>
          </div>

          {/* Save button */}
          <button
            onClick={() => onUpdateTenant({
              nombre: editNombre,
              email_contacto: editEmail,
              telefono: editTelefono || null,
              ciudad: editCiudad || null,
            })}
            className="rounded-lg bg-primary-500 text-white px-4 py-2 text-sm font-medium hover:bg-primary-600 transition-colors"
          >
            Guardar Cambios
          </button>

          {/* Actions */}
          <div className="border-t border-gray-100 pt-4">
            <p className="text-xs font-medium text-gray-500 mb-2">Acciones</p>
            <div className="flex flex-wrap gap-2">
              {/* Extend trial */}
              {tenant.estado === 'trial' && (
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={1}
                    max={90}
                    value={trialDias}
                    onChange={(e) => setTrialDias(Number(e.target.value))}
                    className="w-16 rounded border border-gray-300 px-2 py-1 text-sm"
                  />
                  <button
                    onClick={() => onExtenderTrial(trialDias)}
                    className="rounded px-3 py-1.5 text-xs font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
                  >
                    Extender Trial
                  </button>
                </div>
              )}

              {/* Suspender */}
              {(tenant.estado === 'activo' || tenant.estado === 'trial') && (
                <button
                  onClick={onSuspender}
                  disabled={isPending}
                  className="rounded px-3 py-1.5 text-xs font-medium bg-red-50 text-red-700 hover:bg-red-100 transition-colors disabled:opacity-50"
                >
                  Suspender
                </button>
              )}

              {/* Reactivar */}
              {tenant.estado === 'suspendido' && (
                <button
                  onClick={onReactivar}
                  disabled={isPending}
                  className="rounded px-3 py-1.5 text-xs font-medium bg-green-50 text-green-700 hover:bg-green-100 transition-colors disabled:opacity-50"
                >
                  Reactivar
                </button>
              )}

              {/* Cancelar */}
              {tenant.estado !== 'cancelado' && (
                <button
                  onClick={onCancelar}
                  disabled={isPending}
                  className="rounded px-3 py-1.5 text-xs font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors disabled:opacity-50"
                >
                  Cancelar
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ---- USUARIOS TAB ---- */}
      {detailTab === 'usuarios' && (
        <div>
          {loadingUsuarios ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-12 bg-gray-200 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : usuarios && usuarios.length > 0 ? (
            <div className="space-y-3">
              {usuarios.map((u) => (
                <div
                  key={u.id}
                  className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{u.usuario_nombre}</p>
                    <p className="text-xs text-gray-500">{u.usuario_email}</p>
                  </div>
                  <div className="flex items-center gap-2 ml-3">
                    <select
                      value={u.rol}
                      onChange={(e) => onCambiarRol(u.usuario_id, e.target.value)}
                      className="rounded border border-gray-300 px-2 py-1 text-xs focus:ring-1 focus:ring-primary-500"
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                    <button
                      onClick={() => onRemoveUsuario(u.usuario_id)}
                      className="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                      title="Remover"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-400 py-6">Sin usuarios en este tenant</p>
          )}
        </div>
      )}

      {/* ---- SUSCRIPCION TAB ---- */}
      {detailTab === 'suscripcion' && (
        <div className="space-y-6">
          {/* Suscripciones */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Suscripciones</h4>
            {suscripciones && suscripciones.length > 0 ? (
              <div className="space-y-2">
                {suscripciones.map((s, idx) => (
                  <div
                    key={s.id}
                    className={`rounded-lg border px-4 py-3 text-sm ${idx === 0 ? 'border-primary-200 bg-primary-50' : 'border-gray-200'}`}
                  >
                    <div className="flex justify-between items-center">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${estadoColor[s.estado] || 'bg-gray-100 text-gray-600'}`}>
                        {s.estado}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatDate(s.periodo_inicio)} - {formatDate(s.periodo_fin)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">Sin suscripciones</p>
            )}
          </div>

          {/* Pagos */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Historial de Pagos</h4>
            {pagos && pagos.length > 0 ? (
              <div className="space-y-2">
                {pagos.map((p) => (
                  <div key={p.id} className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3 text-sm">
                    <div>
                      <span className="font-medium">{formatCurrency(p.monto)}</span>
                      <span className="text-xs text-gray-500 ml-2">{p.moneda}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${pagoEstadoColor[p.estado] || 'bg-gray-100 text-gray-600'}`}>
                        {p.estado}
                      </span>
                      <span className="text-xs text-gray-500">
                        {p.fecha_pago ? formatDate(p.fecha_pago) : formatDate(p.created_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">Sin pagos registrados</p>
            )}
          </div>
        </div>
      )}

      {/* ---- METRICAS TAB ---- */}
      {detailTab === 'metricas' && (
        <div>
          {metricas ? (
            <div className="space-y-1">
              <ProgressBar value={metricas.usuarios_count} max={metricas.max_usuarios} label="Usuarios" />
              <ProgressBar value={metricas.productos_count} max={metricas.max_productos} label="Productos" />
              <ProgressBar value={metricas.facturas_mes_count} max={metricas.max_facturas_mes} label="Facturas este mes" />

              <div className="border-t border-gray-100 pt-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Terceros</p>
                    <p className="text-lg font-bold text-gray-900">{metricas.terceros_count}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Ventas del mes</p>
                    <p className="text-lg font-bold text-gray-900">{formatCurrency(metricas.ventas_total_mes)}</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 bg-gray-200 rounded-lg animate-pulse" />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// PLAN FORM
// ============================================================================

function PlanForm({ plan, onSubmit, isPending }: {
  plan: PlanWithStats | null;
  onSubmit: (data: PlanCreate | PlanUpdate) => void;
  isPending: boolean;
}) {
  const [nombre, setNombre] = useState(plan?.nombre || '');
  const [descripcion, setDescripcion] = useState(plan?.descripcion || '');
  const [precioMensual, setPrecioMensual] = useState(plan?.precio_mensual ?? 0);
  const [precioAnual, setPrecioAnual] = useState(plan?.precio_anual ?? 0);
  const [maxUsuarios, setMaxUsuarios] = useState(plan?.max_usuarios ?? 3);
  const [maxProductos, setMaxProductos] = useState(plan?.max_productos ?? 100);
  const [maxFacturas, setMaxFacturas] = useState(plan?.max_facturas_mes ?? 100);
  const [maxStorage, setMaxStorage] = useState(plan?.max_storage_mb ?? 500);
  const [activo, setActivo] = useState(plan?.esta_activo ?? true);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const data: any = {
      nombre,
      descripcion: descripcion || null,
      precio_mensual: precioMensual,
      precio_anual: precioAnual || null,
      max_usuarios: maxUsuarios,
      max_productos: maxProductos,
      max_facturas_mes: maxFacturas,
      max_storage_mb: maxStorage,
      esta_activo: activo,
    };
    onSubmit(data);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Nombre *</label>
        <input
          required
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Descripcion</label>
        <input
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Precio mensual *</label>
          <input
            required
            type="number"
            min={0}
            step={100}
            value={precioMensual}
            onChange={(e) => setPrecioMensual(Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Precio anual</label>
          <input
            type="number"
            min={0}
            step={100}
            value={precioAnual}
            onChange={(e) => setPrecioAnual(Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Max Usuarios</label>
          <input
            type="number"
            min={1}
            value={maxUsuarios}
            onChange={(e) => setMaxUsuarios(Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Max Productos</label>
          <input
            type="number"
            min={1}
            value={maxProductos}
            onChange={(e) => setMaxProductos(Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Max Facturas/mes</label>
          <input
            type="number"
            min={1}
            value={maxFacturas}
            onChange={(e) => setMaxFacturas(Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Max Storage (MB)</label>
          <input
            type="number"
            min={1}
            value={maxStorage}
            onChange={(e) => setMaxStorage(Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="plan-activo"
          checked={activo}
          onChange={(e) => setActivo(e.target.checked)}
          className="rounded border-gray-300 text-primary-500 focus:ring-primary-500"
        />
        <label htmlFor="plan-activo" className="text-sm text-gray-700">Activo</label>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button
          type="submit"
          disabled={isPending || !nombre}
          className="rounded-lg bg-primary-500 text-white px-4 py-2 text-sm font-medium hover:bg-primary-600 transition-colors disabled:opacity-50"
        >
          {isPending ? 'Guardando...' : plan ? 'Actualizar' : 'Crear Plan'}
        </button>
      </div>
    </form>
  );
}
