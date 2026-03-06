# Merx v2 — Project State

**Last Updated:** 2026-03-04
**Active Milestone:** Propuesta de Valor 2026 (v2.0)
**Current Phase:** Phase 1 — Auditoría Integral

---

## Stack (confirmed production)

| Layer | Technology | Hosting |
|-------|-----------|---------|
| Backend | FastAPI + SQLAlchemy + Alembic | Railway |
| Frontend | React + Zustand + React Query + Vite | Vercel |
| Auth | Clerk (dev keys `pk_test_*`) | Clerk Cloud |
| Database | PostgreSQL + RLS | Railway |
| Storage | AWS S3 | AWS |
| Analytics | GA4 | Google |

**Backend URL:** Railway proxy `nozomi.proxy.rlwy.net:47298`
**Alembic head:** `e7f8a9b0c1d2` (2026-03-02)

---

## Completed PRs (reference)

| PR | Feature |
|----|---------|
| #94–#99 | Recetas, merma, conversión unidades, costos estándar |
| #100–#102 | Deploy/migration fixes |
| #103 | CIF mensual distribuido en `produccion_mensual_esperada` |
| #104 | Fix CVU: unit conversion + CIF distribution |

---

## Architectural invariants (non-negotiable)

- `tenant_id` on every business entity — RLS enforces isolation at DB level
- Financial calculations use `Decimal` (never `float`)
- Layer strictness: `rutas/` = HTTP only, `servicios/` = business logic, `datos/` = DB
- Async `def` for all I/O routes
- React Query for all server data (no manual Zustand cache of server responses)

---

## Active modules (production-ready)

- Auth (Clerk → FastAPI JWT)
- Tenants & multi-tenancy
- Productos + Inventario (compound module)
- Facturas + POS
- Recetas + CVU (costeo avanzado con CIF distribuido)
- Contabilidad
- CRM (under construction flag active)
- PQRS/Soporte

---

## Restrictions for new development

- Do NOT break existing modules
- Do NOT add alembic migrations until Phase 4+
- Do NOT change `modelos.py` until Phase 2+
- All new features MUST inherit tenant isolation automatically
- Clerk metadata = viable base for freemium feature flags
