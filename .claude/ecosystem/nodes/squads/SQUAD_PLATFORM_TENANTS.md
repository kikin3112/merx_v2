# Squad: Platform & Tenants

> Cross-functional squad owning the foundational platform — multi-tenancy, auth, and cross-cutting services.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L4 — Domain Team |
| **Model** | Spotify Squad |
| **Scope** | `tenants`, `auth`, `usuarios`, `compras`, `sse`, `health` |
| **Reports To** | Head of Product (functional), VP Eng (technical) |
| **Special Note** | This is the most critical squad — all other squads depend on platform services |

---

## Composition

| Role | Responsibility |
|------|---------------|
| **Product Owner** | Prioritizes multi-tenancy, registration, onboarding, permissions, cross-cutting features |
| **Backend Dev (Senior)** | Tenant service (56k+ lines), multi-tenant isolation, JWT auth, roles/permissions |
| **Backend Dev** | Purchase endpoints, SSE (real-time events), health checks, user management |
| **Frontend Dev** | TenantsPage, LoginPage, RegistroPage, SelectTenantPage, DashboardPage, onboarding |
| **QA Engineer** | Tenant isolation testing, auth penetration tests, permissions validation |

---

## Module Detail

| Module | Key Features | Complexity |
|--------|-------------|-----------|
| `tenants` | Multi-tenant management, tenant config, plan management, data isolation | Critical |
| `auth` | JWT authentication, refresh tokens, password reset, OAuth (future) | High |
| `usuarios` | User CRUD, role assignment, invite flows, profile management | Medium |
| `compras` | Purchase orders, supplier management, receiving | Medium |
| `sse` | Server-Sent Events for real-time updates (stock alerts, notifications) | High |
| `health` | System health checks, dependency status, uptime monitoring | Low |

---

## Key Flows

```
Signup → Tenant Created → User Registered → Auth (JWT) → Select Tenant → Dashboard
                                                            ↓
                                                     Onboarding Flow
                                                            ↓
                                                   First Module Setup

SSE: Event Published → Tenant-scoped Channel → Connected Clients Receive Update
```

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Signup data | Users (PLG) | | Tenant context | ALL other squads |
| Auth requests | All users | | JWT tokens | All client sessions |
| Permission configs | Admin users | | Real-time events (SSE) | All connected clients |
| System metrics | Infrastructure | | Health status | DevOps monitoring |
| Purchase data | Users | | Purchase records | Squad: Accounting + Inventory |

---

## Metrics

| Metric | Target |
|--------|--------|
| Tenant creation success rate | 100% |
| Auth response time (p95) | < 100ms |
| Tenant isolation compliance | 100% (zero cross-tenant data leaks) |
| SSE event delivery latency | < 500ms |
| Onboarding completion rate | ≥ 70% |
| Permission test coverage | 100% of role combinations |
| Sprint commitment completion | ≥ 80% |

---

## Critical Rules (Due to Platform Impact)

1. **Tenant isolation is highest priority** — every code change must be verified for isolation
2. **Zero-downtime deploys required** — platform changes cannot disrupt other squads
3. **Auth changes require security review** — mandatory pre-merge review by Head Security
4. **SSE backwards compatibility** — event schema changes must be backwards-compatible
5. **Health checks must be comprehensive** — verify all dependencies (DB, cache, external services)
6. **Purchase module stays simple** — avoid over-engineering until Phase 2+ demand

---

## Dependencies

| Depends On | For |
|-----------|-----|
| Guild: Security | Auth security reviews, penetration testing |
| Guild: DevOps | Infrastructure scaling for tenant growth |
| Guild: Architecture | Multi-tenant data model governance |
| All squads depend on this squad | Tenant context, auth, permissions |
