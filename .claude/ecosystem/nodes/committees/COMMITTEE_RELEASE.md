# Committee: Release

> Go/No-Go decision body for every production release.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L6 — Governance |
| **Frequency** | Per sprint (bi-weekly) |
| **Duration** | 30 min |
| **Chair** | VP Engineering |
| **Members** | VP Eng, Head QA, DevOps Lead, Product Owners (releasing squads) |

---

## Purpose

Validate **quality, security, and readiness** of each release before deployment to production. Issue **Go/No-Go** decision.

---

## Release Checklist

| Check | Owner | Required |
|-------|-------|----------|
| All tests pass (unit + integration + E2E) | Head QA | ✅ |
| Security scans pass (all 6 pipelines) | Head SecOps | ✅ |
| No open P0/P1 bugs in release scope | Head QA | ✅ |
| Performance benchmarks met | Head Backend/Frontend | ✅ |
| Staging tested and verified | DevOps | ✅ |
| Release notes drafted | Head Product | ✅ |
| Rollback plan documented | DevOps | ✅ |
| Database migration tested | DBA | ✅ (if applicable) |
| Product Owner sign-off | POs | ✅ |

---

## Process

```
1. Release candidate deployed to staging (automated)
2. QA runs final regression suite
3. Security scans executed on staging
4. Release Committee meets: checklist review
5. Decision: GO → deploy to production | NO-GO → document blockers, fix in next sprint
6. Post-deploy: smoke tests + monitoring for 2 hours
```

---

## Outputs

| Output | Destination | Frequency |
|--------|------------|-----------|
| Go/No-Go decision | DevOps + All engineering | Per sprint |
| Release blockers (if No-Go) | Relevant squads | Per sprint |
| Release notes (published) | All org + users | Per release |
| Post-deploy status | VP Eng | Within 2 hours of deploy |

---

## Rules

1. **All checklist items must pass** — any red = No-Go
2. **No exceptions for security** — security gate is non-negotiable
3. **No Friday deploys** — deployments only Mon-Thu to allow monitoring
4. **Rollback authority** — DevOps can rollback without committee approval if monitoring detects issues
