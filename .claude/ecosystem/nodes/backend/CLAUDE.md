# Backend Node — Claude Code Instructions

## Scope
Server-side systems: FastAPI, SQLAlchemy, Alembic, PostgreSQL, multi-tenant ERP.

## Source Code
- Primary: `/backend/`
- Entry point: `backend/app/main.py`
- Layers: `backend/app/rutas/` · `backend/app/servicios/` · `backend/app/datos/`
- Migrations: `backend/alembic/versions/`

## Architecture Rules (NON-NEGOTIABLE)
- `rutas/` → HTTP only. ZERO business logic.
- `servicios/` → ALL business logic and orchestration.
- `datos/` → DB models and queries only.
- Multi-table writes MUST use transactions.
- NEVER use `float` for money — use `Decimal`.
- EVERY query MUST include `tenant_id` filter.

## Key Patterns
- Dependency injection via `Depends()` for DB sessions and user context.
- Auth context: use `get_tenant_id_from_token` (NOT `tenant_id_context`).
- SSE endpoint keeps `--workers 1` (SSEManager is in-memory).

## Run Commands
```bash
uvicorn app.main:app --reload        # dev
uvicorn app.main:app --workers 1     # prod (SSE safe)
alembic upgrade head                  # migrations
pytest                                # tests
```

## Agent
`.claude/agents/backend-engineer.md`

## Node Details
`NODE.md` in this directory.
