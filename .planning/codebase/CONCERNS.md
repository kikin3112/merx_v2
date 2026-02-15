# Codebase Concerns

**Analysis Date:** 2026-02-15

## Critical Issues

### 1. Unprotected Seed Endpoint

**Issue:** The `/api/v1/admin/seed` endpoint lacks authentication guards
- **Files:** `backend/app/main.py` (lines 516-549)
- **Problem:** TODO comments indicate admin authentication is not implemented. Any unauthenticated request can populate database with test data
- **Impact:** Data corruption, test data contamination in production, potential security vulnerability
- **Current State:**
  ```python
  @app.post(f"{prefix}/admin/seed", tags=["Administración"])
  def ejecutar_seeds(current_user=None):  # TODO: Agregar dependency de autenticación admin
      # Endpoint is EXPOSED without auth checks
  ```
- **Fix Approach:**
  1. Implement `require_superadmin()` dependency
  2. Disable endpoint in production (`if settings.ENVIRONMENT == 'production'`)
  3. Add audit logging
  4. Return 403 if not superadmin

### 2. Unprotected Maintenance Mode Cache - Synchronous DB Query in Async Middleware

**Issue:** Maintenance mode check performs synchronous database query in async middleware
- **Files:** `backend/app/middleware/tenant_context.py` (lines 27-54)
- **Problem:**
  - `_is_tenant_in_maintenance()` is called in async middleware but blocks with sync DB session
  - Not using async driver - potential thread pool exhaustion
  - TTL cache has no invalidation mechanism except timeout
  - On error, returns False allowing request through (wrong default)
- **Impact:**
  - Performance degradation during maintenance
  - Race conditions if maintenance state changes during 60s TTL window
  - Requests may bypass maintenance mode during transitions
- **Fix Approach:**
  1. Move to async method if possible or pre-fetch maintenance states
  2. Implement proper cache invalidation hook
  3. Return True on error (safer default - deny on error)
  4. Add cache metrics/monitoring

### 3. Silent Error Returns in PDF/Storage Services

**Issue:** Storage and PDF operations return `None` instead of propagating errors
- **Files:**
  - `backend/app/servicios/servicio_almacenamiento.py` (lines 64, 80, 93, 107)
  - `backend/app/servicios/servicio_pdf.py`
- **Problem:**
  ```python
  def subir_pdf(...) -> Optional[str]:
      if not self.is_enabled or not self._client:
          return None  # Silent failure
  ```
- **Impact:** Callers cannot distinguish between "S3 disabled" and "upload failed". PDFs may fail to save without error notification
- **Fix Approach:**
  1. Distinguish between disabled (return None) vs error (raise exception)
  2. Log all failures with context
  3. Update callers to handle both cases explicitly

### 4. Missing Tenant Context in Multiple Routes

**Issue:** Some routes don't properly validate X-Tenant-ID header presence
- **Files:**
  - `backend/app/middleware/tenant_context.py` (lines 94-115)
  - `backend/app/rutas/crm.py` (entire file uses `get_tenant_id_from_token` instead of validating header)
- **Problem:**
  - CRM routes depend on JWT tenant_id instead of header validation
  - No validation that user has access to requested tenant
  - Potential tenant isolation bypass
- **Impact:** Users could access other tenants if JWT is reused/manipulated
- **Fix Approach:**
  1. Create unified middleware that validates X-Tenant-ID matches JWT tenant_id
  2. Audit all routes for tenant access validation
  3. Add permission check: `assert user_tenant_access(user_id, tenant_id)`

### 5. Exposed Admin Endpoints Without Rate Limiting

**Issue:** Superadmin endpoints lack rate limiting on sensitive operations
- **Files:**
  - `backend/app/main.py` (line 516)
  - `backend/app/rutas/tenants.py` (admin/superadmin endpoints)
- **Problem:** No rate limit on seed, tenant creation, plan management
- **Impact:** Brute force attacks, denial of service vectors
- **Fix Approach:**
  1. Apply `@limiter.limit("5/hour")` to all admin endpoints
  2. Use IP-based limiting for tenant management
  3. Add alert on repeated failures

## Tech Debt

### 1. Large Service Files - Low Cohesion

**Issue:** Service classes are too large and handle multiple concerns
- **Files:**
  - `backend/app/servicios/servicio_tenants.py` (1,186 lines)
  - `backend/app/datos/esquemas.py` (1,439 lines)
  - `backend/app/datos/modelos.py` (1,188 lines)
  - `backend/app/rutas/tenants.py` (1,208 lines)
- **Problem:**
  - Single file does CRUD, auth, billing, onboarding, admin operations
  - Hard to test individual features
  - High complexity (McCabe)
  - Difficult to navigate and maintain
- **Mitigation:** Files are stable and well-structured despite size
- **Fix Approach:**
  1. Split `ServicioTenants` into:
     - `ServicioTenantsCRUD` - basic operations
     - `ServicioTenantsBilling` - subscription/payment handling
     - `ServicioTenantsOnboarding` - registration flow
  2. Create separate schema files by domain (tenant_schemas.py, billing_schemas.py)
  3. Break models.py into feature-specific files: models_crm.py, models_inventory.py

### 2. Inconsistent Error Handling Patterns

**Issue:** Mixed error handling approaches across codebase
- **Files:** All service files (`backend/app/servicios/*`)
- **Problem:**
  ```python
  # Pattern 1: Exception on error
  if not plan:
      raise ValueError("Plan no encontrado")

  # Pattern 2: Silent return None
  def obtener_plan_por_id(...) -> Optional[Planes]:
      return self.db.query(...).first()  # Returns None, no error

  # Pattern 3: HTTPException in routes
  raise HTTPException(status_code=404, detail="Not found")
  ```
- **Impact:** Inconsistent client error handling, unclear error boundaries
- **Fix Approach:**
  1. Establish error handling policy:
     - Services: Raise domain exceptions (ValueError, custom exceptions)
     - Routes: Convert to HTTPException with proper status codes
     - Middleware: Log and propagate to global handler
  2. Create custom exception hierarchy:
     ```python
     class BusinessLogicError(Exception): pass
     class ValidationError(BusinessLogicError): pass
     class TenantAccessError(BusinessLogicError): pass
     ```

### 3. Circular Import Risk in Client Module

**Issue:** API client has circular dependency workaround
- **Files:** `frontend/src/api/client.ts` (lines 119-125)
- **Problem:**
  ```typescript
  // Lazy import to avoid circular dependency
  const { useAuthStore } = await import('../stores/authStore');
  ```
- **Impact:**
  - Fragile - breaks silently if import fails
  - Not caught by build-time checks
  - Runtime error possible
- **Fix Approach:**
  1. Restructure imports: move auth state to separate module
  2. Use dependency injection for client initialization
  3. Avoid importing client in store init

### 4. No Rate Limiting on File Uploads

**Issue:** File upload endpoints lack size/rate limits
- **Files:** `backend/app/servicios/servicio_almacenamiento.py`
- **Problem:**
  - No `@limiter.limit()` on upload routes
  - Max upload sizes defined in comments only, not enforced at app level
  - No content-type validation before S3
- **Impact:**
  - Storage exhaustion attacks
  - Bandwidth waste
  - Quota bypass
- **Fix Approach:**
  1. Add middleware to validate Content-Length before processing
  2. Apply `@limiter.limit("10/hour")` to upload endpoints
  3. Validate file type before S3: check magic bytes, not just extension
  4. Implement per-tenant storage quota checks

### 5. Missing Test Coverage for Core Features

**Issue:** Very limited test suite
- **Files:**
  - `backend/tests/test_inventario_concurrency.py` (concurrency tests only)
  - `backend/tests/test_rbac_backend.py` (RBAC tests only)
- **Problem:**
  - No tests for: auth flow, tenant isolation, financial operations, PDF generation
  - Concurrency tests use mocks, not real transactions
  - No integration tests
  - No E2E tests for critical flows
- **Impact:**
  - Regressions undetected
  - Tenant isolation bugs not caught
  - Production incidents possible
- **Fix Approach:**
  1. Add pytest fixtures for common scenarios
  2. Test suites for:
     - Authentication (JWT, multi-tenant)
     - RLS policies (verify data isolation)
     - Inventory operations (with concurrency)
     - Financial operations (asiento balance, double-entry)
     - Tenant lifecycle
  3. Integration test framework with test database

### 6. Hardcoded Configuration in Routes

**Issue:** Some configuration is hardcoded in code instead of environment
- **Files:**
  - `backend/app/main.py` (line 284): hardcoded allowed_hosts
  - `backend/app/servicios/servicio_inventario.py`: hardcoded cost calculation method
- **Problem:**
  ```python
  allowed_hosts = ["api.tudominio.com", "www.tudominio.com"]  # Hardcoded!
  ```
- **Impact:**
  - Not configurable per environment
  - Requires code change for new domains
  - Security misconfiguration risk
- **Fix Approach:**
  1. Move to `config.py`: `TRUSTED_HOSTS: str = Field(default="...")`
  2. Parse at startup with validation
  3. Log configuration at initialization

## Performance Issues

### 1. In-Memory List Processing in Dashboard

**Issue:** Dashboard endpoint loads all records into memory and filters in Python
- **Files:** `backend/app/rutas/reportes.py` (lines 21-81)
- **Problem:**
  ```python
  ventas = query.all()  # Loads ALL records
  ventas_hoy = [v for v in ventas if v.fecha_venta == hoy]  # Filter in Python
  ```
- **Impact:**
  - O(n) memory for large datasets
  - Slow for tenants with 10k+ sales
  - Database indexes not used
- **Current Scale:** MVP level (microempresas < 1000 sales/month)
- **Fix Approach:**
  1. Move filtering to SQL:
     ```python
     ventas_hoy = db.query(Ventas).filter(
         Ventas.tenant_id == ctx.tenant_id,
         Ventas.fecha_venta == hoy
     ).all()
     ```
  2. Aggregate with SQL:
     ```python
     total_hoy = db.query(func.sum(Ventas.total_venta))...
     ```

### 2. Missing Database Indexes on Frequently Queried Columns

**Issue:** Some queries lack corresponding indexes
- **Files:** `backend/app/datos/modelos.py`, `alembic/versions/*`
- **Problem:**
  - `Ventas.tercero_id` - filtered frequently, no index documented
  - `Inventarios.producto_id` - join frequently
  - `AsientosContables.fecha` - range queries, needs index
- **Impact:** Slow queries at scale (50k+ records)
- **Fix Approach:**
  1. Audit slow queries (enable `query_log_duration = 100ms`)
  2. Add composite indexes:
     - `(tenant_id, tercero_id)` on ventas
     - `(tenant_id, fecha)` on asientos_contables
     - `(tenant_id, estado)` on ventas, facturas
  3. Monitor query execution plans

### 3. Full-Text Search Not Implemented

**Issue:** Customer/product search uses ILIKE with %-patterns
- **Files:** `backend/app/servicios/servicio_tenants.py` (line 96)
- **Problem:**
  ```python
  .filter(Tenants.nombre.ilike(f"%{busqueda}%"))  # SLOW - can't use indexes
  ```
- **Impact:**
  - Search is slow on large datasets
  - CPU intensive (regex matching)
  - Not suitable for autocomplete
- **Fix Approach:**
  1. Add PostgreSQL full-text search with GIN index
  2. Create tsvector columns for searchable fields
  3. Implement search ranking/relevance

## Security Issues

### 1. JWT Secret Rotation Not Implemented

**Issue:** JWT secret is static, no rotation mechanism
- **Files:** `backend/app/config.py` (line 149), `backend/app/utils/seguridad.py`
- **Problem:**
  - If secret leaks, all tokens valid forever
  - No way to invalidate old tokens
  - Production uses same secret for refresh + access tokens
- **Impact:** Compromised tokens cannot be revoked
- **Fix Approach:**
  1. Implement token blacklist/revocation list (Redis)
  2. Add secret rotation mechanism with grace period
  3. Implement token versioning (kid in JWT header)
  4. Add logout endpoint that blacklists tokens

### 2. No CSRF Protection on State-Changing Operations

**Issue:** PUT/POST/DELETE endpoints lack CSRF tokens
- **Files:** All routes in `backend/app/rutas/*`
- **Problem:**
  - Assumes same-origin requests only
  - If frontend is on different domain, vulnerable to CSRF
  - No SameSite cookie flags (if cookies used)
- **Impact:** Cross-site request forgery attacks possible
- **Fix Approach:**
  1. Add `@app.middleware` to validate origin/referer
  2. For sensitive ops, require CSRF token
  3. Set SameSite=Strict on cookies
  4. Validate X-Requested-With header

### 3. Password Hashing Configuration Could Be Stronger

**Issue:** Argon2 parameters may not match threat model
- **Files:** `backend/app/utils/seguridad.py` (lines 40-46)
- **Problem:**
  ```python
  pwd_context = CryptContext(
      schemes=["argon2"],
      argon2__memory_cost=65536,  # 64 MB - acceptable
      argon2__time_cost=3,        # 3 iterations - may be low for 2026
      argon2__parallelism=4       # 4 threads
  )
  ```
- **Current State:** Adequate for MVP but should increase over time
- **Fix Approach:**
  1. Increase time_cost to 4-5 for production
  2. Monitor hash computation time (should be < 500ms)
  3. Plan migration path for existing hashes

### 4. No Input Validation on Critical Fields

**Issue:** Some financial fields accept arbitrary decimals without bounds
- **Files:** `backend/app/datos/esquemas.py`, `backend/app/datos/modelos.py`
- **Problem:**
  ```python
  # No max value validation
  precio_venta: Decimal  # Could be 999,999,999.99
  cantidad: Integer      # Could be negative despite DB check
  ```
- **Impact:**
  - Accounting errors from extreme values
  - Integer overflow in calculations
  - Financial audits may fail
- **Fix Approach:**
  1. Add field validators for financial amounts:
     ```python
     @field_validator('precio_venta')
     def validate_precio(v):
         if v < Decimal('0.01') or v > Decimal('999999999.99'):
             raise ValueError('Price out of range')
     ```
  2. Use Decimal(6,2) precision in database
  3. Document maximum transaction size

### 5. Insufficient Audit Trail for Financial Operations

**Issue:** Asiento contable changes not fully audited
- **Files:** `backend/app/datos/modelos.py`, no audit log for asiento modifications
- **Problem:**
  - No who/when/what for asiento creation
  - Deletions use soft-delete but changes aren't logged
  - No changelog for reconciliation
- **Impact:**
  - Cannot prove asiento integrity
  - Regulatory non-compliance (SAS 70)
  - Fraud detection impossible
- **Fix Approach:**
  1. Add audit columns to AsientosContables:
     - `creado_por_id`, `creado_en`
     - `modificado_por_id`, `modificado_en`
  2. Create AsientosAudit table for all changes
  3. Implement immutability: no updates after creation
  4. Add certificate hash for tamper detection

## Fragile Areas

### 1. Receta/BOM Validation - No Quantity Constraints

**Issue:** Recipe ingredient quantities not validated
- **Files:** `backend/app/datos/modelos.py`, `backend/app/rutas/recetas.py`
- **Problem:**
  - No validation that quantities are positive
  - No max ingredients per recipe
  - Circular recipe dependencies not detected
- **Impact:**
  - Invalid recipes cause production errors
  - Infinite loops possible in cost calculation
  - Nonsensical production data
- **Safe Modification:**
  1. Add CHECK constraint: `cantidad > 0`
  2. Implement graph cycle detection before saving
  3. Test with max ingredients scenario

### 2. Cotización to Factura Conversion - No Idempotency

**Issue:** Converting quote to invoice not idempotent
- **Files:** `backend/app/rutas/cotizaciones.py`
- **Problem:**
  - Multiple calls create duplicate invoices
  - No guard against double-conversion
  - Network retry could duplicate transaction
- **Impact:**
  - Revenue recognition issues
  - Inventory double-deduction
  - Duplicate customer charges
- **Test Coverage:** Missing
- **Fix Approach:**
  1. Add unique constraint on (cotizacion_id, factura_id)
  2. Check if already converted before creating new invoice
  3. Make endpoint idempotent by checking state first

### 3. Multi-Step Transaction with Partial Failures

**Issue:** Emitting invoice has multiple non-atomic steps
- **Files:** `backend/app/rutas/facturas.py` (lines 116+)
- **Problem:**
  1. Generate PDF
  2. Upload to S3
  3. Save in DB

  If step 2 fails, step 3 never runs → inconsistent state
- **Impact:**
  - Factura exists without PDF URL
  - Cannot download/view factura
  - Retry unclear (partial state)
- **Safe Modification:**
  1. Use database transaction that wraps all steps
  2. Generate PDF but don't persist until DB save succeeds
  3. Use saga pattern for S3 rollback
  4. Add status field: `pdf_status: PENDING|UPLOADED|FAILED`

### 4. Inventory Cost Calculation - Rounding Errors Possible

**Issue:** Weighted average cost uses Decimal but may accumulate errors
- **Files:** `backend/app/servicios/servicio_inventario.py`
- **Problem:**
  ```python
  # After many operations, costo_promedio_ponderado may drift
  nuevo_costo = (stock * costo_actual + entrada * costo_nuevo) / nuevo_stock
  ```
- **Impact:**
  - Over time, total inventory value ≠ sum(stock × cost)
  - Accounting reconciliation fails
  - Financial statements inaccurate
- **Fix Approach:**
  1. Use FIFO instead of weighted-average (simpler)
  2. If keeping WAC, add reconciliation job:
     - Weekly: recalculate all costs from transaction log
     - Alert if drift > threshold
  3. Store movement history for recomputation

## Performance Bottlenecks

### 1. N+1 Query in Tenant Listing with Stats

**Issue:** Loading tenant stats triggers query per tenant
- **Files:** `backend/app/rutas/tenants.py` (admin listing)
- **Problem:**
  - List 100 tenants
  - For each: count usuarios, count facturas, sum revenue (3 more queries each)
  - Total: 1 + (100 × 3) = 301 queries
- **Current Capacity:** Works for < 50 tenants (MVP)
- **Improvement Path:**
  1. Use `joinedload()` and aggregation in single query
  2. Denormalize stats to tenants table (updated weekly)
  3. Cache at Redis level

### 2. Dashboard Sorting in Memory

**Issue:** Reporting sorts large result sets in Python
- **Files:** `backend/app/rutas/reportes.py`
- **Problem:** `sorted([...large list...])` instead of SQL ORDER BY
- **Scaling Limit:** 5000+ sales causes noticeable delay
- **Improvement Path:**
  1. Use SQL ORDER BY/LIMIT before fetch
  2. Paginate results

## Scaling Limits

### 1. Webhook Processing Synchronous

**Issue:** Wompi webhook processing is synchronous
- **Files:** Backend has no webhook implementation yet (TODO)
- **Problem:**
  - If Wompi sends webhook while processing long request, timeout
  - Cannot handle burst of webhooks
  - External dependency blocks payment processing
- **Current Capacity:** Single webhook/sec
- **Scaling Path:**
  1. Add Celery task queue for webhook processing
  2. Implement webhook retry/idempotency (webhook_id tracking)
  3. Use dead-letter queue for failed webhooks

### 2. Session Management Not Distributed

**Issue:** JWT refresh in-memory queue (frontend)
- **Files:** `frontend/src/api/client.ts` (lines 65-66)
- **Problem:**
  - `refreshQueue` only exists in single tab/window
  - Multiple tabs make duplicate refresh requests
  - Memory not shared across browser windows
- **Current Capacity:** Works for single tab
- **Scaling Path:**
  1. Use localStorage events to coordinate refresh
  2. Implement distributed lock (Redlock) on backend
  3. Use service worker for token coordination

### 3. Single Database Connection Bottleneck

**Issue:** Connection pool fixed size for all operations
- **Files:** `backend/app/config.py` (lines 55-80)
- **Configuration:**
  ```python
  DB_POOL_SIZE: int = 10           # Default pool
  DB_MAX_OVERFLOW: int = 20        # Max additional connections
  ```
- **Current Capacity:** 30 concurrent connections max
  - 2 users per connection = 15 concurrent users
  - Spiking queries exhaust pool
- **Improvement Path:**
  1. Separate read/write pools
  2. Async queries for read-heavy endpoints
  3. Query timeout enforcement (already at 30s)

## Dependencies at Risk

### 1. Outdated Pydantic v2 Migration

**Issue:** Code migrated to Pydantic v2 but using deprecated patterns
- **Files:** `backend/app/datos/esquemas.py`, `backend/app/config.py`
- **Problem:**
  - Some validators use old `@root_validator` style
  - No `ConfigDict` usage observed
  - Might be mixed patterns
- **Migration Status:** Mostly complete but incomplete audit
- **Fix Approach:**
  1. Audit all validators for v1 vs v2 compatibility
  2. Standardize on ConfigDict
  3. Test with Pydantic v3 early

### 2. SQLAlchemy 2.0 - Async Not Fully Utilized

**Issue:** Using SQLAlchemy 2.0 but sync driver only
- **Files:** All `backend/app/datos/*` and `backend/app/servicios/*`
- **Problem:**
  - FastAPI is async but DB calls are sync (blocking)
  - SQLAlchemy async support available but not used
  - Thread pool may be exhausted
- **Impact:** Cannot scale beyond thread pool size (~1000 requests)
- **Migration Effort:** Medium (changes in connection handling)
- **Fix Approach:** (Phase 2)
  1. Use `asyncpg` driver instead of psycopg2
  2. Convert servicios to async
  3. Use `sessionmaker(AsyncSession)`

### 3. ReportLab Hard-Coded PDF Generation

**Issue:** PDF generation tightly coupled to ReportLab
- **Files:** `backend/app/servicios/servicio_pdf.py`
- **Problem:**
  - Cannot easily swap for other PDF generator (e.g., WeasyHTML)
  - No interface/abstraction for PDF generation
  - Hard to test (complex setup)
- **Impact:**
  - Switching libraries requires rewrite
  - Testing requires actual PDF creation
- **Fix Approach:**
  1. Create `IPdfGenerator` interface
  2. Implement adapters for ReportLab, WeasyHTML
  3. Dependency inject in routes

### 4. Alembic Migrations - Manual Handling of RLS Policies

**Issue:** RLS policies not managed by Alembic
- **Files:** `backend/app/middleware/tenant_context.py` (lines 234-262), migrations manual
- **Problem:**
  - RLS creation/updates done manually
  - Not in Alembic migrations
  - New tables may forget RLS setup
- **Risk:** Data isolation breach if RLS forgotten
- **Fix Approach:**
  1. Create custom Alembic directives for RLS
  2. Template all table creation with RLS
  3. Validation: test all tables for RLS policies

## Missing Features

### 1. No Token Revocation/Blacklist

**Issue:** Logged-out users can still use old tokens
- **Impact:** Session hijacking not recoverable
- **Current Status:** Not implemented
- **Blocker:** None - can add in Phase 2
- **Fix Approach:**
  1. Redis blacklist: `SETEX token:${token_hash} ${ttl} 1`
  2. Check on every request: `EXISTS token:${token_hash}`
  3. Clear on logout

### 2. Webhook Implementation Missing

**Issue:** Wompi payment webhooks not implemented
- **Files:** Mentioned in CLAUDE.md but no code
- **Status:** Blocking subscription SaaS flow
- **Implementation Size:** Medium (endpoint + payment state machine)
- **Fix Approach:**
  1. Create `/api/v1/webhooks/wompi` endpoint
  2. Validate HMAC signature
  3. Update subscription state
  4. Idempotency: track webhook IDs

### 3. No Email Sending Implementation

**Issue:** Celery tasks for emails exist but SMTP config incomplete
- **Files:** `backend/app/config.py` (SMTP fields exist)
- **Status:** Not blocking MVP but needed for invites
- **Fix Approach:**
  1. Add to settings: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
  2. Implement email service: template rendering + SMTP
  3. Wire into onboarding flow

## Test Coverage Gaps

### 1. RLS Policies - No Verification

**Issue:** No tests verify Row Level Security enforcement
- **Problem:**
  - Policies created in migration but not tested
  - Easy to forget RLS on new table
  - Cross-tenant access bugs undetected
- **Risk:** HIGH - data isolation is critical
- **Test Case:**
  ```python
  def test_rls_prevents_cross_tenant_access(db, tenant1, tenant2):
      # Create product for tenant1
      # Try to access as tenant2 (should return empty)
      assert db.query(Productos).filter(...).count() == 0
  ```

### 2. Financial Transactions - No Balance Validation

**Issue:** No tests verify accounting equations
- **Problem:**
  - Create sale → create asiento
  - But no test checks: DEBE == HABER
  - Could introduce balance errors
- **Test Case:**
  ```python
  def test_venta_asiento_balanceado(db, sale):
      asiento = create_sale_asiento(sale)
      debe = sum(d.debe for d in asiento.detalles)
      haber = sum(d.haber for d in asiento.detalles)
      assert debe == haber, "Asiento debe estar balanceado"
  ```

### 3. Inventory Consistency - Race Condition Edge Cases

**Issue:** Tests use mocks, don't test actual concurrent DB access
- **Files:** `backend/tests/test_inventario_concurrency.py`
- **Problem:**
  - `with_for_update()` tested but edge case: lock timeout not tested
  - Deadlock between two concurrent operations not tested
  - Stock never goes negative - but what if query returns None?
- **Test Cases Needed:**
  1. Lock acquisition timeout
  2. Circular lock dependency
  3. Stock == 0 edge case

### 4. Authentication - JWT Edge Cases

**Issue:** No tests for token expiration, refresh flow edge cases
- **Problem:**
  - What if refresh token expires during refresh?
  - Multiple simultaneous refresh requests?
  - Token used after logout?
- **Test Scenarios:**
  1. Expired token refresh
  2. Concurrent refresh requests
  3. Use token after logout

---

**Analysis Priority:**

1. **IMMEDIATE (Security):**
   - Unprotected seed endpoint
   - Missing tenant isolation validation
   - Insufficient audit trails

2. **HIGH (Stability):**
   - Multi-step transaction failures
   - Idempotency in conversion flows
   - Test coverage for RLS and accounting

3. **MEDIUM (Performance/Debt):**
   - Large file refactoring
   - Database indexing
   - Error handling standardization

4. **PHASE 2 (Scaling/Features):**
   - Async database driver
   - Webhook infrastructure
   - Email sending
