"""add_cobro_cartera_to_tipo_asiento_check

Revision ID: 30bd1c39837f
Revises: de736ea93ccf
Create Date: 2026-03-06 23:09:33.279907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30bd1c39837f'
down_revision: Union[str, None] = 'de736ea93ccf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old check constraint and recreate with COBRO_CARTERA added
    op.drop_constraint("check_tipo_asiento_valido", "asientos_contables", type_="check")
    op.create_check_constraint(
        "check_tipo_asiento_valido",
        "asientos_contables",
        "tipo_asiento IN ('VENTAS', 'COMPRAS', 'PRODUCCION', 'AJUSTE', 'NOMINA', 'COBRO_CARTERA', 'OTRO')",
    )


def downgrade() -> None:
    # Revert to original constraint (without COBRO_CARTERA)
    op.drop_constraint("check_tipo_asiento_valido", "asientos_contables", type_="check")
    op.create_check_constraint(
        "check_tipo_asiento_valido",
        "asientos_contables",
        "tipo_asiento IN ('VENTAS', 'COMPRAS', 'PRODUCCION', 'AJUSTE', 'NOMINA', 'OTRO')",
    )
