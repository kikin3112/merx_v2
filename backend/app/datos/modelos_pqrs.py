import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .db import Base
from .mixins import TenantAuditMixin

# ============================================================================
# ENUMS PQRS
# ============================================================================


class TipoPQRS(str, PyEnum):
    PETICION = "PETICION"
    QUEJA = "QUEJA"
    RECLAMO = "RECLAMO"
    SUGERENCIA = "SUGERENCIA"
    SOPORTE = "SOPORTE"


class EstadoTicket(str, PyEnum):
    ABIERTO = "ABIERTO"
    EN_PROCESO = "EN_PROCESO"
    RESUELTO = "RESUELTO"
    CERRADO = "CERRADO"


class PrioridadTicket(str, PyEnum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


# ============================================================================
# MODELO: TicketsPQRS
# ============================================================================


class TicketsPQRS(TenantAuditMixin, Base):
    """
    Sistema de tickets PQRS (Peticiones, Quejas, Reclamos, Sugerencias, Soporte).
    Modelo con multi-tenancy, soft delete y auditoria completa.
    """

    __tablename__ = "tickets_pqrs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo = Column(Enum(TipoPQRS), nullable=False, default=TipoPQRS.SOPORTE)
    asunto = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=False)
    estado = Column(Enum(EstadoTicket), nullable=False, default=EstadoTicket.ABIERTO)
    prioridad = Column(Enum(PrioridadTicket), nullable=False, default=PrioridadTicket.MEDIA)

    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)

    # Respuestas como JSONB array: [{autor_id, autor_nombre, contenido, fecha}]
    respuestas = Column(JSONB, default=list)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    usuario = relationship("Usuarios", foreign_keys=[usuario_id])

    __table_args__ = (
        Index("idx_tickets_pqrs_tenant_estado", "tenant_id", "estado"),
        Index("idx_tickets_pqrs_tenant_usuario", "tenant_id", "usuario_id"),
        Index("idx_tickets_pqrs_tenant_tipo", "tenant_id", "tipo"),
    )
