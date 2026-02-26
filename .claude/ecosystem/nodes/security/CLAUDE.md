# Security Node — Claude Code Instructions

## Scope
DevSecOps, 6 security pipelines, tenant isolation enforcement, vulnerability management.

## Source Code
- Security workflows: `.github/workflows/` (sast, secrets, sca, container, dast, ai-sec)
- Backend security: `backend/app/rutas/` (auth middleware), `backend/app/servicios/`
- Pre-commit: `.pre-commit-config.yaml`

## 6 Security Pipelines
1. SAST — CodeQL + Semgrep + Bandit
2. Secret Scanning — Gitleaks + TruffleHog
3. SCA — Dependabot (pip + npm)
4. Container Security — Trivy
5. DAST — OWASP ZAP (weekly)
6. AI Integration — custom rules

## NON-NEGOTIABLE Rules
- EVERY DB query must include `tenant_id` — no exceptions.
- NEVER merge PRs with exposed secrets.
- NEVER disable any security scanning tool.
- NEVER run containers as root in production.
- NEVER bypass auth middleware in any FastAPI route.
- Critical vulnerabilities (CVSS 9.0+) block deployment.

## Project Security Rules
See `project-rules.md` in this directory.

## Agent
`.claude/agents/security-engineer.md`

## Node Details
`NODE.md` in this directory.
