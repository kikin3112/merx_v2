# 04 — Strategic Objectives

> Three-horizon strategic plan with measurable North Star metrics for chandelierp.

---

## North Star Metrics (Composite)

| Metric | Definition | Target (Year 1) | Target (Year 3) | Target (Year 5) |
|--------|-----------|-----------------|-----------------|-----------------|
| **Active Tenants** | Tenants with ≥1 active user in last 30 days | 50 | 500 | 5,000 |
| **NPS** | Net Promoter Score from quarterly surveys | ≥ 40 | ≥ 55 | ≥ 70 |
| **DAU/MAU Ratio** | Daily active / Monthly active users | ≥ 30% | ≥ 45% | ≥ 60% |

---

## Horizon 1 — Year 1: Product-Market Fit

**Theme**: *"Build something 50 businesses can't live without."*

| Objective | Key Result | Owner |
|-----------|-----------|-------|
| Validate core ERP modules | 5 modules in production (Sales, Inventory, Accounting, CRM, Tenants) | CPO |
| Acquire first paying tenants | 50 active tenants | COO |
| Achieve baseline NPS | NPS ≥ 40 | Head CS |
| Zero critical security incidents | 0 P0 security events | Head SecOps |
| Establish PLG funnel | Self-serve signup → onboarding in < 15 min | Head Product |
| Build engineering foundation | 80% test coverage on core modules | VP Eng |

---

## Horizon 2 — Year 3: Scale & Depth

**Theme**: *"Become the default ERP for Colombian micro/SMEs."*

| Objective | Key Result | Owner |
|-----------|-----------|-------|
| Market penetration | 500 active tenants across 5+ industries | COO |
| Module completeness | 10+ ERP modules, integrated billing with DIAN | CPO |
| Platform reliability | 99.9% uptime SLA | Head DevOps |
| User engagement | DAU/MAU ≥ 45% | Head Product |
| Revenue sustainability | MRR covering operating costs | CEO |
| LATAM readiness | i18n framework + 2 pilot tenants outside Colombia | CPO |

---

## Horizon 3 — Year 5: Market Leadership

**Theme**: *"The ERP that grows with you — from 1 employee to 200."*

| Objective | Key Result | Owner |
|-----------|-----------|-------|
| Regional leader | 5,000 active tenants across LATAM | CEO |
| AI-powered ERP | Demand forecasting, anomaly detection, smart suggestions live | VP Eng |
| Ecosystem/marketplace | 20+ third-party integrations (payment, logistics, tax) | CPO |
| Enterprise-grade security | SOC2 Type II certified | Head SecOps |
| Brand recognition | Top 3 in "best ERP for SMEs LATAM" rankings | COO |
| Self-sustaining growth | 60%+ organic/viral acquisition | Head Sales |

---

## Market Strategy

### Target Segments

| Segment | Size | Priority | Approach |
|---------|------|----------|----------|
| **Micro-businesses** (1-10 employees) | High volume, low ARPU | Primary (Y1-Y2) | PLG: free tier, self-serve, templates |
| **Small businesses** (10-50 employees) | Medium volume, medium ARPU | Primary (Y1-Y3) | PLG + guided onboarding |
| **Medium businesses** (50-200 employees) | Lower volume, higher ARPU | Secondary (Y2-Y5) | PLG + consultative sales |

### Geographic Strategy

```
Year 1: Colombia (focus cities: Bogotá, Medellín, Cali, Barranquilla)
Year 2-3: Colombia nationwide + pilot in Ecuador, Perú
Year 3-5: LATAM expansion (México, Chile, Argentina)
```

### Go-to-Market: Product-Led Growth (PLG)

| Stage | Mechanism | Metric |
|-------|-----------|--------|
| **Awareness** | Content marketing, SEO, community, referrals | Website visitors |
| **Acquisition** | Free self-serve signup, pre-built industry templates | Signups/week |
| **Activation** | Guided onboarding < 15 min, first invoice in < 30 min | Time-to-value |
| **Retention** | Feature depth, integrations, customer success | Monthly churn < 5% |
| **Revenue** | Freemium → paid tiers, module-based upsell | Conversion rate |
| **Referral** | In-app referral program, "Powered by MERX" badge | Viral coefficient |

---

## Budget Philosophy

**"$0 until proven necessary."**

| Category | Approach | Free Tools |
|----------|----------|-----------|
| Hosting | Start free tiers, scale on revenue | Railway (free tier), Vercel (free) |
| CI/CD | GitHub Actions free minutes | GitHub Actions |
| Monitoring | Free-tier observability | Grafana Cloud Free, Sentry Free |
| Security | Open-source scanners | Semgrep, Gitleaks, Trivy, Bandit |
| Design | Open-source design tools | Figma (free), Penpot |
| Communication | Free-tier tools | GitHub Discussions, Discord/Slack free |
| Analytics | Self-hosted or free-tier | PostHog (free), Umami |

---

## OKR Cadence

| Level | OKR Cycle | Review |
|-------|-----------|--------|
| Company | Annual (set in Q4) | Quarterly review |
| Pillar/VP | Quarterly | Monthly check-in |
| Squad | Quarterly (aligned to company) | Sprint retro includes OKR check |
| Individual | Quarterly (aligned to squad) | 1:1 with manager |
