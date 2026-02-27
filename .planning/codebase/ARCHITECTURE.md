# Architecture

**Analysis Date:** 2026-02-27

## Pattern Overview

**Overall:** Multi-tenant SaaS ERP with strict tenant isolation via Row-Level Security (RLS) and compound business modules that unify related operations.

**Key Characteristics:**
- **Multi-tenant at core** - Every business entity has `tenant_id`; RLS enforces isolation at PostgreSQL level
- **Compound unified modules** - Operations (e.g., Products+Inventory, Invoices+Clients) execute related flows atomically
- **Async-first backend** - FastAPI with `async def` for all I/O operations
- **Context-driven frontend** - Zustand global state + React Query for server state; state always reflects current tenant context
- **SSE for real-time** - Server-Sent Events for live updates; no polling
- **Superadmin bypass** - Superusers can impersonate tenants without losing their original session

## Layers

**HTTP/Request (Frontend → Backend):**
- Purpose: Accept HTTP requests, validate input, return responses
- Location: `backend/app/rutas/`
- Contains: Route handlers, DTO validation with Pydantic, HTTP status codes
- Depends on: Service layer for business logic
- Used by: Frontend via Axios client
- Pattern: Minimal logic; delegates to services immediately

**Business Logic (Services):**
- Purpose: Execute all business operations, orchestrate multi-table changes, enforce invariants
- Location: `backend/app/servicios/`
- Contains: Service classes (`ServicioProductos`, `ServicioVentas`, `ServicioTenants`, etc.)
- Depends on: Data access layer (models) and utilities (auth, PDF, storage)
- Used by: Route handlers, other services
- Pattern: Transaction-wrapped methods; methods are atomic operations

**Data Access (Models & ORM):**
- Purpose: Define database schema and provide query interface
- Location: `backend/app/datos/`
  - `modelos.py` - Main business entities (Productos, Ventas, Terceros, Usuarios, etc.)
  - `modelos_tenant.py` - Tenant management (Tenants, UsuariosTenants, Planes, Suscripciones)
  - `modelos_crm.py` - CRM entities (Contactos, Deals, ActivityLog)
  - `modelos_pqrs.py` - Support tickets (Tickets, Respuestas)
  - `modelos_calificaciones.py` - Supplier/customer ratings
  - `esquemas.py` - Pydantic DTO schemas for request/response validation
  - `db.py` - SQLAlchemy session factory, RLS context setup, event listeners
  - `mixins.py` - Common model fields (timestamps, soft deletes, audit fields)
  - `audit_listeners.py` - Automatic audit trail on all changes
- Contains: SQLAlchemy declarative models with RLS support
- Depends on: PostgreSQL driver (psycopg2)
- Used by: Services via SQLAlchemy ORM
- Pattern: RLS via `SET LOCAL app.tenant_id_actual` on every transaction

**Middleware (Request Processing):**
- Purpose: Intercept and enrich requests with context, enforce policies
- Location: `backend/app/middleware/`
- Key components:
  - `tenant_context.py` - Extracts `X-Tenant-ID` header, validates UUID, establishes RLS context, blocks maintenance mode writes
  - `user_context.py` - Extracts user_id from JWT, establishes ContextVar for audit logging
  - `RequestContextMiddleware` (main.py) - Assigns `request_id`, logs request/response times
  - `SecurityHeadersMiddleware` (main.py) - Adds security headers (X-Content-Type-Options, HSTS, etc.)
- Depends on: FastAPI middleware hooks
- Order: RequestContextMiddleware → SecurityHeadersMiddleware → TenantContextMiddleware → UserContextMiddleware → CORS → app logic

**Frontend State (Client-side):**
- Purpose: Manage UI state (global auth/tenant context) and cache server responses
- Location: `frontend/src/stores/` and `frontend/src/api/`
- Key components:
  - `authStore.ts` (Zustand) - Persistent auth state: `token`, `refreshToken`, `user`, `tenants`, `tenantId`, `rolEnTenant`, `impersonation`
  - `client.ts` (Axios) - HTTP client with auto-auth injection, token refresh queue, 401 retry logic
  - `endpoints.ts` - API endpoint helpers (auth, productos, ventas, etc.)
- Depends on: localStorage for persistence, Axios for HTTP
- Used by: React components via hooks and direct store access
- Pattern: Server state in React Query; app state in Zustand

**Frontend Components (UI):**
- Purpose: Render UI and trigger state changes
- Location: `frontend/src/components/`
  - `layout/` - Shell, sidebar, navbar, drawer (persistent structure)
  - `auth/` - RoleGuard, SuperadminGuard (access control)
  - `unified/` - Compound modules (ProductInventoryModule)
  - `crm/` - CRM-specific: Kanban, Deals, ActivityFeed
  - `soporte/` - Support system: TicketList, TicketDetail, CreateTicketModal
  - `onboarding/` - Wizard flows for new tenants
  - `ui/` - Reusable: Modal, SearchInput, DataCard, Skeleton
  - `virtualized/` - VirtualList for 100k+ row tables
- Contains: React functional components with hooks
- Depends on: API client, Zustand store, React Router, UI libraries (Tailwind, Heroicons, Framer Motion)
- Pattern: Container/Presentation separation via custom hooks

**Pages (Route Components):**
- Purpose: Map routes to full-page experiences
- Location: `frontend/src/pages/`
- Key pages:
  - `LoginPage.tsx` / `RegistroPage.tsx` - Auth flows (Clerk + legacy)
  - `ClerkCallbackPage.tsx` - Clerk JWT → custom JWT exchange, auto-redirect
  - `SelectTenantPage.tsx` - Multi-tenant selector (if user has >1 tenant)
  - `EmpresaWizardPage.tsx` - Onboarding wizard for new company
  - `DashboardPage.tsx` - Home dashboard
  - `ProductosPage.tsx`, `VentasPage.tsx`, `InventarioPage.tsx` - Domain pages
  - `TenantsPage.tsx` - Superadmin: manage all tenants
- Contains: Page-level state, data fetching, layout composition
- Depends on: Components, hooks, API client, auth store
- Pattern: UseEffect for data loading, useCallback for event handlers

## Data Flow

**User Authentication Flow:**

1. User submits login form (email/password) or Clerk OAuth
2. Frontend: `POST /auth/login` or `POST /auth/clerk-exchange` with credentials/Clerk JWT
3. Backend: Authenticate user, generate JWT tokens, return list of available tenants
4. Frontend: Store tokens in `authStore` (persisted to localStorage), display tenant selector if >1 tenant
5. Frontend: User selects tenant → `POST /auth/select-tenant`
6. Backend: Validate user-tenant relationship, generate new JWT with `tenant_id` claim
7. Frontend: Store new token, redirect to dashboard
8. All subsequent requests: Axios interceptor injects `Authorization: Bearer {token}` + `X-Tenant-ID: {tenantId}`

**Tenant Isolation (RLS):**

1. Request arrives at `TenantContextMiddleware`
2. Extract `X-Tenant-ID` header, validate UUID format
3. Store in ContextVar `_current_tenant_id` (async context)
4. On database transaction begin: SQLAlchemy event listener executes `SET LOCAL app.tenant_id_actual = {tenant_id}`
5. PostgreSQL RLS policies filter all queries by tenant automatically
6. After response: Clear ContextVar, RLS context is reset on next transaction

**Business Operation (Example: Create Sale):**

1. Frontend: User submits sale form (ProductosSale component)
2. Frontend: `POST /api/v1/ventas` with sale details
3. Backend Route: `rutas/ventas.py:crear_venta()` validates DTO
4. Backend Service: `ServicioVentas.crear_venta()` orchestrates:
   - Create Ventas record
   - Create VentasDetalles for each line item
   - Update Productos stock
   - Create corresponding Movimientos (inventory transactions)
   - Create Asientos (journal entries) if accounting enabled
   - Update Terceros client balance
   - Commit all in single transaction (atomic)
5. Frontend: React Query cache updated via response or invalidation
6. Real-time: SSE notifies other users of inventory changes

**State Management:**

- **App State** (Zustand): `token`, `user`, `tenantId`, `rolEnTenant`
  - Persistent to localStorage
  - Synchronized across tabs via `storage` listener
  - Single source of truth for auth context
- **Server State** (React Query): All API responses
  - Cached per endpoint
  - Stale time: 30s
  - Invalidated on mutations
  - Retry: 1 attempt on failure
- **Local UI State** (React useState): Form inputs, modal open/close, pagination
  - Not persisted
  - Reset on navigation

## Key Abstractions

**Service Classes (Pattern: Façade + Repository):**
- Purpose: Encapsulate all business logic for a domain
- Examples: `ServicioProductos`, `ServicioVentas`, `ServicioTenants`, `ServicioContabilidad`
- Pattern:
  ```python
  class ServicioProductos:
      def __init__(self, db: Session):
          self.db = db

      def crear_producto(self, tenant_id: UUID, data: ProductoCreate) -> Productos:
          # Validate, create, update related entities, commit atomically
          ...
  ```
- Methods are business operations (not CRUD): `crear_venta()`, `anular_factura()`, `registrar_pago()`

**DTO Schemas (Pydantic):**
- Purpose: Validate and serialize request/response data
- Location: `backend/app/datos/esquemas.py`
- Pattern: Separate `*Create`, `*Update`, `*Response` classes per entity
- Example:
  ```python
  class ProductoCreate(BaseModel):
      nombre: str
      precio_unitario: Decimal
      categoria: str

  class ProductoResponse(ProductoCreate):
      id: UUID
      tenant_id: UUID
      created_at: datetime
  ```

**RLS Policies (PostgreSQL):**
- Purpose: Enforce tenant isolation at DB level
- Implementation: `SET LOCAL app.tenant_id_actual` per transaction
- Every table: CREATE POLICY `tenant_isolation_*` on SELECT/INSERT/UPDATE/DELETE
- Schema reference: `backend/app/middleware/tenant_context.py:RLS_POLICIES_SQL`

**JWT Tokens:**
- **Access Token**: 15-minute lifespan, contains `user_id`, `tenant_id` (if selected), `es_superadmin`, `rol_en_tenant`
- **Refresh Token**: 7-day lifespan, used to obtain new access token
- Issued by: `backend/app/utils/seguridad.py:create_access_token()`
- Verified by: `get_current_user()` dependency in protected routes

**Superadmin Impersonation:**
- Superadmin calls `POST /api/v1/superadmin/impersonate/{user_id}/{tenant_id}`
- Backend: Creates 15-minute token without refresh capability
- Frontend: Stores in `authStore.impersonation` state
- UI: Shows banner "Impersonating User X in Tenant Y"
- On end: Restore original superadmin token from stored backup

## Entry Points

**Backend:**
- **`backend/app/main.py`** - FastAPI app creation, middleware setup, router registration
  - Lifespan events: startup DB checks, shutdown pool cleanup
  - Exception handlers: validation errors, HTTP errors, generic exceptions
  - Static files: Tenant logos at `/static/`

**Frontend:**
- **`frontend/src/main.tsx`** - React entry point, ClerkProvider wrapper, root render
- **`frontend/src/App.tsx`** - BrowserRouter with all routes, RequireAuth wrapper
- **`frontend/src/index.css`** - Tailwind CSS initialization

**API Entry Points (by module):**
- Auth: `backend/app/rutas/auth.py` - /api/v1/auth/* (login, refresh, select-tenant, change-password)
- Tenants: `backend/app/rutas/tenants.py` - /api/v1/tenants/* (CRUD + registration)
- Products: `backend/app/rutas/productos.py` - /api/v1/productos/*
- Sales: `backend/app/rutas/ventas.py` - /api/v1/ventas/*
- Inventory: `backend/app/rutas/inventarios.py` - /api/v1/inventarios/*
- Accounting: `backend/app/rutas/contabilidad.py` - /api/v1/contabilidad/*
- CRM: `backend/app/rutas/crm.py` - /api/v1/* (deals, contacts, activity)
- Support: `backend/app/rutas/pqrs.py` - /api/v1/pqrs/*
- Real-time: `backend/app/rutas/sse.py` - /api/v1/sse/* (EventSource for live updates)

## Error Handling

**Strategy:** Fail fast with clear errors; log detailed context; avoid exposing internals in production

**Backend Patterns:**
- Validation errors (422): Pydantic DTO validation failure → `@app.exception_handler(RequestValidationError)` returns error details
- Business errors (400): ValueError raised in service → `@app.exception_handler(ValueError)` returns "Bad Request" with message
- Auth errors (401/403): HTTPException from `get_current_user()` dependency
- Not found (404): HTTPException from route handler when entity doesn't exist
- Rate limit (429): SlowAPI limiter → `@app.exception_handler(RateLimitExceeded)`
- Server errors (500): Unhandled exceptions → `@app.exception_handler(Exception)` returns generic error (Sentry logs details)

**Frontend Patterns:**
- API errors: Axios interceptor on 401 → token refresh or redirect to login
- Other errors: Caught in React component, displayed as toast/modal
- Async operations: React Query handles retries, loading/error states

**Logging:**
- Structured JSON logging via `python-json-logger`
- Context: `request_id`, `user_id`, `tenant_id`, `method`, `path`, `duration_ms`
- Levels: DEBUG (SQL in dev only), INFO (request/response), WARNING (validation, rate limit), ERROR (exceptions)
- Production: Sentry captures error stack traces + context variables

## Cross-Cutting Concerns

**Logging:**
- Backend: `setup_logger(__name__)` in every module
- Frontend: `useAnalytics()` hook for page view tracking
- Context: Request ID added to all backend logs via `RequestContextMiddleware`

**Validation:**
- Backend: Pydantic schemas in `esquemas.py` + service-level invariants (e.g., price > 0)
- Frontend: HTML5 form validation + Zod/custom validators in forms

**Authentication:**
- Backend: JWT verification in `get_current_user()` dependency; checked on every protected route
- Frontend: Token stored in Zustand + localStorage; Axios adds to every request
- Real-time check: Middleware extracts `X-Tenant-ID`; RLS enforces at DB

**Authorization (Role-based):**
- Backend: `RoleGuard` dependency checks `rol_en_tenant` against allowed roles (admin, operador, contador)
- Frontend: `<RoleGuard allowedRoles={[...]}>` wrapper component hides pages from non-admin
- Superadmin: Bypasses all role checks via `es_superadmin=true` flag in JWT

**Audit Trail:**
- Automatic: SQLAlchemy event listeners capture all INSERT/UPDATE/DELETE
- Fields tracked: `usuario_id` (who), `timestamp` (when), `accion` (what), `registros_afectados` (affected rows)
- Stored in: `AuditLog` table per tenant
- Accessible: `GET /api/v1/tenants/{tenant_id}/audit-logs`

**Data Integrity:**
- Transactions: All service methods use implicit transactions (autocommit=False)
- Foreign keys: PostgreSQL enforces referential integrity
- Constraints: Check constraints for enums (estado, rol, categoria)
- Soft deletes: `eliminado_en` timestamp instead of hard DELETE for audit trail

---

*Architecture analysis: 2026-02-27*
