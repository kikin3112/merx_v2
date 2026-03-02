"""recetas: replace unique index with partial (soft-delete safe)

Revision ID: f2a3b4c5d6e7
Revises: b2c3d4e5f6a7
Create Date: 2026-03-02

"""
from alembic import op

revision = 'f2a3b4c5d6e7'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old full unique index (blocked soft-deleted names from being reused)
    op.drop_index('idx_recetas_tenant_nombre', table_name='recetas')
    # Create partial unique index — only enforces uniqueness on active rows
    op.execute(
        "CREATE UNIQUE INDEX idx_recetas_tenant_nombre_active "
        "ON recetas (tenant_id, nombre) WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    op.drop_index('idx_recetas_tenant_nombre_active', table_name='recetas')
    op.create_index('idx_recetas_tenant_nombre', 'recetas', ['tenant_id', 'nombre'], unique=True)
