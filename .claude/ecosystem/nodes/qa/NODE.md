# L3 — Head of QA & Testing

> Guardian of quality. No release ships without QA approval.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L3 — Functional Direction |
| **Reports To** | VP Engineering (L2) |
| **Pillar** | Core Engineering |
| **Direct Reports** | QA Engineers in each squad (dotted line) |

---

## Purpose

Define and enforce the **testing strategy** across all ERP modules. Own quality gates, test automation, and regression prevention.

---

## Responsibilities

| Area | Responsibility |
|------|---------------|
| **Test strategy** | Define unit, integration, E2E, and security testing standards |
| **Automation** | Build and maintain test automation framework |
| **Quality gates** | Define release criteria; member of Release Committee |
| **Regression** | Ensure regression suites run on every PR and release |
| **Coverage** | Track and improve test coverage across modules |
| **QA coaching** | Mentor QA engineers embedded in squads |
| **Bug triage** | Lead bug triage process, classify severity, track resolution |

---

## Testing Pyramid

```
         ┌──────────┐
         │   E2E    │  < 10% — Critical user flows only
         ├──────────┤
         │ Integra- │  ~ 30% — API, DB, cross-module
         │  tion    │
         ├──────────┤
         │   Unit   │  ≥ 60% — Functions, services, utilities
         └──────────┘
```

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Feature specs + acceptance criteria | Head Product | | Test plans | Squads |
| Code changes (PRs) | Developers | | Test results / reports | Release Committee |
| Security scan results | Head Security | | Bug reports | Squad backlogs |
| Deployment plan | DevOps | | Coverage reports | VP Eng |

---

## Metrics

| Metric | Target |
|--------|--------|
| Test coverage (overall) | ≥ 80% |
| Bug escape rate (bugs found in production) | < 5% of stories |
| Regression suite pass rate | ≥ 98% |
| Test automation ratio | ≥ 70% automated |
| Bug fix turnaround (P0/P1) | < 24 hours |
| Release quality score | ≥ 90% (stories passing on first deploy) |

---

## Operational Rules

1. **No release without QA sign-off** — Release Committee requires QA green status
2. **Regression suite on every PR** — automated, mandatory, blocking
3. **Bug bash per release** — dedicated session for manual exploratory testing
4. **P0 bugs = stop the line** — team drops everything to fix production-breaking bugs
5. **Test-first for bugs** — every bug fix includes a test that reproduces the issue
6. **Coverage never decreases** — PRs that decrease coverage require Head QA justification
