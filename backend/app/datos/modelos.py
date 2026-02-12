import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Numeric,
    DateTime, Date, Text, CheckConstraint, Index, func, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property

from .db import Base
from .mixins import TenantMixin, SoftDeleteMixin


# ============================================================================
# ENUMS PARA ESTADOS
# ============================================================================

class EstadoVenta(str, PyEnum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    ANULADA = "ANULADA"
    FACTURADA = "FACTURADA"


class EstadoCompra(str, PyEnum):
    PENDIENTE = "PENDIENTE"
    RECIBIDA = "RECIBIDA"
    ANULADA = "ANULADA"


class EstadoOrdenProduccion(str, PyEnum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    ANULADA = "ANULADA"


class TipoMovimiento(str, PyEnum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"
    PRODUCCION = "PRODUCCION"
    DEVOLUCION = "DEVOLUCION"


# ============================================================================
# MODELO: Usuarios
# ============================================================================

class Usuarios(Base):
    """
    Usuarios del sistema (tabla global, sin RLS).
    Un usuario puede pertenecer a múltiples tenants via UsuariosTenants.
    """
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False, default="operador")  # Rol global
    estado = Column(Boolean, default=True, nullable=False)
    es_superadmin = Column(Boolean, default=False, nullable=False)  # SuperAdmin del sistema
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relación con tenants
    tenants = relationship(
        "UsuariosTenants",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "rol IN ('superadmin', 'admin', 'operador', 'contador')",
            name="check_rol_valido"
        ),
    )


# ============================================================================
# MODELO: Terceros
# ============================================================================

class Terceros(TenantMixin, SoftDeleteMixin, Base):
    """
    Clientes, proveedores y otros terceros.
    Modelo con multi-tenancy y soft delete.
    """
    __tablename__ = "terceros"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_documento = Column(String(20), nullable=False)
    numero_documento = Column(String(50), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    tipo_tercero = Column(String(20), nullable=False)
    direccion = Column(String(200))
    telefono = Column(String(50))
    email = Column(String(100))
    estado = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    ventas = relationship("Ventas", back_populates="tercero")
    compras = relationship("Compras", back_populates="tercero")

    __table_args__ = (
        CheckConstraint(
            "tipo_documento IN ('CC', 'NIT', 'CE', 'PAS', 'TI')",
            name="check_tipo_documento_valido"
        ),
        CheckConstraint(
            "tipo_tercero IN ('CLIENTE', 'PROVEEDOR', 'AMBOS')",
            name="check_tipo_tercero_valido"
        ),
        # Número de documento único por tenant
        Index('idx_terceros_tenant_documento', 'tenant_id', 'numero_documento', unique=True),
    )


# ============================================================================
# MODELO: Productos
# ============================================================================

class Productos(TenantMixin, SoftDeleteMixin, Base):
    """
    Productos e insumos del inventario.
    Modelo con multi-tenancy y soft delete.
    """
    __tablename__ = "productos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_interno = Column(String(50), nullable=False, index=True)
    codigo_barras = Column(String(100), index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(50), nullable=False)
    unidad_medida = Column(String(20), nullable=False)
    maneja_inventario = Column(Boolean, default=True, nullable=False)
    porcentaje_iva = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    tipo_iva = Column(String(20), nullable=False, default="Excluido")
    precio_venta = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    stock_minimo = Column(Numeric(15, 2))
    stock_maximo = Column(Numeric(15, 2))
    estado = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    inventarios = relationship("Inventarios", back_populates="producto", uselist=False)
    movimientos = relationship("MovimientosInventario", back_populates="producto")
    recetas_como_resultado = relationship(
        "Recetas",
        foreign_keys="Recetas.producto_resultado_id",
        back_populates="producto_resultado"
    )

    __table_args__ = (
        CheckConstraint(
            "categoria IN ('Insumo', 'Producto_Propio', 'Producto_Tercero', 'Servicio')",
            name="check_categoria_valida"
        ),
        CheckConstraint(
            "unidad_medida IN ('UNIDAD', 'KILOGRAMO', 'GRAMO', 'LITRO', 'METRO', 'CAJA', 'SET')",
            name="check_unidad_medida_valida"
        ),
        CheckConstraint(
            "tipo_iva IN ('Excluido', 'Exento', 'Gravado')",
            name="check_tipo_iva_valido"
        ),
        CheckConstraint("precio_venta >= 0", name="check_precio_venta_positivo"),
        # Código interno único por tenant
        Index('idx_productos_tenant_codigo', 'tenant_id', 'codigo_interno', unique=True),
        # Código de barras único por tenant (si existe)
        Index('idx_productos_tenant_barras', 'tenant_id', 'codigo_barras', unique=True,
              postgresql_where=Column('codigo_barras').isnot(None)),
    )


# ============================================================================
# MODELO: Inventarios
# ============================================================================

class Inventarios(TenantMixin, Base):
    """
    Estado actual del inventario por producto.
    Modelo con multi-tenancy.
    """
    __tablename__ = "inventarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    cantidad_disponible = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    costo_promedio_ponderado = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    valor_total = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    producto = relationship("Productos", back_populates="inventarios")

    __table_args__ = (
        CheckConstraint("cantidad_disponible >= 0", name="check_cantidad_positiva"),
        CheckConstraint("costo_promedio_ponderado >= 0", name="check_costo_positivo"),
        CheckConstraint("valor_total >= 0", name="check_valor_positivo"),
        # Producto único por tenant
        Index('idx_inventarios_tenant_producto', 'tenant_id', 'producto_id', unique=True),
    )


# ============================================================================
# MODELO: MovimientosInventario
# ============================================================================

class MovimientosInventario(TenantMixin, Base):
    """
    Historial de movimientos de inventario.
    Modelo con multi-tenancy.
    """
    __tablename__ = "movimientos_inventario"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    tipo_movimiento = Column(Enum(TipoMovimiento), nullable=False)
    cantidad = Column(Numeric(15, 2), nullable=False)
    costo_unitario = Column(Numeric(15, 2))
    valor_total = Column(Numeric(15, 2))
    documento_referencia = Column(String(100))
    observaciones = Column(Text)
    fecha_movimiento = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relaciones
    producto = relationship("Productos", back_populates="movimientos")

    __table_args__ = (
        Index('idx_movimientos_tenant_producto_fecha', 'tenant_id', 'producto_id', 'fecha_movimiento'),
        CheckConstraint("cantidad != 0", name="check_cantidad_no_cero"),
    )


# ============================================================================
# MODELO: Ventas
# ============================================================================

class Ventas(TenantMixin, SoftDeleteMixin, Base):
    """
    Ventas realizadas.
    Modelo con multi-tenancy y soft delete.
    """
    __tablename__ = "ventas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_venta = Column(String(50), nullable=False, index=True)
    tercero_id = Column(UUID(as_uuid=True), ForeignKey("terceros.id", ondelete="RESTRICT"), nullable=False)
    fecha_venta = Column(Date, nullable=False, index=True)
    estado = Column(Enum(EstadoVenta), nullable=False, default=EstadoVenta.PENDIENTE)
    descuento_global = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    observaciones = Column(Text)
    url_pdf = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    tercero = relationship("Terceros", back_populates="ventas")
    detalles = relationship("VentasDetalle", back_populates="venta", cascade="all, delete-orphan")

    # Propiedades calculadas
    @hybrid_property
    def subtotal(self) -> Decimal:
        """Suma de (cantidad * precio_unitario) de todos los detalles"""
        if not self.detalles:
            return Decimal("0.00")
        return sum(
            (detalle.cantidad * detalle.precio_unitario)
            for detalle in self.detalles
        )

    @hybrid_property
    def total_descuento(self) -> Decimal:
        """Descuentos de lineas + descuento global prorrateado"""
        if not self.detalles:
            return Decimal("0.00")
        desc_lineas = sum(detalle.monto_descuento for detalle in self.detalles)
        dg = self.descuento_global or Decimal("0")
        if dg == 0:
            return desc_lineas
        base = self.subtotal - desc_lineas
        desc_global = base * dg / Decimal("100")
        return desc_lineas + desc_global

    @hybrid_property
    def base_gravable(self) -> Decimal:
        """Subtotal menos todos los descuentos"""
        return self.subtotal - self.total_descuento

    @hybrid_property
    def total_iva(self) -> Decimal:
        """IVA de lineas, ajustado proporcionalmente por descuento global"""
        if not self.detalles:
            return Decimal("0.00")
        iva_lineas = sum(detalle.valor_iva for detalle in self.detalles)
        dg = self.descuento_global or Decimal("0")
        if dg == 0:
            return iva_lineas
        factor = (Decimal("100") - dg) / Decimal("100")
        return iva_lineas * factor

    @hybrid_property
    def total_venta(self) -> Decimal:
        """Base gravable + IVA"""
        return self.base_gravable + self.total_iva

    __table_args__ = (
        Index('idx_ventas_tenant_fecha_estado', 'tenant_id', 'fecha_venta', 'estado'),
        Index('idx_ventas_tenant_tercero', 'tenant_id', 'tercero_id'),
        # Número de venta único por tenant
        Index('idx_ventas_tenant_numero', 'tenant_id', 'numero_venta', unique=True),
    )


# ============================================================================
# MODELO: VentasDetalle
# ============================================================================

class VentasDetalle(TenantMixin, Base):
    """
    Detalles de ventas.
    Modelo con multi-tenancy.
    """
    __tablename__ = "ventas_detalle"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venta_id = Column(UUID(as_uuid=True), ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    cantidad = Column(Numeric(15, 2), nullable=False)
    precio_unitario = Column(Numeric(15, 2), nullable=False)
    descuento = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    porcentaje_iva = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))

    # Relaciones
    venta = relationship("Ventas", back_populates="detalles")
    producto = relationship("Productos")

    # Propiedades calculadas
    @hybrid_property
    def subtotal(self) -> Decimal:
        """Cantidad * Precio Unitario"""
        return self.cantidad * self.precio_unitario

    @hybrid_property
    def monto_descuento(self) -> Decimal:
        """Monto del descuento = subtotal * descuento% / 100"""
        return self.subtotal * self.descuento / Decimal("100")

    @hybrid_property
    def base_gravable(self) -> Decimal:
        """Subtotal - Monto Descuento"""
        return self.subtotal - self.monto_descuento

    @hybrid_property
    def valor_iva(self) -> Decimal:
        """Base Gravable * (Porcentaje IVA / 100)"""
        return self.base_gravable * (self.porcentaje_iva / Decimal("100"))

    @hybrid_property
    def total_linea(self) -> Decimal:
        """Base Gravable + IVA"""
        return self.base_gravable + self.valor_iva

    __table_args__ = (
        Index('idx_ventas_detalle_tenant_venta', 'tenant_id', 'venta_id'),
        Index('idx_ventas_detalle_tenant_producto', 'tenant_id', 'producto_id'),
        CheckConstraint("cantidad > 0", name="check_venta_cantidad_positiva"),
        CheckConstraint("precio_unitario >= 0", name="check_venta_precio_positivo"),
        CheckConstraint("descuento >= 0", name="check_venta_descuento_positivo"),
    )


# ============================================================================
# MODELO: Compras
# ============================================================================

class Compras(TenantMixin, SoftDeleteMixin, Base):
    """
    Compras realizadas a proveedores.
    Modelo con multi-tenancy y soft delete.
    """
    __tablename__ = "compras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_compra = Column(String(50), nullable=False, index=True)
    tercero_id = Column(UUID(as_uuid=True), ForeignKey("terceros.id", ondelete="RESTRICT"), nullable=False)
    fecha_compra = Column(Date, nullable=False, index=True)
    estado = Column(Enum(EstadoCompra), nullable=False, default=EstadoCompra.PENDIENTE)
    descuento_global = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    observaciones = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    tercero = relationship("Terceros", back_populates="compras")
    detalles = relationship("ComprasDetalle", back_populates="compra", cascade="all, delete-orphan")

    # Propiedades calculadas
    @hybrid_property
    def subtotal(self) -> Decimal:
        if not self.detalles:
            return Decimal("0.00")
        return sum((d.cantidad * d.precio_unitario) for d in self.detalles)

    @hybrid_property
    def total_descuento(self) -> Decimal:
        if not self.detalles:
            return Decimal("0.00")
        desc_lineas = sum(d.monto_descuento for d in self.detalles)
        dg = self.descuento_global or Decimal("0")
        if dg == 0:
            return desc_lineas
        base = self.subtotal - desc_lineas
        return desc_lineas + base * dg / Decimal("100")

    @hybrid_property
    def base_gravable(self) -> Decimal:
        return self.subtotal - self.total_descuento

    @hybrid_property
    def total_iva(self) -> Decimal:
        if not self.detalles:
            return Decimal("0.00")
        iva_lineas = sum(d.valor_iva for d in self.detalles)
        dg = self.descuento_global or Decimal("0")
        if dg == 0:
            return iva_lineas
        factor = (Decimal("100") - dg) / Decimal("100")
        return iva_lineas * factor

    @hybrid_property
    def total_compra(self) -> Decimal:
        return self.base_gravable + self.total_iva

    __table_args__ = (
        Index('idx_compras_tenant_fecha_estado', 'tenant_id', 'fecha_compra', 'estado'),
        Index('idx_compras_tenant_tercero', 'tenant_id', 'tercero_id'),
        # Número de compra único por tenant
        Index('idx_compras_tenant_numero', 'tenant_id', 'numero_compra', unique=True),
    )


# ============================================================================
# MODELO: ComprasDetalle
# ============================================================================

class ComprasDetalle(TenantMixin, Base):
    """
    Detalles de compras.
    Modelo con multi-tenancy.
    """
    __tablename__ = "compras_detalle"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    compra_id = Column(UUID(as_uuid=True), ForeignKey("compras.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    cantidad = Column(Numeric(15, 2), nullable=False)
    precio_unitario = Column(Numeric(15, 2), nullable=False)
    descuento = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    porcentaje_iva = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))

    # Relaciones
    compra = relationship("Compras", back_populates="detalles")
    producto = relationship("Productos")

    # Propiedades calculadas
    @hybrid_property
    def subtotal(self) -> Decimal:
        """Cantidad * Precio Unitario"""
        return self.cantidad * self.precio_unitario

    @hybrid_property
    def monto_descuento(self) -> Decimal:
        """Monto del descuento = subtotal * descuento% / 100"""
        return self.subtotal * self.descuento / Decimal("100")

    @hybrid_property
    def base_gravable(self) -> Decimal:
        """Subtotal - Monto Descuento"""
        return self.subtotal - self.monto_descuento

    @hybrid_property
    def valor_iva(self) -> Decimal:
        """Base Gravable * (Porcentaje IVA / 100)"""
        return self.base_gravable * (self.porcentaje_iva / Decimal("100"))

    @hybrid_property
    def total_linea(self) -> Decimal:
        """Base Gravable + IVA"""
        return self.base_gravable + self.valor_iva

    __table_args__ = (
        Index('idx_compras_detalle_tenant_compra', 'tenant_id', 'compra_id'),
        Index('idx_compras_detalle_tenant_producto', 'tenant_id', 'producto_id'),
        CheckConstraint("cantidad > 0", name="check_compra_cantidad_positiva"),
        CheckConstraint("precio_unitario >= 0", name="check_compra_precio_positivo"),
        CheckConstraint("descuento >= 0", name="check_compra_descuento_positivo"),
    )


# ============================================================================
# MODELO: OrdenesProduccion
# ============================================================================

class OrdenesProduccion(TenantMixin, SoftDeleteMixin, Base):
    """
    Órdenes de producción.
    Modelo con multi-tenancy y soft delete.
    """
    __tablename__ = "ordenes_produccion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_orden = Column(String(50), nullable=False, index=True)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    cantidad_producir = Column(Numeric(15, 2), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin_estimada = Column(Date)
    fecha_fin_real = Column(Date)
    estado = Column(Enum(EstadoOrdenProduccion), nullable=False, default=EstadoOrdenProduccion.PENDIENTE)
    observaciones = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    producto = relationship("Productos")
    detalles = relationship("OrdenesProduccionDetalle", back_populates="orden", cascade="all, delete-orphan")

    # Propiedades calculadas
    @hybrid_property
    def costo_estimado(self) -> Decimal:
        """Suma del costo total de todos los insumos utilizados"""
        if not self.detalles:
            return Decimal("0.00")
        return sum(
            (detalle.cantidad_requerida * detalle.costo_unitario)
            for detalle in self.detalles
        )

    @hybrid_property
    def costo_unitario(self) -> Decimal:
        """Costo estimado dividido entre cantidad a producir"""
        if self.cantidad_producir == 0:
            return Decimal("0.00")
        return self.costo_estimado / self.cantidad_producir

    __table_args__ = (
        Index('idx_ordenes_tenant_fecha_estado', 'tenant_id', 'fecha_inicio', 'estado'),
        Index('idx_ordenes_tenant_producto', 'tenant_id', 'producto_id'),
        Index('idx_ordenes_tenant_numero', 'tenant_id', 'numero_orden', unique=True),
        CheckConstraint("cantidad_producir > 0", name="check_cantidad_producir_positiva"),
    )


# ============================================================================
# MODELO: OrdenesProduccionDetalle
# ============================================================================

class OrdenesProduccionDetalle(TenantMixin, Base):
    """
    Detalles de órdenes de producción.
    Modelo con multi-tenancy.
    """
    __tablename__ = "ordenes_produccion_detalle"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orden_id = Column(UUID(as_uuid=True), ForeignKey("ordenes_produccion.id", ondelete="CASCADE"), nullable=False)
    insumo_id = Column(UUID(as_uuid=True), ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    cantidad_requerida = Column(Numeric(15, 2), nullable=False)
    costo_unitario = Column(Numeric(15, 2), nullable=False)

    # Relaciones
    orden = relationship("OrdenesProduccion", back_populates="detalles")
    insumo = relationship("Productos")

    # Propiedades calculadas
    @hybrid_property
    def costo_total(self) -> Decimal:
        """Cantidad Requerida * Costo Unitario"""
        return self.cantidad_requerida * self.costo_unitario

    __table_args__ = (
        Index('idx_ordenes_detalle_tenant_orden', 'tenant_id', 'orden_id'),
        Index('idx_ordenes_detalle_tenant_insumo', 'tenant_id', 'insumo_id'),
        CheckConstraint("cantidad_requerida > 0", name="check_cantidad_requerida_positiva"),
        CheckConstraint("costo_unitario >= 0", name="check_costo_unitario_positivo"),
    )


# ============================================================================
# MODELO: Recetas (BOM - Bill of Materials para produccion de velas)
# ============================================================================

class Recetas(TenantMixin, SoftDeleteMixin, Base):
    """
    Recetas para produccion de velas.
    Define los ingredientes necesarios para producir un producto terminado.
    Modelo con multi-tenancy y soft delete.
    """
    __tablename__ = "recetas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    producto_resultado_id = Column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    cantidad_resultado = Column(Numeric(10, 2), nullable=False, default=Decimal("1.00"))
    costo_mano_obra = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tiempo_produccion_minutos = Column(Integer, default=0)
    estado = Column(Boolean, default=True, nullable=False)
    notas = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    producto_resultado = relationship("Productos", foreign_keys=[producto_resultado_id])
    ingredientes = relationship(
        "RecetasIngredientes",
        back_populates="receta",
        cascade="all, delete-orphan"
    )

    @hybrid_property
    def costo_ingredientes(self) -> Decimal:
        """Suma del costo de todos los ingredientes"""
        if not self.ingredientes:
            return Decimal("0.00")
        total = Decimal("0.00")
        for ing in self.ingredientes:
            if ing.producto and ing.producto.inventarios:
                costo_unitario = ing.producto.inventarios.costo_promedio_ponderado or Decimal("0.00")
                total += ing.cantidad * costo_unitario
        return total

    @hybrid_property
    def costo_total(self) -> Decimal:
        """Costo ingredientes + mano de obra"""
        return self.costo_ingredientes + self.costo_mano_obra

    @hybrid_property
    def costo_unitario(self) -> Decimal:
        """Costo total dividido entre cantidad resultado"""
        if self.cantidad_resultado == 0:
            return Decimal("0.00")
        return self.costo_total / self.cantidad_resultado

    __table_args__ = (
        CheckConstraint("cantidad_resultado > 0", name="check_receta_cantidad_positiva"),
        CheckConstraint("costo_mano_obra >= 0", name="check_receta_mano_obra_positiva"),
        # Nombre unico por tenant
        Index('idx_recetas_tenant_nombre', 'tenant_id', 'nombre', unique=True),
        Index('idx_recetas_tenant_producto', 'tenant_id', 'producto_resultado_id'),
    )


# ============================================================================
# MODELO: RecetasIngredientes
# ============================================================================

class RecetasIngredientes(Base):
    """
    Ingredientes de una receta.
    No tiene TenantMixin porque hereda el tenant de la receta padre.
    """
    __tablename__ = "recetas_ingredientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recetas.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    producto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    cantidad = Column(Numeric(10, 4), nullable=False)
    unidad = Column(String(20), nullable=False, default="UNIDAD")
    notas = Column(String(200))

    # Relaciones
    receta = relationship("Recetas", back_populates="ingredientes")
    producto = relationship("Productos")

    @hybrid_property
    def costo_linea(self) -> Decimal:
        """Costo del ingrediente (cantidad * costo promedio)"""
        if self.producto and self.producto.inventarios:
            costo_unitario = self.producto.inventarios.costo_promedio_ponderado or Decimal("0.00")
            return self.cantidad * costo_unitario
        return Decimal("0.00")

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="check_ingrediente_cantidad_positiva"),
        CheckConstraint(
            "unidad IN ('UNIDAD', 'GRAMO', 'KILOGRAMO', 'MILILITRO', 'LITRO', 'METRO', 'CENTIMETRO')",
            name="check_ingrediente_unidad_valida"
        ),
        # Un producto solo puede estar una vez por receta
        Index('idx_ingredientes_receta_producto', 'receta_id', 'producto_id', unique=True),
    )


# ============================================================================
# MODELO: Cotizaciones
# ============================================================================

class Cotizaciones(TenantMixin, SoftDeleteMixin, Base):
    """
    Cotizaciones a clientes.
    Modelo con multi-tenancy y soft delete.
    """
    __tablename__ = "cotizaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_cotizacion = Column(String(50), nullable=False, index=True)
    tercero_id = Column(UUID(as_uuid=True), ForeignKey("terceros.id", ondelete="RESTRICT"), nullable=False)
    fecha_cotizacion = Column(Date, nullable=False, index=True)
    fecha_vencimiento = Column(Date, nullable=False)
    estado = Column(String(50), nullable=False, default="VIGENTE")
    descuento_global = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    observaciones = Column(Text)
    url_pdf = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    tercero = relationship("Terceros")
    detalles = relationship("CotizacionesDetalle", back_populates="cotizacion", cascade="all, delete-orphan")

    # Propiedades calculadas
    @hybrid_property
    def subtotal(self) -> Decimal:
        if not self.detalles:
            return Decimal("0.00")
        return sum((d.cantidad * d.precio_unitario) for d in self.detalles)

    @hybrid_property
    def total_descuento(self) -> Decimal:
        if not self.detalles:
            return Decimal("0.00")
        desc_lineas = sum(d.monto_descuento for d in self.detalles)
        dg = self.descuento_global or Decimal("0")
        if dg == 0:
            return desc_lineas
        base = self.subtotal - desc_lineas
        return desc_lineas + base * dg / Decimal("100")

    @hybrid_property
    def total_iva(self) -> Decimal:
        if not self.detalles:
            return Decimal("0.00")
        iva_lineas = sum(d.valor_iva for d in self.detalles)
        dg = self.descuento_global or Decimal("0")
        if dg == 0:
            return iva_lineas
        factor = (Decimal("100") - dg) / Decimal("100")
        return iva_lineas * factor

    @hybrid_property
    def total_cotizacion(self) -> Decimal:
        return self.subtotal - self.total_descuento + self.total_iva

    __table_args__ = (
        Index('idx_cotizaciones_tenant_fecha', 'tenant_id', 'fecha_cotizacion'),
        Index('idx_cotizaciones_tenant_tercero', 'tenant_id', 'tercero_id'),
        Index('idx_cotizaciones_tenant_numero', 'tenant_id', 'numero_cotizacion', unique=True),
        CheckConstraint(
            "estado IN ('VIGENTE', 'VENCIDA', 'ACEPTADA', 'RECHAZADA')",
            name="check_estado_cotizacion_valido"
        ),
    )


# ============================================================================
# MODELO: CotizacionesDetalle
# ============================================================================

class CotizacionesDetalle(TenantMixin, Base):
    """
    Detalles de cotizaciones.
    Modelo con multi-tenancy.
    """
    __tablename__ = "cotizaciones_detalle"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cotizacion_id = Column(UUID(as_uuid=True), ForeignKey("cotizaciones.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    cantidad = Column(Numeric(15, 2), nullable=False)
    precio_unitario = Column(Numeric(15, 2), nullable=False)
    descuento = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    porcentaje_iva = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))

    # Relaciones
    cotizacion = relationship("Cotizaciones", back_populates="detalles")
    producto = relationship("Productos")

    # Propiedades calculadas
    @hybrid_property
    def subtotal(self) -> Decimal:
        return self.cantidad * self.precio_unitario

    @hybrid_property
    def monto_descuento(self) -> Decimal:
        """Monto del descuento = subtotal * descuento% / 100"""
        return self.subtotal * self.descuento / Decimal("100")

    @hybrid_property
    def base_gravable(self) -> Decimal:
        return self.subtotal - self.monto_descuento

    @hybrid_property
    def valor_iva(self) -> Decimal:
        return self.base_gravable * (self.porcentaje_iva / Decimal("100"))

    @hybrid_property
    def total_linea(self) -> Decimal:
        return self.base_gravable + self.valor_iva

    __table_args__ = (
        Index('idx_cotizaciones_detalle_tenant_cot', 'tenant_id', 'cotizacion_id'),
        Index('idx_cotizaciones_detalle_tenant_producto', 'tenant_id', 'producto_id'),
        CheckConstraint("cantidad > 0", name="check_cotizacion_cantidad_positiva"),
        CheckConstraint("precio_unitario >= 0", name="check_cotizacion_precio_positivo"),
    )


# ============================================================================
# MODELO: CuentasContables
# ============================================================================

class CuentasContables(TenantMixin, Base):
    """
    Plan de cuentas contables (PUC).
    Modelo con multi-tenancy.
    """
    __tablename__ = "cuentas_contables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(20), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    tipo_cuenta = Column(String(50), nullable=False)
    nivel = Column(Integer, nullable=False)
    cuenta_padre_id = Column(UUID(as_uuid=True), ForeignKey("cuentas_contables.id", ondelete="RESTRICT"))
    naturaleza = Column(String(20), nullable=False)
    acepta_movimiento = Column(Boolean, default=True, nullable=False)
    estado = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    subcuentas = relationship("CuentasContables", backref="cuenta_padre", remote_side=[id])

    __table_args__ = (
        CheckConstraint(
            "tipo_cuenta IN ('ACTIVO', 'PASIVO', 'PATRIMONIO', 'INGRESO', 'EGRESO', 'COSTOS')",
            name="check_tipo_cuenta_valido"
        ),
        CheckConstraint(
            "naturaleza IN ('DEBITO', 'CREDITO')",
            name="check_naturaleza_valida"
        ),
        CheckConstraint("nivel >= 1 AND nivel <= 6", name="check_nivel_valido"),
        # Código único por tenant
        Index('idx_cuentas_contables_tenant_codigo', 'tenant_id', 'codigo', unique=True),
    )


# ============================================================================
# MODELO: ConfiguracionContable
# ============================================================================

class ConfiguracionContable(TenantMixin, Base):
    """
    Configuración de cuentas contables por concepto.
    Modelo con multi-tenancy.
    """
    __tablename__ = "configuracion_contable"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concepto = Column(String(100), nullable=False, index=True)
    cuenta_debito_id = Column(UUID(as_uuid=True), ForeignKey("cuentas_contables.id", ondelete="RESTRICT"))
    cuenta_credito_id = Column(UUID(as_uuid=True), ForeignKey("cuentas_contables.id", ondelete="RESTRICT"))
    descripcion = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    cuenta_debito = relationship("CuentasContables", foreign_keys=[cuenta_debito_id])
    cuenta_credito = relationship("CuentasContables", foreign_keys=[cuenta_credito_id])

    __table_args__ = (
        # Concepto único por tenant
        Index('idx_config_contable_tenant_concepto', 'tenant_id', 'concepto', unique=True),
    )


# ============================================================================
# MODELO: AsientosContables
# ============================================================================

class AsientosContables(TenantMixin, Base):
    """
    Asientos contables del libro diario.
    Modelo con multi-tenancy.
    """
    __tablename__ = "asientos_contables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_asiento = Column(String(50), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    tipo_asiento = Column(String(50), nullable=False)
    concepto = Column(String(200), nullable=False)
    documento_referencia = Column(String(100))
    estado = Column(String(50), nullable=False, default="ACTIVO")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    detalles = relationship("DetallesAsiento", back_populates="asiento", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_asientos_tenant_fecha', 'tenant_id', 'fecha'),
        Index('idx_asientos_tenant_numero', 'tenant_id', 'numero_asiento', unique=True),
        CheckConstraint(
            "tipo_asiento IN ('VENTAS', 'COMPRAS', 'PRODUCCION', 'AJUSTE', 'NOMINA', 'OTRO')",
            name="check_tipo_asiento_valido"
        ),
        CheckConstraint(
            "estado IN ('ACTIVO', 'ANULADO')",
            name="check_estado_asiento_valido"
        ),
    )


# ============================================================================
# MODELO: DetallesAsiento
# ============================================================================

class DetallesAsiento(TenantMixin, Base):
    """
    Líneas de asientos contables.
    Modelo con multi-tenancy.
    """
    __tablename__ = "detalles_asiento"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asiento_id = Column(UUID(as_uuid=True), ForeignKey("asientos_contables.id", ondelete="CASCADE"), nullable=False)
    cuenta_id = Column(UUID(as_uuid=True), ForeignKey("cuentas_contables.id", ondelete="RESTRICT"), nullable=False)
    debito = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    credito = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    descripcion = Column(Text)

    # Relaciones
    asiento = relationship("AsientosContables", back_populates="detalles")
    cuenta = relationship("CuentasContables", lazy="joined")

    @hybrid_property
    def cuenta_codigo(self) -> str:
        return self.cuenta.codigo if self.cuenta else None

    @hybrid_property
    def cuenta_nombre(self) -> str:
        return self.cuenta.nombre if self.cuenta else None

    __table_args__ = (
        Index('idx_detalles_asiento_tenant_asiento', 'tenant_id', 'asiento_id'),
        Index('idx_detalles_asiento_tenant_cuenta', 'tenant_id', 'cuenta_id'),
        CheckConstraint("debito >= 0", name="check_debito_positivo"),
        CheckConstraint("credito >= 0", name="check_credito_positivo"),
        CheckConstraint(
            "(debito > 0 AND credito = 0) OR (debito = 0 AND credito > 0)",
            name="check_debito_o_credito"
        ),
    )


# ============================================================================
# MODELO: MediosPago
# ============================================================================

class MediosPago(TenantMixin, Base):
    """
    Medios de pago configurados.
    Modelo con multi-tenancy.
    """
    __tablename__ = "medios_pago"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    tipo = Column(String(50), nullable=False)
    requiere_referencia = Column(Boolean, default=False)
    estado = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('EFECTIVO', 'TRANSFERENCIA', 'CHEQUE', 'TARJETA_CREDITO', 'TARJETA_DEBITO', 'OTRO')",
            name="check_tipo_medio_pago_valido"
        ),
        # Nombre único por tenant
        Index('idx_medios_pago_tenant_nombre', 'tenant_id', 'nombre', unique=True),
    )


# ============================================================================
# MODELO: Cartera (Cuentas por Cobrar/Pagar)
# ============================================================================

class Cartera(TenantMixin, Base):
    """
    Cuentas por cobrar y por pagar.
    Modelo con multi-tenancy.
    """
    __tablename__ = "cartera"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_cartera = Column(String(20), nullable=False)
    documento_referencia = Column(String(100), nullable=False, index=True)
    tercero_id = Column(UUID(as_uuid=True), ForeignKey("terceros.id", ondelete="RESTRICT"), nullable=False)
    fecha_emision = Column(Date, nullable=False, index=True)
    fecha_vencimiento = Column(Date, nullable=False, index=True)
    valor_total = Column(Numeric(15, 2), nullable=False)
    saldo_pendiente = Column(Numeric(15, 2), nullable=False)
    estado = Column(String(50), nullable=False, default="PENDIENTE")
    observaciones = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    tercero = relationship("Terceros")
    pagos = relationship("PagosCartera", back_populates="cartera", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_cartera_tenant_tipo_estado', 'tenant_id', 'tipo_cartera', 'estado'),
        Index('idx_cartera_tenant_tercero', 'tenant_id', 'tercero_id'),
        Index('idx_cartera_tenant_documento', 'tenant_id', 'documento_referencia'),
        CheckConstraint(
            "tipo_cartera IN ('COBRAR', 'PAGAR')",
            name="check_tipo_cartera_valido"
        ),
        CheckConstraint(
            "estado IN ('PENDIENTE', 'PARCIAL', 'PAGADA', 'VENCIDA', 'ANULADA')",
            name="check_estado_cartera_valido"
        ),
        CheckConstraint("valor_total >= 0", name="check_valor_total_positivo"),
        CheckConstraint("saldo_pendiente >= 0", name="check_saldo_positivo"),
    )


# ============================================================================
# MODELO: PagosCartera
# ============================================================================

class PagosCartera(TenantMixin, Base):
    """
    Pagos aplicados a cartera.
    Modelo con multi-tenancy.
    """
    __tablename__ = "pagos_cartera"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cartera_id = Column(UUID(as_uuid=True), ForeignKey("cartera.id", ondelete="CASCADE"), nullable=False)
    fecha_pago = Column(Date, nullable=False, index=True)
    valor_pago = Column(Numeric(15, 2), nullable=False)
    medio_pago_id = Column(UUID(as_uuid=True), ForeignKey("medios_pago.id", ondelete="RESTRICT"), nullable=False)
    numero_referencia = Column(String(100))
    observaciones = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relaciones
    cartera = relationship("Cartera", back_populates="pagos")
    medio_pago = relationship("MediosPago")

    __table_args__ = (
        Index('idx_pagos_cartera_tenant_cartera', 'tenant_id', 'cartera_id'),
        Index('idx_pagos_cartera_tenant_fecha', 'tenant_id', 'fecha_pago'),
        CheckConstraint("valor_pago > 0", name="check_valor_pago_positivo"),
    )


# ============================================================================
# MODELO: Secuencias (Numeración automática)
# ============================================================================

class Secuencias(TenantMixin, Base):
    """
    Secuencias de numeración para documentos.
    Modelo con multi-tenancy.
    """
    __tablename__ = "secuencias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(50), nullable=False, index=True)
    prefijo = Column(String(20), nullable=False)
    siguiente_numero = Column(Integer, nullable=False, default=1)
    longitud_numero = Column(Integer, nullable=False, default=6)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("siguiente_numero >= 1", name="check_siguiente_numero_positivo"),
        CheckConstraint("longitud_numero >= 1 AND longitud_numero <= 10", name="check_longitud_valida"),
        # Nombre único por tenant
        Index('idx_secuencias_tenant_nombre', 'tenant_id', 'nombre', unique=True),
    )


# ============================================================================
# IMPORTACIÓN DE MODELOS TENANT (después de Usuarios para evitar circular imports)
# ============================================================================

# Agregar la relación de usuario a UsuariosTenants
from .modelos_tenant import UsuariosTenants

# Completar la relación bidireccional
UsuariosTenants.usuario = relationship("Usuarios", back_populates="tenants")