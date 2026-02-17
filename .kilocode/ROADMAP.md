# Roadmap: Chandelier — Reset & Tenant Onboarding

## Overview

This roadmap transforms Chandelier from a development system to a production-ready SaaS by adding database reset capabilities and a progressive onboarding wizard. The journey moves from infrastructure (reset scripts, Excel parsing, templates) through validation pipelines (preview, error detection) to user-facing features (multi-step wizard with save/resume). Each phase delivers a complete capability that can be tested independently, ensuring data integrity is architecturally guaranteed before any tenant onboarding can execute.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Reset** - Database reset infrastructure and Excel template system
- [ ] **Phase 2: Validation Pipeline** - Import preview with error detection and validation rules
- [ ] **Phase 3: Bulk Import Execution** - Transactional bulk operations with RLS safety
- [ ] **Phase 4: Core Onboarding Wizard** - Mandatory 3-step tenant setup (company, products, clients)
- [ ] **Phase 5: Advanced Onboarding** - Optional steps for inventory, accounting opening balances
- [ ] **Phase 6: UX & Polish** - Save/resume progress, Colombian-specific validations, completion flow

## Phase Details

### Phase 1: Foundation & Reset
**Goal**: Superadmin can reset database safely and system can generate Excel templates for imports
**Depends on**: Nothing (first phase)
**Requirements**: RESET-01, RESET-02, RESET-03, RESET-04, IMPORT-01, IMPORT-03
**Success Criteria** (what must be TRUE):
  1. Superadmin can execute database reset that clears development data while preserving schema, PUC, planes, and superadmin account
  2. System validates database integrity before and after reset (row counts, constraints, RLS policies exist)
  3. System logs audit trail of reset operations (who, when, what was deleted) in persistent storage
  4. User can download Excel templates (.xlsx) with correct headers and 2-3 example rows for products, clients, inventory
  5. Backend can parse .xlsx and .csv files detecting columns automatically
**Plans**: TBD

Plans:
- [ ] 01-01: TBD
- [ ] 01-02: TBD

### Phase 2: Validation Pipeline
**Goal**: User can see preview of imported data with errors highlighted before committing to database
**Depends on**: Phase 1
**Requirements**: IMPORT-02, IMPORT-04, IMPORT-05
**Success Criteria** (what must be TRUE):
  1. User uploads Excel file and sees preview table showing first 100 rows with detected data types
  2. System validates NITs with Colombian check digit algorithm and highlights invalid rows in red
  3. System validates currency formats (COP) and date formats (DD/MM/YYYY) with clear error messages
  4. User can manually map Excel column names to system fields via dropdown selectors
  5. User can download error report CSV listing all validation failures for offline fixing
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Bulk Import Execution
**Goal**: System can execute validated imports transactionally with RLS context safety
**Depends on**: Phase 2
**Requirements**: (Foundational for WIZARD-02, WIZARD-03, WIZARD-04 — no explicit REQ-ID but architecturally required)
**Success Criteria** (what must be TRUE):
  1. System executes bulk insert of 1000+ rows in single transaction with rollback on any error
  2. System maintains RLS context (tenant_id) throughout import preventing cross-tenant data leakage
  3. System calculates weighted average costs correctly for inventory adjustments
  4. User sees real-time progress indicator during import execution (percentage complete, rows processed)
  5. System handles duplicate detection (existing SKUs, NITs) with clear conflict resolution options
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Core Onboarding Wizard
**Goal**: New tenant completes mandatory setup (company data, products, clients) via guided wizard
**Depends on**: Phase 3
**Requirements**: WIZARD-01, WIZARD-02, WIZARD-03
**Success Criteria** (what must be TRUE):
  1. User completes Step 1 entering company data (NIT, razón social, dirección, logo upload, prefijo factura, IVA config)
  2. User completes Step 2 importing products from Excel with preview/validation/execute flow integrated
  3. User completes Step 3 importing clients from Excel with same preview/validation/execute flow
  4. Wizard shows step indicator (1 of 7, progress bar) and blocks advancing until current step valid
  5. New tenant account redirects to wizard automatically on first login (cannot skip mandatory steps)
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD
- [ ] 04-03: TBD

### Phase 5: Advanced Onboarding
**Goal**: User can optionally configure inventory stock/costs and accounting opening balances
**Depends on**: Phase 4
**Requirements**: WIZARD-04, WIZARD-05
**Success Criteria** (what must be TRUE):
  1. User can skip to Step 4 (inventory adjustment) and adjust stock quantities and costs for imported products
  2. User can skip to Step 5 (accounting opening) and enter opening balances by PUC account code
  3. System validates opening balances are balanced (sum debits = sum credits) before allowing save
  4. User can skip optional steps entirely and wizard marks tenant as "setup complete" after Step 3
  5. Inventory adjustments create movimientos_stock entries with tipo=ajuste and proper audit trail
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

### Phase 6: UX & Polish
**Goal**: Wizard experience is polished with save/resume, contextual help, and Colombian-specific features
**Depends on**: Phase 5
**Requirements**: UX-01, UX-02, UX-03, WIZARD-06
**Success Criteria** (what must be TRUE):
  1. User can exit wizard mid-step and resume later from exactly where they left off (progress persisted)
  2. User sees loading spinners during file uploads and progress bars during bulk imports with time estimates
  3. User sees contextual tips in each wizard step explaining what data to enter and why it matters
  4. Wizard is accessible from Settings > "Re-run Setup Wizard" for re-importing data after initial setup
  5. System validates Colombian NIT format (9 digits + check digit) with auto-calculation if check digit missing
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Reset | 0/2 | Not started | - |
| 2. Validation Pipeline | 0/2 | Not started | - |
| 3. Bulk Import Execution | 0/2 | Not started | - |
| 4. Core Onboarding Wizard | 0/3 | Not started | - |
| 5. Advanced Onboarding | 0/2 | Not started | - |
| 6. UX & Polish | 0/2 | Not started | - |
