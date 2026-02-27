# External Integrations

**Analysis Date:** 2026-02-27

## APIs & External Services

**Authentication & Identity:**
- **Clerk** - User authentication and identity management
  - SDK/Client: `@clerk/clerk-react` (v5.0.0) on frontend, `svix` (v1.14.0) for webhook verification on backend
  - Auth: `CLERK_SECRET_KEY` (env var - backend API access)
  - Webhooks: `CLERK_WEBHOOK_SECRET` (env var - svix signature verification)
  - Clerk JWKS URL: `CLERK_JWKS_URL` (env var - JWT validation endpoint)
  - Integration Pattern: Clerk JWT → `POST /auth/clerk-exchange` → Custom internal JWT
  - Endpoints:
    - `POST /auth/clerk-exchange` - Exchange Clerk JWT for internal token (with lazy user sync)
    - `POST /auth/clerk-webhook` - Receive Clerk events (user.created, user.updated, user.deleted)
  - Frontend: `ClerkProvider` wraps app in `main.tsx`, `SignIn`/`SignUp` components with Spanish localization
  - Lazy User Sync: Users created in Clerk are automatically synced to DB on first login/exchange

**Billing & Plans:**
- Not detected - No payment processor integrated (Stripe, etc. not in dependencies)

## Data Storage

**Databases:**
- **PostgreSQL 12+**
  - Connection: `DB_URL` or `DATABASE_URL` (env var)
  - Client: SQLAlchemy 2.0.46+ ORM
  - Schema: Alembic migrations in `backend/alembic/` (alembic upgrade head)
  - RLS Enabled: `SET LOCAL app.tenant_id_actual` per request (tenant isolation enforced at DB level)
  - Features:
    - JSONB columns for flexible storage
    - Foreign keys with cascading
    - CHECK constraints on enums (role, estado, etc.)
    - Audit triggers via `audit_listeners.py`

**File Storage:**
- **AWS S3 or S3-Compatible** (optional, disabled by default)
  - Service: AWS S3, Cloudflare R2, DigitalOcean Spaces (all compatible)
  - Client: boto3 (v1.34+)
  - Configuration:
    - `S3_ENABLED` - Enable/disable (default: false)
    - `S3_BUCKET` - Bucket name (default: "chandelier-documents")
    - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - Credentials (env vars)
    - `S3_ENDPOINT_URL` - Custom endpoint (for R2, Spaces, etc.)
    - `S3_PRESIGNED_URL_EXPIRY` - URL expiry in seconds (default: 86400 = 24h)
  - Usage: PDF document storage (facturas, cotizaciones, etc.)
  - Service: `ServicioAlmacenamiento` in `backend/app/servicios/servicio_almacenamiento.py`
  - Methods: `subir_pdf()`, `obtener_url_presigned()`, `eliminar_archivo()`
  - Fallback: None - if S3 disabled, no file storage available

**Caching:**
- Not detected - No Redis or explicit caching layer (query results cached by React Query on frontend)

## Authentication & Identity

**Auth Provider:**
- **Clerk** (primary, optional) - Modern OAuth-ready auth platform
- **Legacy Custom** - Password-based auth with JWT tokens (always available as fallback)

Implementation Approaches:
- **Clerk Flow**: ClerkProvider → ClerkCallbackPage → clerk-exchange endpoint → custom JWT
- **Legacy Flow**: LoginPage form → /auth/login endpoint → custom JWT directly
- Custom JWT Format:
  - Algorithm: HS256 (configurable via ALGORITHM setting)
  - Payload: `{sub: user_id, email, rol, tenant_id?, rol_en_tenant?}`
  - Expiry: Configurable (default: 30 minutes for access, 7 days for refresh)
  - Signing: `SECRET_KEY` (min 32 chars, validated for entropy)

**User Sync (Clerk):**
- Webhook: `POST /auth/clerk-webhook` receives events from Clerk
- Events handled: `user.created`, `user.updated`, `user.deleted`
- Webhook verification: Svix signature validation (CLERK_WEBHOOK_SECRET)
- Database sync: Auto-create/update/deactivate users based on Clerk events

**Token Rotation:**
- Refresh tokens rotate on each refresh request
- Access token refresh via `POST /auth/refresh` with `refresh_token` + optional `tenant_id`
- Frontend interceptor queues requests during token refresh (no thundering herd)

## Monitoring & Observability

**Error Tracking:**
- **Sentry** (optional, production/staging only)
  - Configuration: `SENTRY_DSN` (env var)
  - Integrations: FastAPI, SQLAlchemy
  - Features:
    - Performance monitoring (10% of transactions sampled)
    - Sensitive data filtering (Authorization headers, X-Tenant-ID removed)
    - No PII sent
  - Initialization: `backend/app/main.py` lines 23-49
  - Status: Only active if `SENTRY_DSN` configured

**Logging:**
- **Structured JSON Logging** (production-ready)
  - Library: python-json-logger (4.0.0+)
  - Format: Configurable via `LOG_FORMAT` (json for prod, text for dev)
  - Level: Configurable via `LOG_LEVEL` (default: INFO)
  - Context: Request ID, User ID, Tenant ID automatically attached
  - Implementation: `backend/app/utils/logger.py`
  - Features:
    - Request context tracking (set_request_context, clear_request_context)
    - Structured extra fields (user_id, tenant_id, ip, etc.)
    - Stack traces on errors with exc_info=e

**Database Monitoring:**
- Pool health: `pool_pre_ping=True` (checks connection before use)
- Query timeouts: PostgreSQL `statement_timeout` (30s default, configurable)
- Idle transaction timeout: PostgreSQL `idle_in_transaction_session_timeout` (60s default)
- Pool size: 10 connections + 20 overflow (configurable, 5-50 range)

## CI/CD & Deployment

**Hosting:**
- **Backend**: Railway.app
  - Service ID: `576ca852-4cd9-4ea5-90d8-11c42be5a941`
  - Project ID: `bf2dde70-b888-42d5-b9f0-f35dda4ae54e`
  - Deployment: Manual `railway up --detach` or git push trigger
  - Runtime: Uvicorn ASGI server
  - Database: Railway PostgreSQL (production proxy: `nozomi.proxy.rlwy.net:47298`)

- **Frontend**: Vercel
  - Deployment: Auto-deploy on push to master
  - Build: `npm run build` (tsc + vite)
  - Environment: `VITE_API_URL` and `VITE_CLERK_PUBLISHABLE_KEY` injected

- **Landing Page**: Vercel or Next.js compatible
  - Framework: Next.js 15.1.0
  - Deployment: Auto-deploy with frontend

**CI Pipeline:**
- GitHub Actions (not explicitly configured in checked files)
- pytest with SQLite (tests) and PostgreSQL (CI) via GitHub Actions setup
- Linting: ruff + ESLint on PR checks
- Testing: pytest with coverage reports

**Environment Configuration:**
- Railway Backend: env vars injected from Railway dashboard
- Vercel Frontend: env vars injected from Vercel project settings
- No `.env` file committed; uses platform-provided env vars

## Webhooks & Callbacks

**Incoming:**
- `POST /auth/clerk-webhook` - Clerk user lifecycle events
  - Events: `user.created`, `user.updated`, `user.deleted`
  - Security: Svix signature verification (CLERK_WEBHOOK_SECRET)
  - Response: HTTP 200 on success, 400 on invalid signature
  - Location: `backend/app/rutas/auth.py` lines 471-540

**Outgoing:**
- Not detected - No outgoing webhooks to external services (no payment, CRM sync, etc.)

## Real-Time Communication

**Server-Sent Events (SSE):**
- **Endpoint**: `GET /api/v1/sse/dashboard?token=<jwt>`
- **Purpose**: Real-time dashboard updates (order/invoice status changes)
- **Protocol**:
  - Client connects via EventSource API
  - Server sends heartbeats every 25 seconds (keeps connection alive)
  - Server broadcasts events to all connected clients for same tenant
  - Client auto-reconnects on disconnect (5s retry)
- **Security**: JWT token required as query param (tenant_id must be in token)
- **Implementation**: `backend/app/rutas/sse.py`
- **Manager**: `ServicioSSE` in `backend/app/servicios/servicio_sse.py`
- **Frontend**: Not detected - SSE endpoint exists but no EventSource consumer found in FE code

## Rate Limiting

**Configuration:**
- Enabled by default (`RATE_LIMIT_ENABLED = true`)
- Limit: 60 requests/minute per IP (configurable: 10-1000 range)
- Library: slowapi (wraps limits library)
- Applied to: Login (5/min), Refresh (10/min), Change Password (3/min), Clerk Exchange (10/min)

## CORS Configuration

**Allowed Origins:**
- Development: `localhost:3000`, `localhost:3001`, `localhost:5173`
- Production: Must be explicitly configured (no wildcard, no localhost)
- Credentials: Allowed (cookies/auth headers)
- Max Age: 600 seconds (10 minutes) for preflight caching

**Trusted Hosts:**
- Development: `localhost`, `127.0.0.1`, `0.0.0.0`, `*`
- Production: Must be restricted (wildcard temporary for Railway health checks)

## Environment Variable Schema

**Required:**
- `DB_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key (32+ chars)

**Optional but Recommended:**
- `ENVIRONMENT` - `development|staging|production`
- `SENTRY_DSN` - Error tracking
- `CLERK_SECRET_KEY`, `CLERK_WEBHOOK_SECRET`, `CLERK_JWKS_URL` - Clerk auth
- `S3_ENABLED`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - File storage
- `VITE_API_URL` (frontend) - API base URL
- `VITE_CLERK_PUBLISHABLE_KEY` (frontend) - Clerk frontend key

**Defaults Provided:**
- `CORS_ORIGINS`, `LOG_LEVEL`, `LOG_FORMAT`, `RATE_LIMIT_PER_MINUTE`, `S3_PRESIGNED_URL_EXPIRY`

---

*Integration audit: 2026-02-27*
