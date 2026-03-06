# Merx v2 — Decisiones Técnicas Bloqueadas (Phase 1)

**Fecha:** 2026-03-04
**Estado:** BLOQUEADO — Todas las decisiones son definitivas hasta Phase 7
**Fuente:** 01-RESEARCH.md (investigación 2026-03-04)

> Estas decisiones desbloquean las fases 2–7. No se inicia ninguna fase de implementación
> sin su decisión correspondiente bloqueada aquí.

---

## DECISIÓN 1 — Phase 2: IA Costeo

**DECISION LOCKED: claude-haiku-4-5 via Anthropic API**

### Contexto

El módulo de recetas de Merx calcula CVU y costo unitario con precisión. El gap identificado en AUDIT.md (brecha R1.1-P0) es la ausencia de sugerencias de precio inteligentes basadas en márgenes, mercado y contexto del negocio. La solución requiere un LLM que devuelva outputs estructurados (Decimal-safe) a bajo costo y con latencia adecuada para interacción síncrona usuario-ERP.

### Opciones evaluadas

| Opción | Costo/mes (150K req) | Input /MTok | Output /MTok | Pros | Contras |
|--------|---------------------|------------|-------------|------|---------|
| claude-haiku-4-5 (batch) | $0.83 | $0.50 | $2.50 | Mismo vendor, structured output nativo via `tool_use`, prompt caching, latencia más baja del lineup Anthropic | Costo mayor que Gemini |
| claude-haiku-3-5 (batch) | $0.66 | $0.40 | $2.00 | Más económico que 4.5 | Menor performance que 4.5, ya sin soporte prioritario |
| Gemini 2.0 Flash (batch) | $0.09 | $0.05 | $0.20 | 10× más económico | Nuevo vendor, nuevas credenciales, nuevo SDK, sin consolidación de vendor |
| claude-sonnet-4-6 | $3.30 | $1.50 | $7.50 | Máxima calidad Anthropic | Overkill para costeo, 4× más caro que Haiku 4.5 |

Fuente: [Anthropic official pricing](https://platform.claude.com/docs/en/about-claude/pricing) | [Google Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)

### Decisión

**claude-haiku-4-5** con prompt caching habilitado. Razón: consolidación de vendor (Merx ya usa Anthropic SDK — zero nuevo onboarding de proveedor), structured output via `tool_use` con schema Pydantic, latencia más baja del lineup Anthropic para respuestas síncronas. Costo proyectado: $0.83/mes al pico de 150K requests/mes — bien por debajo del techo de $50/mes. Sistema prompt del módulo recetas (~500 tokens) es cacheable en cada request, reduciendo costo efectivo hasta 90% en los tokens de sistema.

### Configuración técnica

- Model ID: `claude-haiku-4-5`
- Modo: synchronous para interacción usuario directa; batch opcional si se escala a >500K requests/mes
- Prompt caching: sistema prompt (~500 tokens) cacheable en cada request (0.1× precio base en cache hits)
- Output schema obligatorio:
  ```
  {
    precio_sugerido: Decimal,
    margen_esperado: Decimal,
    justificacion: str,
    alertas: list[str]
  }
  ```
- Archivo nuevo: `backend/app/servicios/servicio_ia_costeo.py`
- Endpoint nuevo: `POST /recetas/{id}/asistente-ia`
- Env var nueva: `ANTHROPIC_API_KEY` — agregar a Railway antes de Phase 2
- Riesgo crítico: Decimal serialization — TODOS los outputs numéricos del LLM deben castearse via Pydantic antes de cualquier storage. Un float en datos financieros invalida la integridad del módulo.

### Deferred (OUT OF SCOPE para Phase 2–7)

- R1.3: Análisis predictivo de flujo de caja — requiere historial transaccional suficiente (mínimo 6 meses de datos)
- R1.4: Chatbot WhatsApp para clientes finales del tenant — requiere flujo conversacional completo (Phase 5+ backlog)
- Gemini Flash como alternativa de costo — re-evaluar únicamente si volumen supera 500K req/mes

---

## DECISIÓN 2 — Phase 3: Generación PDF

**DECISION LOCKED: ReportLab (extender instalación existente)**

### Contexto

Merx ya genera PDFs de facturas y cotizaciones via `servicio_pdf.py` usando ReportLab. La brecha (R4.1-P0, R4.2-P1) es la ausencia de branding por tenant: actualmente todos los PDFs usan el mismo template genérico sin logo ni colores del negocio. La decisión técnica determina si extender ReportLab o migrar a una librería diferente para soportar CSS-based branding.

### Opciones evaluadas

| Opción | Estado en repo | Railway OK | Branding support | Effort |
|--------|----------------|------------|------------------|--------|
| ReportLab | INSTALADO, ACTIVO en `servicio_pdf.py` | Nativo Python — sin problemas Railway | Logo via `RLImage`, colores via `colors.HexColor` | Bajo — ya conoce el codebase |
| WeasyPrint | No instalado | RIESGO CONFIRMADO: `libgobject-2.0-0` missing en Railway nixpacks (GitHub issue #2461) | CSS-based — excelente para HTML templates | Alto — nueva dep + Railway config + riesgo runtime |
| Puppeteer/Playwright | No instalado | MUY ALTO: requiere Node.js sidecar o servicio Railway separado | HTML/CSS — excelente | Muy alto — nuevo servicio Railway, complejidad operativa |
| React-PDF | No instalado | Solo render client-side | Bueno | Alto — no puede hacer S3 push, solo descarga directa |

Fuente: [WeasyPrint Railway issue #2461](https://github.com/Kozea/WeasyPrint/issues/2461) | Código leído: `servicio_pdf.py`, `servicio_almacenamiento.py`

### Decisión

**ReportLab** — extender `servicio_pdf.py` con soporte de branding por tenant. Razón: ya deployado y operacional en producción Railway, sin nuevas dependencias Railway, sin riesgo de runtime. WeasyPrint confirmado fallando en Railway nixpacks por `libgobject-2.0-0` ausente — patrón documentado en GitHub con múltiples reportes de usuarios. El fix requiere `NIXPACKS_PKGS` env var adicional, complicando el pipeline de deploy sin ganancia real: ReportLab ya soporta logo e imágenes via `RLImage` y colores HEX via `colors.HexColor`.

### Configuración técnica

- Extensión en: `backend/app/servicios/servicio_pdf.py` (archivo existente)
- Branding: nueva columna `tenants.brand_config JSONB` — `{logo_s3_key, primary_color, secondary_color}` (migración Phase 3)
- Logo pipeline: tenant sube logo → S3 key `tenants/{tenant_id}/logo.png` → `servicio_pdf.py` descarga y embebe via `RLImage`
- Colores: `colors.HexColor(brand_config['primary_color'])` en headers ReportLab
- S3 activation: cambiar `S3_ENABLED=true` en Railway env vars (ya scaffolded en `servicio_almacenamiento.py`)
- Bucket configurado: `chandelier-documents`, region `us-east-1` (en `config.py`)

### Acción previa requerida (owner action antes de Phase 3)

- [ ] Verificar existencia de bucket `chandelier-documents` en AWS Console (us-east-1) — config indica el bucket pero existencia en AWS no confirmada
- [ ] Confirmar que `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` están seteados en Railway env vars (ya están en el schema de config)

### Deferred (OUT OF SCOPE)

- R4.3: Página web/tienda pública por tenant — requiere nueva ruta pública + subdomain routing
- WeasyPrint como alternativa — re-evaluar solo si ReportLab no puede satisfacer un caso de uso específico de layout complejo

---

## DECISIÓN 3 — Phase 4: Pagos Locales

**DECISION LOCKED: Wompi como gateway unificado**

### Contexto

La brecha (R3.1-P0, R3.2-P1, R3.3-P1) requiere que los clientes del tenant puedan pagar facturas via Nequi, Daviplata y Bre-b directamente desde el ERP. La decisión es si integrar cada API de pago directamente (Nequi API, Daviplata API) o usar un gateway unificador como Wompi. La restricción de CONTEXT.md es explícita: no evaluar APIs con más de 2 semanas de aprobación.

### Opciones evaluadas

| Opción | Métodos cubiertos | Sandbox | Comisión | Tiempo aprobación |
|--------|------------------|---------|----------|-------------------|
| **Wompi** (Bancolombia) | Nequi + Daviplata + PSE + Cards + QR + Bre-b | Inmediato con test keys | 2.65% + $700 COP + IVA | < 1 día hábil |
| Nequi API directa | Nequi solo | Por email a `certificacion@conecta.nequi.com` | 1.99% + IVA | 1–4 semanas (certificación manual) |
| Daviplata directa | Daviplata solo | Portal `conectesunegocio.daviplata.com` | Desconocido | > 2 semanas (requiere relación Davivienda) |
| PayU Colombia | Cards + PSE + Nequi + Efectivo | Inmediato | ~3.49% + fijo | < 1 día |
| Bre-b / Transfiya directo | Transferencias ACH | Via banco partner | Gratis para transferencias | No disponible como merchant API directo |

Fuente: [Wompi tarifas](https://wompi.com/es/co/planes-tarifas/) | [Wompi sandbox](https://docs.wompi.co/en/docs/colombia/pruebas-sandbox-pagos-a-terceros/)

### Decisión

**Wompi** como gateway primario y único. Razón: cubre Nequi + Daviplata + PSE en una sola integración SDK. Sandbox disponible inmediatamente con test keys. Respaldado por Bancolombia (mismo parent que Nequi = integración nativa con Nequi como método habilitado). Nequi API directa y Daviplata directa ambas presentan riesgo de timeline > 2 semanas — eliminadas por restricción CONTEXT.md. Comisión 2.65% + $700 COP es estándar del mercado colombiano.

### Configuración técnica

- Sandbox base URL: `https://sandbox.wompi.co/v1`
- Production base URL: `https://api.wompi.co/v1`
- Archivo nuevo: `backend/app/servicios/servicio_pagos.py` — abstracción multi-proveedor
- Nueva tabla requerida: `pagos_externos` — migración Alembic en Phase 4 (primera migración del proyecto de nuevas tablas)
  - Columnas: `id, tenant_id, factura_id, monto, moneda, proveedor, referencia_externa, estado, webhook_payload, created_at`
- Endpoint webhook: `POST /api/v1/pagos/webhook-wompi` para confirmaciones async
- Env vars nuevas: `WOMPI_PUB_KEY`, `WOMPI_PRI_KEY`, `WOMPI_EVENTS_KEY` — agregar a Railway antes de Phase 4
- Acción owner requerida: Registrar cuenta Wompi producción en `wompi.com/negocios` antes de Phase 4

### Open question (resolver en Phase 4 via sandbox testing)

- ¿Nequi como método dentro de Wompi requiere acuerdo comercial separado con Bancolombia (Plan Avanzado)? Wompi sandbox lo incluye en test keys — verificar en production tier antes de go-live.

### Deferred (OUT OF SCOPE)

- R3.4: PSE como botón web separado — cubierto nativamente por Wompi, no requiere integración independiente
- Bre-b directo: accesible solo via banco partner (Cobre, Transfiya), no como merchant API directa — Wompi ofrece exposición parcial via su red de partners
- Epayco como alternativa — re-evaluar solo si Wompi presenta problemas en producción

---

## DECISIÓN 4 — Phase 5: WhatsApp Business

**DECISION LOCKED: BSP (WATI o 360dialog) + número compartido Merx**

### Contexto

La brecha (R2.1-P0, R2.2-P1) requiere enviar facturas PDF, catálogos y links de pago por WhatsApp desde el ERP. La decisión determina si conectar Meta Cloud API directamente o via un BSP (Business Solution Provider), y si cada tenant tiene su propio número WABA o comparten el número de Merx.

### Opciones evaluadas

| Opción | Setup time | Costo Colombia utility msg | Número por tenant | Complejidad |
|--------|-----------|--------------------------|-------------------|-------------|
| BSP — WATI | 24–48h (BSP maneja verificación) | ~$0.001 (20% markup sobre Meta) | Compartido o dedicado | Baja — plataforma managed |
| BSP — 360dialog | 24–48h | ~$0.001 flat | Compartido o dedicado | Baja — plataforma managed |
| Meta Cloud API directo | 2–10 días hábiles (verificación manual) | $0.0008 (precio oficial Meta) | 1 WABA = 1 número | Media — gestión directa de templates y webhooks |
| BSP — Infobip | 24–48h | Variable (enterprise tiers) | Compartido | Media — tier empresarial |

Fuente: [Meta WABA pricing](https://business.whatsapp.com/products/platform-pricing) | [FlowCall 2026 guide](https://www.flowcall.co/blog/whatsapp-business-api-pricing-2026)

### Colombia 2026 — Costos por categoría de mensaje

| Categoría | Precio por mensaje |
|-----------|------------------|
| Marketing | $0.0125 |
| Utility (facturas, confirmaciones) | $0.0008 |
| Authentication | $0.0008 |
| Service (inbound 24h window) | GRATIS |

### Decisión

**BSP (WATI o 360dialog)** para aceleración de onboarding WABA (24–48h vs 2–10 días con Meta directo). **Número compartido Merx** para MVP — un WABA, nombre del tenant en el body del mensaje (ej: "Luz De Luna Velas te envía tu factura #1234"). Razón del número compartido: elimina overhead de registrar WABA por tenant, que requiere NIT colombiano, documentos de incorporación y aprobación individual — bloqueante para micro-negocios sin estructura empresarial formal. El markup BSP (~20% sobre precio Meta) es costo operacional aceptable vs el riesgo de bloqueo por verificación directa.

### Costo proyectado a escala

- 100 tenants × 100 utility msgs/mes = 10,000 msgs/mes = **$8/mes**
- 100 tenants × 20 marketing msgs/mes = 2,000 msgs/mes = **$25/mes**
- Total: **~$33/mes** — bien por debajo del techo de $50/mes

### Configuración técnica

- Templates requeridos: `factura_enviada` (utility), `pago_confirmado` (utility) — approval time 24–72h post-WABA verification
- Archivo nuevo: `backend/app/servicios/servicio_whatsapp.py`
- Endpoints nuevos: `POST /comunicaciones/enviar-factura`, `POST /comunicaciones/enviar-catalogo`
- Env vars nuevas: `WHATSAPP_API_KEY`, `WHATSAPP_PHONE_NUMBER_ID`
- Rate limiting crítico: limitar marketing msgs por tenant/mes (15× más caro que utility — riesgo de cost spike)

### Open question (resolver antes de Phase 5)

- ¿Meta requiere NIT colombiano para business verification incluso via BSP? BSP (WATI/360dialog) maneja compliance y reduce fricción — confirmar proceso exacto al iniciar onboarding BSP.

### Acción previa requerida (owner action con 1 semana de anticipación)

- [ ] Iniciar cuenta BSP (WATI: `wati.io` o 360dialog: `360dialog.com`) antes de Phase 5 — proceso de verificación WABA toma 24–72h mínimo y puede requerir documentos del negocio

### Deferred (OUT OF SCOPE)

- Número WABA propio por tenant: re-evaluar en Phase 5+ cuando base de tenants supere 50 y haya justificación de negocio
- R2.3: Recepción de pedidos por WhatsApp (webhook → orden en ERP) — requiere flujo conversacional completo (NLP, gestión de estado de conversación)
- R1.4: Chatbot WhatsApp para clientes finales del tenant — arquitectura conversacional separada

---

## DECISIÓN 5 — Phase 6: Freemium / Feature Flags

**DECISION LOCKED: Clerk publicMetadata + FastAPI dependency decorator**

### Contexto

La brecha (R6.1-P0, R6.2-P0, R6.3-P1) requiere un tier gratuito con límites configurables para atraer micro-negocios. La decisión técnica determina dónde almacenar el plan del tenant (DB vs Clerk metadata) y cómo enforzar los límites en backend sin degradar performance.

### Opciones evaluadas

| Opción | Migración DB | Latencia enforcement | Sync complexity | Seguridad |
|--------|-------------|---------------------|-----------------|-----------|
| **Clerk `publicMetadata`** | NINGUNA | Cero — plan embebido en JWT | Webhook on plan change | Alta — server-side only |
| DB tabla `planes` + JWT claim | Sí — migration Phase 4+ | Cero si cacheado en JWT | Alta — Clerk webhook + DB update + reissue token | Alta |
| Posthog Feature Flags | Ninguna | Network call por request | SDK en FastAPI | Media |
| Hardcoded middleware | N/A | Cero | N/A — inflexible | Baja |
| Clerk `unsafeMetadata` | NINGUNA | Cero | N/A | MUY BAJA — cliente puede escribirlo directamente |

Fuente: [Clerk publicMetadata docs](https://clerk.com/docs/users/metadata) | Código leído: `auth.py`, JWT claim handling

### Decisión

**Clerk `publicMetadata.plan`** con enforcement via FastAPI dependency decorator. Razón: ya en el pipeline de autenticación, zero DB migration, latencia cero (plan embebido en cada JWT), alineado con restricción PROJECT.md "no modelos.py hasta Phase 2+" y "no migrations hasta Phase 4+". El decorator lee el claim del JWT en memoria — no DB round trip por request.

Restricción CRÍTICA de seguridad: SIEMPRE usar `publicMetadata` (propagado en JWT, escribible solo desde servidor). NUNCA usar `unsafeMetadata` (el cliente puede escribirlo directamente — cualquier usuario podría asignarse plan `pro`).

### Límites del tier gratuito (Phase 6)

| Recurso | Free limit | Pro | Enterprise |
|---------|-----------|-----|------------|
| Facturas / mes | 20 | Ilimitadas | Ilimitadas |
| Productos | 50 | Ilimitados | Ilimitados |
| Recetas | 5 | Ilimitadas | Ilimitadas |

Límites almacenados en `publicMetadata.limits` como JSON — permiten ajuste por tenant sin redeploy.

### Configuración técnica

- Plan values: `'free' | 'pro' | 'enterprise'`
- Enforcement: `backend/app/middleware/plan_enforcement.py` — decorator `@require_plan(min_plan='pro')`
- Patrón: decorator lee `current_user.public_metadata.get("plan", "free")` — cero DB call
- Frontend: `frontend/src/hooks/usePlanLimits.ts` — hook leyendo Clerk session claims
- UI gates: `frontend/src/components/ui/UpgradePrompt.tsx` — paywall contextual in-app
- Actualización de plan: Clerk backend API `PATCH /v1/users/{user_id}` con `public_metadata: {plan: 'pro'}` — ejecutable desde panel superadmin Merx

### Acción previa requerida (owner action antes de Phase 6)

- [ ] Migrar Clerk de dev keys (`pk_test_*`) a prod keys (`pk_live_*`) para habilitar upgrade flows reales — actualmente dev keys en producción (conocido de MEMORY.md)

### Deferred (OUT OF SCOPE)

- DB tabla `planes` con historial de cambios de plan — re-evaluar cuando se requiera auditoría financiera de upgrades/downgrades
- R6.4: Dashboard de uso para superadmin — métricas de adopción por plan (Phase 6+ backlog)
- Posthog Feature Flags — re-evaluar si Clerk no cubre casos de uso de A/B testing

---

## DECISIÓN 6 — Phase 7: DIAN Asistente

**DECISION LOCKED: Contenido estático Markdown + LLM contextual (claude-haiku-4-5)**

### Contexto

La brecha (R5.1-P1, R5.2-P1) requiere guía contextual de cumplimiento DIAN: recordatorios de declaración, explicaciones de IVA/retenciones en contexto del módulo activo. La decisión es si el contenido es estático (Markdown curado) o generado por LLM en cada request.

### Decisión

**Híbrido:** calendario tributario en Markdown estático (bajo costo, sin latencia LLM, sin riesgo de hallucination en fechas críticas) + LLM para preguntas contextuales específicas del tenant (¿qué IVA aplica a mi receta de velas?, ¿tengo retención en la fuente en esta factura?).

Recordatorios de declaración via Railway cron job (ya disponible en Railway — sin nueva infraestructura). Modelo LLM: `claude-haiku-4-5` (misma decisión que Phase 2 — consolidación de vendor).

**Restricción de alcance:** guía informativa únicamente. No contabilidad certificada. Disclaimer legal obligatorio en toda respuesta del asistente.

### Configuración técnica

- Calendario tributario: `backend/app/data/calendario_dian.md` — Markdown curado, actualizable sin redeploy
- Recordatorios: Railway cron job `servicios/servicio_dian.py` — `0 8 * * 1` (lunes 8am para la semana)
- LLM preguntas contextuales: misma infraestructura de `servicio_ia_costeo.py` (Phase 2) — reutilizar
- Frontend: `frontend/src/components/dian/AsistenteDIANWidget.tsx` — widget lateral por módulo

### Deferred (OUT OF SCOPE)

- R5.3: Facturación electrónica certificada DIAN — requiere integrador certificado (SIIGO, ALEGRA API) — inversión L (2+ semanas), fuera del alcance de este roadmap
- Cálculo automático de impuestos — contabilidad certificada, responsabilidad legal

---

## Resumen de Decisiones

| Phase | Area | Decisión | Status |
|-------|------|---------|--------|
| 2 — IA Costeo | LLM Provider | claude-haiku-4-5 via Anthropic API (batch+caching) | LOCKED |
| 3 — PDF Branding | PDF Engine | ReportLab extend + S3 activate (`S3_ENABLED=true`) | LOCKED |
| 4 — Pagos Locales | Payment Gateway | Wompi gateway unificado (Nequi+Daviplata+PSE) | LOCKED |
| 5 — WhatsApp | Channel | BSP (WATI/360dialog) + número compartido Merx | LOCKED |
| 6 — Freemium | Feature Flags | Clerk publicMetadata + FastAPI decorator (zero migration) | LOCKED |
| 7 — DIAN | Content Strategy | Markdown estático + LLM contextual claude-haiku-4-5 | LOCKED |

---

## Owner Actions (requeridas antes de implementación)

| Action | Owner | Blocks Phase | Urgency |
|--------|-------|-------------|---------|
| Agregar `ANTHROPIC_API_KEY` a Railway env vars | Owner | Phase 2 | Antes de iniciar Phase 2 |
| Verificar bucket `chandelier-documents` en AWS Console (us-east-1) | Owner | Phase 3 | Antes de iniciar Phase 3 |
| Registrar cuenta Wompi producción en `wompi.com/negocios` | Owner | Phase 4 | Antes de iniciar Phase 4 |
| Iniciar cuenta BSP — WATI (`wati.io`) o 360dialog (`360dialog.com`) para WABA | Owner | Phase 5 | Iniciar con 1 semana de anticipación a Phase 5 |
| Migrar Clerk de dev keys (`pk_test_*`) a prod keys (`pk_live_*`) | Owner | Phase 6 upgrade flows | Antes de iniciar Phase 6 |

---

## Open Questions (con ruta de resolución)

| # | Pregunta | Ruta de resolución | Blocks |
|---|----------|-------------------|--------|
| OQ-1 | ¿Bucket `chandelier-documents` existe en AWS? | Verificar en AWS Console us-east-1 antes de Phase 3 | Phase 3 S3 activation |
| OQ-2 | ¿Nequi dentro de Wompi requiere acuerdo comercial separado con Bancolombia? | Verificar sandbox flow en Phase 4 antes de go-live | Phase 4 Nequi integration |
| OQ-3 | ¿Clerk dev keys permiten `publicMetadata` write via backend API? | Confirmado — dev keys soportan full backend API. Prod keys necesarias solo para upgrade flows reales | Phase 6 |
| OQ-4 | ¿Meta requiere NIT colombiano incluso via BSP? | BSP (WATI/360dialog) maneja compliance — confirmar al iniciar onboarding BSP | Phase 5 WABA verification |

---

## Pitfalls a Evitar (extraídos de RESEARCH.md)

### Pitfall 1 — Nequi/Daviplata directo: trampa de timeline de aprobación
El equipo inicia integración Nequi API directa, se encuentra con proceso de certificación 2–4 semanas, bloquea entrega Phase 4. **Fix:** Wompi cubre Nequi nativamente, sandbox en minutos.

### Pitfall 2 — WeasyPrint en Railway: éxito silencioso en build, fallo en runtime
`pip install weasyprint` succeed, pero `libgobject-2.0-0` ausente en nixpacks → crash en producción al generar PDF. **Fix:** ReportLab ya funciona. Nunca instalar WeasyPrint sin `NIXPACKS_PKGS` configurado.

### Pitfall 3 — Clerk unsafeMetadata vs publicMetadata
Almacenar plan en `unsafeMetadata` → cliente puede escribirlo → cualquier usuario asigna plan `pro`. **Fix:** SIEMPRE `publicMetadata` (server-side only). NUNCA `unsafeMetadata` para planes.

### Pitfall 4 — WhatsApp marketing cost spike
Mensajes marketing = $0.0125 (15× más caro que utility $0.0008). Sin rate limiting por tenant → cost spike descontrolado. **Fix:** Rate limit marketing msgs por tenant/mes desde Phase 5.

### Pitfall 5 — Decimal corruption desde LLM output
LLM retorna precios como float → stored con float arithmetic → datos financieros corruptos. **Fix:** Castear SIEMPRE via `Decimal(str(raw_value))` antes de cualquier storage o cálculo.
