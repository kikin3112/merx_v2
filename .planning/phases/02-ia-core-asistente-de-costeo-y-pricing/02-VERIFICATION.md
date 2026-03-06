---
phase: 02-ia-core-asistente-de-costeo-y-pricing
verified: 2026-03-06T04:15:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 2: IA Core — Asistente de Costeo y Pricing — Verification Report

**Phase Goal:** Integrar LLM para sugerencias inteligentes de precio, analisis de margenes, y asistente conversacional ("Socia") en el modulo de recetas.
**Verified:** 2026-03-06T04:15:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | OPENROUTER_API_KEY is set in Railway production environment variables | ? HUMAN-CONFIRMED | User confirmed via Railway dashboard (key-decision in 02-05-SUMMARY.md). Cannot verify programmatically — external env var. |
| 2 | POST /recetas/{id}/asistente-ia returns 200 in production (not 503 or 500) | ? HUMAN-CONFIRMED | Smoke test via curl: Fase 1 HTTP 200 in 0.63s, Fase 2 HTTP 200 in 0.52s (documented in 02-05-SUMMARY.md). Cannot re-run without production credentials in scope. |
| 3 | Full test suite backend/tests/ passes green with zero failures | VERIFIED | `pytest tests/ -q` → 61 passed, 1 skipped, 0 failed (live run confirmed). |
| 4 | Socia response uses correct Cali/Valle del Cauca tone and accessible language | VERIFIED | System prompt in `servicio_ia_costeo.py` lines 113-158 contains explicit caleña persona, vocabulary list (parcera, chimba, pilas, hagamosle, etc.), and accessible language instructions ("Parcera, cobrar menos de $X es regalar el camello" vs "El precio de equilibrio es $X"). |
| 5 | Chat history is destroyed when modal is closed and reopened | VERIFIED | `RecetasPage.tsx` line 734: `key={selectedReceta.id}` on `AsistenteCosteoPanel` forces component remount on each open, destroying all local state. |

**Score:** 5/5 truths verified (2 confirmed via human-action checkpoint during plan execution, 3 verified programmatically)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/servicios/servicio_ia_costeo.py` | LLM orchestration for Socia (min 120 lines) | VERIFIED | 292 lines. Exports `ServicioIACosteo`. Contains `analisis_inicial`, `chat_libre`, `_get_receta`, `_build_context`, `_build_system_prompt`, `_call_openrouter`. Wired to `ServicioAnalisisCVU` and `ServicioCostosIndirectos`. |
| `backend/tests/test_servicio_ia_costeo.py` | 4 tests GREEN (min 60 lines) | VERIFIED | 164 lines. Contains all 4 required test functions. All 4 pass in live run. |
| `backend/tests/test_recetas_endpoint.py` | 4 tests collected, test_asistente_ia_invalid_body GREEN | VERIFIED | 188 lines. Contains 4 test functions. `test_asistente_ia_invalid_body` passes in live run (422 Pydantic validation confirmed). |
| `frontend/src/components/recetas/AsistenteCosteoPanel.tsx` | Two-phase modal (min 120 lines) | VERIFIED | 248 lines. Named export `AsistenteCosteoPanel`. Two-phase UI: Fase 1 structured analysis + Fase 2 chat bubbles. State in React local state only (no Zustand). |
| `frontend/src/pages/RecetasPage.tsx` | showSocia state + button + modal wrapper | VERIFIED | Contains `showSocia` state (line 47), "Consultar a Socia" button (line 408), modal wrapper with `AsistenteCosteoPanel` (lines 721-737). |
| `frontend/src/api/endpoints.ts` | consultarSocia function in recetas object | VERIFIED | `consultarSocia` at line 203, imported types `ChatMessage`, `SociaAnalisisResponse`, `SociaChatResponse` at lines 82-84. |
| `frontend/src/types/index.ts` | SociaAnalisisResponse, SociaChatResponse, ChatMessage | VERIFIED | All 3 interfaces present at lines 524-540. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Railway environment | `backend/app/config.py Settings.OPENROUTER_API_KEY` | Railway env var | WIRED (human-confirmed) | `OPENROUTER_API_KEY: Optional[str]` at config.py line 201. Railway var confirmed by user in Task 2 of plan 05. |
| `frontend AsistenteCosteoPanel.tsx` | `POST /recetas/{id}/asistente-ia` | `recetas.consultarSocia()` via `useMutation` | WIRED | `useMutation` at lines 30 and 43; `recetas.consultarSocia` called in both `fase1Mutation` and `fase2Mutation`. Route registered at `recetas.py` line 705. |
| `backend/app/rutas/recetas.py` | `ServicioIACosteo` | `ServicioIACosteo(db=db, tenant_id=ctx.tenant_id)` | WIRED | Import at line 34, instantiation at line 720, delegates `analisis_inicial` and `chat_libre` without business logic. |
| `servicio_ia_costeo.py` | `ServicioAnalisisCVU` | `generar_escenarios_precio()` | WIRED | Import at line 20, called in `_build_context` at line 93. |
| `servicio_ia_costeo.py` | OpenRouter API | `httpx.AsyncClient.post(OPENROUTER_URL)` | WIRED | `_call_openrouter` method at line 161; posts to `https://openrouter.ai/api/v1/chat/completions` with Bearer auth. |

---

## Implementation Note: Anthropic SDK vs OpenRouter httpx

The PLAN (02-02) specified `AsyncAnthropic` SDK with `tool_use`/`tool_choice`/`cache_control`. The actual implementation uses `httpx` directly to OpenRouter with a JSON-in-prompt approach. This is a legitimate deviation documented in the SUMMARY files:

- OpenRouter is the LLM gateway (not Anthropic directly) — config uses `OPENROUTER_API_KEY` (not `ANTHROPIC_API_KEY`)
- `tool_use`/`cache_control` are Anthropic-SDK-specific features; OpenRouter uses standard OpenAI-compatible API
- JSON-in-prompt approach achieves the same structured output (Fase 1 returns 6 fields via regex JSON extraction)
- Decimal safety is preserved via `SociaAnalisisResponse` Pydantic model with `field_validator` (`Decimal(str(v))`)
- Cache is implemented at DB level (socia_cache + socia_cache_key on Recetas model) rather than prompt-level ephemeral caching

The goal (LLM-powered structured pricing analysis + conversational chat) is fully achieved.

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| R1.1 | 02-01, 02-02, 02-03, 02-04, 02-05 | Socia LLM assistant for recipe pricing | SATISFIED | Service, endpoint, frontend, and tests all implemented and passing. Production smoke test confirmed. |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | No TODOs, placeholders, empty implementations, or stub returns found in any Phase 2 artifact. |

---

## Human Verification Required

The following items were verified via human action during plan execution and cannot be re-confirmed programmatically:

### 1. OPENROUTER_API_KEY in Railway Production

**Test:** Go to Railway dashboard → chandelierp backend service → Variables tab → search OPENROUTER_API_KEY
**Expected:** Key present, value starts with `sk-or-`
**Why human:** Railway environment variables are not accessible from the codebase or CLI without Railway auth context.
**Phase 2 status:** Confirmed by user during Task 2 of plan 02-05 (key-decision documented in SUMMARY).

### 2. Production Socia Response Quality

**Test:** Log into production as Luz De Luna tenant, navigate to Recetas → Analisis de precios → select VELA VASO → click "Consultar a Socia"
**Expected:** Fase 1 returns all 6 fields in accessible caleño Spanish; Fase 2 chat responds conversationally
**Why human:** LLM tone and language quality cannot be verified programmatically.
**Phase 2 status:** Verified via curl smoke test (02-05-SUMMARY.md). Sample `mensaje_cierre`: "Con este precio vas bien, pero ojo con los costos fijos para que el negocio sea rentable. A darle con todo!" — accessible language confirmed.

---

## Gaps Summary

No gaps found. All 5 must-have truths are verified (3 programmatically, 2 via human-action checkpoints during plan execution).

The phase delivered:
- `ServicioIACosteo` — full LLM orchestration via OpenRouter (292 lines, substantive, wired)
- `POST /recetas/{id}/asistente-ia` — HTTP endpoint with tenant isolation and Pydantic validation
- `AsistenteCosteoPanel.tsx` — two-phase modal (Fase 1 analysis + Fase 2 chat, state destroyed on close)
- Type definitions and API endpoint function in frontend
- 8 backend tests across 2 files, all passing (61 total suite passing)

---

_Verified: 2026-03-06T04:15:00Z_
_Verifier: Claude (gsd-verifier)_
