---
phase: 02-ia-core-asistente-de-costeo-y-pricing
plan: 02
subsystem: backend-ia
tags: [anthropic, claude-haiku, tool_use, decimal, pydantic, socia, tdd, wave-1]

requires:
  - phase: 02-01
    provides: anthropic SDK installed, ANTHROPIC_API_KEY in config, 4 TDD stubs RED

provides:
  - ServicioIACosteo class with analisis_inicial() and chat_libre() methods
  - SOCIA_TOOL constant (Anthropic tool_use definition)
  - SociaAnalisisResponse Pydantic model with Decimal safety validator
  - _AnthropicClientWrapper thin async wrapper for testable mock patching
  - All 4 Wave 0 TDD stubs now GREEN

affects:
  - 02-03 (route that exposes ServicioIACosteo endpoints)
  - 02-04 (frontend that calls Socia endpoints)
  - any plan that needs IA costeo context

tech-stack:
  added: []
  patterns:
    - Thin async wrapper pattern for non-coroutine SDK methods (inspect.iscoroutinefunction compatibility)
    - Pydantic field_validator with mode="before" for Decimal safety from LLM float output
    - Anthropic tool_choice forced (type=tool) for structured Fase 1 output
    - Prompt caching via cache_control ephemeral on system prompt
    - Service delegates ALL CVU calculation to ServicioAnalisisCVU (zero duplication)

key-files:
  created:
    - backend/app/servicios/servicio_ia_costeo.py
  modified: []

key-decisions:
  - "_AnthropicClientWrapper wraps AsyncAnthropic so _client.messages.create is a true async def — required because inspect.iscoroutinefunction returns False on the raw SDK method, causing unittest.mock.patch.object to create MagicMock instead of AsyncMock"
  - "SociaAnalisisResponse Pydantic model with field_validator(mode='before') enforces Decimal(str(v)) on LLM float output — consistent with project NEVER use float rule"
  - "tool_choice type=tool forced in analisis_inicial to prevent free-text fallback from claude-haiku-4-5"

patterns-established:
  - "SDK async wrapper pattern: when third-party SDK coroutine methods fail inspect.iscoroutinefunction, wrap in a class with real async def methods for testability"
  - "LLM Decimal safety: always use Pydantic field_validator(mode='before') with Decimal(str(v)) to coerce LLM float output"
  - "Socia persona: caleña, femenina, accessible language — embed CVU+escenarios in system prompt, target ~500 tokens"

requirements-completed:
  - R1.1

duration: 4min
completed: "2026-03-05"
---

# Phase 02 Plan 02: ServicioIACosteo — Socia IA Orchestration Summary

**AsyncAnthropic wrapper + Pydantic Decimal validator + forced tool_use enabling Socia IA costeo assistant with claude-haiku-4-5, turning all 4 Wave 0 TDD stubs GREEN.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-05T00:52:58Z
- **Completed:** 2026-03-05T00:56:51Z
- **Tasks:** 1 (TDD GREEN phase)
- **Files modified:** 1

## Accomplishments

- `ServicioIACosteo` class implemented with `analisis_inicial()` (Fase 1 tool_use) and `chat_libre()` (Fase 2 free text)
- `_AnthropicClientWrapper` thin async wrapper resolves `inspect.iscoroutinefunction` incompatibility with Anthropic SDK — enables `patch.object` to auto-create `AsyncMock`
- `SociaAnalisisResponse` Pydantic model with `field_validator(mode="before")` ensures `precio_sugerido` and `margen_esperado` are always `Decimal` (never `float`) from LLM output
- Prompt caching (`cache_control: ephemeral`) on system prompt for efficiency
- Tenant isolation enforced via `_get_receta` with `.options().filter(tenant_id, deleted_at)` chain
- All 4 Wave 0 tests GREEN: `test_analisis_inicial_returns_schema`, `test_decimal_safety`, `test_chat_fase2_returns_respuesta`, `test_tenant_isolation`
- Full test suite: 49 passed, 0 new failures (9 pre-existing DB connection errors unrelated to this plan)

## Task Commits

1. **Task 1: Implement ServicioIACosteo — turn all 4 Wave 0 tests GREEN** - `d35875b` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified

- `backend/app/servicios/servicio_ia_costeo.py` - LLM orchestration service: SOCIA_TOOL constant, SociaAnalisisResponse model, _AnthropicClientWrapper, ServicioIACosteo with analisis_inicial + chat_libre (289 lines)

## Decisions Made

1. **`_AnthropicClientWrapper` wraps `AsyncAnthropic`** — `inspect.iscoroutinefunction(client.messages.create)` returns `False` on the Anthropic SDK (the method is dynamically built, not a plain `async def`). Without the wrapper, `patch.object` creates a synchronous `MagicMock` and `await` fails. The wrapper defines a real `async def create(**kwargs)` that delegates to the raw client, making `patch.object` auto-select `AsyncMock`.

2. **Pydantic `field_validator(mode="before")` for Decimal safety** — LLM output via tool_use returns JSON floats (e.g., `25000.0`, `48.5`). The validator calls `Decimal(str(v))` before Pydantic coerces the type, ensuring no float precision loss per project constitution ("NEVER use float for financial calculations").

3. **`tool_choice={"type": "tool", "name": "analisis_costeo"}` forced** — Prevents claude-haiku-4-5 from returning free text in Fase 1. Without forced tool_choice, the model may opt to respond conversationally rather than using the structured tool, breaking schema validation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added `_AnthropicClientWrapper` thin wrapper for SDK async compatibility**
- **Found during:** Task 1 (GREEN phase — running tests)
- **Issue:** `inspect.iscoroutinefunction(AsyncAnthropic().messages.create)` returns `False` because Anthropic SDK wraps methods dynamically. `patch.object` creates a sync `MagicMock`, so `await self._client.messages.create(...)` raises `TypeError: object MagicMock can't be used in 'await' expression`
- **Fix:** Created `_AnthropicMessages` (with real `async def create`) and `_AnthropicClientWrapper` composing it. The wrapper is assigned to `self._client` in `__init__`, so tests patch `servicio._client.messages.create` correctly
- **Files modified:** `backend/app/servicios/servicio_ia_costeo.py`
- **Verification:** All 4 tests pass GREEN after fix
- **Committed in:** `d35875b` (part of task commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug: SDK async compatibility)
**Impact on plan:** Required for tests to pass. No scope creep — wrapper is minimal (~15 lines) and stays internal to the service.

## Issues Encountered

- Anthropic SDK `messages.create` not recognized as coroutine by `inspect.iscoroutinefunction` — resolved via thin wrapper pattern (see Deviations above).

## Next Phase Readiness

- `ServicioIACosteo` is ready to be exposed via FastAPI routes (Plan 02-03)
- `analisis_inicial(receta_id, precio_referencia)` and `chat_libre(receta_id, messages)` are the two entry points
- `ANTHROPIC_API_KEY` must be set in `.env` for production calls (validated at call time, not startup)
- 4 tests serve as regression guard for all future refactoring

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| backend/app/servicios/servicio_ia_costeo.py exists | FOUND |
| 02-02-SUMMARY.md exists | FOUND |
| commit d35875b exists | FOUND |

---
*Phase: 02-ia-core-asistente-de-costeo-y-pricing*
*Completed: 2026-03-05*
