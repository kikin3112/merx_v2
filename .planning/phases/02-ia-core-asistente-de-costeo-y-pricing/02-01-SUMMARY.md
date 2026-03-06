---
phase: 02-ia-core-asistente-de-costeo-y-pricing
plan: 01
subsystem: backend-ia
tags: [anthropic, sdk, config, tdd, wave-0]
dependency_graph:
  requires: []
  provides:
    - anthropic SDK importable in project virtualenv
    - Settings.ANTHROPIC_API_KEY declared (Optional[str], default None)
    - test stubs RED state for Wave 1 implementation
  affects:
    - backend/app/config.py (new field)
    - pyproject.toml (new dependency)
    - all downstream Wave 1+ plans (unblocked)
tech_stack:
  added:
    - anthropic==0.84.0
    - distro==1.9.0
    - jiter==0.13.0
    - sniffio==1.3.1
  patterns:
    - TDD RED state stubs pattern (Wave 0 → Wave 1 handoff)
    - Optional[str] Field pattern with None default (consistent with SENTRY_DSN)
key_files:
  created:
    - backend/tests/test_servicio_ia_costeo.py
  modified:
    - pyproject.toml
    - backend/app/config.py
decisions:
  - "anthropic>=0.40.0 pinned to >=0.40.0 in pyproject.toml; resolved to 0.84.0 by uv"
  - "ANTHROPIC_API_KEY declared Optional[str] with default=None — service validates at call time, not at startup"
metrics:
  duration: 133s
  completed_date: "2026-03-05T00:29:45Z"
  tasks_completed: 2
  files_modified: 3
---

# Phase 02 Plan 01: SDK Bootstrap and TDD RED State Summary

**One-liner:** Anthropic SDK 0.84.0 installed, ANTHROPIC_API_KEY declared in Settings, and 4 TDD test stubs created in RED state — all Wave 1+ blockers resolved.

---

## What Was Done

Wave 0 resolved the two critical blockers identified in Phase 1 research:
1. Missing `anthropic` dependency (import would fail at wave 1 runtime)
2. Missing `ANTHROPIC_API_KEY` in config (would cause silent failures or require hardcoding)

Both are now resolved, unblocking all downstream Phase 2 plans.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Install anthropic SDK + declare ANTHROPIC_API_KEY | `5e63628` | pyproject.toml, backend/app/config.py |
| 2 | Create test stubs (RED state) | `106f00e` | backend/tests/test_servicio_ia_costeo.py |

---

## Verification Results

- `uv run python -c "import anthropic; print(anthropic.__version__)"` → `0.84.0` (exit 0)
- `settings.ANTHROPIC_API_KEY` → `None` (field exists, defaults to None safely)
- `uv run pytest backend/tests/test_servicio_ia_costeo.py -x -q` → `ModuleNotFoundError: No module named 'app.servicios.servicio_ia_costeo'` (RED state confirmed)
- 4 test stubs valid Python (no syntax errors — ruff passes)

---

## Decisions Made

1. **anthropic resolved to 0.84.0** — uv resolved `>=0.40.0` to the latest available (0.84.0). No upper bound set to allow patch updates.

2. **ANTHROPIC_API_KEY as Optional[str] with None default** — Consistent with SENTRY_DSN pattern. Service code validates at call time rather than failing startup when key is absent. This allows local development without the key.

---

## Deviations from Plan

None — plan executed exactly as written. ruff-format auto-reformatted both config.py and test stubs (string concatenation style, import ordering) — pre-commit hooks applied automatically, staged and recommitted.

---

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| backend/tests/test_servicio_ia_costeo.py exists | FOUND |
| anthropic>=0.40.0 in pyproject.toml | FOUND |
| ANTHROPIC_API_KEY in backend/app/config.py | FOUND |
| commit 5e63628 exists | FOUND |
| commit 106f00e exists | FOUND |
