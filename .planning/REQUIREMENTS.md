# Requirements — Propuesta de Valor 2026

**Source:** `Chandelier/PROPUESTA DE VALOR.md` — Solopreneur Palmireño 2026
**Method:** JTBD → Functional Requirements mapping

---

## R1 — Automatización con IA

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| R1.1 | Asistente de costeo IA: sugerencias de precio basadas en márgenes y mercado | P0 | Integra con módulo recetas existente |
| R1.2 | Generación automática de descripciones de productos y catálogos | P1 | LLM + contexto del producto |
| R1.3 | Análisis predictivo de flujo de caja | P2 | Requiere historial transaccional |
| R1.4 | Chatbot de soporte al cliente del tenant (bot para sus clientes finales) | P2 | WhatsApp-first |

**JTBD:** "Adopción de IA para Productividad — IA generativa para contenido, servicio al cliente y análisis de datos"

---

## R2 — Canales Conversacionales

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| R2.1 | Integración WhatsApp Business API: envío de facturas, catálogos, confirmaciones | P0 | Meta Cloud API o BSP |
| R2.2 | Link de pago por WhatsApp (deep link Nequi/Daviplata en mensaje) | P1 | Depende de R3 |
| R2.3 | Recepción de pedidos por WhatsApp (webhook → orden en ERP) | P2 | Requiere flujo conversacional |

**JTBD:** "Digitalización de la Última Milla — ventas por canales conversacionales con variedad de medios de pago"

---

## R3 — Pagos Locales Colombianos

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| R3.1 | Integración Nequi (Bancolombia) — generación de QR/link de cobro | P0 | API directa o Wompi |
| R3.2 | Integración Daviplata — generación de link de cobro | P1 | Verificar disponibilidad API |
| R3.3 | Bre-b (ACH Colombia) — transferencias inmediatas | P1 | Requiere afiliación bancaria |
| R3.4 | PSE (botón de pago web) | P2 | Via Wompi/PayU |

**JTBD:** "Frontera Digital — uso básico de WhatsApp y billeteras digitales (Nequi, Daviplata, Bre-b)"

---

## R4 — Imagen Profesional

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| R4.1 | Plantillas de factura PDF con branding del tenant (logo, colores) | P0 | WeasyPrint/Puppeteer + S3 |
| R4.2 | Generador de catálogo de productos descargable (PDF) | P1 | Template engine + S3 |
| R4.3 | Página web/tienda pública por tenant (URL pública) | P2 | Nueva ruta pública |

**JTBD:** "Orgullo y Clúster — ser percibido como profesional; Alegrías inesperadas: facturas estéticas y catálogos limpios"

---

## R5 — Cumplimiento y Legal DIAN

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| R5.1 | Widget de asistente DIAN: guía contextual por módulo (IVA, retenciones) | P1 | Contenido estático + LLM |
| R5.2 | Recordatorios de declaración (IVA bimestral, renta anual) | P1 | Cron job + notificaciones |
| R5.3 | Facturación electrónica certificada DIAN | P2 | Integrador certificado (SIIGO/ALEGRA API) |

**JTBD:** "Complejidad regulatoria — aliviador de frustración"

---

## R6 — Modelo Freemium

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| R6.1 | Tier gratuito: límites configurables (X facturas/mes, Y productos, Z recetas) | P0 | Feature gate en servicios |
| R6.2 | Feature flags por plan (plan_id en tenant metadata) | P0 | Clerk metadata o DB |
| R6.3 | Upgrade flow: paywall contextual, integración con pasarela de pagos | P1 | UI + backend validation |
| R6.4 | Dashboard de uso para superadmin | P2 | Métricas de adopción por plan |

**JTBD:** "Bueno, bonito y barato — 81% micronegocios, alta informalidad; capturar 5% micronegocios Palmira"

---

## R7 — Localismo Digital

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| R7.1 | Onboarding adaptado: ejemplos con negocios locales reales (velas, confites, etc.) | P1 | Copy/UX change |
| R7.2 | Métodos de pago regionales visibles en UI (Nequi, Daviplata como primera opción) | P1 | Depende de R3 |
| R7.3 | Jerga local en microcopy (sin tecnicismos contables) | P2 | i18n o copy review |

**JTBD:** "Factor Diferencial: Localismo Digital — adaptación a jerga local, métodos de pago regionales"

---

## Priority Matrix

| Priority | Requirements | Rationale |
|----------|-------------|-----------|
| P0 (Core) | R1.1, R2.1, R3.1, R4.1, R6.1, R6.2 | Diferenciación inmediata, tracción |
| P1 (High) | R1.2, R2.2, R3.2–R3.3, R4.2, R5.1–R5.2, R6.3, R7.1–R7.2 | Completitud de propuesta de valor |
| P2 (Medium) | R1.3–R1.4, R2.3, R3.4, R4.3, R5.3, R6.4, R7.3 | Escalabilidad futura |
