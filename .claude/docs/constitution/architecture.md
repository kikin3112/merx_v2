## Overview

This is a comprehensive DevSecOps ecosystem designed to protect a FastAPI + Postgres + React application with a public GitHub repository. The system implements multiple security layers that work together to prevent code theft, hacks, and data breaches throughout the entire development lifecycle. The architecture follows a "shift-left" security approach where vulnerabilities are caught early and continuously, with automated protection mechanisms that run without manual intervention.

## Components

**Code Analysis Layer**
- CodeQL (GitHub native) - Static analysis for SQL Injection, XSS, and OWASP Top 10 vulnerabilities
- Semgrep - Custom rule engine for FastAPI-specific insecure patterns
- ESLint + SonarJS - Frontend React security analysis

**Secrets Management Layer**
- GitHub Secret Scanning - Real-time credential detection
- TruffleHog - Historical repository scanning for exposed secrets
- Gitleaks - Pre-commit hooks for immediate feedback

**Supply Chain Security Layer**
- Dependabot - Automated dependency updates for pip and npm packages
- Snyk - Deep dependency graph analysis with vulnerability tracking
- Safety audit - Python dependency security scanning

**Container Security Layer**
- Trivy - Docker image vulnerability scanning
- Docker Bench - Container configuration hardening
- Snyk Container - OS-level vulnerability detection

**Dynamic Analysis Layer**
- OWASP ZAP - Automated API endpoint security testing
- Postman/Newman - API contract and security validation
- Selenium - Frontend security flow testing

**AI Integration Layer**
- Claude/GPT Code Reviewer - Pull request security analysis
- Custom rules engine - Domain-specific pattern detection
- A.C.O.S. Engine - Automated security decision making

## Data Flow

Code flows through the system in a continuous pipeline: Developers push code → GitHub triggers automated security scans (CodeQL, Secret Scanning) → Pull requests are analyzed by AI reviewer (Claude/GPT) → Dependencies are checked by Dependabot and Snyk → Container images are scanned by Trivy before deployment → Live API is tested by OWASP ZAP → Security metrics and vulnerabilities are reported back to developers. Each layer provides immediate feedback and blocks insecure code from progressing further in the pipeline.

## Key Decisions

**1. Full Automation Over Manual Control**
The system prioritizes complete automation through GitHub Actions to ensure security is applied consistently without relying on developer discipline. This eliminates human error and ensures every code change undergoes the same rigorous security validation.

**2. Multitenant-Specific Security Rules**
Given the ERP's multitenant nature, the architecture includes specialized CodeQL and Semgrep rules that specifically validate tenant isolation and prevent data leakage between tenants. This goes beyond generic security scanning to address the unique risks of shared infrastructure.

**3. AI-Powered Business Logic Validation**
The inclusion of Claude/GPT for pull request analysis addresses a critical gap in traditional security tools: detecting business logic flaws and tenant-specific security violations that automated scanners typically miss. This provides human-level reasoning about security context.
