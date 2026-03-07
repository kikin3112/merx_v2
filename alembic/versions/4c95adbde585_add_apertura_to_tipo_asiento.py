"""add_apertura_to_tipo_asiento

Revision ID: 4c95adbde585
Revises: 835b979b6465
Create Date: 2026-03-07 02:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c95adbde585'
down_revision: Union[str, None] = '835b979b6465'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # C-07: Add APERTURA to tipo_asiento check constraint
    op.drop_constraint("check_tipo_asiento_valido", "asientos_contables", type_="check")
    op.create_check_constraint(
        "check_tipo_asiento_valido",
        "asientos_contables",
        "tipo_asiento IN ('VENTAS', 'COMPRAS', 'PRODUCCION', 'AJUSTE', 'NOMINA', 'COBRO_CARTERA', 'OTRO', 'APERTURA')",
    )


def downgrade() -> None:
    op.drop_constraint("check_tipo_asiento_valido", "asientos_contables", type_="check")
    op.create_check_constraint(
        "check_tipo_asiento_valido",
        "asientos_contables",
        "tipo_asiento IN ('VENTAS', 'COMPRAS', 'PRODUCCION', 'AJUSTE', 'NOMINA', 'COBRO_CARTERA', 'OTRO')",
    )
