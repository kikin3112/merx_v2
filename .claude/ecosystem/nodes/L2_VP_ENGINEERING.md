# L2 — VP of Engineering (VP Eng)

> Owner of HOW we build. Guardian of technical excellence, system reliability, and engineering culture.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L2 — Strategic Leadership |
| **Reports To** | CEO / CTO (L1) |
| **Direct Reports** | Head of Backend (L3), Head of Frontend (L3), Head of QA (L3), Head of DevOps (L3), Head of Security (L3) |
| **Pillar** | Engineering |
| **Model** | Netflix: Freedom & Responsibility + Chaos Engineering |
| **Reference** | Netflix (engineering culture, chaos engineering), Google (Design Docs, eng levels) |

---

## Purpose

Build and maintain the **technical systems** that power chandelierp with **extreme reliability**, **high velocity**, and **engineering excellence**. Create an environment where engineers have **freedom to innovate** and **responsibility for outcomes**.

---

## Responsibilities

| Area | Responsibility |
|------|---------------|
| **Architecture** | Own high-level system architecture. Chair Architecture Committee. Final say on T2 technical decisions |
| **Quality** | Set and enforce code quality standards, review processes, testing strategy |
| **Reliability** | Own system uptime, performance SLAs, incident response |
| **Tech Debt** | Manage tech debt budget (≥ 10% of sprint capacity dedicated to improvement) |
| **Talent** | Hire, grow, and retain engineering talent. Define eng levels and career ladders |
| **Delivery** | Ensure squads deliver sprint commitments with consistent velocity |
| **Security** | Oversee SecOps integration in development pipeline (DevSecOps) |
| **Innovation** | Sponsor engineering innovation (hack weeks, tool improvements, chaos experiments) |

---

## Technical Stack Governance

| Layer | Technology | VP Eng Authority |
|-------|-----------|-----------------|
| **Backend** | FastAPI, Python, SQLAlchemy, Alembic | Approves changes |
| **Frontend** | React, TypeScript, Vite, Zustand | Approves changes |
| **Database** | PostgreSQL | Approves schema changes |
| **Infra** | Docker, Railway, Vercel, Nginx | Approves vendor changes |
| **CI/CD** | GitHub Actions (9 workflows) | Owns pipeline strategy |
| **Security** | Semgrep, Gitleaks, Bandit, Trivy, OWASP ZAP | Approves policy changes |

---

## Engineering Standards

| Standard | Requirement |
|----------|-------------|
| Code review | All PRs require ≥ 1 approval. Critical paths require 2 |
| Design docs | Required for any work > 1 sprint or cross-squad |
| Testing | Unit + integration required. E2E for critical paths |
| Coverage target | ≥ 80% on core modules |
| Documentation | All public APIs documented. README per module |
| Branch strategy | Feature branches → PR → main. No direct commits to main |
| Deployment | Blue-green or canary. No big-bang deployments |

---

## Inputs

| Input | Source | Frequency |
|-------|--------|-----------|
| Product roadmap & sprint priorities | CPO | Per sprint |
| Company strategy & OKRs | CEO | Quarterly |
| Architecture proposals (RFCs) | Guilds + Squads | As needed |
| Incident reports | DevOps / On-call | As needed |
| Security scan results | Head SecOps | Weekly |
| Squad velocity reports | Scrum Master | Per sprint |

## Outputs

| Output | Destination | Frequency |
|--------|------------|-----------|
| Engineering health dashboard | CEO + CPO | Weekly |
| ADRs (Architecture Decision Records) | All engineering | As needed |
| Release readiness assessment | Release Committee | Per sprint |
| Tech debt status report | CEO + Architecture Committee | Monthly |
| Engineering OKR scorecard | CEO | Quarterly |
| Incident post-mortems | All org | Per incident |

---

## Metrics

| Metric | Target | Cadence |
|--------|--------|---------|
| System uptime | ≥ 99.5% (H1) → ≥ 99.9% (H2) | Monthly |
| Deployment frequency | ≥ 2/week | Weekly |
| Mean time to recover (MTTR) | < 1 hour for P0 | Per incident |
| Code review turnaround | < 24 hours | Weekly |
| Test coverage (core) | ≥ 80% | Per sprint |
| Sprint velocity stability | ±15% variance | Per sprint |
| Tech debt ratio | ≤ 20% of backlog | Monthly |
| Engineering satisfaction (eNPS) | ≥ 50 | Quarterly |

---

## Netflix-Inspired Practices

| Practice | How We Apply It |
|----------|----------------|
| **Freedom & Responsibility** | Engineers choose their approach within guardrails. No micromanagement |
| **Context, Not Control** | VP Eng shares context (goals, constraints, data). Teams decide implementation |
| **Chaos Engineering** | Quarterly resilience testing in staging. Simulate failures proactively |
| **Highly Aligned, Loosely Coupled** | Clear north stars, autonomous squads |
| **Talent Density** | Prefer fewer, excellent engineers over many average ones |

---

## Operational Rules

1. **Design docs before complex code** — write first, build second
2. **Post-mortems are mandatory for P0/P1** — blameless, published within 48h
3. **Tech debt has a budget** — ≥ 10% of sprint capacity, non-negotiable
4. **Security gates in CI/CD** — no deploy without passing security scans
5. **Chaos experiments quarterly** — break things in staging to build resilience
6. **Open-source by default** — use free tools. Propose paid tools only with ROI analysis
7. **Weekly engineering digest** — async summary of what shipped, what's coming, what's blocked

---

## Boundaries

- Does NOT decide WHAT to build (that's CPO)
- Does NOT manage customer relationships (that's COO)
- Does NOT approve product roadmap (that's CPO + CEO)
- Does NOT handle commercial pricing (that's COO)
