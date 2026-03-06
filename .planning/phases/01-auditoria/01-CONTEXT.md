# Phase 1 Context — Auditoría Integral y Decisiones Técnicas

**Phase:** 1 of 7
**Goal:** Gap analysis cuantificado + decisiones técnicas que desbloquean Phases 2–7
**Status:** Planning

---

## What This Phase Does

Produces two documents that gate all subsequent implementation:

1. **AUDIT.md** — gap analysis with severity/effort/impact per requirement
2. **DECISIONS.md** — technical decision per phase (LLM provider, PDF engine,
   WhatsApp provider, payment gateway, freemium storage)

Zero code produced in this phase.

---

## Existing System State

**Mature modules (production PR #104):**
- Recetas + CVU: costeo completo con CIF distribuido, conversión de unidades
- Facturas + POS: flujo completo de venta
- Contabilidad: módulo activo
- Auth: Clerk → FastAPI JWT multi-tenant
- Inventario + Productos: compound module

**Infrastructure confirmed:**
- Railway (backend) + Vercel (frontend) CI/CD active
- PostgreSQL RLS tenant isolation
- AWS S3 configured (confirm bucket for PDF storage)
- GA4 analytics events

---

## Research Areas

### Area 1: IA para Costeo (R1.1)

Questions to answer:
- Claude API `claude-haiku-4-5` vs `claude-sonnet-4-6` — latencia p95, costo por request típico de costeo
- Gemini 2.0 Flash — comparative cost/latency for structured output (JSON pricing recommendation)
- Context size needed: receta completa (ingredientes, CVU, historial) = ~2K tokens
- Expected request volume: 10–50/day per tenant, ~100 tenants = 1K–5K requests/day
- Structured output format: `{precio_sugerido, margen_esperado, justificacion, alertas[]}`

Decision needed: **Provider + model + estimated monthly cost**

### Area 2: Pagos Locales Colombia (R3.1–R3.3)

Questions to answer:
- **Nequi API** (Bancolombia): ¿requiere vinculación empresarial? ¿sandbox disponible? ¿endpoints de cobro?
- **Wompi** (Bancolombia): ¿cubre Nequi + PSE + tarjetas en un SDK? ¿comisión por transacción?
- **Daviplata**: ¿API pública o solo integración via Davivienda merchant?
- **Bre-b** (ACH Colombia): ¿modelo de integración para PSE inmediato?
- Alternativa consolidada: Epayco, PayU, Kushki — cobertura de métodos locales

Decision needed: **Gateway primario + métodos cubiertos + comisión estimada**

### Area 3: WhatsApp Business API (R2.1)

Questions to answer:
- Meta Cloud API directo: requisitos de verificación de negocio, tiempo de aprobación WABA
- BSP Colombia: WATI, Infobip, Treble.ai — comparativa pricing conversaciones de servicio vs utilidad
- Precio por conversación en Colombia 2026 (Meta pricing actualizado)
- Modelo: número compartido chandelierp (1 WABA, sender name = tenant) vs número propio por tenant
- Template requirements: factura enviada, pago confirmado — proceso de aprobación Meta

Decision needed: **BSP vs direct + número compartido vs por tenant + costo mensual estimado**

### Area 4: Generación PDF (R4.1, R4.2)

Questions to answer:
- **WeasyPrint**: Python-native, Railway-compatible? CSS support for custom fonts/logos?
- **Puppeteer/Playwright**: requiere Node sidecar o separate service — complejidad Railway
- **React-PDF** (`@react-pdf/renderer`): renderizado en frontend vs backend
- **ReportLab** (Python): bajo nivel, máximo control, curva alta
- S3 integration: ¿bucket ya configurado en Railway env vars? Confirmar `AWS_S3_BUCKET`
- Tenant branding: logo upload → S3, colores primarios → nueva columna `tenant.brand_config JSONB`

Decision needed: **PDF engine + storage strategy + branding DB schema**

### Area 5: Freemium / Feature Flags (R6.1–R6.2)

Questions to answer:
- **Clerk metadata**: `publicMetadata.plan = 'free'|'pro'` — sync con DB? Latency?
- **DB tabla `planes`**: join en cada request vs JWT claim
- **Posthog Feature Flags**: ¿ya integrado? overhead de SDK en FastAPI
- **Simple middleware approach**: decorator `@require_plan('pro')` en rutas
- Límites por definir: facturas/mes (free=20?), productos (free=50?), recetas (free=5?)

Decision needed: **Storage de plan + enforcement pattern + límites del tier free**

---

## Deliverables

```
.planning/phases/01-auditoria/
├── 01-CONTEXT.md          ← este archivo
├── PLAN.md                ← generado por /gsd:plan-phase
├── AUDIT.md               ← output principal (gap analysis)
└── DECISIONS.md           ← output secundario (decisiones técnicas)
```

---

## Success Criteria

- [ ] Cada brecha (R1–R7) tiene: severity (P0/P1/P2), effort (S/M/L), impact (1–10)
- [ ] Decisión técnica documentada para: LLM provider, PDF engine, WhatsApp provider, pagos gateway, freemium storage
- [ ] Riesgos identificados por fase (regulatory, API availability, cost overrun)
- [ ] ROADMAP.md actualizado con estimaciones de esfuerzo revisadas post-auditoría
- [ ] Zero código escrito en esta fase

---

## Constraints

- Do NOT evaluate WhatsApp or payment APIs that require >2 weeks of approval
- Prefer solutions with public sandbox/dev environment for immediate testing
- Cost ceiling per feature: <$50 USD/month at 100 tenants scale
- All external APIs must have Colombian peso support or USD with local methods
