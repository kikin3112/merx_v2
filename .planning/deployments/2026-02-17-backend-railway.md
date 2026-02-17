---
phase: backend
environment: production
platform: railway
status: success
deployed_at: 2026-02-17T10:11:00Z
updated_at: 2026-02-17T10:41:00Z
url: https://backend-production-14545.up.railway.app
---

# Backend Deployment Log

## Summary

Backend desplegado exitosamente en Railway después de resolver problemas de health check y CORS.

## Issues Resolved

### 1. TrustedHostMiddleware Blocking Health Checks

**Problem:** `TrustedHostMiddleware` rechazaba peticiones de health check porque Railway usa hostnames dinámicos internos (`healthcheck.railway.app`).

**Solution:** Deshabilitado temporalmente. Reactivar cuando se configure dominio propio.

**Files Changed:**
- `backend/app/main.py` - Comentado TrustedHostMiddleware
- `backend/app/config.py` - Agregado ALLOWED_HOSTS setting (para futuro)

### 2. Health Path Exclusions

**Problem:** Middleware de tenant y usuario no excluían todos los paths de health check.

**Solution:** Agregados `/health/ready` y `/health/startup` a exclusiones.

**Files Changed:**
- `backend/app/middleware/tenant_context.py`
- `backend/app/middleware/user_context.py`

### 3. CORS Preflight (OPTIONS) Blocked

**Problem:** El middleware de tenant bloqueaba peticiones OPTIONS (CORS preflight) porque no tenían header `X-Tenant-ID`.

**Solution:** Agregar verificación `if request.method == "OPTIONS": return await call_next(request)` al inicio del dispatch.

**Files Changed:**
- `backend/app/middleware/tenant_context.py`

### 4. CORS Origin Not Allowed

**Problem:** `CORS_ORIGINS` solo permitía `merx-v2.vercel.app`, pero el frontend está en `frontend-eta-seven-0k6okqj6xf.vercel.app`.

**Solution:** Actualizado `CORS_ORIGINS` para incluir ambos dominios.

**Railway Variable:**
```
CORS_ORIGINS=https://frontend-eta-seven-0k6okqj6xf.vercel.app,https://merx-v2.vercel.app
```

## Verification

```bash
# Health check
curl https://backend-production-14545.up.railway.app/health
# {"status":"healthy","environment":"production","version":"1.0.0"}

# CORS preflight
curl -X OPTIONS https://backend-production-14545.up.railway.app/api/v1/auth/login \
  -H "Origin: https://frontend-eta-seven-0k6okqj6xf.vercel.app"
# HTTP/2 200 OK

# Login
curl -X POST https://backend-production-14545.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
# {"access_token":"...", "user": {...}, "tenants": [...]}
```

## Configuration

| Variable | Value |
|----------|-------|
| ENVIRONMENT | production |
| DATABASE_URL | postgresql://postgres:***@postgres.railway.internal:5432/railway |
| CORS_ORIGINS | https://frontend-eta-seven-0k6okqj6xf.vercel.app,https://merx-v2.vercel.app |
| SECRET_KEY | [configured] |

## Test Credentials

| Usuario | Email | Password |
|---------|-------|----------|
| Superadmin | superadmin@chandelier.com | superadmin123 |
| Admin | admin@example.com | admin123 |
| Operador | operador@velasaromaticas.com | operador123 |

## Railway CLI Commands Used

```bash
railway status          # Ver estado
railway variables       # Ver variables
railway variables set   # Actualizar variable
railway logs           # Ver logs
railway up -d          # Deploy forzado
```

## Next Steps

- [x] Desplegar frontend en Vercel
- [x] Verificar conexión frontend → backend
- [x] Login funciona
- [ ] Configurar dominio personalizado
- [ ] Reactivar TrustedHostMiddleware con dominio
