# Architecture Analysis: MERX/Chandelier ERP System

## Overview

MERX (also branded as Chandelier) is a **multi-tenant SaaS ERP/POS system** designed for small and medium enterprises (PyMEs) in Colombia, specifically targeting candle-making microbusinesses. The system follows a **modular monolithic architecture** with PostgreSQL Row-Level Security (RLS) for tenant isolation.

---

## Architectural Pattern

### Monolithic Modular Architecture

The system is a **monolithic application** with clear module boundaries, deployed as a single unit but organized with internal separation of concerns. This is evident from:

- Single FastAPI application entry point (`backend/app/main.py`)
- Unified database schema with tenant isolation at the database level
- Modular organization within the monolith (auth, inventory, accounting, sales, etc.)

### Multi-Tenancy Strategy

**Database-per-tenant is NOT used.** Instead, the system employs:

1. **Shared Database with Row-Level Security (RLS)**
   - All tenant data lives in the same database
   - PostgreSQL RLS policies enforce isolation at the database level
   - Tenant ID stored in `app.tenant_id_actual` session variable

2. **Context Propagation via Middleware**
   - `TenantContextMiddleware` extracts `X-Tenant-ID` header
   - Sets PostgreSQL session variable for RLS: `SET LOCAL app.tenant_id_actual = :tenant_id`
   - ContextVar pattern for in-request tenant tracking

3. **Mixin-Based Tenant Scoping**
   - `TenantMixin` adds `tenant_id` foreign key to all tenant-scoped tables
   - `TenantAuditMixin` combines tenant scoping with soft deletes and audit fields

---

## Layer Organization

### Backend (FastAPI + SQLAlchemy)

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  FastAPI Routes (backend/app/rutas/)                        │
│  - Request validation (Pydantic schemas)                    │
│  - Authentication/Authorization                             │
│  - HTTP response formatting                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                      │
│  Services (backend/app/servicios/)                          │
│  - Business rules enforcement                               │
│  - Transaction management                                   │
│  - Cross-entity operations                                  │
│  - Domain calculations (weighted average cost, margins)     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                         │
│  SQLAlchemy ORM (backend/app/datos/)                        │
│  - Model definitions (modelos.py, modelos_tenant.py)        │
│  - Database session management (db.py)                      │
│  - RLS context setup                                        │
│  - Mixins for cross-cutting concerns                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                            │
│  PostgreSQL 16                                              │
│  - Row-Level Security policies                              │
│  - Foreign key constraints                                  │
│  - Check constraints for data integrity                     │
│  - Composite indexes for tenant-scoped queries              │
└─────────────────────────────────────────────────────────────┘
```

### Frontend (React + TypeScript)

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  Pages (frontend/src/pages/)                                │
│  - Route-level components                                   │
│  - Page composition                                         │
│  - Route guards (RequireAuth, RoleGuard)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    COMPONENT LAYER                           │
│  Components (frontend/src/components/)                      │
│  - Reusable UI components                                   │
│  - Layout (AppShell, navigation)                            │
│  - Feature components (forms, tables, modals)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STATE MANAGEMENT LAYER                    │
│  Zustand Stores (frontend/src/stores/)                      │
│  - authStore: Authentication state, tenant selection        │
│  - posStore: POS cart state                                 │
│  - Persisted to localStorage                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA FETCHING LAYER                       │
│  API Client + React Query (frontend/src/api/)               │
│  - Axios client with interceptors                           │
│  - Token refresh handling                                   │
│  - Tenant ID header injection                               │
│  - Query caching and invalidation                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Patterns Used

### 1. Repository Pattern (Implicit via SQLAlchemy ORM)
- Models abstract database operations
- Session-based database access via dependency injection

### 2. Service Layer Pattern
- Business logic encapsulated in service classes
- Example: `ServicioInventario`, `ServicioContabilidad`, `ServicioVentas`
- Services receive `db: Session` and `tenant_id: UUID` in constructor

### 3. Dependency Injection (FastAPI)
- `get_db()` generator for database sessions
- Authentication dependencies for protected routes
- Middleware injection for tenant context

### 4. Mixin Pattern
- `TenantMixin`: Adds tenant_id column
- `SoftDeleteMixin`: Adds deleted_at/deleted_by
- `AuditMixin`: Adds created_at/updated_at/created_by/updated_by
- `TenantAuditMixin`: Combines all three

### 5. Middleware Chain Pattern
- Request tracking → Security headers → Tenant context → User context → CORS
- Each middleware handles a specific cross-cutting concern

### 6. Context Variables Pattern
- Python `contextvars.ContextVar` for tenant/user context
- Allows access from anywhere in the request lifecycle
- Used by SQLAlchemy event listeners for RLS

### 7. Unit of Work Pattern
- SQLAlchemy session acts as Unit of Work
- Changes tracked, committed explicitly in services

### 8. Observer Pattern (Audit Logging)
- SQLAlchemy event listeners for automatic audit trail
- `register_audit_listeners()` hooks into flush events

---

## Module Boundaries and Responsibilities

### Backend Modules

| Module | Location | Responsibility |
|--------|----------|----------------|
| **Authentication** | `rutas/auth.py`, `utils/seguridad.py` | JWT tokens, password hashing, login/logout |
| **Multi-Tenancy** | `middleware/tenant_context.py`, `modelos_tenant.py` | Tenant isolation, RLS context, subscription management |
| **Inventory** | `rutas/inventarios.py`, `servicios/servicio_inventario.py` | Stock management, movements, weighted average cost |
| **Products** | `rutas/productos.py`, `servicios/servicio_productos.py` | Product catalog, pricing, categories |
| **Sales** | `rutas/ventas.py`, `servicios/servicio_ventas.py` | Sales orders, invoice generation |
| **
