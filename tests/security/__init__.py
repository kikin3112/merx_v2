"""
Security test suite for Merx v2 / Chandelier ERP.

Tests:
- Tenant isolation (cross-tenant data access attempts)
- Authentication bypass probes
- Rate limiting enforcement
- SQL injection resistance

Run with:
    pytest tests/security/ -v --cov=backend/app
"""
