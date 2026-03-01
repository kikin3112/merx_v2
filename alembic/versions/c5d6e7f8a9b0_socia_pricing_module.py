"""socia pricing module: costos_indirectos, socia_progress, margen_objetivo

Revision ID: c5d6e7f8a9b0
Revises: ff850d4bb783
Create Date: 2026-03-01 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5d6e7f8a9b0"
down_revision = ("f1a2b3c4d5e6", "a1b2c3d4e5f6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Costos Indirectos ──────────────────────────────────────────────────
    op.create_table(
        "costos_indirectos",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("monto", sa.Numeric(15, 2), nullable=False),
        sa.Column("tipo", sa.Enum("FIJO", "PORCENTAJE", name="tipocostoindirecto"), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("monto >= 0", name="check_costo_indirecto_monto_positivo"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deleted_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_costos_indirectos_tenant_activo", "costos_indirectos", ["tenant_id", "activo"])
    op.create_index("ix_costos_indirectos_tenant_id", "costos_indirectos", ["tenant_id"])

    # ── 2. Socia Progress ─────────────────────────────────────────────────────
    op.create_table(
        "socia_progress",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("logro_id", sa.String(50), nullable=False),
        sa.Column("desbloqueado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("nivel_actual", sa.String(20), nullable=False, server_default="emprendedora"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deleted_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "user_id", "logro_id", name="uq_socia_progress_tenant_user_logro"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_socia_progress_tenant_user", "socia_progress", ["tenant_id", "user_id"])
    op.create_index("ix_socia_progress_tenant_id", "socia_progress", ["tenant_id"])
    op.create_index("ix_socia_progress_user_id", "socia_progress", ["user_id"])

    # ── 3. margen_objetivo en recetas ─────────────────────────────────────────
    op.add_column("recetas", sa.Column("margen_objetivo", sa.Numeric(5, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("recetas", "margen_objetivo")
    op.drop_index("ix_socia_progress_user_id", table_name="socia_progress")
    op.drop_index("idx_socia_progress_tenant_user", table_name="socia_progress")
    op.drop_index("ix_socia_progress_tenant_id", table_name="socia_progress")
    op.drop_table("socia_progress")
    op.drop_index("idx_costos_indirectos_tenant_activo", table_name="costos_indirectos")
    op.drop_index("ix_costos_indirectos_tenant_id", table_name="costos_indirectos")
    op.drop_table("costos_indirectos")
    op.execute("DROP TYPE IF EXISTS tipocostoindirecto")
