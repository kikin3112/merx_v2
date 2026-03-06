# Chandelier - Despliegue

Comandos para ejecutar el proyecto localmente y preparar para producción.

## Desarrollo Local

```bash
# Instalar dependencias
uv sync

# Ejecutar servidor backend
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Ejecutar frontend
cd frontend && npm run dev

# Ejecutar seeders
uv run python -c "from backend.app.utils.seeders import run_all_seeders; run_all_seeders()"

# Migraciones
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "descripcion"
```

## Verificación de Salud

```bash
# Health check
curl http://localhost:8000/health

# API docs
# http://localhost:8000/api/v1/docs

# Login rápido
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<TU_EMAIL_ADMIN>","password":"<TU_PASSWORD>"}'
```

## Estructura de Puertos

| Servicio | Puerto |
|----------|--------|
| Backend (FastAPI) | 8000 |
| Frontend (Vite) | 5173 |
| PostgreSQL | 5432 |

## Variables de Entorno (.env)

```bash
DB_URL=postgresql://postgres:<TU_PASSWORD>@localhost:5432/api_merx_v2
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
SECRET_KEY=<GENERAR_CON: python -c "import secrets; print(secrets.token_urlsafe(32))">
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_NAME=chandelierp
APP_VERSION=1.0.0
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=INFO
```

## Build Frontend

```bash
cd frontend && npm run build
# Output en frontend/dist/
```
