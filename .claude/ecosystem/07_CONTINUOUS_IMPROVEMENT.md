# 07 — Continuous Improvement (Kaizen System)

> Every day, make something 1% better. Small improvements compound into extraordinary results.

---

## Philosophy: Kaizen (改善)

From Toyota Production System: **continuous, incremental improvement involving everyone**.

Our interpretation:
- Improvement is **everyone's job**, not a separate initiative
- **Small daily improvements** beat big annual overhauls
- **Measure → Improve → Measure** — data-driven, not feeling-driven
- **Respect for people** — improvement respects existing work and context

---

## Improvement Mechanisms

### 1. Daily Kaizen (Individual Level)

- Every team member is empowered to make small improvements without approval
- Examples: fix a typo in documentation, refactor 10 lines, improve an error message
- **Rule**: If it takes < 30 minutes and doesn't break anything, just do it
- **Log**: Optional brief note in the Kaizen channel/log

### 2. Sprint Retrospective (Squad Level)

| Element | Detail |
|---------|--------|
| Frequency | End of every sprint (bi-weekly) |
| Duration | 45 minutes max |
| Format | What went well? / What didn't? / What will we change? |
| Output | ≤ 3 action items with DRI and deadline |
| Follow-up | Action items reviewed FIRST at next retro |
| Facilitator | Scrum Master (rotated for variety) |

### 3. Blameless Post-Mortems (Incident-Triggered)

**Triggered by**: Any P0 or P1 incident.

**Format**:
```
# Post-Mortem: [Incident Title]
- Date: [When it happened]
- Duration: [How long it lasted]
- Impact: [Users/tenants affected, revenue impact]
- DRI: [Who led the response]

## Timeline
[Minute-by-minute account of what happened]

## Root Cause
[The systemic cause, NOT "human error"]

## Contributing Factors
[What made it worse or delayed resolution]

## Action Items
[Systemic fixes to prevent recurrence]
| Action | DRI | Deadline | Status |
|--------|-----|----------|--------|

## Lessons Learned
[What we will do differently]
```

**Rules**:
- NO blame. Ever. "Human error" is not a root cause — the system that allowed it is.
- Published to all of engineering within 48 hours
- Action items tracked until completion
- Review in next Security/Architecture Committee

### 4. Monthly Kaizen Review (Squad Level)

- Each squad reviews their Kaizen log
- Identify patterns: what types of improvements are most common? Where are the systemic issues?
- Select 1 "deep improvement" to tackle in the next month
- Present findings at Show & Tell

### 5. Quarterly Process Audit (VP Level)

- VPs review cross-pillar processes for waste (Muda)
- Categories of waste (from Lean):
  - **Waiting** — delays between handoffs
  - **Overprocessing** — unnecessary approvals or documentation
  - **Defects** — bugs, rework, miscommunication
  - **Motion** — context switching, tool friction
  - **Inventory** — unfinished PRs, stale branches, untriaged bugs
- Output: Process improvement OKRs for next quarter

---

## Improvement Backlog

Every squad maintains an **Improvement Backlog** alongside their feature backlog:

| Priority | Improvement | Type | Effort | Impact |
|----------|------------|------|--------|--------|
| P1 | Automate deploy smoke tests | Process | 2 days | High — reduces manual verification |
| P2 | Add TypeScript strict mode to 3 modules | Quality | 3 days | Med — catches more bugs |
| P3 | Document onboarding flow for new devs | Knowledge | 1 day | Med — reduces ramp-up time |

**Rule**: ≥ 10% of sprint capacity is reserved for improvements (process, quality, developer experience).

---

## Feedback Channels

| Channel | From → To | Purpose |
|---------|-----------|---------|
| Sprint Retro | Squad → Squad | Process improvement |
| 1:1 Meetings | Individual ↔ Manager | Personal growth + feedback |
| Peer Reviews | IC ↔ IC | Code quality + skill sharing |
| User Interviews | Customers → Product | Feature quality + UX improvement |
| PQRS Module | End Users → Support → Product | Bug reports + feature requests |
| Failure Friday | Anyone → Everyone | Celebrate learning from mistakes |
| Anonymous Survey | Anyone → Leadership | Unfiltered organizational feedback |

---

## Improvement Metrics

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Kaizen improvements/month/squad | Improvement velocity | ≥ 5 |
| Retro action item completion rate | Follow-through | ≥ 80% |
| Post-mortem publication time | Learning speed | < 48 hours |
| Time between recurrence of same issue | Systemic fix effectiveness | Increasing |
| Developer experience score (DX) | Internal tooling quality | Quarterly survey, improving trend |
| Improvement backlog freshness | Items acted on vs stale | < 30 days avg age |
