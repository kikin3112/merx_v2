# ========================================================================
# Chandelier ERP/POS - Free Tier Deployment Script (Windows PowerShell)
# ========================================================================
# Este script automatiza el deployment en Railway (backend) + Vercel (frontend)
# Costo: $0/mes (Railway $5 crédito + Vercel free tier)
#
# Requisitos:
# - Node.js 20+
# - Git configurado
# - Cuenta GitHub
# - PowerShell 5.1+ (incluido en Windows 10/11)
# ========================================================================

$ErrorActionPreference = "Stop"

# Colores
function Write-Step {
    param($Message)
    Write-Host "`n==> " -NoNewline -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Green
    Write-Host ""
}

function Write-Success {
    param($Message)
    Write-Host "✓ " -NoNewline -ForegroundColor Green
    Write-Host $Message
}

function Write-Error-Custom {
    param($Message)
    Write-Host "ERROR: " -NoNewline -ForegroundColor Red
    Write-Host $Message
}

function Write-Warning-Custom {
    param($Message)
    Write-Host "WARNING: " -NoNewline -ForegroundColor Yellow
    Write-Host $Message
}

# Banner
Write-Host @"

   _____ _                     _      _ _
  / ____| |                   | |    | (_)
 | |    | |__   __ _ _ __   __| | ___| |_  ___ _ __
 | |    | '_ \ / _\` | '_ \ / _\` |/ _ \ | |/ _ \ '__|
 | |____| | | | (_| | | | | (_| |  __/ | |  __/ |
  \_____|_| |_|\__,_|_| |_|\__,_|\___|_|_|\___|_|

         FREE TIER DEPLOYMENT SCRIPT
         Costo: `$0/mes | Deploy: 5 minutos

"@ -ForegroundColor Blue

# ========================================================================
# PASO 1: Verificar Requisitos
# ========================================================================
Write-Step "1/6 Verificando requisitos..."

# Verificar Node.js
try {
    $nodeVersion = node --version
    Write-Success "Node.js $nodeVersion instalado"
} catch {
    Write-Error-Custom "Node.js no instalado. Instalar desde: https://nodejs.org"
    exit 1
}

# Verificar Git
try {
    $gitVersion = git --version
    Write-Success "Git instalado"
} catch {
    Write-Error-Custom "Git no instalado. Instalar desde: https://git-scm.com"
    exit 1
}

# Verificar que estamos en el directorio correcto
if (!(Test-Path "backend\app\main.py")) {
    Write-Error-Custom "Ejecutar este script desde la raíz del proyecto (merx_v2\)"
    exit 1
}
Write-Success "Directorio correcto detectado"

# ========================================================================
# PASO 2: Instalar CLIs
# ========================================================================
Write-Step "2/6 Instalando CLIs de Railway y Vercel..."

# Railway CLI
try {
    railway --version | Out-Null
    Write-Success "Railway CLI ya instalado"
} catch {
    Write-Host "Instalando Railway CLI..."
    npm install -g @railway/cli
    Write-Success "Railway CLI instalado"
}

# Vercel CLI
try {
    vercel --version | Out-Null
    Write-Success "Vercel CLI ya instalado"
} catch {
    Write-Host "Instalando Vercel CLI..."
    npm install -g vercel
    Write-Success "Vercel CLI instalado"
}

# ========================================================================
# PASO 3: Deploy Backend en Railway
# ========================================================================
Write-Step "3/6 Deploying Backend en Railway..."

Write-Host "Abriendo navegador para login en Railway..." -ForegroundColor Yellow
railway login

Write-Host "Inicializando proyecto Railway..." -ForegroundColor Yellow
railway init

Write-Host "Provisionando PostgreSQL..." -ForegroundColor Yellow
railway add postgresql

Write-Host "Configurando variables de entorno..." -ForegroundColor Yellow

# Generar SECRET_KEY
$SECRET_KEY = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Configurar variables de entorno
railway variables set SECRET_KEY=$SECRET_KEY
railway variables set ENVIRONMENT=production
railway variables set DEBUG=False
railway variables set ALGORITHM=HS256
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES=30

Write-Success "Variables de entorno configuradas"

Write-Host "Deploying backend (puede tardar 2-3 minutos)..." -ForegroundColor Yellow
railway up

# Ejecutar migraciones
Write-Host "Ejecutando migraciones Alembic..." -ForegroundColor Yellow
railway run alembic upgrade head

# Obtener URL del backend
$railwayStatus = railway status --json | ConvertFrom-Json
$BACKEND_URL = $railwayStatus.deployments[0].url
Write-Success "Backend deployed en: $BACKEND_URL"

# Ejecutar seeders (opcional)
$response = Read-Host "¿Ejecutar seeders de datos iniciales? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    railway run python -c "from backend.app.utils.seeders import run_all_seeders; run_all_seeders()"
    Write-Success "Seeders ejecutados"
}

# ========================================================================
# PASO 4: Deploy Frontend en Vercel
# ========================================================================
Write-Step "4/6 Deploying Frontend en Vercel..."

Set-Location frontend

Write-Host "Login en Vercel..." -ForegroundColor Yellow
vercel login

Write-Host "Deploying frontend (primera vez puede tardar 3-4 min)..." -ForegroundColor Yellow
vercel --prod --yes

# Configurar variable de entorno
Write-Host "Configurando VITE_API_URL..." -ForegroundColor Yellow
$apiUrl = "$BACKEND_URL/api/v1"
Write-Output $apiUrl | vercel env add VITE_API_URL production

# Redeploy para aplicar variable
Write-Host "Redeploying para aplicar variables..." -ForegroundColor Yellow
vercel --prod --yes

$vercelInspect = vercel inspect --prod --json | ConvertFrom-Json
$FRONTEND_URL = $vercelInspect.url

Set-Location ..

Write-Success "Frontend deployed en: https://$FRONTEND_URL"

# ========================================================================
# PASO 5: Actualizar CORS en Backend
# ========================================================================
Write-Step "5/6 Actualizando CORS en Backend..."

railway variables set CORS_ORIGINS="https://$FRONTEND_URL"
railway restart

Write-Success "CORS actualizado y backend reiniciado"

# ========================================================================
# PASO 6: Verificación
# ========================================================================
Write-Step "6/6 Verificando deployment..."

Write-Host "Verificando health check del backend..."
try {
    $healthCheck = Invoke-RestMethod -Uri "$BACKEND_URL/health"
    if ($healthCheck.status -eq "healthy") {
        Write-Success "Backend health check OK"
    }
} catch {
    Write-Error-Custom "Backend health check falló. Ver logs: railway logs"
}

Write-Host "Verificando frontend..."
try {
    $frontendResponse = Invoke-WebRequest -Uri "https://$FRONTEND_URL" -UseBasicParsing
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Success "Frontend accesible"
    }
} catch {
    Write-Error-Custom "Frontend no accesible. Ver logs en Vercel dashboard"
}

# ========================================================================
# RESUMEN
# ========================================================================
Write-Host "`n========================================================================"
Write-Host "✓ DEPLOYMENT COMPLETADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "========================================================================`n"

Write-Host "URLs:" -ForegroundColor Blue
Write-Host "  Frontend: " -NoNewline
Write-Host "https://$FRONTEND_URL" -ForegroundColor Green
Write-Host "  Backend:  " -NoNewline
Write-Host "$BACKEND_URL" -ForegroundColor Green
Write-Host "  API Docs: " -NoNewline
Write-Host "$BACKEND_URL/api/v1/docs (solo en dev)`n" -ForegroundColor Green

Write-Host "Credenciales de prueba:" -ForegroundColor Blue
Write-Host "  Superadmin: " -NoNewline
Write-Host "superadmin@chandelier.com" -NoNewline -ForegroundColor Yellow
Write-Host " / " -NoNewline
Write-Host "superadmin123" -ForegroundColor Yellow
Write-Host "  Admin:      " -NoNewline
Write-Host "admin@velasaromaticas.com" -NoNewline -ForegroundColor Yellow
Write-Host " / " -NoNewline
Write-Host "admin123" -ForegroundColor Yellow
Write-Host "  Operador:   " -NoNewline
Write-Host "operador@velasaromaticas.com" -NoNewline -ForegroundColor Yellow
Write-Host " / " -NoNewline
Write-Host "operador123`n" -ForegroundColor Yellow

Write-Host "Monitoreo:" -ForegroundColor Blue
Write-Host "  Railway Dashboard:  " -NoNewline
Write-Host "https://railway.app/dashboard" -ForegroundColor Green
Write-Host "  Vercel Dashboard:   " -NoNewline
Write-Host "https://vercel.com/dashboard" -ForegroundColor Green
Write-Host "  Logs Backend:       " -NoNewline
Write-Host "railway logs -f" -ForegroundColor Green
Write-Host "  Métricas Railway:   " -NoNewline
Write-Host "railway status`n" -ForegroundColor Green

Write-Host "Costo mensual:" -ForegroundColor Blue
Write-Host "  Backend (Railway):  " -NoNewline
Write-Host "`$0" -NoNewline -ForegroundColor Green
Write-Host " (`$5 crédito/mes incluido)"
Write-Host "  Frontend (Vercel):  " -NoNewline
Write-Host "`$0" -NoNewline -ForegroundColor Green
Write-Host " (free tier 100GB bandwidth)"
Write-Host "  Database:           " -NoNewline
Write-Host "`$0" -NoNewline -ForegroundColor Green
Write-Host " (1GB PostgreSQL incluido)"
Write-Host "  " -NoNewline
Write-Host "TOTAL: `$0/mes`n" -ForegroundColor Green

Write-Host "Siguientes pasos:" -ForegroundColor Yellow
Write-Host "  1. Configurar UptimeRobot (https://uptimerobot.com) para monitoreo"
Write-Host "  2. Agregar custom domain en Vercel (opcional)"
Write-Host "  3. Configurar Sentry para error tracking (opcional)"
Write-Host "  4. Habilitar GitHub Actions CI/CD`n"

Write-Host "Comandos útiles:" -ForegroundColor Blue
Write-Host "  Ver logs backend:     " -NoNewline
Write-Host "railway logs -f" -ForegroundColor Green
Write-Host "  Reiniciar backend:    " -NoNewline
Write-Host "railway restart" -ForegroundColor Green
Write-Host "  Ejecutar comando:     " -NoNewline
Write-Host "railway run <comando>" -ForegroundColor Green
Write-Host "  Ver variables env:    " -NoNewline
Write-Host "railway variables" -ForegroundColor Green
Write-Host "  Redeploy frontend:    " -NoNewline
Write-Host "cd frontend; vercel --prod`n" -ForegroundColor Green

Write-Host "¡Sistema deployado exitosamente! 🎉`n" -ForegroundColor Green
Write-Host "Visitar: " -NoNewline
Write-Host "https://$FRONTEND_URL`n" -ForegroundColor Blue
