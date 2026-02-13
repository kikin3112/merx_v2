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

## Patrón de Test

```python
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_headers(email="admin@velasaromaticas.com", password="admin123"):
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
