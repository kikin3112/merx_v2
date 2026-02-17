# Codebase Analysis: Concerns & Issues

**Analysis Date:** 2026-02-17  
**Codebase:** MERX/Chandelier ERP-POS SaaS

---

## 1. Technical Debt

### 1.1 TODO/FIXME Comments

| Location | Line | Issue | Severity |
|----------|------|-------|----------|
| `backend/app/main.py` | 518 | `# TODO: Agregar dependency de autenticación admin` - Seed endpoint has no auth | **HIGH** |
| `backend/app/main.py` | 526 | `# TODO: Descomentar cuando el sistema de auth esté completo` - Auth check commented out | **HIGH** |
| `backend/app/datos/modelos_crm.py` | 149 | `# TODO: Relación futura con Cotizaciones del ERP` - Incomplete CRM integration | **LOW** |

### 1.2 Incomplete Implementations

**Unprotected Admin Seed Endpoint:**
```python
# backend/app/main.py:516-531
@app.post(f"{prefix}/admin/seed", tags=["Administración"])
def ejecutar_seeds(
        current_user=None  # TODO: Agregar dependency de autenticación admin
):
    # TODO: Descomentar cuando el sistema de auth esté completo
    # if current_user.rol != "admin":
    #     raise HTTPException(...)
```
**Risk:** Anyone can execute database seeds without authentication.

### 1.3 Debug Mode Exposure

```python
# backend/app/main.py:356-364
if settings.DEBUG:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor",
            "error": str(exc),
            "type": type(exc).__name__
        }
    )
```
**Risk:** Stack traces and error details exposed in DEBUG mode.

---

## 2. Security Concerns

### 2.1 Authentication/Authorization Gaps

**CRITICAL: Unprotected Seed Endpoint**
- Path: `POST /api/v1/admin/seed`
- Impact: Anyone can reset/seed the database
- Fix: Implement `Depends(get_current_active_admin)` or remove in production

**Maintenance Mode Race Condition:**
```python
# backend/app/middleware/tenant_context.py:23-24
_MAINTENANCE_CACHE: dict = {}
_MAINTENANCE_CACHE_TTL = 60.0  # seconds
```
- Cache TTL of 60 seconds means writes could be allowed for up to 1 minute after maintenance mode is enabled
- Consider: Reduce TTL or implement immediate invalidation via Redis

### 2.2 Secrets Management

**Development Secret Key Fallback:**
```python
# backend/app/config.py:291-292
if not data.get("SECRET_KEY") and environment == "development":
    data["SECRET_KEY"] = "dev_secret_key_for_development_only_min_32_chars"
```
- Acceptable for development but ensure this cannot be triggered in production
- Current validator blocks production with missing SECRET_KEY

**Frontend Token Storage:**
```typescript
// frontend/src/stores/authStore.ts:142-152
persist(
    ...
    {
      name: 'chandelier-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        ...
      }),
    }
)
```
- Tokens stored in localStorage via Zustand persist
- **Risk:** Vulnerable to XSS attacks
- **Recommendation:** Consider httpOnly cookies for refresh tokens

### 2.3 Input Validation

**Missing validation on some endpoints:**
- Multiple endpoints accept string parameters without length validation
- Email validation relies on Pydantic's built-in validation (acceptable)

### 2.4 SQL Injection Assessment

**STATUS: LOW RISK**

All SQL operations use SQLAlchemy ORM or parameterized queries:
```python
# Parameterized (safe)
db.execute(text("SET LOCAL app.tenant_id_actual = :tenant_id"), {"tenant_id": str(tenant_id)})

# ORM (safe)
db.query(Productos).filter(Productos.tenant_id == tenant_id).all()
```

No raw string concatenation with user input found in SQL queries.

---

## 3. Performance Concerns

### 3.1 N+1 Query Risks

**Ventas Listing Without Details:**
```python
# backend/app/servicios/servicio_ventas.py:113-116
query = db.query(Ventas).options(
    selectinload(Ventas.created_by_user),
    selectinload(Ventas.updated_by_user)
).filter(Ventas.tenant_id == tenant_id)
```
- `selectinload` used for user relationships but NOT for `Ventas.detalles`
- If response serialization accesses `venta.detalles`, this causes N+1 queries
- **Fix:** Add `selectinload(Ventas.detalles)` if details are included in response

**Recetas Without Ingredient Products:**
```python
# backend/app/rutas/recetas.py:159-161
selectinload(Recetas.created_by_user),
selectinload(Recetas.updated_by_user)
```
- Missing `selectinload(Recetas.ingredientes)` and nested product loads

### 3.2 Database Query Patterns

**Loop-Based Inventory Updates:**
```python
# backend/app/servicios/servicio_ventas.py:229-238
for detalle in venta.detalles:
    producto = db.query(Productos).filter(Productos.id == detalle.producto_id).first()
    if producto and producto.maneja_inventario:
        servicio_inv.crear_movimiento(...)
```
- Each iteration queries the product
- **Fix:** Batch query all products upfront, then iterate

### 3.3 Pagination Limits

**Default limit of 100 with max of 1000:**
```python
# backend/app/rutas/productos.py:77
limit: int = Query(100, ge=1, le=1000)
```
- Acceptable for MVP
- Consider cursor-based pagination for large datasets

### 3.4 Concurrency Handling

**Positive: Row-Level Locking Implemented:**
```python
# backend/app/servicios/servicio_inventario.py:57
query = query.with_for_update()

# backend/app/servicio_inventario.py:332-344
ingredient_ids = sorted([ing.producto_id for ing in receta.ingredientes])
self.db.query(Inventarios).filter(
    Inventarios.tenant_id == self.tenant_id,
    Inventarios.producto_id.in_(ingredient_ids)
).with_for_update().all()
```
- Proper deadlock prevention by ordering lock acquisition
- Stock operations protected against race conditions

---

## 4. Maintainability Issues

### 4.1 Code Duplication

**Repeated pattern across routes (ventas, compras, cotizaciones):**
```python
# Similar structure in all three files:
@router.get("/", response_model=List[...])
async def listar_...(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ...
):
    query = db.query(...).options(
        selectinload(...),
        selectinload(...)
    ).filter(...tenant_id == tenant_id)
```
- Consider: Generic base service class with tenant filtering

**Duplicate total calculation logic:**
- `Ventas.subtotal`, `Compras.subtotal`, `Cotizaciones.subtotal` all have identical hybrid_property implementations
- Consider: Mixin class for document totals

### 4.2 Error Handling Inconsistency

**Mixed patterns:**
```python
# Pattern 1: Generic catch-all
except Exception as e:
    db.rollback()
    logger.error("Error...", exc_info=e)
    raise HTTPException(status_code=500, detail="Error interno...")

# Pattern 2: Specific + re-raise
except HTTPException:
    raise
except Exception as e:
    ...
```
- Pattern 2 is better but not consistently applied

### 4.3 Missing Documentation

**Files without module-level docstrings:**
- `backend/app/rutas/health.py`
- `backend/app/rutas/medios_pago.py`
- `backend/app/middleware/__init__.py`

**Complex functions without docstrings:**
- Several service functions in `servicio_inventario.py`
- Utility functions in `secuencia_helper.py`

### 4.4 Type Annotations

**Partial coverage:**
- Most functions have return type hints
- Some internal helper functions missing annotations
- Frontend TypeScript is well-typed

---

## 5. Dependencies Analysis

### 5.1 Backend (requirements.txt)

| Package | Version | Status | Notes |
|---------|---------|--------|-------|
| fastapi | >=0.115.0 | Current | Good |
| sqlalchemy | >=2.0.0 | Current | Good |
| pydantic | >=2.0.0 | Current | Good |
| python-jose | >=3.3.0 | Stable | Auth |
| passlib | >=1.7.4 | Stable | Password hashing |

**No deprecated packages detected.**

### 5.2 Frontend (package.json)

| Package | Version | Status |
|---------|---------|--------|
| react | ^19.2.0 | Current |
| react-router-dom | ^7.13.0 | Current |
| axios | ^1.13.5 | Current |
| zustand | ^5.0.11 | Current |
| tailwindcss | ^4.1.18 | Current |

**No deprecated packages detected.**

---

## 6. Priority Fixes

### Immediate (Security)
1. **Protect admin seed endpoint** - Add authentication dependency
2. **Review DEBUG mode exposu
re** - Ensure production cannot enable DEBUG

### Short-term (Performance)
3. **Add eager loading for ventas.detalles** - Prevent N+1 queries
4. **Batch product queries in confirmar_venta** - Reduce DB roundtrips

### Medium-term (Maintainability)
5. **Create base document service** - Reduce duplication
6. **Standardize error handling pattern** - Consistent across all routes

### Low Priority
7. **Add missing docstrings** - Improve code documentation
8. **Consider httpOnly cookies for refresh tokens** - Enhance frontend security

---

## 7. Positive Observations

- **RLS implementation is solid** - PostgreSQL Row Level Security properly configured
- **Row-level locking for inventory** - Race conditions handled correctly
- **Parameterized queries** - No SQL injection vectors found
- **Rate limiting implemented** - Login and password change endpoints protected
- **Audit logging** - Comprehensive audit trail for sensitive operations
- **Modern stack** - Current versions of all major dependencies
- **Type safety** - Pydantic v2 for backend, TypeScript for frontend
