import client from './client';
import type {
  LoginResponse,
  TenantTokenResponse,
  User,
  Producto,
  ProductoCreate,
  ProductoUpdate,
  Tercero,
  TerceroCreate,
  TerceroUpdate,
  Venta,
  Factura,
  Cotizacion,
  AsientoContable,
  ConfiguracionContable,
  PeriodoContable,
  BalancePrueba,
  DashboardKPIs,
  VentaDiaria,
  ProductoMasVendido,
  TopCliente,
  RentabilidadProducto,
  ABCInventario,
  Inventario,
  AlertaStock,
  MovimientoInventario,
  TenantDetail,
  Receta,
  RecetaCosto,
  ProduccionResponse,
  RentabilidadCategoria,
  ComparativaMensual,
  ProyeccionFlujoCaja,
  MargenCategoria,
  CarteraItem,
  PagoCartera,
  CarteraResumen,
  MedioPago,
  PlanWithStats,
  PlanCreate,
  PlanUpdate,
  SaaSDashboardKPIs,
  TenantMetricas,
  Suscripcion,
  PagoHistorial,
  UsuarioTenantDetail,
  ImpersonationResponse,
  GlobalUserResponse,
  GlobalUserListResponse,
  GlobalUserCreate,
  GlobalUserUpdate,
  UserTenantMembership,
  TenantPulse,
  CrmPipeline,
  CrmPipelineCreate,
  CrmPipelineUpdate,
  CrmDeal,
  CrmDealCreate,
  CrmDealUpdate,
  CrmActivity,
  CrmActivityCreate,
  TenantRegisterRequest,
  TenantRegisterResponse,
  TicketPQRS,
  TicketPQRSAdmin,
  TicketPQRSCreate,
  TicketPQRSUpdate,
  GastosVsIngresos,
  CalificacionCreate,
  CalificacionResponse,
  CostoIndirecto,
  CVURequest,
  CVUResponse,
  SensibilidadResponse,
  EscenariosResponse,
  RentabilidadItem,
  EconomiaEscalaResponse,
  SociaProgreso,
  EquivalenciaUnidad,
  CostoEstandar,
  ChatMessage,
  SociaAnalisisResponse,
  SociaChatResponse,
} from '../types';

// Auth
export const auth = {
  login: (email: string, password: string) =>
    client.post<LoginResponse>('/auth/login', { email, password }),
  selectTenant: (tenant_id: string) =>
    client.post<TenantTokenResponse>('/auth/select-tenant', { tenant_id }),
  refresh: (refresh_token: string, tenant_id?: string | null) =>
    client.post<LoginResponse>('/auth/refresh', { refresh_token, tenant_id: tenant_id || undefined }),
  me: () => client.get<User>('/auth/me'),
};

// Productos
export const productos = {
  list: (params?: Record<string, unknown>) =>
    client.get<Producto[]>('/productos/', { params }),
  get: (id: string) => client.get<Producto>(`/productos/${id}`),
  create: (data: ProductoCreate) => client.post<Producto>('/productos/', data),
  update: (id: string, data: ProductoUpdate) =>
    client.patch<Producto>(`/productos/${id}`, data),
  delete: (id: string) => client.delete(`/productos/${id}`),
  siguienteCodigo: (categoria: string) =>
    client.get<{ codigo_interno: string }>('/productos/siguiente-codigo', { params: { categoria } }),
};

// Terceros
export const terceros = {
  list: (params?: Record<string, unknown>) =>
    client.get<Tercero[]>('/terceros/', { params }),
  get: (id: string) => client.get<Tercero>(`/terceros/${id}`),
  create: (data: TerceroCreate) => client.post<Tercero>('/terceros/', data),
  update: (id: string, data: TerceroUpdate) =>
    client.patch<Tercero>(`/terceros/${id}`, data),
  delete: (id: string) => client.delete(`/terceros/${id}`),
  historial: (id: string) => client.get(`/terceros/${id}/historial`),
};

// Ventas
export const ventas = {
  list: (params?: Record<string, unknown>) =>
    client.get<Venta[]>('/ventas/', { params }),
  get: (id: string) => client.get<Venta>(`/ventas/${id}`),
  create: (data: unknown) => client.post<Venta>('/ventas/', data),
  update: (id: string, data: unknown) => client.put<Venta>(`/ventas/${id}`, data),
  confirmar: (id: string) => client.post<Venta>(`/ventas/${id}/confirmar`),
  anular: (id: string, motivo?: string) =>
    client.post<Venta>(`/ventas/${id}/anular`, null, { params: { motivo } }),
  pos: (data: unknown) => client.post<Venta>('/ventas/pos', data),
  facturar: (id: string) => client.post<Venta>(`/ventas/${id}/facturar`),
  registrarEnvio: (id: string, data: { canal: string; destinatario: string }) =>
    client.post<Venta>(`/ventas/${id}/registrar-envio`, data),
};

// Inventario
export const inventarios = {
  list: () => client.get('/inventarios/'),
  valorizado: () => client.get<Inventario[]>('/inventarios/valorizado'),
  alertas: () => client.get<AlertaStock[]>('/inventarios/alertas'),
  movimientos: (params?: Record<string, unknown>) =>
    client.get<MovimientoInventario[]>('/inventarios/movimientos', { params }),
  ajuste: (data: { producto_id: string; cantidad_nueva: number; motivo: string }) =>
    client.post<MovimientoInventario>('/inventarios/ajuste', data),
  entrada: (data: { producto_id: string; cantidad: number; costo_unitario: number; documento_referencia?: string; observaciones?: string }) =>
    client.post<MovimientoInventario>('/inventarios/entrada', data),
  paginado: (params?: { cursor?: string; limit?: number }) =>
    client.get<{ items: Inventario[]; next_cursor: string | null; has_more: boolean }>(
      '/inventarios/paginado',
      { params },
    ),
  jerarquia: () =>
    client.get<{
      total_productos: number;
      valor_total: number;
      productos: Array<{
        producto_id: string;
        nombre: string;
        codigo: string;
        cantidad: number;
        costo_promedio: number;
        valor_total: number;
        stock_minimo: number | null;
        alerta: boolean;
        ultimos_movimientos: Array<{
          id: string;
          tipo: string;
          cantidad: number;
          fecha: string | null;
          referencia: string | null;
        }>;
      }>;
    }>('/inventarios/jerarquia'),
};

// Recetas
export const recetas = {
  list: (params?: Record<string, unknown>) =>
    client.get<Receta[]>('/recetas/', { params }),
  get: (id: string) => client.get<Receta>(`/recetas/${id}`),
  create: (data: unknown) => client.post<Receta>('/recetas/', data),
  update: (id: string, data: unknown) => client.put<Receta>(`/recetas/${id}`, data),
  delete: (id: string) => client.delete(`/recetas/${id}`),
  agregarIngrediente: (id: string, data: unknown) =>
    client.post<Receta>(`/recetas/${id}/ingredientes`, data),
  eliminarIngrediente: (recetaId: string, ingredienteId: string) =>
    client.delete(`/recetas/${recetaId}/ingredientes/${ingredienteId}`),
  calcularCosto: (id: string) =>
    client.post<RecetaCosto>(`/recetas/${id}/calcular-costo`),
  producir: (id: string, data: { cantidad: number; observaciones?: string }) =>
    client.post<ProduccionResponse>(`/recetas/${id}/producir`, data),
  validarStock: (id: string, cantidad: number) =>
    client.get(`/recetas/${id}/validar-stock`, { params: { cantidad } }),
  consultarEquivalencia: (productoId: string, unidad: string) =>
    client.get<EquivalenciaUnidad | null>('/recetas/equivalencia', { params: { producto_id: productoId, unidad } }),
  fijarCosto: (id: string, data: { notas?: string; vigente_desde?: string }) =>
    client.post<CostoEstandar>(`/recetas/${id}/fijar-costo`, data),
  costoEstandar: (id: string) =>
    client.get<CostoEstandar | null>(`/recetas/${id}/costo-estandar`),
  consultarSocia: (
    id: string,
    data: { precio_referencia?: number; messages?: ChatMessage[] }
  ) =>
    client.post<SociaAnalisisResponse | SociaChatResponse>(
      `/recetas/${id}/asistente-ia`,
      data
    ),
};

// Equivalencias de unidad por producto
export const equivalencias = {
  list: (productoId: string) =>
    client.get<EquivalenciaUnidad[]>(`/productos/${productoId}/equivalencias`),
  crear: (productoId: string, data: { unidad_receta: string; factor: number; notas?: string }) =>
    client.post<EquivalenciaUnidad>(`/productos/${productoId}/equivalencias`, data),
  eliminar: (productoId: string, equivalenciaId: string) =>
    client.delete(`/productos/${productoId}/equivalencias/${equivalenciaId}`),
};

// Facturas
export const facturas = {
  list: (params?: Record<string, unknown>) =>
    client.get<Factura[]>('/facturas/', { params }),
  get: (id: string) => client.get<Factura>(`/facturas/${id}`),
  create: (data: unknown) => client.post<Factura>('/facturas/', data),
  emitir: (id: string) => client.post(`/facturas/${id}/emitir`),
  pos: (data: unknown) => client.post<Factura>('/facturas/pos', data),
  anular: (id: string, motivo?: string) =>
    client.post(`/facturas/${id}/anular`, null, { params: { motivo } }),
  descargarPdf: (id: string) =>
    client.get(`/facturas/${id}/pdf`, { responseType: 'blob' }),
};

// Cotizaciones
export const cotizaciones = {
  list: (params?: Record<string, unknown>) =>
    client.get<Cotizacion[]>('/cotizaciones/', { params }),
  get: (id: string) => client.get<Cotizacion>(`/cotizaciones/${id}`),
  create: (data: unknown) => client.post<Cotizacion>('/cotizaciones/', data),
  convertir: (id: string) => client.post(`/cotizaciones/${id}/convertir`),
  rechazar: (id: string) => client.patch(`/cotizaciones/${id}/rechazar`),
  renovar: (id: string, dias = 15) =>
    client.patch(`/cotizaciones/${id}/renovar`, null, { params: { dias } }),
  descargarPdf: (id: string) =>
    client.get(`/cotizaciones/${id}/pdf`, { responseType: 'blob' }),
};

export const comercial = {
  pipeline: () => client.get('/comercial/pipeline'),
};

// Contabilidad
export const contabilidad = {
  asientos: (params?: Record<string, unknown>) =>
    client.get<AsientoContable[]>('/contabilidad/asientos', { params }),
  asiento: (id: string) => client.get<AsientoContable>(`/contabilidad/asientos/${id}`),
  crearAsiento: (data: unknown) => client.post<AsientoContable>('/contabilidad/asientos', data),
  balancePrueba: (params?: Record<string, unknown>) =>
    client.get<BalancePrueba>('/contabilidad/balance-prueba', { params }),
};

// Configuración Contable
export const configuracionContable = {
  list: () =>
    client.get<ConfiguracionContable[]>('/contabilidad/configuracion/'),
  inicializar: () =>
    client.post<{ message: string }>('/contabilidad/configuracion/inicializar'),
  update: (concepto: string, data: unknown) =>
    client.put<ConfiguracionContable>(`/contabilidad/configuracion/${concepto}`, data),
};

// Períodos Contables
export const periodosContables = {
  list: () =>
    client.get<PeriodoContable[]>('/contabilidad/periodos/'),
  cerrar: (anio: number, mes: number) =>
    client.post<PeriodoContable>(`/contabilidad/periodos/${anio}/${mes}/cerrar`),
  reabrir: (anio: number, mes: number) =>
    client.post<PeriodoContable>(`/contabilidad/periodos/${anio}/${mes}/reabrir`),
};

// Registro público de tenant
export const registro = {
  register: (data: TenantRegisterRequest) =>
    client.post<TenantRegisterResponse>('/tenants/register', data),
  registerWithClerk: (data: Omit<TenantRegisterRequest, 'admin_nombre' | 'admin_email' | 'admin_password'>) =>
    client.post<TenantRegisterResponse>('/tenants/register-with-clerk', data),
  planes: () =>
    client.get<PlanWithStats[]>('/tenants/planes/'),
};

// Clerk auth exchange
export const clerkAuth = {
  exchange: (clerkToken: string) =>
    client.post<LoginResponse>('/auth/clerk-exchange', {}, {
      headers: { Authorization: `Bearer ${clerkToken}` },
    }),
};

// Tenants (superadmin)
export const tenants = {
  list: (params?: Record<string, unknown>) =>
    client.get<TenantDetail[]>('/tenants/', { params }),
  get: (id: string) => client.get<TenantDetail>(`/tenants/${id}`),
  create: (data: unknown) => client.post<TenantDetail>('/tenants/', data),
  update: (id: string, data: unknown) => client.put<TenantDetail>(`/tenants/${id}`, data),
  suspender: (id: string, motivo?: string) =>
    client.post<TenantDetail>(`/tenants/${id}/suspender`, null, { params: { motivo } }),
  reactivar: (id: string) =>
    client.post<TenantDetail>(`/tenants/${id}/reactivar`),
  cancelar: (id: string, motivo?: string) =>
    client.post<TenantDetail>(`/tenants/${id}/cancelar`, null, { params: { motivo } }),
  cambiarPlan: (id: string, plan_id: string) =>
    client.put<TenantDetail>(`/tenants/${id}/cambiar-plan`, { plan_id }),
  extenderTrial: (id: string, dias: number) =>
    client.post<TenantDetail>(`/tenants/${id}/extender-trial`, { dias_adicionales: dias }),
  metricas: (id: string) =>
    client.get<TenantMetricas>(`/tenants/${id}/metricas`),
  suscripciones: (id: string) =>
    client.get<Suscripcion[]>(`/tenants/${id}/suscripciones`),
  pagos: (id: string) =>
    client.get<PagoHistorial[]>(`/tenants/${id}/pagos`),
  usuarios: (id: string) =>
    client.get<UsuarioTenantDetail[]>(`/tenants/${id}/usuarios`),
  cambiarRolUsuario: (tenantId: string, usuarioId: string, rol: string) =>
    client.put(`/tenants/${tenantId}/usuarios/${usuarioId}/rol`, null, { params: { rol } }),
  removeUsuario: (tenantId: string, usuarioId: string) =>
    client.delete(`/tenants/${tenantId}/usuarios/${usuarioId}`),
  impersonate: (tenantId: string, userId: string) =>
    client.post<ImpersonationResponse>(`/tenants/${tenantId}/impersonate/${userId}`),
  pulse: (id: string) =>
    client.get<TenantPulse>(`/tenants/${id}/pulse`),
  mantenimiento: (id: string, motivo?: string) =>
    client.post<TenantDetail>(`/tenants/${id}/mantenimiento`, null, { params: motivo ? { motivo } : {} }),
  salirMantenimiento: (id: string) =>
    client.post<TenantDetail>(`/tenants/${id}/salir-mantenimiento`),
  uploadLogo: (id: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return client.post<TenantDetail>(`/tenants/${id}/logo`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getMe: (tenantId: string) => client.get<TenantDetail>('/tenants/me', { params: { tenant_id: tenantId } }),
  updateMe: (data: { color_primario?: string; color_secundario?: string }) =>
    client.patch<TenantDetail>('/tenants/me', data),
  uploadLogoMe: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return client.post<{ url_logo: string; message: string }>('/tenants/me/logo', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  dashboard: () =>
    client.get<SaaSDashboardKPIs>('/tenants/dashboard/'),
  planes: {
    list: () => client.get<PlanWithStats[]>('/tenants/planes/admin/'),
    get: (id: string) => client.get<PlanWithStats>(`/tenants/planes/admin/${id}`),
    create: (data: PlanCreate) => client.post<PlanWithStats>('/tenants/planes/admin/', data),
    update: (id: string, data: PlanUpdate) => client.put<PlanWithStats>(`/tenants/planes/admin/${id}`, data),
    delete: (id: string) => client.delete(`/tenants/planes/admin/${id}`),
  },
};

// Usuarios admin (superadmin - user governance)
export const usuariosAdmin = {
  list: (params?: Record<string, unknown>) =>
    client.get<GlobalUserListResponse>('/tenants/usuarios/', { params }),
  create: (data: GlobalUserCreate) =>
    client.post<GlobalUserResponse>('/tenants/usuarios/', data),
  get: (id: string) =>
    client.get<GlobalUserResponse>(`/tenants/usuarios/${id}`),
  update: (id: string, data: GlobalUserUpdate) =>
    client.put<GlobalUserResponse>(`/tenants/usuarios/${id}`, data),
  resetPassword: (id: string, new_password: string) =>
    client.post(`/tenants/usuarios/${id}/reset-password`, { new_password }),
  toggleStatus: (id: string) =>
    client.post<GlobalUserResponse>(`/tenants/usuarios/${id}/toggle-status`),
  tenants: (id: string) =>
    client.get<UserTenantMembership[]>(`/tenants/usuarios/${id}/tenants`),
};

// Reportes
export const reportes = {
  dashboard: (params?: { fecha_inicio?: string; fecha_fin?: string }) =>
    client.get<DashboardKPIs>('/reportes/dashboard', { params }),
  ventas: (params?: Record<string, unknown>) =>
    client.get('/reportes/ventas', { params }),
  ventasDiarias: (params?: { dias?: number; fecha_inicio?: string; fecha_fin?: string }) =>
    client.get<VentaDiaria[]>('/reportes/ventas-diarias', { params }),
  productosTop: (limite?: number) =>
    client.get('/reportes/productos-top', { params: { limite } }),
  productosMasVendidos: (params?: { limite?: number; dias?: number; fecha_inicio?: string; fecha_fin?: string }) =>
    client.get<ProductoMasVendido[]>('/reportes/productos-mas-vendidos', { params }),
  topClientes: (params?: { limite?: number; dias?: number; fecha_inicio?: string; fecha_fin?: string }) =>
    client.get<TopCliente[]>('/reportes/top-clientes', { params }),
  rentabilidad: (limite?: number) =>
    client.get<RentabilidadProducto[]>('/reportes/rentabilidad', { params: { limite } }),
  abcInventario: () =>
    client.get<ABCInventario>('/reportes/abc-inventario'),
  rentabilidadCategoria: () =>
    client.get<RentabilidadCategoria[]>('/reportes/rentabilidad-categoria'),
  comparativaMensual: (params?: { fecha_referencia?: string }) =>
    client.get<ComparativaMensual>('/reportes/comparativa-mensual', { params }),
  proyeccionFlujoCaja: (dias?: number) =>
    client.get<ProyeccionFlujoCaja>('/reportes/proyeccion-flujo-caja', { params: { dias_proyeccion: dias } }),
  margenesCategoria: (params?: { dias?: number; fecha_inicio?: string; fecha_fin?: string }) =>
    client.get<MargenCategoria[]>('/reportes/margenes-categoria', { params }),
  gastosVsIngresos: (params?: { fecha_inicio?: string; fecha_fin?: string }) =>
    client.get<GastosVsIngresos>('/reportes/gastos-vs-ingresos', { params }),
};

// Cartera
export const cartera = {
  list: (params?: Record<string, unknown>) =>
    client.get<CarteraItem[]>('/cartera/', { params }),
  get: (id: string) => client.get<CarteraItem>(`/cartera/${id}`),
  resumen: () => client.get<CarteraResumen>('/cartera/resumen/totales'),
  mediosPago: () => client.get<MedioPago[]>('/cartera/medios-pago/list'),
  registrarPago: (carteraId: string, data: {
    cartera_id: string;
    fecha_pago: string;
    valor_pago: number;
    medio_pago_id: string;
    numero_referencia?: string;
    observaciones?: string;
  }) => client.post<PagoCartera>(`/cartera/${carteraId}/pagos`, data),
  pagos: (carteraId: string) =>
    client.get<PagoCartera[]>(`/cartera/${carteraId}/pagos`),
};

// CRM
export const crm = {
  // Pipelines
  pipelines: {
    list: () => client.get<CrmPipeline[]>('/crm/pipelines/'),
    create: (data: CrmPipelineCreate) => client.post<CrmPipeline>('/crm/pipelines/', data),
    update: (id: string, data: CrmPipelineUpdate) =>
      client.patch<CrmPipeline>(`/crm/pipelines/${id}`, data),
    delete: (id: string) => client.delete(`/crm/pipelines/${id}`),
  },

  // Deals
  deals: {
    list: (filters?: { pipeline_id?: string; stage_id?: string; usuario_id?: string; estado_cierre?: string }) =>
      client.get<CrmDeal[]>('/crm/deals/', { params: filters }),
    get: (id: string) => client.get<CrmDeal>(`/crm/deals/${id}`),
    create: (data: CrmDealCreate) => client.post<CrmDeal>('/crm/deals/', data),
    update: (id: string, data: CrmDealUpdate) =>
      client.put<CrmDeal>(`/crm/deals/${id}`, data),
    moveStage: (id: string, stage_id: string) =>
      client.patch<CrmDeal>(`/crm/deals/${id}/stage`, null, { params: { stage_id } }),
    close: (id: string, estado: string, motivo?: string) =>
      client.post<CrmDeal>(`/crm/deals/${id}/cerrar`, null, { params: { estado, motivo } }),
    delete: (id: string) => client.delete(`/crm/deals/${id}`),
  },

  // Activities
  activities: {
    list: (dealId: string) =>
      client.get<CrmActivity[]>(`/crm/deals/${dealId}/activities/`),
    create: (dealId: string, data: CrmActivityCreate) =>
      client.post<CrmActivity>(`/crm/deals/${dealId}/activities/`, data),
    delete: (activityId: string) =>
      client.delete(`/crm/activities/${activityId}`),
  },
};

// PQRS (Soporte)
export const pqrs = {
  list: (params?: { tipo?: string; estado?: string; prioridad?: string }) =>
    client.get<TicketPQRS[]>('/pqrs/', { params }),
  get: (id: string) => client.get<TicketPQRS>(`/pqrs/${id}`),
  create: (data: TicketPQRSCreate) => client.post<TicketPQRS>('/pqrs/', data),
  update: (id: string, data: TicketPQRSUpdate) =>
    client.patch<TicketPQRS>(`/pqrs/${id}`, data),
  responder: (id: string, contenido: string) =>
    client.post<TicketPQRS>(`/pqrs/${id}/respuestas`, { contenido }),
  adminTodos: (params?: { tenant_id?: string; tipo?: string; estado?: string; prioridad?: string }) =>
    client.get<TicketPQRSAdmin[]>('/pqrs/admin/todos', { params }),
  adminResponder: (id: string, contenido: string) =>
    client.post<TicketPQRSAdmin>(`/pqrs/admin/${id}/responder`, { contenido }),
};

// Calificaciones
export const calificaciones = {
  crear: (data: CalificacionCreate) =>
    client.post<CalificacionResponse>('/calificaciones/', data),
  miCalificacion: () =>
    client.get<CalificacionResponse>('/calificaciones/mi-tenant'),
  adminList: (params?: { estado?: string }) =>
    client.get<CalificacionResponse[]>('/calificaciones/admin', { params }),
  moderar: (id: string, nuevo_estado: string) =>
    client.patch<CalificacionResponse>(`/calificaciones/${id}/moderar`, { nuevo_estado }),
};

// Socia — Costos Indirectos
export const costosIndirectos = {
  list: (params?: { solo_activos?: boolean }) =>
    client.get<CostoIndirecto[]>('/costos-indirectos/', { params }),
  create: (data: { nombre: string; monto: number; tipo: 'FIJO' | 'PORCENTAJE' }) =>
    client.post<CostoIndirecto>('/costos-indirectos/', data),
  update: (id: string, data: { nombre?: string; monto?: number; tipo?: string; activo?: boolean }) =>
    client.put<CostoIndirecto>(`/costos-indirectos/${id}`, data),
  delete: (id: string) =>
    client.delete(`/costos-indirectos/${id}`),
};

// Socia — Análisis de Precios (IO/AO)
export const analisisPrecios = {
  cvu: (data: CVURequest) =>
    client.post<CVUResponse>('/analisis-precios/cvu', data),
  sensibilidad: (data: {
    receta_id: string;
    precio_venta: number;
    costos_fijos: number;
    volumen_base: number;
    variaciones: Array<{ variable: string; delta_porcentaje: number; ingrediente_id?: string }>;
  }) =>
    client.post<SensibilidadResponse>('/analisis-precios/sensibilidad', data),
  escenarios: (data: {
    receta_id: string;
    costos_fijos: number;
    volumen: number;
    precio_mercado_referencia?: number;
  }) =>
    client.post<EscenariosResponse>('/analisis-precios/escenarios', data),
  comparador: (receta_ids?: string) =>
    client.get<RentabilidadItem[]>('/analisis-precios/comparador', {
      params: receta_ids ? { receta_ids } : undefined,
    }),
  economiaEscala: (data: {
    receta_id: string;
    costos_fijos_setup: number;
    lotes?: number[];
  }) =>
    client.post<EconomiaEscalaResponse>('/analisis-precios/economia-escala', data),
};

// Socia — Gamificación
export const socia = {
  progreso: () =>
    client.get<SociaProgreso>('/socia/progreso'),
  registrarLogro: (logro_id: string) =>
    client.post<{ logro_id: string; nivel_actual: string }>(`/socia/logro/${logro_id}`),
};
