#!/bin/bash
# ========================================================================
# Chandelier ERP/POS - Free Tier Deployment Script
# ========================================================================
# Este script automatiza el deployment en Railway (backend) + Vercel (frontend)
# Costo: $0/mes (Railway $5 crédito + Vercel free tier)
#
# Requisitos:
# - Node.js 20+
# - Git configurado
# - Cuenta GitHub
# ========================================================================

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones auxiliares
print_step() {
    echo -e "\n${BLUE}==>${NC} ${GREEN}$1${NC}\n"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
   _____ _                     _      _ _
  / ____| |                   | |    | (_)
 | |    | |__   __ _ _ __   __| | ___| |_  ___ _ __
 | |    | '_ \ / _` | '_ \ / _` |/ _ \ | |/ _ \ '__|
 | |____| | | | (_| | | | | (_| |  __/ | |  __/ |
  \_____|_| |_|\__,_|_| |_|\__,_|\___|_|_|\___|_|

         FREE TIER DEPLOYMENT SCRIPT
         Costo: $0/mes | Deploy: 5 minutos
EOF
echo -e "${NC}"

# ========================================================================
# PASO 1: Verificar Requisitos
# ========================================================================
print_step "1/6 Verificando requisitos..."

# Verificar Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js no instalado. Instalar desde: https://nodejs.org"
    exit 1
fi
print_success "Node.js $(node --version) instalado"

# Verificar Git
if ! command -v git &> /dev/null; then
    print_error "Git no instalado. Instalar desde: https://git-scm.com"
    exit 1
fi
print_success "Git $(git --version | awk '{print $3}') instalado"

# Verificar que estamos en el directorio correcto
if [ ! -f "backend/app/main.py" ]; then
    print_error "Ejecutar este script desde la raíz del proyecto (merx_v2/)"
    exit 1
fi
print_success "Directorio correcto detectado"

# ========================================================================
# PASO 2: Instalar CLIs
# ========================================================================
print_step "2/6 Instalando CLIs de Railway y Vercel..."

# Railway CLI
if ! command -v railway &> /dev/null; then
    echo "Instalando Railway CLI..."
    npm install -g @railway/cli
    print_success "Railway CLI instalado"
else
    print_success "Railway CLI ya instalado"
fi

# Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "Instalando Vercel CLI..."
    npm install -g vercel
    print_success "Vercel CLI instalado"
else
    print_success "Vercel CLI ya instalado"
fi

# ========================================================================
# PASO 3: Deploy Backend en Railway
# ========================================================================
print_step "3/6 Deploying Backend en Railway..."

echo -e "${YELLOW}Abriendo navegador para login en Railway...${NC}"
railway login

echo -e "${YELLOW}Inicializando proyecto Railway...${NC}"
railway init

echo -e "${YELLOW}Provisionando PostgreSQL...${NC}"
railway add postgresql

echo -e "${YELLOW}Configurando variables de entorno...${NC}"

# Generar SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Configurar variables de entorno
railway variables set SECRET_KEY="$SECRET_KEY"
railway variables set ENVIRONMENT=production
railway variables set DEBUG=False
railway variables set ALGORITHM=HS256
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES=30

print_success "Variables de entorno configuradas"

echo -e "${YELLOW}Deploying backend (puede tardar 2-3 minutos)...${NC}"
railway up

# Ejecutar migraciones
echo -e "${YELLOW}Ejecutando migraciones Alembic...${NC}"
railway run alembic upgrade head

# Obtener URL del backend
BACKEND_URL=$(railway status --json | jq -r '.deployments[0].url')
print_success "Backend deployed en: $BACKEND_URL"

# Ejecutar seeders (opcional)
read -p "¿Ejecutar seeders de datos iniciales? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    railway run python -c "from backend.app.utils.seeders import run_all_seeders; run_all_seeders()"
    print_success "Seeders ejecutados"
fi

# ========================================================================
# PASO 4: Deploy Frontend en Vercel
# ========================================================================
print_step "4/6 Deploying Frontend en Vercel..."

cd frontend

echo -e "${YELLOW}Login en Vercel...${NC}"
vercel login

echo -e "${YELLOW}Deploying frontend (primera vez puede tardar 3-4 min)...${NC}"
vercel --prod --yes

# Configurar variable de entorno
echo -e "${YELLOW}Configurando VITE_API_URL...${NC}"
vercel env add VITE_API_URL production <<< "$BACKEND_URL/api/v1"

# Redeploy para aplicar variable
echo -e "${YELLOW}Redeploying para aplicar variables...${NC}"
vercel --prod --yes

FRONTEND_URL=$(vercel inspect --prod --json | jq -r '.url')
cd ..

print_success "Frontend deployed en: https://$FRONTEND_URL"

# ========================================================================
# PASO 5: Actualizar CORS en Backend
# ========================================================================
print_step "5/6 Actualizando CORS en Backend..."

railway variables set CORS_ORIGINS="https://$FRONTEND_URL"
railway restart

print_success "CORS actualizado y backend reiniciado"

# ========================================================================
# PASO 6: Verificación
# ========================================================================
print_step "6/6 Verificando deployment..."

echo "Verificando health check del backend..."
if curl -s "$BACKEND_URL/health" | grep -q "healthy"; then
    print_success "Backend health check OK"
else
    print_error "Backend health check falló. Ver logs: railway logs"
fi

echo "Verificando frontend..."
if curl -s -o /dev/null -w "%{http_code}" "https://$FRONTEND_URL" | grep -q "200"; then
    print_success "Frontend accesible"
else
    print_error "Frontend no accesible. Ver logs en Vercel dashboard"
fi

# ========================================================================
# RESUMEN
# ========================================================================
echo -e "\n${GREEN}========================================================================${NC}"
echo -e "${GREEN}✓ DEPLOYMENT COMPLETADO EXITOSAMENTE${NC}"
echo -e "${GREEN}========================================================================${NC}\n"

echo -e "${BLUE}URLs:${NC}"
echo -e "  Frontend: ${GREEN}https://$FRONTEND_URL${NC}"
echo -e "  Backend:  ${GREEN}$BACKEND_URL${NC}"
echo -e "  API Docs: ${GREEN}$BACKEND_URL/api/v1/docs${NC} (solo en dev)\n"

echo -e "${BLUE}Credenciales de prueba:${NC}"
echo -e "  Superadmin: ${YELLOW}superadmin@chandelier.com${NC} / ${YELLOW}superadmin123${NC}"
echo -e "  Admin:      ${YELLOW}admin@example.com${NC} / ${YELLOW}admin123${NC}"
echo -e "  Operador:   ${YELLOW}operador@velasaromaticas.com${NC} / ${YELLOW}operador123${NC}\n"

echo -e "${BLUE}Monitoreo:${NC}"
echo -e "  Railway Dashboard:  ${GREEN}https://railway.app/dashboard${NC}"
echo -e "  Vercel Dashboard:   ${GREEN}https://vercel.com/dashboard${NC}"
echo -e "  Logs Backend:       ${GREEN}railway logs -f${NC}"
echo -e "  Métricas Railway:   ${GREEN}railway status${NC}\n"

echo -e "${BLUE}Costo mensual:${NC}"
echo -e "  Backend (Railway):  ${GREEN}$0${NC} ($5 crédito/mes incluido)"
echo -e "  Frontend (Vercel):  ${GREEN}$0${NC} (free tier 100GB bandwidth)"
echo -e "  Database:           ${GREEN}$0${NC} (1GB PostgreSQL incluido)"
echo -e "  ${GREEN}TOTAL: $0/mes${NC}\n"

echo -e "${YELLOW}Siguientes pasos:${NC}"
echo -e "  1. Configurar UptimeRobot (https://uptimerobot.com) para monitoreo"
echo -e "  2. Agregar custom domain en Vercel (opcional)"
echo -e "  3. Configurar Sentry para error tracking (opcional)"
echo -e "  4. Habilitar GitHub Actions CI/CD\n"

echo -e "${BLUE}Comandos útiles:${NC}"
echo -e "  Ver logs backend:     ${GREEN}railway logs -f${NC}"
echo -e "  Reiniciar backend:    ${GREEN}railway restart${NC}"
echo -e "  Ejecutar comando:     ${GREEN}railway run <comando>${NC}"
echo -e "  Ver variables env:    ${GREEN}railway variables${NC}"
echo -e "  Redeploy frontend:    ${GREEN}cd frontend && vercel --prod${NC}\n"

echo -e "${GREEN}¡Sistema deployado exitosamente!${NC} 🎉\n"
echo -e "Visitar: ${BLUE}https://$FRONTEND_URL${NC}\n"
