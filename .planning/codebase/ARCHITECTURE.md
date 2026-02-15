# Architecture

**Analysis Date:** 2026-02-15

## Pattern Overview

**Overall:** Layered architecture with multi-tenant isolation at the database level using PostgreSQL Row Level Security (RLS). Clear separation between routing, business logic (services), and data access layers. Frontend follows component-based React patterns with centralized state management.

**Key Characteristics:**
- Multi-tenant SaaS architecture with PostgreSQL RLS enforcing tenant isolation at database level
- Service layer handles all business logic, with middlewares managing cross-cutting concerns
- Automatic audit trails for all business entity modifications
- JWT-based authentication with role-based access control (RBAC)
- Frontend state management via Zustand stores with persistent auth state
- API-first design with async/await patterns throughout

## Layers

**API/Routing Layer:**
- Purpose: Accept HTTP requests, validate input, dispatch to services
- Location: `backend/app/rutas/` (20+ router files like `facturas.py`, `productos.py`)
- Contains: FastAPI route handlers with request/response validation
- Depends on: Service layer, data models, dependencies (auth, DB session)
- Used by: Frontend via Axios HTTP client

**Service Layer:**
- Purpose: Encapsulate all business logic (inventory, accounting, PDF generation, CRM)
- Location: `backend/app/servicios/` (files like `servicio_inventario.py`, `servicio_contabilidad.py`)
- Contains: Business logic classes with methods for domain operations
- Depends on: Data access layer (SQLAlchemy models), utilities
- Used by: Routers to process requests

**Data Access Layer:**
- Purpose: Define data models and database interactions
- Location: `backend/app/datos/` (models in `modelos.py`, `modelos_tenant.py`, `modelos_crm.py`)
- Contains: SQLAlchemy ORM models with relationships and constraints
- Depends on: Database connection, mixins for common fields
- Used by: Service layer for queries and mutations

**Middleware Layer:**
- Purpose: Handle cross-cutting concerns (tenant context, user context, security, logging)
- Location: `backend/app/middleware/` (files like `tenant_context.py`, `user_context.py`)
- Contains: BaseHTTPMiddleware implementations
- Depends on: FastAPI, context variables
- Used by: FastAPI app initialization

**Utilities/Helpers:**
- Purpose: Provide shared utilities and constants
- Location: `backend/app/utils/` (logger, seguridad for JWT, seeders, rate limiting)
- Contains: Authentication, logging, sequence generation, data seeding
- Depends on: Config, external libraries
- Used by: All layers

## Data Flow

**Request Flow (Authenticated):**

1. HTTP request arrives with `Authorization: Bearer <jwt>` and `X-Tenant-ID: <uuid>`
2. `RequestContextMiddleware` assigns unique request_id and starts timing
3. `TenantContextMiddleware` validates tenant UUID from header, sets ContextVar for RLS
4. `UserContextMiddleware` extracts user_id from JWT token claims
5. `SecurityHeadersMiddleware` prepares response headers
6. FastAPI routes request to handler based on path
7. `get_current_user` dependency validates JWT, extracts user claims, returns user object
8. Route handler receives service layer via dependency injection
9. Service layer executes business logic with automatic DB RLS filtering
10. SQLAlchemy ORM models map results to Python objects
11. Response serialized via Pydantic schemas
12. Middleware chain unwinds: response headers added, context cleaned
13. Response sent to client with X-Request-ID header

**Write Operation Example (Creating Invoice):**

1. POST `/api/v1/facturas` with invoice details and line items
2. Route handler validates schema via Pydantic
3. Service layer (`ServicioVentas`) creates invoice in DB
4. Service automatically creates inventory movements (stock decrements)
5. Service calls `ServicioContabilidad` to create accounting entry
6. Accounting service creates balanced journal entry (DEBE/HABER)
7. Service generates PDF via `ServicioPDF` with tenant branding
8. PDF uploaded to S3 via `ServicioAlmacenamiento`
9. Invoice record updated with PDF URL
10. All within single transaction: if PDF upload fails, whole operation rolls back
11. Response includes invoice data and PDF download URL

**State Management (Frontend):**

1. User logs in → `authStore.login()` calls `/auth/login` endpoint
2. Backend returns `access_token`, `refresh_token`, user data, list of accessible tenants
3. Zustand store persists auth state to localStorage
4. User selects tenant → `authStore.selectTenant()` calls `/auth/select-tenant`
5. New tenant-scoped token issued, stored alongside refresh token
6. Axios interceptor reads tokens from localStorage, adds to every request header
7. If 401 response → automatic token refresh using refresh_token
8. If refresh fails → clear auth state, redirect to login

## Key Abstractions

**ServicioInventario:**
- Purpose: Manages stock movements, weighted average costing, recipe-based production
- Examples: `backend/app/servicios/servicio_inventario.py`
- Pattern: Constructor takes `db: Session` and `tenant_id: UUID`, methods are stateless operations
- Methods: `registrar_movimiento()`, `aplicar_receta()`, `obtener_inventario_valorizado()`

**ServicioContabilidad:**
- Purpose: Automatically creates balanced journal entries for business transactions
- Examples: `backend/app/servicios/servicio_contabilidad.py`
- Pattern: Reads accounting configuration per tenant, ensures DEBE = HABER balance
- Methods: `crear_asiento_venta()`, `crear_asiento_produccion()`, `crear_asiento_anulacion()`

**ServicioPDF:**
- Purpose: Generates PDF documents (invoices, quotes) with tenant branding
- Examples: `backend/app/servicios/servicio_pdf.py`
- Pattern: Takes data object, renders to bytes, returns for upload
- Methods: `generar_factura()`, `generar_cotizacion()`

**TenantMixin / TenantAuditMixin:**
- Purpose: SQLAlchemy mixins that add tenant isolation and audit fields to any model
- Examples: `backend/app/datos/mixins.py`
- Pattern: Declarative attributes added to model classes via inheritance
- Adds fields: `tenant_id`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

**TenantContextMiddleware:**
- Purpose: Extract tenant_id from header, validate UUID, set PostgreSQL session variable for RLS
- Examples: `backend/app/middleware/tenant_context.py`
- Pattern: Middleware that hooks into every request lifecycle
- Key feature: Maintenance mode cache to avoid DB hits on every write

## Entry Points

**Backend Entry Point:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn.run()` or Docker container start
- Responsibilities: Initialize FastAPI app, register all middleware, include routers, setup lifespan events (startup/shutdown checks)

**Frontend Entry Point:**
- Location: `frontend/src/main.tsx`
- Triggers: Browser loads application
- Responsibilities: Mount React app to DOM, initialize QueryClient, wrap with providers

**Authentication Entry Point:**
- Location: `backend/app/rutas/auth.py`
- Triggers: POST `/api/v1/auth/login`
- Responsibilities: Validate credentials, generate JWT tokens, return user + tenant list

**Tenant Registration Entry Point:**
- Location: `backend/app/rutas/tenants.py` endpoint `POST /api/v1/tenants/register`
- Triggers: New organization signs up
- Responsibilities: Create tenant record, create admin user, initialize tenant configuration, seed chart of accounts

## Error Handling

**Strategy:** Centralized exception handlers at FastAPI app level, with logging at each layer. Production vs development error exposure controlled by settings.

**Patterns:**

1. **Validation Errors (422):**
   - `RequestValidationError` caught by `@app.exception_handler`
   - Returns Pydantic validation error details
   - Logged at WARNING level
   - File: `backend/app/main.py` lines 292-309

2. **Business Logic Errors (400):**
   - ValueError raised in service layer with descriptive message
   - Caught by `@app.exception_handler(ValueError)`
   - Returns 400 Bad Request with error message
   - File: `backend/app/main.py` lines 312-323

3. **Authentication Errors (401/403):**
   - HTTPException with status_code 401 or 403 raised by `get_current_user` dependency
   - Propagates through, returns 401/403 to client
   - Axios interceptor on frontend handles 401 → refresh token flow

4. **Rate Limiting (429):**
   - slowapi library enforces 100 req/min per IP
   - Custom handler returns 429 Too Many Requests
   - File: `backend/app/main.py` lines 376-390

5. **Unhandled Exceptions (500):**
   - Generic handler catches all exceptions
   - In development: full error details returned
   - In production: generic message + request_id returned
   - Always logged with full traceback via logger.error()
   - Sent to Sentry if enabled

6. **Database Errors:**
   - SQLAlchemy exceptions caught in `get_db()` dependency
   - Session rolled back on error
   - Exception re-raised for request handler to convert to HTTP response

## Cross-Cutting Concerns

**Logging:**
- Setup: `backend/app/utils/logger.py` with structlog
- Per-request context includes request_id, user_id, method, path, status_code
- All service operations logged with business context (e.g., "Factura creada: FAC-001")
- In production, sent to Sentry for error tracking

**Validation:**
- Input: Pydantic schemas in route handlers enforce request shape
- Business rules: Service layer validates (e.g., "stock cannot be negative")
- Database: CHECK constraints on critical columns (stock >= 0)
- Pattern: Validate as early as possible, fail fast with descriptive error

**Authentication:**
- JWT tokens generated with HS256 algorithm
- Payload includes user_id, email, rol (global role), tenants list
- Tokens expire in 1 hour; refresh tokens valid 7 days
- File: `backend/app/utils/seguridad.py` for token generation/validation
- Frontend: `frontend/src/stores/authStore.ts` manages token lifecycle
- Axios interceptor automatically handles refresh on 401

**Multi-Tenancy/RLS:**
- Middleware extracts tenant_id from X-Tenant-ID header
- ContextVar stores tenant_id for request lifetime
- Database event listener sets PostgreSQL `app.tenant_id_actual` variable at transaction start
- All tenant-isolation table rows filtered via PostgreSQL RLS policies
- Pattern: Cannot be bypassed; RLS is database-enforced

**Auditing:**
- SQLAlchemy event listener intercepts inserts/updates/deletes
- Automatically populates created_at, created_by, updated_at, updated_by
- User context extracted from ContextVar set by middleware
- File: `backend/app/datos/audit_listeners.py`
- Soft deletes: records marked with deleted_at timestamp instead of physically deleted

**Permission/RBAC:**
- User has global role (admin, operador, contador, superadmin)
- User has per-tenant role (admin, vendedor, contador)
- Routes check role via `require_tenant_roles()` decorator
- Example: inventory operations require rol in ['admin', 'operador']
- File: `backend/app/utils/seguridad.py` function `require_tenant_roles`

---

*Architecture analysis: 2026-02-15*
