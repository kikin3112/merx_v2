# External Integrations

**Analysis Date:** 2026-02-15

## APIs & External Services

**Payment Processing:**
- Wompi - Online payment gateway for SaaS subscription collection
  - SDK/Client: None (direct HTTPS API calls via httpx)
  - Auth: `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_WEBHOOK_SECRET`
  - Usage: Subscription payment processing and webhook callbacks
  - Status: Optional (configurable via `WOMPI_ENABLED`)

**Document Generation:**
- ReportLab - PDF generation library (not external API, local library)
  - Used for: Invoice/quote PDFs, embedded in backend
  - Integration: `reportlab >= 4.0`

## Data Storage

**Databases:**
- PostgreSQL 16
  - Connection: `DB_URL` env var (postgresql://user:pass@host:port/db)
  - Client: SQLAlchemy 2.0.46+ with psycopg2-binary driver
  - ORM: SQLAlchemy async with Session/engine pooling
  - RLS: Row Level Security policies per tenant (app.tenant_id_actual context variable)
  - Pool Settings: size=20, max_overflow=40, recycle=3600s, timeout=30s

**File Storage:**
- AWS S3 / Cloudflare R2 / DigitalOcean Spaces (S3-compatible)
  - SDK/Client: boto3 1.34+
  - Connection: `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
  - Bucket: `S3_BUCKET` (configurable, default: "chandelier-documents")
  - Region: `S3_REGION` (default: "us-east-1", set to "auto" for Cloudflare R2)
  - Usage: PDF storage (invoices, quotes), logo uploads
  - Presigned URLs: 24h expiry (configurable via `S3_PRESIGNED_URL_EXPIRY`)
  - Implementation: `backend/app/servicios/servicio_almacenamiento.py`
  - Optional: Disabled by default (`S3_ENABLED=False`)

**Caching & Task Queue:**
- Redis 7
  - Connection: `REDIS_URL` (redis://redis:6379/0 in Docker)
  - Usage: Task queue (planned for Celery), caching (future)
  - Status: Running in docker-compose but not actively used in MVP

## Authentication & Identity

**Auth Provider:**
- Custom JWT implementation
  - Implementation: `backend/app/utils/auth.py` (implied by config)
  - Algorithm: HS256 (HMAC-SHA256, configurable via `ALGORITHM`)
  - Secret: `SECRET_KEY` (32+ chars, validated)
  - Access Token: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
  - Refresh Token: 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
  - Password Hashing: argon2-cffi with bcrypt via passlib
  - Flow: JWT tokens stored in localStorage (frontend), sent via Authorization header
  - Token Refresh: Automatic 401 interception and token refresh (see `frontend/src/api/client.ts`)

**Multi-Tenancy:**
- Header-based tenant isolation
  - Header: `X-Tenant-ID` (UUID format)
  - RLS: PostgreSQL SET LOCAL app.tenant_id_actual per transaction
  - Enforcement: Automatic via SQLAlchemy event listener on transaction begin
  - Middleware: `backend/app/middleware/tenant_context.py`

## Monitoring & Observability

**Error Tracking:**
- Sentry SDK 1.40.0+
  - Config: `SENTRY_DSN` (optional)
  - Integrations: FastAPI, SQLAlchemy
  - Activation: Production and staging only
  - Sampling: 10% of transactions for performance monitoring
  - Filtering: Sensitive headers (Authorization, X-Tenant-ID) stripped before sending
  - Implementation: `backend/app/main.py` (lines 28-54)

**Logs:**
- Standard Python logging with JSON formatting
  - Format: JSON (production) or text (development)
  - Level: Configurable via `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Library: `python-json-logger 4.0.0`
  - Context: Request ID, user ID, tenant ID included in logs
  - Implementation: `backend/app/utils/logger.py`

**Monitoring (Deployment):**
- Health checks (not integrations but infrastructure):
  - HTTP: `/health` endpoint (database connection check)
  - Docker: Health checks in docker-compose.yml
  - Third-party: UptimeRobot (mentioned in config example, external service)

## CI/CD & Deployment

**Hosting:**
- Docker Compose (development)
- Container-based (production): Kubernetes, Docker Swarm, Railway, Heroku, DigitalOcean App Platform, etc.
- Orchestration: Docker Swarm or Kubernetes (not explicitly configured)

**CI Pipeline:**
- Not detected - No GitHub Actions, GitLab CI, or other CI config files found

**Build & Deployment:**
- Docker multi-stage builds for both backend and frontend
- Backend: Python 3.12-slim, uv for dependency caching, Uvicorn 4 workers
- Frontend: Node 20-alpine builder, Nginx Alpine runtime
- Database migrations: Alembic (runs on startup: `alembic upgrade head`)

## Environment Configuration

**Required env vars:**
- `DB_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret (minimum 32 chars)
- `ENVIRONMENT` - development|staging|production

**Recommended env vars:**
- `CORS_ORIGINS` - Comma-separated allowed origins (default: localhost:3000,5173)
- `SENTRY_DSN` - For production error tracking
- `S3_ENABLED` - Enable S3 storage
- `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - S3 credentials

**Optional env vars:**
- `WOMPI_ENABLED`, `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY` - Payment gateway
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` - Email (for future transactional emails)
- `LOG_LEVEL`, `LOG_FORMAT` - Logging control
- `RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MINUTE` - Rate limiting

**Secrets location:**
- `.env` file (development - in .gitignore, example at `.env.production.example`)
- Environment variables in container runtime (Docker Compose, Kubernetes secrets, etc.)
- Never commit `.env` or `.env.production` to git

## Webhooks & Callbacks

**Incoming:**
- Wompi Payment Webhook: `/api/v1/webhooks/wompi` (planned, not yet implemented)
  - Event: transaction.updated (payment status changes)
  - Signature: HMAC validation using `WOMPI_WEBHOOK_SECRET`
  - Payload: Wompi transaction ID, status, amount, reference

**Outgoing:**
- Not implemented in MVP
- Email notifications (future via SMTP)
- Sentry error reports (automatic, handled by SDK)

## Rate Limiting

**Implementation:**
- slowapi (0.1.9+) - FastAPI rate limiting middleware
- Configuration: `RATE_LIMIT_ENABLED` (default: True)
- Limit: 60 requests/minute per IP (configurable via `RATE_LIMIT_PER_MINUTE`)
- Response: 429 Too Many Requests

## CORS (Cross-Origin Resource Sharing)

**Configuration:**
- Origins: Controlled via `CORS_ORIGINS` env var
- Methods: GET, POST, PUT, DELETE, PATCH (explicit, not *)
- Headers: Authorization, Content-Type, X-Tenant-ID, Accept
- Credentials: Allowed by default (`CORS_ALLOW_CREDENTIALS=True`)
- Max Age: 600 seconds (configurable)
- Production: Validates no wildcard (*) and no localhost allowed

## Security Headers

**Implementation:**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- HSTS: max-age=31536000 (production only, requires HTTPS)
- Implementation: `backend/app/main.py` SecurityHeadersMiddleware

## Frontend API Integration

**Client:**
- axios 1.13.5+ with custom interceptors
- Base URL: `/api/v1` (proxied via Vite dev server)
- Token refresh: Automatic 401 interception and refresh flow
- Storage: Access token and refresh token in localStorage (zustand persisted state)
- Implementation: `frontend/src/api/client.ts`

---

*Integration audit: 2026-02-15*
