# L3 — Head of Frontend Engineering

> Architect and guardian of the client-side experience powering MERX v2.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L3 — Functional Direction |
| **Reports To** | VP Engineering (L2) |
| **Pillar** | Core Engineering |
| **Stack** | React, TypeScript, Vite, Zustand, react-window, React Spring / Framer Motion |

---

## Purpose

Lead the **frontend architecture**, ensure **performance at scale** (100k+ rows virtualized), and deliver a **fluid, responsive UX** across all ERP modules.

---

## Responsibilities

| Area | Responsibility |
|------|---------------|
| **Architecture** | React + TypeScript patterns, component structure, state management (Zustand) |
| **Performance** | Virtualization (react-window), bundle optimization, lazy loading |
| **Component library** | Maintain shared components aligned with design system |
| **State management** | Global (Zustand) vs local state guidelines, SSE real-time updates |
| **Navigation** | Contextual navigation, breadcrumbs, module routing |
| **Code standards** | TypeScript strict mode, linting, formatting, testing patterns |
| **Accessibility** | Keyboard navigation, ARIA labels, screen reader support in components |

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Design specs + prototypes | Head UX/UI | | Implemented pages/components | Users |
| API contracts | Head Backend | | Performance benchmarks | VP Eng |
| Design system tokens | Guild UX/Design | | Component library updates | All squads |
| Feature specs | Head Product | | Frontend architecture docs | Architecture Committee |
| Accessibility requirements | Head UX/UI | | Bundle size reports | DevOps |

---

## Metrics

| Metric | Target |
|--------|--------|
| Largest Contentful Paint (LCP) | < 2.5s |
| First Input Delay (FID) | < 100ms |
| Cumulative Layout Shift (CLS) | < 0.1 |
| Bundle size (main chunk) | < 250KB gzipped |
| Test coverage (frontend) | ≥ 70% |
| Design system compliance | ≥ 95% |
| Table performance (100k rows) | Smooth 60fps scrolling |

---

## Operational Rules

1. **TypeScript strict mode** — no `any` types without explicit justification in comments
2. **Component-first** — reusable components in shared library before page-specific code
3. **Design system compliance** — all UI must use design system tokens (colors, spacing, typography)
4. **Virtual everything** — lists > 100 rows must use virtualization
5. **SSE for real-time** — no polling; use Server-Sent Events for live updates
6. **Bundle analysis per PR** — flag any PR that increases bundle > 10KB
7. **Accessibility audit per module** — keyboard + screen reader testing before module release
