# Committee: Architecture

> Strategic technical decision-making body for high-impact architectural choices.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L6 — Governance |
| **Frequency** | Bi-weekly |
| **Duration** | 60 min |
| **Chair** | VP Engineering |
| **Members** | VP Eng, Software Architect (Lead), Tech Leads (Backend + Frontend), Head SecOps |

---

## Purpose

Make **T2 architectural decisions** with cross-squad impact. Approve or reject RFCs and ADRs. Review tech debt strategy.

---

## Scope of Decisions

| Decides | Does NOT Decide |
|---------|----------------|
| Technology stack changes | Sprint-level implementation |
| Cross-squad data model changes | Individual code style |
| Security architecture patterns | Feature prioritization |
| Infrastructure scaling strategy | Budget allocation |
| ADR approval/rejection | Hiring decisions |
| Tech debt prioritization | Product roadmap |

---

## Process

```
1. RFC submitted (async, 3+ days before meeting)
2. Members review and comment async
3. Meeting: author presents (10 min), discussion (20 min), decision (10 min)
4. Decision recorded as ADR
5. ADR published to all engineering
```

---

## Outputs

| Output | Destination | Frequency |
|--------|------------|-----------|
| ADRs | All engineering | Per meeting |
| Tech debt priority list | VP Eng + Squads | Monthly |
| Technology radar updates | All org | Quarterly |
| Architecture risk register | CEO + VP Eng | Quarterly |

---

## Rules

1. **Quorum**: ≥ 3 of 5 members required for decisions
2. **Veto**: VP Eng has single veto power (rarely used, must document reasoning)
3. **Async participation**: Members who can't attend submit written position
4. **Decision durability**: ADRs stand until formally superseded
