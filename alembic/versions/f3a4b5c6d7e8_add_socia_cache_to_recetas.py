"""add socia_cache to recetas

Revision ID: f3a4b5c6d7e8
Revises: e7f8a9b0c1d2
Create Date: 2026-03-05

Almacena el análisis Fase-1 de Socia en DB para evitar llamadas repetidas al LLM.
El cache se invalida automáticamente cuando cambian los costos de la receta (hash del CVU + escenarios).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "f3a4b5c6d7e8"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recetas", sa.Column("socia_cache", JSONB, nullable=True))
    op.add_column("recetas", sa.Column("socia_cache_key", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("recetas", "socia_cache_key")
    op.drop_column("recetas", "socia_cache")
