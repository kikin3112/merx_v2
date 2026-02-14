"""fix_audit_columns_add_missing_only

Revision ID: a791fb678a02
Revises: b4c55005691b
Create Date: 2026-02-13 15:29:02.087220

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision: str = 'a791fb678a02'
down_revision: Union[str, None] = 'b4c55005691b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add audit columns (created_by, updated_by) to transactional models.
    Create a 'Sistema' user for legacy data attribution.
    Uses conditional logic to avoid duplicate column errors.
    """

    # Step 1: Create 'Sistema' user for legacy data
    sistema_user_id = str(uuid.uuid4())
    op.execute(f"""
        INSERT INTO usuarios (id, nombre, email, password_hash, rol, estado, es_superadmin, created_at, updated_at)
        VALUES (
            '{sistema_user_id}'::uuid,
            'Sistema',
            'sistema@chandelier.internal',
            '$argon2id$v=19$m=65536,t=3,p=4$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
            'operador',
            false,
            false,
            NOW(),
            NOW()
        )
        ON CONFLICT (email) DO NOTHING;
    """)

    # Get the actual sistema_user_id if it already existed
    result = op.get_bind().execute(sa.text("""
        SELECT id FROM usuarios WHERE email = 'sistema@chandelier.internal'
    """))
    sistema_user_id = str(result.fetchone()[0])

    # Step 2: Define tables and audit columns to add
    tables_needing_audit = [
        'terceros',
        'productos',
        'ventas',
        'compras',
        'ordenes_produccion',
        'recetas',
        'cotizaciones',
        'crm_pipelines',
        'crm_stages',
        'crm_deals',
        'crm_activities',
        'movimientos_inventario',
        'asientos_contables'
    ]

    # Step 3: For each table, add columns only if they don't exist
    for table in tables_needing_audit:
        # Add created_by if not exists
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'created_by'
                ) THEN
                    ALTER TABLE {table} ADD COLUMN created_by UUID;
                    ALTER TABLE {table} ADD CONSTRAINT fk_{table}_created_by
                        FOREIGN KEY (created_by) REFERENCES usuarios(id) ON DELETE SET NULL;
                    CREATE INDEX ix_{table}_created_by ON {table}(created_by);
                END IF;
            END $$;
        """)

        # Add updated_by if not exists
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'updated_by'
                ) THEN
                    ALTER TABLE {table} ADD COLUMN updated_by UUID;
                    ALTER TABLE {table} ADD CONSTRAINT fk_{table}_updated_by
                        FOREIGN KEY (updated_by) REFERENCES usuarios(id) ON DELETE SET NULL;
                    CREATE INDEX ix_{table}_updated_by ON {table}(updated_by);
                END IF;
            END $$;
        """)

        # Update legacy data to Sistema user
        op.execute(f"""
            UPDATE {table}
            SET created_by = COALESCE(created_by, '{sistema_user_id}'::uuid),
                updated_by = COALESCE(updated_by, '{sistema_user_id}'::uuid)
            WHERE created_by IS NULL OR updated_by IS NULL;
        """)


def downgrade() -> None:
    """
    Remove audit columns from transactional models.
    Note: This does NOT remove the Sistema user (to avoid breaking existing FKs).
    """

    tables = [
        'terceros', 'productos', 'ventas', 'compras', 'ordenes_produccion',
        'recetas', 'cotizaciones', 'crm_pipelines', 'crm_stages',
        'crm_deals', 'crm_activities', 'movimientos_inventario', 'asientos_contables'
    ]

    for table in tables:
        # Drop indexes and constraints if they exist
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_indexes WHERE tablename = '{table}' AND indexname = 'ix_{table}_updated_by'
                ) THEN
                    DROP INDEX ix_{table}_updated_by;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM pg_indexes WHERE tablename = '{table}' AND indexname = 'ix_{table}_created_by'
                ) THEN
                    DROP INDEX ix_{table}_created_by;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'fk_{table}_updated_by'
                ) THEN
                    ALTER TABLE {table} DROP CONSTRAINT fk_{table}_updated_by;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'fk_{table}_created_by'
                ) THEN
                    ALTER TABLE {table} DROP CONSTRAINT fk_{table}_created_by;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'updated_by'
                ) THEN
                    ALTER TABLE {table} DROP COLUMN updated_by;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'created_by'
                ) THEN
                    ALTER TABLE {table} DROP COLUMN created_by;
                END IF;
            END $$;
        """)
