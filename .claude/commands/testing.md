# Chandelier - Framework de Testing

Guía completa de testing para el proyecto chandelierp.

## Setup

```bash
# Instalar dependencias de test
uv add --dev pytest pytest-cov httpx

# Ejecutar
uv run pytest -v
```

## Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.datos.db import get_db, Base

TEST_DB_URL = os.environ.get("DB_URL", "postgresql://postgres:<TU_PASSWORD>@localhost:5432/api_merx_v2_test")

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    """Headers autenticados con tenant seleccionado."""
    resp = client.post("/api/v1/auth/login", json={
        "email": os.environ.get("TEST_ADMIN_EMAIL"),
        "password": os.environ.get("TEST_ADMIN_PASSWORD")
    })
    data = resp.json()
    token = data["access_token"]
    tenant_id = data["tenants"][0]["id"]

    resp = client.post(
        "/api/v1/auth/select-tenant",
        json={"tenant_id": tenant_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    new_token = resp.json()["access_token"]
    return {
        "Authorization": f"Bearer {new_token}",
        "X-Tenant-ID": tenant_id,
    }
```

## Tests de API

```python
# tests/test_productos.py
def test_crear_producto(client, auth_headers):
    data = {
        "sku": "TEST-001",
        "nombre": "Vela Test",
        "tipo": "producto_terminado",
        "precio_venta": 10000,
        "precio_costo": 5000,
        "tarifa_iva": 19.00,
        "stock": 0,
        "alerta_stock_min": 5,
    }
    resp = client.post("/api/v1/productos/", json=data, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["sku"] == "TEST-001"

def test_listar_productos(client, auth_headers):
    resp = client.get("/api/v1/productos/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_sin_auth_retorna_401(client):
    resp = client.get("/api/v1/productos/")
    assert resp.status_code == 401
```

## Tests de Servicios

```python
# tests/test_servicio_inventario.py
from backend.app.servicios.servicio_inventario import ServicioInventario

def test_costo_promedio_ponderado(db_session):
    servicio = ServicioInventario(db_session)
    # stock_actual=10, costo_actual=1000, entrada=5, costo_nuevo=1200
    # esperado: (10*1000 + 5*1200) / (10+5) = 1066.67
    resultado = servicio.calcular_costo_promedio(10, 1000, 5, 1200)
    assert round(resultado, 2) == 1066.67
```

## Convenciones

- Archivos: `tests/test_{modulo}.py`
- Funciones: `test_{accion}_{escenario}`
- Siempre usar `auth_headers` fixture para endpoints protegidos
- Trailing slash en URLs de colección: `/productos/` no `/productos`
- Limpiar data en fixtures (rollback automático via fixture)
