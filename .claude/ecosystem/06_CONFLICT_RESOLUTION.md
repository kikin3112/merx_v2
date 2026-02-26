# 06 — Conflict Resolution

> Every healthy system has conflicts. What matters is how they are resolved — fast, fair, and forward-looking.

---

## Conflict Tiers

| Tier | Description | Mechanism | Timeline |
|------|------------|-----------|----------|
| **C1 — Disagreement** | Two people have different opinions on approach | Direct conversation between parties | Resolve within 24h |
| **C2 — Persistent Disagreement** | Direct conversation didn't resolve it | Bring to squad lead / chapter lead | Resolve within 48h |
| **C3 — Cross-Squad Conflict** | Two squads/guilds disagree on ownership/approach | Arbitration Committee convened | Resolve within 1 week |
| **C4 — Strategic Conflict** | Fundamental disagreement on direction/priorities | VP-level mediation → CEO final call | Resolve within 2 weeks |

---

## Arbitration Committee

**Composition**: One representative from each pillar involved + one neutral party (typically Scrum Master or Agile Coach).

### Process

```
1. SUBMIT: Either party submits a written conflict brief (max 1 page)
   - What is the conflict?
   - What has been tried?
   - What outcome do you want?

2. REVIEW: Arbitration Committee reviews briefs (24h)

3. HEAR: Both parties present their position (15 min each, evidence-based)

4. DELIBERATE: Committee discusses privately (30 min max)

5. DECIDE: Committee issues a decision with reasoning
   - Decision is binding
   - Dissenting opinion can be recorded but execution proceeds

6. DOCUMENT: Decision is logged in the Conflict Resolution Log

7. FOLLOW-UP: 2-week check-in to verify resolution held
```

### Principles

1. **Attack the problem, never the person**
2. **Evidence over opinions** — bring data, examples, user feedback
3. **Bias toward action** — a imperfect decision now beats a perfect decision never
4. **Disagree and commit** — once decided, all parties execute wholeheartedly
5. **No retaliation** — raising a conflict is brave, not political
6. **Confidentiality** — discussions stay within the resolution process

---

## Common Conflict Scenarios

| Scenario | Resolution Path |
|----------|----------------|
| Two squads want to own the same module | Architecture Committee decides based on domain expertise and existing ownership |
| Product wants feature X, Engineering says it's too risky | RICE scoring review + Architecture Committee risk assessment |
| Squad member consistently underperforming | 1:1 feedback → PIP → escalation to Head → VP if unresolved |
| Disagreement on tech stack choice | RFC process → Architecture Committee vote → ADR |
| Priority conflict between squads | Product Committee arbitrates based on North Star impact |
| Security blocks a release | Security Committee emergency review → risk-based Go/No-Go |

---

## Escalation Path Diagram

```
Individual ──→ Squad Lead ──→ Head (L3) ──→ VP (L2) ──→ CEO (L1)
                    │               │             │
                    └── Scrum ──────┴── Arbit. ───┘
                        Master         Committee
```

---

## Conflict Prevention

| Practice | How It Prevents Conflict |
|----------|------------------------|
| Clear DRI assignment | No ambiguity about ownership |
| Written RFCs for big decisions | Everyone's voice is heard async |
| RACI for recurring activities | No role confusion |
| Sprint planning with cross-squad sync | No surprise dependencies |
| Radical transparency | No hidden agendas or surprises |
| Regular retrospectives | Small tensions addressed before they grow |
