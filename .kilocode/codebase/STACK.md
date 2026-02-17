# Technology Stack

**Analysis Date:** 2026-02-15

## Languages

**Primary:**
- Python 3.12 - Backend API (FastAPI)
- TypeScript ~5.9.3 - Frontend (React)
- JavaScript - Frontend build tooling

**Secondary:**
- PostgreSQL SQL - Database queries and RLS policies
- Bash/Shell - Docker entrypoints and build scripts

## Runtime

**Environment:**
- Python 3.12 (backend, see `.python-version`)
- Node.js 20 LTS (frontend, via Docker)
- Uvicorn 0.40.0 (ASGI server for FastAPI)
- Nginx (reverse proxy in Docker frontend)

**Package Manager:**
- Backend: `uv` (fast Python package manager) via pip, `pyproject.toml` manifest
- Frontend: npm, `package.json` manifest
- Lockfiles: Frontend has `package-lock.json` (generated), Backend uses `uv.lock`

## Frameworks

**Core:**
- FastAPI 0.128.0+ - REST API framework with OpenAPI docs
- React 19.2.0 - UI library with hooks
- Vite 7.3.1 - Frontend build tool (replaces Create React App)

**Routing:**
- React Router DOM 7.13.0 - Frontend client-side routing

**Data Management:**
- SQLAlchemy 2.0.46+ - ORM with async support (`sqlalchemy`)
- Alembic 1.14.0 - Database migration tool
- Pydantic v2 12.5+ - Data validation and settings management

**Testing:**
- pytest 7.4.0+ - Python test runner
- pytest-asyncio 0.21.0+ - Async test support
- pytest-cov 4.1.0+ - Coverage reporting

**Build/Dev:**
- Tailwind CSS 4.1.18 - Utility-first CSS framework
- TypeScript ESLint (9.39.1+) - Linting with TypeScript support
- Ruff 0.1.0+ - Fast Python linter/formatter

## Key Dependencies

**Critical - Backend:**
- `passlib` 1.7.4 - Password hashing
- `argon2-cffi` 23.1.0 - Argon2 password hashing algorithm
- `psycopg2-binary` 2.9.11+ - PostgreSQL driver for SQLAlchemy
- `python-jose` 3.5.0+ - JWT creation/validation with cryptography support
- `reportlab` 4.0+ - PDF generation for invoices/quotes
- `boto3` 1.34+ - AWS S3/Cloudflare R2 file uploads

**Infrastructure - Backend:**
- `uvicorn` 0.40.0+ - Production ASGI server
- `slowapi` 0.1.9+ - Rate limiting middleware
- `sentry-sdk` 1.40.0+ - Error tracking (production/staging only)
- `python-json-logger` 4.0.0 - JSON-formatted logging
- `httpx` 0.27.0 - Async HTTP client for external API calls

**Frontend UI:**
- `@heroicons/react` 2.2.0 - Icon library (24px, 20px, 16px variants)
- `recharts` 3.7.0 - React charting library for dashboard KPIs/graphs
- `zustand` 5.0.11 - Lightweight state management (auth, tenant context)
- `axios` 1.13.5+ - HTTP client with interceptors for auth/token refresh

**Frontend State:**
- `@tanstack/react-query` 5.90.21 - Data fetching, caching, synchronization (TanStack Query)

## Configuration

**Environment:**
- Backend: `.env` file with Pydantic Settings (BaseSettings) validation
- Frontend: No `.env` files needed (env vars via Docker/deployment)
- Production example: `.env.production.example` (git-tracked template)

**Key configs required (Backend):**
- `DB_URL` - PostgreSQL connection string (required)
- `SECRET_KEY` - JWT secret (32+ chars, validated for strength)
- `ENVIRONMENT` - one of: development, staging, production
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `S3_ENABLED`, `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - S3/R2 storage
- `SENTRY_DSN` - Error tracking (optional, production/staging only)

**Build:**
- `pyproject.toml` - Python project config with dependencies, pytest, ruff settings
- `frontend/package.json` - NPM scripts: `dev`, `build`, `lint`, `preview`
- `Dockerfile.backend` - Multi-stage build (builder → slim Python 3.12 image)
- `Dockerfile.frontend` - Multi-stage build (builder → Nginx Alpine)
- `vite.config.ts` - Vite build config with React plugin, Tailwind, dev proxy to `/api`
- `eslint.config.js` - ESLint configuration for TypeScript/React
- `frontend/tsconfig.json` - TypeScript configuration (references app/node files)

## Platform Requirements

**Development:**
- Python 3.12+ (exact version via `.python-version`)
- Node.js 20 LTS (for npm)
- PostgreSQL 16 (via Docker Compose)
- Redis 7 (via Docker Compose for caching/tasks)
- Docker + Docker Compose (for local development services)

**Production:**
- Docker + container orchestration (Kubernetes, Docker Swarm, or managed container platforms)
- PostgreSQL 16+ (managed database or self-hosted)
- Redis 7+ (for async tasks, caching)
- S3-compatible storage (AWS S3, Cloudflare R2, DigitalOcean Spaces) - optional
- Sentry account for error tracking (optional, recommended)
- Nginx reverse proxy (frontend already uses Nginx in Docker)
- TLS/SSL certificate (Let's Encrypt in docker-compose.yml notes)

**Database:**
- PostgreSQL 16 with RLS (Row Level Security) enabled
- Supported drivers: psycopg2-binary (async via SQLAlchemy)
- Database pool: 20 connections (dev), 40 overflow, 3600s recycle, 30s timeout
- Timeouts: 30s statement timeout, 60s idle-in-transaction timeout

**Performance/Scaling:**
- Uvicorn: 4 workers in production (auto-reloading dev)
- Rate limiting: 60 requests/minute default (configurable via `RATE_LIMIT_PER_MINUTE`)
- Request timeout: 30s (configurable)
- S3 presigned URLs: 24h expiry (configurable)

---

*Stack analysis: 2026-02-15*
