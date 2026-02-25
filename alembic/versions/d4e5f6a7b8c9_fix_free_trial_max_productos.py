"""fix_free_trial_max_productos

Revision ID: d4e5f6a7b8c9
Revises: cbb160c37bbc
Create Date: 2026-02-25 22:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "cbb160c37bbc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE planes
        SET max_productos = 500
        WHERE nombre = 'Free Trial' AND max_productos < 500
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE planes
        SET max_productos = 50
        WHERE nombre = 'Free Trial' AND max_productos = 500
        """
    )
