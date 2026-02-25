"""
Pytest fixtures for all tests.
Provides test database, sessions, and authenticated clients.
"""

from uuid import uuid4

import pytest
from app.datos.db import Base, get_db
from app.datos.modelos import Usuarios
from app.datos.modelos_tenant import Tenants
from app.main import app
from app.utils.seguridad import create_access_token, hash_password
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Use in-memory SQLite for faster tests
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


@pytest.fixture(scope="function")
def db_session(engine):
    """Create isolated test database session with automatic rollback."""
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


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


@pytest.fixture
def tenant_admin_token(db_session: Session):
    """
    Create tenant + admin user, return JWT token with tenant context.

    Returns:
        dict: {
            "token": str,
            "tenant_id": str,
            "user_id": str,
            "tenant": Tenants,
            "user": Usuarios
        }
    """
    # Create tenant
    tenant = Tenants(nombre="Test Tenant", nit="900123456-7", estado="ACTIVO", email_contacto="test@test.com")
    db_session.add(tenant)
    db_session.flush()

    # Create admin user
    user = Usuarios(
        email="admin@test.com",
        nombre="Test Admin",
        hash_password=hash_password("test123"),
        rol="admin",
        estado=True,
        es_superadmin=False,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "rol": "admin"}, tenant_id=tenant.id, rol_en_tenant="admin"
    )

    return {"token": token, "tenant_id": str(tenant.id), "user_id": str(user.id), "tenant": tenant, "user": user}


@pytest.fixture
def vendedor_token(db_session: Session, tenant_admin_token):
    """Create vendedor user and return JWT token."""
    tenant_id = uuid4(tenant_admin_token["tenant_id"])

    user = Usuarios(
        email="vendedor@test.com",
        nombre="Test Vendedor",
        hash_password=hash_password("test123"),
        rol="vendedor",
        estado=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "rol": "vendedor"},
        tenant_id=tenant_id,
        rol_en_tenant="vendedor",
    )

    return {"token": token, "user_id": str(user.id), "tenant_id": str(tenant_id)}


@pytest.fixture
def contador_token(db_session: Session, tenant_admin_token):
    """Create contador user and return JWT token."""
    tenant_id = uuid4(tenant_admin_token["tenant_id"])

    user = Usuarios(
        email="contador@test.com",
        nombre="Test Contador",
        hash_password=hash_password("test123"),
        rol="contador",
        estado=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "rol": "contador"},
        tenant_id=tenant_id,
        rol_en_tenant="contador",
    )

    return {"token": token, "user_id": str(user.id), "tenant_id": str(tenant_id)}
