from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


# ============================================================================
# AUTENTICACIÓN
# ============================================================================

class LoginRequest(BaseModel):
    """Schema para request de login"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=1, description="Contraseña")


class ChangePasswordRequest(BaseModel):
    """Schema para cambio de contraseña"""
    current_password: str = Field(..., min_length=1, description="Contraseña actual")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña (mínimo 8 caracteres)")


class Token(BaseModel):
    """Schema para respuesta de autenticación con tokens"""
    access_token: str = Field(..., description="Token de acceso JWT")
    refresh_token: str = Field(..., description="Token de refresh JWT")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Segundos hasta que expire el access token")
    user: "UsuarioResponse" = Field(..., description="Información del usuario autenticado")


# ============================================================================
# USUARIOS
# ============================================================================

class UsuarioBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    email: EmailStr
    rol: str = Field(..., pattern="^(admin|operador|contador)$")
    estado: bool = True


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8)


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    rol: Optional[str] = None
    estado: Optional[bool] = None
    password: Optional[str] = None


class UsuarioResponse(UsuarioBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TERCEROS
# ============================================================================

class TerceroBase(BaseModel):
    tipo_documento: str = Field(..., pattern="^(CC|NIT|CE|PAS|TI)$")
    numero_documento: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=200)
    tipo_tercero: str = Field(..., pattern="^(CLIENTE|PROVEEDOR|AMBOS)$")
    direccion: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    estado: bool = True


class TerceroCreate(TerceroBase):
    pass


class TerceroUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo_tercero: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    estado: Optional[bool] = None


class TerceroResponse(TerceroBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PRODUCTOS
# ============================================================================

class ProductoBase(BaseModel):
    codigo_interno: str = Field(..., max_length=50)
    codigo_barras: Optional[str] = Field(None, max_length=100)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    categoria: str = Field(..., pattern="^(Insumo|Producto_Propio|Producto_Tercero|Servicio)$")
    unidad_medida: str = Field(..., pattern="^(UNIDAD|KILOGRAMO|GRAMO|LITRO|METRO|CAJA|SET)$")
    maneja_inventario: bool = True
    porcentaje_iva: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    tipo_iva: str = Field(..., pattern="^(Excluido|Exento|Gravado)$")
    precio_venta: Decimal = Field(default=Decimal("0.00"), ge=0)
    stock_minimo: Optional[Decimal] = Field(None, ge=0)
    stock_maximo: Optional[Decimal] = Field(None, ge=0)
    estado: bool = True


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    codigo_barras: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    unidad_medida: Optional[str] = None
    maneja_inventario: Optional[bool] = None
    porcentaje_iva: Optional[Decimal] = None
    tipo_iva: Optional[str] = None
    precio_venta: Optional[Decimal] = None
    stock_minimo: Optional[Decimal] = None
    stock_maximo: Optional[Decimal] = None
    estado: Optional[bool] = None


class ProductoResponse(ProductoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INVENTARIOS
# ============================================================================

class InventarioBase(BaseModel):
    producto_id: UUID
    cantidad_disponible: Decimal = Field(default=Decimal("0.00"), ge=0)
    costo_promedio_ponderado: Decimal = Field(default=Decimal("0.00"), ge=0)
    valor_total: Decimal = Field(default=Decimal("0.00"), ge=0)


class InventarioCreate(InventarioBase):
    pass


class InventarioUpdate(BaseModel):
    cantidad_disponible: Optional[Decimal] = None
    costo_promedio_ponderado: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None


class InventarioResponse(InventarioBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MovimientoInventarioBase(BaseModel):
    producto_id: UUID
    tipo_movimiento: str  # Usa Enum del modelo
    cantidad: Decimal
    costo_unitario: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None
    documento_referencia: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None


class MovimientoInventarioCreate(MovimientoInventarioBase):
    pass


class MovimientoInventarioResponse(MovimientoInventarioBase):
    id: UUID
    fecha_movimiento: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# VENTAS
# ============================================================================

class VentasDetalleBase(BaseModel):
    producto_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., ge=0)
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0)
    porcentaje_iva: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)


class VentasDetalleCreate(VentasDetalleBase):
    """
    Schema para crear detalle de venta.
    Los campos calculados (subtotal, base_gravable, valor_iva, total_linea)
    se generan automáticamente via @hybrid_property en el modelo.
    """
    pass


class VentasDetalleResponse(VentasDetalleBase):
    """
    Schema de respuesta con campos calculados incluidos
    """
    id: UUID
    venta_id: UUID
    # Campos calculados (vienen del modelo via @hybrid_property)
    subtotal: Decimal
    base_gravable: Decimal
    valor_iva: Decimal
    total_linea: Decimal
    model_config = ConfigDict(from_attributes=True)


class VentasBase(BaseModel):
    tercero_id: UUID
    fecha_venta: date
    estado: str = "PENDIENTE"
    observaciones: Optional[str] = None


class VentasCreate(BaseModel):
    """
    Schema para crear venta.
    NO requiere totales manuales del cliente.
    Los totales se calculan automáticamente en el servicio.
    """
    tercero_id: UUID
    fecha_venta: date
    observaciones: Optional[str] = None
    detalles: List[VentasDetalleCreate]


class VentasUpdate(BaseModel):
    estado: Optional[str] = None
    observaciones: Optional[str] = None


class VentasResponse(BaseModel):
    """
    Schema de respuesta con todos los campos calculados
    """
    id: UUID
    numero_venta: str
    tercero_id: UUID
    fecha_venta: date
    estado: str
    observaciones: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Campos calculados (vienen del modelo via @hybrid_property)
    subtotal: Decimal
    total_descuento: Decimal
    base_gravable: Decimal
    total_iva: Decimal
    total_venta: Decimal

    # Relaciones
    detalles: List[VentasDetalleResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# COMPRAS
# ============================================================================

class ComprasDetalleBase(BaseModel):
    producto_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., ge=0)
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0)
    porcentaje_iva: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)


class ComprasDetalleCreate(ComprasDetalleBase):
    """Los campos calculados se generan automáticamente"""
    pass


class ComprasDetalleResponse(ComprasDetalleBase):
    id: UUID
    compra_id: UUID
    # Campos calculados
    subtotal: Decimal
    base_gravable: Decimal
    valor_iva: Decimal
    total_linea: Decimal
    model_config = ConfigDict(from_attributes=True)


class ComprasBase(BaseModel):
    tercero_id: UUID
    fecha_compra: date
    estado: str = "PENDIENTE"
    observaciones: Optional[str] = None


class ComprasCreate(BaseModel):
    """NO requiere totales manuales"""
    tercero_id: UUID
    fecha_compra: date
    observaciones: Optional[str] = None
    detalles: List[ComprasDetalleCreate]


class ComprasUpdate(BaseModel):
    estado: Optional[str] = None
    observaciones: Optional[str] = None


class ComprasResponse(BaseModel):
    id: UUID
    numero_compra: str
    tercero_id: UUID
    fecha_compra: date
    estado: str
    observaciones: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Campos calculados
    subtotal: Decimal
    total_descuento: Decimal
    base_gravable: Decimal
    total_iva: Decimal
    total_compra: Decimal

    detalles: List[ComprasDetalleResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ÓRDENES DE PRODUCCIÓN
# ============================================================================

class OrdenesProduccionDetalleBase(BaseModel):
    insumo_id: UUID
    cantidad_requerida: Decimal = Field(..., gt=0)
    costo_unitario: Decimal = Field(..., ge=0)


class OrdenesProduccionDetalleCreate(OrdenesProduccionDetalleBase):
    """Costo total se calcula automáticamente"""
    pass


class OrdenesProduccionDetalleResponse(OrdenesProduccionDetalleBase):
    id: UUID
    orden_id: UUID
    costo_total: Decimal  # Calculado
    model_config = ConfigDict(from_attributes=True)


class OrdenesProduccionBase(BaseModel):
    producto_id: UUID
    cantidad_producir: Decimal = Field(..., gt=0)
    fecha_inicio: date
    fecha_fin_estimada: Optional[date] = None
    estado: str = "PENDIENTE"
    observaciones: Optional[str] = None


class OrdenesProduccionCreate(BaseModel):
    """NO requiere costo_estimado manual"""
    producto_id: UUID
    cantidad_producir: Decimal = Field(..., gt=0)
    fecha_inicio: date
    fecha_fin_estimada: Optional[date] = None
    observaciones: Optional[str] = None
    detalles: List[OrdenesProduccionDetalleCreate]


class OrdenesProduccionUpdate(BaseModel):
    fecha_fin_real: Optional[date] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None


class OrdenesProduccionResponse(BaseModel):
    id: UUID
    numero_orden: str
    producto_id: UUID
    cantidad_producir: Decimal
    fecha_inicio: date
    fecha_fin_estimada: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    estado: str
    observaciones: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Campos calculados
    costo_estimado: Decimal
    costo_unitario: Decimal

    detalles: List[OrdenesProduccionDetalleResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# COTIZACIONES
# ============================================================================

class CotizacionesDetalleBase(BaseModel):
    producto_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., ge=0)
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0)
    porcentaje_iva: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)


class CotizacionesDetalleCreate(CotizacionesDetalleBase):
    pass


class CotizacionesDetalleResponse(CotizacionesDetalleBase):
    id: UUID
    cotizacion_id: UUID
    subtotal: Decimal
    base_gravable: Decimal
    valor_iva: Decimal
    total_linea: Decimal
    model_config = ConfigDict(from_attributes=True)


class CotizacionesBase(BaseModel):
    tercero_id: UUID
    fecha_cotizacion: date
    fecha_vencimiento: date
    estado: str = "VIGENTE"
    observaciones: Optional[str] = None


class CotizacionesCreate(BaseModel):
    tercero_id: UUID
    fecha_cotizacion: date
    fecha_vencimiento: date
    observaciones: Optional[str] = None
    detalles: List[CotizacionesDetalleCreate]


class CotizacionesUpdate(BaseModel):
    estado: Optional[str] = None
    observaciones: Optional[str] = None


class CotizacionesResponse(BaseModel):
    id: UUID
    numero_cotizacion: str
    tercero_id: UUID
    fecha_cotizacion: date
    fecha_vencimiento: date
    estado: str
    observaciones: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    subtotal: Decimal
    total_descuento: Decimal
    total_iva: Decimal
    total_cotizacion: Decimal

    detalles: List[CotizacionesDetalleResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CUENTAS CONTABLES
# ============================================================================

class CuentaContableBase(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=200)
    tipo_cuenta: str = Field(..., pattern="^(ACTIVO|PASIVO|PATRIMONIO|INGRESO|EGRESO|COSTOS)$")
    nivel: int = Field(..., ge=1, le=6)
    cuenta_padre_id: Optional[UUID] = None
    naturaleza: str = Field(..., pattern="^(DEBITO|CREDITO)$")
    acepta_movimiento: bool = True
    estado: bool = True


class CuentaContableCreate(CuentaContableBase):
    pass


class CuentaContableUpdate(BaseModel):
    nombre: Optional[str] = None
    acepta_movimiento: Optional[bool] = None
    estado: Optional[bool] = None


class CuentaContableResponse(CuentaContableBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CONFIGURACIÓN CONTABLE
# ============================================================================

class ConfiguracionContableBase(BaseModel):
    concepto: str = Field(..., max_length=100)
    cuenta_debito_id: Optional[UUID] = None
    cuenta_credito_id: Optional[UUID] = None
    descripcion: Optional[str] = None


class ConfiguracionContableCreate(ConfiguracionContableBase):
    pass


class ConfiguracionContableUpdate(BaseModel):
    cuenta_debito_id: Optional[UUID] = None
    cuenta_credito_id: Optional[UUID] = None
    descripcion: Optional[str] = None


class ConfiguracionContableResponse(ConfiguracionContableBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ASIENTOS CONTABLES
# ============================================================================

class DetalleAsientoBase(BaseModel):
    cuenta_id: UUID
    debito: Decimal = Field(default=Decimal("0.00"), ge=0)
    credito: Decimal = Field(default=Decimal("0.00"), ge=0)
    descripcion: Optional[str] = None


class DetalleAsientoCreate(DetalleAsientoBase):
    pass


class DetalleAsientoResponse(DetalleAsientoBase):
    id: UUID
    asiento_id: UUID
    model_config = ConfigDict(from_attributes=True)


class AsientoContableBase(BaseModel):
    fecha: date
    tipo_asiento: str = Field(..., pattern="^(VENTAS|COMPRAS|PRODUCCION|AJUSTE|NOMINA|OTRO)$")
    concepto: str = Field(..., max_length=200)
    documento_referencia: Optional[str] = Field(None, max_length=100)
    estado: str = "ACTIVO"


class AsientoContableCreate(BaseModel):
    fecha: date
    tipo_asiento: str
    concepto: str
    documento_referencia: Optional[str] = None
    detalles: List[DetalleAsientoCreate]


class AsientoContableUpdate(BaseModel):
    estado: Optional[str] = None


class AsientoContableResponse(BaseModel):
    id: UUID
    numero_asiento: str
    fecha: date
    tipo_asiento: str
    concepto: str
    documento_referencia: Optional[str] = None
    estado: str
    created_at: datetime
    updated_at: datetime
    detalles: List[DetalleAsientoResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# MEDIOS DE PAGO
# ============================================================================

class MedioPagoBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    tipo: str = Field(..., pattern="^(EFECTIVO|TRANSFERENCIA|CHEQUE|TARJETA_CREDITO|TARJETA_DEBITO|OTRO)$")
    requiere_referencia: bool = False
    estado: bool = True


class MedioPagoCreate(MedioPagoBase):
    pass


class MedioPagoUpdate(BaseModel):
    nombre: Optional[str] = None
    requiere_referencia: Optional[bool] = None
    estado: Optional[bool] = None


class MedioPagoResponse(MedioPagoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CARTERA (CUENTAS POR COBRAR/PAGAR)
# ============================================================================

class CarteraBase(BaseModel):
    tipo_cartera: str = Field(..., pattern="^(COBRAR|PAGAR)$")
    documento_referencia: str = Field(..., max_length=100)
    tercero_id: UUID
    fecha_emision: date
    fecha_vencimiento: date
    valor_total: Decimal = Field(..., ge=0)
    saldo_pendiente: Decimal = Field(..., ge=0)
    estado: str = "PENDIENTE"
    observaciones: Optional[str] = None


class CarteraCreate(CarteraBase):
    pass


class CarteraUpdate(BaseModel):
    saldo_pendiente: Optional[Decimal] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None


class CarteraResponse(CarteraBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PagoCarteraBase(BaseModel):
    cartera_id: UUID
    fecha_pago: date
    valor_pago: Decimal = Field(..., gt=0)
    medio_pago_id: UUID
    numero_referencia: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None


class PagoCarteraCreate(PagoCarteraBase):
    pass


class PagoCarteraResponse(PagoCarteraBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SECUENCIAS
# ============================================================================

class SecuenciaBase(BaseModel):
    nombre: str = Field(..., max_length=50)
    prefijo: str = Field(..., max_length=20)
    siguiente_numero: int = Field(default=1, ge=1)
    longitud_numero: int = Field(default=6, ge=1, le=10)


class SecuenciaCreate(SecuenciaBase):
    pass


class SecuenciaUpdate(BaseModel):
    siguiente_numero: Optional[int] = None


class SecuenciaResponse(SecuenciaBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)