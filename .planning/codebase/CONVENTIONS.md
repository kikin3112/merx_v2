# Coding Conventions

**Analysis Date:** 2026-02-15

## Naming Patterns

**Files:**
- Python: `snake_case` (e.g., `seguridad.py`, `logger.py`, `modelos_tenant.py`)
- TypeScript/React: `camelCase` for files and folders (e.g., `authStore.ts`, `useNavigation.ts`, `Sidebar.tsx`)
- Test files: Python `test_*.py` (e.g., `test_rbac_backend.py`, `test_inventario_concurrency.py`)
- Route files: Spanish names in snake_case (e.g., `productos.py`, `contabilidad.py`, `facturas.py`)

**Functions & Methods:**
- Python: `snake_case` (e.g., `hash_password()`, `crear_movimiento()`, `listar_productos()`)
- TypeScript: `camelCase` (e.g., `startImpersonation()`, `filterByRole()`, `getPersistedAuth()`)
- React hooks: `use` prefix + camelCase (e.g., `useNavigation()`, `useMediaQuery()`, `useAuthStore()`)

**Variables:**
- Python: `snake_case` (e.g., `tenant_id`, `costo_promedio_ponderado`, `fecha_emision`)
- TypeScript: `camelCase` (e.g., `tenantId`, `costoPonderado`, `token`)
- React state: camelCase (e.g., `isLoading`, `userData`, `refToken`)
- Constants: UPPERCASE_SNAKE_CASE (e.g., `API_BASE`, `STORAGE_KEY`, `MAX_UPLOAD`)

**Types & Interfaces:**
- Python Enums: UPPERCASE values in PascalCase class (e.g., `EstadoVenta.PENDIENTE`, `TipoMovimiento.ENTRADA`)
- TypeScript Interfaces: PascalCase, `I` prefix optional (e.g., `User`, `AuthState`, `NavItem`)
- Pydantic schemas: PascalCase with suffix pattern (e.g., `ProductoCreate`, `ProductoUpdate`, `ProductoResponse`)
- React component names: PascalCase (e.g., `Sidebar.tsx`, `Modal.tsx`, `RoleGuard.tsx`)

**Database columns:**
- snake_case, English-inspired names (e.g., `created_at`, `updated_at`, `tenant_id`, `numero_venta`)
- Timestamps: `created_at`, `updated_at`, `deleted_at` (for soft deletes)
- Boolean columns: prefix with `es_` or `esta_` (e.g., `es_superadmin`, `estado`)

## Code Style

**Formatting:**
- Python: Ruff with line length 120, target Python 3.12
  - Config: `[tool.ruff]` in `pyproject.toml`
  - Line-length: 120
- TypeScript: ESLint + TypeScript strict mode
  - Config: `eslint.config.js` (flat config)
  - No `any` types allowed
  - Extends: `typescript-eslint`, `react-hooks`, `react-refresh`

**Linting:**
- Python Ruff rules: `["E", "F", "I", "N", "W"]`
  - Ignores: E501 (long lines), N806 (function arg case)
- TypeScript: Recommended rules for hooks + refresh
- Pre-commit checks: None enforced (implicit)

**Indentation:**
- Python: 4 spaces
- TypeScript/React: 2 spaces (Vite default)

## Import Organization

**Python Order:**
1. Standard library imports (`os`, `sys`, `datetime`, etc.)
2. Third-party imports (`fastapi`, `sqlalchemy`, `pydantic`, etc.)
3. Relative imports from codebase (`from ..datos.db import`, `from ..utils.logger import`)

Example from `rutas/productos.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from uuid import UUID

from ..datos.db import get_db
from ..datos.modelos import Productos, Usuarios
from ..datos.esquemas import ProductoCreate, ProductoUpdate, ProductoResponse
from ..utils.seguridad import get_current_user, get_tenant_id_from_token, require_tenant_roles, UserContext
from ..utils.logger import setup_logger
```

**TypeScript Order:**
1. External libraries (`axios`, `zustand`, `react`, `react-router-dom`)
2. Heroicons imports
3. Local store/hook/component imports
4. Type imports at top with explicit `import type` for types

Example from `stores/authStore.ts`:
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Tenant, ImpersonationResponse } from '../types';
import { auth } from '../api/endpoints';
```

**Path Aliases:**
- Python: Relative imports (no path aliases defined)
- TypeScript: Relative paths with `../` (no aliases configured)

## Error Handling

**Backend (FastAPI):**
- Pattern: Try-catch with specific exceptions first, generic Exception last
- Always use `HTTPException` from FastAPI with appropriate status codes
- Log errors with context before raising

```python
try:
    nuevo_producto = Productos(tenant_id=ctx.tenant_id, **producto_data.model_dump())
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)

    logger.info(
        f"Producto creado: {nuevo_producto.nombre}",
        extra={
            "producto_id": str(nuevo_producto.id),
            "codigo": nuevo_producto.codigo_interno,
            "user_id": str(ctx.user.id)
        }
    )
    return ProductoResponse.model_validate(nuevo_producto)
except Exception as e:
    db.rollback()
    logger.error("Error creando producto", exc_info=e)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error interno al crear el producto"
    )
```

**Status Codes:**
- 400 Bad Request: Validation failures, business logic violations
- 401 Unauthorized: Missing/invalid token
- 403 Forbidden: User lacks permissions (RBAC)
- 404 Not Found: Resource doesn't exist
- 500 Internal Server Error: Unexpected exceptions

**Frontend (React/TypeScript):**
- Axios interceptor handles 401 with token refresh
- Error responses follow format: `{ detail: string }` (from backend)
- Toast notifications for user-facing errors
- Specific error messages logged, generic messages shown to users

## Logging

**Framework:** Python `logging` module with structured JSON output

**Setup:** `setup_logger(__name__)` in each module

**Patterns:**
- Context vars for request tracking: `request_id_var`, `user_id_var`, `correlation_id_var`
- Extra metadata logged with `extra={}` dict
- JSON formatter includes: `timestamp`, `level`, `logger`, `message`, `request_id`, `user_id`, `module`, `function`, `line`
- Text formatter for development (human-readable)

**When to Log:**
- Info: Successful operations (product created, invoice emitted)
- Error: Exceptions with full traceback via `exc_info=e`
- Debug: Not used in codebase; use print for local debugging

Example from `rutas/productos.py`:
```python
logger.info(
    f"Producto creado: {nuevo_producto.nombre}",
    extra={
        "producto_id": str(nuevo_producto.id),
        "codigo": nuevo_producto.codigo_interno,
        "user_id": str(ctx.user.id)
    }
)

logger.error("Error creando producto", exc_info=e)
```

**File Locations:**
- `backend/app/utils/logger.py`: Core logging setup
- Loggers configured at module level: `logger = setup_logger(__name__)`

## Comments

**When to Comment:**
- Complex business logic (e.g., weighted average cost calculation)
- Non-obvious algorithm steps
- Section headers for organization

**Style:**
- Single-line comments: `#` with space after
- Multi-line docstrings: Triple quotes for functions/classes
- Docstring format: Summary line, blank line, detailed description with Args/Returns

**JSDoc/TSDoc:**
- Python: Minimal docstrings, focus on `what`, not `how`
- TypeScript: None observed; rely on type inference
- Pydantic schemas: Field descriptions with `Field(..., description="...")`

Example from `datos/esquemas.py`:
```python
class LoginRequest(BaseModel):
    """Schema para request de login"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=1, description="Contraseña")
```

## Function Design

**Size:**
- Keep functions focused on single responsibility
- Average 20-50 lines for route handlers
- Longer functions (100+ lines) acceptable for complex flows (e.g., invoice emission)

**Parameters:**
- Use Pydantic models for request bodies (not individual params)
- Dependency injection for `db: Session`, `ctx: UserContext`
- FastAPI `Query`, `Path` for URL params with validation

Example:
```python
@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    producto_data: ProductoCreate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles('admin', 'operador'))
):
```

**Return Values:**
- Always return response models (not raw ORM objects)
- Use `.model_validate()` to convert ORM → Pydantic
- Include proper status codes via `status_code=` parameter

```python
return ProductoResponse.model_validate(nuevo_producto)
```

## Module Design

**Exports:**
- Python: No explicit `__all__` (implicit exports of public names)
- TypeScript: Named exports, no default exports for types
- Barrel files: `/api/endpoints.ts` exports all API methods

**Barrel Files (Index Files):**
- Not heavily used; most imports are direct
- `api/endpoints.ts` consolidates API method exports
- `types/index.ts` exports all TypeScript interfaces

**Separation of Concerns:**
- **Models** (`datos/modelos*.py`): ORM definitions only
- **Schemas** (`datos/esquemas.py`): Pydantic validation
- **Routes** (`rutas/*.py`): HTTP handlers, business logic
- **Utilities** (`utils/*.py`): Reusable functions (auth, logging, validators)
- **Stores** (`stores/*.ts`): Zustand state management
- **Hooks** (`hooks/*.ts`): Custom React hooks
- **Components** (`components/**/*.tsx`): Presentational React components

## Multi-Tenancy & Security Patterns

**Backend:**
- Header `X-Tenant-ID: <uuid>` required on all requests
- Middleware validates user has access to tenant
- Set local DB context: `SET LOCAL app.tenant_id_actual = '<uuid>'` before queries
- RLS automatically filters queries by tenant_id
- Never skip `WHERE tenant_id = ctx.tenant_id` in queries

**Frontend:**
- `X-Tenant-ID` added via Axios interceptor from localStorage
- Auth token includes `tenant_id` in JWT payload
- Zustand store persists tokens to localStorage

**RBAC (Role-Based Access Control):**
- Backend: `require_tenant_roles('admin', 'operador')` decorator
- Raises `HTTPException(403, "Permisos insuficientes")` if role not allowed
- Roles: `superadmin` (system-wide), `admin`, `operador`, `contador`, `vendedor` (tenant-scoped)

## TypeScript React Patterns

**Component Props:**
- Use `interface ComponentProps` for type safety
- Avoid inline prop typing
- No prop drilling; use Zustand stores or Context

**State Management:**
- Zustand for global state (auth, navigation)
- `persist` middleware for localStorage sync
- No Redux, no Context API

**Type Safety:**
- Strict mode enabled in `tsconfig.json`
- No `any` types
- Import `type` keyword for type-only imports

Example from `stores/authStore.ts`:
```typescript
interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;

  login: (email: string, password: string) => Promise<Tenant[]>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist((set, get) => ({
    // implementation
  }), {
    name: 'chandelier-auth'
  })
);
```

**Async/Await:**
- Prefer async/await over promises
- Error handling in try-catch blocks
- Don't leave unhandled promise rejections

---

*Convention analysis: 2026-02-15*
