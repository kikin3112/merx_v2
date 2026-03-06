# Chandelier - Tests

Ejecuta tests del proyecto con pytest.

## Uso

```
/test
```

## Comandos

```bash
# Ejecutar todos los tests
uv run pytest

# Tests con output verbose
uv run pytest -v

# Tests de un módulo específico
uv run pytest tests/test_productos.py
uv run pytest tests/test_ventas.py

# Tests que coinciden con un patrón
uv run pytest -k "test_crear"

# Tests con coverage
uv run pytest --cov=backend/app --cov-report=term-missing

# Tests parando al primer fallo
uv run pytest -x

# Tests con output de print
uv run pytest -s
```

## Estructura de Tests

```
tests/
  test_auth.py          # Login, JWT, permisos
  test_productos.py     # CRUD productos
  test_ventas.py        # Ventas + inventario
  test_facturas.py      # Facturación + contabilidad
  test_cotizaciones.py  # Cotizaciones + conversión
  conftest.py           # Fixtures compartidos
```

## Fixtures (conftest.py)

```python
import os, pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.datos.db import get_db, Base

TEST_DB_URL = os.environ.get("DB_URL", "postgresql://postgres:<PW>@localhost:5432/api_merx_v2_test")

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_engine):
    session = sessionmaker(bind=test_engine)()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: (yield db_session)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    resp = client.post("/api/v1/auth/login", json={
        "email": os.environ.get("TEST_ADMIN_EMAIL"),
        "password": os.environ.get("TEST_ADMIN_PASSWORD"),
    })
    data = resp.json()
    resp2 = client.post("/api/v1/auth/select-tenant",
        json={"tenant_id": data["tenants"][0]["id"]},
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    return {"Authorization": f"Bearer {resp2.json()['access_token']}", "X-Tenant-ID": data["tenants"][0]["id"]}
```

## Tests de Servicios

```python
from backend.app.servicios.servicio_inventario import ServicioInventario

def test_costo_promedio_ponderado(db_session):
    servicio = ServicioInventario(db_session)
    resultado = servicio.calcular_costo_promedio(10, 1000, 5, 1200)
    assert round(resultado, 2) == 1066.67
```

## Convenciones

- Archivos: `tests/test_{modulo}.py`
- Funciones: `test_{accion}_{escenario}`
- Siempre usar `auth_headers` fixture para endpoints protegidos
- Trailing slash en URLs de colección: `/productos/` no `/productos`
- Rollback automático via fixture — no limpiar data manualmente

## Patrón de Test

```python
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_headers(email="admin@example.com", password="admin123"):
    """Helper para obtener headers autenticados."""
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    tenant_id = response.json()["tenants"][0]["id"]
    # Select tenant
    response = client.post(
        "/api/v1/auth/select-tenant",
        json={"tenant_id": tenant_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    new_token = response.json()["access_token"]
    return {
        "Authorization": f"Bearer {new_token}",
        "X-Tenant-ID": tenant_id,
    }

def test_listar_productos():
    headers = get_auth_headers()
    response = client.get("/api/v1/productos/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```
