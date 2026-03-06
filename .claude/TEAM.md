# TEAM — Ecosystem Index

> This file is the navigation index for the chandelierp / chandelierp organizational ecosystem.
> Source of truth: `.claude/ecosystem/00_MASTER_BLUEPRINT.md`

---

## Hierarchical Structure

### LEVEL 1 — Executive Direction

| Role | Node |
|------|------|
| CEO / Founder / CTO | [l1_executive/NODE.md](ecosystem/nodes/l1_executive/NODE.md) |

---

### LEVEL 2 — Strategic Leadership

| Role | Pillar | Node |
|------|--------|------|
| VP Product & Strategy (CPO) | Product & Design | [l2_product/NODE.md](ecosystem/nodes/l2_product/NODE.md) |
| VP Engineering | Core Engineering + Infra | [l2_engineering/NODE.md](ecosystem/nodes/l2_engineering/NODE.md) |
| VP Operations & Commercial (COO) | Operations & Commercial | [l2_operations/NODE.md](ecosystem/nodes/l2_operations/NODE.md) |

---

### LEVEL 3 — Functional Direction (Heads)

#### 🟦 Product & Design Pillar

| Role | Node | Claude Agent |
|------|------|-------------|
| Head of Product | [product/NODE.md](ecosystem/nodes/product/NODE.md) | — |
| Head of UX/UI & Design | [ux_ui/NODE.md](ecosystem/nodes/ux_ui/NODE.md) | — |

#### 🟩 Core Engineering Pillar

| Role | Node | Claude Agent |
|------|------|-------------|
| Head of Backend Engineering | [backend/NODE.md](ecosystem/nodes/backend/NODE.md) | [backend-engineer.md](agents/backend-engineer.md) |
| Head of Frontend Engineering | [frontend/NODE.md](ecosystem/nodes/frontend/NODE.md) | [frontend-engineer.md](agents/frontend-engineer.md) |
| Head of QA & Testing | [qa/NODE.md](ecosystem/nodes/qa/NODE.md) | — |

#### 🟧 Infrastructure, DevOps & Security Pillar

| Role | Node | Claude Agent |
|------|------|-------------|
| Head of DevOps & Platform | [devops/NODE.md](ecosystem/nodes/devops/NODE.md) | [devops-engineer.md](agents/devops-engineer.md) |
| Head of Security (SecOps) | [security/NODE.md](ecosystem/nodes/security/NODE.md) | [security-engineer.md](agents/security-engineer.md) |

#### 🟪 Operations & Commercial Pillar

| Role | Node | Claude Agent |
|------|------|-------------|
| Head of Sales & Growth | [sales/NODE.md](ecosystem/nodes/sales/NODE.md) | — |
| Head of Customer Success & Support | [customer_success/NODE.md](ecosystem/nodes/customer_success/NODE.md) | — |
| Head of Marketing & Brand | [marketing/NODE.md](ecosystem/nodes/marketing/NODE.md) | — |

---

### LEVEL 4 — Domain Squads

| Squad | Domain |
|-------|--------|
| Sales & Billing | Ventas, facturas, cobros |
| Inventory & Production | Productos, stock, recetas, almacenes |
| Accounting & Finance | Contabilidad, cartera, impuestos, DIAN |
| CRM & Third Parties | Clientes, proveedores, terceros |
| Platform & Tenants | Auth, tenants, PQRS, onboarding, SaaS control |

---

### LEVEL 5 — Cross-Functional Guilds

| Guild | Focus |
|-------|-------|
| Architecture & Standards | Design patterns, ADRs, code standards |
| DevOps & Infrastructure | CI/CD, infra tooling, observability |
| Security (SecOps) | Security pipelines, threat modeling, compliance |
| UX/UI & Design System | Design tokens, components, accessibility |
| Data & Analytics | Metrics, dashboards, PostHog/Umami |

---

### LEVEL 6 — Governance Committees

| Committee | Scope |
|-----------|-------|
| Architecture Committee | Cross-module technical decisions |
| Product Committee | Roadmap and prioritization |
| Security Committee | Security posture and incidents |
| Release Committee | Deploy gates and release coordination |

---

## Claude Agents Reference

| Agent | Ecosystem Node | File |
|-------|---------------|------|
| Backend Engineer | L3 Head of Backend | [agents/backend-engineer.md](agents/backend-engineer.md) |
| Frontend Engineer | L3 Head of Frontend | [agents/frontend-engineer.md](agents/frontend-engineer.md) |
| DevOps Engineer | L3 Head of DevOps | [agents/devops-engineer.md](agents/devops-engineer.md) |
| Security Engineer | L3 Head of Security | [agents/security-engineer.md](agents/security-engineer.md) |
| Vercel Specialist | — (superpowers plugin) | [agents/vercel-deployment-specialist.md](agents/vercel-deployment-specialist.md) |
