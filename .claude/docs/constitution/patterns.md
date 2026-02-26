## Naming Conventions (file names, variable names, class names)

- Use `snake_case` for Python files and variables (e.g., `security_scan.py`, `tenant_id`)
- Use `PascalCase` for Python classes (e.g., `TenantIsolationValidator`)
- Use `kebab-case` for GitHub Actions workflows (e.g., `codeql-analysis.yml`)
- Use `camelCase` for JavaScript/React variables and functions
- Use descriptive names that indicate security purpose (e.g., `secret_scan_report`, `dependency_vulnerability_check`)

## File Organization (directory structure rules)

```
.security/
├── codeql/
├── semgrep-rules/
├── workflows/
├── docker-security/
└── scripts/

tests/security/
├── tenant-isolation/
├── dependency-vulnerabilities/
├── container-security/
└── api-security/

src/
├── security/
│   ├── middleware/
│   ├── validators/
│   └── audit/
├── tenant/
│   ├── isolation/
│   └── permissions/
└── api/
    ├── authentication/
    └── authorization/
```

## Code Patterns (preferred patterns for this stack)

- Use dependency injection for security services
- Implement middleware for tenant isolation in FastAPI
- Use context managers for database connections with tenant scoping
- Implement security headers middleware in FastAPI
- Use React Context for tenant-based UI permissions
- Implement rate limiting using FastAPI middleware
- Use PostgreSQL row-level security (RLS) for data isolation

## ALWAYS

- ALWAYS enable GitHub native Secret Scanning for public repositories
- ALWAYS use parameterized queries to prevent SQL Injection
- ALWAYS validate tenant_id in every database query for multitenant systems
- ALWAYS implement proper authentication middleware in FastAPI
- ALWAYS scan Docker images with Trivy before deployment
- ALWAYS use HTTPS and security headers in FastAPI responses
- ALWAYS implement proper CORS configuration
- ALWAYS use environment variables for sensitive configuration
- ALWAYS validate and sanitize all user inputs
- ALWAYS implement proper error handling without information leakage

## NEVER

- NEVER commit secrets, API keys, or credentials to the repository
- NEVER use raw SQL queries without parameterization
- NEVER allow direct database access without tenant validation
- NEVER expose stack traces or internal errors to end users
- NEVER run containers as root user
- NEVER use outdated or vulnerable dependencies
- NEVER disable security headers in production
- NEVER skip security scanning in CI/CD pipelines
- NEVER allow cross-tenant data access
- NEVER use hardcoded passwords or tokens in code
