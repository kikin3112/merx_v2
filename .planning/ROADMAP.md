# Roadmap: Alineación Propuesta de Valor chandelierp

**Milestone:** Propuesta de Valor 2026 (v2.0)
**Base:** ERP multi-tenant maduro (PR #104 completo)
**Objetivo:** Transformar chandelierp en el sistema operativo del Solopreneur Palmireño

---

## Phase 1: Auditoría Integral y Decisiones Técnicas

**Goal:** Producir un documento exhaustivo de brechas (AUDIT.md), investigar
el estado del arte 2026 (IA, pagos locales, WhatsApp API, PDF generation,
freemium patterns) y bloquear todas las decisiones técnicas antes de implementar.

**Requirements:** R1–R7 (análisis solamente, cero código)

**Research scope:**
- Claude API / Gemini Flash para costeo IA — costos, latencia
- Nequi API + Wompi Colombia — sandbox, requisitos de afiliación
- Meta Cloud API WhatsApp Business — pricing conversaciones Colombia
- WeasyPrint vs Puppeteer vs React-PDF para branded PDFs
- Clerk metadata vs DB feature flags para freemium

**Deliverables producidos:**
- `.planning/phases/01-auditoria/AUDIT.md` — gap analysis cuantificado (16 brechas, R1–R7)
- `.planning/phases/01-auditoria/DECISIONS.md` — 6 decisiones técnicas bloqueadas (Phases 2–7)
- `.planning/ROADMAP.md` — actualizado con estimaciones post-auditoría

**Plans:** 3/3 plans executed
- [x] 01-01-PLAN.md — AUDIT.md: gap analysis completo (R1–R7, 16 brechas)
- [x] 01-02-PLAN.md — DECISIONS.md: 6 decisiones técnicas bloqueadas
- [x] 01-03-PLAN.md — ROADMAP.md: actualización post-auditoría

**Status:** COMPLETO

---

## Phase 2: IA Core — Asistente de Costeo y Pricing

**Goal:** Integrar LLM para sugerencias inteligentes de precio, análisis de
márgenes y recomendaciones de optimización de costos dentro del módulo recetas.

**Requirements:** R1.1

**Key decisions (pending Phase 1):**
- LLM provider: Claude API vs Gemini Flash (costo/latencia)
- Prompt strategy: contexto de receta + CVU → recomendación estructurada
- UI: panel lateral en RecetasPage o modal de sugerencias

**Deliverables:**
- `backend/app/servicios/servicio_ia_costeo.py` — LLM orchestration
- `backend/app/rutas/recetas.py` — endpoint `/recetas/{id}/asistente-ia`
- `frontend/src/components/recetas/AsistenteCosteoPanel.tsx`

**Dependencies:** Phase 1 AUDIT.md decision on LLM provider

**Plans:** 5/5 plans executed
- [x] 02-01-PLAN.md — ServicioIACosteo backend skeleton + OpenRouter integration
- [x] 02-02-PLAN.md — SociaAnalisisResponse schema + Decimal safety
- [x] 02-03-PLAN.md — /recetas/{id}/asistente-ia endpoint + tenant isolation
- [x] 02-04-PLAN.md — AsistenteCosteoPanel frontend modal + "Consultar a Socia" button
- [x] 02-05-PLAN.md — E2E validation: 61 tests green, Socia HTTP 200 in production

**Status:** COMPLETO

---

## Phase 3: Imagen Profesional — Plantillas PDF y Catálogos

**Goal:** Facturas PDF con branding del tenant (logo, colores primarios),
generador de catálogo de productos descargable/compartible por WhatsApp.

**Requirements:** R4.1, R4.2

**Key decisions (pending Phase 1):**
- PDF engine: WeasyPrint (Python, Railway) vs Puppeteer (Node, sidecar)
- Storage: S3 bucket existente (confirmar configuración)
- Branding: configuración de logo/colores por tenant (nueva tabla `tenant_branding`)

**Deliverables:**
- `backend/app/servicios/servicio_pdf.py` — generación branded PDF
- `backend/app/rutas/facturas.py` — endpoint `/facturas/{id}/pdf-branded`
- `backend/app/rutas/productos.py` — endpoint `/productos/catalogo-pdf`
- `frontend` — botón "Descargar PDF" en FacturasPage + CatálogoPage

**Dependencies:** None (independiente de Phase 2)

---

## Phase 4: Pagos Locales — Nequi y Daviplata

**Goal:** Integrar APIs de pago colombianas para que los clientes del tenant
puedan pagar vía Nequi/Daviplata directamente desde la factura.

**Requirements:** R3.1, R3.2, R3.3

**Key decisions (pending Phase 1):**
- Estrategia: API directa Nequi vs Wompi (intermediario) vs ambas
- Modelo: QR de cobro vs deep link vs notificación push
- Nueva tabla: `pagos_externos` (monto, estado, proveedor, referencia)
- Alembic migration requerida en esta fase

**Deliverables:**
- `backend/app/servicios/servicio_pagos.py` — abstracción multi-proveedor
- `backend/app/rutas/pagos.py` — webhook de confirmación de pago
- `frontend/src/components/facturas/MetodosPagoPanel.tsx`
- Alembic migration `add_pagos_externos_table`

**Dependencies:** Phase 1 (decisión técnica proveedor)

---

## Phase 5: Canales Conversacionales — WhatsApp Business

**Goal:** Integrar WhatsApp Business API para enviar facturas PDF, catálogos
y links de pago por WhatsApp desde el ERP.

**Requirements:** R2.1, R2.2

**Key decisions (pending Phase 1):**
- Proveedor: Meta Cloud API directo vs BSP (WATI, Infobip, Yalochat)
- Configuración: número por tenant vs número compartido chandelierp + nombre tenant
- Templates: factura enviada, pago recibido, recordatorio

**Deliverables:**
- `backend/app/servicios/servicio_whatsapp.py` — envío de mensajes
- `backend/app/rutas/comunicaciones.py` — endpoints de envío
- Config WhatsApp por tenant en panel de configuración
- Template registry (plantillas aprobadas WABA)

**Dependencies:** Phase 3 (PDF de factura para adjuntar), Phase 4 (link de pago)

---

## Phase 6: Modelo Freemium

**Goal:** Implementar sistema de feature flags y límites por plan para
habilitar un tier gratuito que atraiga micro-negocios de Palmira.

**Requirements:** R6.1, R6.2, R6.3

**Key decisions (pending Phase 1):**
- Feature gate: Clerk metadata vs tabla `planes` en DB
- Límites: facturas/mes, productos, recetas, usuarios por tenant
- Upgrade flow: in-app paywall o email + WhatsApp

**Deliverables:**
- `backend/app/servicios/servicio_planes.py` — validación de límites
- `backend/app/middleware/plan_enforcement.py` — middleware de gates
- `frontend/src/hooks/usePlanLimits.ts` — hook de UI gates
- `frontend/src/components/ui/UpgradePrompt.tsx` — paywall contextual
- Alembic migration `add_planes_table` (si DB-based)

**Dependencies:** Phase 1 (decisión técnica storage de flags)

---

## Phase 7: Asistente Legal y DIAN

**Goal:** Guía contextual de cumplimiento DIAN integrada en el ERP:
recordatorios de declaración, explicaciones de IVA/retenciones en contexto.

**Requirements:** R5.1, R5.2

**Key decisions (pending Phase 1):**
- Contenido: estático (Markdown) vs LLM-generado en contexto
- Recordatorios: cron job Railway vs Clerk webhooks
- Alcance: guía informativa solamente (no contabilidad certificada)

**Deliverables:**
- `backend/app/servicios/servicio_dian.py` — recordatorios + guías
- `frontend/src/components/dian/AsistenteDIANWidget.tsx`
- Calendario tributario configurable por tipo de empresa (simplificado vs ordinario)

**Dependencies:** Phase 6 (feature flag para plan premium)

---

## Phase Summary

| Phase | Goal | Requirements | Effort | Impact | Notes |
|-------|------|-------------|--------|--------|-------|
| 1 | Auditoría + Decisiones | R1–R7 | S | Unlock todo | COMPLETO |
| 2 | 5/5 | COMPLETO   | 2026-03-06 | Alto diferenciador | COMPLETO — OpenRouter confirmed, 61 tests green, Socia E2E validated |
| 3 | PDF Branded | R4.1, R4.2 | M | Imagen profesional | Requiere: verificar S3 bucket AWS |
| 4 | Pagos Locales | R3.1–R3.3 | L | Conversión crítica | Requiere: cuenta Wompi producción |
| 5 | WhatsApp | R2.1, R2.2 | L | Canal de ventas | Requiere: BSP onboarding (1 sem lead time) |
| 6 | Freemium | R6.1–R6.3 | M | Adquisición masiva | Requiere: Clerk pk_live_* keys |
| 7 | DIAN | R5.1, R5.2 | S | Confianza/retención | Depende de: Phase 6 |

**Effort:** S=1-3 días, M=1 semana, L=2 semanas
