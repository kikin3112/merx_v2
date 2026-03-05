---
phase: 2
slug: ia-core-asistente-de-costeo-y-pricing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-04
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), React Testing Library (frontend) |
| **Config file** | `backend/pyproject.toml` (pytest), `frontend/vite.config.ts` (vitest) |
| **Quick run command** | `cd backend && pytest tests/test_servicio_ia_costeo.py -x -q` |
| **Full suite command** | `cd backend && pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && pytest tests/test_servicio_ia_costeo.py -x -q`
- **After every plan wave:** Run `cd backend && pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | R1.1 | install | `cd backend && uv run python -c "import anthropic; print('OK')"` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 0 | R1.1 | unit-stub | `cd backend && pytest tests/test_servicio_ia_costeo.py -x -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | R1.1 | unit | `cd backend && pytest tests/test_servicio_ia_costeo.py::test_analisis_inicial -x -q` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | R1.1 | unit | `cd backend && pytest tests/test_servicio_ia_costeo.py::test_decimal_safety -x -q` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | R1.1 | integration | `cd backend && pytest tests/test_recetas_endpoint.py::test_asistente_ia -x -q` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 3 | R1.1 | manual | N/A — browser UI test | N/A | ⬜ pending |
| 02-04-02 | 04 | 3 | R1.1 | manual | N/A — browser chat test | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_servicio_ia_costeo.py` — stubs for R1.1 (mocked Anthropic client)
- [ ] `backend/tests/conftest.py` — verify shared fixtures exist (tenant mock, DB session)
- [ ] `anthropic` package in `backend/pyproject.toml` — `uv add anthropic`
- [ ] `ANTHROPIC_API_KEY` in `backend/app/config.py` Settings class

*Wave 0 must complete before Wave 1 backend service implementation.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Modal opens on "Consultar a Socia" button click | R1.1 | Browser UI interaction | Open RecetasPage, select recipe, click button, verify modal appears |
| Fase 1 analysis renders with all 6 schema fields | R1.1 | Visual verification of React render | Verify precio_sugerido, margen_esperado, escenario_recomendado, justificacion, alertas, mensaje_cierre all display |
| "¿Tienes más preguntas?" → chat appears | R1.1 | Conditional UI state | Click Sí on prompt, verify chat bubble interface appears |
| Chat history clears on modal close | R1.1 | State destruction verification | Type messages, close modal, reopen — verify history is gone |
| Socia tone is cálida/caleña | R1.1 | Qualitative LLM output review | Verify response uses accessible language, no corporate tone, caleño flavor |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
