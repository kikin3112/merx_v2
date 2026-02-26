"""
Authentication bypass security tests.

Probes for:
- Unauthenticated access to protected endpoints
- Expired/invalid JWT tokens
- Missing/malformed Authorization headers
- Role escalation attempts
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
from app.datos.modelos_tenant import Tenants
from app.datos.modelos import Usuarios
from app.utils.seguridad import hash_password, create_access_token


TEST_DB_URL = os.environ.get("DB_URL", "postgresql://postgres:postgres@localhost:5432/chandelier_test")

# Protected API paths that should require authentication
PROTECTED_ENDPOINTS = [
    ("GET",    "/api/v1/productos"),
    ("GET",    "/api/v1/clientes"),
    ("GET",    "/api/v1/usuarios"),
    ("GET",    "/api/v1/inventario/stock"),
    ("POST",   "/api/v1/productos"),
    ("DELETE", "/api/v1/productos/some-id"),
]

# Paths that must be publicly accessible (auth not required)
PUBLIC_ENDPOINTS = [
    ("POST", "/api/v1/auth/login"),
    ("GET",  "/health"),
]


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
def client(db: Session):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def tenant_and_token(db: Session):
    tenant = Tenants(
        nombre="Auth Test Tenant",
        slug="auth-test-tenant",
        nit="333333333-3",
        estado="ACTIVO",
        email_contacto="authtest@test.com"
    )
    db.add(tenant)
    db.flush()

    user = Usuarios(
        email="vendedor@authtest.com",
        nombre="Test Vendedor",
        password_hash=hash_password("vendedor123"),
        rol="vendedor",
        estado=True,
        es_superadmin=False,
    )
    db.add(user)
    db.commit()

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "rol": "vendedor"},
        tenant_id=tenant.id,
        rol_en_tenant="vendedor",
    )
    return {"tenant": tenant, "user": user, "token": token}


class TestUnauthenticatedAccess:
    """All protected endpoints must reject unauthenticated requests."""

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_no_token_returns_401(self, client, tenant_and_token, method, path):
        """Request without Authorization header must return 401."""
        tenant_id = str(tenant_and_token["tenant"].id)
        resp = client.request(
            method,
            path,
            headers={"X-Tenant-ID": tenant_id},
        )
        assert resp.status_code in (401, 403, 422), (
            f"{method} {path} without auth returned {resp.status_code}, expected 401/403"
        )

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_invalid_token_returns_401(self, client, tenant_and_token, method, path):
        """Request with a tampered/invalid JWT must return 401."""
        tenant_id = str(tenant_and_token["tenant"].id)
        resp = client.request(
            method,
            path,
            headers={
                "Authorization": "Bearer this.is.not.a.valid.jwt",
                "X-Tenant-ID": tenant_id,
            },
        )
        assert resp.status_code in (401, 403), (
            f"{method} {path} with invalid token returned {resp.status_code}, expected 401/403"
        )

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_expired_token_returns_401(self, client, tenant_and_token, method, path):
        """Request with an expired JWT must return 401."""
        tenant_id = str(tenant_and_token["tenant"].id)
        # Create a token with negative expiry (already expired)
        import time
        from jose import jwt
        from app.config import settings
        expired_payload = {
            "sub": str(tenant_and_token["user"].id),
            "email": tenant_and_token["user"].email,
            "rol": "vendedor",
            "exp": int(time.time()) - 3600,  # expired 1 hour ago
        }
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")

        resp = client.request(
            method,
            path,
            headers={
                "Authorization": f"Bearer {expired_token}",
                "X-Tenant-ID": tenant_id,
            },
        )
        assert resp.status_code in (401, 403), (
            f"{method} {path} with expired token returned {resp.status_code}, expected 401/403"
        )


class TestPublicEndpointsAccessible:
    """Public endpoints must NOT require authentication."""

    @pytest.mark.parametrize("method,path", PUBLIC_ENDPOINTS)
    def test_public_endpoint_no_auth_required(self, client, method, path):
        """Public endpoints should return something other than 401."""
        resp = client.request(method, path)
        assert resp.status_code != 401, (
            f"Public endpoint {method} {path} unexpectedly requires auth (401)"
        )


class TestRoleEscalation:
    """Lower-privilege users must not access admin-only resources."""

    def test_vendedor_cannot_delete_users(self, client, tenant_and_token):
        """Vendedor role must not be allowed to delete users."""
        tenant_id = str(tenant_and_token["tenant"].id)
        resp = client.delete(
            f"/api/v1/usuarios/{uuid4()}",
            headers={
                "Authorization": f"Bearer {tenant_and_token['token']}",
                "X-Tenant-ID": tenant_id,
            },
        )
        assert resp.status_code in (401, 403, 404), (
            f"Vendedor deleting user returned {resp.status_code}, expected 403"
        )

    def test_vendedor_cannot_access_superadmin(self, client, tenant_and_token):
        """Vendedor JWT must not grant access to superadmin endpoints."""
        resp = client.get(
            "/api/v1/superadmin/tenants",
            headers={"Authorization": f"Bearer {tenant_and_token['token']}"},
        )
        assert resp.status_code in (401, 403), (
            f"Vendedor accessing superadmin returned {resp.status_code}, expected 403"
        )
