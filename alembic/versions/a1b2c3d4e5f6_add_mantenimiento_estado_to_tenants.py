"""add_mantenimiento_estado_to_tenants

Revision ID: a1b2c3d4e5f6
Revises: c7eb4b5e1ff2
Create Date: 2026-02-13 00:00:00.000000

Adds 'mantenimiento' as a valid value for tenants.estado,
enabling Maintenance Mode (write-blocking without full suspension).
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c7eb4b5e1ff2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the existing CHECK constraint and recreate it including 'mantenimiento'
    op.execute(
        "ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_estado_check"
    )
    op.execute(
        "ALTER TABLE tenants ADD CONSTRAINT tenants_estado_check "
        "CHECK (estado IN ('activo', 'suspendido', 'cancelado', 'trial', 'pendiente', 'mantenimiento'))"
    )


def downgrade() -> None:
    # Restore original CHECK constraint (without 'mantenimiento')
    # First set any 'mantenimiento' tenants back to 'activo'
    op.execute(
        "UPDATE tenants SET estado = 'activo' WHERE estado = 'mantenimiento'"
    )
    op.execute(
        "ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_estado_check"
    )
    op.execute(
        "ALTER TABLE tenants ADD CONSTRAINT tenants_estado_check "
        "CHECK (estado IN ('activo', 'suspendido', 'cancelado', 'trial', 'pendiente'))"
    )
