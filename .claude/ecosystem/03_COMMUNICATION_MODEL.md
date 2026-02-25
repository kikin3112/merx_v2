# 03 — Communication Model

> How information flows through the ecosystem. Async-first, documentation-heavy, meetings-last.

---

## Philosophy: Async-First

Inspired by GitLab's handbook-first culture:
- **Write it down** before saying it
- **Document decisions** where they'll be found (not buried in chat)
- **Meetings are expensive** — only for decisions that need real-time discussion
- **Everyone's time zone matters** — async enables global-ready operations

---

## Communication Channels

| Channel | Use For | NOT For |
|---------|---------|---------|
| **Git Issues/PRs** | Technical decisions, code review, bugs, feature specs | General discussion, social chat |
| **Documentation (Markdown)** | ADRs, RFCs, specs, runbooks, meeting notes | Real-time updates |
| **Project Board** | Sprint tracking, task status, backlog management | Detailed discussion |
| **Chat (async)** | Quick questions, social, ephemeral coordination | Decisions (move to docs) |
| **Video Call** | Conflict resolution, brainstorming, 1:1s, complex alignment | Status updates, FYIs |
| **Email** | External communication, formal notices | Internal coordination |

### The 24-Hour Rule
- Any question asked async must receive a response within **24 business hours**
- If you can't answer, acknowledge receipt and give an ETA
- Silence is not an acceptable response

---

## Communication Protocols by Level

| Level | Primary Channel | Cadence | Format |
|-------|----------------|---------|--------|
| L1 (CEO) → L2 (VPs) | Weekly VP sync + async docs | Weekly | Agenda doc shared 24h before |
| L2 (VPs) → L3 (Heads) | 1:1 async updates + bi-weekly sync | Bi-weekly | Written status update |
| L3 (Heads) → L4 (Squads) | Sprint artifacts + daily async standups | Daily | Written standup format |
| L4 (Squads) → L5 (Guilds) | Cross-squad channels + guild meetings | Per-need | RFC or discussion thread |
| All → All | Show & Tell, All-Hands | Bi-weekly / Monthly | Live demo + recorded |

---

## Written Communication Standards

### Status Updates (Async Standup Format)
```
**[Name] — [Date]**
✅ Done: [What I completed]
🔄 Today: [What I'm working on]
🚧 Blocked: [What I need help with] (tag the person)
```

### RFC (Request for Comments) Format
```
# RFC: [Title]
- Author: [Name]
- Date: [YYYY-MM-DD]
- Status: [Draft | Open for Comments | Decided]
- Deadline for comments: [Date]

## Problem
[What problem does this solve?]

## Proposal
[Your proposed solution]

## Alternatives Considered
[Other options and why they were rejected]

## Open Questions
[Things you need input on]
```

### Meeting Notes Format
```
# [Meeting Name] — [Date]
**Attendees**: [List]
**Decisions Made**: [Numbered list]
**Action Items**: [Who | What | By When]
**Open Items**: [Carried to next meeting]
```

---

## Meeting Rules

1. **No agenda, no meeting** — every meeting has a written agenda shared 24h before
2. **No decision needed? It's an email** — don't schedule meetings for information sharing
3. **15 or 30 minutes default** — 60 min only for workshops/brainstorms
4. **Notes are mandatory** — published within 4 hours of meeting end
5. **Decisions in meetings are binding** — if you weren't there, the decision stands (read the notes)
6. **Camera optional, engagement mandatory** — participate actively or excuse yourself

---

## Recurring Rituals Calendar

| Ritual | Day | Time | Duration | Owner |
|--------|-----|------|----------|-------|
| Async Standup | Daily | Written by 10am | N/A | Each IC |
| Sprint Planning | Monday (sprint start) | 10:00 | 60 min | Scrum Master |
| VP Sync | Tuesday | 09:00 | 30 min | CEO |
| Product Committee | Wednesday | 10:00 | 45 min | CPO |
| Architecture Committee | Bi-weekly Thursday | 14:00 | 60 min | VP Eng |
| Show & Tell | Bi-weekly Friday | 15:00 | 45 min | Rotating squad |
| Sprint Retro | Last Friday of sprint | 14:00 | 45 min | Scrum Master |
| All-Hands | First Monday of month | 11:00 | 60 min | CEO |
| Failure Friday | Last Friday of month | 16:00 | 30 min | Rotating |
| Security Committee | First Wednesday of month | 14:00 | 60 min | Head SecOps |

---

## Information Flow Diagram

```
                CEO/CTO
                   │
          ┌────────┼────────┐
          │        │        │
         CPO    VP Eng    COO
          │        │        │
     ┌────┴────┐   │   ┌───┴───┐
     │         │   │   │       │
   Head      Head  │  Head   Head
   Product   UX    │  Sales  CS
     │         │   │   │       │
     └────┬────┘   │   └───┬───┘
          │        │       │
    ┌─────┴────────┴───────┴─────┐
    │        SQUAD LAYER          │
    │  (cross-functional teams)   │
    │  Squads communicate         │
    │  horizontally via guilds    │
    └─────────────┬──────────────┘
                  │
    ┌─────────────┴──────────────┐
    │        GUILD LAYER          │
    │  (horizontal standards)     │
    │  Architecture │ DevOps      │
    │  Security │ UX │ Data       │
    └────────────────────────────┘
```

**Vertical flow**: Strategy → Execution (top-down), Feedback → Learning (bottom-up)
**Horizontal flow**: Cross-squad coordination via guilds, joint demos, shared channels

---

## Escalation Communication Protocol

| Severity | Response Time | Channel | Who Is Notified |
|----------|--------------|---------|-----------------|
| **P0 — Critical** (production down) | 15 min | Immediate alert + war room | VP Eng, Head DevOps, on-call squad |
| **P1 — High** (major feature broken) | 2 hours | Async thread + tag DRI | Head of relevant squad + VP Eng |
| **P2 — Medium** (degraded experience) | 24 hours | Issue tracker | Squad lead |
| **P3 — Low** (minor bug, cosmetic) | Next sprint | Issue tracker | Squad backlog |
