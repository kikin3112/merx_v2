# Testing Patterns

**Analysis Date:** 2026-02-27

## Test Framework

**Runner:**
- pytest 7.4.0+ with pytest-asyncio for async tests
- Config file: `pyproject.toml` under `[tool.pytest.ini_options]`
- Run all tests: `pytest`
- Run with coverage: `pytest --cov` (pytest-cov 4.1.0+)
- Watch mode: Not configured (use manual re-runs or IDE integration)

**Command Reference:**
```bash
pytest                                    # Run all tests
pytest backend/tests/ tests/security/     # Run specific directories
pytest -v                                 # Verbose output
pytest -v --tb=short                      # Short tracebacks (default)
pytest -x                                 # Stop on first failure
pytest tests/security/test_auth_bypass.py::TestUnauthenticatedAccess::test_no_token_returns_401  # Run single test
pytest --cov=app --cov-report=html       # Coverage with HTML report
```

**Assertion Library:**
- Built-in pytest assertions: `assert condition`, `assert x == y`
- No pytest-mock or extra assertion libraries needed

**Configuration (pyproject.toml):**
```toml
[tool.pytest.ini_options]
testpaths = ["backend/tests", "tests/security"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short --strict-markers"
asyncio_mode = "auto"
```

**Key Settings:**
- `asyncio_mode = "auto"` - Enables async test support automatically
- `testpaths` - Only runs tests from these directories
- `python_classes = "Test*"` - Test classes must be named `Test{Something}`
- `python_functions = "test_*"` - Test functions must start with `test_`

## Test File Organization

**Location:**
- Backend tests: `backend/tests/` - Co-located with test database fixtures
- Security tests: `tests/security/` - Isolated security-focused tests
- Naming: `test_{feature}.py`

**Test File Structure:**
```
backend/tests/
├── conftest.py          # Shared fixtures (database, client, auth tokens)
├── test_produtos.py
├── test_auth.py
└── ...

tests/security/
├── test_auth_bypass.py
├── test_tenant_isolation.py
├── test_sql_injection.py
└── test_rate_limiting.py
```

**Naming Convention:**
- Files: `test_*.py` (e.g., `test_auth_bypass.py`)
- Classes: `Test{Feature}` (e.g., `TestUnauthenticatedAccess`, `TestPublicEndpointsAccessible`)
- Methods: `test_{scenario}` (e.g., `test_no_token_returns_401`, `test_invalid_token_returns_401`)

## Test Structure

**Suite Organization Pattern:**
```python
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Test database URL from env or fallback
TEST_DB_URL = os.environ.get("DB_URL", "postgresql://postgres:postgres@localhost:5432/chandelier_test")

# ============================================================================
# FIXTURES (Module-Scoped)
# ============================================================================

@pytest.fixture(scope="module")
def engine():
    """Create test database engine using Postgres."""
    eng = create_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)  # Cleanup after all tests
    eng.dispose()

@pytest.fixture(scope="module")
def db(engine):
    """Create test database session."""
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def client(db: Session):
    """FastAPI TestClient with dependency override."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()

# ============================================================================
# TEST CLASSES
# ============================================================================

class TestUnauthenticatedAccess:
    """All protected endpoints must reject unauthenticated requests."""

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_no_token_returns_401(self, client, method, path):
        resp = client.request(method, path)
        assert resp.status_code in (401, 403, 422)

class TestRoleEscalation:
    """Lower-privilege users cannot access admin resources."""

    def test_vendedor_cannot_delete_users(self, client, tenant_and_token):
        resp = client.delete(
            f"/api/v1/usuarios/{uuid4()}",
            headers={"Authorization": f"Bearer {tenant_and_token['token']}"}
        )
        assert resp.status_code in (401, 403, 404)
```

**Key Patterns:**
- Fixtures at module level with appropriate scope
- Cleanup in yield-after pattern
- Test classes group related tests
- Parametrize common test patterns to avoid duplication

## Mocking

**Framework:**
- unittest.mock (Python standard library) imported as needed, not configured globally
- Minimal mocking philosophy: mock only external services, test real database interactions

**Patterns:**

No global mock framework configured. When mocking is needed (for external APIs like Clerk, AWS):

```python
from unittest.mock import patch, MagicMock

# Mock example for Clerk API interaction
@patch('app.utils.seguridad.verify_clerk_token')
def test_clerk_exchange(mock_verify_clerk, client):
    mock_verify_clerk.return_value = {"sub": "user_123", "email": "test@test.com"}
    response = client.post("/auth/clerk-exchange", json={"token": "fake_jwt"})
    assert response.status_code == 200
```

**What to Mock:**
- External HTTP APIs (Clerk, AWS S3, etc.)
- Third-party services with slow/unreliable network calls
- Sentry or other observability that shouldn't be called in tests

**What NOT to Mock:**
- Database queries - use real PostgreSQL test database
- FastAPI dependency injection - override with real implementations
- Password hashing functions - test with real Argon2
- JWT creation/verification - test with real keys from settings
- Service layer methods - test their real implementation

**Override Pattern (Preferred):**
```python
def override_get_db():
    try:
        yield db_session
    finally:
        pass

app.dependency_overrides[get_db] = override_get_db
```

## Fixtures and Factories

**Test Data Creation:**
All fixtures defined in `backend/tests/conftest.py`. Pattern uses direct model instantiation:

```python
@pytest.fixture
def tenant_admin_token(db_session: Session):
    """Create tenant + admin user, return JWT token."""

    # Create required plan (FK dependency)
    plan = Planes(nombre="Test Plan", precio_mensual=0)
    db_session.add(plan)
    db_session.flush()

    # Create tenant
    tenant = Tenants(
        nombre="Test Tenant",
        slug="test-tenant",
        nit="900123456-7",
        estado="activo",
        email_contacto="test@test.com",
        plan_id=plan.id,
    )
    db_session.add(tenant)
    db_session.flush()

    # Create user
    user = Usuarios(
        email="admin@test.com",
        nombre="Test Admin",
        password_hash=hash_password("test123"),
        rol="admin",
        estado=True,
        es_superadmin=False,
    )
    db_session.add(user)
    db_session.commit()

    # Create token
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "rol": "admin"},
        tenant_id=tenant.id,
        rol_en_tenant="admin",
    )

    return {"token": token, "tenant_id": str(tenant.id), "user_id": str(user.id), "tenant": tenant, "user": user}
```

**Key Fixture Rules:**
1. Create database dependencies in correct order (Planes → Tenants → Usuarios)
2. Always use `db_session.flush()` before creating dependent records
3. Use `db_session.commit()` to finalize
4. Include related objects in return dict for assertions
5. Fixtures can depend on other fixtures (e.g., `vendedor_token(db_session, tenant_admin_token)`)

**Available Fixtures (conftest.py):**
- `engine`: Test database engine with schema creation/cleanup
- `db_session`: SQLAlchemy session with automatic rollback
- `client`: FastAPI TestClient with database override
- `tenant_admin_token`: Admin user + tenant + JWT token
- `vendedor_token`: Vendor user with tenant context + JWT token
- `contador_token`: Accountant user with tenant context + JWT token

**Location:**
- `backend/tests/conftest.py` - Shared fixtures for all backend tests
- Security-specific fixtures in individual test files (e.g., `test_tenant_isolation.py:two_tenants()`)

## Coverage

**Requirements:**
- Minimum target: 70% code coverage for critical paths
- Security tests: 100% coverage of auth endpoints
- Not enforced via CI (no coverage threshold blocking merge)

**View Coverage:**
```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
# Opens htmlcov/index.html for visual coverage map
```

**What's Typically Covered:**
- All authentication endpoints
- Tenant isolation enforcement
- Authorization checks (role-based access)
- Error handling paths
- Database interactions (fixture-based)

**What's Typically NOT Covered:**
- Frontend React components (no Jest/Vitest configured)
- Admin UI features (manual testing)
- Legacy code paths not actively maintained

## Test Types

**Unit Tests:**
- Scope: Individual function/method in isolation
- Approach: Mock external dependencies (database, APIs), test logic only
- Location: Same directory as code or in `tests/` subdirectory
- Example: Testing `hash_password()` returns valid Argon2 hash

**Integration Tests:**
- Scope: Multiple components working together through real dependencies
- Approach: Real database, real HTTP client, real JWT generation
- Location: `backend/tests/test_*.py` files
- Example: Full login flow: POST /login → JWT token → GET /protected endpoint

**End-to-End Tests:**
- Scope: Full user workflow from login to action
- Approach: Not formally configured (manual testing only)
- Browser testing: Not set up (no Playwright, Cypress, Selenium)
- API E2E: Possible via pytest + TestClient + fixtures

**Security Tests:**
- Scope: Authorization, tenant isolation, injection prevention, rate limiting
- Location: `tests/security/` directory
- Approach: Real database, attack scenarios
- Examples:
  - `test_auth_bypass.py`: Unauthenticated access, expired tokens, role escalation
  - `test_tenant_isolation.py`: Cross-tenant access prevention
  - `test_sql_injection.py`: Parameter validation against injection
  - `test_rate_limiting.py`: Rate limit enforcement

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected

# OR with FastAPI TestClient (automatically handles async):
def test_async_endpoint(client):
    response = client.get("/api/endpoint")
    assert response.status_code == 200
```

**Error/Exception Testing:**
```python
def test_invalid_token_returns_401(self, client, method, path):
    """Request with tampered JWT must return 401."""
    resp = client.request(
        method,
        path,
        headers={
            "Authorization": "Bearer this.is.not.a.valid.jwt",
            "X-Tenant-ID": tenant_id,
        },
    )
    assert resp.status_code in (401, 403)

# For expected exceptions:
def test_raises_http_exception():
    with pytest.raises(HTTPException) as exc_info:
        authenticate_user("invalid@test.com", "wrongpass", db)
    assert exc_info.value.status_code == 401
```

**Parametrized Testing:**
```python
# Test same logic with multiple inputs
PROTECTED_ENDPOINTS = [
    ("GET",    "/api/v1/productos"),
    ("GET",    "/api/v1/clientes"),
    ("POST",   "/api/v1/productos"),
]

@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
def test_protected_requires_auth(self, client, method, path):
    resp = client.request(method, path)
    assert resp.status_code in (401, 403, 422)
```

**Database State Assertions:**
```python
def test_login_updates_ultimo_acceso(client, tenant_admin_token, db_session):
    user = db_session.query(Usuarios).filter_by(id=tenant_admin_token["user_id"]).first()
    old_time = user.ultimo_acceso

    # Trigger login
    response = client.post("/api/v1/auth/login", json={...})

    # Verify state changed
    db_session.refresh(user)
    assert user.ultimo_acceso > old_time
```

**Multiple Request Scenarios:**
```python
class TestTenantIsolation:
    def test_tenant_a_cannot_see_tenant_b_data(self, client, two_tenants):
        # Request with tenant_a credentials to access tenant_b data
        resp = client.get(
            "/api/v1/productos",
            headers={
                "Authorization": f"Bearer {two_tenants['token_a']}",
                "X-Tenant-ID": str(two_tenants['tenant_b'].id),  # Mismatch!
            },
        )
        assert resp.status_code in (401, 403)
```

## Test Database

**Setup:**
- Uses PostgreSQL (not SQLite)
- URL from env `DB_URL` or defaults to `postgresql://postgres:postgres@localhost:5432/chandelier_test`
- Schema created automatically from SQLAlchemy models via `Base.metadata.create_all()`
- Cleaned up after each test run via `Base.metadata.drop_all()`

**Fixtures Ensure:**
- Fresh database for each test (function scope)
- Automatic rollback on session closure
- No state leakage between tests

**Connection:**
```python
TEST_DB_URL = os.environ.get("DB_URL", "postgresql://postgres:postgres@localhost:5432/chandelier_test")
eng = create_engine(TEST_DB_URL)
Base.metadata.create_all(bind=eng)
```

## Pre-Commit Hooks

**Security scanning (`.pre-commit-config.yaml`):**
- Bandit: Static security analysis of Python code
- Semgrep: Pattern-based code scanning
- Gitleaks: Secret detection in commits
- Safety: Vulnerability scanning for Python dependencies

**Run Manually:**
```bash
pre-commit run --all-files
bandit -r backend/app/
semgrep --config=p/security-audit backend/
```

## Current Test Gaps

**Known Failing Tests (Pre-existing):**
- `test_admin_can_anular_factura` - ORM access pattern issue
- `test_superadmin_bypasses_tenant_role_checks` - Superadmin bypass logic not implemented in API
- `test_rate_limiting` - Request format mismatch
- `test_tenant_isolation` - Cross-tenant access not enforced in all endpoints

**Areas with Limited Coverage:**
- Frontend React components (no Jest configured)
- PDF generation (reportlab, manual testing only)
- S3/AWS integration (requires mocking)
- Email sending (requires mocking)
- Webhook handling (Svix integration, manual verification only)

---

*Testing analysis: 2026-02-27*
