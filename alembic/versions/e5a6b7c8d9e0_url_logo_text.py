"""url_logo_text

Revision ID: e5a6b7c8d9e0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-26 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "e5a6b7c8d9e0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "tenants",
        "url_logo",
        existing_type=sa.String(500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "tenants",
        "url_logo",
        existing_type=sa.Text(),
        type_=sa.String(500),
        existing_nullable=True,
    )
