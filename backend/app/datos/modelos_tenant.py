"""
Modelos globales para Multi-Tenancy.
Estas tablas NO tienen RLS - son globales para toda la aplicación.
"""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .db import Base

# ============================================================================
# MODELO: Planes (Global - Sin RLS)
# ============================================================================


class Planes(Base):
    """
    Planes de suscripción SaaS.
    Tabla global sin RLS.
    """

    __tablename__ = "planes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    precio_mensual = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    precio_anual = Column(Numeric(12, 2), nullable=True)

    # Límites del plan
    max_usuarios = Column(Integer, nullable=False, default=3)
    max_productos = Column(Integer, nullable=False, default=100)
    max_facturas_mes = Column(Integer, nullable=False, default=100)
    max_storage_mb = Column(Integer, nullable=False, default=500)

    # Características como JSON para flexibilidad
    caracteristicas = Column(JSONB, nullable=True, default=dict)

    # Control
    esta_activo = Column(Boolean, default=True, nullable=False)
    es_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    tenants = relationship("Tenants", back_populates="plan")

    __table_args__ = (
        CheckConstraint("precio_mensual >= 0", name="check_precio_mensual_positivo"),
        CheckConstraint("max_usuarios >= 1", name="check_max_usuarios_minimo"),
    )


# ============================================================================
# MODELO: Tenants (Global - Sin RLS)
# ============================================================================


class Tenants(Base):
    """
    Empresas/Organizaciones (tenants) del sistema.
    Tabla global sin RLS.
    """

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identificación
    nombre = Column(String(200), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    nit = Column(String(50), nullable=True, unique=True)

    # Contacto
    email_contacto = Column(String(100), nullable=False)
    telefono = Column(String(50))
    direccion = Column(Text)
    ciudad = Column(String(100))
    departamento = Column(String(100))

    # Configuración visual
    url_logo = Column(Text)
    color_primario = Column(String(20), default="#1976D2")
    color_secundario = Column(String(20), default="#424242")

    # Plan y estado
    plan_id = Column(UUID(as_uuid=True), ForeignKey("planes.id", ondelete="RESTRICT"), nullable=False)
    estado = Column(String(50), nullable=False, default="activo")

    # Suscripción
    fecha_inicio_suscripcion = Column(DateTime, server_default=func.now())
    fecha_fin_suscripcion = Column(DateTime, nullable=True)
    dias_gracia = Column(Integer, default=5)

    # Configuración general (JSON flexible)
    configuracion = Column(JSONB, nullable=True, default=dict)

    # Auditoría
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    plan = relationship("Planes", back_populates="tenants")
    usuarios_tenants = relationship("UsuariosTenants", back_populates="tenant", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "estado IN ('activo', 'suspendido', 'cancelado', 'trial', 'pendiente')", name="check_estado_tenant_valido"
        ),
        Index("idx_tenants_estado", "estado"),
        Index("idx_tenants_plan", "plan_id"),
    )

    @property
    def esta_activo(self) -> bool:
        """Verifica si el tenant está operativo"""
        return self.estado in ("activo", "trial")


# ============================================================================
# MODELO: UsuariosTenants (Global - Sin RLS)
# ============================================================================


class UsuariosTenants(Base):
    """
    Relación muchos-a-muchos entre Usuarios y Tenants.
    Permite que un usuario pertenezca a múltiples organizaciones.
    Tabla global sin RLS.
    """

    __tablename__ = "usuarios_tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Rol dentro del tenant (puede ser diferente al rol global del usuario)
    rol = Column(String(50), nullable=False, default="operador")

    # Estado de la membresía
    esta_activo = Column(Boolean, default=True, nullable=False)

    # Tenant por defecto para el usuario
    es_default = Column(Boolean, default=False, nullable=False)

    # Fecha de ingreso al tenant
    fecha_ingreso = Column(DateTime, server_default=func.now(), nullable=False)

    # Auditoría
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    tenant = relationship("Tenants", back_populates="usuarios_tenants")
    # usuario se define en modelos.py para evitar import circular

    __table_args__ = (
        UniqueConstraint("usuario_id", "tenant_id", name="uq_usuario_tenant"),
        CheckConstraint(
            "rol IN ('admin', 'operador', 'contador', 'vendedor', 'readonly')", name="check_rol_tenant_valido"
        ),
        Index("idx_usuarios_tenants_usuario", "usuario_id"),
        Index("idx_usuarios_tenants_tenant", "tenant_id"),
    )


# ============================================================================
# MODELO: Suscripciones (Global - Sin RLS)
# ============================================================================


class Suscripciones(Base):
    """
    Historial de suscripciones de tenants.
    Permite tracking de cambios de plan y pagos.
    """

    __tablename__ = "suscripciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("planes.id", ondelete="RESTRICT"), nullable=False)

    # Período de suscripción
    periodo_inicio = Column(DateTime, nullable=False)
    periodo_fin = Column(DateTime, nullable=False)

    # Estado
    estado = Column(String(50), nullable=False, default="activo")

    # Integración pagos (Wompi u otro)
    proveedor_pago = Column(String(50), default="wompi")
    id_suscripcion_externa = Column(String(200), nullable=True)

    # Auditoría
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "estado IN ('activo', 'suspendido', 'cancelado', 'expirado', 'trial')",
            name="check_estado_suscripcion_valido",
        ),
        Index("idx_suscripciones_tenant_estado", "tenant_id", "estado"),
    )


# ============================================================================
# MODELO: HistorialPagos (Global - Sin RLS)
# ============================================================================


class HistorialPagos(Base):
    """
    Registro de pagos de suscripciones.
    """

    __tablename__ = "historial_pagos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    suscripcion_id = Column(
        UUID(as_uuid=True), ForeignKey("suscripciones.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Detalles del pago
    monto = Column(Numeric(12, 2), nullable=False)
    moneda = Column(String(10), default="COP", nullable=False)
    estado = Column(String(50), nullable=False, default="pendiente")

    # Referencia del proveedor de pagos
    id_transaccion_externa = Column(String(200), nullable=True, unique=True)
    firma_webhook = Column(Text, nullable=True)
    metadata_pago = Column(JSONB, nullable=True)

    # Fechas
    fecha_pago = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("monto > 0", name="check_monto_pago_positivo"),
        CheckConstraint(
            "estado IN ('pendiente', 'aprobado', 'rechazado', 'reembolsado')", name="check_estado_pago_valido"
        ),
    )


# ============================================================================
# MODELO: AuditLog (Global - Sin RLS)
# ============================================================================


class AuditLog(Base):
    """
    Registro inmutable de auditoría para acciones críticas del sistema.
    Tabla global sin RLS - los logs de superadmin no tienen tenant.
    NO se permite UPDATE ni DELETE a nivel de servicio.
    """

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Quién realizó la acción
    actor_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_email = Column(String(100), nullable=False)

    # Contexto de tenant (null para acciones globales/superadmin)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)

    # Qué se hizo
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=True)

    # Detalle de cambios (old/new values)
    changes = Column(JSONB, nullable=True)

    # Contexto de la petición
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamp inmutable
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_audit_logs_tenant_created", "tenant_id", "created_at"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_action", "action"),
    )
