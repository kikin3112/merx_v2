"""
Mixins reutilizables para modelos SQLAlchemy.
Proporcionan campos comunes para multi-tenancy, auditoría y soft deletes.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, TypeDecorator, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr, relationship


class UTCDateTime(TypeDecorator):
    """
    DateTime que garantiza que los valores cargados desde la DB tengan
    siempre tzinfo=UTC, independientemente del comportamiento del driver.

    Esto evita el bug donde psycopg2 retorna datetimes naive para columnas
    TIMESTAMPTZ y el frontend los interpreta como hora local en vez de UTC.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class TenantMixin:
    """
    Mixin para agregar tenant_id a modelos de negocio.
    Habilita aislamiento multi-tenant via RLS en PostgreSQL.

    Uso:
        class Productos(Base, TenantMixin):
            __tablename__ = "productos"
            ...

    El tenant_id se usará automáticamente con RLS para filtrar
    registros por tenant.
    """

    @declared_attr
    def tenant_id(self):
        return Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)


class SoftDeleteMixin:
    """
    Mixin para soft deletes.
    Los registros no se eliminan físicamente, se marcan con timestamp.

    Uso:
        # Eliminar registro
        registro.soft_delete(user_id=current_user.id)
        db.commit()

        # Filtrar registros activos
        db.query(Modelo).filter(Modelo.deleted_at == None)
    """

    @declared_attr
    def deleted_at(self):
        return Column(UTCDateTime, nullable=True, index=True)

    @declared_attr
    def deleted_by(self):
        return Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    @property
    def is_deleted(self) -> bool:
        """Verifica si el registro está eliminado."""
        return self.deleted_at is not None

    def soft_delete(self, user_id=None):
        """
        Marca el registro como eliminado.

        Args:
            user_id: UUID del usuario que realiza la eliminación
        """
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = user_id

    def restore(self):
        """Restaura un registro eliminado."""
        self.deleted_at = None
        self.deleted_by = None


class AuditMixin:
    """
    Mixin para campos de auditoría.
    Rastrea quién y cuándo creó/modificó el registro.
    """

    @declared_attr
    def created_at(self):
        return Column(UTCDateTime, server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(self):
        return Column(UTCDateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    @declared_attr
    def created_by(self):
        return Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    @declared_attr
    def updated_by(self):
        return Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    @declared_attr
    def created_by_user(self):
        """Relación con el usuario creador (para eager loading)"""
        return relationship(
            "Usuarios",
            foreign_keys=f"[{self.__name__}.created_by]",
            lazy="noload",  # Requiere eager loading explícito
        )

    @declared_attr
    def updated_by_user(self):
        """Relación con el usuario que hizo la última modificación"""
        return relationship(
            "Usuarios",
            foreign_keys=f"[{self.__name__}.updated_by]",
            lazy="noload",  # Requiere eager loading explícito
        )


class TenantAuditMixin(TenantMixin, SoftDeleteMixin, AuditMixin):
    """
    Mixin combinado para modelos de negocio multi-tenant.
    Incluye: tenant_id, soft delete, auditoría completa.

    Uso:
        class Productos(Base, TenantAuditMixin):
            __tablename__ = "productos"
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
            nombre = Column(String(200), nullable=False)
            ...

    Campos agregados automáticamente:
        - tenant_id: UUID del tenant (con FK e índice)
        - deleted_at: Timestamp de eliminación (soft delete)
        - deleted_by: Usuario que eliminó
        - created_at: Timestamp de creación
        - updated_at: Timestamp de última modificación
        - created_by: Usuario que creó
        - updated_by: Usuario que modificó
    """

    pass


class TenantSoftDeleteMixin(TenantMixin, SoftDeleteMixin):
    """
    Mixin para modelos que solo necesitan tenant + soft delete.
    Sin campos de auditoría de usuario (created_by, updated_by).
    """

    pass
