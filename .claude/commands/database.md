# Chandelier - Base de Datos

Configuración de PostgreSQL + SQLAlchemy sync + Alembic para el proyecto.

## Conexión

```python
# backend/app/datos/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from ..config import settings

engine = create_engine(
    str(settings.DB_URL),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Modelos - Patrón Tenant

```python
# backend/app/datos/mixins.py
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

class TenantMixin:
    """Agrega tenant_id FK a modelos multi-tenant."""
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

class SoftDeleteMixin:
    """Agrega soft delete."""
    deleted_at = Column(DateTime, nullable=True, default=None)
```

```python
# backend/app/datos/modelos_tenant.py (ejemplo)
from sqlalchemy import Column, String, Numeric, Integer, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from .db import Base
from .mixins import TenantMixin, SoftDeleteMixin
import uuid

class Productos(Base, TenantMixin, SoftDeleteMixin):
    __tablename__ = "productos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), nullable=False)
    nombre = Column(String(200), nullable=False)
    precio_venta = Column(Numeric(12, 2), nullable=False)
    precio_costo = Column(Numeric(12, 2), nullable=False)
    stock = Column(Integer, default=0)
    tarifa_iva = Column(Numeric(5, 2), default=19.00)

    __table_args__ = (
        Index("idx_productos_tenant_sku", "tenant_id", "sku", unique=True),
        CheckConstraint("stock >= 0", name="ck_productos_stock_positivo"),
    )
```

## Alembic

```bash
# Crear migración
uv run alembic revision --autogenerate -m "descripcion del cambio"

# Aplicar migraciones
uv run alembic upgrade head

# Bajar una migración
uv run alembic downgrade -1

# Ver estado
uv run alembic current
uv run alembic history --verbose
```

## Secuencias (Numeración de Documentos)

```python
# Patrón para numeración secuencial por tenant
from ..datos.modelos_tenant import Secuencias

def generar_numero_secuencia(db: Session, tipo_documento: str, tenant_id: UUID) -> str:
    """Genera número secuencial atómico (FOR UPDATE locking)."""
    secuencia = (
        db.query(Secuencias)
        .filter(Secuencias.tenant_id == tenant_id, Secuencias.tipo == tipo_documento)
        .with_for_update()
        .first()
    )
    # Incrementar y retornar
    ...
```

## Queries Comunes

```python
# SIEMPRE filtrar por tenant_id
productos = db.query(Productos).filter(Productos.tenant_id == tenant_id).all()

# Paginación
items = db.query(Model).filter(...).offset(skip).limit(limit).all()

# Flush vs Commit
db.flush()   # En servicios (genera ID sin commit)
db.commit()  # En rutas (persiste la transacción)

# Rollback en errores
try:
    db.commit()
except Exception:
    db.rollback()
    raise
```

## Gotchas

- `@hybrid_property` solo funciona en Python, NO en SQL aggregations
- `generar_numero_secuencia()` requiere `tenant_id` como 3er argumento
- Pool: `pool_pre_ping=True` evita conexiones muertas
- DB local: `postgresql://postgres:kikin3112@localhost:5432/api_merx_v2`
