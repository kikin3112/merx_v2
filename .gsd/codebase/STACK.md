# Technology Stack Analysis

## Backend

### Framework & Runtime
- **Python**: 3.12 (required version in pyproject.toml)
- **FastAPI**: >=0.115.0 (requirements.txt) / >=0.128.0 (pyproject.toml)
- **Uvicorn**: >=0.32.0 / >=0.40.0 (ASGI server with standard extras)

### Database
- **PostgreSQL**: 16-alpine (Docker compose)
- **SQLAlchemy**: 2.0+ (async support via asyncio extra)
- **asyncpg**: >=0.29.0 (async PostgreSQL driver)
- **Alembic**: >=1.13.0 / >=1.14.0 (database migrations)
- **psycopg2-binary**: >=2.9.11 (sync PostgreSQL driver)

### ORM & Data Validation
- **Pydantic**: 2.0+ with email extra and settings
- **Pydantic Settings**: >=2.0.0 / >=2.12.0 (environment configuration)

### Authentication & Security
- **python-jose**: >=3.3.0 / >=3.5.0 with cryptography extra (JWT handling)
- **passlib**: >=1.7.4 with bcrypt extra (password hashing)
- **argon2-cffi**: >=23.1.0 (modern password hashing, preferred over bcrypt)
- **slowapi**: >=0.1.9 (rate limiting)

### HTTP & API
- **httpx**: >=0.27.0 (HTTP client for external APIs)
- **python-multipart**: >=0.0.9 (form data handling)
- **fastapi-cors**: >=0.0.6 (CORS middleware)

### PDF Generation
- **ReportLab**: >=4.0 (PDF generation for invoices and quotes)

### Cloud Storage
- **boto3**: >=1.34 (S3/Cloudflare R2 integration)

### Error Tracking
- **Sentry SDK**: >=1.40.0 / >=2.0.0 with FastAPI integration

### Logging
- **python-json-logger**: >=4.0.0 (structured JSON logging)

## Frontend

### Framework & Runtime
- **React**: 19.2.0
- **React DOM**: 19.2.0
- **TypeScript**: ~5.9.3 (strict mode enabled)

### Build Tools
- **Vite**: 7.3.1 (build tool and dev server)
- **@vitejs/plugin-react**: 5.1.1

### Styling
- **Tailwind CSS**: 4.1.18 (via @tailwindcss/vite plugin)

### State Management
- **Zustand**: 5.0.11 (state management with persistence)

### Data Fetching
- **TanStack React Query**: 5.90.21 (server state management)
- **Axios**: 1.13.5 (HTTP client with interceptors)

### Routing
- **React Router DOM**: 7.13.0

### UI Components
- **Heroicons React**: 2.2.0 (icon library)
- **Recharts**: 3.7.0 (charting library for dashboards)

### Development Tools
- **ESLint**: 9.39.1 with React plugins
- **typescript-eslint**: 8.48.0

## Infrastructure

### Containerization
- **Docker Compose**: 3.8 format
- **Docker Images**:
  - Backend: Python 3.12-slim (multi-stage build)
  - Frontend: Node 20-alpine (build) + Nginx alpine (production)
  - Database: PostgreSQL 16-alpine
  - Cache: Redis 7-alpine

### Web Server
- **Nginx**: Alpine (reverse proxy, static file serving)

### Package Management
- **Backend**: uv (fast Python package manager)
- **Frontend**: npm

## Testing

### Backend Testing
- **pytest**: >=7.4.0
- **pytest-asyncio**: >=0.21.0
- **pytest-cov**: >=4.1.0 (coverage reporting)
- **FastAPI TestClient**: For integration tests
- **SQLite in-memory**: For test database isolation

### Frontend Testing
- No testing framework currently configured

## Code Quality

### Backend
- **Ruff**: >=0.1.0 (linter, replaces flake8/isort)
  - Line length: 120
  - Target: Python 3.12
  - Rules: E, F, I, N, W

### Frontend
- **ESLint**: 9.39.1 with React hooks plugin
- **TypeScript**: strict mode enabled

## CI/CD

### GitHub Actions
- **Backend Lint**: Ruff check on Python 3.12
- **Backend Test**: pytest with PostgreSQL 16 service container
- **Frontend Lint**: ESLint + TypeScript type check
- **Frontend Build**: Production build verification
- **Docker Build**: Multi-architecture image builds
- **Security Scan**: Trivy vulnerability scanner

### Coverage
- **Codecov**: Integration for coverage reporting

## Development Workflow

### Environment Management
- `.env` file (local development)
- `.env.production.example` (production template)
- `.env.railway.example` (Railway deployment template)

### Database Migrations
- Alembic with auto-generated migrations
- Migrations stored in `alembic/versions/`

## Deployment Targets

### Supported Platforms
- **Railway**: Backend + PostgreSQL
- **Vercel**: Frontend
- **Docker Compose**: Full stack self-hosted

## Key Architectural Patterns

### Backend
- Multi-tenant architecture with Row-Level Security (RLS)
- Service layer pattern (separation of concerns)
- Repository pattern via SQLAlchemy ORM
- Middleware-based tenant context injection
- JWT authentication with refresh token rotation

### Frontend
- Mobile-first responsive design
- Component-based architecture
- API client with request/response interceptors
- Automatic token refresh handling
- Role-based access control (RBAC)
