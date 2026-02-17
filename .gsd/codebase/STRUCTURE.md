# Structure Analysis: MERX/Chandelier ERP System

## Project Root Layout

```
merx_v2/
├── .env                        # Environment variables (not committed)
├── .env.production.example     # Production environment template
├── .env.railway.example        # Railway deployment template
├── .gitignore
├── .python-version             # Python version specification
├── alembic.ini                 # Alembic configuration
├── docker-compose.yml          # Docker orchestration
├── Dockerfile.backend          # Backend container
├── Dockerfile.frontend         # Frontend container  
├── Dockerfile.railway          # Railway-specific container
├── nixpacks.toml               # Railway build config
├── railway.json                # Railway deployment config
├── railway.toml
├── Procfile                    # Process declaration
├── requirements.txt            # Python dependencies
├── runtime.txt                 # Python runtime version
├── pyproject.toml              # Project metadata
├── uv.lock                     # UV package manager lock
├── README.md
├── QUICKSTART.md
├── CLAUDE.md                   # PRD/Technical spec
├── DEPLOYMENT.md
├── FREE-TIER-DEPLOY.md
├── IMPLEMENTATION_SUMMARY.md
├── nginx.conf                  # Nginx reverse proxy config
├── analyze_logs.py             # Log analysis utility
│
├── alembic/                    # Database migrations
│   ├── env.py
│   ├── versions/
│   │   ├── 5600c67af29d_initial.py
│   │   ├── 23fa462778a8_p0_contabilidad_fundamentos.py
│   │   ├── 470bb2b033d8_add_audit_columns_to_movimientos_.py
│   │   ├── b4c55005691b_add_crm_tables.py
│   │   ├── c7eb4b5e1ff2_fase1_seguridad_audit_logs_ultimo_acceso.py
│   │   └── ... (other migrations)
│
├── backend/                    # FastAPI backend
│   ├── __init__.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI application entry
│   │   ├── config.py           # Settings/configuration
│   │   ├── datos/              # Data layer
│   │   ├── rutas/              # API routes
│   │   ├── servicios/          # Business logic services
│   │   ├── middleware/         # FastAPI middleware
│   │   └── utils/              # Utilities
│   └── tests/                  # Backend tests
│
├── frontend/                   # React frontend
│   ├── package.json
│   ├── src/
│   │   ├── main.tsx            # React entry point
│   │   ├── App.tsx             # Root component with routing
│   │   ├── index.css           # Global styles
│   │   ├── api/                # API client
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks
│   │   ├── pages/              # Page components
│   │   ├── stores/             # Zustand stores
│   │   ├── types/              # TypeScript types
│   │   ├── utils/              # Utility functions
│   │   └── assets/             # Static assets
│   └── ...
│
├── logs/                       # Application logs
├── .claude/                    # Claude AI configuration
├── .kilocode/                  # KiloCode configuration
├── .gsd/                       # GSD framework files
└── gsd-template/               # GSD template files
```

---

## Backend Structure

### Directory: `backend/app/`

```
backend/app/
├── __init__.py
├── main.py                     # FastAPI app factory, middleware, routers
├── config.py                   # Pydantic Settings, environment validation
│
├── datos/                      # Data Access Layer
│   ├── __init__.py
│   ├── db.py                   # SQLAlchemy engine, session, RLS setup
│   ├── modelos.py              # Business entity models (Ventas, Productos, etc.)
│   ├── modelos_tenant.py       # Global models (Tenants, Planes, Usuarios)
│   ├── modelos_crm.py          # CRM-specific models
│   ├── esquemas.py             # Pydantic schemas for validation
│   ├── mixins.py               # Reusable model mixins (TenantMixin, etc.)
│   └── audit_listeners.py      # SQLAlchemy event listeners for audit
│
├── rutas/                      # API Route Handlers (Presentation Layer)
│   ├── __init__.py             # Router exports
│   ├── auth.py                 # Authentication endpoints
│   ├── usuarios.py             # User management
│   ├── tenants.py              # Tenant management (superadmin)
│   ├── terceros.py             # Third parties (clients/suppliers)
│   ├── productos.py            # Product catalog
│   ├── inventarios.py          # Inventory management
│   ├── ventas.py               # Sales orders
│   ├── compras.py              # Purchase orders
│   ├── facturas.py             # Invoice generation
│   ├── cotizaciones.py         # Quotations
│   ├── recetas.py              # Recipes/BOM
│   ├── ordenes_produccion.py   # Production orders
│   ├── contabilidad.py         # Accounting entries
│   ├── cuentas_contables.py    # Chart of accounts
│   ├── configuracion_contable.py
│   ├── periodos_contables.py   # Accounting periods
│   ├── cartera.py              # Receivables/payables
│   ├── medios_pago.py          # Payment methods
│   ├── crm.py                  # CRM endpoints
│   ├── reportes.py             # Reports
│   └── health.py               # Health check endpoints
│
├── servicios/                  # Business Logic Layer
│   ├── __init__.py
│   ├── servicio_inventario.py  # Stock, movements, weighted average cost
│   ├── servicio_ventas.py      # Sales operations
│   ├── servicio_productos.py   # Product operations
│   ├── servicio_contabilidad.py # Accounting operations
│   ├── servicio_crm.py         # CRM operations
│   ├── servicio_tenants.py     # Tenant management
│   ├── servicio_audit.py       # Audit logging
│   ├── servicio_pdf.py         # PDF generation
│   └── servicio_almacenamiento.py # S3/R2 storage
│
├── middleware/                 # FastAPI Middleware
│   ├── __init__.py
│   ├── tenant_context.py       # RLS context, maintenance mode
│   └── user_context.py         # User context for audit
│
└── utils/                      # Utilities
    ├── __init__.py
    ├── logger.py               # Structured logging setup
    ├── seguridad.py            # JWT, password hashing
    ├── rate_limiter.py         # slowapi configuration
    ├── seeders.py              # Database seeding
    ├── constantes_contables.py # Accounting constants
    └── secuencia_helper.py     # Document numbering
```

### Key Files Analysis

#### `main.py` (571 lines)
- FastAPI application factory
- Lifespan context manager for startup/shutdown
- Middleware stack registration (ordered)
- Global exception handlers
- Router inclusion with prefixes
- Sentry integration (production only)
- Rate limiting setup

#### `config.py` (381 lines)
- Pydantic Settings for environment validation
- Database URL resolution (DB_URL / DATABASE_URL)
- Security validators (SECRET_KEY entropy, DEBUG in production)
- CORS validation for production
- Computed properties (cors_origins_list, is_production)

#### `datos/db.py` (187 lines)
- SQLAlchemy engine with connection pooling
- SessionLocal factory
- RLS context functions
- Dependency injection helpers (`get_db()`)
- TenantSession context manager
- Event listener for automatic RLS on transaction begin

---

## Frontend Structure

### Directory: `frontend/src/`

```
frontend/src/
├── main.tsx                    # React entry, renders App
├── App.tsx                     # Root component, routing setup
├── index.css                   # Global Tailwind styles
│
├── api/                        # API Layer
│   ├── client.ts               # Axios instance, interceptors
│   └── endpoints.ts            # API endpoint functions
│
├── components/                 # Reusable Components
│   ├── auth/
│   │   ├── RoleGuard.tsx       # Role-based access control
│   │   └── SuperadminGuard.tsx # Superadmin routes
│   ├── layout/
│   │   └── AppShell.tsx        # Main layout wrapper
│   ├── crm/                    # CRM-specific components
│   ├── ui/                     # Generic UI components
│   ├── DocumentForm.tsx        # Form for invoices/quotes
│   ├── DocumentDetail.tsx      # Document viewer
│   ├── ImpersonationBanner.tsx # Superadmin impersonation
│   └
