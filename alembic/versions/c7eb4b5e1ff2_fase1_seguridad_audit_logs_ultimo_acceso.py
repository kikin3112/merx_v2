"""fase1_seguridad_audit_logs_ultimo_acceso

Revision ID: c7eb4b5e1ff2
Revises: b0955cb14c15
Create Date: 2026-02-13 10:54:45.248785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c7eb4b5e1ff2'
down_revision: Union[str, None] = 'b0955cb14c15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables with TenantMixin that need RLS policies
RLS_TABLES = [
    "terceros",
    "productos",
    "inventarios",
    "movimientos_inventario",
    "ventas",
    "ventas_detalle",
    "compras",
    "compras_detalle",
    "ordenes_produccion",
    "ordenes_produccion_detalle",
    "recetas",
    "cotizaciones",
    "cotizaciones_detalle",
    "cuentas_contables",
    "configuracion_contable",
    "asientos_contables",
    "detalles_asiento",
    "medios_pago",
    "cartera",
    "pagos_cartera",
    "secuencias",
]


def upgrade() -> None:
    # === 1. Audit Logs table ===
    op.create_table('audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('actor_email', sa.String(length=100), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.UUID(), nullable=True),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'], unique=False)
    op.create_index('idx_audit_logs_tenant_created', 'audit_logs', ['tenant_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'], unique=False)

    # === 2. ultimo_acceso on usuarios ===
    op.add_column('usuarios', sa.Column('ultimo_acceso', sa.DateTime(timezone=True), nullable=True))

    # === 3. RLS Policies for all tenant-scoped tables ===
    for tabla in RLS_TABLES:
        op.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {tabla} FORCE ROW LEVEL SECURITY;")

        # SELECT/UPDATE/DELETE policy
        op.execute(f"""
            CREATE POLICY tenant_isolation_{tabla} ON {tabla}
                USING (tenant_id::text = current_setting('app.tenant_id_actual', true));
        """)

        # INSERT policy
        op.execute(f"""
            CREATE POLICY tenant_insert_{tabla} ON {tabla}
                FOR INSERT
                WITH CHECK (tenant_id::text = current_setting('app.tenant_id_actual', true));
        """)


def downgrade() -> None:
    # === 3. Remove RLS Policies ===
    for tabla in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{tabla} ON {tabla};")
        op.execute(f"DROP POLICY IF EXISTS tenant_insert_{tabla} ON {tabla};")
        op.execute(f"ALTER TABLE {tabla} DISABLE ROW LEVEL SECURITY;")

    # === 2. Remove ultimo_acceso ===
    op.drop_column('usuarios', 'ultimo_acceso')

    # === 1. Remove audit_logs table ===
    op.drop_index(op.f('ix_audit_logs_actor_id'), table_name='audit_logs')
    op.drop_index('idx_audit_logs_tenant_created', table_name='audit_logs')
    op.drop_index('idx_audit_logs_resource', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_table('audit_logs')
