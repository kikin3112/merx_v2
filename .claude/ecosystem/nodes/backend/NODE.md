# L3 — Head of Backend Engineering

> Architect and guardian of the server-side systems powering chandelierp.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L3 — Functional Direction |
| **Reports To** | VP Engineering (L2) |
| **Pillar** | Core Engineering |
| **Stack** | FastAPI, Python, SQLAlchemy, Alembic, PostgreSQL |
| **Modules Governed** | auth, tenants, facturas, ventas, inventarios, contabilidad, CRM, terceros, compras, recetas, PQRS, SSE, health |

---

## Purpose

Lead the **backend architecture**, ensure **multi-tenant data isolation**, and maintain **API performance and reliability** across all ERP modules.

---

## Responsibilities

| Area | Responsibility |
|------|---------------|
| **Architecture** | FastAPI service patterns, data models, API design guidelines |
| **Multi-tenancy** | Tenant isolation strategy, data partitioning, cross-tenant security |
| **Data modeling** | SQLAlchemy models, Alembic migrations, schema evolution |
| **API standards** | RESTful conventions, error handling, pagination, filtering |
| **Performance** | Query optimization, connection pooling, caching strategy |
| **Code review** | Backend code review standards and mentorship |
| **Module ownership** | Assign backend ownership per ERP module across squads |

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Feature specs | Head Product | | API endpoints | Frontend squads |
| Architecture RFCs | Guild Architecture | | Data migration scripts | DevOps |
| Security scan results | Head Security | | API documentation | Technical Writer |
| Performance benchmarks | DevOps | | Design docs for complex features | Architecture Committee |
| Database metrics | DBA / DevOps | | Code review feedback | Squad developers |

---

## Metrics

| Metric | Target |
|--------|--------|
| API response time (p95) | < 200ms |
| Test coverage (backend) | ≥ 80% |
| Migration success rate | 100% (zero data loss) |
| Code review turnaround | < 24 hours |
| Open critical bugs (backend) | 0 at sprint end |
| API documentation coverage | 100% of public endpoints |

---

## Operational Rules

1. **Multi-tenant isolation is sacrosanct** — every query must be tenant-scoped, no exceptions
2. **Design doc for cross-module changes** — any change touching 2+ modules needs written design
3. **Alembic migrations are irreversible-safe** — always include rollback scripts
4. **No raw SQL in service layer** — use SQLAlchemy ORM; raw SQL only in optimized queries with justification
5. **API versioning** — breaking changes require new API version
6. **Performance budget** — every new endpoint must meet p95 < 200ms before merge
