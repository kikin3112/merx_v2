# 02 — Governance & Decision-Making

> How decisions are made, who makes them, and how authority flows through the ecosystem.

---

## Decision-Making Framework

### Model: Flexible, Documented, Innovative

Our governance is NOT bureaucratic. It is:
- **Flexible**: Adapts to context. Strategic decisions ≠ tactical decisions.
- **Documented**: Every significant decision produces an artifact (ADR, RFC, decision log).
- **Innovative**: We favor experimentation over analysis paralysis.

### Decision Tiers

| Tier | Scope | Who Decides | Mechanism | Documentation |
|------|-------|------------|-----------|---------------|
| **T1 — Strategic** | Company direction, major pivots, partnerships, budget > $10k impact | CEO/CTO | Consultative (gathers input, decides) | Written decision memo |
| **T2 — Architectural** | Tech stack changes, system design, security policies | Architecture Committee | RFC → discuss → decide | ADR (Architecture Decision Record) |
| **T3 — Product** | Roadmap priorities, feature scope, module sequencing | CPO + Product Committee | RICE scoring + Design Thinking | Product brief |
| **T4 — Squad-Level** | Implementation approach, sprint scope, tech choices within guardrails | Squad autonomously | Informed Captain model | Sprint notes |
| **T5 — Individual** | Code style within standards, task ordering, personal workflow | Individual contributor | Full autonomy | None required |

### The "Informed Captain" Model

For T3-T5 decisions:
1. One person is the **captain** (DRI — Directly Responsible Individual)
2. The captain **gathers context** from relevant stakeholders
3. The captain **decides and documents** the reasoning
4. Others can **disagree and commit** — once decided, all execute
5. If the decision fails, it's a **learning event**, not a blame event

---

## RACI Framework

Applied to recurring activities. Each node manual specifies its RACI position for relevant activities.

| Letter | Meaning | Rule |
|--------|---------|------|
| **R** (Responsible) | Does the work | Exactly 1 per activity |
| **A** (Accountable) | Owns the outcome, has final approval | Exactly 1 per activity |
| **C** (Consulted) | Provides input before decision | As many as needed |
| **I** (Informed) | Notified after decision/action | As many as needed |

### Cross-Ecosystem RACI Matrix

| Activity | CEO | CPO | VP Eng | COO | Squad | Guild |
|----------|-----|-----|--------|-----|-------|-------|
| Company strategy | A | C | C | C | I | I |
| Product roadmap | C | A | C | C | R | I |
| Architecture decisions | I | C | A | I | C | R |
| Sprint planning | I | I | C | I | A/R | C |
| Security policy | A | I | C | I | I | R |
| Release go/no-go | I | C | A | I | R | C |
| Customer onboarding | I | I | I | A | I | I |
| Incident response | I | I | A | C | R | R |

---

## Transparency Rules

### Default: Need-to-Know with Generous Defaults

| Category | Visibility | Rationale |
|----------|-----------|-----------|
| Product roadmap | All org | Everyone should know where we're going |
| Technical architecture | All engineering + product | Context enables better decisions |
| Sprint progress | All org | Transparency breeds accountability |
| Customer feedback/NPS | All org | Customer obsession requires visibility |
| Financial details | CEO + COO + VPs | Sensitive; shared quarterly as aggregate |
| HR/personnel | Manager + HR | Privacy protection |
| Security vulnerabilities | SecOps + VP Eng + CEO | Responsible disclosure |
| Salary/compensation | Individual + HR | Privacy |

### Documentation Standards

Every significant decision must produce:
1. **What** was decided
2. **Why** (context, alternatives considered, trade-offs)
3. **Who** made it (DRI)
4. **When** it was made
5. **Expiry/Review date** (decisions are not permanent)

### ADR (Architecture Decision Record) Template

```
# ADR-[number]: [Title]
- Status: [Proposed | Accepted | Deprecated | Superseded]
- Date: [YYYY-MM-DD]
- DRI: [Name/Role]
- Context: [Why this decision is needed]
- Options Considered: [List with pros/cons]
- Decision: [What was chosen and why]
- Consequences: [Expected impact, risks, trade-offs]
- Review Date: [When to revisit]
```

---

## Authority Boundaries

### What Each Level CAN Do Without Escalation

| Level | Autonomous Authority |
|-------|---------------------|
| **CEO/CTO** | Any decision. Can override any other level. |
| **VP (L2)** | Decisions within their pillar up to T2 scope. Budget allocation within approved limits. Hiring/firing within their org. |
| **Head (L3)** | Technical decisions within their domain. Sprint priorities within roadmap guardrails. Tool selection within budget. |
| **Squad (L4)** | Implementation decisions. Internal process. Task distribution. |
| **Individual** | Code approach within standards. Personal workflow. Learning time allocation. |

### Escalation Triggers (MUST Escalate)

1. Decision impacts more than one squad/pillar
2. Decision creates irreversible consequences
3. Decision involves security/compliance risk
4. Decision requires budget not previously approved
5. Decision changes committed timelines by > 1 sprint
6. Disagreement persists after 48 hours

---

## Governance Cadence

| Meeting | Frequency | Duration | Attendees | Output |
|---------|-----------|----------|-----------|--------|
| All-Hands | Monthly | 60 min | Everyone | Company update, roadmap progress, metrics |
| VP Sync | Weekly | 30 min | CEO + VPs | Cross-pillar alignment, blockers |
| Architecture Committee | Bi-weekly | 60 min | See committees/ | ADRs, tech debt review |
| Product Committee | Weekly | 45 min | See committees/ | Roadmap updates, RICE reviews |
| Security Committee | Monthly | 60 min | See committees/ | Vulnerability review, policy updates |
| Release Committee | Per sprint | 30 min | See committees/ | Go/No-Go decision |
