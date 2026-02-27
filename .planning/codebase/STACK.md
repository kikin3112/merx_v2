# Technology Stack

**Analysis Date:** 2026-02-27

## Languages

**Primary:**
- Python 3.12 - Backend (FastAPI), async application server with type hints
- TypeScript 5.9.3 - Frontend and landing site, strict type safety across UI and client

**Secondary:**
- SQL (PostgreSQL) - Relational database queries with RLS (Row-Level Security) support
- JavaScript - Build and dev tools

## Runtime

**Environment:**
- Python 3.12 (enforced via `.python-version`)
- Node.js (version not pinned, uses system Node)

**Package Managers:**
- pip/Poetry - Python dependencies via `pyproject.toml`
- npm - Node.js dependencies via `package.json` (frontend and landing)
- Lockfiles: Present (implicitly managed by pip and npm)

## Frameworks

**Core:**
- FastAPI 0.128.0+ - Backend REST API framework, async/await throughout
- React 19.2.0 - Frontend UI library (SPA in Vite)
- Next.js 15.1.0 - Landing page static site generation

**Web/HTTP:**
- Uvicorn 0.40.0 - ASGI server for FastAPI
- Axios 1.13.5 - Frontend HTTP client with interceptors (auth, tenant context)
- httpx 0.27.0 - Python async HTTP client (Clerk API calls, webhooks)

**Testing:**
- pytest 7.4.0+ - Python unit/integration tests
- pytest-asyncio 0.21.0+ - Async test support
- pytest-cov 4.1.0+ - Coverage reporting

**Build/Dev:**
- Vite 7.3.1 - Frontend bundler and dev server
- TypeScript 5.9.3 - Type checking
- ESLint 9.39.1 - JavaScript linting
- Ruff 0.1.0+ - Python linting (E, F, I, N, W rules)
- Tailwind CSS 4.1.18 - Utility-first CSS framework

## Key Dependencies

**Authentication & Security:**
- pyjwt 2.8.0 - JWT encoding/decoding for custom tokens
- python-jose[cryptography] 3.5.0+ - Alternative JWT handling
- passlib 1.7.4 - Password hashing interface
- argon2-cffi 23.1.0+ - Argon2 password hashing algorithm
- cryptography 42.0.0+ - Cryptographic primitives

**Database:**
- sqlalchemy 2.0.46+ - ORM and SQL toolkit
- psycopg2-binary 2.9.11+ - PostgreSQL adapter
- alembic 1.14.0+ - Schema migrations
- pydantic[email] 2.12.5+ - Data validation (with email support)

**State Management (Frontend):**
- Zustand 5.0.11 - Lightweight global state (auth, tenants, app settings)
- @tanstack/react-query 5.90.21 - Server state and caching

**UI & Components (Frontend):**
- @heroicons/react 2.2.0 - Icon set
- React Router DOM 7.13.0 - Client-side routing
- React Window 1.8.10 - Virtualized lists (100k+ rows)
- Recharts 3.7.0 - React charting library
- @react-spring/web 10.0.3 - Animation library

**Infrastructure & Monitoring:**
- sentry-sdk[fastapi] 1.40.0+ - Error tracking and performance monitoring
- slowapi 0.1.9+ - Rate limiting (SlowAPI wrapper around limits)
- python-json-logger 4.0.0+ - Structured JSON logging

**External Service Integrations:**
- boto3 1.34+ - AWS S3 client (or S3-compatible: Cloudflare R2, DigitalOcean Spaces)
- svix 1.14.0+ - Webhook signing and verification (Clerk webhooks)
- pydantic-settings 2.12.0+ - Environment configuration validation

**Utilities:**
- python-multipart 0.0.9+ - Multipart form handling
- fastapi-cors 0.0.6 - CORS middleware

**Development Tools:**
- bandit 1.8.0+ - Security linting
- safety 3.0.0+ - Dependency vulnerability scanning
- semgrep 1.70.0+ - Code pattern analysis
- pre-commit 3.7.0+ - Git hook framework

## Configuration

**Environment:**
- `.env` files (not version controlled - contains secrets)
- Pydantic Settings (Settings class in `backend/app/config.py`) - validates all env vars at startup
- Settings classes applied at module load time (singleton pattern)

**Key Configs Required:**
- `DB_URL` or `DATABASE_URL` - PostgreSQL connection string (required)
- `SECRET_KEY` - JWT signing key (min 32 chars, validated for entropy)
- `ENVIRONMENT` - `development|staging|production` (default: development)
- `VITE_API_URL` - Frontend API base URL (default: /api/v1)
- `VITE_CLERK_PUBLISHABLE_KEY` - Clerk frontend key (if using Clerk auth)
- `CLERK_SECRET_KEY` - Clerk backend secret (if using Clerk auth)
- `CLERK_WEBHOOK_SECRET` - Clerk webhook signing secret (if using webhooks)

**Build:**
- `pyproject.toml` - Python project metadata and dependencies
- `frontend/package.json` - npm dependencies and scripts
- `frontend/tsconfig.json` - TypeScript compiler options
- `landing/package.json` - Next.js landing page config
- `.eslintrc` (frontend) - Linting rules
- Vite configuration (implicit, uses defaults)

## Platform Requirements

**Development:**
- Python 3.12+
- Node.js 16+ (no LTS pinning in repo)
- PostgreSQL 12+ (RLS support required)
- Git

**Production:**
- Deployment target: Railway.app (backend) + Vercel (frontend)
- PostgreSQL 12+ with public schema access
- HTTPS/TLS required
- Environment variable injection via platform (not .env file)

**Optional Production Services:**
- Sentry (error tracking)
- Clerk (user authentication + webhooks)
- AWS S3 or compatible (Cloudflare R2, DigitalOcean Spaces) for document storage
- SendGrid or similar (email - not currently integrated)

---

*Stack analysis: 2026-02-27*
