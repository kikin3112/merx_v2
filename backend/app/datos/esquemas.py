from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

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


class UsuarioMini(BaseModel):
    """Schema mínimo de usuario para embeddings (creadores, etc.)"""

    id: UUID
    nombre: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TerceroMini(BaseModel):
    """Schema mínimo de tercero para embeddings en ventas."""

    id: UUID
    nombre: str
    telefono: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    email: EmailStr
    rol: str = Field(..., pattern="^(superadmin|admin|operador|contador|vendedor|readonly)$")
    estado: bool = True


class UsuarioCreate(UsuarioBase):
    """Creación de usuario. El rol 'superadmin' NO es asignable via API."""

    rol: str = Field(..., pattern="^(admin|operador|contador|vendedor|readonly)$")
    password: str = Field(..., min_length=8)


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    rol: Optional[str] = Field(None, pattern="^(admin|operador|contador|vendedor|readonly)$")
    estado: Optional[bool] = None
    password: Optional[str] = None


class UsuarioResponse(UsuarioBase):
    id: UUID
    es_superadmin: bool = False
    ultimo_acceso: Optional[datetime] = None
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
    # CRM fields
    notas: Optional[str] = None
    limite_credito: Decimal = Field(default=Decimal("0.00"), ge=0)
    plazo_pago_dias: int = Field(default=0, ge=0)
    persona_contacto: Optional[str] = Field(None, max_length=200)
    sector_economico: Optional[str] = Field(None, max_length=100)
    grupo_cliente: Optional[str] = Field(None, max_length=100)


class TerceroCreate(TerceroBase):
    pass


class TerceroUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo_tercero: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    estado: Optional[bool] = None
    notas: Optional[str] = None
    limite_credito: Optional[Decimal] = None
    plazo_pago_dias: Optional[int] = None
    persona_contacto: Optional[str] = None
    sector_economico: Optional[str] = None
    grupo_cliente: Optional[str] = None


class TerceroResponse(TerceroBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    porcentaje_iva: Optional[Decimal] = Field(None, ge=0, le=100)
    tipo_iva: Optional[str] = None
    precio_venta: Optional[Decimal] = Field(None, ge=0)
    stock_minimo: Optional[Decimal] = Field(None, ge=0)
    stock_maximo: Optional[Decimal] = Field(None, ge=0)
    estado: Optional[bool] = None


class ProductoResponse(ProductoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    updated_at: datetime
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============================================================================
# VENTAS
# ============================================================================


class VentasDetalleBase(BaseModel):
    producto_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., ge=0)
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Porcentaje de descuento (0-100)")
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
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    # Campos calculados (vienen del modelo via @hybrid_property)
    subtotal: Decimal
    base_gravable: Decimal
    valor_iva: Decimal
    total_linea: Decimal
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="wrap")
    @classmethod
    def _add_producto_fields(cls, value, handler):
        result = handler(value)
        if hasattr(value, "producto") and value.producto:
            result.nombre = value.producto.nombre
            result.categoria = value.producto.categoria
        return result


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
    descuento_global: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Descuento global % (0-100)")
    observaciones: Optional[str] = None
    detalles: List[VentasDetalleCreate] = Field(..., min_length=1)


class VentasUpdate(BaseModel):
    estado: Optional[str] = None
    observaciones: Optional[str] = None


class VentaEnvioCreate(BaseModel):
    canal: str = Field(..., pattern="^(whatsapp|email)$")
    destinatario: str = Field(..., min_length=1, max_length=200)


class VentaEnvioResponse(BaseModel):
    id: UUID
    venta_id: UUID
    canal: str
    destinatario: str
    enviado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class VentasResponse(BaseModel):
    """
    Schema de respuesta con todos los campos calculados
    """

    id: UUID
    numero_venta: str
    tercero_id: UUID
    fecha_venta: date
    estado: str
    descuento_global: Decimal = Decimal("0.00")
    observaciones: Optional[str] = None
    url_pdf: Optional[str] = None
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
    tercero: Optional[TerceroMini] = None
    envios: List[VentaEnvioResponse] = []

    # Auditoría
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============================================================================
# COMPRAS
# ============================================================================


class ComprasDetalleBase(BaseModel):
    producto_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., ge=0)
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Porcentaje de descuento (0-100)")
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
    descuento_global: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
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
    descuento_global: Decimal = Decimal("0.00")
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

    # Auditoría
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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

    # Auditoría
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============================================================================
# RECETAS (BOM - Bill of Materials)
# ============================================================================


class RecetaIngredienteBase(BaseModel):
    producto_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    unidad: str = Field(default="UNIDAD", pattern="^(UNIDAD|GRAMO|KILOGRAMO|MILILITRO|LITRO|METRO|CENTIMETRO)$")
    porcentaje_merma: Decimal = Field(default=Decimal("0.00"), ge=0, lt=100)
    notas: Optional[str] = Field(None, max_length=200)


class RecetaIngredienteCreate(RecetaIngredienteBase):
    pass


class RecetaIngredienteResponse(RecetaIngredienteBase):
    id: UUID
    receta_id: UUID
    costo_linea: Optional[Decimal] = None
    producto_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_nombre(cls, obj: object) -> "RecetaIngredienteResponse":
        """Construye la respuesta incluyendo el nombre del producto si está cargado."""
        instance = cls.model_validate(obj)
        producto = getattr(obj, "producto", None)
        if producto:
            instance.producto_nombre = getattr(producto, "nombre", None)
        return instance


class RecetaBase(BaseModel):
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    producto_resultado_id: UUID
    cantidad_resultado: Decimal = Field(default=Decimal("1.00"), gt=0)
    costo_mano_obra: Decimal = Field(default=Decimal("0.00"), ge=0)
    tiempo_produccion_minutos: Optional[int] = Field(None, ge=0)
    margen_objetivo: Optional[Decimal] = Field(None, gt=0, lt=100)
    produccion_mensual_esperada: Optional[Decimal] = Field(
        None, gt=0, description="Unidades/mes esperadas para distribuir CIF fijo mensual"
    )
    notas: Optional[str] = None
    estado: bool = True


class RecetaCreate(RecetaBase):
    ingredientes: List[RecetaIngredienteCreate] = Field(default=[])


class RecetaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    cantidad_resultado: Optional[Decimal] = None
    costo_mano_obra: Optional[Decimal] = None
    tiempo_produccion_minutos: Optional[int] = None
    margen_objetivo: Optional[Decimal] = Field(None, gt=0, lt=100)
    produccion_mensual_esperada: Optional[Decimal] = Field(None, gt=0)
    notas: Optional[str] = None
    estado: Optional[bool] = None


class RecetaResponse(RecetaBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    ingredientes: List[RecetaIngredienteResponse] = []

    # Auditoría
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def model_validate(cls, obj: object, **kwargs: object) -> "RecetaResponse":  # type: ignore[override]
        """Hydrata producto_nombre en cada ingrediente al serializar desde ORM."""
        instance = super().model_validate(obj, **kwargs)
        orm_ingredientes = getattr(obj, "ingredientes", []) or []
        for i, ing_orm in enumerate(orm_ingredientes):
            if i < len(instance.ingredientes):
                producto = getattr(ing_orm, "producto", None)
                if producto:
                    instance.ingredientes[i].producto_nombre = getattr(producto, "nombre", None)
        return instance


# ============================================================================
# RECETAS - CALCULAR COSTO
# ============================================================================


class IngredienteCostoDetalle(BaseModel):
    producto_id: str
    producto_nombre: str
    cantidad: Decimal
    unidad: str
    porcentaje_merma: Decimal
    cantidad_bruta: Decimal
    costo_unitario: Decimal
    costo_linea: Decimal
    # Nuevos campos: conversión de unidades
    factor_aplicado: Decimal = Decimal("1.000000")
    unidad_inventario: str = ""
    porcentaje_del_total: Decimal = Decimal("0.00")


class RecetaCostoResponse(BaseModel):
    receta_id: str
    receta_nombre: str
    producto_resultado_id: str
    cantidad_resultado: Decimal
    # Estructura profesional de costos de manufactura
    costo_material_directo: Decimal = Decimal("0.00")  # = costo_ingredientes
    costo_mano_obra_directa: Decimal = Decimal("0.00")  # = costo_mano_obra (alias claro)
    costo_primo: Decimal = Decimal("0.00")  # = material_directo + MOD
    costo_indirecto: Decimal = Decimal("0.00")  # CIF
    costo_conversion: Decimal = Decimal("0.00")  # = MOD + CIF
    costo_total: Decimal
    costo_unitario: Decimal
    # Backwards-compat aliases
    costo_ingredientes: Decimal = Decimal("0.00")
    costo_mano_obra: Decimal = Decimal("0.00")
    # CIF distribuido por producción mensual
    cif_fijo_mensual: Decimal = Decimal("0.00")  # Monto fijo mensual ANTES de distribuir
    cif_por_unidad: Decimal = Decimal("0.00")  # CIF fijo ÷ produccion_mensual
    cif_lote: Decimal = Decimal("0.00")  # cif_por_unidad × cantidad_resultado (lo que se suma al costo)
    produccion_mensual_usada: Decimal = Decimal("0.00")  # Base utilizada (histórico o esperado)
    fuente_produccion_mensual: str = "lote"  # "historico" | "esperado" | "lote"
    # Cobertura de stock
    lotes_posibles_con_stock: int = 0
    ingrediente_critico: Optional[str] = None
    # Precio/margen
    precio_venta_actual: Decimal
    margen_actual_porcentaje: Decimal
    margen_objetivo: Optional[Decimal] = None
    precio_sugerido: Optional[Decimal] = None
    detalle_ingredientes: List[IngredienteCostoDetalle]


# ============================================================================
# RECETAS - EQUIVALENCIAS DE UNIDAD
# ============================================================================


class EquivalenciaUnidadCreate(BaseModel):
    unidad_receta: str = Field(..., description="Unidad usada en la receta (ej: GRAMO)")
    factor: Decimal = Field(
        ..., gt=0, description="Factor de conversión: cuántas unidades de inventario por 1 unidad_receta"
    )
    notas: Optional[str] = Field(None, max_length=200)

    @field_validator("unidad_receta")
    @classmethod
    def unidad_valida(cls, v: str) -> str:
        validas = {"UNIDAD", "GRAMO", "KILOGRAMO", "MILILITRO", "LITRO", "METRO", "CENTIMETRO"}
        if v not in validas:
            raise ValueError(f"unidad_receta debe ser una de: {validas}")
        return v


class EquivalenciaUnidadResponse(BaseModel):
    id: UUID
    producto_id: UUID
    unidad_receta: str
    factor: Decimal
    notas: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# RECETAS - COSTO ESTÁNDAR (FIJAR)
# ============================================================================


class FijarCostoRequest(BaseModel):
    notas: Optional[str] = Field(None, max_length=500)
    vigente_desde: Optional[date] = None


class CostoEstandarResponse(BaseModel):
    id: UUID
    receta_id: UUID
    costo_unitario: Decimal
    precio_sugerido: Optional[Decimal] = None
    confirmado_por_nombre: Optional[str] = None
    confirmado_en: datetime
    vigente_desde: Optional[date] = None
    notas_confirmacion: Optional[str] = None


# ============================================================================
# RECETAS - PRODUCCION
# ============================================================================


class ProduccionRequest(BaseModel):
    cantidad: Decimal = Field(..., gt=0, description="Cantidad de lotes a producir")
    observaciones: Optional[str] = None


class ProduccionResponse(BaseModel):
    receta_id: str
    receta_nombre: str
    producto_resultado_id: str
    cantidad_producida: Decimal
    costo_ingredientes: Decimal
    costo_mano_obra: Decimal
    costo_indirecto: Decimal
    costo_total: Decimal
    costo_unitario: Decimal
    documento_referencia: str
    movimiento_id: str


# ============================================================================
# SOCIA — COSTOS INDIRECTOS
# ============================================================================


class CostoIndirectoCreate(BaseModel):
    nombre: str = Field(..., max_length=150, description="Ej: Empaque, Gas, Arrendamiento")
    monto: Decimal = Field(..., ge=0, description="COP por unidad (FIJO) o % del costo base (PORCENTAJE)")
    tipo: str = Field(..., description="FIJO o PORCENTAJE")

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v: str) -> str:
        if v not in ("FIJO", "PORCENTAJE"):
            raise ValueError("tipo debe ser FIJO o PORCENTAJE")
        return v


class CostoIndirectoUpdate(BaseModel):
    nombre: Optional[str] = None
    monto: Optional[Decimal] = Field(None, ge=0)
    tipo: Optional[str] = None
    activo: Optional[bool] = None

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("FIJO", "PORCENTAJE"):
            raise ValueError("tipo debe ser FIJO o PORCENTAJE")
        return v


class CostoIndirectoResponse(BaseModel):
    id: UUID
    nombre: str
    monto: Decimal
    tipo: str
    activo: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CostoIndirectoDetalle(BaseModel):
    """Detalle de un costo indirecto aplicado en un cálculo."""

    id: str
    nombre: str
    tipo: str
    monto_configurado: Decimal
    monto_aplicado: Decimal


# ============================================================================
# SOCIA — ANÁLISIS CVU / PRECIOS
# ============================================================================


class CVURequest(BaseModel):
    receta_id: UUID
    precio_venta: Decimal = Field(gt=0, description="Precio de venta unitario en COP")
    costos_fijos_periodo: Decimal = Field(ge=0, description="Costos fijos totales del periodo (ej: mes)")
    volumen_esperado: int = Field(gt=0, description="Unidades esperadas a producir/vender en el periodo")


class CVUResponse(BaseModel):
    receta_nombre: str
    costo_variable_unitario: Decimal
    margen_contribucion_unitario: Decimal
    ratio_margen_contribucion: Decimal
    punto_equilibrio_unidades: Decimal
    punto_equilibrio_ingresos: Decimal
    margen_seguridad_unidades: Decimal
    margen_seguridad_porcentaje: Decimal
    utilidad_esperada: Decimal


class VariacionSensibilidad(BaseModel):
    variable: str = Field(..., description="precio_venta | mano_obra | ingrediente | costos_fijos | volumen")
    ingrediente_id: Optional[UUID] = None
    delta_porcentaje: Decimal = Field(..., description="Ej: 20 = +20%, -10 = -10%")


class SensibilidadRequest(BaseModel):
    receta_id: UUID
    precio_venta: Decimal = Field(gt=0)
    costos_fijos: Decimal = Field(ge=0)
    volumen_base: int = Field(gt=0)
    variaciones: List[VariacionSensibilidad]


class SensibilidadResultado(BaseModel):
    variable: str
    delta_porcentaje: Decimal
    nuevo_pe_unidades: Decimal
    nuevo_pe_ingresos: Decimal
    nueva_utilidad: Decimal
    impacto_pe_porcentaje: Decimal


class SensibilidadResponse(BaseModel):
    receta_nombre: str
    pe_base_unidades: Decimal
    pe_base_ingresos: Decimal
    utilidad_base: Decimal
    resultados: List[SensibilidadResultado]


class EscenarioPrecioCompleto(BaseModel):
    nombre: str
    precio: Decimal
    margen_porcentaje: Decimal
    margen_contribucion: Decimal
    punto_equilibrio_unidades: Decimal
    viabilidad: str  # VIABLE | CRITICO | NO_VIABLE


class EscenariosRequest(BaseModel):
    receta_id: UUID
    costos_fijos: Decimal = Field(ge=0)
    volumen: int = Field(gt=0)
    precio_mercado_referencia: Optional[Decimal] = Field(None, gt=0)


class EscenariosResponse(BaseModel):
    receta_nombre: str
    costo_variable_unitario: Decimal
    escenarios: List[EscenarioPrecioCompleto]


class RentabilidadItem(BaseModel):
    receta_id: str
    receta_nombre: str
    costo_unitario: Decimal
    precio_venta: Decimal
    margen_contribucion: Decimal
    margen_porcentaje: Decimal
    tiempo_produccion_minutos: int
    mc_por_minuto: Optional[Decimal] = None


class EscalaLote(BaseModel):
    lote: int
    costo_unitario: Decimal
    ahorro_vs_lote_1: Decimal


class EconomiaEscalaRequest(BaseModel):
    receta_id: UUID
    costos_fijos_setup: Decimal = Field(ge=0, description="Costo fijo de preparación/setup por lote")
    lotes: List[int] = Field(default=[1, 5, 10, 20, 50], description="Tamaños de lote a evaluar")


class EconomiaEscalaResponse(BaseModel):
    receta_nombre: str
    costo_variable_unitario: Decimal
    escala: List[EscalaLote]


# ============================================================================
# SOCIA — PROGRESO Y LOGROS
# ============================================================================


class SociaLogroCreate(BaseModel):
    logro_id: str = Field(..., max_length=50)


class SociaLogroResponse(BaseModel):
    id: UUID
    logro_id: str
    desbloqueado_en: datetime
    nivel_actual: str

    model_config = ConfigDict(from_attributes=True)


class SociaProgresoResponse(BaseModel):
    nivel_actual: str
    logros: List[str]
    total_logros: int


# ============================================================================
# COTIZACIONES
# ============================================================================


class CotizacionesDetalleBase(BaseModel):
    producto_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., ge=0)
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Porcentaje de descuento (0-100)")
    porcentaje_iva: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)


class CotizacionesDetalleCreate(CotizacionesDetalleBase):
    pass


class CotizacionesDetalleResponse(CotizacionesDetalleBase):
    id: UUID
    cotizacion_id: UUID
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    subtotal: Decimal
    base_gravable: Decimal
    valor_iva: Decimal
    total_linea: Decimal
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="wrap")
    @classmethod
    def _add_producto_fields(cls, value, handler):
        result = handler(value)
        if hasattr(value, "producto") and value.producto:
            result.nombre = value.producto.nombre
            result.categoria = value.producto.categoria
        return result


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
    descuento_global: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
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
    descuento_global: Decimal = Decimal("0.00")
    observaciones: Optional[str] = None
    url_pdf: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    subtotal: Decimal
    total_descuento: Decimal
    total_iva: Decimal
    total_cotizacion: Decimal

    detalles: List[CotizacionesDetalleResponse] = []

    # Auditoría
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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


class ConfiguracionContableResponse(BaseModel):
    id: UUID
    concepto: str
    cuenta_debito_id: Optional[UUID] = None
    cuenta_credito_id: Optional[UUID] = None
    descripcion: Optional[str] = None
    cuenta_debito_codigo: Optional[str] = None
    cuenta_debito_nombre: Optional[str] = None
    cuenta_credito_codigo: Optional[str] = None
    cuenta_credito_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PERÍODOS CONTABLES
# ============================================================================


class PeriodoContableResponse(BaseModel):
    id: UUID
    anio: int
    mes: int
    estado: str
    fecha_cierre: Optional[datetime] = None
    total_asientos: int = 0
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
    cuenta_codigo: Optional[str] = None
    cuenta_nombre: Optional[str] = None
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
    tercero_id: Optional[UUID] = None
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
    periodo_id: Optional[UUID] = None
    tercero_id: Optional[UUID] = None
    tercero_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    detalles: List[DetalleAsientoResponse] = []

    # Auditoría
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    cartera_id: Optional[UUID] = None  # viene del path param, no requerido en body


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


# ============================================================================
# PLANES (Multi-Tenancy)
# ============================================================================


class PlanBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    precio_mensual: Decimal = Field(default=Decimal("0.00"), ge=0)
    precio_anual: Optional[Decimal] = Field(None, ge=0)
    max_usuarios: int = Field(default=3, ge=1)
    max_productos: int = Field(default=100, ge=1)
    max_facturas_mes: int = Field(default=100, ge=1)
    max_storage_mb: int = Field(default=500, ge=1)
    esta_activo: bool = True
    es_default: bool = False


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio_mensual: Optional[Decimal] = None
    precio_anual: Optional[Decimal] = None
    max_usuarios: Optional[int] = None
    max_productos: Optional[int] = None
    max_facturas_mes: Optional[int] = None
    max_storage_mb: Optional[int] = None
    esta_activo: Optional[bool] = None


class PlanResponse(PlanBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PlanWithStats(PlanResponse):
    """Plan con estadísticas de uso."""

    tenant_count: int = 0


# ============================================================================
# TENANTS (Multi-Tenancy)
# ============================================================================


class TenantBase(BaseModel):
    nombre: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9-]+$")
    nit: Optional[str] = Field(None, max_length=50)
    email_contacto: EmailStr
    telefono: Optional[str] = Field(None, max_length=50)
    direccion: Optional[str] = None
    ciudad: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    url_logo: Optional[str] = None
    color_primario: str = Field(default="#1976D2", max_length=20)
    color_secundario: str = Field(default="#424242", max_length=20)


class TenantCreate(TenantBase):
    """Schema para crear un nuevo tenant (onboarding)"""

    plan_id: UUID
    # Datos del admin inicial
    admin_nombre: str = Field(..., max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)


class TenantUpdate(BaseModel):
    nombre: Optional[str] = None
    nit: Optional[str] = None
    email_contacto: Optional[EmailStr] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    url_logo: Optional[str] = None
    color_primario: Optional[str] = None
    color_secundario: Optional[str] = None


class TenantResponse(TenantBase):
    id: UUID
    plan_id: UUID
    estado: str
    fecha_inicio_suscripcion: Optional[datetime] = None
    fecha_fin_suscripcion: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TenantBriefResponse(BaseModel):
    """Respuesta simplificada de tenant para listados"""

    id: UUID
    nombre: str
    slug: str
    estado: str
    url_logo: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# USUARIOS-TENANTS (Multi-Tenancy)
# ============================================================================


class UsuarioTenantBase(BaseModel):
    rol: str = Field(default="operador", pattern="^(admin|operador|contador|vendedor|readonly)$")
    esta_activo: bool = True
    es_default: bool = False


class UsuarioTenantCreate(UsuarioTenantBase):
    usuario_id: UUID
    tenant_id: UUID


class UsuarioTenantUpdate(BaseModel):
    rol: Optional[str] = None
    esta_activo: Optional[bool] = None
    es_default: Optional[bool] = None


class UsuarioTenantResponse(UsuarioTenantBase):
    id: UUID
    usuario_id: UUID
    tenant_id: UUID
    fecha_ingreso: datetime
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AUTENTICACIÓN CON MULTI-TENANT
# ============================================================================


class TenantSelectionRequest(BaseModel):
    """Request para seleccionar un tenant después del login"""

    tenant_id: UUID


class TokenWithTenants(BaseModel):
    """Respuesta de login con lista de tenants disponibles"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UsuarioResponse"
    tenants: List[TenantBriefResponse] = []


class TokenWithTenant(BaseModel):
    """Respuesta después de seleccionar un tenant"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UsuarioResponse"
    tenant: TenantBriefResponse
    rol_en_tenant: str


# ============================================================================
# REGISTRO DE TENANT (Onboarding)
# ============================================================================


class TenantRegisterRequest(BaseModel):
    """Request para registrar un nuevo tenant y su admin"""

    # Datos del tenant
    nombre_empresa: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9-]+$")
    nit: Optional[str] = Field(None, max_length=50)
    email_empresa: EmailStr
    telefono: Optional[str] = Field(None, max_length=50)
    ciudad: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)

    # Datos del admin
    admin_nombre: str = Field(..., max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)

    # Plan (opcional, usa default si no se especifica)
    plan_id: Optional[UUID] = None


class TenantRegisterResponse(BaseModel):
    """Respuesta del registro de tenant"""

    tenant: TenantResponse
    user: UsuarioResponse
    message: str = "Tenant registrado exitosamente"


class TenantRegisterWithClerkRequest(BaseModel):
    """Request para registrar un tenant con usuario ya autenticado via Clerk"""

    nombre_empresa: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9-]+$")
    nit: Optional[str] = Field(None, max_length=50)
    email_empresa: EmailStr
    telefono: Optional[str] = Field(None, max_length=50)
    ciudad: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    plan_id: Optional[UUID] = None


# ============================================================================
# TENANT ACCIONES (Superadmin)
# ============================================================================


class TenantChangePlanRequest(BaseModel):
    """Request para cambiar el plan de un tenant."""

    plan_id: UUID


class TenantExtendTrialRequest(BaseModel):
    """Request para extender el periodo trial de un tenant."""

    dias_adicionales: int = Field(..., ge=1, le=90)


class TenantMetricas(BaseModel):
    """Métricas de uso de un tenant."""

    tenant_id: UUID
    usuarios_count: int = 0
    productos_count: int = 0
    facturas_mes_count: int = 0
    ventas_total_mes: float = 0.0
    terceros_count: int = 0
    max_usuarios: int = 0
    max_productos: int = 0
    max_facturas_mes: int = 0


class TenantPulse(BaseModel):
    """Health Score de un tenant para predecir churn."""

    tenant_id: UUID
    score: int = Field(..., ge=0, le=100)  # 0-100
    estado_salud: str  # 'saludable', 'en_riesgo', 'critico'
    logins_recientes: int = 0  # usuarios activos últimos 7 días
    ventas_mes: int = 0  # facturas/ventas último mes
    dias_activo: int = 0  # antigüedad del tenant
    calculado_en: datetime


class SaaSDashboardKPIs(BaseModel):
    """KPIs del dashboard SaaS para superadmin."""

    total_tenants: int = 0
    tenants_activos: int = 0
    tenants_trial: int = 0
    tenants_suspendidos: int = 0
    tenants_cancelados: int = 0
    mrr: float = 0.0
    nuevos_ultimos_30_dias: int = 0
    churn_rate: float = 0.0
    revenue_por_plan: list = []


class SuscripcionResponse(BaseModel):
    """Respuesta de suscripción."""

    id: UUID
    tenant_id: UUID
    plan_id: UUID
    periodo_inicio: datetime
    periodo_fin: datetime
    estado: str
    proveedor_pago: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PagoHistorialResponse(BaseModel):
    """Respuesta de historial de pagos."""

    id: UUID
    suscripcion_id: UUID
    monto: Decimal
    moneda: str = "COP"
    estado: str
    id_transaccion_externa: Optional[str] = None
    fecha_pago: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UsuarioTenantDetailResponse(BaseModel):
    """Respuesta de usuario en tenant con detalle de usuario."""

    id: UUID
    usuario_id: UUID
    tenant_id: UUID
    rol: str
    esta_activo: bool = True
    fecha_ingreso: datetime
    usuario_nombre: str = ""
    usuario_email: str = ""
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AUDIT LOGS
# ============================================================================


class AuditLogResponse(BaseModel):
    """Respuesta de un registro de auditoría."""

    id: UUID
    actor_id: Optional[UUID] = None
    actor_email: str
    tenant_id: Optional[UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[UUID] = None
    changes: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Respuesta paginada de audit logs."""

    items: List[AuditLogResponse]
    total: int
    page: int
    limit: int


# ============================================================================
# GHOST MODE (IMPERSONACIÓN)
# ============================================================================


class ImpersonationResponse(BaseModel):
    """Respuesta al impersonar un usuario. Token de corta duración (15 min)."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutos
    impersonated_user: "UsuarioResponse"
    tenant_id: UUID
    rol_en_tenant: str


# ============================================================================
# USER GOVERNANCE (GOD MODE)
# ============================================================================


class GlobalUserCreate(BaseModel):
    """Crear usuario global sin asociación a tenant."""

    nombre: str = Field(..., max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    rol: str = Field(default="operador", pattern="^(admin|operador|contador|vendedor|readonly)$")
    estado: bool = True


class GlobalUserUpdate(BaseModel):
    """Actualizar datos globales de un usuario."""

    nombre: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    rol: Optional[str] = Field(None, pattern="^(admin|operador|contador|vendedor|readonly)$")
    estado: Optional[bool] = None


class GlobalUserResponse(UsuarioResponse):
    """Usuario global con count de tenants."""

    tenant_count: int = 0


class GlobalUserListResponse(BaseModel):
    """Respuesta paginada de usuarios globales."""

    items: List[GlobalUserResponse]
    total: int
    page: int
    limit: int


class ForcePasswordRequest(BaseModel):
    """Request para forzar reset de contraseña (superadmin)."""

    new_password: str = Field(..., min_length=8, description="Nueva contraseña (mínimo 8 caracteres)")


# ============================================================================
# CRM SCHEMAS
# ============================================================================


# Pipelines
class CrmPipelineBase(BaseModel):
    """Base schema para CRM Pipeline."""

    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    es_default: bool = False
    color: str = Field(default="#3B82F6", max_length=7)


class CrmPipelineCreate(CrmPipelineBase):
    """Schema para crear Pipeline."""

    pass


class CrmPipelineUpdate(BaseModel):
    """Schema para actualizar Pipeline."""

    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7)


class CrmStageBase(BaseModel):
    """Base schema para CRM Stage."""

    nombre: str = Field(..., max_length=100)
    orden: int
    probabilidad: int = Field(default=10, ge=0, le=100)


class CrmStageResponse(CrmStageBase):
    """Schema de respuesta para Stage."""

    id: UUID
    pipeline_id: UUID
    requiere_motivo_perdida: bool = False
    dias_estancamiento_alerta: int = 0
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CrmPipelineResponse(CrmPipelineBase):
    """Schema de respuesta para Pipeline con stages."""

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    etapas: List[CrmStageResponse] = []
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Stages
class CrmStageCreate(CrmStageBase):
    """Schema para crear Stage."""

    pipeline_id: UUID


# Deals
class CrmDealBase(BaseModel):
    """Base schema para CRM Deal."""

    nombre: str = Field(..., max_length=200)
    tercero_id: UUID
    valor_estimado: Decimal = Field(default=Decimal("0"), decimal_places=2)
    fecha_cierre_estimada: Optional[date] = None
    origen: Optional[str] = Field(None, max_length=100)


class CrmDealCreate(CrmDealBase):
    """Schema para crear Deal."""

    pipeline_id: UUID
    stage_id: UUID
    usuario_id: Optional[UUID] = None


class CrmDealUpdate(BaseModel):
    """Schema para actualizar Deal."""

    nombre: Optional[str] = Field(None, max_length=200)
    valor_estimado: Optional[Decimal] = None
    fecha_cierre_estimada: Optional[date] = None
    usuario_id: Optional[UUID] = None


class CrmDealResponse(CrmDealBase):
    """Schema de respuesta para Deal."""

    id: UUID
    stage_id: UUID
    pipeline_id: UUID
    usuario_id: Optional[UUID] = None
    estado_cierre: str
    moneda: str = "COP"
    created_at: datetime
    updated_at: datetime
    fecha_ultimo_contacto: Optional[datetime] = None
    # Campos computados (populate desde service)
    tercero_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None
    stage_nombre: Optional[str] = None
    # Auditoría
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CrmDealMoveRequest(BaseModel):
    """Request para mover deal a otro stage."""

    stage_id: UUID


class CrmDealCloseRequest(BaseModel):
    """Request para cerrar deal."""

    estado_cierre: str = Field(..., pattern="^(GANADO|PERDIDO|ABANDONADO)$")
    motivo: Optional[str] = None


# Activities
class CrmActivityCreate(BaseModel):
    """Schema para crear Activity."""

    deal_id: UUID
    tipo: str = Field(..., pattern="^(NOTA|LLAMADA|EMAIL|REUNION|WHATSAPP|TAREA)$")
    asunto: Optional[str] = Field(None, max_length=200)
    contenido: Optional[str] = None
    fecha_actividad: Optional[datetime] = None
    duracion_minutos: int = Field(default=0, ge=0)

    @field_validator("fecha_actividad", mode="before")
    @classmethod
    def set_default_fecha(cls, v):
        return v or datetime.now(timezone.utc)


class CrmActivityResponse(BaseModel):
    """Schema de respuesta para Activity."""

    id: UUID
    deal_id: UUID
    usuario_id: Optional[UUID] = None
    tipo: str
    asunto: Optional[str] = None
    contenido: Optional[str] = None
    fecha_actividad: datetime
    duracion_minutos: int = 0
    es_automatica: bool = False
    created_at: datetime
    updated_at: datetime
    # Campo computado
    usuario_nombre: Optional[str] = None
    # Auditoría
    created_by: Optional[UsuarioMini] = Field(None, validation_alias="created_by_user")
    updated_by: Optional[UsuarioMini] = Field(None, validation_alias="updated_by_user")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============================================================================
# PQRS (Soporte / Tickets)
# ============================================================================


class TicketPQRSCreate(BaseModel):
    """Request para crear un ticket PQRS"""

    tipo: str = Field(default="SOPORTE", description="PETICION|QUEJA|RECLAMO|SUGERENCIA|SOPORTE")
    asunto: str = Field(..., max_length=300)
    descripcion: str = Field(..., min_length=10)
    prioridad: str = Field(default="MEDIA", description="BAJA|MEDIA|ALTA|CRITICA")


class TicketPQRSUpdate(BaseModel):
    """Request para actualizar un ticket (admin)"""

    estado: Optional[str] = Field(None, description="ABIERTO|EN_PROCESO|RESUELTO|CERRADO")
    prioridad: Optional[str] = Field(None, description="BAJA|MEDIA|ALTA|CRITICA")


class RespuestaTicket(BaseModel):
    """Request para agregar una respuesta a un ticket"""

    contenido: str = Field(..., min_length=1)


class TicketPQRSResponse(BaseModel):
    """Response de un ticket PQRS"""

    id: UUID
    tipo: str
    asunto: str
    descripcion: str
    estado: str
    prioridad: str
    usuario_id: Optional[UUID] = None
    respuestas: Optional[list] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketPQRSAdminResponse(TicketPQRSResponse):
    """Response de ticket PQRS para superadmin — incluye tenant_id."""

    tenant_id: Optional[UUID] = None


# ============================================================================
# CALIFICACIONES
# ============================================================================


class CalificacionCreate(BaseModel):
    """Request para crear o actualizar la calificación del tenant."""

    estrellas: int = Field(..., ge=1, le=5, description="Calificación de 1 a 5 estrellas")
    titulo: Optional[str] = Field(None, max_length=200)
    comentario: Optional[str] = None


class CalificacionResponse(BaseModel):
    """Response de una calificación."""

    id: UUID
    tenant_id: UUID
    estrellas: int
    titulo: Optional[str] = None
    comentario: Optional[str] = None
    estado: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CalificacionPublicaResponse(BaseModel):
    """Para la landing page — sin datos sensibles de tenant."""

    estrellas: int
    titulo: Optional[str] = None
    comentario: Optional[str] = None
    nombre_empresa: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalificacionModerarRequest(BaseModel):
    """Request para moderar una calificación (superadmin)."""

    nuevo_estado: str = Field(..., pattern="^(aprobada|rechazada)$")
