"""add produccion_mensual_esperada to recetas

Revision ID: e7f8a9b0c1d2
Revises: d1e2f3a4b5c6
Create Date: 2026-03-02

Distribuye los costos indirectos fijos (CIF mensual) entre la producción
mensual total en lugar de cargarlos completos a cada lote.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e7f8a9b0c1d2"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "recetas",
        sa.Column("produccion_mensual_esperada", sa.Numeric(10, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recetas", "produccion_mensual_esperada")
