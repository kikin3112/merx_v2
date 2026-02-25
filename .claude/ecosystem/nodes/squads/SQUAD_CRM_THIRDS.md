# Squad: CRM & Third Parties

> Cross-functional squad owning customer relationships, third-party management, and support module.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L4 — Domain Team |
| **Model** | Spotify Squad |
| **Scope** | `crm`, `terceros`, `pqrs` |
| **Reports To** | Head of Product (functional), VP Eng (technical) |

---

## Composition

| Role | Responsibility |
|------|---------------|
| **Product Owner** | Prioritizes CRM pipeline, third-party management, PQRS module |
| **Backend Dev** | CRM service, third-party module (clients/suppliers), PQRS workflows |
| **Frontend Dev** | CRMPage, TercerosPage, SoportePage with CRM and support components |
| **QA Engineer** | CRM flow testing, third-party search, PQRS management |

---

## Module Detail

| Module | Key Features | Complexity |
|--------|-------------|-----------|
| `crm` | Lead pipeline, deal stages, activity tracking, conversion | Medium |
| `terceros` | Client/supplier registry, contact info, classification, history | Medium |
| `pqrs` | Petitions, complaints, claims, suggestions — workflow + SLA tracking | High |

---

## Key Flows

```
Lead → [Qualify] → Opportunity → [Won] → Client (tercero) → Invoicing
                                → [Lost] → Archive + Learning

User Complaint → PQRS Created → Auto-assigned → SLA Timer → Resolution → Feedback
```

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Lead data | Marketing/Sales channels | | Client data | Squad: Sales (invoicing) |
| Customer interactions | End users (PQRS) | | PQRS reports | Head CS + CPO |
| Product feedback | PQRS module | | Third-party data | All squads (shared entity) |
| Support tickets | Users | | Customer insights | Data & Analytics |

---

## Metrics

| Metric | Target |
|--------|--------|
| Lead → Client conversion rate | ≥ 20% |
| PQRS first response time | < 4 hours |
| PQRS resolution time | < 72 hours |
| Third-party data completeness | ≥ 95% |
| Sprint commitment completion | ≥ 80% |

---

## Dependencies

| Depends On | For |
|-----------|-----|
| Squad: Sales | Linking clients to invoices/quotations |
| Squad: Platform | Tenant context, auth, user roles |
| Head CS | PQRS escalation rules, SLA definitions |
| Guild: UX/Design | CRM pipeline visualization |
