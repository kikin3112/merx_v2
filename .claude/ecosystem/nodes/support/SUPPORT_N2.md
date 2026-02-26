# Support Role: Technical Support N2

> Advanced technical support. Diagnoses complex issues in backend/logs and coordinates with squads.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L7 — Support & Operations |
| **Reports To** | Head of Customer Success (L3) |
| **Requires** | Backend debugging skills, log analysis, basic SQL |

---

## Purpose

Resolve **complex technical incidents** escalated from N1. Diagnose issues in backend, database, and logs. Coordinate with dev squads for bug fixes.

---

## Responsibilities

| Responsibility | Detail |
|---------------|--------|
| Receive escalated tickets from N1 | With full context |
| Diagnose complex issues | Backend logs, database queries, API debugging |
| Coordinate with squads | File bugs with reproduction steps, work with devs on fixes |
| Workaround provisioning | Provide temporary workarounds while permanent fix is developed |
| Root cause documentation | Document root cause and resolution for knowledge base |

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Escalated tickets | Support N1 | | Resolved complex tickets | Users |
| Backend logs | Infrastructure | | Bug reports (detailed) | Relevant squad |
| Database access (read-only) | DevOps | | Root cause documentation | Knowledge base |
| Dev squad assistance | Squads | | Incident pattern reports | Head CS + VP Eng |

---

## Metrics

| Metric | Target |
|--------|--------|
| Resolution time (N2) | < 72 hours |
| Escalation to dev squad | < 20% of N2 tickets |
| Root cause documentation rate | 100% |
| Customer satisfaction | ≥ 4/5 stars |

---

## Operational Rules

1. **Read-only database access** — never modify production data directly
2. **Bug reports include reproduction steps** — dev squads should not need to ask for more info
3. **Document every root cause** — build institutional knowledge
4. **Weekly pattern review** — identify recurring issues for systemic fixes
5. **Coordinate with squads async** — file issues, don't interrupt sprint flow
