"""
Modelo de Calificaciones: rating 1-5 estrellas por tenant con moderación superadmin.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .db import Base
from .mixins import SoftDeleteMixin, TenantMixin


class Calificaciones(TenantMixin, SoftDeleteMixin, Base):
    """
    Calificación de 1-5 estrellas que un tenant hace sobre ChandeliERP.
    Solo una calificación activa por tenant (upsert).
    Estados: pendiente → aprobada | rechazada
    """

    __tablename__ = "calificaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    estrellas = Column(Integer, nullable=False)  # 1–5
    titulo = Column(String(200), nullable=True)
    comentario = Column(Text, nullable=True)
    # Nombre de la empresa al momento de la calificación (cacheado)
    nombre_empresa = Column(String(200), nullable=True)

    estado = Column(String(20), nullable=False, default="pendiente")  # pendiente|aprobada|rechazada

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relaciones
    usuario = relationship("Usuarios", foreign_keys=[usuario_id])

    __table_args__ = (
        Index("idx_calificaciones_tenant", "tenant_id"),
        Index("idx_calificaciones_estado", "estado"),
    )
