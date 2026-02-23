"""
SQL injection security tests.

Probes FastAPI endpoints with common SQLi payloads.
Verifies that SQLAlchemy ORM parameterization prevents injection.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.main import app
from app.datos.db import Base, get_db
from app.datos.modelos import Usuarios
from app.datos.modelos_tenant import Tenants
from app.utils.seguridad import hash_password, create_access_token


TEST_DB_URL = "sqlite:///:memory:"

# Classic SQL injection payloads
SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1--",
    "'; DROP TABLE productos;--",
    "' UNION SELECT null, username, password FROM usuarios--",
    "1' AND SLEEP(5)--",
    "1 OR 1=1",
    "' OR 'x'='x",
    "admin'--",
    "' OR ''='",
    "\"; DROP TABLE usuarios; --",
    "' AND 1=2 UNION SELECT 1,2,3--",
    "%27%20OR%20%271%27%3D%271",  # URL-encoded version
]

# Endpoints that accept user input as query params or path params
INJECTABLE_ENDPOINTS = [
    # (method, path_template, param_location)
    ("GET",  "/api/v1/productos",          "query",  "search"),
    ("GET",  "/api/v1/clientes",           "query",  "search"),
    ("GET",  "/api/v1/usuarios",           "query",  "search"),
]


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def set_pragma(dbapi_conn, _):
        dbapi_conn.cursor().execute("PRAGMA foreign_keys=ON")

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
def auth_headers(db: Session):
    """Provide valid auth headers for injection testing."""
    tenant = Tenants(
        nombre="SQLi Test Tenant",
        nit="444444444-4",
        estado="ACTIVO",
        email_contacto="sqli@test.com"
    )
    db.add(tenant)
    db.flush()

    user = Usuarios(
        email="sqli_admin@test.com",
        nombre="SQLi Admin",
        hash_password=hash_password("sqli_test_pass"),
        rol="admin",
        estado=True,
        es_superadmin=False,
    )
    db.add(user)
    db.commit()

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "rol": "admin"},
        tenant_id=tenant.id,
        rol_en_tenant="admin",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant.id),
    }


@pytest.fixture(scope="module")
def client(db: Session):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


class TestSQLInjectionQueryParams:
    """Verify that query parameter injection is neutralized by ORM parameterization."""

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    @pytest.mark.parametrize("method,path,_loc,param", INJECTABLE_ENDPOINTS)
    def test_sqli_payload_does_not_crash_server(
        self, client, auth_headers, payload, method, path, _loc, param
    ):
        """
        SQLi payloads must not cause 500 errors.
        Either the app returns a safe empty result or a 4xx error.
        A 500 may indicate the payload leaked into raw SQL.
        """
        resp = client.request(
            method,
            path,
            params={param: payload},
            headers=auth_headers,
        )
        assert resp.status_code != 500, (
            f"SQLi payload caused 500 on {method} {path}?{param}={payload!r}. "
            "Possible SQL injection vulnerability."
        )

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS[:5])  # Subset for path params
    def test_sqli_in_path_param_does_not_crash(self, client, auth_headers, payload):
        """Path parameter injection should return 422 (validation) or 404, not 500."""
        resp = client.get(
            f"/api/v1/productos/{payload}",
            headers=auth_headers,
        )
        assert resp.status_code != 500, (
            f"SQLi in path param caused 500: {payload!r}"
        )
        # UUIDs are strictly validated — payload should fail with 422 or 404
        assert resp.status_code in (400, 404, 422), (
            f"Expected 422/404 for invalid path param, got {resp.status_code}"
        )


class TestLoginEndpointSQLi:
    """Login endpoint must resist SQL injection in credentials."""

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS[:8])
    def test_sqli_in_login_email(self, client, payload):
        """Injecting SQLi into email field must not bypass auth or cause 500."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": payload, "password": "anypassword"},
        )
        assert resp.status_code != 500, (
            f"SQLi in login email caused 500: {payload!r}"
        )
        # Should return auth failure, not success
        assert resp.status_code in (400, 401, 422, 429), (
            f"Login with SQLi payload returned unexpected {resp.status_code}"
        )

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS[:8])
    def test_sqli_in_login_password(self, client, payload):
        """Injecting SQLi into password field must not bypass auth."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "legit@user.com", "password": payload},
        )
        assert resp.status_code != 500, (
            f"SQLi in login password caused 500: {payload!r}"
        )
        assert resp.status_code in (400, 401, 422, 429), (
            f"Login with SQLi password returned unexpected {resp.status_code}"
        )
