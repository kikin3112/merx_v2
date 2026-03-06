import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tenants, usuariosAdmin, pqrs as pqrsApi } from '../api/endpoints';
import { formatCurrency, formatDate } from '../utils/format';
import Modal from '../components/ui/Modal';
import { useAuthStore } from '../stores/authStore';
import type {
  TenantDetail,
  PlanWithStats,
  PlanCreate,
  PlanUpdate,
  SaaSDashboardKPIs,
  TenantMetricas,
  TenantPulse,
  Suscripcion,
  PagoHistorial,
  UsuarioTenantDetail,
  GlobalUserResponse,
  GlobalUserListResponse,
  UserTenantMembership,
  ImpersonationResponse,
  TicketPQRSAdmin,
} from '../types';

// ============================================================================
// HELPERS
// ============================================================================

const estadoColor: Record<string, string> = {
  activo: 'cv-badge-positive',
  trial: 'cv-badge-primary',
  suspendido: 'cv-badge-negative',
  cancelado: 'cv-badge-neutral',
  pendiente: 'cv-badge-accent',
  mantenimiento: 'cv-badge-accent',
};

const pagoEstadoColor: Record<string, string> = {
  pendiente: 'cv-badge-accent',
  aprobado: 'cv-badge-positive',
  rechazado: 'cv-badge-negative',
  reembolsado: 'cv-badge-primary',
};

const ROLES = ['admin', 'operador', 'contador', 'vendedor', 'readonly'];

function ProgressBar({ value, max, label }: { value: number; max: number; label: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  const color = pct < 70 ? 'bg-[var(--cv-positive)]' : pct < 90 ? 'bg-[var(--cv-accent)]' : 'bg-[var(--cv-negative)]';
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="cv-muted">{label}</span>
        <span className="font-medium cv-text">{value} / {max}</span>
      </div>
      <div className="w-full cv-elevated rounded-full h-2">
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
  const [activeTab, setActiveTab] = useState<'tenants' | 'planes' | 'usuarios' | 'tickets'>('tenants');
  const [filtroEstado, setFiltroEstado] = useState('');
  const [busqueda, setBusqueda] = useState('');

  // Tenant detail modal
  const [selectedTenant, setSelectedTenant] = useState<TenantDetail | null>(null);
  const [detailTab, setDetailTab] = useState<'info' | 'usuarios' | 'suscripcion' | 'metricas' | 'pulso'>('info');

  // Create tenant modal
  const [createTenantModal, setCreateTenantModal] = useState(false);

  // Plan modal
  const [planModal, setPlanModal] = useState(false);
  const [editingPlan, setEditingPlan] = useState<PlanWithStats | null>(null);

  // User governance state
  const [busquedaUsuario, setBusquedaUsuario] = useState('');
  const [filtroEstadoUsuario, setFiltroEstadoUsuario] = useState<string>('');
  const [selectedUser, setSelectedUser] = useState<GlobalUserResponse | null>(null);
  const [userModalTab, setUserModalTab] = useState<'info' | 'tenants' | 'password'>('info');
  const [editUserNombre, setEditUserNombre] = useState('');
  const [editUserEmail, setEditUserEmail] = useState('');
  const [editUserRol, setEditUserRol] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const startImpersonation = useAuthStore((s) => s.startImpersonation);
  const currentUser = useAuthStore((s) => s.user);
  const isSelf = selectedUser?.id === currentUser?.id;

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

  // User governance queries
  const { data: usuariosList, isLoading: loadingUsuariosList } = useQuery<GlobalUserListResponse>({
    queryKey: ['usuarios-global', busquedaUsuario, filtroEstadoUsuario],
    queryFn: () =>
      usuariosAdmin.list({
        ...(busquedaUsuario ? { busqueda: busquedaUsuario } : {}),
        ...(filtroEstadoUsuario === 'activo' ? { estado: true } : filtroEstadoUsuario === 'inactivo' ? { estado: false } : {}),
      }).then((r) => r.data),
    enabled: activeTab === 'usuarios',
  });

  const { data: userTenants, isLoading: loadingUserTenants } = useQuery<UserTenantMembership[]>({
    queryKey: ['user-tenants', selectedUser?.id],
    queryFn: () => usuariosAdmin.tenants(selectedUser!.id).then((r) => r.data),
    enabled: !!selectedUser && userModalTab === 'tenants',
  });

  // Admin PQRS tickets query
  const [filtroTicketEstado, setFiltroTicketEstado] = useState('');
  const [filtroTicketTipo, setFiltroTicketTipo] = useState('');
  const [selectedTicket, setSelectedTicket] = useState<TicketPQRSAdmin | null>(null);
  const [respuestaContenido, setRespuestaContenido] = useState('');

  const { data: ticketsAdmin, isLoading: loadingTickets, refetch: refetchTickets } = useQuery<TicketPQRSAdmin[]>({
    queryKey: ['pqrs-admin', filtroTicketEstado, filtroTicketTipo],
    queryFn: () =>
      pqrsApi.adminTodos({
        ...(filtroTicketEstado ? { estado: filtroTicketEstado } : {}),
        ...(filtroTicketTipo ? { tipo: filtroTicketTipo } : {}),
      }).then((r) => r.data),
    enabled: activeTab === 'tickets',
  });

  const responderTicketMut = useMutation({
    mutationFn: ({ id, contenido }: { id: string; contenido: string }) =>
      pqrsApi.adminResponder(id, contenido),
    onSuccess: (res) => {
      setRespuestaContenido('');
      setSelectedTicket(res.data);
      refetchTickets();
    },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al responder ticket'),
  });

  // --- Mutations ---
  const invalidateAll = () => {
    qc.invalidateQueries({ queryKey: ['tenants'] });
    qc.invalidateQueries({ queryKey: ['saas-dashboard'] });
    qc.invalidateQueries({ queryKey: ['planes-admin'] });
  };

  const crearTenantMut = useMutation({
    mutationFn: (data: unknown) => tenants.create(data),
    onSuccess: () => { invalidateAll(); setCreateTenantModal(false); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al crear tenant'),
  });

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

  const mantenimientoMut = useMutation({
    mutationFn: ({ id, motivo }: { id: string; motivo?: string }) =>
      tenants.mantenimiento(id, motivo),
    onSuccess: () => { invalidateAll(); setSelectedTenant(null); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al poner en mantenimiento'),
  });

  const salirMantenimientoMut = useMutation({
    mutationFn: (id: string) => tenants.salirMantenimiento(id),
    onSuccess: () => { invalidateAll(); setSelectedTenant(null); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al salir de mantenimiento'),
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

  // User governance mutations
  const invalidateUsers = () => qc.invalidateQueries({ queryKey: ['usuarios-global'] });

  const updateUserMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => usuariosAdmin.update(id, data),
    onSuccess: () => { invalidateUsers(); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al actualizar usuario'),
  });

  const resetPasswordMut = useMutation({
    mutationFn: ({ id, pwd }: { id: string; pwd: string }) => usuariosAdmin.resetPassword(id, pwd),
    onSuccess: () => { setNewPassword(''); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al resetear contraseña'),
  });

  const toggleStatusMut = useMutation({
    mutationFn: (id: string) => usuariosAdmin.toggleStatus(id),
    onSuccess: () => { invalidateUsers(); },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al cambiar estado'),
  });

  const impersonateMut = useMutation({
    mutationFn: ({ tenantId, userId }: { tenantId: string; userId: string }) =>
      tenants.impersonate(tenantId, userId),
    onSuccess: (res, vars) => {
      const data: ImpersonationResponse = res.data;
      const membership = userTenants?.find((t) => t.tenant_id === vars.tenantId);
      startImpersonation(data, membership?.tenant_nombre || vars.tenantId);
      setSelectedUser(null);
      window.location.href = '/dashboard';
    },
    onError: (e: any) => showError(e?.response?.data?.detail || 'Error al iniciar impersonación'),
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
        <div className="cv-alert-error mb-4 px-4 py-3 text-sm flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="cv-muted hover:cv-text ml-4">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      )}

      {/* Header */}
      <div className="mb-6">
        <h1 className="font-brand text-xl font-medium cv-text">Control de tenants</h1>
        <p className="text-sm cv-muted mt-1">Panel de superadmin</p>
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
      <div className="flex border-b cv-divider mb-4">
        {(['tenants', 'planes', 'usuarios', 'tickets'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-[var(--cv-primary)] cv-primary'
                : 'border-transparent cv-muted'
            }`}
          >
            {tab === 'tenants' ? 'Tenants' : tab === 'planes' ? 'Planes' : tab === 'usuarios' ? 'Usuarios' : 'Tickets PQRS'}
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
              className="cv-input flex-1"
            />
            <div className="flex gap-2 flex-wrap items-center">
              {['', 'activo', 'trial', 'suspendido', 'cancelado'].map((estado) => (
                <button
                  key={estado}
                  onClick={() => setFiltroEstado(estado)}
                  className={`cv-badge cursor-pointer transition-colors ${
                    filtroEstado === estado
                      ? 'cv-badge-primary'
                      : 'cv-badge-neutral'
                  }`}
                >
                  {estado || 'Todos'}
                </button>
              ))}
              <button
                onClick={() => setCreateTenantModal(true)}
                className="cv-btn cv-btn-primary text-xs py-1.5 px-3"
              >
                + Nuevo Tenant
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-14 cv-elevated rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <>
            {/* Desktop table */}
            <div className="hidden md:block cv-card overflow-hidden">
              <table className="w-full text-sm">
                <thead className="cv-table-header">
                  <tr>
                    <th className="text-left">Tenant</th>
                    <th className="text-left">Plan</th>
                    <th className="text-left">Email</th>
                    <th className="text-left hidden lg:table-cell">Creado</th>
                    <th className="text-center">Estado</th>
                  </tr>
                </thead>
                <tbody className="cv-table-body">
                  {tenantsList?.map((t) => (
                    <tr
                      key={t.id}
                      onClick={() => { setSelectedTenant(t); setDetailTab('info'); }}
                      className="cursor-pointer"
                    >
                      <td>
                        <p className="font-medium cv-text">{t.nombre}</p>
                        <p className="text-xs cv-muted">{t.slug}</p>
                      </td>
                      <td className="cv-muted">{getPlanNombre(t.plan_id)}</td>
                      <td className="cv-muted">{t.email_contacto}</td>
                      <td className="cv-muted hidden lg:table-cell">{formatDate(t.created_at)}</td>
                      <td className="text-center">
                        <span className={`cv-badge ${estadoColor[t.estado] || 'cv-badge-neutral'}`}>
                          {t.estado}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {tenantsList?.length === 0 && (
                <div className="text-center py-12 cv-muted">
                  <p className="text-lg mb-2">Sin tenants</p>
                  <p className="text-sm">No se encontraron tenants con los filtros aplicados</p>
                </div>
              )}
            </div>

            {/* Mobile cards */}
            <div className="md:hidden space-y-3">
              {tenantsList?.map((t) => (
                <div
                  key={t.id}
                  onClick={() => { setSelectedTenant(t); setDetailTab('info'); }}
                  className="cv-card p-4 cursor-pointer active:opacity-80 transition-opacity"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="min-w-0 flex-1">
                      <h4 className="text-sm font-semibold cv-text truncate">{t.nombre}</h4>
                      <p className="text-xs cv-muted font-mono">{t.slug}</p>
                    </div>
                    <span className={`cv-badge ml-2 ${estadoColor[t.estado] || 'cv-badge-neutral'}`}>
                      {t.estado}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><span className="cv-muted">Plan:</span> <span className="font-medium">{getPlanNombre(t.plan_id)}</span></div>
                    <div className="truncate"><span className="cv-muted">Email:</span> <span className="font-medium">{t.email_contacto}</span></div>
                  </div>
                </div>
              ))}
              {tenantsList?.length === 0 && (
                <div className="text-center py-12 cv-muted cv-card">
                  <p className="text-lg mb-2">Sin tenants</p>
                  <p className="text-sm">No se encontraron tenants con los filtros aplicados</p>
                </div>
              )}
            </div>
            </>
          )}
        </>
      )}

      {/* TAB: Planes */}
      {activeTab === 'planes' && (
        <>
          <div className="flex justify-end mb-4">
            <button
              onClick={() => { setEditingPlan(null); setPlanModal(true); }}
              className="cv-btn cv-btn-primary"
            >
              + Nuevo Plan
            </button>
          </div>

          {loadingPlanes ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 cv-elevated rounded-lg animate-pulse" />
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
                    <th className="text-right">Precio/mes</th>
                    <th className="text-center">Limites</th>
                    <th className="text-center">Tenants</th>
                    <th className="text-center">Estado</th>
                    <th className="text-center">Acciones</th>
                  </tr>
                </thead>
                <tbody className="cv-table-body">
                  {planes?.map((p) => (
                    <tr key={p.id}>
                      <td>
                        <p className="font-medium cv-text">{p.nombre}</p>
                        {p.descripcion && <p className="text-xs cv-muted truncate max-w-[200px]">{p.descripcion}</p>}
                      </td>
                      <td className="text-right font-medium">{formatCurrency(p.precio_mensual)}</td>
                      <td className="text-center">
                        <span className="text-xs cv-muted">
                          {p.max_usuarios}u / {p.max_productos}p / {p.max_facturas_mes}f
                        </span>
                      </td>
                      <td className="text-center font-medium">{p.tenant_count}</td>
                      <td className="text-center">
                        <span className={`cv-badge ${p.esta_activo ? 'cv-badge-positive' : 'cv-badge-neutral'}`}>
                          {p.esta_activo ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={() => { setEditingPlan(p); setPlanModal(true); }}
                            className="cv-btn cv-btn-ghost text-xs py-1 px-2"
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
                              className="cv-btn cv-btn-danger text-xs py-1 px-2"
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

            {/* Mobile cards */}
            <div className="md:hidden space-y-3">
              {planes?.map((p) => (
                <div key={p.id} className="cv-card p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="min-w-0 flex-1">
                      <h4 className="text-sm font-semibold cv-text">{p.nombre}</h4>
                      {p.descripcion && <p className="text-xs cv-muted mt-0.5">{p.descripcion}</p>}
                    </div>
                    <span className={`cv-badge ml-2 ${p.esta_activo ? 'cv-badge-positive' : 'cv-badge-neutral'}`}>
                      {p.esta_activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div><span className="cv-muted">Precio:</span> <span className="font-semibold">{formatCurrency(p.precio_mensual)}/mes</span></div>
                    <div><span className="cv-muted">Tenants:</span> <span className="font-medium">{p.tenant_count}</span></div>
                    <div className="col-span-2"><span className="cv-muted">Limites:</span> <span className="font-medium">{p.max_usuarios}u / {p.max_productos}p / {p.max_facturas_mes}f</span></div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => { setEditingPlan(p); setPlanModal(true); }}
                      className="cv-btn cv-btn-ghost text-xs py-1.5 px-3"
                    >
                      Editar
                    </button>
                    {p.esta_activo && (
                      <button
                        onClick={() => {
                          if (confirm(`Desactivar plan "${p.nombre}"?`)) deletePlanMut.mutate(p.id);
                        }}
                        className="cv-btn cv-btn-danger text-xs py-1.5 px-3"
                      >
                        Desactivar
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            </>
          )}

          {/* Revenue por plan */}
          {kpis && kpis.revenue_por_plan.length > 0 && (
            <div className="mt-6 cv-card p-4">
              <h3 className="text-sm font-semibold cv-text mb-3">Utilidad por plan</h3>
              <div className="space-y-2">
                {kpis.revenue_por_plan.map((rp) => (
                  <div key={rp.plan_id} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium cv-text">{rp.plan_nombre}</span>
                      <span className="text-xs cv-muted">{rp.tenant_count} tenants</span>
                    </div>
                    <span className="text-sm font-semibold cv-text">{formatCurrency(rp.revenue)}/mes</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* TAB: Usuarios */}
      {activeTab === 'usuarios' && (
        <>
          <div className="flex flex-col sm:flex-row gap-3 mb-4">
            <input
              type="text"
              placeholder="Buscar por nombre o email..."
              value={busquedaUsuario}
              onChange={(e) => setBusquedaUsuario(e.target.value)}
              className="cv-input flex-1"
            />
            <div className="flex gap-2">
              {[['', 'Todos'], ['activo', 'Activos'], ['inactivo', 'Inactivos']].map(([val, label]) => (
                <button
                  key={val}
                  onClick={() => setFiltroEstadoUsuario(val)}
                  className={`cv-badge cursor-pointer transition-colors ${
                    filtroEstadoUsuario === val
                      ? 'cv-badge-primary'
                      : 'cv-badge-neutral'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {loadingUsuariosList ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 cv-elevated rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <>
            {/* Desktop table */}
            <div className="hidden md:block cv-card overflow-hidden">
              <table className="w-full text-sm">
                <thead className="cv-table-header">
                  <tr>
                    <th className="text-left">Usuario</th>
                    <th className="text-left">Rol</th>
                    <th className="text-center">Tenants</th>
                    <th className="text-left hidden lg:table-cell">Último acceso</th>
                    <th className="text-center">Estado</th>
                    <th className="text-center">Acciones</th>
                  </tr>
                </thead>
                <tbody className="cv-table-body">
                  {usuariosList?.items?.map((u) => (
                    <tr key={u.id}>
                      <td>
                        <p className="font-medium cv-text">{u.nombre}</p>
                        <p className="text-xs cv-muted">{u.email}</p>
                      </td>
                      <td>
                        <span className="cv-badge cv-badge-neutral font-mono">{u.rol}</span>
                        {u.es_superadmin && (
                          <span className="ml-1 cv-badge cv-badge-primary">superadmin</span>
                        )}
                      </td>
                      <td className="text-center">
                        <span className="text-sm font-medium">{u.tenant_count}</span>
                      </td>
                      <td className="text-xs cv-muted hidden lg:table-cell">
                        {u.ultimo_acceso ? formatDate(u.ultimo_acceso) : 'Nunca'}
                      </td>
                      <td className="text-center">
                        <span className={`cv-badge ${u.estado ? 'cv-badge-positive' : 'cv-badge-neutral'}`}>
                          {u.estado ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="text-center">
                        <button
                          onClick={() => {
                            setSelectedUser(u);
                            setUserModalTab('info');
                            setEditUserNombre(u.nombre);
                            setEditUserEmail(u.email);
                            setEditUserRol(u.rol);
                            setNewPassword('');
                          }}
                          className="cv-btn cv-btn-ghost text-xs py-1 px-2"
                        >
                          Gestionar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(!usuariosList?.items || usuariosList.items.length === 0) && (
                <div className="text-center py-12 cv-muted">
                  <p>No se encontraron usuarios</p>
                </div>
              )}
            </div>

            {/* Mobile cards */}
            <div className="md:hidden space-y-3">
              {usuariosList?.items?.map((u) => (
                <div
                  key={u.id}
                  onClick={() => {
                    setSelectedUser(u);
                    setUserModalTab('info');
                    setEditUserNombre(u.nombre);
                    setEditUserEmail(u.email);
                    setEditUserRol(u.rol);
                    setNewPassword('');
                  }}
                  className="cv-card p-4 cursor-pointer active:opacity-80 transition-opacity"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="min-w-0 flex-1">
                      <h4 className="text-sm font-semibold cv-text truncate">{u.nombre}</h4>
                      <p className="text-xs cv-muted">{u.email}</p>
                    </div>
                    <span className={`cv-badge ml-2 ${u.estado ? 'cv-badge-positive' : 'cv-badge-neutral'}`}>
                      {u.estado ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="cv-badge cv-badge-neutral font-mono">{u.rol}</span>
                    {u.es_superadmin && (
                      <span className="cv-badge cv-badge-primary">superadmin</span>
                    )}
                    <span className="text-xs cv-muted ml-auto">{u.tenant_count} tenants</span>
                  </div>
                </div>
              ))}
              {(!usuariosList?.items || usuariosList.items.length === 0) && (
                <div className="text-center py-12 cv-muted cv-card">
                  <p>No se encontraron usuarios</p>
                </div>
              )}
            </div>
            </>
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
            onMantenimiento={() => {
              if (confirm('Poner este tenant en modo mantenimiento? Los usuarios no podrán escribir.')) {
                mantenimientoMut.mutate({ id: selectedTenant.id });
              }
            }}
            onSalirMantenimiento={() => salirMantenimientoMut.mutate(selectedTenant.id)}
            isPending={suspenderMut.isPending || reactivarMut.isPending || cancelarMut.isPending || mantenimientoMut.isPending || salirMantenimientoMut.isPending}
          />
        )}
      </Modal>

      {/* ================================================================== */}
      {/* CREATE TENANT MODAL */}
      {/* ================================================================== */}
      <Modal
        open={createTenantModal}
        onClose={() => setCreateTenantModal(false)}
        title="Nuevo Tenant"
        maxWidth="max-w-lg"
      >
        <TenantCreateForm
          planes={planes || []}
          onSubmit={(data) => crearTenantMut.mutate(data)}
          isPending={crearTenantMut.isPending}
        />
      </Modal>

      {/* ================================================================== */}
      {/* PLAN MODAL */}
      {/* ================================================================== */}
      <Modal
        open={planModal}
        onClose={() => { setPlanModal(false); setEditingPlan(null); }}
        title={editingPlan ? `Editar: ${editingPlan.nombre}` : 'Nuevo plan'}
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

      {/* ================================================================== */}
      {/* USER DETAIL MODAL */}
      {/* ================================================================== */}
      <Modal
        open={!!selectedUser}
        onClose={() => setSelectedUser(null)}
        title={selectedUser?.nombre || 'Usuario'}
        maxWidth="max-w-2xl"
      >
        {selectedUser && (
          <div>
            {/* Header info */}
            <div className="flex items-center gap-2 mb-4">
              <span className={`cv-badge ${selectedUser.estado ? 'cv-badge-positive' : 'cv-badge-neutral'}`}>
                {selectedUser.estado ? 'Activo' : 'Inactivo'}
              </span>
              <span className="text-sm cv-muted">{selectedUser.email}</span>
              {selectedUser.es_superadmin && (
                <span className="cv-badge cv-badge-primary">superadmin</span>
              )}
            </div>

            {isSelf && (
              <div className="mb-3 cv-alert-accent px-3 py-2 text-xs">
                Estás viendo tu propia cuenta. El reseteo de contraseña no está disponible para prevenir auto-bloqueo.
              </div>
            )}

            {/* Sub-tabs */}
            <div className="overflow-x-auto -mx-4 px-4 md:mx-0 md:px-0">
              <div className="flex border-b cv-divider mb-4 w-max md:w-auto">
                {([
                  { key: 'info', label: 'Info' },
                  { key: 'tenants', label: 'Tenants / Impersonar' },
                  { key: 'password', label: 'Contraseña' },
                ] as const).filter((tab) => !(isSelf && tab.key === 'password')).map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setUserModalTab(tab.key)}
                    className={`px-3 py-2 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                      userModalTab === tab.key
                        ? 'border-[var(--cv-primary)] cv-primary'
                        : 'border-transparent cv-muted'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Info tab */}
            {userModalTab === 'info' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium cv-muted mb-1">Nombre</label>
                    <input
                      value={editUserNombre}
                      onChange={(e) => setEditUserNombre(e.target.value)}
                      className="cv-input"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium cv-muted mb-1">Email</label>
                    <input
                      value={editUserEmail}
                      onChange={(e) => setEditUserEmail(e.target.value)}
                      className="cv-input"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium cv-muted mb-1">Rol global</label>
                    <select
                      value={editUserRol}
                      onChange={(e) => setEditUserRol(e.target.value)}
                      className="cv-input"
                    >
                      {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                  <button
                    onClick={() => updateUserMut.mutate({
                      id: selectedUser.id,
                      data: { nombre: editUserNombre, email: editUserEmail, rol: editUserRol },
                    })}
                    disabled={updateUserMut.isPending}
                    className="cv-btn cv-btn-primary"
                  >
                    {updateUserMut.isPending ? 'Guardando...' : 'Guardar Cambios'}
                  </button>

                  <button
                    onClick={() => {
                      if (confirm(`${selectedUser.estado ? 'Desactivar' : 'Activar'} usuario ${selectedUser.email}?`)) {
                        toggleStatusMut.mutate(selectedUser.id);
                      }
                    }}
                    disabled={toggleStatusMut.isPending}
                    className={selectedUser.estado ? 'cv-btn cv-btn-danger' : 'cv-btn cv-btn-primary'}
                  >
                    {selectedUser.estado ? 'Desactivar' : 'Activar'}
                  </button>
                </div>
              </div>
            )}

            {/* Tenants / Impersonar tab */}
            {userModalTab === 'tenants' && (
              <div>
                {loadingUserTenants ? (
                  <div className="space-y-2">
                    {[1, 2].map((i) => (
                      <div key={i} className="h-12 cv-elevated rounded-lg animate-pulse" />
                    ))}
                  </div>
                ) : userTenants && userTenants.length > 0 ? (
                  <div className="space-y-2">
                    {userTenants.map((t) => (
                      <div key={t.tenant_id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 cv-card px-4 py-3">
                        <div>
                          <p className="text-sm font-medium cv-text">{t.tenant_nombre}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="cv-badge cv-badge-neutral font-mono">{t.rol}</span>
                            <span className={`cv-badge ${estadoColor[t.tenant_estado] || 'cv-badge-neutral'}`}>
                              {t.tenant_estado}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            if (confirm(`Impersonar a ${selectedUser.nombre} en ${t.tenant_nombre}?`)) {
                              impersonateMut.mutate({ tenantId: t.tenant_id, userId: selectedUser.id });
                            }
                          }}
                          disabled={impersonateMut.isPending || !t.esta_activo}
                          className="cv-btn cv-btn-ghost text-xs disabled:opacity-50"
                          title={!t.esta_activo ? 'Usuario inactivo en este tenant' : ''}
                        >
                          {impersonateMut.isPending ? '...' : 'Impersonar'}
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center cv-muted py-6">Este usuario no tiene tenants asociados</p>
                )}
              </div>
            )}

            {/* Password tab */}
            {userModalTab === 'password' && (
              <div className="space-y-4">
                <p className="text-sm cv-muted">
                  Fuerza un cambio de contraseña para <strong>{selectedUser.email}</strong>.
                  El usuario deberá usar esta contraseña en su próximo login.
                </p>
                <div>
                  <label className="block text-xs font-medium cv-muted mb-1">Nueva contraseña</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    minLength={8}
                    placeholder="Mínimo 8 caracteres"
                    className="cv-input"
                  />
                </div>
                <button
                  onClick={() => {
                    if (newPassword.length < 8) { showError('La contraseña debe tener al menos 8 caracteres'); return; }
                    if (confirm(`Cambiar contraseña de ${selectedUser.email}?`)) {
                      resetPasswordMut.mutate({ id: selectedUser.id, pwd: newPassword });
                    }
                  }}
                  disabled={resetPasswordMut.isPending || newPassword.length < 8}
                  className="cv-btn cv-btn-primary disabled:opacity-50"
                >
                  {resetPasswordMut.isPending ? 'Cambiando...' : 'Cambiar Contraseña'}
                </button>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* TAB: Tickets PQRS */}
      {activeTab === 'tickets' && (
        <div className="flex gap-4">
          {/* Lista de tickets */}
          <div className={`${selectedTicket ? 'hidden md:block md:w-1/2' : 'w-full'}`}>
            {/* Filtros */}
            <div className="flex flex-wrap gap-2 mb-4">
              <select
                value={filtroTicketEstado}
                onChange={(e) => setFiltroTicketEstado(e.target.value)}
                className="cv-input w-auto"
              >
                <option value="">Todos los estados</option>
                {['ABIERTO', 'EN_PROCESO', 'RESUELTO', 'CERRADO'].map((e) => (
                  <option key={e} value={e}>{e}</option>
                ))}
              </select>
              <select
                value={filtroTicketTipo}
                onChange={(e) => setFiltroTicketTipo(e.target.value)}
                className="cv-input w-auto"
              >
                <option value="">Todos los tipos</option>
                {['PETICION', 'QUEJA', 'RECLAMO', 'SUGERENCIA', 'SOPORTE'].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            {loadingTickets ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => <div key={i} className="h-16 cv-elevated rounded-lg animate-pulse" />)}
              </div>
            ) : (ticketsAdmin && ticketsAdmin.length > 0) ? (
              <div className="space-y-2">
                {ticketsAdmin.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setSelectedTicket(t)}
                    className={`w-full text-left cv-card px-4 py-3 transition-all ${selectedTicket?.id === t.id ? 'border-[var(--cv-primary)] bg-[var(--cv-primary-dim)]' : ''}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium cv-text truncate">{t.asunto}</p>
                        <p className="text-xs cv-muted truncate mt-0.5">
                          {t.tenant_id ? `Tenant: ${t.tenant_id.slice(0, 8)}...` : 'Sin tenant'}
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-1 shrink-0">
                        <span className={`cv-badge font-medium ${
                          t.estado === 'ABIERTO' ? 'cv-badge-negative' :
                          t.estado === 'EN_PROCESO' ? 'cv-badge-accent' :
                          t.estado === 'RESUELTO' ? 'cv-badge-positive' :
                          'cv-badge-neutral'
                        }`}>{t.estado}</span>
                        <span className="text-xs cv-muted">{t.tipo}</span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 cv-muted text-sm">No hay tickets</div>
            )}
          </div>

          {/* Detalle del ticket */}
          {selectedTicket && (
            <div className="flex-1 cv-card p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold cv-text">{selectedTicket.asunto}</h3>
                <button onClick={() => setSelectedTicket(null)} className="cv-muted text-lg leading-none">×</button>
              </div>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="cv-badge cv-badge-neutral">{selectedTicket.tipo}</span>
                <span className="cv-badge cv-badge-neutral">{selectedTicket.prioridad}</span>
                <span className={`cv-badge font-medium ${
                  selectedTicket.estado === 'ABIERTO' ? 'cv-badge-negative' :
                  selectedTicket.estado === 'EN_PROCESO' ? 'cv-badge-accent' :
                  selectedTicket.estado === 'RESUELTO' ? 'cv-badge-positive' :
                  'cv-badge-neutral'
                }`}>{selectedTicket.estado}</span>
              </div>
              <p className="text-sm cv-text">{selectedTicket.descripcion}</p>

              {/* Respuestas */}
              {selectedTicket.respuestas && selectedTicket.respuestas.length > 0 && (
                <div className="space-y-2">
                  <p className="cv-section-label">Respuestas</p>
                  {(selectedTicket.respuestas as Array<{ autor_nombre: string; contenido: string; fecha: string }>).map((r, i) => (
                    <div key={i} className="rounded-lg cv-elevated px-3 py-2 text-sm">
                      <p className="font-medium cv-text text-xs mb-1">{r.autor_nombre}</p>
                      <p className="cv-muted">{r.contenido}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Responder */}
              <div className="space-y-2">
                <textarea
                  value={respuestaContenido}
                  onChange={(e) => setRespuestaContenido(e.target.value)}
                  placeholder="Escribe una respuesta..."
                  rows={3}
                  className="cv-input resize-none"
                />
                <button
                  onClick={() => {
                    if (!respuestaContenido.trim()) return;
                    responderTicketMut.mutate({ id: selectedTicket.id, contenido: respuestaContenido });
                  }}
                  disabled={responderTicketMut.isPending || !respuestaContenido.trim()}
                  className="cv-btn cv-btn-primary disabled:opacity-50"
                >
                  {responderTicketMut.isPending ? 'Enviando...' : 'Enviar respuesta'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
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
    <div className="cv-card p-4">
      <p className="cv-section-label">{title}</p>
      <p className={`text-2xl font-bold mt-1 ${negative ? 'cv-negative' : 'cv-text'}`}>{value}</p>
      <p className="text-xs cv-muted mt-1">{subtitle}</p>
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
  onMantenimiento,
  onSalirMantenimiento,
  isPending,
}: {
  tenant: TenantDetail;
  detailTab: string;
  setDetailTab: (t: 'info' | 'usuarios' | 'suscripcion' | 'metricas' | 'pulso') => void;
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
  onMantenimiento: () => void;
  onSalirMantenimiento: () => void;
  isPending: boolean;
}) {
  const [trialDias, setTrialDias] = useState(7);

  // Editable info
  const [editNombre, setEditNombre] = useState(tenant.nombre);
  const [editEmail, setEditEmail] = useState(tenant.email_contacto);
  const [editTelefono, setEditTelefono] = useState(tenant.telefono || '');
  const [editCiudad, setEditCiudad] = useState(tenant.ciudad || '');

  // Logo upload
  const [logoUploading, setLogoUploading] = useState(false);
  const [logoPreview, setLogoPreview] = useState<string | null>(tenant.url_logo ?? null);
  const qcLocal = useQueryClient();

  const handleLogoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLogoUploading(true);
    try {
      const { data } = await tenants.uploadLogo(tenant.id, file);
      setLogoPreview(data.url_logo ?? null);
      qcLocal.invalidateQueries({ queryKey: ['tenants'] });
    } catch {
      // silent fail — user sees no change
    } finally {
      setLogoUploading(false);
    }
  };

  // Pulse query (lazy — only when tab is active)
  const { data: pulse, isLoading: loadingPulse } = useQuery<TenantPulse>({
    queryKey: ['tenant-pulse', tenant.id],
    queryFn: () => tenants.pulse(tenant.id).then((r) => r.data),
    enabled: detailTab === 'pulso',
  });

  const tabs = [
    { key: 'info', label: 'Info' },
    { key: 'usuarios', label: 'Usuarios' },
    { key: 'suscripcion', label: 'Suscripcion' },
    { key: 'metricas', label: 'Metricas' },
    { key: 'pulso', label: 'Pulso' },
  ] as const;

  return (
    <div>
      {/* Status badge + slug */}
      <div className="flex items-center gap-2 mb-4">
        <span className={`cv-badge ${estadoColor[tenant.estado] || 'cv-badge-neutral'}`}>
          {tenant.estado}
        </span>
        <span className="text-xs cv-muted font-mono">{tenant.slug}</span>
        {tenant.nit && <span className="text-xs cv-muted">NIT: {tenant.nit}</span>}
      </div>

      {/* Sub-tabs */}
      <div className="overflow-x-auto -mx-4 px-4 md:mx-0 md:px-0">
        <div className="flex border-b border-[var(--cv-divider)] mb-4 w-max md:w-auto">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setDetailTab(tab.key)}
              className={`px-3 py-2 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                detailTab === tab.key
                  ? 'border-[var(--cv-primary)] text-[var(--cv-primary)]'
                  : 'border-transparent cv-muted hover:text-[var(--cv-text)]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ---- INFO TAB ---- */}
      {detailTab === 'info' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium cv-muted mb-1">Nombre</label>
              <input
                value={editNombre}
                onChange={(e) => setEditNombre(e.target.value)}
                className="cv-input"
              />
            </div>
            <div>
              <label className="block text-xs font-medium cv-muted mb-1">Email</label>
              <input
                value={editEmail}
                onChange={(e) => setEditEmail(e.target.value)}
                className="cv-input"
              />
            </div>
            <div>
              <label className="block text-xs font-medium cv-muted mb-1">Teléfono</label>
              <input
                value={editTelefono}
                onChange={(e) => setEditTelefono(e.target.value)}
                className="cv-input"
              />
            </div>
            <div>
              <label className="block text-xs font-medium cv-muted mb-1">Ciudad</label>
              <input
                value={editCiudad}
                onChange={(e) => setEditCiudad(e.target.value)}
                className="cv-input"
              />
            </div>
          </div>

          {/* Plan selector */}
          <div>
            <label className="block text-xs font-medium cv-muted mb-1">Plan</label>
            <div className="flex gap-2">
              <select
                value={tenant.plan_id}
                onChange={(e) => onCambiarPlan(e.target.value)}
                className="cv-input flex-1"
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
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-xs cv-muted">Inicio suscripcion</span>
              <p className="font-medium cv-text">{tenant.fecha_inicio_suscripcion ? formatDate(tenant.fecha_inicio_suscripcion) : '-'}</p>
            </div>
            <div>
              <span className="text-xs cv-muted">Fin suscripcion</span>
              <p className="font-medium cv-text">{tenant.fecha_fin_suscripcion ? formatDate(tenant.fecha_fin_suscripcion) : '-'}</p>
            </div>
          </div>

          {/* Logo del tenant */}
          <div>
            <label className="block text-xs font-medium cv-muted mb-2">Logo del tenant</label>
            <div className="flex items-center gap-3">
              {logoPreview ? (
                <img
                  src={logoPreview.startsWith('http') ? logoPreview : `${(import.meta.env.VITE_API_URL as string || '/api/v1').replace(/\/api\/v\d+\/?$/, '')}${logoPreview}`}
                  alt="Logo actual"
                  className="h-12 w-12 rounded-full object-cover border border-[var(--cv-divider)]"
                  onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
                />
              ) : (
                <div className="h-12 w-12 rounded-full cv-elevated flex items-center justify-center cv-muted text-xs">Sin logo</div>
              )}
              <label className={`cv-btn cv-btn-ghost cursor-pointer ${logoUploading ? 'opacity-50 pointer-events-none' : ''}`}>
                {logoUploading ? 'Subiendo...' : 'Subir logo'}
                <input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handleLogoChange} />
              </label>
              <span className="text-xs cv-muted">JPEG, PNG o WebP · máx. 2 MB</span>
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
            className="cv-btn cv-btn-primary"
          >
            Guardar cambios
          </button>

          {/* Actions */}
          <div className="border-t border-[var(--cv-divider)] pt-4">
            <p className="text-xs font-medium cv-muted mb-2">Acciones</p>
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
                    className="cv-input w-16"
                  />
                  <button
                    onClick={() => onExtenderTrial(trialDias)}
                    className="cv-btn cv-btn-ghost text-xs"
                  >
                    Extender trial
                  </button>
                </div>
              )}

              {/* Suspender */}
              {(tenant.estado === 'activo' || tenant.estado === 'trial') && (
                <button
                  onClick={onSuspender}
                  disabled={isPending}
                  className="cv-btn cv-btn-danger text-xs disabled:opacity-50"
                >
                  Suspender
                </button>
              )}

              {/* Reactivar */}
              {tenant.estado === 'suspendido' && (
                <button
                  onClick={onReactivar}
                  disabled={isPending}
                  className="cv-btn cv-btn-secondary text-xs disabled:opacity-50"
                >
                  Reactivar
                </button>
              )}

              {/* Cancelar */}
              {tenant.estado !== 'cancelado' && (
                <button
                  onClick={onCancelar}
                  disabled={isPending}
                  className="cv-btn cv-btn-ghost text-xs disabled:opacity-50"
                >
                  Cancelar
                </button>
              )}

              {/* Modo Mantenimiento */}
              {(tenant.estado === 'activo' || tenant.estado === 'trial') && (
                <button
                  onClick={onMantenimiento}
                  disabled={isPending}
                  className="cv-btn cv-btn-ghost text-xs disabled:opacity-50"
                >
                  Modo mantenimiento
                </button>
              )}

              {/* Salir de Mantenimiento */}
              {tenant.estado === 'mantenimiento' && (
                <button
                  onClick={onSalirMantenimiento}
                  disabled={isPending}
                  className="cv-btn cv-btn-secondary text-xs disabled:opacity-50"
                >
                  Salir mantenimiento
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
                <div key={i} className="h-12 cv-elevated rounded-lg animate-pulse" />
              ))}
            </div>
          ) : usuarios && usuarios.length > 0 ? (
            <div className="space-y-3">
              {usuarios.map((u) => (
                <div
                  key={u.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 cv-card px-4 py-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium cv-text truncate">{u.usuario_nombre}</p>
                    <p className="text-xs cv-muted">{u.usuario_email}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={u.rol}
                      onChange={(e) => onCambiarRol(u.usuario_id, e.target.value)}
                      className="cv-input text-xs px-2 py-1"
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                    <button
                      onClick={() => onRemoveUsuario(u.usuario_id)}
                      className="p-1 rounded cv-muted hover:text-[var(--cv-negative)] hover:bg-[var(--cv-negative)]/10 transition-colors"
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
            <p className="text-center cv-muted py-6">Sin usuarios en este tenant</p>
          )}
        </div>
      )}

      {/* ---- SUSCRIPCION TAB ---- */}
      {detailTab === 'suscripcion' && (
        <div className="space-y-6">
          {/* Suscripciones */}
          <div>
            <h4 className="text-sm font-semibold cv-text mb-2">Suscripciones</h4>
            {suscripciones && suscripciones.length > 0 ? (
              <div className="space-y-2">
                {suscripciones.map((s, idx) => (
                  <div
                    key={s.id}
                    className={`cv-card px-4 py-3 text-sm ${idx === 0 ? 'border-[var(--cv-primary)]/40 bg-[var(--cv-primary-dim)]' : ''}`}
                  >
                    <div className="flex justify-between items-center">
                      <span className={`cv-badge ${estadoColor[s.estado] || 'cv-badge-neutral'}`}>
                        {s.estado}
                      </span>
                      <span className="text-xs cv-muted">
                        {formatDate(s.periodo_inicio)} - {formatDate(s.periodo_fin)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm cv-muted">Sin suscripciones</p>
            )}
          </div>

          {/* Pagos */}
          <div>
            <h4 className="text-sm font-semibold cv-text mb-2">Historial de pagos</h4>
            {pagos && pagos.length > 0 ? (
              <div className="space-y-2">
                {pagos.map((p) => (
                  <div key={p.id} className="cv-card flex items-center justify-between px-4 py-3 text-sm">
                    <div>
                      <span className="font-medium cv-text">{formatCurrency(p.monto)}</span>
                      <span className="text-xs cv-muted ml-2">{p.moneda}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`cv-badge ${pagoEstadoColor[p.estado] || 'cv-badge-neutral'}`}>
                        {p.estado}
                      </span>
                      <span className="text-xs cv-muted">
                        {p.fecha_pago ? formatDate(p.fecha_pago) : formatDate(p.created_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm cv-muted">Sin pagos registrados</p>
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

              <div className="border-t border-[var(--cv-divider)] pt-4 mt-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="cv-elevated rounded-lg p-3">
                    <p className="text-xs cv-muted">Terceros</p>
                    <p className="text-lg font-bold cv-text">{metricas.terceros_count}</p>
                  </div>
                  <div className="cv-elevated rounded-lg p-3">
                    <p className="text-xs cv-muted">Ventas del mes</p>
                    <p className="text-lg font-bold cv-text">{formatCurrency(metricas.ventas_total_mes)}</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 cv-elevated rounded-lg animate-pulse" />
              ))}
            </div>
          )}
        </div>
      )}

      {/* ---- PULSO TAB ---- */}
      {detailTab === 'pulso' && (
        <div>
          {loadingPulse ? (
            <div className="space-y-4">
              <div className="h-28 cv-elevated rounded-xl animate-pulse" />
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 cv-elevated rounded-lg animate-pulse" />
                ))}
              </div>
            </div>
          ) : pulse ? (
            <div className="space-y-4">
              {/* Score principal */}
              <div className="cv-card flex flex-col sm:flex-row items-center gap-4 sm:gap-6 rounded-xl p-5">
                {/* Número grande */}
                <div className="flex-shrink-0 text-center">
                  <span
                    className={`text-5xl font-black ${
                      pulse.estado_salud === 'saludable'
                        ? 'text-[var(--cv-positive)]'
                        : pulse.estado_salud === 'en_riesgo'
                        ? 'text-[var(--cv-accent)]'
                        : 'text-[var(--cv-negative)]'
                    }`}
                  >
                    {pulse.score}
                  </span>
                  <p className="text-xs cv-muted mt-0.5">/ 100</p>
                </div>

                {/* Barra de score */}
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold cv-text">Health score</span>
                    <span
                      className={`cv-badge ${
                        pulse.estado_salud === 'saludable'
                          ? 'cv-badge-positive'
                          : pulse.estado_salud === 'en_riesgo'
                          ? 'cv-badge-accent'
                          : 'cv-badge-negative'
                      }`}
                    >
                      {pulse.estado_salud === 'saludable'
                        ? 'Saludable'
                        : pulse.estado_salud === 'en_riesgo'
                        ? 'En Riesgo'
                        : 'Critico'}
                    </span>
                  </div>
                  <div className="w-full cv-elevated rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${
                        pulse.estado_salud === 'saludable'
                          ? 'bg-[var(--cv-positive)]'
                          : pulse.estado_salud === 'en_riesgo'
                          ? 'bg-[var(--cv-accent)]'
                          : 'bg-[var(--cv-negative)]'
                      }`}
                      style={{ width: `${pulse.score}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs cv-muted mt-1">
                    <span>Critico</span>
                    <span>En riesgo</span>
                    <span>Saludable</span>
                  </div>
                </div>
              </div>

              {/* Metricas del score */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="cv-elevated rounded-lg p-3 text-center">
                  <p className="text-xs cv-muted mb-1">Logins (7d)</p>
                  <p className="text-2xl font-bold cv-text">{pulse.logins_recientes}</p>
                  <p className="text-xs cv-muted mt-0.5">usuarios activos</p>
                </div>
                <div className="cv-elevated rounded-lg p-3 text-center">
                  <p className="text-xs cv-muted mb-1">Ventas (30d)</p>
                  <p className="text-2xl font-bold cv-text">{pulse.ventas_mes}</p>
                  <p className="text-xs cv-muted mt-0.5">transacciones</p>
                </div>
                <div className="cv-elevated rounded-lg p-3 text-center">
                  <p className="text-xs cv-muted mb-1">Antigüedad</p>
                  <p className="text-2xl font-bold cv-text">{pulse.dias_activo}</p>
                  <p className="text-xs cv-muted mt-0.5">días</p>
                </div>
              </div>

              {/* Descripcion del estado */}
              <div className={`rounded-lg px-4 py-3 text-sm ${
                pulse.estado_salud === 'saludable'
                  ? 'cv-alert-positive'
                  : pulse.estado_salud === 'en_riesgo'
                  ? 'cv-alert-accent'
                  : 'cv-alert-error'
              }`}>
                {pulse.estado_salud === 'saludable' && 'El tenant está activo y en buen estado. Sin señales de churn.'}
                {pulse.estado_salud === 'en_riesgo' && 'El tenant muestra señales de bajo engagement. Considerar seguimiento proactivo.'}
                {pulse.estado_salud === 'critico' && 'Riesgo alto de churn. Se recomienda contacto inmediato con el cliente.'}
              </div>

              <p className="text-xs cv-muted text-right">
                Calculado: {new Date(pulse.calculado_en).toLocaleString('es-CO')}
              </p>
            </div>
          ) : (
            <div className="text-center py-10 cv-muted">
              <p>No se pudo calcular el pulso</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// TENANT CREATE FORM
// ============================================================================

function TenantCreateForm({ planes, onSubmit, isPending }: {
  planes: PlanWithStats[];
  onSubmit: (data: unknown) => void;
  isPending: boolean;
}) {
  const [nombre, setNombre] = useState('');
  const [slug, setSlug] = useState('');
  const [slugManual, setSlugManual] = useState(false);
  const [emailContacto, setEmailContacto] = useState('');
  const [nit, setNit] = useState('');
  const [ciudad, setCiudad] = useState('');
  const [planId, setPlanId] = useState(planes.find(p => p.esta_activo)?.id || '');
  const [adminNombre, setAdminNombre] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');

  // Auto-generate slug from nombre
  function toSlug(s: string) {
    return s
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // remove accents
      .replace(/[^a-z0-9\s-]/g, '')
      .trim()
      .replace(/\s+/g, '-');
  }

  function handleNombreChange(v: string) {
    setNombre(v);
    if (!slugManual) setSlug(toSlug(v));
  }

  function handleSlugChange(v: string) {
    setSlugManual(true);
    setSlug(v.toLowerCase().replace(/[^a-z0-9-]/g, ''));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      nombre,
      slug,
      email_contacto: emailContacto,
      plan_id: planId,
      nit: nit || null,
      ciudad: ciudad || null,
      admin_nombre: adminNombre,
      admin_email: adminEmail,
      admin_password: adminPassword,
    });
  }

  const activePlanes = planes.filter(p => p.esta_activo);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Datos del tenant */}
      <div>
        <p className="cv-section-label mb-3">Datos del Tenant</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium cv-muted mb-1">Nombre *</label>
            <input
              required
              value={nombre}
              onChange={(e) => handleNombreChange(e.target.value)}
              placeholder="Ej: Velas Aromáticas S.A.S."
              className="cv-input"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium cv-muted mb-1">
              Slug * <span className="cv-muted font-normal">(solo minúsculas, números y guiones)</span>
            </label>
            <input
              required
              value={slug}
              onChange={(e) => handleSlugChange(e.target.value)}
              pattern="^[a-z0-9-]+$"
              placeholder="ej: mi-negocio-palmira"
              className="cv-input font-mono"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium cv-muted mb-1">Email de contacto *</label>
            <input
              required
              type="email"
              value={emailContacto}
              onChange={(e) => setEmailContacto(e.target.value)}
              placeholder="contacto@empresa.com"
              className="cv-input"
            />
          </div>
          <div>
            <label className="block text-xs font-medium cv-muted mb-1">NIT</label>
            <input
              value={nit}
              onChange={(e) => setNit(e.target.value)}
              placeholder="900123456-7"
              className="cv-input"
            />
          </div>
          <div>
            <label className="block text-xs font-medium cv-muted mb-1">Ciudad</label>
            <input
              value={ciudad}
              onChange={(e) => setCiudad(e.target.value)}
              placeholder="Bogotá"
              className="cv-input"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium cv-muted mb-1">Plan *</label>
            <select
              required
              value={planId}
              onChange={(e) => setPlanId(e.target.value)}
              className="cv-input"
            >
              <option value="">Seleccionar plan...</option>
              {activePlanes.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre} — {formatCurrency(p.precio_mensual)}/mes
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Datos del admin */}
      <div className="border-t border-[var(--cv-divider)] pt-4">
        <p className="cv-section-label mb-3">Admin Inicial</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium cv-muted mb-1">Nombre *</label>
            <input
              required
              value={adminNombre}
              onChange={(e) => setAdminNombre(e.target.value)}
              placeholder="Juan Pérez"
              className="cv-input"
            />
          </div>
          <div>
            <label className="block text-xs font-medium cv-muted mb-1">Email *</label>
            <input
              required
              type="email"
              value={adminEmail}
              onChange={(e) => setAdminEmail(e.target.value)}
              placeholder="admin@empresa.com"
              className="cv-input"
            />
          </div>
          <div>
            <label className="block text-xs font-medium cv-muted mb-1">Contraseña *</label>
            <input
              required
              type="password"
              minLength={8}
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
              placeholder="Mínimo 8 caracteres"
              className="cv-input"
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button
          type="submit"
          disabled={isPending || !nombre || !slug || !emailContacto || !planId || !adminNombre || !adminEmail || adminPassword.length < 8}
          className="cv-btn cv-btn-primary disabled:opacity-50"
        >
          {isPending ? 'Creando...' : 'Crear Tenant'}
        </button>
      </div>
    </form>
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
        <label className="block text-xs font-medium cv-muted mb-1">Nombre *</label>
        <input
          required
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          className="cv-input"
        />
      </div>

      <div>
        <label className="block text-xs font-medium cv-muted mb-1">Descripcion</label>
        <input
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          className="cv-input"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium cv-muted mb-1">Precio mensual *</label>
          <input
            required
            type="number"
            min={0}
            step={100}
            value={precioMensual}
            onChange={(e) => setPrecioMensual(Number(e.target.value))}
            className="cv-input"
          />
        </div>
        <div>
          <label className="block text-xs font-medium cv-muted mb-1">Precio anual</label>
          <input
            type="number"
            min={0}
            step={100}
            value={precioAnual}
            onChange={(e) => setPrecioAnual(Number(e.target.value))}
            className="cv-input"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium cv-muted mb-1">Max Usuarios</label>
          <input
            type="number"
            min={1}
            value={maxUsuarios}
            onChange={(e) => setMaxUsuarios(Number(e.target.value))}
            className="cv-input"
          />
        </div>
        <div>
          <label className="block text-xs font-medium cv-muted mb-1">Max Productos</label>
          <input
            type="number"
            min={1}
            value={maxProductos}
            onChange={(e) => setMaxProductos(Number(e.target.value))}
            className="cv-input"
          />
        </div>
        <div>
          <label className="block text-xs font-medium cv-muted mb-1">Max Facturas/mes</label>
          <input
            type="number"
            min={1}
            value={maxFacturas}
            onChange={(e) => setMaxFacturas(Number(e.target.value))}
            className="cv-input"
          />
        </div>
        <div>
          <label className="block text-xs font-medium cv-muted mb-1">Max Storage (MB)</label>
          <input
            type="number"
            min={1}
            value={maxStorage}
            onChange={(e) => setMaxStorage(Number(e.target.value))}
            className="cv-input"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="plan-activo"
          checked={activo}
          onChange={(e) => setActivo(e.target.checked)}
          className="rounded border-[var(--cv-divider)] text-[var(--cv-primary)] focus:ring-[var(--cv-primary)]"
        />
        <label htmlFor="plan-activo" className="text-sm cv-text">Activo</label>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button
          type="submit"
          disabled={isPending || !nombre}
          className="cv-btn cv-btn-primary disabled:opacity-50"
        >
          {isPending ? 'Guardando...' : plan ? 'Actualizar' : 'Crear Plan'}
        </button>
      </div>
    </form>
  );
}
