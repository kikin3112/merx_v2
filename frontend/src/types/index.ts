export interface User {
  id: string;
  email: string;
  nombre: string;
  rol: string;
  estado: boolean;
  es_superadmin: boolean;
}

// ---- Tenant Management (superadmin) ----

export interface TenantDetail {
  id: string;
  nombre: string;
  slug: string;
  nit: string | null;
  email_contacto: string;
  telefono: string | null;
  direccion: string | null;
  ciudad: string | null;
  departamento: string | null;
  url_logo: string | null;
  color_primario: string;
  color_secundario: string;
  plan_id: string;
  estado: string;
  fecha_inicio_suscripcion: string | null;
  fecha_fin_suscripcion: string | null;
  created_at: string;
  updated_at: string;
}

export interface UsuarioTenant {
  id: string;
  usuario_id: string;
  tenant_id: string;
  rol: string;
  fecha_ingreso: string;
  created_at: string;
  updated_at: string;
}

export interface Tenant {
  id: string;
  nombre: string;
  slug: string;
  estado: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  tenants: Tenant[];
}

export interface TenantTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  tenant: Tenant;
  rol_en_tenant: string;
}

// ---- Productos ----

export interface Producto {
  id: string;
  codigo_interno: string;
  codigo_barras: string | null;
  nombre: string;
  descripcion: string | null;
  categoria: string;
  unidad_medida: string;
  maneja_inventario: boolean;
  porcentaje_iva: number;
  tipo_iva: string;
  precio_venta: number;
  stock_minimo: number | null;
  stock_maximo: number | null;
  estado: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductoCreate {
  codigo_interno: string;
  codigo_barras?: string | null;
  nombre: string;
  descripcion?: string | null;
  categoria: string;
  unidad_medida: string;
  maneja_inventario?: boolean;
  porcentaje_iva?: number;
  tipo_iva: string;
  precio_venta?: number;
  stock_minimo?: number | null;
  stock_maximo?: number | null;
  estado?: boolean;
}

export interface ProductoUpdate {
  codigo_barras?: string | null;
  nombre?: string;
  descripcion?: string | null;
  categoria?: string;
  unidad_medida?: string;
  maneja_inventario?: boolean;
  porcentaje_iva?: number;
  tipo_iva?: string;
  precio_venta?: number;
  stock_minimo?: number | null;
  stock_maximo?: number | null;
  estado?: boolean;
}

// ---- Terceros ----

export interface Tercero {
  id: string;
  tipo_documento: string;
  numero_documento: string;
  nombre: string;
  tipo_tercero: string;
  direccion: string | null;
  telefono: string | null;
  email: string | null;
  estado: boolean;
  notas: string | null;
  limite_credito: number;
  plazo_pago_dias: number;
  persona_contacto: string | null;
  sector_economico: string | null;
  grupo_cliente: string | null;
  created_at: string;
  updated_at: string;
}

export interface TerceroCreate {
  tipo_documento: string;
  numero_documento: string;
  nombre: string;
  tipo_tercero: string;
  direccion?: string | null;
  telefono?: string | null;
  email?: string | null;
  estado?: boolean;
  notas?: string | null;
  limite_credito?: number;
  plazo_pago_dias?: number;
  persona_contacto?: string | null;
  sector_economico?: string | null;
  grupo_cliente?: string | null;
}

export interface TerceroUpdate {
  nombre?: string;
  tipo_tercero?: string;
  direccion?: string | null;
  telefono?: string | null;
  email?: string | null;
  estado?: boolean;
  notas?: string | null;
  limite_credito?: number;
  plazo_pago_dias?: number;
  persona_contacto?: string | null;
  sector_economico?: string | null;
  grupo_cliente?: string | null;
}

// ---- Ventas ----

export interface Venta {
  id: string;
  numero_venta: string;
  tercero_id: string;
  fecha_venta: string;
  estado: string;
  descuento_global: number;
  observaciones: string | null;
  url_pdf: string | null;
  subtotal: number;
  total_descuento: number;
  base_gravable: number;
  total_iva: number;
  total_venta: number;
  detalles: VentaDetalle[];
}

export interface VentaDetalle {
  id: string;
  venta_id: string;
  producto_id: string;
  cantidad: number;
  precio_unitario: number;
  descuento: number;
  porcentaje_iva: number;
  subtotal: number;
  base_gravable: number;
  valor_iva: number;
  total_linea: number;
}

// ---- Facturas (reuses Venta type) ----
export type Factura = Venta;

// ---- Cotizaciones ----

export interface Cotizacion {
  id: string;
  numero_cotizacion: string;
  tercero_id: string;
  fecha_cotizacion: string;
  fecha_vencimiento: string;
  estado: string;
  descuento_global: number;
  observaciones: string | null;
  url_pdf: string | null;
  subtotal: number;
  total_descuento: number;
  total_iva: number;
  total_cotizacion: number;
  detalles: CotizacionDetalle[];
}

export interface CotizacionDetalle {
  id: string;
  cotizacion_id: string;
  producto_id: string;
  cantidad: number;
  precio_unitario: number;
  descuento: number;
  porcentaje_iva: number;
  subtotal: number;
  base_gravable: number;
  valor_iva: number;
  total_linea: number;
}

// ---- Contabilidad ----

export interface AsientoContable {
  id: string;
  numero_asiento: string;
  fecha: string;
  tipo_asiento: string;
  concepto: string;
  documento_referencia: string | null;
  estado: string;
  detalles: DetalleAsiento[];
}

export interface DetalleAsiento {
  id: string;
  asiento_id: string;
  cuenta_id: string;
  cuenta_codigo?: string;
  cuenta_nombre?: string;
  debito: number;
  credito: number;
  descripcion: string | null;
}

export interface BalancePrueba {
  cuentas: BalanceCuenta[];
  total_debito: number;
  total_credito: number;
  diferencia: number;
  balanceado: boolean;
}

export interface BalanceCuenta {
  cuenta_id: string;
  codigo: string;
  nombre: string;
  tipo_cuenta: string;
  naturaleza: string;
  total_debito: number;
  total_credito: number;
  saldo: number;
}

// ---- Dashboard / Reportes ----

export interface DashboardKPIs {
  total_ventas: number;
  cantidad_ventas: number;
  promedio_venta: number;
  alertas_stock_bajo: number;
  ventas_hoy: number;
  cantidad_hoy: number;
  ventas_mes: number;
  cantidad_mes: number;
  facturas_pendientes: number;
  cantidad_facturas_pendientes: number;
}

export interface VentaDiaria {
  fecha: string;
  total: number;
  cantidad: number;
}

export interface ProductoMasVendido {
  producto_id: string;
  nombre: string;
  codigo: string;
  precio_venta: number;
  total_cantidad: number;
  total_ingresos: number;
}

export interface TopCliente {
  tercero_id: string;
  nombre: string;
  total_ventas: number;
  cantidad_ventas: number;
}

export interface RentabilidadProducto {
  producto_id: string;
  nombre: string;
  codigo: string;
  categoria: string;
  precio_venta: number;
  costo_promedio: number;
  margen_bruto: number;
  margen_porcentaje: number;
  stock: number;
  valor_inventario: number;
}

export interface ABCProducto {
  producto_id: string;
  nombre: string;
  codigo: string;
  stock: number;
  valor_total: number;
  porcentaje_valor: number;
  porcentaje_acumulado: number;
  clasificacion: 'A' | 'B' | 'C';
}

export interface ABCInventario {
  productos: ABCProducto[];
  resumen: { A: number; B: number; C: number };
  valor_total_inventario: number;
}

// ---- Recetas ----

export interface RecetaIngrediente {
  id: string;
  receta_id: string;
  producto_id: string;
  cantidad: number;
  unidad: string;
  notas: string | null;
  costo_linea: number | null;
}

export interface Receta {
  id: string;
  nombre: string;
  descripcion: string | null;
  producto_resultado_id: string;
  cantidad_resultado: number;
  costo_mano_obra: number;
  tiempo_produccion_minutos: number | null;
  notas: string | null;
  estado: boolean;
  costo_ingredientes: number | null;
  costo_total: number | null;
  costo_unitario: number | null;
  ingredientes: RecetaIngrediente[];
  created_at: string;
  updated_at: string;
}

export interface RecetaCosto {
  receta_id: string;
  receta_nombre: string;
  producto_resultado_id: string;
  cantidad_resultado: number;
  costo_ingredientes: number;
  costo_mano_obra: number;
  costo_total: number;
  costo_unitario: number;
  precio_venta_actual: number;
  margen_actual_porcentaje: number;
  detalle_ingredientes: {
    producto_id: string;
    producto_nombre: string;
    cantidad: number;
    unidad: string;
    costo_unitario: number;
    costo_linea: number;
  }[];
}

export interface ProduccionResponse {
  receta_id: string;
  receta_nombre: string;
  producto_resultado_id: string;
  cantidad_producida: number;
  costo_ingredientes: number;
  costo_mano_obra: number;
  costo_total: number;
  costo_unitario: number;
  documento_referencia: string;
  movimiento_id: string;
}

// ---- Inventario ----

export interface Inventario {
  producto_id: string;
  codigo: string;
  nombre: string;
  cantidad: number;
  costo_promedio: number;
  valor_total: number;
}

export interface AlertaStock {
  producto_id: string;
  codigo: string;
  nombre: string;
  stock_minimo: number;
  stock_actual: number;
  diferencia: number;
}

export interface MovimientoInventario {
  id: string;
  producto_id: string;
  tipo_movimiento: string;
  cantidad: number;
  costo_unitario: number | null;
  valor_total: number | null;
  documento_referencia: string | null;
  observaciones: string | null;
  fecha_movimiento: string;
  created_at: string;
}

// ---- Reportes Avanzados ----

export interface RentabilidadCategoria {
  categoria: string;
  cantidad_productos: number;
  precio_promedio: number;
  costo_promedio: number;
  margen_promedio: number;
  valor_inventario: number;
  stock_total: number;
}

export interface ComparativaMensual {
  mes_actual: {
    total_ventas: number;
    cantidad_ventas: number;
    promedio_venta: number;
    periodo: string;
  };
  mes_anterior: {
    total_ventas: number;
    cantidad_ventas: number;
    promedio_venta: number;
    periodo: string;
  };
  variacion: {
    total_ventas: number;
    cantidad_ventas: number;
    promedio_venta: number;
  };
}

export interface ProyeccionFlujoCaja {
  promedio_diario: number;
  total_por_cobrar: number;
  cantidad_facturas_pendientes: number;
  total_proyectado: number;
  dias_proyeccion: number;
  proyeccion: {
    fecha: string;
    proyectado_dia: number;
    acumulado: number;
  }[];
}

export interface MargenCategoria {
  categoria: string;
  ingresos: number;
  costo: number;
  margen: number;
  margen_porcentaje: number;
  cantidad_items: number;
}

// ---- Cartera ----

export interface CarteraItem {
  id: string;
  tipo_cartera: 'COBRAR' | 'PAGAR';
  documento_referencia: string;
  tercero_id: string;
  fecha_emision: string;
  fecha_vencimiento: string;
  valor_total: number;
  saldo_pendiente: number;
  estado: string;
  observaciones: string | null;
  created_at: string;
  updated_at: string;
}

export interface PagoCartera {
  id: string;
  cartera_id: string;
  fecha_pago: string;
  valor_pago: number;
  medio_pago_id: string;
  numero_referencia: string | null;
  observaciones: string | null;
  created_at: string;
}

export interface CarteraResumen {
  total_por_cobrar: number;
  total_vencido: number;
  cantidad_pendientes: number;
  cantidad_vencidas: number;
}

export interface MedioPago {
  id: string;
  nombre: string;
  tipo: string;
}

// ---- SaaS Management (superadmin) ----

export interface PlanWithStats {
  id: string;
  nombre: string;
  descripcion: string | null;
  precio_mensual: number;
  precio_anual: number | null;
  max_usuarios: number;
  max_productos: number;
  max_facturas_mes: number;
  max_storage_mb: number;
  esta_activo: boolean;
  es_default: boolean;
  created_at: string;
  updated_at: string;
  tenant_count: number;
}

export interface PlanCreate {
  nombre: string;
  descripcion?: string | null;
  precio_mensual: number;
  precio_anual?: number | null;
  max_usuarios?: number;
  max_productos?: number;
  max_facturas_mes?: number;
  max_storage_mb?: number;
  esta_activo?: boolean;
  es_default?: boolean;
}

export interface PlanUpdate {
  nombre?: string;
  descripcion?: string | null;
  precio_mensual?: number;
  precio_anual?: number | null;
  max_usuarios?: number;
  max_productos?: number;
  max_facturas_mes?: number;
  max_storage_mb?: number;
  esta_activo?: boolean;
}

export interface TenantMetricas {
  tenant_id: string;
  usuarios_count: number;
  productos_count: number;
  facturas_mes_count: number;
  ventas_total_mes: number;
  terceros_count: number;
  max_usuarios: number;
  max_productos: number;
  max_facturas_mes: number;
}

export interface SaaSDashboardKPIs {
  total_tenants: number;
  tenants_activos: number;
  tenants_trial: number;
  tenants_suspendidos: number;
  tenants_cancelados: number;
  mrr: number;
  nuevos_ultimos_30_dias: number;
  churn_rate: number;
  revenue_por_plan: {
    plan_id: string;
    plan_nombre: string;
    tenant_count: number;
    revenue: number;
  }[];
}

export interface Suscripcion {
  id: string;
  tenant_id: string;
  plan_id: string;
  periodo_inicio: string;
  periodo_fin: string;
  estado: string;
  proveedor_pago: string | null;
  created_at: string;
}

export interface PagoHistorial {
  id: string;
  suscripcion_id: string;
  monto: number;
  moneda: string;
  estado: string;
  id_transaccion_externa: string | null;
  fecha_pago: string | null;
  created_at: string;
}

export interface UsuarioTenantDetail {
  id: string;
  usuario_id: string;
  tenant_id: string;
  rol: string;
  esta_activo: boolean;
  fecha_ingreso: string;
  usuario_nombre: string;
  usuario_email: string;
}

// Ghost Mode (Impersonation)
export interface ImpersonationResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  impersonated_user: User;
  tenant_id: string;
  rol_en_tenant: string;
}

// User Governance (God Mode)
export interface GlobalUserResponse {
  id: string;
  nombre: string;
  email: string;
  rol: string;
  estado: boolean;
  es_superadmin: boolean;
  ultimo_acceso: string | null;
  tenant_count: number;
  created_at: string;
  updated_at: string;
}

export interface GlobalUserListResponse {
  items: GlobalUserResponse[];
  total: number;
  page: number;
  limit: number;
}

export interface GlobalUserCreate {
  nombre: string;
  email: string;
  password: string;
  rol?: string;
  estado?: boolean;
}

export interface GlobalUserUpdate {
  nombre?: string;
  email?: string;
  rol?: string;
  estado?: boolean;
}

export interface UserTenantMembership {
  usuario_tenant_id: string;
  tenant_id: string;
  tenant_nombre: string;
  tenant_slug: string;
  tenant_estado: string;
  rol: string;
  esta_activo: boolean;
  fecha_ingreso: string;
}

export interface TenantPulse {
  tenant_id: string;
  score: number;
  estado_salud: 'saludable' | 'en_riesgo' | 'critico';
  logins_recientes: number;
  ventas_mes: number;
  dias_activo: number;
  calculado_en: string;
}

// ---- CRM ----

export interface CrmPipeline {
  id: string;
  nombre: string;
  descripcion: string | null;
  es_default: boolean;
  color: string;
  tenant_id: string;
  created_at: string;
  etapas: CrmStage[];
}

export interface CrmPipelineCreate {
  nombre: string;
  descripcion?: string | null;
  es_default?: boolean;
  color?: string;
}

export interface CrmPipelineUpdate {
  nombre?: string;
  descripcion?: string | null;
  es_default?: boolean;
  color?: string;
}

export interface CrmStage {
  id: string;
  pipeline_id: string;
  nombre: string;
  orden: number;
  probabilidad: number;
}

export interface CrmStageCreate {
  pipeline_id: string;
  nombre: string;
  orden: number;
  probabilidad?: number;
}

export interface CrmStageUpdate {
  nombre?: string;
  orden?: number;
  probabilidad?: number;
}

export type EstadoDeal = 'ABIERTO' | 'GANADO' | 'PERDIDO' | 'ABANDONADO';

export interface CrmDeal {
  id: string;
  nombre: string;
  tercero_id: string;
  tercero_nombre: string | null;
  stage_id: string;
  stage_nombre: string | null;
  pipeline_id: string;
  usuario_id: string | null;
  usuario_nombre: string | null;
  valor_estimado: number;
  moneda: string;
  fecha_cierre_estimada: string | null;
  origen: string | null;
  estado_cierre: EstadoDeal;
  motivo_perdida: string | null;
  fecha_ultimo_contacto: string | null;
  created_at: string;
  updated_at: string;
}

export interface CrmDealCreate {
  nombre: string;
  tercero_id: string;
  pipeline_id: string;
  stage_id: string;
  usuario_id?: string | null;
  valor_estimado?: number;
  moneda?: string;
  fecha_cierre_estimada?: string | null;
  origen?: string | null;
}

export interface CrmDealUpdate {
  nombre?: string;
  valor_estimado?: number;
  fecha_cierre_estimada?: string | null;
  usuario_id?: string | null;
}

export type TipoActividadCRM = 'NOTA' | 'LLAMADA' | 'EMAIL' | 'REUNION' | 'WHATSAPP' | 'TAREA';

export interface CrmActivity {
  id: string;
  deal_id: string;
  usuario_id: string | null;
  usuario_nombre: string | null;
  tipo: TipoActividadCRM;
  asunto: string | null;
  contenido: string | null;
  fecha_actividad: string;
  duracion_minutos: number;
  es_automatica: boolean;
  created_at: string;
}

export interface CrmActivityCreate {
  deal_id: string;
  tipo: TipoActividadCRM;
  asunto?: string | null;
  contenido?: string | null;
  fecha_actividad?: string | null;
  duracion_minutos?: number;
}
