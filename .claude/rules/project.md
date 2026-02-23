# Project Security Rules

## ALWAYS

- Implement all six security layers (SAST, Secret Scanning, SCA, Container Security, DAST, AI Integration) as a unified DevSecOps ecosystem
- Use GitHub-native tools (CodeQL, Secret Scanning, Dependabot) as primary security controls
- Scan for SQL Injection, XSS, and authentication bypass vulnerabilities in FastAPI endpoints
- Validate tenant isolation in multitenant ERP architecture with every code change
- Include tenant_id validation in all database queries and API endpoints
- Run automated security scans on every pull request without exception
- Maintain dependency vulnerability monitoring for both Python pip and Node.js npm packages
- Scan Docker images with Trivy before deployment to production
- Perform OWASP ZAP dynamic analysis against live API endpoints weekly
- Implement custom Semgrep rules for domain-specific security patterns
- Use TruffleHog and Gitleaks to scan entire repository history for exposed secrets
- Configure automated security alerts with severity-based escalation
- Document all security findings with remediation steps
- Include security testing in CI/CD pipeline with blocking gates for critical vulnerabilities

## NEVER

- Allow any code changes that bypass tenant isolation validation
- Merge pull requests with exposed secrets or credentials
- Deploy containers with known critical vulnerabilities (CVSS 9.0+)
- Disable any security scanning tool in the automated pipeline
- Skip security review for any API endpoint that handles tenant data
- Use hardcoded credentials or API keys in the codebase
- Ignore dependency updates for known security vulnerabilities
- Run containers as root user in production environment
- Expose database connection strings or encryption keys in configuration files
- Merge code that disables CORS, HSTS, or other security headers
- Bypass authentication middleware in any FastAPI route
- Allow direct database access without tenant context validation
- Skip OWASP Top 10 vulnerability scanning for any new feature
- Disable security logging or monitoring in production