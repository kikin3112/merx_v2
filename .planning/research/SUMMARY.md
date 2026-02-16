# Project Research Summary

**Project:** Chandelier ERP/POS - Tenant Onboarding, Excel Import, and DB Reset
**Domain:** SaaS Multi-Tenant ERP/POS for Colombian Microenterprises
**Researched:** 2026-02-15
**Confidence:** HIGH (85%)

## Executive Summary

This research covers adding critical onboarding and data migration capabilities to Chandelier's existing FastAPI + React + PostgreSQL RLS multi-tenant ERP system. The focus is on enabling tenant self-service setup through a progressive wizard with Excel data import and superadmin database reset tools.

**The recommended approach** is a 5-phase implementation starting with foundation components (template generation, Excel parsing) before building the user-facing wizard. This sequence minimizes risk by establishing data integrity guarantees early, then layering UX progressively. The stack leverages mature, battle-tested libraries (openpyxl for Excel, react-dropzone for uploads, react-data-grid for preview) rather than bleeding-edge alternatives, prioritizing stability over novelty.

**Key risks center on multi-tenant data integrity**: RLS context loss during bulk operations can cause silent cross-tenant data leakage, weighted average inventory costing errors create irreversible financial corruption, and database reset operations that destroy RLS policies open security holes. All three require architectural safeguards in Phase 1 (foundation) before any import features ship. Secondary risks include wizard abandonment (mitigated by making only 3 of 7 steps mandatory) and Excel encoding issues with Spanish characters (mitigated by enforcing UTF-8 .xlsx format).

## Key Findings

### Recommended Stack

The research identifies mature, proven libraries suitable for a production SaaS environment serving non-technical users. All components integrate cleanly with Chandelier's existing FastAPI + PostgreSQL + React stack without requiring architecture changes.

**Core technologies:**
- **openpyxl 3.1.2+**: Excel parsing and template generation (pure Python, streaming mode for large files, 10+ years mature)
- **pandas 2.2.0+**: Data validation and transformation (vectorized operations, industry standard for tabular data)
- **react-dropzone 14.2.3+**: File upload UI (10M+ weekly downloads, accessible, mobile-friendly)
- **react-data-grid 7.0.0-beta.44+**: Excel-like preview with cell highlighting (virtual scrolling handles 10k+ rows, 50KB vs AG Grid's 500KB)
- **papaparse 5.4.1**: Client-side CSV preview (8M+ weekly downloads, instant feedback without server round-trip)
- **SQLAlchemy 2.0 bulk operations**: RLS-aware bulk insert with RETURNING (200ms for 1000 rows)

**Critical decisions:**
- Backend Excel parsing (not client-side): Security, consistency, performance
- Synchronous preview + async execution: Immediate feedback for validation, background processing for large imports
- Single transaction per import: All-or-nothing guarantee, rollback on any error prevents partial corruption

**Version confidence**: HIGH (90%). All libraries verified current as of January 2025, low-churn packages with stable APIs.

### Expected Features

Research into competitor SaaS products (QuickBooks, Siigo, Alegra) and Colombian microenterprise workflows reveals clear feature expectations.

**Must have (table stakes):**
- Downloadable Excel templates with examples and validation dropdowns
- Drag-drop file upload with preview table (first 50 rows)
- Inline validation errors highlighted before import commits
- Column mapping interface (manual in MVP, auto-detect in Phase 2)
- Error CSV download for offline fixing
- Transaction rollback on any import error
- Save and resume wizard progress
- Skip optional steps (only company info, products, clients mandatory)

**Should have (competitive advantage):**
- Data quality score (e.g., "85% complete" gauge with missing fields)
- Progress celebration animations (reduce abandonment)
- Auto-detect column mapping (AI/heuristics map "Nombre Producto" → "product_name")
- Multi-sheet import (products + inventory + clients in one file)
- Smart data type inference based on content patterns
- Colombian-specific NIT validation (check digit algorithm)

**Defer to Phase 2+:**
- Real-time collaborative wizard (overkill for solo setup)
- Custom field mapping (too flexible, support burden)
- OCR for scanned invoices (low accuracy for handwritten)
- API-based import for external tools (no demand from non-technical users)
- Auto-migration from Siigo/Alegra (export formats change frequently)

**User expectations context**: Colombian microenterprises use Excel for everything pre-SaaS. Template-based import is table stakes, not a differentiator. Users expect same-day activation and fear data loss, requiring "reset tenant" escape hatch.

### Architecture Approach

The implementation adds 5 distinct systems to the existing architecture without breaking changes: (1) Database Reset orchestrator with preservation rules, (2) Frontend wizard state machine with 7 steps, (3) Excel import 5-stage pipeline (upload → parse → validate → transform → load), (4) Template generation service, and (5) Onboarding API endpoints. All integrate through existing RLS tenant isolation mechanisms.

**Major components:**

1. **Import Orchestrator (backend)** — Coordinates the 5-stage pipeline with RLS context management, transaction safety, and validation error aggregation. Handles openpyxl parsing, Pydantic schema validation, pandas transformations, and SQLAlchemy bulk inserts.

2. **Onboarding Wizard (frontend)** — Multi-step form with React state management (Zustand for persistence), progress indication, file upload components (react-dropzone), and preview grid (react-data-grid). Supports save/resume, skip optional steps, and progress celebration.

3. **Database Reset System** — Orchestrator + preservation rules (keeps PUC, plans, superadmin) + RLS-aware cleaner + pre/post-validation checker + audit logger. Uses TRUNCATE (preserves policies) not DROP TABLE.

4. **Template Generator** — On-demand Excel creation with openpyxl, includes instruction sheet, example rows, dropdown validations (categories, PUC codes), and conditional formatting hints (red = required).

5. **RLS Context Manager** — Wrapper ensuring `SET LOCAL app.tenant_id_actual` is set for every transaction in import/reset operations. Includes assertion checks to fail fast if context lost.

**Critical patterns:**
- RLS as safety net: Application code includes tenant_id explicitly for performance; RLS catches bugs
- Atomic transactions: All imports/resets wrapped in single transaction with rollback on error
- Streaming mode: Excel parsing uses `read_only=True` for memory efficiency with large files
- Decimal precision: Always use Decimal type for financial calculations, never float
- Chronological enforcement: Inventory imports require opening date before any historical invoices

**Build sequence**: 5 sprints (5 weeks, 1 FTE). Critical path: Template generation → Excel parser → Validation pipeline → Bulk loader → Wizard UI → DB reset.

### Critical Pitfalls

Research identifies 15 domain-specific pitfalls, with 3 causing irreversible damage requiring manual data surgery.

1. **RLS context loss during bulk operations** — PostgreSQL session variable `app.tenant_id_actual` not set in Celery background tasks or after connection pool rotation, causing inserts without tenant_id or with wrong tenant_id. Silent data corruption, cross-tenant leakage. **Prevention**: Explicit `SET LOCAL` at start of every transaction with assertion check; use ORM not raw SQL COPY; test with non-superuser (superusers bypass RLS).

2. **Weighted average cost corruption** — Importing inventory as snapshots ("100 units at $5") instead of movements, applying out of chronological order, or using float precision causes permanently wrong costs that corrupt all future COGS and financial reports. **Prevention**: Import as `movimientos_stock` entries with opening date before sales; enforce chronological consistency; use Decimal type; show calculated cost in preview for user validation.

3. **Database reset destroys RLS policies** — Naive reset script runs `DROP TABLE CASCADE`, removing RLS policies along with data, leaving tenants able to see each other's data with no errors. **Prevention**: Use TRUNCATE (preserves policies) not DROP; automated verification counts policies after reset; version-controlled Alembic migrations not manual SQL.

4. **Excel encoding hell with Spanish characters** — Colombian names/addresses contain ñ, á, é, í, ó, ú. Windows Excel CSV defaults to Latin-1 not UTF-8, causing mojibake or database UTF-8 rejection errors. **Prevention**: Provide .xlsx templates (always UTF-8) not CSV; detect encoding with chardet for CSV uploads; UI warning recommending .xlsx for special characters.

5. **NIT check digit validation missing** — Colombian tax IDs have check digit algorithm. Accepting invalid NITs creates compliance risk when DIAN (tax authority) rejects documents in Phase 2. **Prevention**: Implement modulo-11 validation algorithm; auto-calculate check digit if missing; show corrected NIT in preview.

**Additional moderate risks**: Large file upload timeouts (increase Nginx limits, show progress), preview caching (use POST not GET), sequential invoice number conflicts on historical import (update next_number after import), wizard abandonment (only 3 mandatory steps, save progress).

**Phase-specific warnings table** in PITFALLS.md maps each pitfall to implementation phase with mitigation priority (CRITICAL/HIGH/MEDIUM).

## Implications for Roadmap

Based on research, the implementation should be structured in 5 phases prioritizing data integrity foundations before user-facing features. This sequence ensures critical safeguards are in place before any imports can execute.

### Phase 1: Foundation (DB Reset + Import Infrastructure)
**Rationale:** Establish data integrity safeguards and reset capabilities before building import features. RLS context management and transaction safety are non-negotiable prerequisites that must be validated before proceeding. Database reset script needs to exist early for development/testing workflows.

**Delivers:**
- DB reset script with RLS policy preservation
- RLS context wrapper with assertion checks
- Template generation service (backend)
- Template download endpoints
- Basic Excel parser (products only)
- Automated RLS policy verification

**Addresses pitfalls:**
- Pitfall #1 (RLS context loss) — Critical
- Pitfall #3 (Reset destroys policies) — Critical

**Technical complexity:** Medium. No UI work, focus on backend patterns.

**Duration estimate:** 1 sprint (1 week)

**Research flag:** Standard patterns, no additional research needed.

---

### Phase 2: Validation Pipeline (Preview + Validation)
**Rationale:** Build validation and preview before any data writes. Users must see and fix errors before committing, preventing the "garbage in" scenario. This phase creates the feedback loop that makes imports trustworthy.

**Delivers:**
- Schema validators (Pydantic models)
- Business rule validators (uniqueness, FK checks)
- Import preview endpoint (parse + validate)
- Frontend Excel upload component (react-dropzone)
- Preview table with error highlighting (react-data-grid)
- Error CSV download

**Addresses features:**
- Inline validation errors (table stakes)
- Preview table (table stakes)
- Error CSV download (table stakes)

**Addresses pitfalls:**
- Pitfall #4 (Excel encoding) — High priority
- Pitfall #2 partially (show calculated costs in preview)

**Technical complexity:** High (validation logic, UI components).

**Duration estimate:** 1 sprint (1 week)

**Research flag:** Standard patterns for validation, no research needed.

---

### Phase 3: Import Execution (Bulk Operations)
**Rationale:** With validation proven safe, implement the write operations. This phase includes the weighted average costing logic for inventory and transaction safety for rollback on error.

**Delivers:**
- Bulk loader with RLS context
- Import orchestrator (coordinates pipeline)
- Execute endpoint (sync for <1000 rows)
- Async job system (Celery for >1000 rows)
- Progress tracking and status endpoint
- Weighted average cost calculation for inventory

**Addresses features:**
- Batch processing (table stakes)
- Transaction rollback (table stakes)

**Addresses pitfalls:**
- Pitfall #2 (Weighted average cost) — Critical
- Pitfall #12 (Transaction rollback on partial failure)

**Technical complexity:** High (Celery integration, decimal precision, cost calculation).

**Duration estimate:** 1 sprint (1 week)

**Research flag:** Weighted average costing may need accounting domain research if unclear from PRD.

---

### Phase 4: Onboarding Wizard (Multi-Step UI)
**Rationale:** With import pipeline proven stable, build the user-facing wizard. Progressive disclosure (7 steps, only 3 mandatory) reduces abandonment. Wizard state management and file handling patterns are well-established.

**Delivers:**
- Frontend wizard skeleton (7 steps)
- Step 1: Company info + logo upload
- Step 2: Accounting opening balances (form, not import)
- Step 3: Products import (integrated with preview/execute)
- Step 4: Clients import (optional)
- Steps 5-7: Inventory adjustment, historical invoices, receivables (optional)
- Save/resume progress (Zustand persistence)
- Completion endpoint

**Addresses features:**
- Progressive disclosure UI (table stakes)
- Step indicator (table stakes)
- Save & resume later (table stakes)
- Skip optional steps (table stakes)
- Mobile-responsive wizard (table stakes)

**Addresses pitfalls:**
- Pitfall #6 (Wizard abandonment) — High priority
- Pitfall #11 (Orphaned file storage)

**Technical complexity:** Medium (UI state machine, file upload orchestration).

**Duration estimate:** 1 sprint (1 week)

**Research flag:** Standard wizard patterns, no research needed.

---

### Phase 5: Polish + Edge Cases (Advanced Features)
**Rationale:** Core flow working, now handle edge cases, Colombian-specific features, and UX refinements that improve success rate.

**Delivers:**
- NIT check digit validation (Colombian tax ID)
- Column mapping interface (manual dropdown selects)
- Multi-sheet import (one Excel with products + inventory + clients)
- Sequential invoice number adjustment after historical import
- Date format detection and disambiguation
- Empty row filtering
- Progress celebration animations
- Admin reset UI with confirmation modal

**Addresses features:**
- Column mapping interface (table stakes in MVP, auto-detect deferred to Phase 2 post-MVP)
- NIT validation (competitive advantage for Colombian market)

**Addresses pitfalls:**
- Pitfall #5 (NIT validation) — High priority
- Pitfall #9 (Sequential invoice numbers)
- Pitfall #13 (Date format ambiguity)

**Technical complexity:** Medium (validation algorithms, multi-sheet parsing).

**Duration estimate:** 1 sprint (1 week)

**Research flag:** NIT algorithm needs Colombian tax authority documentation review for verification.

---

### Phase Ordering Rationale

**Dependency chain**: Foundation (Phase 1) establishes RLS safety and reset capability → Validation pipeline (Phase 2) creates preview/error feedback → Execution (Phase 3) implements writes with transaction safety → Wizard (Phase 4) wraps in user-facing UI → Polish (Phase 5) handles edge cases.

**Risk mitigation sequence**: The three critical pitfalls (RLS context loss, cost corruption, policy destruction) are addressed in Phases 1-3 before any production imports can execute. This sequence ensures data integrity is architecturally guaranteed, not just tested.

**User value delivery**: Each phase delivers testable value. Phase 1 enables development reset workflows. Phase 2 enables manual import testing via API. Phase 3 enables batch imports for power users. Phase 4 enables self-service onboarding. Phase 5 enhances success rate.

**Why not different order**: Cannot build wizard (Phase 4) before import execution (Phase 3) because preview alone doesn't help users onboard. Cannot build execution (Phase 3) before validation (Phase 2) because users need to see errors before committing. Cannot build validation (Phase 2) before foundation (Phase 1) because RLS context loss would corrupt data silently during testing.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Import Execution):** Weighted average costing algorithm needs accounting domain validation. If PRD definition insufficient, research FIFO vs weighted average vs LIFO accounting methods for Colombian tax law compliance.
- **Phase 5 (Polish + Edge Cases):** Colombian NIT check digit algorithm needs DIAN (tax authority) official documentation review. Training data includes algorithm but should verify against 2026 current requirements.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Database reset, template generation, Excel parsing are well-documented patterns with established libraries.
- **Phase 2 (Validation Pipeline):** Pydantic validation, file upload UI, preview tables have extensive community examples and documentation.
- **Phase 4 (Onboarding Wizard):** Multi-step forms, progress indication, save/resume are solved problems with many reference implementations.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH (90%) | All libraries verified current as of Jan 2025, mature with stable APIs. Only uncertainty is react-data-grid v7 beta status (fallback: use v6 stable or TanStack Table). |
| Features | HIGH (85%) | Competitor analysis (QuickBooks, Siigo, Alegra) provides clear table-stakes baseline. Colombian market context from PRD requirements is well-defined. Uncertainty around optional vs mandatory wizard steps (recommend A/B testing). |
| Architecture | HIGH (90%) | Component boundaries clear, integration points documented. RLS patterns proven in existing Chandelier codebase. Build sequence dependencies validated. Uncertainty around async threshold (sync <1000 rows, async >1000 rows needs load testing). |
| Pitfalls | MEDIUM (80%) | Critical pitfalls (RLS context loss, cost corruption, policy destruction) identified from PostgreSQL documentation and multi-tenant SaaS patterns. Colombian NIT validation algorithm from training data but not verified with 2026 DIAN sources. Wizard abandonment rates based on industry averages, not Chandelier-specific user research. |

**Overall confidence:** HIGH (85%)

### Gaps to Address

**1. Colombian NIT check digit algorithm verification:**
The modulo-11 algorithm for NIT validation is documented in PITFALLS.md based on training data, but should be verified against current DIAN (Colombian tax authority) requirements before Phase 5 implementation. May have changed in 2025-2026 tax reforms.

**Mitigation:** Consult DIAN official documentation during Phase 5 planning. If validation is complex, implement basic format check (9 digits + hyphen + 1 digit) in Phase 5, defer full check digit validation to Phase 2 post-MVP.

---

**2. Weighted average costing edge cases:**
PRD specifies weighted average for inventory valuation but doesn't address edge cases: (a) negative cost after adjustment, (b) zero-quantity products, (c) rounding in multi-tier BOM (recipes using products that use materials). Need accounting domain validation.

**Mitigation:** During Phase 3 planning, review Colombian accounting standards for inventory costing. Consult with accountant user during pilot testing to validate cost calculations match manual spreadsheet expectations.

---

**3. Wizard step abandonment thresholds:**
Research recommends only 3 mandatory steps (company, products, clients) with 4 optional steps. This is based on general SaaS onboarding patterns, not Colombian microenterprise behavioral data. Actual abandonment rate unknown.

**Mitigation:** Instrument wizard with analytics (Mixpanel or similar) to track drop-off at each step. After 100 onboarding completions, review funnel data and adjust mandatory/optional classification. Consider A/B test: 3 mandatory vs 5 mandatory.

---

**4. Excel file size and row count limits:**
Stack research recommends 5MB file size limit and 10,000 row soft limit based on typical SaaS constraints. Actual performance on Chandelier's server hardware unknown.

**Mitigation:** Load test during Phase 3 with sample Excel files: 1k rows (200ms expected), 5k rows (1s expected), 10k rows (2s expected), 20k rows (timeout expected). Adjust limits based on results. Consider progressive loading (show first 1000 rows immediately, load rest in background).

---

**5. Auto-detect column mapping accuracy:**
Deferred to Phase 2 post-MVP. If implemented, success rate of auto-detection unknown (will "Nombre Producto" reliably map to "nombre"? What about "SKU" vs "Código" vs "Referencia"?).

**Mitigation:** Collect telemetry on manual column mappings during Phase 4-5. Build training dataset of user mappings. Implement simple keyword matching (high-confidence mappings only) before attempting ML-based auto-detection.

## Sources

### Primary (HIGH confidence)
- **Chandelier PRD (CLAUDE.md):** Technical requirements, multi-tenant architecture, RLS implementation, weighted average costing specification, Colombian tax compliance needs
- **PostgreSQL 16 documentation:** RLS policies, SET LOCAL behavior, bulk INSERT with RETURNING, transaction isolation
- **SQLAlchemy 2.0 documentation:** Async sessions, bulk operations, ORM event hooks
- **openpyxl documentation:** Excel parsing API, streaming mode, data validation
- **FastAPI documentation:** File upload handling, async routes, dependency injection

### Secondary (MEDIUM confidence)
- **Competitor analysis (training data):** QuickBooks Online onboarding flow, Siigo Excel import patterns, Alegra smart column mapping
- **React ecosystem libraries:** react-dropzone, react-data-grid, papaparse usage patterns from npm registry stats and GitHub issues
- **Colombian NIT validation:** Algorithm documented in multiple accounting software forums and Colombian developer communities (training data cutoff January 2025)
- **SaaS onboarding patterns:** Multi-step wizard abandonment rates, mandatory vs optional step recommendations from UX research articles

### Tertiary (LOW confidence)
- **Library version currency:** openpyxl 3.1.2, pandas 2.2.0, react-data-grid 7.0.0-beta verified as of January 2025 but may have patches/updates in February 2026
- **Weighted average costing edge cases:** General accounting principles from training data, not specific to Colombian tax law for microenterprises
- **Wizard step count optimization:** General SaaS recommendations (3-5 mandatory steps optimal) not validated with Colombian microenterprise user research

---
*Research completed: 2026-02-15*
*Ready for roadmap: yes*
