# Integration Analysis

## Database Integrations

### PostgreSQL (Primary Database)
- **Purpose**: Main data store for all application data
- **Connection**: Via SQLAlchemy 2.0 with async support (asyncpg driver)
- **Features Used**:
  - Row-Level Security (RLS) for multi-tenancy
  - UUID primary keys
  - JSONB columns for flexible data
  - Custom PostgreSQL settings (`app.tenant_id_actual`)
  - Check constraints for data validation
  - Composite indexes for query optimization

### Redis (Cache/Session)
- **Purpose**: Rate limiting, session management, caching
- **Status**: Configured in docker-compose, not actively used in code yet
- **Connection URL**: `redis://redis:6379/0`

## Authentication & Authorization

### JWT Authentication (Self-Implemented)
- **Library**: python-jose with HS256 algorithm
- **Features**:
  - Access tokens (30-minute expiry default)
  - Refresh tokens (7-day expiry default)
  - Multi-tenant context in JWT payload
  - Role-based access control (RBAC)
  - Token refresh with automatic retry queue
  - Impersonation support for superadmin

### Password Security
- **Primary**: Argon2 (argon2-cffi)
  - Memory cost: 64MB
  - Time cost: 3 iterations
  - Parallelism: 4 threads
- **Fallback**: bcrypt via passlib

## External Services

### Sentry (Error Tracking)
- **Purpose**: Production error monitoring and performance tracing
- **Integration**: FastAPI and SQLAlchemy integrations
- **Configuration**:
  - Traces sample rate: 10%
  - Sensitive data filtering (Authorization, X-Tenant-ID headers)
  - Environment-based activation (production/staging only)

### S3-Compatible Storage
- **Library**: boto3
- **Supported Providers**:
  - AWS S3
  - Cloudflare R2
  - DigitalOcean Spaces
- **Purpose**: PDF storage for invoices and quotes
- **Features**:
  - Presigned URLs (24-hour expiry default)
  - Tenant-isolated storage paths (`{tenant_id}/{tipo}/{uuid}.pdf`)
  - Configurable endpoint for non-AWS providers

## Payment Processing

### Wompi (Planned)
- **Purpose**: Payment processing for SaaS subscriptions
- **Status**: Database schema prepared, integration not implemented
- **Configuration**: Environment variables defined in `.env.production.example`
  - `WOMPI_PUBLIC_KEY`
  - `WOMPI_PRIVATE_KEY`
  - `WOMPI_WEBHOOK_SECRET`
  - `WOMPI_ENABLED`

## Email Services

### SMTP (Planned)
- **Purpose**: Transactional emails
- **Configuration**: Environment variables defined
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
  - Default: Mailgun SMTP relay

## Frontend Integrations

### API Communication
- **Client**: Axios with interceptors
- **Features**:
  - Automatic JWT token injection
  - Tenant ID header injection
  - Automatic token refresh on 401
  - Request queueing during refresh
  - Error handling with redirect to login

### State Management
- **Zustand**: Client state with localStorage persistence
- **TanStack Query**: Server state caching and synchronization

## Third-Party Libraries by Purpose

### Backend

| Library | Purpose | Notes |
|---------|---------|-------|
| FastAPI | Web framework | Async support, OpenAPI docs |
| SQLAlchemy | ORM | 2.0 with async support |
| Pydantic | Data validation | Settings management |
| python-jose | JWT handling | HS256 algorithm |
| passlib/argon2-cffi | Password hashing | Argon2 preferred |
| ReportLab | PDF generation | Invoices, quotes |
| boto3 | S3 storage | Multi-provider support |
| slowapi | Rate limiting | Per-IP limiting |
| Sentry SDK | Error tracking | Production monitoring |
| httpx | HTTP client | External API calls |
| uvicorn | ASGI server | Production deployment |

### Frontend

| Library | Purpose | Notes |
|---------|---------|-------|
| React 19 | UI framework | Latest version |
| React Router | Client routing | v7 |
| Zustand | State management | With persistence |
| TanStack Query | Server state | Caching, invalidation |
| Axios | HTTP client | With interceptors |
| Tailwind CSS | Styling | v4 via Vite plugin |
| Heroicons | Icons | React components |
| Recharts | Charts | Dashboard visualizations |

## CI/CD Integrations

### GitHub Actions
- **Triggers**: Push to master/develop, Pull Requests
- **Services**: PostgreSQL 16 for test execution
- **Tools**:
  - Ruff (linting)
  - pytest (testing)
  - TypeScript compiler
  - ESLint
  - Docker Buildx
  - Trivy (security scanning)
  - Codecov (coverage reporting)

## Deployment Platforms

### Railway (Backend)
- **Configuration**: `Dockerfile.railway`
- **Services**: Backend + PostgreSQL
- **Variables**: Auto-generated `DATABASE_URL`

### Vercel (Frontend)
- **Build**: Vite production build
- **Variables**: `VITE_API_URL`, `VITE_ENVIRONMENT`

### Docker Compose (Self-Hosted)
- **Services**: backend, frontend, postgres, redis
- **Networking**: Bridge network (`chandelier_network`)
- **Volumes**: Persistent PostgreSQL data

## Monitoring & Observability

### Health Checks
- **Backend**: `/health` endpoint with database connectivity check
- **Frontend**: Nginx health check on `/health`
- **Docker**: Container-level health checks

### Logging
- **Format**: JSON (production), text (development)
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context**: Request ID, user ID, tenant ID

### External Monitoring
- **UptimeRobot**: Recommended for uptime monitoring (not integrated)
- **Sentry**: Error and performance monitoring

## Security Integrations

### Rate Limiting
- **Library**: slowapi
- **Default**: 60 requests/minute per IP
- **Configurable**: Via `RATE_LIMIT_PER_MINUTE` env var

### Security Headers (Nginx)
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- HSTS (production only)

### CORS Configuration
- **Library**: fastapi-cors + FastAPI CORSMiddleware
- **Credentials**: Enabled
- **Max Age**: 600 seconds
- **Production**: Must specify exact domains (no localhost, no wildcard)

## Webhooks (Planned)

### Wompi Webhooks
- **Endpoint**: `/api/webhooks/wompi` (not implemented)
- **Purpose**: Payment status updates for subscriptions
- **Security**: HMAC signature verification

## Not Yet Integrated

The following are mentioned in configuration/architecture but not implemented:

1. **Celery + Redis**: Async task processing (mentioned in PRD, not in dependencies)
2. **Wompi Payment API**: Subscription billing
3. **Email Service**: Transactional emails
4. **WhatsApp Business API**: Customer communication (Phase 2)
5. **DIAN Electronic Invoicing**: Colombian tax authority integration (Phase 2)
