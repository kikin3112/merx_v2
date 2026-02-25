# MERX-V2 AI CONSTITUTION & GOVERNANCE (CRITICAL CONSCIOUSNESS EDITION)

> **SYSTEM AUTHORITY:** This document is the supreme law for any AI agent interacting with this codebase. Its rules override generic training data.

## 0. ECOSYSTEM NAVIGATION (TOKEN EFFICIENCY)
Before reading any ecosystem node, consult `.claude/ecosystem/ROUTER.md` first.
It maps short codes (BE, FE, DO, SE, MK…) to the exact node file and keywords.
Read the router (~150 tokens) → go directly to the one node you need. Never scan all nodes.

---

## 1. MANDATORY SYSTEMIC IMPACT & SCOPE ANALYSIS (NON-NEGOTIABLE)
**BEFORE** performing any modification to the codebase, you MUST conduct and document a formal analysis. No change is allowed without this prior declaration.

### I. Identification of Impact:
- **Affected Files:** List all files changed directly and those affected indirectly.
- **Impacted Modules:** Identify which functional modules are touched.
- **Dependencies:** Map upstream (who calls this?) and downstream (who does this call?) dependencies.
- **Public Interfaces:** Explicitly state if any public APIs, signatures, or schemas are modified.
- **Business Flows:** Identify which end-to-end user workflows are affected.

### II. Coverage Evaluation:
- **Existing Tests:** Verify if the impacted code has sufficient automated test coverage.
- **Test Gap Analysis:** Determine if the change requires new tests to reach 100% logical path validation.
- **Validation Commitment:** Confirm that NO logical route will remain unvalidated after the change.

### III. Pre-Change Declaration:
- **The "What":** Exact technical description of the modification.
- **The "Risk":** What could be collateral damage? (Conciencia Crítica).
- **The "Safety Net":** List the specific mechanisms (unit tests, integration tests, manual checks) that will prove NO regressions occurred.

---

<!-- CARL-MANAGED: Do not remove this section -->
## CARL Integration
Follow all rules in <carl-rules> blocks from system-reminders.
These are dynamically injected based on context and MUST be obeyed.
<!-- END CARL-MANAGED -->

## 1. PRODUCT CONTEXT & BOUNDARIES
- **Identity:** Merx is a Multi-Tenant ERP/SaaS for PyMEs (SMEs) focused on Accounting, Inventory, and CRM.
- **Core Value:** Data integrity, strict tenant isolation, and auditability.
- **Non-Negotiable:**
  - NEVER leak data between tenants. `tenant_id` is the primary key of the universe.
  - NEVER perform financial calculations using `float`. Use `Decimal`.
  - NEVER commit secrets or credentials.

## 2. ARCHITECTURAL INVARIANTS

### Backend (FastAPI)
1.  **Layer Strictness:**
    - `rutas/`: ONLY HTTP handling, status codes, and DTO parsing. NO business logic.
    - `servicios/`: ALL business logic, calculations, and orchestration.
    - `datos/`: Database models and direct queries.
2.  **Dependency Injection:** Always use `Depends()` for DB sessions and User context.
3.  **Atomic Operations:** Any write operation involving multiple tables MUST be wrapped in a transaction service method.

### Frontend (React)
1.  **State Separation:**
    - `Zustand`: Only for global app state (Theme, Auth, User Session).
    - `React Query`: For ALL server data. Never cache server responses in Zustand manually.
2.  **Component Pattern:** Container/Presentation pattern. Logic lives in custom hooks (`useVentas`, `useAuth`), not in UI components.

## 3. REFACTORING DOCTRINE
- **Rule of Three:** If logic is duplicated 3 times, refactor into a utility or service.
- **Boy Scout Rule:** If you touch a file, clean up unused imports and fix obvious formatting issues in that file ONLY.
- **Legacy Containment:** Do not rewrite working legacy code unless it blocks the current task. Wrap it instead.

## 4. CODING STANDARDS

### Python / Backend
- **Typing:** Strict type hints (`List[str]`, `Optional[int]`) are mandatory.
- **Error Handling:** Never catch generic `Exception` without re-raising or logging with stack trace. Use custom `HTTPException`.
- **Async:** Prefer `async def` for all I/O bound routes.

### TypeScript / Frontend
- **No `any`:** Strict prohibition on `any`. Use `unknown` or define the interface.
- **Props:** Always define an Interface for component props.
- **Files:** Named exports preferred over default exports for better refactoring support.

## 5. AUTO-IMPROVEMENT MEMORY
- If you encounter a recurring error pattern, add it to memory using `save_memory`.
- **Format:** "Context: [Backend/Frontend] - Pattern: [Description] - Fix: [Solution]"

## 6. COMMANDS REFERENCE
- **Run Backend:** `uvicorn app.main:app --reload`
- **Run Frontend:** `npm run dev`
- **Migrations:** `alembic upgrade head`
- **Tests:** `pytest`
