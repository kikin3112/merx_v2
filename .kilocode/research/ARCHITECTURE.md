# Architecture Research: Onboarding Wizard, Excel Import, and DB Reset

**Research Date:** 2026-02-15
**Project:** Chandelier ERP/POS
**Scope:** Multi-tenant SaaS onboarding with bulk data import capabilities

## Executive Summary

This document outlines the architectural components needed to add onboarding wizard, Excel data import, and database reset capabilities to Chandelier's existing FastAPI + PostgreSQL RLS multi-tenant architecture. The research synthesizes patterns from enterprise SaaS systems and adapts them to the microempresa candelería domain.

**Key Findings:**
- Onboarding wizards require 4 distinct backend components and 1 frontend state machine
- Excel import needs a 5-stage pipeline with RLS-aware bulk operations
- DB reset must be schema-aware with selective preservation logic
- All components integrate through existing tenant isolation mechanisms

---

## 1. Component Taxonomy

### 1.1 Database Reset System

**Purpose:** Wipe tenant operational data while preserving schema, seed data, and global tables.

#### Components:

```
db_reset/
├── reset_orchestrator.py      # Main entry point, transaction coordinator
├── preservation_rules.py      # Defines what to keep (PUC, plans, superadmin)
├── tenant_data_cleaner.py     # RLS-aware DELETE operations
├── validation_checker.py      # Pre/post-reset integrity checks
└── audit_logger.py            # Tracks reset operations for compliance
```

**Boundaries:**
- **IN:** Tenant ID, confirmation token, requesting user
- **OUT:** Success status, counts of deleted rows, audit log entry
- **DOES NOT:** Touch global tables (planes, tenants, usuarios), modify schema, handle rollback UI

**Integration Points:**
- Reads from: `usuarios_tenants` (verify admin role)
- Writes to: All tenant-scoped tables via RLS context
- Depends on: PostgreSQL transaction isolation, Alembic schema awareness

---

### 1.2 Onboarding Wizard (Frontend)

**Purpose:** Multi-step form capturing tenant setup data and file uploads.

#### Components:

```
frontend/src/features/onboarding/
├── OnboardingWizard.tsx           # Main container, step orchestration
├── steps/
│   ├── 01_CompanyInfo.tsx         # Tenant config (logo, prefijo_factura)
│   ├── 02_ChartOfAccounts.tsx     # Accounting opening balances
│   ├── 03_ProductsImport.tsx      # Excel upload + preview
│   ├── 04_ClientsImport.tsx       # Excel upload + preview
│   └── 05_Review.tsx              # Summary before commit
├── hooks/
│   ├── useOnboardingState.ts      # Zustand store for wizard data
│   ├── useFileUpload.ts           # Chunk upload, progress tracking
│   └── useImportValidation.ts     # Real-time validation feedback
└── components/
    ├── ExcelPreviewTable.tsx      # Shows parsed data before import
    ├── ValidationErrorList.tsx    # Row-level error display
    └── ProgressStepper.tsx        # Visual step indicator
```

**State Machine:**
```
START → company_info → chart_of_accounts → products_import
      → clients_import → review → IMPORTING → SUCCESS/ERROR
```

**Boundaries:**
- **IN:** User interactions, file uploads (xlsx), backend validation responses
- **OUT:** HTTP requests to backend import endpoints, UI state updates
- **DOES NOT:** Parse Excel files (backend only), persist state server-side (stateless wizard)

**Integration Points:**
- Calls: `/api/v1/onboarding/*` endpoints
- Uses: Existing `X-Tenant-ID` header mechanism
- Depends on: React Query for caching, Zustand for local state

---

### 1.3 Excel Import Pipeline (Backend)

**Purpose:** Parse, validate, transform, and bulk-insert Excel data with tenant isolation.

#### Stage Architecture:

```
┌─────────────┐
│ 1. UPLOAD   │  S3 storage, virus scan, size check
└──────┬──────┘
       │
┌──────▼──────┐
│ 2. PARSE    │  openpyxl → Python dicts, column mapping
└──────┬──────┘
       │
┌──────▼──────┐
│ 3. VALIDATE │  Schema validation, business rules, duplicate checks
└──────┬──────┘
       │
┌──────▼──────┐
│ 4. TRANSFORM│  Type coercion, PUC code lookup, FK resolution
└──────┬──────┘
       │
┌──────▼──────┐
│ 5. LOAD     │  Bulk INSERT with RLS context, transaction atomicity
└─────────────┘
```

#### Components:

```
backend/app/services/import_service/
├── __init__.py
├── orchestrator.py                # ImportOrchestrator class
├── parsers/
│   ├── base_parser.py             # Abstract parser interface
│   ├── products_parser.py         # Productos + recetas parsing
│   ├── clients_parser.py          # Clientes parsing
│   └── accounting_parser.py       # Opening balances parsing
├── validators/
│   ├── schema_validator.py        # Pydantic schema checks
│   ├── business_validator.py      # Domain rules (SKU unique, stock >= 0)
│   └── reference_validator.py     # FK existence checks (categoria_id, etc.)
├── transformers/
│   ├── data_normalizer.py         # Trim strings, format dates
│   ├── lookup_resolver.py         # Resolve PUC codes → IDs
│   └── default_applier.py         # Apply tenant-level defaults
├── loaders/
│   ├── bulk_loader.py             # PostgreSQL COPY or bulk INSERT
│   └── rls_context_manager.py    # SET LOCAL app.tenant_id_actual
└── result_builder.py              # ImportResult dataclass
```

**Boundaries:**
- **IN:** File stream (bytes), tenant_id, import type (productos/clientes/contabilidad)
- **OUT:** ImportResult (success count, error rows, preview data)
- **DOES NOT:** Generate Excel files (separate service), handle retries (client responsibility)

**Integration Points:**
- Reads from: S3/R2 (file storage), `categorias`, `cuentas_puc` (lookups)
- Writes to: `productos`, `clientes`, `asientos_contables`, `movimientos_stock`
- Depends on: SQLAlchemy async sessions, Celery for async processing (large files)

---

### 1.4 Template Generation Service

**Purpose:** Create downloadable Excel templates with pre-filled structure and validation hints.

#### Components:

```
backend/app/services/template_service/
├── __init__.py
├── template_generator.py          # Main class
├── builders/
│   ├── products_template.py       # Columns: SKU, Nombre, Precio, etc.
│   ├── clients_template.py        # Columns: NIT, Nombre, Email, etc.
│   └── accounting_template.py     # Columns: Código PUC, Debe, Haber
└── styles/
    ├── cell_formats.py            # Currency, date formats
    └── data_validation.py         # Dropdown lists (categorías, PUC codes)
```

**Template Structure:**
```
Sheet 1: "Instrucciones"  (Markdown-style guide)
Sheet 2: "Datos"          (Actual import columns)
Sheet 3: "Ref_Categorias" (Hidden, for dropdown validation)
Sheet 4: "Ref_PUC"        (Hidden, for dropdown validation)
```

**Boundaries:**
- **IN:** Template type (productos/clientes/contabilidad), tenant_id (for tenant-specific dropdowns)
- **OUT:** BytesIO stream with .xlsx file
- **DOES NOT:** Store templates (generated on-demand), include tenant data (empty template)

**Integration Points:**
- Reads from: `categorias`, `cuentas_puc` (for validation dropdowns)
- Uses: `openpyxl` library for Excel generation
- Depends on: Tenant isolation for category/PUC lists

---

### 1.5 Onboarding Endpoints (Backend API)

**Purpose:** RESTful endpoints orchestrating wizard flow.

#### Endpoint Design:

```
POST /api/v1/onboarding/company
├── Body: { nombre, url_logo, prefijo_factura, ... }
├── Updates: configuracion_tenant
└── Returns: { success: true, config: {...} }

POST /api/v1/onboarding/accounting/opening
├── Body: { cuentas: [{ codigo_puc, debe, haber, descripcion }] }
├── Creates: asiento_contable (tipo_origen='apertura')
└── Returns: { asiento_id, numero }

POST /api/v1/onboarding/import/preview
├── Body: multipart/form-data (file, import_type)
├── Parses: Excel → JSON preview (first 10 rows + validation)
└── Returns: { preview: [...], errors: [...], warnings: [...] }

POST /api/v1/onboarding/import/execute
├── Body: { import_job_id, confirmed: true }
├── Processes: Full import with RLS context
└── Returns: { job_id, status: 'processing' } (async via Celery)

GET /api/v1/onboarding/import/status/{job_id}
├── Returns: { status, progress, rows_imported, errors }
└── Uses: Celery result backend

POST /api/v1/onboarding/complete
├── Body: { confirmed: true }
├── Updates: tenant metadata (onboarding_completed_at)
└── Returns: { success: true, redirect_url: '/dashboard' }

GET /api/v1/templates/download/{type}
├── Params: type = productos | clientes | contabilidad
├── Generates: Excel template on-the-fly
└── Returns: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

**Boundaries:**
- **IN:** HTTP requests with `X-Tenant-ID`, JWT auth
- **OUT:** JSON responses, file streams (templates)
- **DOES NOT:** Handle file storage directly (delegates to import service), manage wizard UI state

**Integration Points:**
- Calls: ImportOrchestrator, TemplateGenerator services
- Depends on: Middleware for tenant context, Celery for async jobs

---

## 2. Data Flow Architecture

### 2.1 Onboarding Happy Path

```
┌─────────┐
│ User    │
└────┬────┘
     │ 1. Start onboarding
     ▼
┌─────────────────┐
│ Frontend Wizard │
├─────────────────┤
│ Step 1: Company │──2. POST /onboarding/company──┐
│ Step 2: PUC     │──3. POST /accounting/opening──┤
│ Step 3: Upload  │──4. POST /import/preview──────┤
│ Step 4: Review  │──5. POST /import/execute──────┤
│ Step 5: Complete│──6. POST /onboarding/complete─┤
└─────────────────┘                                │
                                                   │
     ┌─────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────┐
│ Backend API Router   │
├──────────────────────┤
│ Set RLS context      │ SET LOCAL app.tenant_id_actual = $1
│ Validate auth/role   │ Check usuarios_tenants.rol = 'admin'
│ Delegate to service  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Import Orchestrator  │
├──────────────────────┤
│ Parse Excel          │ openpyxl → dicts
│ Validate rows        │ Schema + business rules
│ Transform data       │ Lookup FK IDs
│ Bulk insert          │ RLS-aware INSERT
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ PostgreSQL with RLS  │
├──────────────────────┤
│ productos            │ INSERT with tenant_id
│ clientes             │ INSERT with tenant_id
│ asientos_contables   │ INSERT with tenant_id
└──────────────────────┘
```

### 2.2 Excel Import with Validation Errors

```
User uploads products.xlsx
         │
         ▼
┌────────────────────┐
│ POST /import/preview│
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Parse Stage        │
├────────────────────┤
│ Row 1: OK          │
│ Row 2: Missing SKU │──┐
│ Row 3: OK          │  │
│ Row 4: Invalid $   │──┤
└────────────────────┘  │
                        │
         ┌──────────────┘
         │
         ▼
┌────────────────────────┐
│ Validation Stage       │
├────────────────────────┤
│ errors: [              │
│   {row: 2, field: 'sku', message: 'Required'},
│   {row: 4, field: 'precio_costo', message: 'Must be > 0'}
│ ]                      │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Frontend Preview Table │ Shows errors inline with red highlights
├────────────────────────┤
│ User fixes Excel       │
│ Re-uploads             │ Loop back to POST /import/preview
└────────────────────────┘
```

### 2.3 Database Reset Flow

```
Admin clicks "Reset Data"
         │
         ▼
┌────────────────────────┐
│ Frontend Confirmation  │ Modal: "Are you sure? Type 'RESET' to confirm"
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ POST /api/admin/reset  │ Body: { tenant_id, confirmation: 'RESET' }
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Reset Orchestrator     │
├────────────────────────┤
│ 1. Validate requester  │ Check role = admin
│ 2. Start transaction   │ BEGIN
│ 3. Set RLS context     │ SET LOCAL app.tenant_id_actual
│ 4. Pre-reset snapshot  │ Count rows for audit
│ 5. Delete tenant data  │ DELETE FROM productos WHERE tenant_id = $1
│ 6. Validate integrity  │ Check FKs, constraints
│ 7. Commit transaction  │ COMMIT
│ 8. Log audit entry     │ INSERT INTO audit_logs
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Preserved Tables       │ (Untouched)
├────────────────────────┤
│ planes                 │
│ tenants                │
│ usuarios               │
│ usuarios_tenants       │
│ cuentas_puc            │ (Global PUC)
└────────────────────────┘
```

---

## 3. RLS Integration Patterns

### 3.1 Import Service RLS Context

**Challenge:** Bulk imports must respect tenant isolation without N+1 queries.

**Solution:**
```python
class BulkLoader:
    async def load_with_rls(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        table: Table,
        rows: List[dict]
    ):
        # Set RLS context ONCE per transaction
        await session.execute(
            text("SET LOCAL app.tenant_id_actual = :tenant_id"),
            {"tenant_id": str(tenant_id)}
        )

        # Bulk insert with tenant_id in every row
        stmt = insert(table).values([
            {**row, "tenant_id": tenant_id}
            for row in rows
        ])

        await session.execute(stmt)
        await session.commit()
```

**Key:** `SET LOCAL` persists for transaction duration, RLS policies enforce isolation even if tenant_id accidentally wrong.

### 3.2 Reset Service RLS Context

**Pattern:**
```python
async def reset_tenant_data(tenant_id: UUID):
    async with async_session() as session:
        async with session.begin():
            # Set RLS context
            await session.execute(
                text("SET LOCAL app.tenant_id_actual = :tenant_id"),
                {"tenant_id": str(tenant_id)}
            )

            # Delete operations (RLS ensures only this tenant's data deleted)
            for table in TENANT_TABLES:
                await session.execute(delete(table))

            # Validate (should be 0 rows for this tenant)
            count = await session.scalar(select(func.count()).select_from(productos))
            assert count == 0
```

**Safety:** RLS prevents cross-tenant deletion even with bugs in reset logic.

---

## 4. Component Dependencies (Build Order)

### Phase 1: Foundation (No dependencies)
1. **Template Generator Service** (standalone, no DB writes)
2. **Excel Parser Components** (stateless, file-only dependencies)

### Phase 2: Validation Layer (Depends on Phase 1)
3. **Schema Validators** (Pydantic models)
4. **Business Rule Validators** (reads existing DB data for uniqueness checks)

### Phase 3: Import Pipeline (Depends on Phase 1-2)
5. **Import Orchestrator** (coordinates parsers + validators)
6. **Bulk Loader with RLS** (writes to DB)
7. **Async Job System** (Celery tasks wrapping orchestrator)

### Phase 4: API Endpoints (Depends on Phase 1-3)
8. **Onboarding Endpoints** (REST API using import services)
9. **Template Download Endpoint** (uses template generator)

### Phase 5: Frontend (Depends on Phase 4)
10. **Onboarding Wizard UI** (multi-step form)
11. **Excel Preview Components** (displays validation results)

### Phase 6: Admin Tools (Depends on Phase 3)
12. **DB Reset Service** (orchestrator + cleaner)
13. **Reset UI** (admin panel integration)

**Critical Path:** 1 → 3 → 5 → 8 → 10 (Minimal viable onboarding)

---

## 5. Technology Stack Additions

### Backend Libraries
- **openpyxl** (3.1+): Excel parsing/generation (pure Python, no dependencies)
- **pandas** (2.2+): Optional for complex transformations (heavy dependency)
- **pydantic-extra-types**: Excel-specific validators (currency, date formats)
- **celery[redis]**: Async job processing (already in stack)

### Frontend Libraries
- **react-dropzone** (14+): File upload with drag-and-drop
- **xlsx** (0.20+): Client-side Excel preview (optional, reduces backend calls)
- **react-hook-form** (7+): Wizard form state management (already in stack)

### Database
- **No schema changes needed:** RLS policies already in place
- **New enum:** `tipo_origen` in `asientos_contables` add value `'apertura'`

---

## 6. Security Considerations

### 6.1 File Upload Security
- **Max size:** 10 MB (configurable)
- **Allowed types:** `.xlsx`, `.xls` (MIME type validation)
- **Virus scanning:** ClamAV integration (optional for MVP)
- **Storage:** S3 with presigned URLs (24h expiry)
- **Cleanup:** Delete uploaded files after processing (Celery task)

### 6.2 RLS Bypass Prevention
- **Never raw SQL:** Always use SQLAlchemy ORM with RLS context
- **Validate tenant_id:** Middleware checks `X-Tenant-ID` matches JWT tenant
- **Admin role check:** Reset endpoints require `rol = 'admin'`
- **Confirmation tokens:** Reset requires typing "RESET" (prevent accidental clicks)

### 6.3 Import Validation
- **Row limit:** Max 10,000 rows per import (prevent DoS)
- **Duplicate detection:** Check SKU/NIT uniqueness before insert
- **FK validation:** Verify categoria_id, cuenta_puc_id exist
- **Rollback on error:** Atomic transactions (all or nothing)

---

## 7. Performance Optimization

### 7.1 Bulk Insert Strategies
```python
# Bad: N individual INSERTs (slow)
for row in rows:
    session.add(Producto(**row))
await session.commit()

# Good: Single bulk INSERT (fast)
stmt = insert(Producto).values(rows)
await session.execute(stmt)
await session.commit()

# Best: PostgreSQL COPY (fastest, but complex)
await session.execute(
    text(f"COPY productos FROM STDIN WITH CSV HEADER"),
    csv_buffer
)
```

**Recommendation:** Use bulk INSERT for MVP (<10k rows), add COPY for Phase 2.

### 7.2 Validation Caching
- **Cache lookups:** Store categoria_id, cuenta_puc_id maps in memory during import
- **Debounce preview:** Frontend waits 500ms after file change before requesting preview
- **Chunked processing:** Process Excel in 1000-row batches to show progress

### 7.3 Database Indexes
```sql
-- Already exists (RLS queries)
CREATE INDEX idx_productos_tenant_sku ON productos(tenant_id, sku);

-- Add for import FK lookups
CREATE INDEX idx_categorias_tenant_nombre ON categorias(tenant_id, nombre);
CREATE INDEX idx_cuentas_puc_codigo ON cuentas_puc(codigo);
```

---

## 8. Error Handling Patterns

### 8.1 Import Error Types
```typescript
interface ImportError {
  row: number;           // 1-indexed (Excel row number)
  column: string;        // "SKU", "Precio Costo"
  severity: 'error' | 'warning';
  code: string;          // "REQUIRED_FIELD", "INVALID_FORMAT"
  message: string;       // Human-readable
  suggestion?: string;   // "Try: 10.50 instead of $10.50"
}
```

**Error Codes:**
- `REQUIRED_FIELD`: Missing value in required column
- `INVALID_FORMAT`: Wrong data type (text in number column)
- `DUPLICATE_VALUE`: SKU/NIT already exists
- `INVALID_REFERENCE`: categoria_id not found
- `BUSINESS_RULE`: precio_venta < precio_costo (warning)

### 8.2 Reset Validation Errors
```python
class ResetError(Exception):
    """Raised when reset preconditions fail"""
    pass

class ResetOrchestrator:
    async def reset(self, tenant_id: UUID, requester: Usuario):
        # Validation
        if not requester.es_admin_of(tenant_id):
            raise ResetError("Only admins can reset data")

        if tenant_id == PRODUCTION_TENANT_ID:
            raise ResetError("Cannot reset production tenant")

        # Execute with rollback on error
        try:
            await self._delete_tenant_data(tenant_id)
        except Exception as e:
            await session.rollback()
            raise ResetError(f"Reset failed: {str(e)}")
```

---

## 9. Testing Strategy

### 9.1 Unit Tests (Per Component)
- **Parsers:** Test with sample Excel files (valid, invalid, edge cases)
- **Validators:** Test business rules with mock data
- **Loaders:** Test bulk insert with in-memory SQLite + RLS simulation
- **Template Generator:** Test output file structure with openpyxl reader

### 9.2 Integration Tests (Cross-Component)
- **Full import flow:** Upload → Parse → Validate → Load → Verify DB state
- **RLS isolation:** Import for tenant A, verify tenant B cannot see data
- **Reset flow:** Import data → Reset → Verify preservation rules

### 9.3 E2E Tests (Frontend + Backend)
- **Onboarding wizard:** Playwright test completing all steps
- **Error handling:** Upload invalid Excel, verify error display
- **Template download:** Click download, verify file structure

---

## 10. Monitoring and Observability

### 10.1 Metrics to Track
- **Import success rate:** % of imports completing without errors
- **Average import time:** By file size and row count
- **Validation error rate:** Most common error codes
- **Reset frequency:** Number of resets per tenant (flag abuse)

### 10.2 Logging
```python
logger.info(
    "Import started",
    extra={
        "tenant_id": tenant_id,
        "import_type": "productos",
        "row_count": len(rows),
        "file_size_mb": file_size / 1024 / 1024
    }
)

logger.error(
    "Import failed",
    extra={
        "tenant_id": tenant_id,
        "error": str(e),
        "rows_processed": successful_rows,
        "rows_failed": len(errors)
    }
)
```

### 10.3 Alerts
- **Sentry:** Capture import exceptions with context (tenant, file metadata)
- **Slack webhook:** Notify on reset operations (audit trail)

---

## 11. Migration Path (Existing System → New Architecture)

### 11.1 Backward Compatibility
- **Existing routes unchanged:** No breaking changes to current API
- **Optional onboarding:** Tenants can skip wizard, use manual CRUD
- **Gradual rollout:** Feature flag `ENABLE_ONBOARDING_WIZARD=true`

### 11.2 Data Backfill
```python
# For existing tenants, mark onboarding as "completed" retroactively
UPDATE tenants
SET onboarding_completed_at = creado_en
WHERE creado_en < '2026-02-15';  # Before onboarding feature launch
```

---

## 12. Open Questions (For Roadmap Discussion)

1. **Async vs Sync Import:**
   - Small files (<1000 rows): Synchronous response (200 OK with result)
   - Large files (>1000 rows): Async Celery job (202 Accepted, poll for status)
   - **Decision needed:** Where is the threshold?

2. **Template Customization:**
   - Should templates include tenant-specific categories pre-filled?
   - Or always start with empty template + reference sheet?
   - **Trade-off:** Convenience vs. file size

3. **Duplicate Handling Strategy:**
   - Skip duplicates (INSERT IGNORE)?
   - Update existing (UPSERT)?
   - Abort entire import?
   - **Recommendation:** Configurable per import type

4. **Opening Balance Validation:**
   - Require balanced entry (debe = haber)?
   - Allow unbalanced "draft" opening?
   - **Accounting rule:** Strictly balanced for MVP

5. **Reset Granularity:**
   - Reset all data (nuclear option)?
   - Reset by module (only productos, only clientes)?
   - **MVP:** All-or-nothing, add granularity in Phase 2

---

## 13. Recommended Build Sequence

### Sprint 1: Foundation (1 week)
- [ ] Template Generator Service (backend)
- [ ] Template Download Endpoint
- [ ] Basic Excel parser (products only)
- [ ] Unit tests for parser + generator

### Sprint 2: Validation Pipeline (1 week)
- [ ] Schema validators (Pydantic)
- [ ] Business rule validators
- [ ] Import preview endpoint
- [ ] Frontend: Excel upload + preview table

### Sprint 3: Import Execution (1 week)
- [ ] Bulk loader with RLS
- [ ] Import orchestrator
- [ ] Execute endpoint
- [ ] Async job (Celery) for large files

### Sprint 4: Onboarding Wizard (1 week)
- [ ] Frontend wizard skeleton (5 steps)
- [ ] Company info step + accounting opening
- [ ] Integration with import endpoints
- [ ] Complete onboarding endpoint

### Sprint 5: DB Reset + Polish (1 week)
- [ ] Reset orchestrator + cleaner
- [ ] Admin reset UI
- [ ] Error handling refinement
- [ ] E2E testing

**Total MVP estimate:** 5 sprints (5 weeks) assuming 1 FTE

---

## 14. Key Architectural Decisions

### Decision 1: Synchronous Preview, Async Execution
**Rationale:** Preview needs immediate feedback for user to fix errors. Execution can be async for large files (show progress bar).

### Decision 2: Backend Excel Parsing (Not Client-Side)
**Rationale:** Security (validate files server-side), consistency (same parser for preview + execution), performance (avoid large file upload twice).

### Decision 3: Single Transaction for Import
**Rationale:** Atomic all-or-nothing guarantee. Rollback on any error prevents partial data corruption.

### Decision 4: RLS as Safety Net (Not Primary Enforcement)
**Rationale:** Application code includes tenant_id explicitly in queries for performance. RLS catches bugs, not intended as main mechanism.

### Decision 5: Template Generation On-Demand (Not Pre-Generated)
**Rationale:** Templates include tenant-specific dropdowns (categories). Cannot pre-generate. Acceptable latency (<500ms).

---

## Appendices

### A. Sample Excel Template Structure

**Sheet: "Datos_Productos"**
| SKU       | Nombre              | Categoría | Tipo              | Precio Costo | Precio Venta | Stock Inicial | IVA (%) |
|-----------|---------------------|-----------|-------------------|--------------|--------------|---------------|---------|
| VEL-001   | Vela Lavanda 200g   | Aromáticas| Producto Terminado| 1614         | 4035         | 50            | 19      |
| CER-SOY-1 | Cera Soya 1kg       | Materias  | Materia Prima     | 8500         | 0            | 10            | 0       |

**Sheet: "Ref_Categorias"** (Hidden)
| Nombre     |
|------------|
| Aromáticas |
| Materias   |

**Validation:** Column "Categoría" has data validation dropdown sourcing from "Ref_Categorias!A2:A100"

### B. Import Result Schema

```json
{
  "success": true,
  "summary": {
    "total_rows": 150,
    "imported": 148,
    "skipped": 2,
    "errors": 2
  },
  "errors": [
    {
      "row": 23,
      "column": "SKU",
      "severity": "error",
      "code": "DUPLICATE_VALUE",
      "message": "SKU 'VEL-001' already exists",
      "suggestion": "Use a unique SKU or update existing product"
    }
  ],
  "warnings": [
    {
      "row": 45,
      "column": "Precio Venta",
      "severity": "warning",
      "code": "BUSINESS_RULE",
      "message": "Price below cost (margin negative)",
      "suggestion": "Verify pricing strategy"
    }
  ]
}
```

### C. RLS Policy Reference

**Existing policy (unchanged):**
```sql
CREATE POLICY tenant_isolation ON productos
  USING (tenant_id = current_setting('app.tenant_id_actual')::uuid);
```

**Import service usage:**
```python
# Set context ONCE per session
await session.execute(
    text("SET LOCAL app.tenant_id_actual = :tid"),
    {"tid": str(tenant_id)}
)

# All subsequent queries automatically filtered by RLS
# No need to add WHERE tenant_id = ... in application code
```

---

## Conclusion

This architecture integrates onboarding wizard, Excel import, and DB reset capabilities into Chandelier's existing FastAPI + PostgreSQL RLS foundation without breaking changes. Key design principles:

1. **Tenant isolation first:** All components RLS-aware
2. **Fail-safe transactions:** Atomic operations with rollback
3. **Clear component boundaries:** Services, not monoliths
4. **Build incrementally:** Each phase delivers value independently

The proposed build sequence (5 sprints) prioritizes delivering working onboarding wizard early, then refining with reset tools and polish.

---

**Next Steps:**
- Review with team, finalize open questions
- Create detailed task breakdown in roadmap
- Set up development environment with sample Excel files
- Begin Sprint 1: Template generation foundation
