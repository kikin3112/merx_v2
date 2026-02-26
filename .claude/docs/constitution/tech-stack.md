Technology | Version | Purpose | Rationale
--- | --- | --- | ---
GitHub | latest | Repository hosting | Public repository for the codebase
CodeQL | latest | Static Analysis Security Testing (SAST) | Native GitHub tool for finding SQL Injection, XSS, and auth bypass vulnerabilities
Secret Scanning | latest | Credential detection | GitHub's native secret scanning to detect exposed API keys, tokens, and credentials
Dependabot | latest | Dependency management | Automated alerts and PRs for vulnerable dependencies in pip and npm packages
Snyk | latest | Dependency vulnerability analysis | Deep analysis of dependency graphs and vulnerability impact visualization
Trivy | latest | Container security scanning | Scans Docker images for OS and package vulnerabilities
Docker Bench for Security | latest | Docker configuration hardening | Script to check Docker configuration against security best practices
OWASP ZAP (Zaproxy) | latest | Dynamic Analysis Security Testing (DAST) | Automated attacks on deployed application to find configuration weaknesses and security headers issues
Semgrep | latest | Custom pattern detection | Allows writing custom rules to prevent insecure patterns specific to FastAPI and multitenant architecture
TruffleHog | latest | Secret scanning | Detects accidentally committed secrets in repository history
Gitleaks | latest | Secret detection | Alternative secret scanning tool with pre-commit hooks capability
ESLint | latest | Frontend security linting | JavaScript security analysis for React frontend
SonarQube | latest | Code quality metrics | Additional security and quality metrics for both backend and frontend
Safety | latest | Python dependency audit | Command-line tool for checking Python dependencies against known vulnerabilities
npm audit | latest | JavaScript dependency audit | Built-in npm tool for checking frontend dependencies
Docker | latest | Containerization | Container platform for deploying the application
FastAPI | latest | Backend framework | Python web framework for building the API
PostgreSQL | latest | Database | Relational database for storing ERP data
React | latest | Frontend framework | JavaScript library for building the user interface
Claude/GPT | latest | AI code review | Custom AI agent for reviewing pull requests and business logic security
