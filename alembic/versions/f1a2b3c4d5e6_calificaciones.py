"""calificaciones

Revision ID: f1a2b3c4d5e6
Revises: e5a6b7c8d9e0
Create Date: 2026-02-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "e5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calificaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("estrellas", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("nombre_empresa", sa.String(200), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_calificaciones_tenant", "calificaciones", ["tenant_id"])
    op.create_index("idx_calificaciones_estado", "calificaciones", ["estado"])
    op.create_index("idx_calificaciones_tenant_deleted", "calificaciones", ["tenant_id", "deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_calificaciones_tenant_deleted", table_name="calificaciones")
    op.drop_index("idx_calificaciones_estado", table_name="calificaciones")
    op.drop_index("idx_calificaciones_tenant", table_name="calificaciones")
    op.drop_table("calificaciones")
