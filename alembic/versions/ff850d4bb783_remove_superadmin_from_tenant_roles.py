"""remove superadmin from tenant roles

Revision ID: ff850d4bb783
Revises: 5600c67af29d
Create Date: 2026-02-12 10:23:26.717241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff850d4bb783'
down_revision: Union[str, None] = '5600c67af29d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Delete any superadmin-tenant relationships (superadmin is system-level only)
    op.execute(
        "DELETE FROM usuarios_tenants WHERE rol = 'superadmin'"
    )

    # 2. Drop old CHECK constraint and create new one without 'superadmin'
    op.drop_constraint('check_rol_tenant_valido', 'usuarios_tenants', type_='check')
    op.create_check_constraint(
        'check_rol_tenant_valido',
        'usuarios_tenants',
        "rol IN ('admin', 'operador', 'contador', 'vendedor', 'readonly')"
    )


def downgrade() -> None:
    # Revert: allow superadmin in tenant roles again
    op.drop_constraint('check_rol_tenant_valido', 'usuarios_tenants', type_='check')
    op.create_check_constraint(
        'check_rol_tenant_valido',
        'usuarios_tenants',
        "rol IN ('superadmin', 'admin', 'operador', 'contador', 'vendedor', 'readonly')"
    )
