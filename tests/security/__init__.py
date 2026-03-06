"""
Security test suite for chandelierp.

Tests:
- Tenant isolation (cross-tenant data access attempts)
- Authentication bypass probes
- Rate limiting enforcement
- SQL injection resistance

Run with:
    pytest tests/security/ -v --cov=backend/app
"""
