# QA Node — Claude Code Instructions

## Scope
Test strategy, coverage enforcement, regression prevention, quality gates.

## Source Code
- Backend tests: `backend/tests/`
- Frontend tests: `frontend/src/**/*.test.tsx`
- Test runner: `pytest` (backend), Vitest (frontend)

## Coverage Targets
- Backend: 80% minimum (logical path coverage).
- Frontend: cover all store transitions and component interactions.
- Any new feature requires tests before merging.

## Quality Gates (CI/CD)
- All PRs run test suite — failures block merge.
- Pre-commit: ruff (lint+format), bandit (security), gitleaks (secrets).
- Known issues: `frontend/DocumentDetail.tsx:72` setState-in-effect (pre-existing).

## Test Strategy
- Unit: pure business logic in `servicios/`.
- Integration: API endpoints with tenant isolation validation.
- E2E: critical user flows (create invoice, adjust inventory, register tenant).

## Node Details
`NODE.md` in this directory.
