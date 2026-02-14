import uuid
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Numeric,
    DateTime, Date, Text, CheckConstraint, Index, func, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .db import Base
from .mixins import TenantMixin, SoftDeleteMixin, TenantAuditMixin


# ============================================================================
# ENUMS CRM
# ============================================================================

class TipoActividadCRM(str, PyEnum):
    NOTA = "NOTA"
    LLAMADA = "LLAMADA"
    EMAIL = "EMAIL"
    REUNION = "REUNION"
    WHATSAPP = "WHATSAPP"
    TAREA = "TAREA"


class EstadoDeal(str, PyEnum):
    ABIERTO = "ABIERTO"
    GANADO = "GANADO"
    PERDIDO = "PERDIDO"
    ABANDONADO = "ABANDONADO"


# ============================================================================
# MODELO: Pipelines (Flujos de Venta)
# ============================================================================

class CrmPipeline(TenantAuditMixin, Base):
    """
    Define diferentes procesos de venta (ej: "Venta Nuevas Licencias", "Renovaciones").
    Modelo con multi-tenancy, soft delete y auditoría completa.
    """
    __tablename__ = "crm_pipelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    es_default = Column(Boolean, default=False, nullable=False)
    color = Column(String(7), default="#3B82F6")  # Hex color para UI
    
    configuracion = Column(Text)  # JSON string para configuraciones extra
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    etapas = relationship(
        "CrmStage", 
        back_populates="pipeline", 
        order_by="CrmStage.orden",
        cascade="all, delete-orphan"
    )
    deals = relationship("CrmDeal", back_populates="pipeline")

    __table_args__ = (
        Index('idx_crm_pipeline_tenant_default', 'tenant_id', 'es_default'),
    )


# ============================================================================
# MODELO: Stages (Etapas del Pipeline)
# ============================================================================

class CrmStage(TenantAuditMixin, Base):
    """
    Etapas específicas dentro de un Pipeline (ej: "Prospecto", "Calificado", "Propuesta").
    Modelo con multi-tenancy, soft delete y auditoría completa.
    """
    __tablename__ = "crm_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("crm_pipelines.id", ondelete="CASCADE"), nullable=False, index=True)
    
    nombre = Column(String(100), nullable=False)
    orden = Column(Integer, nullable=False, default=0)
    probabilidad = Column(Integer, default=10)  # Probabilidad de cierre % (0-100)
    
    # Metadata para automatización
    requiere_motivo_perdida = Column(Boolean, default=False)
    dias_estancamiento_alerta = Column(Integer, default=0)  # 0 = sin alerta
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    pipeline = relationship("CrmPipeline", back_populates="etapas")
    deals = relationship("CrmDeal", back_populates="stage")

    __table_args__ = (
        CheckConstraint("probabilidad >= 0 AND probabilidad <= 100", name="check_crm_stage_probabilidad"),
        Index('idx_crm_stage_pipeline_orden', 'pipeline_id', 'orden'),
    )


# ============================================================================
# MODELO: Deals (Oportunidades de Negocio)
# ============================================================================

class CrmDeal(TenantAuditMixin, Base):
    """
    El núcleo del CRM. Representa una oportunidad de negocio con un cliente.
    Se vincula al ERP a través de 'tercero_id'.
    Modelo con multi-tenancy, soft delete y auditoría completa.
    """
    __tablename__ = "crm_deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Vinculación con ERP y Proceso
    tercero_id = Column(UUID(as_uuid=True), ForeignKey("terceros.id", ondelete="RESTRICT"), nullable=False, index=True)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("crm_pipelines.id", ondelete="RESTRICT"), nullable=False)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("crm_stages.id", ondelete="RESTRICT"), nullable=False, index=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True) # Dueño del deal
    
    # Datos del Negocio
    nombre = Column(String(200), nullable=False) # Ej: "Licencia Enterprise 50 usuarios"
    valor_estimado = Column(Numeric(15, 2), default=Decimal("0.00"))
    moneda = Column(String(3), default="COP")
    
    fecha_cierre_estimada = Column(Date, nullable=True)
    estado_cierre = Column(Enum(EstadoDeal), default=EstadoDeal.ABIERTO, nullable=False)
    motivo_perdida = Column(Text, nullable=True)
    
    origen = Column(String(100)) # Marketing, Referido, Cold Call, etc.
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    fecha_ultimo_contacto = Column(DateTime, nullable=True)

    # Relaciones
    tercero = relationship("Terceros")
    usuario = relationship("Usuarios", foreign_keys=[usuario_id])
    pipeline = relationship("CrmPipeline", back_populates="deals")
    stage = relationship("CrmStage", back_populates="deals")
    actividades = relationship("CrmActivity", back_populates="deal", cascade="all, delete-orphan")
    
    # TODO: Relación futura con Cotizaciones del ERP
    # cotizaciones = relationship("Cotizaciones", back_populates="deal")

    __table_args__ = (
        Index('idx_crm_deals_tenant_stage', 'tenant_id', 'stage_id'),
        Index('idx_crm_deals_tenant_usuario', 'tenant_id', 'usuario_id'),
    )


# ============================================================================
# MODELO: Activities (Timeline / Feed)
# ============================================================================

class CrmActivity(TenantAuditMixin, Base):
    """
    Registro de interacciones (Llamadas, Notas, Emails).
    Fundamental para el historial "360" del cliente.
    Modelo con multi-tenancy, soft delete y auditoría completa.
    """
    __tablename__ = "crm_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("crm_deals.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True) # Quien realizó la actividad
    
    tipo = Column(Enum(TipoActividadCRM), nullable=False)
    asunto = Column(String(200), nullable=True)
    contenido = Column(Text, nullable=True) # Cuerpo del email, nota de reunión, etc.
    
    fecha_actividad = Column(DateTime, nullable=False, default=func.now())
    duracion_minutos = Column(Integer, default=0)
    
    # Metadata específica
    es_automatica = Column(Boolean, default=False) # Si fue generada por el sistema
    metadata_json = Column(Text, nullable=True) # Para guardar ID de email externo, etc.
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    deal = relationship("CrmDeal", back_populates="actividades")
    usuario = relationship("Usuarios", foreign_keys=[usuario_id])

    __table_args__ = (
        Index('idx_crm_activities_tenant_deal_fecha', 'tenant_id', 'deal_id', 'fecha_actividad'),
    )
