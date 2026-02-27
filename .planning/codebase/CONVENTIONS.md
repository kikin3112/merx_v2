# Coding Conventions

**Analysis Date:** 2026-02-27

## Naming Patterns

**Files:**
- TypeScript/TSX: `camelCase` for files and directories (e.g., `authStore.ts`, `LogoutButton.tsx`)
- Python: `snake_case` for files and modules (e.g., `servicio_audit.py`, `test_auth_bypass.py`)
- Components: `PascalCase` for React components (e.g., `LogoutButton.tsx`, `KanbanBoard.tsx`)
- Directories: lowercase with hyphens for feature grouping (e.g., `components/auth/`, `components/crm/`, `components/onboarding/`)

**Functions:**
- TypeScript: `camelCase` for all function names (e.g., `getPersistedAuth()`, `startImpersonation()`)
- Python: `snake_case` for all functions (e.g., `hash_password()`, `create_access_token()`, `obtener_tenants_usuario()`)
- Methods in classes: `snake_case` in Python (e.g., `ServicioAuditLog.registrar()`)

**Variables:**
- TypeScript: `camelCase` for variables and constants that vary (e.g., `token`, `refreshQueue`, `tenantId`)
- Python: `snake_case` for all variables (e.g., `tenant_id`, `user_email`, `is_refreshing`)
- Constants: `UPPER_SNAKE_CASE` in both (e.g., `API_BASE`, `STORAGE_KEY`, `TEST_DB_URL`)
- React hook selectors: `(s) => s.propertyName` pattern (e.g., `const logout = useAuthStore((s) => s.logout)`)

**Types:**
- TypeScript Interfaces: `PascalCase` with `Interface` suffix optional (e.g., `Props`, `AuthState`, `User`)
- Python type hints: Use `Optional[Type]`, `List[Type]`, `dict` from typing module
- React component props: Always define an `Interface` (e.g., `interface Props { className: string; }`)

**Constants & Environment:**
- Environment variables: `UPPER_SNAKE_CASE` (e.g., `VITE_API_URL`, `VITE_CLERK_PUBLISHABLE_KEY`)
- Storage keys: `kebab-case` (e.g., `'chandelier-auth'` in localStorage)
- Feature flags: `UPPER_SNAKE_CASE` (e.g., `CLERK_KEY` when checking existence)

## Code Style

**Formatting:**
- Tool: No enforced formatter configured (no Prettier, no Black)
- Line length: Python max 120 characters (ruff configuration)
- TypeScript: No strict line length enforcement
- Indentation: 2 spaces (TypeScript/React), 4 spaces (Python)

**Linting:**
- TypeScript: ESLint with typescript-eslint plugins
  - Config file: `/c/Users/luisr/PycharmProjects/merx_v2/frontend/eslint.config.js`
  - Downgraded rules: `@typescript-eslint/no-explicit-any: warn`, `react-hooks/set-state-in-effect: warn`
  - Enforced: React hooks rules-of-hooks, no unused imports/parameters

- Python: Ruff linter
  - Config file: pyproject.toml `[tool.ruff]`
  - Selected rules: E (pycodestyle), F (Pyflakes), I (isort), N (pep8-naming), W (pycodestyle warnings)
  - Ignored: E501 (line length), N806 (variable case)
  - Security: Bandit enabled in CI

**Strict TypeScript Settings:**
- `strict: true` - All TypeScript strict checks enabled
- `noUnusedLocals: true` - Unused variables must be removed
- `noUnusedParameters: true` - All function parameters must be used
- `noFallthroughCasesInSwitch: true` - Switch cases must have break/return
- `noUncheckedSideEffectImports: true` - Side effect imports must be explicit

## Import Organization

**Order (TypeScript):**
1. External libraries (`react`, `axios`, `zustand`, etc.)
2. Internal utilities and stores (`../stores/`, `../api/`, `../utils/`)
3. Components and hooks
4. Types from local modules

Example from `LogoutButton.tsx`:
```typescript
import { useClerk } from '@clerk/clerk-react';
import { ArrowRightStartOnRectangleIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../../stores/authStore';
```

**Order (Python):**
1. Standard library (`import sys`, `from datetime import`)
2. Third-party packages (`from fastapi import`, `from sqlalchemy import`)
3. Application modules (`from ..config import settings`, `from ..datos.db import Base`)

Example from `auth.py`:
```python
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..config import settings
from ..datos.db import get_db
```

**Path Aliases:**
- TypeScript: No path aliases configured (use relative imports)
- Python: Relative imports with parent references (e.g., `from ..config import settings`)

## Error Handling

**TypeScript/React Patterns:**
- Try-catch for async operations with silent failures acceptable in UI handlers
- Explicit error checking: `if (error.response?.status === 401)`
- No generic catch all - specify error types when possible
- Fallback UI rendering on error (e.g., `LegacyLogoutBtn` if Clerk unavailable)
- localStorage access wrapped in try-catch to handle quota/access errors

Example from `client.ts` token refresh:
```typescript
try {
  const { data } = await axios.post(`${API_BASE}/auth/refresh`, {...});
  // success path
} catch (refreshError) {
  processQueue(refreshError, null);
  clearPersistedAuth();
  window.location.href = '/login';
  return Promise.reject(refreshError);
} finally {
  isRefreshing = false;
}
```

**Python Patterns:**
- Raise `HTTPException` with explicit status codes for API errors
- Never catch generic `Exception` without logging stack trace with `exc_info=True`
- Custom exceptions can be created but HTTPException preferred for API layer
- Log all errors with context: `logger.error(message, exc_info=True, extra={context})`
- Service methods return None or object, don't raise on expected failures (return empty list instead)

Example from `servicio_audit.py`:
```python
except Exception as e:
    audit_db.rollback()
    logger.error(f"Error registrando audit log: {e}", exc_info=True)
    # No re-lanzar: el audit log no debe bloquear la operación principal
finally:
    audit_db.close()
```

## Logging

**Framework:**
- Backend: Python `logging` module with custom formatters in `utils/logger.py`
- Frontend: `console.log` (no logging library)

**Backend Logging Patterns:**
- Use `setup_logger(__name__)` at module level to get logger instance
- Log level: DEBUG, INFO, WARNING, ERROR
- Extra context passed via `extra` dict: `logger.info("message", extra={"key": value})`
- Request context automatically injected: `request_id`, `user_id`, `correlation_id`
- Exception logging: `logger.error(message, exc_info=True)` includes full stack trace
- Performance logging: `log_performance(logger, operation, duration_ms, **context)`

Example from `auth.py`:
```python
logger.warning(
    "Intento de login fallido",
    extra={
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
    },
)
```

**Log Format:**
- Production: JSON format (structured logging for ELK/monitoring)
- Development: Colored text format with timestamps
- File output: JSON format with rotation at 10MB (5 backup files)

**Frontend Logging:**
- No structured logging library used
- Use `console.log()`, `console.error()`, `console.warn()` directly where needed
- Avoid logging sensitive data (tokens, passwords, PII)

## Comments

**When to Comment:**
- Complex business logic or non-obvious algorithms (rare in this codebase)
- Security-relevant decisions (e.g., "Only inject stored token if request doesn't already carry Authorization")
- Workarounds or temporary solutions (with ticket reference if available)
- DO NOT comment on what the code does - code should be self-explanatory

**JSDoc/TSDoc:**
- Backend Python: Docstrings for public functions/methods using triple quotes
  ```python
  def hash_password(password: str) -> str:
      """
      Hashea una contraseña usando Argon2.

      Args:
          password: Contraseña en texto plano
      Returns:
          Hash de la contraseña
      """
  ```
- Frontend TypeScript: JSDoc for exported functions/components (optional, focus on type clarity)
- Service methods include docstrings with Args/Returns documentation

**File Headers:**
- Python modules: Module docstring at top explaining purpose
  ```python
  """
  Servicio de Audit Logging.
  Registra acciones críticas del sistema de forma inmutable.
  Usa su propia sesión para no fallar si la transacción principal falla.
  """
  ```
- TypeScript: No required header comments

## Function Design

**Size:**
- Keep functions focused on a single responsibility
- If a function exceeds 50 lines, consider breaking it into smaller functions
- Async functions in TypeScript should be compact, delegate to helper functions

**Parameters:**
- Use destructuring for objects: `function ClerkLogoutBtn({ className, onBeforeLogout }: Props)`
- Limit to 3-4 parameters; use object parameters for more
- Type all parameters in TypeScript (no `any`)
- Default parameters accepted for optional config

Example of good parameter design:
```typescript
// Good - Props interface
interface Props {
  className: string;
  onBeforeLogout?: () => void;
}

function LogoutButton(props: Props) { ... }

// Good - Destructured in function signature
function ClerkLogoutBtn({ className, onBeforeLogout }: Props) { ... }
```

**Return Values:**
- Explicit return types in TypeScript: `(email: string, password: string) => Promise<Tenant[]>`
- Python functions should type-hint returns: `-> Optional[AuditLog]`
- Async functions return Promise/awaitable
- Prefer returning objects over multiple return values

## Module Design

**Exports:**
- TypeScript: Named exports preferred over default exports for better refactoring support
  - Exception: React components often use `export default function ComponentName()`
  - When mixing: default for main component, named for subcomponents/helpers

- Python: All public functions/classes are module-level, no barrel files concept
  - Use `__all__` in modules to indicate public API

**Barrel Files:**
- Not used in this project
- Imports are always specific/relative

**File Organization:**
- React components: One component per file, related utilities in same file if < 50 lines
- Services: One service per file (e.g., `servicio_audit.py`, `servicio_tenants.py`)
- Utils: Small focused modules (e.g., `logger.py`, `seguridad.py`)

## API Client Patterns (TypeScript)

**Axios Configuration:**
- Create single axios instance with base URL: `axios.create({ baseURL, headers })`
- Request interceptor: add auth token from localStorage if not already present
- Response interceptor: handle 401 with token refresh + request queuing
- Key pattern: Check `if (token && !config.headers['Authorization'])` to avoid overwriting explicit headers

Example pattern from `client.ts`:
```typescript
client.interceptors.request.use((config) => {
  const { token, tenantId } = getPersistedAuth();
  if (token && !config.headers['Authorization']) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId;
  }
  return config;
});
```

## Backend Service Layer Patterns (Python)

**Service Class Structure:**
- Classes named `Servicio{Domain}` (e.g., `ServicioAuditLog`, `ServicioTenants`)
- Accept `Session` in `__init__` as dependency
- All public methods are query/command methods
- Log important operations with context
- Raise HTTPException only in routes, return None/empty from services on expected failures

Example:
```python
class ServicioAuditLog:
    def __init__(self, db: Session):
        self.db = db

    def registrar(self, actor_id: Optional[UUID], ...) -> AuditLog:
        # Method implementation
        logger.info(f"Audit: {action}...", extra={...})
        return log_entry
```

## State Management (TypeScript)

**Zustand Store Pattern:**
- Store created with `create<StoreType>()`
- State properties at top of store function
- Actions/methods below state
- Use `persist` middleware for localStorage sync
- Selectors use `(state) => state.property` shorthand: `(s) => s.logout`

Example from `authStore.ts`:
```typescript
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // State
      token: null,
      // Actions
      login: async (email, password) => {
        const { data } = await auth.login(email, password);
        set({ token: data.access_token, ... });
      },
    }),
    { name: 'chandelier-auth', partialize: (state) => ({...}) }
  )
);
```

## TypeScript Type Patterns

**Component Props:**
```typescript
interface Props {
  className: string;
  onBeforeLogout?: () => void;  // Optional with ?
}

// Use in component signature
function LogoutButton(props: Props) { ... }
```

**API Response Types:**
- Define interfaces for all API responses in `types/index.ts`
- Use union types for multiple response states: `LoginResponse | ErrorResponse`
- Use `Optional[Type]` for nullable fields

**Type Safety Rules:**
- NO `any` type (ESLint enforces with warning level)
- Use `unknown` if type truly unknown, narrow with type guards
- Strict null checks enabled - use `?` for optional fields, not `undefined`

---

*Convention analysis: 2026-02-27*
