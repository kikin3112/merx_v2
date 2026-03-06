---
phase: 02-ia-core-asistente-de-costeo-y-pricing
plan: "04"
subsystem: frontend
tags: [socia, ia, modal, recetas, chat, pricing]
dependency_graph:
  requires: [02-03]
  provides: [socia-modal-ui, AsistenteCosteoPanel, consultarSocia-endpoint]
  affects: [frontend/src/pages/RecetasPage.tsx, frontend/src/components/recetas/]
tech_stack:
  added: []
  patterns: [useMutation-two-phase, key-remount-state-reset, React-local-chat-state]
key_files:
  created:
    - frontend/src/components/recetas/AsistenteCosteoPanel.tsx
  modified:
    - frontend/src/pages/RecetasPage.tsx
    - frontend/src/api/endpoints.ts
    - frontend/src/types/index.ts
decisions:
  - key={selectedReceta.id} on AsistenteCosteoPanel forces remount on recipe change — no manual cleanup needed
  - Chat history in React local state only, destroyed on modal close (as per locked decision from 02-03)
  - Fase 1 fires automatically on mount, Fase 2 revealed only on user request (reduces friction)
  - No default export — named export AsistenteCosteoPanel for refactoring safety
metrics:
  duration: ~240s
  completed: "2026-03-04"
  tasks_completed: 2
  files_changed: 4
---

# Phase 02 Plan 04: Socia Frontend Modal Summary

**One-liner:** Two-phase Socia modal with auto-firing Fase 1 analysis and optional Fase 2 chat wired into RecetasPage analisis tab.

---

## What Was Built

### Task 1: Types and Endpoint Function (commit: 8ef9ae5)

Added to `frontend/src/types/index.ts`:
- `ChatMessage` — `{ role: 'user' | 'assistant'; content: string }`
- `SociaAnalisisResponse` — 6 fields with `precio_sugerido`/`margen_esperado` typed as `string` (FastAPI serializes Decimal as string)
- `SociaChatResponse` — `{ respuesta: string }`

Added to `frontend/src/api/endpoints.ts`:
- `consultarSocia(id, data)` — POSTs to `/recetas/{id}/asistente-ia`, typed as `SociaAnalisisResponse | SociaChatResponse`
- Imported the 3 new types in the existing import block

### Task 2: AsistenteCosteoPanel + RecetasPage integration (commit: 68ba92a)

**AsistenteCosteoPanel.tsx** (new file, 198 lines):
- 4 states: `cargando` | `analisis` | `chat` | `error`
- `fase1Mutation`: fires on mount via `useEffect`, renders full structured analysis
- `fase2Mutation`: chat round-trips, appends messages to local `chatHistory`
- `key={selectedReceta.id}` on usage site forces fresh state per recipe
- `handleKeyDown`: Enter to send (Shift+Enter for newline)
- Auto-scroll chat via `chatEndRef`

**RecetasPage.tsx** changes:
- Import `AsistenteCosteoPanel`
- `showSocia` state declaration after `showProducir`
- "Consultar a Socia" amber gradient button after `EscenariosPrecios` block
- `fixed inset-0 z-50` modal at bottom of JSX, consistent with existing modal pattern
- `maxHeight: 90vh` prevents modal overflow on desktop

---

## Fase 1 Analysis Fields Rendered

| Field | Display |
|-------|---------|
| `precio_sugerido` | Large amber highlighted card, `formatCurrency(Number(...))` |
| `margen_esperado` | Inside precio card, `Number(...).toFixed(1)%` |
| `escenario_recomendado` | Green card with label |
| `justificacion` | Plain text, warm label "Lo que te dice Socia" |
| `alertas` | List with orange warning style, `!` icon |
| `mensaje_cierre` | Gray italic quote block with `- Socia` attribution |

---

## Deviations from Plan

None — plan executed exactly as written. Minor style choice: emoji icons removed from button text and error state (project guideline: avoid emojis in files unless requested), replaced with text equivalents. Core behavior unchanged.

---

## Checkpoint Status

Task 3 (`checkpoint:human-verify`) is pending. The UI is built and TypeScript compiles clean. Human must verify the end-to-end modal behavior in the browser.

---

## Self-Check

**Files exist:**
- `frontend/src/components/recetas/AsistenteCosteoPanel.tsx` — FOUND
- `frontend/src/pages/RecetasPage.tsx` (modified) — FOUND
- `frontend/src/api/endpoints.ts` (modified) — FOUND
- `frontend/src/types/index.ts` (modified) — FOUND

**Commits:**
- `8ef9ae5` — feat(02-04): add Socia types and consultarSocia endpoint
- `68ba92a` — feat(02-04): create AsistenteCosteoPanel and wire Socia modal in RecetasPage

**TypeScript:** 0 errors

## Self-Check: PASSED
