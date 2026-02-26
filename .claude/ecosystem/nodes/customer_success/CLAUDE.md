# Customer Success Node — Claude Code Instructions

## Scope
PQRS ticket system, tenant onboarding, support flows, retention.

## Source Code
- Backend: `backend/app/datos/modelos_pqrs.py`, `backend/app/servicios/servicio_pqrs.py`, `backend/app/rutas/pqrs.py`
- Frontend: `frontend/src/pages/SoportePage.tsx`
- Onboarding: `frontend/src/hooks/useOnboarding.ts`

## PQRS System
- 5 endpoints: create, list (tenant), get, reply, close.
- Tenant isolation: uses `get_tenant_id_from_token`.
- JSONB field for replies history.
- NOT visible in superadmin TenantsPage (by design — tickets are per-tenant).

## Onboarding Wizard
- 5-step wizard for new tenants.
- Triggered by `useOnboarding.ts` when tenant has 0 products.
- State persisted in localStorage.

## Retention KPIs
- Track: ticket resolution time, onboarding completion rate.
- Churn signal: tenant goes from `activo` → `suspendido`.

## Node Details
`NODE.md` in this directory.
