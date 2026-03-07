"""phase4_dian_fields

Adds DIAN-compliance columns for Phase 4:
- C-22: retencion_renta, retencion_ica on compras
- C-23: cufe on ventas
- C-24: regimen_tributario on tenants and terceros

Revision ID: b1c2d3e4f5a6
Revises: 4c95adbde585
Create Date: 2026-03-07 02:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "4c95adbde585"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

REGIMEN_TRIBUTARIO_VALUES = (
    "('RESPONSABLE_IVA', 'REGIMEN_SIMPLE', 'REGIMEN_ESPECIAL', 'NO_RESPONSABLE')"
)


def upgrade() -> None:
    # C-22: Retenciones en compras
    op.add_column("compras", sa.Column("retencion_renta", sa.Numeric(15, 2), nullable=True))
    op.add_column("compras", sa.Column("retencion_ica", sa.Numeric(15, 2), nullable=True))

    # C-23: CUFE en ventas
    op.add_column("ventas", sa.Column("cufe", sa.String(96), nullable=True))
    op.create_index("ix_ventas_cufe", "ventas", ["cufe"])

    # C-24: Régimen tributario en tenants
    op.add_column(
        "tenants",
        sa.Column("regimen_tributario", sa.String(50), nullable=True, server_default="RESPONSABLE_IVA"),
    )
    op.create_check_constraint(
        "check_regimen_tributario_tenant_valido",
        "tenants",
        f"regimen_tributario IS NULL OR regimen_tributario IN {REGIMEN_TRIBUTARIO_VALUES}",
    )

    # C-24: Régimen tributario en terceros
    op.add_column(
        "terceros",
        sa.Column("regimen_tributario", sa.String(50), nullable=True, server_default="RESPONSABLE_IVA"),
    )
    op.create_check_constraint(
        "check_regimen_tributario_tercero_valido",
        "terceros",
        f"regimen_tributario IS NULL OR regimen_tributario IN {REGIMEN_TRIBUTARIO_VALUES}",
    )


def downgrade() -> None:
    # C-24 rollback
    op.drop_constraint("check_regimen_tributario_tercero_valido", "terceros", type_="check")
    op.drop_column("terceros", "regimen_tributario")

    op.drop_constraint("check_regimen_tributario_tenant_valido", "tenants", type_="check")
    op.drop_column("tenants", "regimen_tributario")

    # C-23 rollback
    op.drop_index("ix_ventas_cufe", table_name="ventas")
    op.drop_column("ventas", "cufe")

    # C-22 rollback
    op.drop_column("compras", "retencion_ica")
    op.drop_column("compras", "retencion_renta")
