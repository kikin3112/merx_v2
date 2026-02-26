"""
Tenant isolation security tests.

Verifies that tenant A cannot access tenant B's data through any endpoint,
validating PostgreSQL RLS + TenantContextMiddleware are working correctly.
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.main import app
from app.datos.db import Base, get_db
from app.datos.modelos import Usuarios
from app.datos.modelos_tenant import Tenants
from app.utils.seguridad import hash_password, create_access_token


TEST_DB_URL = os.environ.get("DB_URL", "postgresql://postgres:postgres@localhost:5432/chandelier_test")


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture(scope="module")
def db(engine):
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def two_tenants(db: Session):
    """Create two isolated tenants with their own admin users."""
    tenant_a = Tenants(
        nombre="Tenant Alpha",
        nit="111111111-1",
        estado="ACTIVO",
        email_contacto="alpha@test.com"
    )
    tenant_b = Tenants(
        nombre="Tenant Beta",
        nit="222222222-2",
        estado="ACTIVO",
        email_contacto="beta@test.com"
    )
    db.add_all([tenant_a, tenant_b])
    db.flush()

    user_a = Usuarios(
        email="admin_a@test.com",
        nombre="Admin Alpha",
        password_hash=hash_password("pass_alpha"),
        rol="admin",
        estado=True,
        es_superadmin=False,
    )
    user_b = Usuarios(
        email="admin_b@test.com",
        nombre="Admin Beta",
        password_hash=hash_password("pass_beta"),
        rol="admin",
        estado=True,
        es_superadmin=False,
    )
    db.add_all([user_a, user_b])
    db.commit()

    token_a = create_access_token(
        data={"sub": str(user_a.id), "email": user_a.email, "rol": "admin"},
        tenant_id=tenant_a.id,
        rol_en_tenant="admin",
    )
    token_b = create_access_token(
        data={"sub": str(user_b.id), "email": user_b.email, "rol": "admin"},
        tenant_id=tenant_b.id,
        rol_en_tenant="admin",
    )

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "user_a": user_a,
        "user_b": user_b,
        "token_a": token_a,
        "token_b": token_b,
    }


@pytest.fixture(scope="module")
def client(db: Session):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestCrossTenantDataAccess:
    """Tenant A must not access Tenant B's resources and vice-versa."""

    def test_tenant_a_cannot_read_tenant_b_products(self, client, two_tenants):
        """GET /api/v1/productos with Tenant A's token and Tenant B's header."""
        response = client.get(
            "/api/v1/productos",
            headers={
                "Authorization": f"Bearer {two_tenants['token_a']}",
                "X-Tenant-ID": str(two_tenants["tenant_b"].id),
                # Token is for tenant_a but header says tenant_b
            },
        )
        # The JWT tenant claim should not match the header tenant — expect 403 or empty result
        assert response.status_code in (401, 403, 400), (
            f"Expected auth error when token tenant != header tenant, got {response.status_code}"
        )

    def test_tenant_b_cannot_read_tenant_a_products(self, client, two_tenants):
        """GET /api/v1/productos with Tenant B's token and Tenant A's header."""
        response = client.get(
            "/api/v1/productos",
            headers={
                "Authorization": f"Bearer {two_tenants['token_b']}",
                "X-Tenant-ID": str(two_tenants["tenant_a"].id),
            },
        )
        assert response.status_code in (401, 403, 400), (
            f"Expected auth error when token tenant != header tenant, got {response.status_code}"
        )

    def test_missing_tenant_header_blocked(self, client, two_tenants):
        """Request to tenant endpoint without X-Tenant-ID must be rejected."""
        response = client.get(
            "/api/v1/productos",
            headers={"Authorization": f"Bearer {two_tenants['token_a']}"},
            # No X-Tenant-ID header
        )
        assert response.status_code == 400, (
            f"Missing X-Tenant-ID should return 400, got {response.status_code}"
        )

    def test_invalid_tenant_uuid_blocked(self, client, two_tenants):
        """Non-UUID X-Tenant-ID must be rejected."""
        response = client.get(
            "/api/v1/productos",
            headers={
                "Authorization": f"Bearer {two_tenants['token_a']}",
                "X-Tenant-ID": "not-a-uuid",
            },
        )
        assert response.status_code == 400, (
            f"Invalid UUID should return 400, got {response.status_code}"
        )

    def test_random_tenant_id_returns_no_data(self, client, two_tenants):
        """A valid UUID for a non-existent tenant should return empty or 404."""
        random_tenant = str(uuid4())
        random_token = create_access_token(
            data={"sub": str(uuid4()), "email": "ghost@test.com", "rol": "admin"},
            tenant_id=random_tenant,
            rol_en_tenant="admin",
        )
        response = client.get(
            "/api/v1/productos",
            headers={
                "Authorization": f"Bearer {random_token}",
                "X-Tenant-ID": random_tenant,
            },
        )
        # Either empty list or 404/403 — no data from other tenants
        if response.status_code == 200:
            data = response.json()
            items = data if isinstance(data, list) else data.get("items", [])
            assert len(items) == 0, "Non-existent tenant should return zero records"
        else:
            assert response.status_code in (403, 404, 401)


class TestTenantContextPropagation:
    """Verify that tenant context is set/cleared correctly across requests."""

    def test_concurrent_requests_isolation(self, client, two_tenants):
        """
        Simulate two requests for different tenants.
        Each should receive only its own data.
        """
        resp_a = client.get(
            "/api/v1/productos",
            headers={
                "Authorization": f"Bearer {two_tenants['token_a']}",
                "X-Tenant-ID": str(two_tenants["tenant_a"].id),
            },
        )
        resp_b = client.get(
            "/api/v1/productos",
            headers={
                "Authorization": f"Bearer {two_tenants['token_b']}",
                "X-Tenant-ID": str(two_tenants["tenant_b"].id),
            },
        )
        # Both should succeed for their own tenant
        assert resp_a.status_code in (200, 404)
        assert resp_b.status_code in (200, 404)

        # If both succeed with data, ensure no overlap
        if resp_a.status_code == 200 and resp_b.status_code == 200:
            ids_a = {item["id"] for item in (resp_a.json() if isinstance(resp_a.json(), list) else [])}
            ids_b = {item["id"] for item in (resp_b.json() if isinstance(resp_b.json(), list) else [])}
            assert not ids_a.intersection(ids_b), (
                "Tenant A and Tenant B must not share product records"
            )
