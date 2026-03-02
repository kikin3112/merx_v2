"""add porcentaje_merma to recetas_ingredientes (merge heads)

Merges c5d6e7f8a9b0 (socia pricing) and c7eb4b5e1ff2 (fase1_seguridad)
and adds the porcentaje_merma column to recetas_ingredientes.

Revision ID: b2c3d4e5f6a7
Revises: c5d6e7f8a9b0, c7eb4b5e1ff2
Create Date: 2026-03-01 22:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = ("c5d6e7f8a9b0", "c7eb4b5e1ff2")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add porcentaje_merma column with default 0.00 (no behavior change for existing rows)
    op.add_column(
        "recetas_ingredientes",
        sa.Column(
            "porcentaje_merma",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0.00",
        ),
    )
    # Add check constraint: merma must be in [0, 99.99)
    op.create_check_constraint(
        "check_ingrediente_merma_valida",
        "recetas_ingredientes",
        "porcentaje_merma >= 0 AND porcentaje_merma < 100",
    )


def downgrade() -> None:
    op.drop_constraint("check_ingrediente_merma_valida", "recetas_ingredientes", type_="check")
    op.drop_column("recetas_ingredientes", "porcentaje_merma")
