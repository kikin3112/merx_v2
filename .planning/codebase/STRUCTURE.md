# Codebase Structure

**Analysis Date:** 2026-02-15

## Directory Layout

```
merx_v2/
├── backend/                           # Python FastAPI application
│   ├── app/
│   │   ├── main.py                   # FastAPI app initialization, middleware setup, routes inclusion
│   │   ├── config.py                 # Settings from environment (DB, Redis, CORS, etc)
│   │   ├── datos/                    # Data layer - models and database setup
│   │   │   ├── db.py                 # SQLAlchemy engine, session, RLS event listeners
│   │   │   ├── modelos.py            # Core business models (Usuarios, Terceros, Ventas, etc)
│   │   │   ├── modelos_tenant.py     # Tenant-specific models (Tenants, Plans, Subscriptions)
│   │   │   ├── modelos_crm.py        # CRM models (Deals, Activities)
│   │   │   ├── esquemas.py           # Pydantic request/response schemas
│   │   │   ├── mixins.py             # Reusable SQLAlchemy mixins (TenantMixin, AuditMixin)
│   │   │   ├── audit_listeners.py    # Event listeners for automatic audit field population
│   │   │   └── __init__.py
│   │   ├── rutas/                    # API route handlers
│   │   │   ├── auth.py               # Login, refresh, user selection
│   │   │   ├── tenants.py            # Tenant registration, management (superadmin)
│   │   │   ├── usuarios.py           # User management (CRUD)
│   │   │   ├── terceros.py           # Customers/suppliers/third parties
│   │   │   ├── productos.py          # Product CRUD with cost calculation
│   │   │   ├── recetas.py            # BOM (recipes) and production
│   │   │   ├── inventarios.py        # Stock movements and adjustments
│   │   │   ├── ventas.py             # Sales transactions
│   │   │   ├── facturas.py           # Invoice issuance, PDF generation, accounting
│   │   │   ├── cotizaciones.py       # Quotes management and conversion to invoices
│   │   │   ├── contabilidad.py       # Journal entries (asientos)
│   │   │   ├── configuracion_contable.py  # Accounting config per tenant
│   │   │   ├── periodos_contables.py     # Accounting periods (month/year)
│   │   │   ├── cuentas_contables.py      # Chart of accounts (PUC Colombia)
│   │   │   ├── cartera.py            # Accounts receivable/payable tracking
│   │   │   ├── crm.py                # Customer relationships, deals, activities
│   │   │   ├── reportes.py           # Sales, inventory, financial reports
│   │   │   ├── medios_pago.py        # Payment methods
│   │   │   ├── compras.py            # Purchase orders (minimal, MVP phase)
│   │   │   ├── ordenes_produccion.py # Production orders
│   │   │   ├── health.py             # Health checks for orchestration
│   │   │   └── __init__.py
│   │   ├── servicios/                # Business logic layer
│   │   │   ├── servicio_inventario.py       # Stock movements, weighted avg costing, recipes
│   │   │   ├── servicio_contabilidad.py     # Journal entries, balance validation
│   │   │   ├── servicio_pdf.py              # PDF generation using ReportLab
│   │   │   ├── servicio_almacenamiento.py   # S3/R2 file uploads
│   │   │   ├── servicio_productos.py        # Product operations
│   │   │   ├── servicio_ventas.py           # Sales logic, pricing
│   │   │   ├── servicio_crm.py              # CRM operations
│   │   │   ├── servicio_tenants.py          # Tenant management, plan upgrades
│   │   │   ├── servicio_audit.py            # Audit log retrieval
│   │   │   └── __init__.py
│   │   ├── middleware/               # HTTP middleware for cross-cutting concerns
│   │   │   ├── tenant_context.py     # RLS tenant isolation, maintenance mode cache
│   │   │   ├── user_context.py       # User ID context for auditing
│   │   │   └── __init__.py
│   │   ├── utils/                    # Shared utilities and helpers
│   │   │   ├── logger.py             # Structured logging with request context
│   │   │   ├── seguridad.py          # JWT token generation/validation, RBAC decorators
│   │   │   ├── rate_limiter.py       # slowapi rate limiting (100 req/min)
│   │   │   ├── secuencia_helper.py   # Atomic sequence generation for document numbers
│   │   │   ├── constantes_contables.py  # Accounting constants (PUC codes)
│   │   │   ├── seeders.py            # Initial data seeding (PUC, default clients)
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── alembic/                      # Database migration scripts
│   │   ├── versions/                 # Migration files (auto-generated or manual)
│   │   ├── env.py                    # Alembic environment config
│   │   ├── script.py.mako            # Template for new migrations
│   │   └── alembic.ini               # Alembic configuration
│   ├── requirements.txt              # Python dependencies (FastAPI, SQLAlchemy, etc)
│   ├── pyproject.toml                # Project metadata and tool config
│   └── Dockerfile                    # Container build for backend
│
├── frontend/                         # React + TypeScript application
│   ├── src/
│   │   ├── main.tsx                  # React root mount point
│   │   ├── App.tsx                   # Router setup, route definitions, auth guards
│   │   ├── index.css                 # Global Tailwind styles
│   │   ├── api/
│   │   │   ├── client.ts             # Axios instance with auth interceptors, token refresh logic
│   │   │   ├── endpoints.ts          # API endpoint functions grouped by domain (auth, products, etc)
│   │   │   └── __init__.ts
│   │   ├── components/               # Reusable React components
│   │   │   ├── layout/
│   │   │   │   ├── AppShell.tsx      # Main layout wrapper with sidebar + main content
│   │   │   │   ├── Sidebar.tsx       # Navigation sidebar (responsive)
│   │   │   │   ├── BottomNav.tsx     # Mobile bottom navigation bar
│   │   │   │   └── MobileDrawer.tsx  # Mobile menu drawer
│   │   │   ├── auth/
│   │   │   │   ├── RoleGuard.tsx     # Route guard checking user role
│   │   │   │   └── SuperadminGuard.tsx # Route guard for superadmin-only pages
│   │   │   ├── ui/
│   │   │   │   ├── DataCard.tsx      # KPI card component
│   │   │   │   ├── Modal.tsx         # Generic modal wrapper
│   │   │   │   ├── SearchInput.tsx   # Search input with debounce
│   │   │   │   └── (other generic UI components)
│   │   │   ├── crm/
│   │   │   │   ├── KanbanBoard.tsx   # Deal stage kanban view
│   │   │   │   ├── ActivityFeed.tsx  # Activity timeline
│   │   │   │   └── DealDetailModal.tsx
│   │   │   ├── DocumentForm.tsx      # Shared invoice/quote form component
│   │   │   ├── DocumentDetail.tsx    # Shared invoice/quote detail view
│   │   │   ├── PeriodSelector.tsx    # Month/year selector for reports
│   │   │   ├── ImpersonationBanner.tsx # Banner when superadmin impersonates user
│   │   │   └── __init__.ts
│   │   ├── pages/                    # Route page components
│   │   │   ├── LoginPage.tsx         # Authentication form
│   │   │   ├── SelectTenantPage.tsx  # Tenant selection after login
│   │   │   ├── DashboardPage.tsx     # Main dashboard with KPIs
│   │   │   ├── ProductosPage.tsx     # Product list + CRUD
│   │   │   ├── TercerosPage.tsx      # Customer/supplier list
│   │   │   ├── InventarioPage.tsx    # Stock movements, adjustments
│   │   │   ├── RecetasPage.tsx       # BOM management + production
│   │   │   ├── VentasPage.tsx        # Sales transaction list
│   │   │   ├── FacturasPage.tsx      # Invoice list + creation
│   │   │   ├── CotizacionesPage.tsx  # Quotes
│   │   │   ├── ContabilidadPage.tsx  # Journal entries (asientos)
│   │   │   ├── CarteraPage.tsx       # Accounts receivable/payable
│   │   │   ├── ReportesPage.tsx      # Sales, inventory, financial reports
│   │   │   ├── ConfigPage.tsx        # Tenant settings (users, accounting config)
│   │   │   ├── POSPage.tsx           # Point of sale interface
│   │   │   ├── CRMPage.tsx           # Customer relationships dashboard
│   │   │   ├── TenantsPage.tsx       # Superadmin tenant management
│   │   │   └── __init__.ts
│   │   ├── stores/                   # Zustand state management
│   │   │   ├── authStore.ts          # Auth state (token, user, tenant, impersonation)
│   │   │   ├── posStore.ts           # POS session state (shopping cart)
│   │   │   └── __init__.ts
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── useMediaQuery.ts      # Responsive design queries (mobile/tablet/desktop)
│   │   │   ├── useNavigation.ts      # Navigation helper
│   │   │   └── __init__.ts
│   │   ├── types/                    # TypeScript type definitions
│   │   │   ├── index.ts              # All shared interfaces (User, Tenant, Producto, etc)
│   │   │   └── __init__.ts
│   │   ├── utils/                    # Utility functions
│   │   │   ├── formatters.ts         # Number/currency formatting
│   │   │   └── validators.ts         # Form validation helpers
│   │   ├── assets/                   # Static images, icons
│   │   └── __init__.ts
│   ├── public/                       # Static files (favicon, etc)
│   ├── vite.config.ts                # Vite bundler configuration
│   ├── tsconfig.json                 # TypeScript configuration
│   ├── tailwind.config.js            # Tailwind CSS theme customization
│   ├── package.json                  # Node dependencies
│   ├── Dockerfile                    # Container build for frontend
│   └── .eslintrc.json                # ESLint rules
│
├── alembic/                          # Database migrations (root level, shared with backend)
│   ├── versions/                     # Individual migration files
│   ├── env.py
│   └── script.py.mako
│
├── docker-compose.yml                # Local dev environment (PostgreSQL, Redis, app services)
├── nginx.conf                        # Reverse proxy config for production
├── Dockerfile.backend                # Backend container image
├── Dockerfile.frontend               # Frontend container image
├── CLAUDE.md                         # Project requirements and PRD
├── QUICKSTART.md                     # Developer onboarding guide
├── DEPLOYMENT.md                     # Production deployment guide
├── FREE-TIER-DEPLOY.md               # Budget deployment alternatives
├── IMPLEMENTATION_SUMMARY.md         # Feature completion status
├── pyproject.toml                    # Python project config (uv tool)
├── uv.lock                           # Locked dependency versions
├── .env                              # Development environment (NEVER commit secrets)
├── .env.production.example           # Template for production environment
├── .gitignore                        # Git exclusions
├── .python-version                   # Python version (3.11+)
└── README.md                         # Project overview
```

## Directory Purposes

**backend/app/datos/:**
- Purpose: Database models and schema definitions
- Contains: SQLAlchemy ORM models, Pydantic schemas, database setup
- Key files: `modelos.py` (20+ core models), `esquemas.py` (request/response validation), `db.py` (engine + RLS setup)

**backend/app/rutas/:**
- Purpose: HTTP endpoint handlers
- Contains: FastAPI route handlers accepting requests and calling services
- Key files: `facturas.py` (invoice endpoints), `productos.py` (product CRUD), `contabilidad.py` (accounting)
- Pattern: Each router file handles one domain (e.g., `/api/v1/facturas/*` in facturas.py)

**backend/app/servicios/:**
- Purpose: Business logic implementation
- Contains: Domain-specific service classes with methods for operations
- Key files: `servicio_inventario.py` (stock management), `servicio_contabilidad.py` (journal entries)
- Pattern: Service classes take DB session and tenant_id in constructor, expose public methods

**backend/app/middleware/:**
- Purpose: HTTP middleware for cross-cutting concerns
- Contains: Tenant isolation (RLS), user context, security headers
- Key files: `tenant_context.py` (extracts/validates X-Tenant-ID header), `user_context.py` (sets audit user)

**backend/app/utils/:**
- Purpose: Shared utilities and helpers
- Contains: Logging, JWT token handling, RBAC decorators, rate limiting, seeders
- Key files: `seguridad.py` (authentication), `logger.py` (structured logging), `seeders.py` (initial data)

**frontend/src/pages/:**
- Purpose: Full-page components corresponding to routes
- Contains: Page-level containers that fetch data and render sections
- Pattern: One component per route, imports smaller reusable components
- Example: `FacturasPage.tsx` renders invoice list and form, imports `DocumentForm.tsx` and `DocumentDetail.tsx`

**frontend/src/components/:**
- Purpose: Reusable UI components
- Contains: Buttons, modals, cards, forms, layout sections
- Subdirectories: `layout/` (AppShell, Sidebar), `auth/` (route guards), `ui/` (generic components), `crm/` (CRM features)

**frontend/src/stores/:**
- Purpose: Zustand state management
- Contains: Global state (auth, user, tenant) and local feature state (POS cart)
- Key files: `authStore.ts` (login/logout/token refresh), `posStore.ts` (shopping cart items)

**frontend/src/api/:**
- Purpose: Backend API communication
- Contains: Axios instance with interceptors, endpoint function wrappers
- Key files: `client.ts` (axios + token refresh logic), `endpoints.ts` (organized API calls by domain)

**frontend/src/types/:**
- Purpose: TypeScript type definitions
- Contains: Shared interfaces matching backend Pydantic schemas
- Key files: `index.ts` (all types: User, Tenant, Producto, Factura, etc)

## Key File Locations

**Entry Points:**
- Backend: `backend/app/main.py` - FastAPI app initialization
- Frontend: `frontend/src/main.tsx` - React DOM mount
- Vite dev server: `frontend/vite.config.ts`

**Configuration:**
- Backend settings: `backend/app/config.py` - environment variables, database, CORS, JWT secrets
- Tailwind CSS: `frontend/tailwind.config.js` - design system colors, spacing
- TypeScript: `frontend/tsconfig.json` - strict mode enabled, path aliases
- Database migrations: `alembic/versions/` - numbered migration files

**Core Logic:**
- Models: `backend/app/datos/modelos.py` - business entity definitions
- Services: `backend/app/servicios/servicio_inventario.py`, `servicio_contabilidad.py`
- Routers: `backend/app/rutas/facturas.py`, `productos.py`, `contabilidad.py`

**Testing:**
- Backend tests: Not found in structure (integration via endpoints)
- Frontend tests: Not found in structure (cypress/vitest setup not apparent)

**Authentication/Security:**
- JWT handling: `backend/app/utils/seguridad.py` - token generation, validation, RBAC decorators
- Frontend auth store: `frontend/src/stores/authStore.ts` - token persistence, refresh flow
- API client: `frontend/src/api/client.ts` - request/response interceptors for auth

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `servicio_inventario.py`, `tenant_context.py`)
- TypeScript: `camelCase.ts` or `PascalCase.tsx` (e.g., `useMediaQuery.ts`, `AppShell.tsx`)
- Components: `PascalCase.tsx` (e.g., `DocumentForm.tsx`, `RoleGuard.tsx`)
- Hooks: `use` prefix in camelCase (e.g., `useMediaQuery.ts`, `useNavigation.ts`)

**Directories:**
- Feature directories: plural snake_case (e.g., `rutas/`, `servicios/`, `modelos/`)
- Component subdirectories: plural snake_case (e.g., `layout/`, `auth/`, `crm/`)

**Classes/Functions:**
- Python classes: `PascalCase` (e.g., `ServicioInventario`, `TenantContextMiddleware`)
- Python functions: `snake_case` (e.g., `crear_asiento()`, `obtener_stock_disponible()`)
- TypeScript functions: `camelCase` (e.g., `getPersistedAuth()`, `updatePersistedTokens()`)
- React components: `PascalCase` (e.g., `AppShell`, `RoleGuard`)

**Database/Models:**
- Table names: plural snake_case (e.g., `usuarios`, `productos`, `facturas`)
- Column names: snake_case (e.g., `fecha_emision`, `numero_venta`, `total_venta`)
- Enums: `PascalCase` with all-caps variants (e.g., `EstadoVenta.PENDIENTE`)

**Routes:**
- Pattern: `/api/v1/{resource}/{action}`
- Examples: `/api/v1/facturas` (list/create), `/api/v1/facturas/{id}` (get), `/api/v1/facturas/{id}/emitir` (action)

## Where to Add New Code

**New Feature (Domain):**
1. **Models:** Add to `backend/app/datos/modelos.py` with TenantAuditMixin
2. **Schema:** Add Pydantic classes to `backend/app/datos/esquemas.py` (Create, Update, Response)
3. **Service:** Create `backend/app/servicios/servicio_<domain>.py` with class taking db and tenant_id
4. **Routes:** Create `backend/app/rutas/<domain>.py` with FastAPI router
5. **Frontend:** Create `frontend/src/pages/<Domain>Page.tsx` and import in `App.tsx` routes

**New Component (UI):**
1. **If reusable:** Create in `frontend/src/components/ui/<ComponentName>.tsx`
2. **If feature-specific:** Create in `frontend/src/components/<feature>/<ComponentName>.tsx`
3. **If page-level:** Create in `frontend/src/pages/<FeatureName>Page.tsx`
4. **Types:** Add interfaces to `frontend/src/types/index.ts`

**New Utility:**
- Backend: `backend/app/utils/<utility_name>.py` if general, or subfolder if domain-specific
- Frontend: `frontend/src/utils/<utility_name>.ts` or `frontend/src/hooks/use<Feature>.ts` for hooks

**New Route/Endpoint:**
1. Create handler in existing or new `backend/app/rutas/<domain>.py`
2. Use route prefix: `@router.get("/{id}")` (prefix added at registration in main.py)
3. Validate input with Pydantic schema
4. Call service layer for business logic
5. Return response schema

**Database Migration:**
1. Make model change in `backend/app/datos/modelos.py`
2. Run `alembic revision --autogenerate -m "description"`
3. Review generated file in `alembic/versions/`
4. Run `alembic upgrade head` to apply

## Special Directories

**alembic/versions/:**
- Purpose: Database migration history
- Generated: `alembic revision` command creates new files
- Committed: YES - migrations are tracked in git
- Pattern: Numbered files (e.g., `001_initial.py`, `002_add_products.py`)

**frontend/node_modules/:**
- Purpose: Installed npm dependencies
- Generated: `npm install` or `yarn install`
- Committed: NO - .gitignore excludes it, use lock file instead
- Contains: React, Tailwind, Axios, etc

**backend/.venv/ or venv/:**
- Purpose: Python virtual environment
- Generated: `python -m venv venv` or `uv venv`
- Committed: NO - .gitignore excludes it
- Contains: pip packages, Python executable

**logs/:**
- Purpose: Application runtime logs
- Generated: By logger when app runs
- Committed: NO - .gitignore excludes
- Cleared: Periodically or on deployment

**.env:**
- Purpose: Development environment variables
- Generated: Copy from .env.example and populate
- Committed: NO - contains secrets (API keys, DB passwords)
- Never add to git: DATABASE_URL, JWT_SECRET, STRIPE_KEY, etc

---

*Structure analysis: 2026-02-15*
