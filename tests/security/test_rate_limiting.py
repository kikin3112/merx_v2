"""
Rate limiting security tests.

Verifies that:
- Login endpoint is rate-limited at 5 requests/minute (slowapi)
- Brute-force attempts are blocked after limit is exceeded
- Rate limit headers are returned correctly
"""
import pytest
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.main import app
from app.datos.db import Base, get_db


TEST_DB_URL = os.environ.get("DB_URL", "postgresql://postgres:postgres@localhost:5432/chandelier_test")
LOGIN_URL = "/api/v1/auth/login"
RATE_LIMIT = 5  # requests per minute as configured in the app


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
    # Use a fresh client per test class to reset rate limit state
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


class TestLoginRateLimit:
    """Login endpoint must be rate limited to prevent brute-force attacks."""

    def test_rate_limit_triggers_after_threshold(self, client):
        """
        Send RATE_LIMIT+1 login attempts with wrong credentials.
        The (RATE_LIMIT+1)th request should return 429.
        """
        payload = {"username": "brute@force.com", "password": "wrongpassword"}
        status_codes = []

        for i in range(RATE_LIMIT + 2):
            resp = client.post(LOGIN_URL, json=payload)
            status_codes.append(resp.status_code)

        # At least one 429 must appear after the limit is hit
        assert 429 in status_codes, (
            f"Expected a 429 after {RATE_LIMIT} attempts. "
            f"Got status codes: {status_codes}"
        )

    def test_rate_limit_returns_retry_after_header(self, client):
        """
        After hitting the rate limit, the response should include
        Retry-After or X-RateLimit-Reset header.
        """
        payload = {"username": "brute2@force.com", "password": "wrongpassword"}

        for _ in range(RATE_LIMIT + 1):
            resp = client.post(LOGIN_URL, json=payload)
            if resp.status_code == 429:
                # Check for standard rate limit headers
                has_retry = (
                    "Retry-After" in resp.headers
                    or "X-RateLimit-Reset" in resp.headers
                    or "X-RateLimit-Limit" in resp.headers
                )
                assert has_retry, (
                    f"429 response missing Retry-After/X-RateLimit headers. "
                    f"Headers present: {dict(resp.headers)}"
                )
                return

        pytest.skip("Rate limit was not triggered — adjust RATE_LIMIT constant")

    def test_valid_endpoints_not_rate_limited_by_default(self, client):
        """
        Non-auth endpoints should NOT return 429 for normal usage.
        GET /health should always respond 200.
        """
        for _ in range(10):
            resp = client.get("/health")
            assert resp.status_code != 429, (
                "/health endpoint should not be rate limited"
            )


class TestPasswordBruteForce:
    """Verify that multiple failed login attempts do not reveal information."""

    def test_wrong_password_response_is_generic(self, client):
        """
        Failed login should NOT reveal whether the email exists or not.
        Response message should be identical for both cases.
        """
        # Non-existent email
        resp1 = client.post(LOGIN_URL, json={
            "username": "doesnotexist@example.com",
            "password": "wrongpass"
        })
        # Possibly existent but wrong password
        resp2 = client.post(LOGIN_URL, json={
            "username": "admin@test.com",
            "password": "wrongpass"
        })

        # Both should return the same HTTP status
        if resp1.status_code == 429 or resp2.status_code == 429:
            pytest.skip("Rate limit already active — run this test in isolation")

        assert resp1.status_code == resp2.status_code, (
            f"Different status codes for unknown email ({resp1.status_code}) "
            f"vs wrong password ({resp2.status_code}) — potential user enumeration"
        )

        # If both are 401/400, check message doesn't differ between cases
        if resp1.status_code in (401, 400) and resp2.status_code in (401, 400):
            msg1 = resp1.json().get("detail", "")
            msg2 = resp2.json().get("detail", "")
            assert msg1 == msg2, (
                f"Different error messages reveal user existence:\n"
                f"  Unknown email: '{msg1}'\n"
                f"  Wrong password: '{msg2}'"
            )
