# L3 — Head of DevOps & Platform

> Owner of infrastructure, CI/CD, deployments, and platform reliability.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L3 — Functional Direction |
| **Reports To** | VP Engineering (L2) |
| **Pillar** | Infrastructure, DevOps & Security |
| **Stack** | Docker, Railway, Vercel, Nginx, GitHub Actions (9 workflows), PostgreSQL |

---

## Purpose

Ensure **reliable, automated, and cost-effective** infrastructure that enables squads to deploy confidently and frequently.

---

## Responsibilities

| Area | Responsibility |
|------|---------------|
| **CI/CD** | Maintain GitHub Actions workflows (ci, deploy-frontend, deploy-landing, etc.) |
| **Infrastructure** | Docker, Docker Compose, Dockerfiles, Railway, Vercel, Nginx configuration |
| **Monitoring** | Application monitoring, logging, alerting (free-tier tools) |
| **Database ops** | PostgreSQL management, backups, replicas, performance tuning |
| **Deployment** | Blue-green / canary deployment strategy |
| **Cost optimization** | $0 philosophy — maximize free tiers, minimize paid resources |
| **Incident response** | On-call coordination, war room facilitation for P0/P1 |
| **Platform** | Developer experience tools, local dev environment, staging environments |

---

## CI/CD Pipeline Governance

| Workflow | Purpose | Trigger |
|----------|---------|---------|
| `ci` | Lint, test, type-check | Every PR |
| `security-sast` | Static analysis (Semgrep, Bandit) | Every PR |
| `security-sca` | Dependency vulnerability scan | Every PR |
| `security-secrets` | Secret detection (Gitleaks) | Every PR |
| `security-container` | Container scan (Trivy) | Docker image build |
| `security-dast` | Dynamic testing (OWASP ZAP) | Staging deploy |
| `security-ai-review` | AI-powered code review | PR (selected) |
| `deploy-frontend` | Frontend deploy to Vercel | Merge to main |
| `deploy-landing` | Landing page deploy | Merge to main |

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Code changes (merged) | Squads | | Deployed application | Users |
| Infrastructure RFCs | Guild DevOps | | Pipeline status | VP Eng |
| Security policies | Head Security | | Monitoring dashboards | VP Eng + CEO |
| Performance requirements | Head Backend/Frontend | | Incident reports | All engineering |
| Budget constraints | CEO | | Cost reports | CEO + COO |

---

## Metrics

| Metric | Target |
|--------|--------|
| Deployment frequency | ≥ 2/week |
| Deployment success rate | ≥ 99% |
| Mean time to deploy (commit → production) | < 30 min |
| Mean time to recover (MTTR) | < 1 hour (P0) |
| Infrastructure cost | $0 in Phase 0-1, minimized after |
| Pipeline execution time | < 10 min |
| Uptime | ≥ 99.5% (Y1) → ≥ 99.9% (Y3) |

---

## $0 Infrastructure Strategy

| Layer | Free Tool | Paid Trigger |
|-------|-----------|-------------|
| Backend hosting | Railway free tier | > free tier limits |
| Frontend hosting | Vercel free tier | > free tier limits |
| CI/CD | GitHub Actions (2,000 min/mo free) | > free minutes |
| Monitoring | Grafana Cloud Free + Sentry Free | > free tier |
| Database | Railway PostgreSQL (free tier) | > storage/connection limits |
| Container registry | GitHub Container Registry (free) | N/A |
| DNS | Cloudflare Free | N/A |
| SSL | Let's Encrypt (free) | N/A |

---

## Operational Rules

1. **No manual deploys** — everything through CI/CD pipeline
2. **Infrastructure as Code** — Docker/Compose files version controlled
3. **Staging before production** — every change tested in staging first
4. **Rollback plan required** — every deploy has a documented rollback procedure
5. **Cost alarm** — alert if any service exceeds free tier
6. **Backup daily** — PostgreSQL automated backups with verified restores monthly
7. **On-call rotation** — defined rotation among DevOps + senior engineers
