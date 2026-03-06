---
phase: 01-auditoria
plan: 02
subsystem: planning
tags: [decisions, architecture, locked, phase-gates]
dependency_graph:
  requires: [01-01-PLAN.md (01-RESEARCH.md)]
  provides: [DECISIONS.md — 6 locked technical decisions gating Phases 2-7]
  affects: [ROADMAP.md (phase unblock status), all Phase 2-7 PLAN.md files]
tech_stack:
  added: []
  patterns: [Clerk publicMetadata for freemium, FastAPI decorator for plan enforcement, Wompi unified gateway, BSP for WhatsApp WABA, ReportLab extend pattern]
key_files:
  created: [.planning/phases/01-auditoria/DECISIONS.md]
  modified: []
decisions:
  - "claude-haiku-4-5 via Anthropic API for Phase 2 IA Costeo (vendor consolidation, $0.83/month at 150K req)"
  - "ReportLab extend (already operational) + S3 activate for Phase 3 PDF — WeasyPrint rejected (Railway libgobject risk)"
  - "Wompi as unified Colombian payment gateway for Phase 4 — covers Nequi+Daviplata+PSE in one SDK"
  - "BSP (WATI/360dialog) + shared chandelierp number for Phase 5 WhatsApp — 24-48h vs 10-day direct Meta verification"
  - "Clerk publicMetadata + FastAPI decorator for Phase 6 Freemium — zero DB migration, plan in JWT"
  - "Static Markdown + LLM contextual (claude-haiku-4-5) for Phase 7 DIAN Asistente"
metrics:
  duration: "3 minutes 14 seconds"
  completed: "2026-03-04"
  tasks_completed: 1
  files_created: 1
  lines_written: 353
---

# Phase 01 Plan 02: Decisiones Tecnicas Bloqueadas — Summary

**One-liner:** 6 locked technical decisions (LLM/PDF/payments/WhatsApp/freemium/DIAN) derived from 01-RESEARCH.md, gating all implementation phases 2-7 with rejected alternatives, cost data, and 5 owner actions.

---

## What Was Produced

**File:** `.planning/phases/01-auditoria/DECISIONS.md`
**Line count:** 353 lines
**DECISION LOCKED entries:** 6 (one per phase 2-7)

---

## Key Decisions Locked

| # | Phase | Decision | Cost/Rationale |
|---|-------|----------|----------------|
| 1 | Phase 2 — IA Costeo | claude-haiku-4-5 via Anthropic API (batch+caching) | $0.83/month at 150K req — vendor consolidation wins |
| 2 | Phase 3 — PDF Branding | ReportLab extend + S3 activate (`S3_ENABLED=true`) | Already operational — WeasyPrint Railway libgobject risk confirmed |
| 3 | Phase 4 — Pagos Locales | Wompi unified gateway (Nequi+Daviplata+PSE+QR) | Sandbox immediate — Nequi/Daviplata direct risk 2-4 week approval |
| 4 | Phase 5 — WhatsApp | BSP (WATI/360dialog) + shared chandelierp number | 24-48h WABA vs 2-10 days Meta direct; $33/month at 100 tenants |
| 5 | Phase 6 — Freemium | Clerk publicMetadata + FastAPI decorator | Zero DB migration, plan in JWT, zero latency enforcement |
| 6 | Phase 7 — DIAN | Static Markdown + claude-haiku-4-5 contextual | Low cost, no LLM latency on static calendar, same LLM vendor |

---

## Owner Actions (5 items blocking phases)

| Action | Blocks Phase | Urgency |
|--------|-------------|---------|
| Add `ANTHROPIC_API_KEY` to Railway env vars | Phase 2 | Before Phase 2 starts |
| Verify S3 bucket `chandelier-documents` in AWS Console (us-east-1) | Phase 3 | Before Phase 3 starts |
| Register Wompi production account at `wompi.com/negocios` | Phase 4 | Before Phase 4 starts |
| Start BSP account (WATI or 360dialog) for WABA onboarding | Phase 5 | 1 week lead time before Phase 5 |
| Migrate Clerk from dev keys (`pk_test_*`) to prod keys (`pk_live_*`) | Phase 6 upgrade flows | Before Phase 6 starts |

---

## Status

Phase 1 Plan 02 complete — Phases 2-7 unblocked pending owner actions listed above.

All 6 locked decisions are documented with:
- Rejected alternatives and rationale
- Cost and timeline data
- Technical configuration details
- Explicit OUT OF SCOPE deferred items
- Open questions with resolution paths

---

## Deviations from Plan

None — plan executed exactly as written. Document produced from research data in 01-RESEARCH.md. Zero code written.

---

## Self-Check

- [x] DECISIONS.md exists at `.planning/phases/01-auditoria/DECISIONS.md`
- [x] 6 "DECISION LOCKED" entries (one per Phase 2-7)
- [x] Each decision includes rejected alternatives with rationale
- [x] Cost/timeline data included for all decisions
- [x] Owner actions table has 5 items with blocking phases
- [x] Deferred ideas explicitly labeled "OUT OF SCOPE"
- [x] No code in document
- [x] 353 lines (exceeds 120-line minimum)
- [x] Commit 599cc63 verified
