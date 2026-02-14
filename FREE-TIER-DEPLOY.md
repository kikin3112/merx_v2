# 🚀 Chandelier ERP - Deploy Gratuito en 5 Minutos

> **Costo: $0/mes** | Railway ($5 crédito) + Vercel (free tier)

## ✨ Opción 1: Deploy Automático (Recomendado)

### Windows (PowerShell)

```powershell
# Ejecutar desde la raíz del proyecto
.\deploy-free-tier.ps1
```

### Linux/Mac (Bash)

```bash
# Dar permisos de ejecución
chmod +x deploy-free-tier.sh

# Ejecutar
./deploy-free-tier.sh
```

El script automatiza:
- ✅ Instalación de CLIs (Railway + Vercel)
- ✅ Login en ambas plataformas
- ✅ Deploy del backend (FastAPI + PostgreSQL)
- ✅ Ejecución de migraciones Alembic
- ✅ Deploy del frontend (React + Vite)
- ✅ Configuración de variables de entorno
- ✅ Configuración de CORS
- ✅ Verificación de health checks

**Tiempo total: ~5 minutos** ⏱️

---

## 📋 Opción 2: Deploy Manual

### Paso 1: Backend en Railway (2 minutos)

```bash
# Instalar CLI
npm i -g @railway/cli

# Login (abre navegador)
railway login

# Inicializar proyecto
railway init

# Agregar PostgreSQL
railway add postgresql

# Configurar variables de entorno
railway variables set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
railway variables set ENVIRONMENT=production
railway variables set DEBUG=False

# Deploy
railway up

# Ejecutar migraciones
railway run alembic upgrade head

# (Opcional) Ejecutar seeders
railway run python -c "from backend.app.utils.seeders import run_all_seeders; run_all_seeders()"

# Obtener URL del backend
railway status
```

### Paso 2: Frontend en Vercel (2 minutos)

```bash
# Instalar CLI
npm i -g vercel

# Login
vercel login

# Deploy desde carpeta frontend
cd frontend
vercel --prod

# Configurar variable de entorno
# (Reemplazar <RAILWAY_URL> con la URL del paso anterior)
vercel env add VITE_API_URL production
# Pegar: <RAILWAY_URL>/api/v1

# Redeploy para aplicar variable
vercel --prod

# Obtener URL del frontend
vercel inspect --prod
```

### Paso 3: Actualizar CORS (1 minuto)

```bash
# Configurar CORS en backend (reemplazar <VERCEL_URL>)
railway variables set CORS_ORIGINS="<VERCEL_URL>"

# Reiniciar backend
railway restart
```

---

## 🎯 ¿Qué obtienes?

### ✅ Stack Completo

```
┌─────────────────────────────────────────┐
│  [Usuarios]                             │
│      ↓                                  │
│  [Vercel CDN] ← Frontend React          │
│      ↓                                  │
│  [Railway] ← Backend FastAPI            │
│      ├─ PostgreSQL 16 (1GB)            │
│      ├─ Auto-deploy desde Git          │
│      └─ SSL/HTTPS incluido              │
└─────────────────────────────────────────┘

Costo: $0/mes
```

### 📊 Capacidades

- **Usuarios concurrentes:** 10-50
- **Facturas/mes:** Ilimitadas
- **Almacenamiento DB:** 1GB (~5,000 facturas)
- **Bandwidth:** 100GB/mes (Vercel)
- **Uptime:** 99% (Railway no-sleep)
- **SSL:** Incluido
- **Custom domain:** Disponible (gratis)

### 🔒 Features Incluidos

- ✅ Multi-tenancy con RLS
- ✅ Autenticación JWT
- ✅ RBAC (roles: admin, vendedor, contador, operador)
- ✅ Facturación con PDF
- ✅ Inventario con valorización promedio
- ✅ Recetas (BOM)
- ✅ Cotizaciones
- ✅ Contabilidad automática (PUC Colombia)
- ✅ Dashboard con KPIs
- ✅ POS mobile-first
- ✅ Reportes avanzados

---

## 🧪 Verificación Post-Deploy

### 1. Health Check Backend

```bash
# Reemplazar <RAILWAY_URL> con tu URL
curl <RAILWAY_URL>/health

# Respuesta esperada:
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

### 2. Acceder al Frontend

```
https://<tu-app>.vercel.app
```

**Credenciales de prueba:**

| Usuario | Email | Password |
|---------|-------|----------|
| Superadmin | superadmin@chandelier.com | superadmin123 |
| Admin | admin@velasaromaticas.com | admin123 |
| Operador | operador@velasaromaticas.com | operador123 |

### 3. Crear Primer Tenant

```
1. Login como superadmin
2. Ir a /tenants
3. Click "Nuevo Tenant"
4. Llenar datos empresa
5. Crear usuario admin del tenant
6. Logout y login con nuevo admin
```

---

## 📈 Monitoreo

### Railway Dashboard

```
https://railway.app/dashboard
```

**Métricas disponibles:**
- CPU usage
- RAM usage
- Request count
- Database size
- Logs en tiempo real

### Vercel Analytics

```
https://vercel.com/dashboard
```

**Métricas disponibles:**
- Pageviews
- Bandwidth usage
- Deployment history
- Performance metrics

### CLI Commands

```bash
# Ver logs backend en tiempo real
railway logs -f

# Ver estado del proyecto
railway status

# Ver variables de entorno
railway variables

# Ejecutar comando en Railway
railway run <comando>

# Redeploy backend
railway up

# Redeploy frontend
cd frontend && vercel --prod
```

---

## ⚠️ Limitaciones Free Tier

### Railway

- ✅ $5 crédito/mes (suficiente para backend + DB pequeño)
- ⚠️ Crédito NO acumulable (se resetea cada mes)
- ⚠️ 512MB RAM (reduce a 2 workers uvicorn si es necesario)
- ⚠️ 1GB almacenamiento DB

**Cuándo actualizar:** Railway crédito se agota antes de fin de mes

### Vercel

- ✅ 100GB bandwidth/mes
- ✅ Unlimited deployments (hobby)
- ⚠️ No custom domains en free tier (usa subdomain.vercel.app)

**Cuándo actualizar:** >100GB bandwidth o necesitas custom domain

---

## 🔧 Troubleshooting

### "Railway crédito agotado"

```bash
# Ver uso actual
railway status

# Solución 1: Reducir workers
# Editar Dockerfile.backend:
CMD ["uvicorn", "backend.app.main:app", "--workers", "2"]  # En vez de 4

# Redeploy
railway up

# Solución 2: Upgrade a Developer ($5/mes por servicio)
```

### "CORS Error" en producción

```bash
# Verificar CORS_ORIGINS incluye frontend
railway variables

# Si falta, agregar:
railway variables set CORS_ORIGINS="https://tu-frontend.vercel.app"
railway restart
```

### "Database connection failed"

```bash
# Ver logs
railway logs

# Verificar DATABASE_URL existe
railway variables | grep DATABASE_URL

# Re-ejecutar migraciones
railway run alembic upgrade head
```

### Frontend no carga datos

```bash
# Verificar variable VITE_API_URL en Vercel dashboard
# Debe ser: https://<railway-url>/api/v1 (con /api/v1)

# Si está mal, actualizar:
cd frontend
vercel env rm VITE_API_URL production
vercel env add VITE_API_URL production
# Pegar: https://<railway-url>/api/v1

# Redeploy
vercel --prod
```

---

## 💡 Tips de Optimización

### Reducir uso de RAM (Railway)

```python
# Editar Dockerfile.backend
CMD ["uvicorn", "backend.app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "$PORT", \
     "--workers", "2"]  # Reducir de 4 a 2
```

### Caché frontend agresivo

```typescript
// frontend/vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@headlessui/react', '@heroicons/react']
        }
      }
    }
  }
})
```

### Lazy loading de rutas

```typescript
// frontend/src/App.tsx
import { lazy, Suspense } from 'react';

const ProductosPage = lazy(() => import('./pages/ProductosPage'));
const FacturasPage = lazy(() => import('./pages/FacturasPage'));

// En routes:
<Route path="/productos" element={
  <Suspense fallback={<div>Loading...</div>}>
    <ProductosPage />
  </Suspense>
} />
```

---

## 📊 Ruta de Escalamiento

```
Mes 0-2: Validación (FREE TIER)
├─ Railway $5 crédito + Vercel free
├─ 10-50 usuarios
└─ Costo: $0/mes

         ↓ (Usuarios crecen)

Mes 3-6: MVP Productivo (VPS)
├─ Hostinger VPS KVM 2 + Dockploy
├─ 50-200 usuarios
└─ Costo: $15/mes

         ↓ (Necesitas auto-scaling)

Mes 7+: Crecimiento (Managed)
├─ Railway Pro o Render Starter
├─ 200-1000 usuarios
└─ Costo: $40-90/mes
```

**Recomendación:** Empieza en free tier, migra a VPS cuando tengas >20 usuarios activos diarios.

---

## 🆘 Soporte

### Recursos

- **Documentación completa:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Guía técnica:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Railway Docs:** https://docs.railway.app
- **Vercel Docs:** https://vercel.com/docs

### Comandos Útiles

```bash
# Railway
railway logs -f           # Ver logs en tiempo real
railway status            # Ver métricas
railway restart           # Reiniciar servicio
railway variables         # Ver env vars
railway run <cmd>         # Ejecutar comando

# Vercel
vercel --prod             # Redeploy
vercel logs               # Ver logs
vercel env ls             # Ver variables
vercel inspect --prod     # Ver detalles deployment
```

---

## ✅ Checklist Post-Deploy

- [ ] Backend health check responde 200 OK
- [ ] Frontend carga correctamente
- [ ] Login funciona con credenciales de prueba
- [ ] Crear tenant de prueba exitoso
- [ ] Crear producto funciona
- [ ] Crear factura genera PDF
- [ ] CORS configurado correctamente
- [ ] Variables de entorno verificadas
- [ ] UptimeRobot configurado (opcional)
- [ ] GitHub Actions habilitado (opcional)

---

## 🎉 ¡Listo!

Sistema ERP/POS completo deployado **gratis** en 5 minutos.

**Próximos pasos:**

1. Invitar usuarios a probar
2. Crear tenants reales
3. Configurar custom domain (opcional)
4. Agregar Sentry para error tracking
5. Migrar a VPS cuando tengas tracción

**¡Éxito con tu emprendimiento!** 🚀
