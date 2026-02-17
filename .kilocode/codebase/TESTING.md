# Testing Patterns

**Analysis Date:** 2026-02-15

## Test Framework

**Runner:**
- pytest 7.4.0+
- Config: `pyproject.toml` (no separate pytest.ini)
- Async support: pytest-asyncio with `asyncio_mode = "auto"`

**Key settings from `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["backend/tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short --strict-markers"
asyncio_mode = "auto"
```

**Assertion Library:**
- pytest built-in assertions (no external library)
- Standard `assert` statements with descriptive messages

**Coverage Tools:**
- pytest-cov 4.1.0+ installed in test dependencies
- No coverage target enforced

**Run Commands:**
```bash
# Run all tests
pytest

# Run specific test file
pytest backend/tests/test_rbac_backend.py

# Run with verbose output and short tracebacks
pytest -v --tb=short

# Run with coverage report
pytest --cov=app backend/tests/
```

## Test File Organization

**Location:**
- All tests in `backend/tests/` directory
- Test files co-located with conftest.py

**Naming:**
- Test files: `test_*.py` (e.g., `test_rbac_backend.py`, `test_inventario_concurrency.py`)
- Test functions: `test_*` (e.g., `test_vendedor_cannot_delete_producto`)
- No test classes observed; functions preferred

**Current Test Files:**
- `backend/tests/conftest.py`: Fixtures for all tests
- `backend/tests/test_rbac_backend.py`: RBAC enforcement tests
- `backend/tests/test_inventario_concurrency.py`: Concurrency and locking tests
- `backend/tests/__init__.py`: Empty marker file

**Structure:**
```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Fixtures (engine, db_session, client, tokens)
│   ├── test_rbac_backend.py     # RBAC tests
│   ├── test_inventario_concurrency.py  # Concurrency tests
│   └── test_*.py                # Future tests (one feature per file)
```

## Test Structure

**Suite Organization (from conftest.py):**

1. **Fixtures with function scope** - Each test gets fresh database
   ```python
   @pytest.fixture(scope="function")
   def engine():
       """Create test database engine with in-memory SQLite."""

   @pytest.fixture(scope="function")
   def db_session(engine):
       """Create isolated test database session with automatic rollback."""
   ```

2. **Test client with dependency override**
   ```python
   @pytest.fixture(scope="function")
   def client(db_session):
       """FastAPI test client with test database dependency override."""
       def override_get_db():
           try:
               yield db_session
           finally:
               pass

       app.dependency_overrides[get_db] = override_get_db
       with TestClient(app) as test_client:
           yield test_client
       app.dependency_overrides.clear()
   ```

3. **Auth fixtures** - Pre-configured users with tokens
   ```python
   @pytest.fixture
   def tenant_admin_token(db_session: Session):
       """Create tenant + admin user, return JWT token with tenant context."""
       # Returns: { "token": str, "tenant_id": str, "user_id": str, "tenant": Tenants, "user": Usuarios }

   @pytest.fixture
   def vendedor_token(db_session: Session, tenant_admin_token):
       """Create vendedor user and return JWT token."""

   @pytest.fixture
   def contador_token(db_session: Session, tenant_admin_token):
       """Create contador user and return JWT token."""
   ```

**Test Patterns:**

Setup phase:
```python
def test_vendedor_cannot_delete_producto(client, vendedor_token, tenant_admin_token, db_session):
    """Vendedor role should not be able to delete products (403 Forbidden)."""
    from app.datos.modelos import Productos
    from uuid import uuid4

    tenant_id = uuid4(tenant_admin_token["tenant_id"])

    # Create a product as admin (SETUP)
    producto = Productos(
        tenant_id=tenant_id,
        nombre="Test Product",
        codigo_interno="PROD-001",
        precio_venta=Decimal("10000"),
        porcentaje_iva=Decimal("19"),
        categoria="Producto_Propio",
        estado=True
    )
    db_session.add(producto)
    db_session.commit()
```

Execution & assertion:
```python
    # Try to delete as vendedor (EXECUTE)
    response = client.delete(
        f"/api/v1/productos/{producto.id}",
        headers={
            "Authorization": f"Bearer {vendedor_token['token']}",
            "X-Tenant-ID": vendedor_token["tenant_id"]
        }
    )

    # Verify (ASSERT)
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    assert "permisos" in response.json().get("detail", "").lower()
```

**Teardown:**
- Automatic via fixture cleanup
- `db_session.rollback()` in conftest cleanup
- `app.dependency_overrides.clear()` after test

## Mocking

**Framework:**
- No external mocking library observed
- SQLite in-memory database used for isolation
- Fixtures provide pre-configured test data

**Patterns:**

Database mocking via in-memory SQLite:
```python
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def engine():
    """Create test database engine with in-memory SQLite."""
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
```

JWT token mocking via fixture:
```python
token = create_access_token(
    data={"sub": str(user.id), "email": user.email, "rol": "admin"},
    tenant_id=tenant.id,
    rol_en_tenant="admin"
)
```

**What to Mock:**
- Nothing explicitly mocked; use real models + in-memory DB
- Pre-create fixtures (tenants, users, products) rather than mocking

**What NOT to Mock:**
- Do not mock database layer (use fixtures instead)
- Do not mock authentication (use real JWT tokens)
- Do not mock HTTP responses (use TestClient)

## Fixtures and Factories

**Test Data:**

Tenant fixture with user:
```python
@pytest.fixture
def tenant_admin_token(db_session: Session):
    # Create tenant
    tenant = Tenants(
        nombre="Test Tenant",
        nit="900123456-7",
        estado="ACTIVO",
        email_contacto="test@test.com"
    )
    db_session.add(tenant)
    db_session.flush()

    # Create admin user
    user = Usuarios(
        email="admin@test.com",
        nombre="Test Admin",
        hash_password=hash_password("test123"),
        rol="admin",
        estado=True,
        es_superadmin=False
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "rol": "admin"},
        tenant_id=tenant.id,
        rol_en_tenant="admin"
    )

    return {
        "token": token,
        "tenant_id": str(tenant.id),
        "user_id": str(user.id),
        "tenant": tenant,
        "user": user
    }
```

Product fixture (from test):
```python
producto = Productos(
    tenant_id=tenant_id,
    nombre="Test Product",
    codigo_interno="PROD-001",
    precio_venta=Decimal("10000"),
    porcentaje_iva=Decimal("19"),
    categoria="Producto_Propio",
    estado=True
)
db_session.add(producto)
db_session.commit()
```

**Location:**
- All fixtures in `backend/tests/conftest.py`
- Test-specific fixtures defined in test functions or as local fixtures

## Coverage

**Requirements:**
- No coverage target enforced
- Coverage tracking available via `pytest-cov` plugin

**View Coverage:**
```bash
pytest --cov=app --cov-report=html backend/tests/
# Opens htmlcov/index.html
```

**Strategy:**
- Focus on critical paths (RBAC, inventory, accounting)
- Not all functions have tests yet (MVP coverage)

## Test Types

**Unit Tests:**
- Scope: Individual functions/methods in isolation
- Approach: Not heavily used; most tests are integration-style
- Example: Testing role validation logic within endpoint handlers

**Integration Tests:**
- Scope: API endpoint behavior with database and auth
- Approach: Use TestClient + fixtures to test full request cycle
- Primary test type in codebase

Example from `test_rbac_backend.py`:
```python
def test_vendedor_cannot_delete_producto(client, vendedor_token, tenant_admin_token, db_session):
    """Vendedor role should not be able to delete products (403 Forbidden)."""
    # Create product
    # Call API endpoint
    # Assert response status + message
```

**Concurrency Tests:**
- Scope: Race conditions and pessimistic locking
- Framework: ThreadPoolExecutor for concurrent operations
- Location: `backend/tests/test_inventario_concurrency.py`

Example:
```python
def test_concurrent_stock_deductions_prevent_negative(db_session, tenant_admin_token):
    """
    Concurrent sales should not cause negative stock due to pessimistic locking.

    Scenario:
    - Product has stock=10
    - 3 concurrent transactions try to deduct 8 units each
    - Expected: Only 1 succeeds, 2 fail with "Stock insuficiente"
    - Final stock: 2 (10 - 8)
    """
    # Setup
    produto = Productos(...)
    db_session.add(produto)
    db_session.commit()

    # Execute in parallel
    def deduct_stock():
        servicio = ServicioInventario(db_session, tenant_id)
        try:
            servicio.crear_movimiento(
                producto_id=producto.id,
                tipo=TipoMovimiento.SALIDA,
                cantidad=Decimal("8")
            )
            db_session.commit()
            return "success"
        except ValueError as e:
            db_session.rollback()
            if "Stock insuficiente" in str(e):
                return "insufficient_stock"
            return f"error: {str(e)}"

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(deduct_stock) for _ in range(3)]
        results = [future.result() for future in as_completed(futures)]

    # Assert
    assert results.count("success") == 1
    assert results.count("insufficient_stock") == 2
```

**E2E Tests:**
- Not implemented in MVP
- Would test complete workflows (Register → Create Product → Invoice → Accounting)

## Common Patterns

**Testing API Endpoints:**

Pattern:
1. Setup data (create tenant, user, product)
2. Make request with headers (Bearer token, X-Tenant-ID)
3. Assert status code and response body

```python
def test_contador_can_access_contabilidad(client, contador_token):
    """Contador can access accounting routes."""
    response = client.get(
        "/api/v1/contabilidad/asientos",
        headers={
            "Authorization": f"Bearer {contador_token['token']}",
            "X-Tenant-ID": contador_token["tenant_id"]
        }
    )

    assert response.status_code == 200, f"Contador should access accounting, got {response.status_code}"
```

**Testing Error Conditions:**

Check status code and detail message:
```python
assert response.status_code == 403, f"Expected 403, got {response.status_code}"
assert "permisos" in response.json().get("detail", "").lower()
```

**Testing Async Operations:**

Handled via `asyncio_mode = "auto"` in pytest config. Test functions can be async:
```python
# Implicit; pytest-asyncio handles it
```

**Testing Database State Changes:**

Refresh ORM object and verify:
```python
db_session.refresh(inventario)
assert inventario.cantidad_disponible == Decimal("2"), \
    f"Expected stock=2, got {inventario.cantidad_disponible}"
```

**Testing Exception Handling:**

Catch exception in try-except within test:
```python
def deduct_stock():
    try:
        servicio.crear_movimiento(...)
        db_session.commit()
        return "success"
    except ValueError as e:
        db_session.rollback()
        if "Stock insuficiente" in str(e):
            return "insufficient_stock"
        return f"error: {str(e)}"
```

## Frontend Testing

**Status:** Not implemented in MVP

**Planned approach (based on config):**
- ESLint for linting (enforced)
- No test framework currently configured (vitest or jest would be next)
- No component tests exist yet

---

*Testing analysis: 2026-02-15*
