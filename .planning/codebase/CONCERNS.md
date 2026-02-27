# Codebase Concerns

**Analysis Date:** 2026-02-27

## Unresolved Issues

### Clerk Superadmin Login Failure (CRITICAL)
**Status:** Unresolved — Login with Clerk for `prometeoxlabs@gmail.com` does not complete end-to-end.

**Symptoms:**
- Superadmin account exists in DB and Clerk
- Password verified in DB (`Admin123!`)
- Clerk account created via API with same password
- End-to-end flow NOT tested in production

**Files:**
- `backend/app/rutas/auth.py:clerk_exchange` — token verification
- `frontend/src/pages/ClerkCallbackPage.tsx` — post-auth exchange
- `frontend/src/pages/SelectTenantPage.tsx` — tenant routing
- `backend/app/utils/seguridad.py:verify_clerk_token` — JWT verification

**Specific Unknowns:**
1. Does `POST /auth/clerk-exchange` return `es_superadmin=true` in JWT payload?
2. Does `SelectTenantPage` redirect to `/tenants` for superadmin?
3. Does the complete login flow work in production (Railway)?

**Verification Path:**
1. Open DevTools → attempt login with Clerk using `prometeoxlabs@gmail.com` + `Admin123!`
2. Inspect `POST /auth/clerk-exchange` response in Railway logs
3. Decode returned JWT to verify `es_superadmin=true`
4. Verify redirect to `/tenants` not `/select-tenant`

**Fix Approach:**
- Step through each phase of Clerk login in production
- Log JWT payload at `/auth/clerk-exchange` to debug payload contents
- Add explicit logs to `SelectTenantPage` redirects

---

## Test Failures (Pre-Existing in master)

**Critical:** These 4 tests fail and are NOT related to recent Clerk auth PRs.

### test_admin_can_anular_factura
**Problem:** `NotImplementedError: getitem` in ORM access (line 95 of `test_rbac_backend.py`)

**File:** `backend/tests/test_rbac_backend.py:61-102`

**Cause:** Incorrect ORM model access pattern for `Ventas` model — likely accessing `factura.id` after DB flush instead of before.

**Impact:** Cannot verify that admin can annul invoices. RBAC enforcement for invoice operations untested.

**Fix Approach:**
- Check `Ventas.id` attribute access pattern
- Verify property is defined in `backend/app/datos/modelos.py`
- Test expects `factura.id` to be usable immediately after `db.commit()`

---

### test_superadmin_bypasses_tenant_role_checks
**Problem:** Superadmin bypass logic not implemented in API routes.

**File:** `backend/tests/test_rbac_backend.py:143+`

**Cause:** Routes check `ctx.user.es_superadmin` but implementation may be missing in actual endpoint handlers.

**Impact:** Superadmin may not have intended cross-tenant access. Permission system may incorrectly block superadmin actions.

**Fix Approach:**
- Verify all @router methods check `if current_user.es_superadmin: return authorized` before tenant role checks
- Audit key endpoints: `/api/v1/facturas/{id}/anular`, `/api/v1/productos/{id}`, accounting routes
- Check `backend/app/rutas/*` for explicit superadmin bypass logic

---

### test_rate_limiting
**Problem:** Request format incorrect — returns 422 (validation error) instead of 429 (rate limit).

**File:** Unknown — test not shown but referenced in memory

**Cause:** Test is sending malformed payload OR rate limiter is not properly configured for test scenario.

**Impact:** Rate limiting may not be enforced correctly. Brute force protection unverified.

**Fix Approach:**
- Locate test file and inspect request payload
- Verify `@limiter.limit("5/minute")` decorator on `/api/v1/auth/login` (line 45 of `auth.py`)
- Test with correct payload format

---

### test_tenant_isolation
**Problem:** Cross-tenant access returns 200 (success) instead of 401/403 (forbidden).

**File:** Unknown — test not shown

**Cause:** Row-level security (RLS) not enforcing tenant isolation at DB layer OR endpoint not validating tenant ownership.

**Impact:** CRITICAL — Users may access other tenants' data. Data breach risk.

**Fix Approach:**
- Verify all queries filter by `tenant_id` from context
- Check `backend/app/middleware/tenant_context.py` sets `SET app.tenant_id_actual = ...` before queries
- Add explicit integration test that attempts to access another tenant's data with mismatched token

---

## Tech Debt

### Monolithic Service Files (1600+ LOC)
**Files:**
- `backend/app/servicios/servicio_tenants.py` — 1601 lines
- `backend/app/datos/esquemas.py` — 1647 lines
- `backend/app/rutas/tenants.py` — 1297 lines

**Problem:** Files exceed 500 LOC threshold. High cognitive load, difficult to test in isolation.

**Impact:**
- Risk of duplicate logic across files
- Harder to locate bugs and implement features
- Testing individual functions requires loading entire module

**Safe Refactoring:**
- Extract tenant role management into `servicio_tenants_roles.py`
- Extract tenant billing logic into `servicio_tenants_billing.py`
- Extract validation helpers into `validadores_tenants.py`
- Keep imports simple; use function-level organization

---

### TODO Comments (Incomplete Features)

**1. CORS Configuration Incomplete**
**File:** `backend/app/config.py:113`
```
# TODO: Aterrizar esto a dominios específicos en producción.
```
**Status:** CORS origins hardcoded or permissive. Needs environment-specific configuration.

**Impact:** In production, may allow requests from unintended origins.

**Fix:** Add `CORS_ALLOWED_ORIGINS` env var with comma-separated domains. Validate in `config.py` with `@field_validator`.

---

**2. Authentication Dependency Missing (Stub)**
**File:** `backend/app/main.py:493`
```python
current_user=None,  # TODO: Agregar dependency de autenticación admin
```
**Status:** Admin auth endpoint placeholder — not implemented.

**Impact:** Superadmin onboarding or auth management may be incomplete.

**Fix:** Either implement the dependency or remove the TODO if no longer needed.

---

**3. Relational Future Feature**
**File:** `backend/app/datos/modelos_crm.py:165`
```
# TODO: Relación futura con Cotizaciones del ERP
```
**Status:** CRM module not yet linked to sales quotations.

**Impact:** Low priority — feature incomplete but not blocking.

---

### Float Usage in Financial Reports (PRECISION RISK)
**Files:**
- `backend/app/rutas/cartera.py:100-101` — `float(total_pendiente)`, `float(total_vencido)`
- `backend/app/rutas/cotizaciones.py:54-57` — Multiple `float()` casts
- `backend/app/servicios/servicio_contabilidad.py:355-357` — Account balance floats

**Problem:** Converting Decimal to float loses precision. Financial calculations must use Decimal throughout.

**Impact:** Rounding errors in reports. Users may see incorrect totals. Audit trail mismatch between DB and API.

**Fix Approach:**
- Replace `float(value)` with `str(value)` in JSON serialization (DRF auto-converts Decimal → string)
- OR use Pydantic's `Decimal` field with `json_encoders` config
- Keep all internal calculations as Decimal until final serialization

---

## Security Considerations

### Clerk JWKS Verification Fallback (Edge Case)
**File:** `backend/app/utils/seguridad.py:694-750` (verify_clerk_token)

**Risk:** Development keys (`pk_test_*`, `sk_test_*`) may omit `kid` header in JWT when accessed from non-localhost. Fallback to first key in JWKS set may use wrong signing key.

**Current Mitigation:**
- Fallback logic in place (PR #66)
- Production should use live keys (`pk_live_*`, `sk_live_*`)

**Remaining Risk:** If live keys are not configured in production, fallback is triggered.

**Recommendations:**
- Enforce live keys in production (config validation)
- Add explicit check: if `ENVIRONMENT == 'production'` and keys are `pk_test_*`, raise error at startup
- Add telemetry log when fallback is used

---

### Superadmin Impersonation Not Fully Locked
**File:** `backend/app/utils/seguridad.py:548-563` (get_superadmin)

**Current Control:** Token with `impersonating=true` cannot be used for superadmin routes.

**Gap:** What if attacker crafts JWT without `impersonating` flag? No explicit re-verification against DB that user is actually superadmin.

**Recommendation:**
- Add `require_superadmin_verified` that reads from DB and checks `es_superadmin` field explicitly
- Use for sensitive operations: tenant creation, user role changes, password resets

---

### Debug Mode in Production
**File:** `backend/app/config.py:248-258` (DEBUG validator)

**Current:** `DEBUG=true` in production raises ValueError at startup.

**Risk:** Validation only happens on app startup. If DEBUG accidentally set to true via Railway dashboard after startup, setting won't take effect (FastAPI's startup already passed).

**Recommendation:**
- Add runtime check in health endpoint
- Add middleware to log and alert if DEBUG==true in production
- Consider removing DEBUG mode entirely; use LOG_LEVEL instead

---

## Performance Bottlenecks

### N+1 Query in Tenant Admin Listing
**File:** `backend/app/servicios/servicio_tenants.py`

**Problem:** Getting all tenants with their user count likely iterates users in a loop instead of single JOIN query.

**Impact:** Dashboard `/superadmin/tenants` may be slow with 1000+ tenants.

**Fix Approach:**
- Use SQLAlchemy `joinedload()` or explicit JOIN for user counts
- Cache results if tenant list doesn't change frequently

---

### Maintenance Mode Cache TTL (60s)
**File:** `backend/app/middleware/tenant_context.py:24,37-38`

**Problem:** If a tenant state changes to "mantenimiento", 60 seconds may pass before users get error. Users may experience inconsistent behavior.

**Risk Level:** Low — unlikely to be toggled frequently.

**Better Approach:**
- Invalidate cache immediately when tenant state changes
- Add message queue (e.g., Redis pubsub) to broadcast state changes across processes
- For now, document 60s cache latency in runbooks

---

## Fragile Areas

### Axios Interceptor Header Overwriting
**File:** `frontend/src/api/client.ts`

**Known Fix (PR #67):** Conditional auth header injection
```typescript
if (token && !config.headers['Authorization'])
```

**Remaining Risk:** Other interceptors might override headers later in the chain. No guarantee header won't be modified.

**Safer Pattern:**
- Clone headers object instead of modifying in-place
- Document that Authorization header should never be set manually in endpoint calls
- Add assertion in test that manual Authorization headers are preserved

---

### OnboardingWizard Product Category Enum Mismatch
**Previous Issue (Fixed PR #69):**
- Frontend sent `'TERMINADO'/'MATERIA_PRIMA'` — DB expects `'Producto_Propio'/'Insumo'`
- Fixed by correcting enum values

**Remaining Risk:** If new product categories are added, same mistake could happen again.

**Recommendation:**
- Add shared enum file: `frontend/src/types/productCategories.ts` that imports from backend
- Or fetch available categories from `/api/v1/productos/categorias` endpoint
- Add schema validation test that compares DB enums vs frontend values

---

### Clause Select-Tenant Redirect Loop (Fixed but Monitor)
**Previous Issue (Fixed PR #68):** Loop if tenant list empty and wizard couldn't create tenant.

**Current State:** Fixed — wizard redirects to `/registro/empresa`, which redirects to company creation.

**Monitor:** If user can't complete company creation, they're stuck. Add fallback path:
- If stuck in `/registro/empresa` for >5 min, show "Contact Support" button
- Log company creation failures explicitly

---

## Missing Critical Features

### No API Key Auth for Machine-to-Machine
**Problem:** All authentication is user-based (Clerk + legacy). No API key support for automated integrations.

**Impact:** Third-party integrations must use user credentials (insecure).

**Blocks:**
- Webhook integrations
- Accounting system imports
- Automated reporting

**Fix Approach:**
1. Add `ApiKeys` table with tenant_id, key hash, permissions
2. Create `verify_api_key()` in `seguridad.py`
3. Add `/api/v1/api-keys/` endpoints for CRUD
4. Middleware: allow requests with API key instead of JWT

---

### No Refresh Token Rotation
**File:** `backend/app/utils/seguridad.py:create_refresh_token()`

**Problem:** Refresh tokens don't rotate on use. Old tokens remain valid forever.

**Security Risk:** If refresh token is compromised, attacker can use it indefinitely.

**Fix Approach:**
1. On successful refresh, invalidate old token
2. Store issued tokens in Redis with expiration
3. Check refresh token against blacklist before accepting

---

### Email Verification Not Enforced
**File:** `backend/app/rutas/auth.py`

**Problem:** No indication whether user email has been verified. Users can register with fake emails.

**Impact:** Email-based features (password reset, notifications) won't work for unverified users.

**Fix Approach:**
1. Add `email_verificado` boolean to Usuarios model
2. Send verification email on signup
3. Block unverified users from sensitive operations
4. Clerk integration should automatically mark email as verified

---

## Test Coverage Gaps

### Missing Cross-Tenant Access Test (CRITICAL)
**File:** `backend/tests/test_rbac_backend.py`

**What's Tested:** Role-based access (admin vs vendedor)

**What's Missing:** Tenant isolation — user from Tenant A cannot access Tenant B's data even with valid token.

**Risk:** Could leak customer data between tenants.

**Priority:** HIGH

**Implementation:**
```python
def test_tenant_isolation_enforced(client, tenant_a_token, tenant_b_data, db_session):
    """User from tenant A cannot access tenant B's invoices."""
    response = client.get(
        f"/api/v1/facturas/{tenant_b_invoice.id}",
        headers={
            "Authorization": f"Bearer {tenant_a_token['token']}",
            "X-Tenant-ID": tenant_a_token["tenant_id"]  # Different from invoice's tenant
        }
    )
    assert response.status_code == 403  # Not 200!
```

---

### No Superadmin Cross-Tenant Access Test
**File:** `backend/tests/test_rbac_backend.py`

**Gap:** No test verifying superadmin CAN access other tenants' data with `/superadmin/` routes.

**Implementation:**
```python
def test_superadmin_can_access_any_tenant(client, superadmin_token, tenant_b_data):
    """Superadmin can fetch any tenant's data."""
    response = client.get(
        f"/api/v1/superadmin/tenants/{tenant_b_data.id}/facturas",
        headers={"Authorization": f"Bearer {superadmin_token['token']}"}
    )
    assert response.status_code == 200
```

---

### No Rate Limit Test with Correct Payload
**Gap:** Rate limiting test may be using malformed request (returns 422 instead of 429).

**Implementation:**
```python
def test_login_rate_limit(client):
    """5 correct login attempts per minute — 6th returns 429."""
    for i in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "wrong"}
        )
        assert response.status_code in [401, 200]  # Valid request

    # 6th attempt should be rate limited
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong"}
    )
    assert response.status_code == 429
```

---

### Concurrency Tests (Inventory)
**File:** `backend/tests/test_inventario_concurrency.py`

**Status:** File exists but content unknown. Verify it covers:
- Multiple users adjusting inventory simultaneously
- Race conditions in quantity calculations
- Lock mechanisms working correctly

---

## Dependencies at Risk

### Clerk Keys Version Mismatch
**Risk:** Development keys (`sk_test_*`) used in staging/production.

**Impact:** JWTs may behave differently (missing `kid`, different issuer). User login may fail unpredictably.

**Current State:** Config has CLERK_SECRET_KEY env var. Production Railway should have live key.

**Recommendation:**
- Add startup validation: if `ENVIRONMENT==production` and `CLERK_SECRET_KEY.startswith('sk_test')`, raise error
- Document key rotation procedure

---

### PyJWT and PyJWKClient Versions
**Deps:** `pyjwt`, `jwt.PyJWKClient` from jose

**Risk:** Dual JWT libraries in use (`pyjwt` for custom tokens, `jose` for Clerk). Different validation behaviors.

**Current:** `jose` used for custom token creation, `pyjwt` used for Clerk validation.

**Recommendation:**
- Consolidate to single JWT library (prefer `pyjwt`)
- Document why split is needed if not possible

---

## Scaling Limits

### Tenant/User Relationship Table Unbounded
**File:** `backend/app/datos/modelos.py` (UsuariosTenants)

**Problem:** No limit on users per tenant or tenants per user.

**Capacity:** At 1000 users × 1000 tenants, junction table = 1M rows. Queries may slow down.

**Recommendation:**
- Add partial index: `CREATE INDEX idx_usuarios_tenants_user ON usuarios_tenants(usuario_id) WHERE estado='activo'`
- Consider pagination for "list all tenants" queries
- Monitor query performance as data grows

---

### Session Context Variables (ContextVar)
**File:** `backend/app/middleware/tenant_context.py:65`

**Problem:** One ContextVar per request. In high concurrency (1000+ concurrent requests), Python's ContextVar overhead becomes measurable.

**Current Impact:** Low — acceptable for typical SaaS workload.

**Future Risk:** If load exceeds 10k concurrent requests, consider moving to request scope.

---

## Deployment/Runtime Issues

### Database Migration Requirement
**Action Required:** After deploy, must run `alembic upgrade head` manually on Railway.

**Risk:** If migration fails, users are blocked. No rollback procedure documented.

**Recommendation:**
- Add automatic migration in app startup if `ENVIRONMENT==production` (with backup)
- Or add health check that warns if schema version mismatch detected
- Document rollback steps in RUNBOOK.md

---

### Seed Data in Production
**File:** `backend/app/main.py` (/api/v1/admin/seed endpoint)

**Risk:** Endpoint exposed without auth guard. Anyone can call it and populate fake data.

**Current:** Likely only accessible locally, but not documented.

**Fix:**
- Require superadmin auth on /admin/seed
- Disable endpoint in production entirely (only enable in development via env var)

---

## Recommendations (Priority Order)

| Issue | Priority | Effort | Impact |
|-------|----------|--------|--------|
| Verify Clerk superadmin login end-to-end | CRITICAL | 2h | Blocks superadmin usage |
| Fix test_tenant_isolation (add cross-tenant check) | CRITICAL | 4h | Security hole |
| Enforce live Clerk keys in production | HIGH | 1h | Prevents dev key fallback bugs |
| Implement API key auth for integrations | HIGH | 8h | Enables webhooks, imports |
| Refactor servicio_tenants.py (1600+ LOC) | MEDIUM | 16h | Code maintainability |
| Add refresh token rotation | MEDIUM | 6h | Token compromise mitigation |
| Implement email verification | MEDIUM | 4h | Email feature reliability |
| Add rate limit & tenant isolation tests | MEDIUM | 6h | Test coverage |
| Move CORS config to env vars | MEDIUM | 2h | Production security |
| Consolidate JWT libraries (jose vs pyjwt) | LOW | 4h | Technical debt |

---

*Concerns audit: 2026-02-27*
