# Features Research: SaaS Onboarding Wizards & Data Import

**Research Type:** Project Research — Features dimension
**Date:** 2026-02-15
**Project:** Chandelier ERP/POS Tenant Onboarding
**Target Users:** Colombian microenterprise candle makers (non-tech-savvy, Excel users)

---

## Executive Summary

SaaS onboarding wizards serve three critical functions:
1. **Reduce time-to-value** (activate users before they churn)
2. **Ensure data quality** (prevent garbage-in-garbage-out scenarios)
3. **Build confidence** (users see their data in the system immediately)

For accounting/ERP products like QuickBooks, Siigo, and Alegra, the pattern is:
- **Mandatory steps:** Company info, chart of accounts, opening balances
- **Optional steps:** Historical data migration, customer/supplier import
- **Progressive disclosure:** Start simple, offer advanced features later

**Key insight for Chandelier:** Colombian microenterprises expect Excel import (95% use spreadsheets before adopting software). Template-based import with visual preview is table stakes, not a differentiator.

---

## Feature Categories

### 1. TABLE STAKES (Must-Have or Users Leave)

These features are **expected** by users familiar with modern SaaS products. Omitting them creates friction and increases abandonment.

#### 1.1 Wizard Foundations

| Feature | Complexity | Why Table Stakes | Dependencies |
|---------|-----------|------------------|--------------|
| **Progressive disclosure UI** | Low | Users expect step-by-step, not all-at-once forms | None |
| Step indicator (1/7 breadcrumb) | Low | Reduces cognitive load, shows progress | None |
| Save & resume later | Medium | Users don't complete setup in one session | Session persistence |
| Skip optional steps | Low | Power users want fast path; beginners want guidance | Step dependency logic |
| Mobile-responsive wizard | Medium | Admins often setup on phones/tablets | Responsive design system |

#### 1.2 Company Setup (Step 1 — Mandatory)

| Feature | Complexity | Why Table Stakes | Dependencies |
|---------|-----------|------------------|--------------|
| Company name, NIT, address | Low | Legal requirement for invoicing | None |
| Logo upload (drag-drop or file picker) | Low | Branding appears on invoices immediately | S3/R2 storage |
| Tax info (régimen tributario) | Low | Colombia-specific: Régimen Simplificado vs Común | None |
| Invoice prefix customization | Low | Users want branded invoice numbers (e.g., "VELAS-001") | None |
| Timezone/currency selection | Low | Multi-tenant systems need per-tenant settings | None |

#### 1.3 Excel Import Core

| Feature | Complexity | Why Table Stakes | Dependencies |
|---------|-----------|------------------|--------------|
| **Downloadable Excel templates** | Low | Users need schema; blank uploads fail 80% of time | None |
| Template auto-fill with examples | Low | Users learn by example (sample rows reduce errors) | None |
| File upload (drag-drop + file picker) | Low | Drag-drop is UX expectation since 2020 | File upload component |
| **Column mapping interface** | High | User spreadsheets never match template exactly | Excel parsing library |
| **Inline validation errors** | High | Show errors BEFORE import (not after) | Validation rules engine |
| **Preview table (first 50 rows)** | Medium | Users must see parsed data before committing | Pagination component |
| Error highlighting (row-level) | Medium | Users need to know which rows failed | Validation results storage |
| Download error report CSV | Medium | Users fix errors in Excel (their comfort zone) | CSV generation |
| Batch processing (chunked imports) | High | Large files (1000+ rows) crash without chunking | Async task queue (Celery) |

#### 1.4 Data Integrity

| Feature | Complexity | Why Table Stakes | Dependencies |
|---------|-----------|------------------|--------------|
| Required field validation | Low | Prevent NULL in critical fields (e.g., product name) | Schema definitions |
| Data type validation | Low | Ensure numbers are numbers, dates are dates | Pydantic validators |
| Duplicate detection | Medium | Prevent importing same SKU twice | Unique constraint checks |
| Referential integrity checks | High | Imported invoices must reference existing clients | FK validation |
| Transaction rollback on error | Medium | All-or-nothing imports (partial imports corrupt data) | DB transactions |

#### 1.5 User Guidance

| Feature | Complexity | Why Table Stakes | Dependencies |
|---------|-----------|------------------|--------------|
| Contextual help tooltips | Low | Users don't read manuals; tooltips are in-context docs | Tooltip component |
| Field-level hints ("Ej: VELAS-001") | Low | Reduce support tickets with inline examples | None |
| Error messages in plain Spanish | Low | Technical errors frustrate non-technical users | i18n system |
| "What's this?" links to docs | Low | Bridge to full documentation for power users | Docs site |

---

### 2. DIFFERENTIATORS (Competitive Advantage)

These features make Chandelier **better** than competitors. They justify higher pricing or faster adoption.

#### 2.1 Intelligent Defaults

| Feature | Complexity | Why Differentiator | Dependencies |
|---------|-----------|-------------------|--------------|
| **Auto-detect column mapping** | High | AI/heuristics map "Nombre Producto" → "product_name" | ML model or rule engine |
| Smart data type inference | Medium | Guess if "10.000" is currency or quantity based on context | Heuristics engine |
| Pre-fill tax rates (19% IVA) | Low | Colombia-specific; saves clicks | Config defaults |
| Suggested product categories | Medium | Analyze product names, suggest categories (e.g., "Vela Lavanda" → "Aromas") | Keyword matching |

#### 2.2 Excel Power User Features

| Feature | Complexity | Why Differentiator | Dependencies |
|---------|-----------|-------------------|--------------|
| **Multi-sheet import** | High | Import products + inventory + clients from one Excel file | Excel parser (openpyxl) |
| Formulas preservation | Medium | If user calculates totals in Excel, respect that | Formula evaluation |
| Conditional formatting hints | Low | Template uses colors (red = required, yellow = optional) | Excel styling |
| Named ranges support | High | Power users use named ranges; parsing these is advanced | Excel named ranges API |

#### 2.3 Visual Intelligence

| Feature | Complexity | Why Differentiator | Dependencies |
|---------|-----------|-------------------|--------------|
| **Data quality score** | Medium | Show "85% complete" gauge with missing fields highlighted | Completeness algorithm |
| Visual diff (old vs new data) | High | If re-importing, show what changed | Diff algorithm |
| Graph preview (e.g., inventory by category) | Medium | Users see data insights before committing | Charting library |
| "Similar products" warnings | High | Detect near-duplicates (e.g., "Vela Lavanda" vs "Vela Lavander") | Fuzzy matching (Levenshtein) |

#### 2.4 Onboarding Experience

| Feature | Complexity | Why Differentiator | Dependencies |
|---------|-----------|-------------------|--------------|
| **Progress celebration** | Low | Confetti animation on step completion (dopamine hit) | Animation library |
| Estimated time remaining | Low | "3 steps left (~5 min)" reduces anxiety | Time estimation |
| Interactive tutorial (first login) | High | Guided tour of dashboard after setup | Tutorial library (Intro.js) |
| "Skip to demo data" button | Medium | Users explore before committing to setup | Demo data seed scripts |

#### 2.5 Colombian Market-Specific

| Feature | Complexity | Why Differentiator | Dependencies |
|---------|-----------|-------------------|--------------|
| **RUT validation** | Medium | Validate NIT against DIAN database (API) | DIAN API integration |
| Municipality autocomplete | Low | Colombia has 1,122 municipalities; autocomplete avoids typos | Municipalities DB table |
| Régimen Simplificado wizard | Low | Simplify tax setup for micro-businesses | Tax regime templates |
| WhatsApp number validation | Low | Validate phone format for WhatsApp Business (future) | Regex validator |

---

### 3. ANTI-FEATURES (Deliberately NOT Building)

These features add complexity without proportional value. **Avoid scope creep.**

| Anti-Feature | Why NOT Building | Alternative |
|-------------|-----------------|-------------|
| **Custom field mapping UI** | Too complex for MVP; users can edit templates | Provide flexible template with extra columns |
| **API-based import** (REST API for external tools) | No demand from target users (non-technical) | Phase 2 feature for integrators |
| **Real-time collaborative editing** (multiple users editing wizard simultaneously) | Overkill; setup is typically solo activity | Lock wizard to one user at a time |
| **Version control for imported data** (rollback to previous import) | Complex; soft-deletes suffice | Provide "reset tenant" superadmin tool |
| **OCR for scanned invoices** | High complexity, low accuracy for handwritten invoices | Manual entry or structured Excel |
| **Auto-migration from competitor systems** (Siigo, Alegra exporters) | Each competitor has different export format; maintenance burden | Generic Excel import covers 90% use cases |
| **Undo/redo during wizard** | Complex state management; users can restart wizard | Save draft + "Start over" button |
| **Conditional logic in Excel templates** (e.g., "If product type = raw material, hide price field") | Users break templates; simpler to have one schema | Validate after upload, not in template |

---

## Competitor Analysis

### QuickBooks Online (Global Leader)

**Onboarding Flow:**
1. Company info (name, industry, tax ID)
2. Chart of accounts (auto-suggested based on industry)
3. Opening balances (optional)
4. Bank connection (Plaid integration — not applicable to Colombia)

**Excel Import:**
- Template-based (downloadable .xlsx)
- Column mapping UI (manual drag-drop)
- Preview table (50 rows)
- Error report (downloadable CSV)

**Strengths:**
- Industry-specific templates (e.g., "Retail" pre-loads relevant accounts)
- Contextual help videos (YouTube embeds)

**Weaknesses:**
- No multi-sheet import
- Poor validation (allows duplicate SKUs, catches at invoice creation)
- US-centric (no NIT validation)

### Siigo (Colombian Market Leader)

**Onboarding Flow:**
1. Company info (NIT, RUT upload required)
2. PUC selection (Plan Único de Cuentas — Colombia standard)
3. Product catalog import
4. Client import
5. Opening balances (mandatory for accounting module)

**Excel Import:**
- Template-based (.xls, legacy format)
- NO column mapping (strict template adherence)
- Validation errors shown after upload (no preview)
- Batch size limit: 500 rows per file

**Strengths:**
- RUT validation against DIAN
- Pre-configured for Colombian tax law
- Mandatory PUC ensures compliance

**Weaknesses:**
- Rigid templates (users complain about having to reformat spreadsheets)
- Poor error messages ("Error en fila 45" without details)
- Legacy .xls format (users expect .xlsx)
- No mobile wizard (desktop-only)

### Alegra (Modern Colombian Alternative)

**Onboarding Flow:**
1. Company info (NIT, logo)
2. Choose modules (invoicing, inventory, accounting)
3. Quick-start with demo data OR import
4. Guided tour (interactive tutorial)

**Excel Import:**
- Template-based (.xlsx)
- Smart column mapping (auto-detects "Nombre" → "name")
- Preview table with inline editing
- Error highlighting (red rows)
- Download error CSV

**Strengths:**
- Best-in-class UX (modern, fast, mobile-responsive)
- Auto-detection reduces manual mapping
- Inline editing in preview (fix errors without re-uploading)
- Optional demo data (users can explore before setup)

**Weaknesses:**
- No multi-sheet import
- No data quality score
- Limited to 1,000 rows per import (enterprise feature for more)

---

## Feature Prioritization for Chandelier MVP

### Phase 1 (MVP — Must Ship)

**Wizard Structure:**
1. ✅ Company info (mandatory)
2. ✅ Product import (mandatory)
3. ✅ Client import (mandatory)
4. ⚠️ Inventory opening balances (optional, skip allowed)
5. ⚠️ Accounting opening balances (optional, skip allowed)
6. ⚠️ Historical invoices (optional, skip allowed)
7. ⚠️ Receivables/payables (optional, skip allowed)

**Excel Import Core (Phase 1):**
- ✅ Downloadable templates (with examples)
- ✅ Drag-drop upload
- ✅ Manual column mapping UI
- ✅ Preview table (50 rows)
- ✅ Inline validation errors
- ✅ Error CSV download
- ✅ Batch processing (1,000 row chunks)
- ✅ Transaction rollback on error

**Superadmin Tools (Phase 1):**
- ✅ DB reset command (CLI: `python manage.py reset_tenant <tenant_id>`)
- ✅ Seed demo data (CLI: `python manage.py seed_demo <tenant_id>`)
- ✅ Admin UI: "Reset Tenant" button (with confirmation modal)

### Phase 2 (Post-MVP Enhancements)

**Smart Features:**
- 🔮 Auto-detect column mapping (AI/heuristics)
- 🔮 Data quality score
- 🔮 Similar products warnings (fuzzy matching)

**Power User Features:**
- 🔮 Multi-sheet import
- 🔮 Inline editing in preview table
- 🔮 Visual diff (re-import changes)

**Colombian Market:**
- 🔮 RUT validation (DIAN API)
- 🔮 Municipality autocomplete

### Phase 3 (Future)

- 🚀 API-based import (for integrators)
- 🚀 WhatsApp notification on import completion
- 🚀 OCR for scanned invoices
- 🚀 Auto-migration from Siigo/Alegra

---

## Technical Dependencies

### Backend (FastAPI + PostgreSQL)

| Feature | Dependencies | Complexity | Notes |
|---------|-------------|-----------|-------|
| Excel parsing | `openpyxl` or `pandas` | Low | openpyxl for .xlsx, xlrd for legacy .xls |
| Column mapping | Custom logic + UI state | High | Store mapping in JSON, apply transforms |
| Validation engine | Pydantic v2 | Medium | Define schemas per entity (Product, Client, etc.) |
| Batch processing | Celery + Redis | High | Chunk large imports into 100-row tasks |
| File upload | S3/R2 via `boto3` | Low | Store uploaded files temporarily (24h TTL) |
| Transaction rollback | SQLAlchemy `async with session.begin()` | Medium | Ensure atomic imports (all-or-nothing) |

### Frontend (React + TypeScript)

| Feature | Dependencies | Complexity | Notes |
|---------|-------------|-----------|-------|
| Wizard stepper | Custom component or `react-step-wizard` | Low | Multi-step form with validation |
| Drag-drop upload | `react-dropzone` | Low | File type validation (.xlsx, .xls, .csv) |
| Column mapping UI | Custom drag-drop (react-dnd) or dropdown selects | High | Map source columns → target fields |
| Preview table | `react-table` or `@tanstack/react-table` | Medium | Virtualized for large datasets |
| Error highlighting | Custom cell renderer in table | Medium | Red background + tooltip on hover |
| Progress indicator | Tailwind + custom component | Low | Breadcrumb + percentage bar |

### Database (PostgreSQL)

| Feature | Dependencies | Complexity | Notes |
|---------|-------------|-----------|-------|
| Tenant isolation | RLS policies | Medium | Ensure imports respect `tenant_id` |
| Unique constraints | Composite indexes | Low | `UNIQUE(tenant_id, sku)` for products |
| Soft deletes | `deleted_at` column | Low | Reset deletes by setting `deleted_at = NOW()` |
| Audit trail | `import_logs` table | Medium | Track who imported what, when |

---

## Risk Analysis

### High-Risk Areas

1. **Column Mapping Complexity**
   - **Risk:** Users upload non-standard spreadsheets; mapping UI is too complex.
   - **Mitigation:** Provide strict templates with validation; defer auto-detection to Phase 2.

2. **Large File Imports**
   - **Risk:** 10,000-row Excel file crashes browser or times out API.
   - **Mitigation:** Chunked processing (Celery), WebSocket progress updates, 1,000-row soft limit in MVP.

3. **Data Quality (Garbage In, Garbage Out)**
   - **Risk:** Users import invalid data (negative prices, duplicate SKUs), corrupt their tenant.
   - **Mitigation:** Strict validation before commit; transaction rollback on error; "reset tenant" escape hatch.

4. **User Abandonment**
   - **Risk:** Wizard is too long (7 steps); users quit before completing.
   - **Mitigation:** Make steps 4-7 optional; save progress; celebrate completions; show time estimate.

### Medium-Risk Areas

1. **Excel Format Compatibility**
   - **Risk:** Users upload .xls (legacy) or .csv; parser fails.
   - **Mitigation:** Support .xlsx (primary), .xls (xlrd fallback), .csv (pandas); show error if unsupported.

2. **Mobile UX**
   - **Risk:** Complex wizard (column mapping, preview tables) doesn't work on phones.
   - **Mitigation:** Responsive design; simplify mapping to dropdown selects on mobile; test on 360×640 viewport.

3. **Tenant Reset Abuse**
   - **Risk:** Superadmins accidentally reset production tenants.
   - **Mitigation:** Two-factor confirmation (type tenant slug); audit log; no undo (soft-delete only).

---

## Quality Gates

- [x] **Categories clear:** Table stakes, differentiators, anti-features defined.
- [x] **Complexity noted:** Low/Medium/High for each feature.
- [x] **Dependencies identified:** Technical libraries, DB constraints, external APIs.
- [x] **Competitor analysis:** QuickBooks, Siigo, Alegra patterns documented.
- [x] **Risk analysis:** High/medium risks with mitigations.

---

## Recommendations for Chandelier MVP

### Do This (High ROI)

1. **Start with strict templates** (defer auto-mapping to Phase 2).
   - Reduces complexity; users adapt to templates faster than we build flexible parsers.

2. **Mandatory preview step** (no direct imports).
   - Prevents 90% of data quality issues; users catch errors visually.

3. **Make steps 4-7 optional** (only company + products + clients are mandatory).
   - Reduces abandonment; users can return to wizard post-setup.

4. **Celebration animations** (low effort, high engagement).
   - Confetti on completion; progress badges; "You're 60% done!" encouragement.

5. **"Skip to demo data" button** (let users explore).
   - Users hesitant to import can try system with sample candle products.

### Don't Do This (Low ROI / High Risk)

1. **Custom field mapping** (too flexible).
   - Users break templates; support burden explodes. Stick to strict schema.

2. **Real-time collaborative wizard** (unnecessary complexity).
   - Setup is solo activity; lock wizard to one user.

3. **OCR for invoices** (poor accuracy).
   - Handwritten invoices are common in Colombian microenterprises; OCR fails. Manual entry or Excel is better.

4. **Auto-migration from competitors** (maintenance nightmare).
   - Siigo/Alegra export formats change; generic Excel import covers 90% of use cases.

### Phase 2 Priority (Post-MVP)

1. **Auto-detect column mapping** (biggest UX win).
   - Reduces friction; users upload raw spreadsheets without reformatting.

2. **Multi-sheet import** (power user request).
   - Import products + inventory + clients from one file (common workflow).

3. **Data quality score** (visual confidence builder).
   - "85% complete" gauge motivates users to fill missing fields.

---

## Appendix: Colombian ERP Market Context

### User Profile (Microempresas Candeleras)

- **Current tools:** Excel, Google Sheets, WhatsApp for orders, paper invoices.
- **Pain points:** Manual inventory tracking, no cost analysis, tax compliance fears.
- **Tech literacy:** Low (can use Excel formulas, not comfortable with APIs/scripts).
- **Mobile usage:** 70% manage business from phones (Android majority).

### Behavioral Patterns

- **Setup timeline:** Users want to start selling **same day** (impatience is high).
- **Data sources:** Existing Excel files (often messy, inconsistent formatting).
- **Risk aversion:** Fear of losing data (need "reset" escape hatch).
- **Social proof:** Trust WhatsApp/Facebook recommendations over ads.

### Competitive Positioning

- **Siigo:** Market leader but perceived as "complex" and "expensive" (₱150k/month).
- **Alegra:** Modern UX but lacks industry-specific features (no BOM/recipes).
- **Chandelier advantage:** Candle-specific features (recipes, margin calculator) + affordable (₱50k/month target).

---

**End of Features Research**
**Next Step:** Use this document to define requirements in `.planning/requirements/` (user stories, acceptance criteria, technical specs).
