"""producto_equivalencias_unidad + receta_costos_historicos

Revision ID: d1e2f3a4b5c6
Revises: f2a3b4c5d6e7
Create Date: 2026-03-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "d1e2f3a4b5c6"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "producto_equivalencias_unidad",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("producto_id", UUID(as_uuid=True), sa.ForeignKey("productos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unidad_receta", sa.String(20), nullable=False),
        sa.Column("factor", sa.Numeric(15, 6), nullable=False),
        sa.Column("notas", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "idx_equiv_tenant_producto_unidad",
        "producto_equivalencias_unidad",
        ["tenant_id", "producto_id", "unidad_receta"],
        unique=True,
    )
    op.create_index("idx_equiv_tenant_producto", "producto_equivalencias_unidad", ["tenant_id", "producto_id"])

    op.create_table(
        "receta_costos_historicos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("receta_id", UUID(as_uuid=True), sa.ForeignKey("recetas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("costo_unitario", sa.Numeric(15, 2), nullable=False),
        sa.Column("precio_sugerido", sa.Numeric(15, 2), nullable=True),
        sa.Column("confirmado_por", UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confirmado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("snapshot_detalle", JSONB, nullable=True),
        sa.Column("vigente_desde", sa.Date, nullable=True),
        sa.Column("vigente_hasta", sa.Date, nullable=True),
        sa.Column("notas_confirmacion", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_costos_hist_tenant_receta", "receta_costos_historicos", ["tenant_id", "receta_id"])
    op.create_index(
        "idx_costos_hist_tenant_receta_fecha",
        "receta_costos_historicos",
        ["tenant_id", "receta_id", "vigente_desde"],
    )


def downgrade() -> None:
    op.drop_table("receta_costos_historicos")
    op.drop_table("producto_equivalencias_unidad")
