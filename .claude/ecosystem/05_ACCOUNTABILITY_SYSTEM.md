# 05 — Accountability System

> How we measure performance, track progress, and learn from outcomes.

---

## Philosophy

Accountability is not punishment — it is **clarity of ownership** and **a system for learning**. Inspired by Toyota's respect-for-people principle: we hold the system accountable, not just individuals.

---

## Performance Metrics by Level

### L1 — CEO/CTO
| Metric | Target | Cadence |
|--------|--------|---------|
| Active tenant growth | Per horizon targets (see 04) | Quarterly |
| Company NPS | ≥ targets per horizon | Quarterly |
| Runway / financial health | ≥ 6 months runway | Monthly |
| Strategic OKR completion | ≥ 70% | Quarterly |

### L2 — VPs
| Metric | Target | Cadence |
|--------|--------|---------|
| Pillar OKR completion | ≥ 70% | Quarterly |
| Cross-pillar alignment score | Measured via peer feedback | Quarterly |
| Team health (eNPS) | ≥ 50 | Quarterly |
| Budget adherence | Within ±10% | Monthly |

### L3 — Heads
| Metric | Target | Cadence |
|--------|--------|---------|
| Domain-specific KPIs | Per node manual | Monthly |
| Squad velocity trend | Stable or improving | Per sprint |
| Quality metrics (bug escape rate) | Decreasing trend | Per sprint |
| Team member growth | 1 skill growth per person per quarter | Quarterly |

### L4 — Squads
| Metric | Target | Cadence |
|--------|--------|---------|
| Sprint commitment reliability | ≥ 80% completion | Per sprint |
| Cycle time (idea → production) | Decreasing trend | Per sprint |
| Bug escape rate | < 5% of stories | Per sprint |
| Code review turnaround | < 24 hours | Weekly |

### L5 — Guilds
| Metric | Target | Cadence |
|--------|--------|---------|
| Standard adoption rate | ≥ 90% compliance | Monthly |
| Cross-squad improvement initiatives | ≥ 1 per quarter | Quarterly |
| Knowledge sharing sessions delivered | ≥ 2 per quarter | Quarterly |

---

## Review Mechanisms

### 1. Sprint Retrospective (Every Sprint)
- **Who**: Squad + Scrum Master
- **Focus**: What went well? What didn't? What will we improve?
- **Output**: ≤ 3 action items with DRI and deadline
- **Rule**: Past action items reviewed FIRST

### 2. Monthly 1:1 (Manager ↔ Report)
- **Format**: Written async prep + 30-min sync
- **Topics**: Progress against OKRs, blockers, growth goals, feedback exchange
- **Output**: Updated growth plan document

### 3. Quarterly OKR Review (Per Level)
- **Format**: Written self-assessment + team review
- **Scoring**: 0.0–1.0 (0.7 = healthy stretch target met)
- **Three questions**: What did we achieve? What did we learn? What will we change?

### 4. Annual Performance Review
- **Format**: Self-review + peer feedback (360°) + manager assessment
- **Calibration**: VPs calibrate across their pillar
- **Output**: Growth plan for next year + compensation review

---

## Learning Loops

| Loop | Trigger | Output | Owner |
|------|---------|--------|-------|
| **Sprint Retro** | End of every sprint | Action items | Scrum Master |
| **Post-Mortem** | Any P0/P1 incident | Post-mortem doc + systemic fixes | DRI of incident |
| **Kaizen Log** | Daily (ongoing) | Micro-improvement backlog | Every IC |
| **Quarterly Review** | End of quarter | OKR scorecard + learnings | Each level |
| **Annual Review** | End of year | Strategy adjustment + team restructuring | CEO + VPs |

---

## DRI (Directly Responsible Individual) System

Every significant work item has exactly ONE DRI:
- **The DRI is not necessarily the doer** — they are the person accountable for the outcome
- **DRI is public** — everyone knows who owns what
- **DRI can delegate** — but cannot delegate accountability
- **DRI rotates** — to prevent knowledge silos and burnout

### DRI Assignment Rules
1. Assigned at sprint planning (squad-level work)
2. Assigned at committee meetings (cross-squad decisions)
3. Assigned by VP (pillar-level initiatives)
4. Self-assigned (Kaizen improvements, bug fixes)

---

## Failure Handling

| Situation | Response | NOT Acceptable |
|-----------|----------|----------------|
| Missed sprint goal | Retro → root cause → adjust next sprint | Blame individuals |
| Bug escape to production | Post-mortem → systemic fix | "Who wrote this code?" |
| Missed OKR | Analyze → learn → adjust target or approach | Punitive action |
| Repeated same failure | Escalate to process review | Ignore the pattern |
| Innovation experiment fails | Celebrate the learning, document insights | "I told you so" |
