# Codebase Conventions

Analysis of naming, style, documentation, error handling, logging, and comment patterns.

## Backend (Python/FastAPI)

### File Naming

- **Modules**: snake_case (e.g., servicio_inventario.py, modelos.py)
- **Test files**: test_*.py prefix (e.g., test_rbac_backend.py)
- **Configuration**: config.py, settings in class
- **Database**: db.py, modelos.py, esquemas.py
- **Routes**: Named by domain (e.g., productos.py, ventas.py)

### Directory Structure

backend/
  app/
    datos/          # Data layer (models, schemas, db)
    rutas/          # API routes/controllers
    servicios/      # Business logic services
    middleware/     # FastAPI middleware
    utils/          # Utilities (logger, seguridad, etc.)
    main.py         # Application entry point
  tests/              # Test files

### Naming Conventions

#### Classes

- **Models**: Plural nouns in Spanish (e.g., Productos, Ventas, Terceros)
- **Schemas**: EntityBase, EntityCreate, EntityUpdate, EntityResponse
- **Services**: ServicioDomain (e.g., ServicioInventario)
- **Mixins**: PurposeMixin (e.g., TenantMixin, AuditMixin)
- **Enums**: PascalCase with UPPERCASE values (e.g., EstadoVenta.PENDIENTE)

#### Variables and Functions

- **snake_case** for all variables and functions
- **Private methods**: _leading_underscore
- **Boolean fields**: is_, es_, esta_ prefixes (e.g., es_superadmin, esta_activo)
- **ID fields**: producto_id, tenant_id (not productId)

#### Constants

- **UPPER_SNAKE_CASE** for constants (e.g., TEST_DB_URL, STORAGE_KEY)

### Code Style

#### Linting Configuration (Ruff)

Line length: 120
Target: py312
Selected rules: E, F, I, N, W
Ignored: E501 (line too long), N806 (non-lowercase variable)

#### Imports

Standard ordering:
1. Standard library
2. Third-party packages
3. Local imports (relative)

#### Type Hints

- **Required** for function signatures
- **Optional** for return types in simple functions

### Documentation Patterns

#### Docstrings

- **Triple-quoted** with description
- **Args/Returns/Raises** sections for complex functions
- **Spanish** language for business logic documentation

#### Class Docstrings

Include purpose and usage examples.

#### Inline Comments

- **Spanish** language
- **Section separators** with # === pattern

### Error Handling Patterns

#### HTTP Exceptions

- **HTTPException** from FastAPI for API errors
- **Descriptive detail messages** in Spanish

#### Business Logic Errors

- **ValueError** for business rule violations

#### Exception Handlers (Global)

Located in main.py for validation, value errors, HTTP exceptions, and general exceptions.

### Logging Conventions

#### Logger Setup

from utils.logger import setup_logger
logger = setup_logger(__name__)

#### Log Levels

- **INFO**: Normal operations (creations, updates)
- **WARNING**: Soft deletes, potential issues
- **ERROR**: Exceptions, failures

#### Structured Logging

- **JSON format** in production
- **Text format** in development
- **Extra context** as dict with relevant IDs

---

## Frontend (TypeScript/React)

### File Naming

- **Components**: PascalCase.tsx (e.g., Sidebar.tsx)
- **Pages**: NamePage.tsx (e.g., DashboardPage.tsx)
- **Stores**: camelCaseStore.ts (e.g., authStore.ts)
- **Types**: index.ts (barrel export)
- **Hooks**: usePurpose.ts (e.g., useNavigation.ts)

### Directory Structure

frontend/src/
  api/            # API client and endpoints
  components/     # React components
    layout/       # Layout components
    ui/           # UI primitives
    auth/         # Auth-related components
  hooks/          # Custom React hooks
  pages/          # Page components
  stores/         # Zustand stores
  types/          # TypeScript type definitions
  utils/          # Utility functions

### Naming Conventions

#### Interfaces and Types

- **PascalCase** for interface/type names
- **Suffix conventions**: Create, Update, Response

#### Variables and Functions

- **camelCase** for variables and functions
- **UPPER_SNAKE_CASE** for constants

### State Management (Zustand)

Interface defines state + actions
create() with persist middleware
Storage key: chandelier-auth

### API Client Pattern

- **Axios** with interceptors
- **Token refresh** handling
- **Automatic header injection** (Authorization, X-Tenant-ID)

---

## Database Conventions

### Table Names

- **Plural** in Spanish: productos, ventas, terceros
- **Snake_case**: movimientos_inventario, ordenes_produccion

### Column Names

- **snake_case** for all columns
- **Foreign keys**: entity_id (e.g., producto_id, tenant_id)
- **Timestamps**: created_at, updated_at, deleted_at

### Constraints

- **Check constraints** with descriptive names: check_precio_venta_positivo
- **Unique constraints** via indexes: idx_productos_tenant_codigo

### Indexes

- **Naming**: idx_table_columns
- **Composite indexes** for common queries

---

## Key Architectural Patterns

### Multi-Tenancy (RLS)

- **TenantMixin** adds tenant_id to models
- **Middleware** sets PostgreSQL session variable
- **All queries** automatically scoped by tenant

### Soft Deletes

- **SoftDeleteMixin** adds deleted_at and deleted_by
- **Queries filter** deleted_at IS NULL

### Audit Trail

- **AuditMixin** adds created_at, updated_at, created_by, updated_by
- **Automatic population** via middleware

### Repository Pattern

Services receive db: Session and tenant_id: UUID:

class ServicioInventario:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
