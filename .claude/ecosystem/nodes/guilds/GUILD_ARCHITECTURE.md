# Guild: Architecture & Standards

> Horizontal guild ensuring architectural consistency and technical excellence across all squads.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L5 — Cross-Functional |
| **Type** | Guild (horizontal, serves all squads) |
| **Chair** | Software Architect (Lead) |
| **Members** | Tech Lead Backend, Tech Lead Frontend, representatives from each squad |

---

## Purpose

Define, maintain, and evolve **architectural patterns, coding standards, and technical guidelines** that apply across all squads. Govern tech debt. Own the ADR process.

---

## Composition

| Role | Responsibility |
|------|---------------|
| **Software Architect (Lead)** | Cross-squad architectural patterns, reviews, guidelines. Governs tech debt |
| **Tech Lead Backend** | FastAPI standards, service patterns, data schemas, Alembic migrations |
| **Tech Lead Frontend** | React/TypeScript standards, component system, Zustand stores, hooks |

---

## Responsibilities

| Area | Detail |
|------|--------|
| **ADR process** | Own the Architecture Decision Record lifecycle |
| **Code standards** | Define and update coding guidelines (Python, TypeScript) |
| **Design reviews** | Review architectural design docs from squads |
| **Tech debt** | Track, prioritize, and allocate tech debt work (≥ 10% sprint capacity) |
| **Cross-squad patterns** | Shared services, utility libraries, common abstractions |
| **Technology radar** | Evaluate new technologies quarterly |

---

## Outputs

| Output | Destination |
|--------|------------|
| ADRs | All squads |
| Coding guidelines | All developers |
| Design review feedback | Requesting squad |
| Tech debt backlog | VP Eng + Squads |
| Technology radar | VP Eng + CEO |

---

## Metrics

| Metric | Target |
|--------|--------|
| ADR coverage (significant decisions documented) | 100% |
| Coding standard compliance | ≥ 90% (linting pass rate) |
| Design review turnaround | < 3 business days |
| Tech debt ratio | ≤ 20% of total backlog |
| Knowledge sharing sessions | ≥ 2 per quarter |

---

## Cadence

| Activity | Frequency |
|----------|-----------|
| Guild meeting | Bi-weekly |
| Design reviews | As needed (≤ 3 day turnaround) |
| Tech debt review | Monthly |
| Technology radar update | Quarterly |
