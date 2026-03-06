# Merx v2 — Auditoría de Brechas (Phase 1)

**Fecha:** 2026-03-04
**Base:** PR #104 (ERP multi-tenant maduro en producción)
**Milestone objetivo:** Solopreneur Palmireño 2026 (v2.0)
**Alembic head confirmado:** `e7f8a9b0c1d2`

---

## Guía de Puntuación

| Campo | Valores | Definición |
|-------|---------|------------|
| Severidad | P0/P1/P2 | P0=bloqueante, P1=alto valor, P2=nice to have |
| Esfuerzo | S/M/L | S=1–3 días, M=1 semana, L=2 semanas |
| Impacto | 1–10 | Valor de negocio si se implementa |
| Estado | FALTANTE/PARCIAL/EXISTE | Estado actual en el codebase |

---

## R1 — Automatización con IA

### R1.1 — Asistente de Costeo IA

**Requisito:** Sugerencias de precio basadas en márgenes, CVU y contexto de mercado local.

**Estado actual:** FALTANTE

**Verificado en codebase:**
- `backend/app/rutas/recetas.py` — sin endpoints `/asistente-ia` ni integración LLM
- `backend/app/servicios/` — no existe `servicio_ia_costeo.py`
- No hay variable `ANTHROPIC_API_KEY` referenciada en `config.py` ni en Railway

**Brecha específica:** Se requieren los siguientes artefactos:
- `backend/app/servicios/servicio_ia_costeo.py` — orquestación LLM con Anthropic claude-haiku-4-5
- Endpoint `POST /recetas/{id}/asistente-ia` en `backend/app/rutas/recetas.py`
- `frontend/src/components/recetas/AsistenteCosteoPanel.tsx` — panel lateral con sugerencias
- Variable de entorno `ANTHROPIC_API_KEY` en Railway dashboard

**Proveedor recomendado:** `claude-haiku-4-5` via Anthropic API con prompt caching.
- Costo estimado: $0.83/mes (batch) a 150K requests/mes con 100 tenants
- Structured output nativo via `tool_use` — sin parsing manual
- Ecosistema Anthropic ya usado en el proyecto (cero nuevo vendor onboarding)
- Alternativa: Gemini 2.0 Flash ($0.09/mes batch) — 10× más barato pero requiere cuenta Google Cloud

**Riesgo crítico:** Salida LLM devuelve floats — siempre castear a `Decimal` antes de almacenar.
Patrón: `precio_sugerido=Decimal(str(raw["precio_sugerido"]))` en Pydantic model.

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P0** | M | 9 |

---

### R1.2 — Generación Automática de Descripciones de Productos

**Requisito:** Descripciones de productos generadas por LLM a partir del nombre, categoría y contexto del tenant.

**Estado actual:** FALTANTE

**Brecha específica:**
- Endpoint `POST /productos/{id}/generar-descripcion`
- Prompt con contexto del producto + instrucción de tono local ("velas artesanales palmireñas")
- Campo `descripcion` en `Productos` ya existe — solo falta el generador

**Nota:** Piggybacks la infraestructura LLM de R1.1 (mismo `servicio_ia_costeo.py` extendido).
No requiere nueva dependencia si R1.1 se implementa primero.

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P1** | S | 7 |

---

## R2 — Canales Conversacionales (WhatsApp)

### R2.1 — Integración WhatsApp Business API

**Requisito:** Envío de facturas PDF, catálogos y confirmaciones de pedido por WhatsApp.

**Estado actual:** FALTANTE

**Verificado en codebase:**
- `backend/app/servicios/` — no existe `servicio_whatsapp.py`
- `backend/app/rutas/` — no existe `comunicaciones.py`
- Sin variables WABA_TOKEN, WABA_PHONE_ID, BSP_API_KEY en config.py

**Brecha específica:**
- `backend/app/servicios/servicio_whatsapp.py` — cliente HTTP a BSP (WATI o 360dialog)
- `backend/app/rutas/comunicaciones.py` — endpoints de envío y webhook de estado
- Templates de mensaje pre-aprobados WABA: "Factura enviada", "Pago confirmado"
- Panel de configuración WhatsApp por tenant en frontend

**Proveedor recomendado:** BSP (WATI o 360dialog) en vez de Meta Cloud API directo.
- BSP: onboarding WABA en 24–48h vs 2–10 días hábiles para verificación Meta directa
- Precio Colombia: $0.0008/mensaje utility (envío de facturas) — ~$8/mes a 100 tenants × 100 msgs
- Número compartido Merx para MVP (cero setup por tenant)

**Brecha de infraestructura:** Registro WABA requerido antes de Phase 5.
- Acción del propietario: Iniciar cuenta BSP (WATI: wati.io, 360dialog.com)
- Pregunta abierta: ¿Verificación Meta requiere NIT colombiano o acepta registro extranjero?
  - Mitigación: BSP maneja cumplimiento — reduce fricción de verificación

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P0** | L | 9 |

---

### R2.2 — Link de Pago por WhatsApp

**Requisito:** Link profundo Nequi/Daviplata embebido en mensaje WhatsApp de factura.

**Estado actual:** FALTANTE

**Dependencias:** R2.1 (infraestructura WhatsApp) + R3.1 (generación de link de pago Wompi)

**Brecha específica:**
- Función en `servicio_whatsapp.py` que combina PDF adjunto + link de pago en mismo mensaje
- Plantilla WABA con variable `{{link_pago}}` aprobada por Meta
- Esfuerzo mínimo si R2.1 y R3.1 están implementados primero

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P1** | S | 8 |

---

## R3 — Pagos Locales Colombianos

### R3.1 — Nequi via Wompi

**Requisito:** Generación de QR/link de cobro Nequi para clientes del tenant.

**Estado actual:** FALTANTE

**Verificado en codebase:**
- `backend/app/datos/modelos_tenant.py:212` — campo `proveedor_pago = Column(String(50))` existe pero solo almacena string, sin integración
- Sin tabla `pagos_externos` en modelos
- Sin `backend/app/servicios/servicio_pagos.py`
- Sin `backend/app/rutas/pagos.py`

**Brecha específica:**
- Tabla nueva `pagos_externos` (monto, estado, proveedor, referencia_externa, factura_id, tenant_id)
  - Nota: migración Alembic diferida a Phase 4 (restricción arquitectónica: no migrations hasta Phase 4+)
- `backend/app/servicios/servicio_pagos.py` — abstracción multi-proveedor
- `backend/app/rutas/pagos.py` — endpoint webhook de confirmación + endpoint generación link
- `frontend/src/components/facturas/MetodosPagoPanel.tsx`

**Proveedor recomendado:** Wompi como gateway unificado.
- Cubre: Nequi, Daviplata, PSE, tarjetas, QR en una sola integración
- Sandbox disponible inmediatamente con test keys (wompi.co/developers)
- Comisión: 2.65% + $700 COP + IVA por transacción
- Alternativa descartada: API Nequi directa — requiere proceso de certificación por email (`certificacion@conecta.nequi.com`), potencialmente >2 semanas

**Brecha de infraestructura:** Cuenta Wompi producción requerida antes de Phase 4.
- Acción del propietario: Registrar en wompi.com/negocios
- Pregunta abierta: ¿Nequi dentro de Wompi requiere acuerdo comercial separado con Bancolombia?
  - Mitigación: Verificar en sandbox de Wompi durante Phase 4

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P0** | L | 10 |

---

### R3.2 — Daviplata via Wompi

**Requisito:** Link de cobro Daviplata para clientes del tenant.

**Estado actual:** FALTANTE

**Nota:** Cubierto por la integración Wompi de R3.1. Sin esfuerzo adicional si R3.1 se implementa con Wompi (Daviplata es método de pago nativo en el SDK).

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P1** | S (piggyback R3.1) | 9 |

---

### R3.3 — Bre-b (Transferencias Inmediatas)

**Requisito:** Transferencias bancarias inmediatas ACH Colombia.

**Estado actual:** FALTANTE / PARCIAL via Wompi

**Nota:** Bre-b/Transfiya es infraestructura banco-a-banco, no API merchant directa. Accesible via red de partners de Wompi (cobertura parcial según banco del cliente). No es API directa — la exposición es via Wompi automáticamente.

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P1** | S (piggyback R3.1) | 7 |

---

## R4 — Imagen Profesional (PDF)

### R4.1 — Facturas PDF con Branding del Tenant

**Requisito:** Plantillas de factura PDF con logo y colores primarios del tenant.

**Estado actual:** PARCIAL

**Verificado en codebase:**
- `backend/app/servicios/servicio_pdf.py` — ReportLab ACTIVO y operacional
  - Importa: `reportlab.lib.colors`, `reportlab.platypus.Image as RLImage`
  - Genera facturas y cotizaciones completamente funcionales
- `backend/app/datos/modelos_tenant.py:99` — columna `url_logo = Column(Text)` EXISTS
- `backend/app/datos/esquemas.py:1314,1337,1360` — `url_logo: Optional[str]` en schemas
- `backend/app/servicios/servicio_almacenamiento.py` — S3 boto3 scaffolded, `S3_ENABLED=false`

**Brecha específica (solo branding layer faltante):**
- Columna `brand_config JSONB` en tabla `tenants` — para colores primario/secundario y preferencia de fuente
  - Restricción: NO hasta Phase 2+ en `modelos.py` → diferida a Phase 3
  - El campo `url_logo` ya existe, solo faltan colores
- Extensión de `servicio_pdf.py` para leer `brand_config` del tenant y aplicar colores via `colors.HexColor()`
- Activación S3: `S3_ENABLED=true` + `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` en Railway
- Endpoint `GET /facturas/{id}/pdf-branded` (el actual genera PDF genérico sin branding)

**Brecha de infraestructura crítica:** S3 bucket `chandelier-documents` — existencia no verificada.
- Acción del propietario: Verificar en AWS Console us-east-1 antes de Phase 3
- Riesgo: si el bucket no existe, activar S3_ENABLED=true causará errores en producción

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P0** | M | 8 |

---

### R4.2 — Catálogo PDF de Productos

**Requisito:** Catálogo de productos descargable en PDF, compartible por WhatsApp.

**Estado actual:** FALTANTE

**Brecha específica:**
- Extensión de `servicio_pdf.py` con template de catálogo (grid de productos con imagen, nombre, precio)
- Endpoint `GET /productos/catalogo-pdf` en `backend/app/rutas/productos.py`
- Botón "Descargar Catálogo" en frontend ProductosPage
- Depende de S3 activo para almacenar y generar URL pública compartible

**Nota:** ReportLab ya soporta tablas e imágenes — la extensión es incremental, no un reemplazo.

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P1** | M | 7 |

---

## R5 — Cumplimiento y Legal DIAN

### R5.1 — Widget de Asistente DIAN

**Requisito:** Guía contextual por módulo: IVA, retenciones, bases imponibles.

**Estado actual:** FALTANTE

**Brecha específica:**
- Contenido estático: Markdown con guías DIAN (IVA bimestral, renta anual, retenciones)
  - Estrategia: estático para MVP, LLM en Phase 2+ para respuestas dinámicas
- `frontend/src/components/dian/AsistenteDIANWidget.tsx` — widget colapsable por módulo
- Integración contextual: widget en FacturasPage muestra guía IVA, en RecetasPage muestra guía costos deducibles

**Restricción de alcance:** Solo guía informativa — NO contabilidad certificada DIAN.

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P1** | S | 7 |

---

### R5.2 — Recordatorios de Declaración

**Requisito:** Alertas automáticas para fechas de declaración IVA bimestral y renta anual.

**Estado actual:** FALTANTE

**Brecha específica:**
- Cron job Railway (variable `CRON_SCHEDULE` o Railway scheduled tasks) — evaluación mensual de fechas
- `backend/app/servicios/servicio_dian.py` — lógica de calendario tributario
- Notificación: email (ya existe infraestructura de correo?) o WhatsApp (depende de R2.1)
- Calendario configurable por tipo de empresa: régimen simplificado vs ordinario

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P1** | S | 6 |

---

## R6 — Modelo Freemium

### R6.1 — Tier Gratuito con Límites Configurables

**Requisito:** Plan gratuito con límites por tenant (X facturas/mes, Y productos, Z recetas).

**Estado actual:** FALTANTE

**Verificado en codebase:**
- `backend/app/middleware/` — solo `tenant_context.py` y `user_context.py`, sin `plan_enforcement.py`
- `backend/app/servicios/` — sin `servicio_planes.py`
- No hay lógica de límites en ningún servicio

**Brecha específica:**
- `backend/app/middleware/plan_enforcement.py` — decorator `@require_plan('pro')` que lee JWT claim
- `backend/app/servicios/servicio_planes.py` — validación de contadores (facturas_mes, productos, recetas)
- Límites base recomendados para Free tier: 20 facturas/mes, 50 productos, 5 recetas
- Enforcement en capa `servicios/` (nunca en `rutas/`) — alineado con invariantes arquitectónicos

**Patrón arquitectónico correcto:**
```
JWT publicMetadata.plan = "free" | "pro"
→ @require_plan('pro') en endpoint → 403 si plan insuficiente
→ check_limit('facturas_mes', tenant_id) en servicio → 402 si límite alcanzado
```

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P0** | M | 10 |

---

### R6.2 — Feature Flags por Plan

**Requisito:** `plan_id` en metadata del tenant — propagado en JWT para enforcement sin DB lookup.

**Estado actual:** FALTANTE

**Verificado en codebase:**
- Clerk dev keys `pk_test_*` activos en producción (soportan backend API completo)
- No hay `publicMetadata.plan` seteado en ningún tenant actualmente
- No hay integración con Clerk backend API para escribir metadata desde FastAPI

**Brecha específica:**
- Integración Clerk backend API en `backend/app/servicios/servicio_planes.py`:
  - `PATCH /users/{clerk_user_id}/metadata` con `public_metadata: {"plan": "free"}`
- Seed script para setear plan "free" en todos los tenants existentes
- Lectura de claim en `get_current_user()` — ya disponible en JWT, solo falta leer `.public_metadata`

**Decisión de storage:** Clerk `publicMetadata` (no tabla DB).
- Ventajas: propagado en cada JWT (cero DB roundtrip), modificable via Clerk backend API, secure (solo servidor)
- No usar `unsafeMetadata` (client-settable = riesgo de seguridad)
- Alineado con restricción "no migrations hasta Phase 4+"

**Brecha de infraestructura:** Clerk dev keys en producción limitan funcionalidades de auth avanzadas.
- Acción del propietario: Migrar a `pk_live_*` / `sk_live_*` antes de Phase 6 launch
- Las dev keys sí soportan `publicMetadata` write via backend API — no bloquea el desarrollo

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P0** | S | 10 |

---

### R6.3 — Upgrade Flow

**Requisito:** Paywall contextual que aparece cuando el tenant alcanza el límite del plan gratuito.

**Estado actual:** FALTANTE

**Brecha específica:**
- `frontend/src/hooks/usePlanLimits.ts` — hook que lee claim del JWT y expone `isAtLimit()`, `canUse(feature)`
- `frontend/src/components/ui/UpgradePrompt.tsx` — modal/banner contextual con CTA de upgrade
- `backend/app/rutas/` — respuesta estructurada de error `402 Payment Required` con campo `upgrade_url`
- Integración con pasarela de pagos para suscripción (depende de R3 para pagos locales)

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P1** | M | 8 |

---

## R7 — Localismo Digital

### R7.1 — Onboarding con Ejemplos Locales

**Requisito:** Wizard de onboarding con ejemplos de negocios reales de Palmira (velas, confites, artesanías).

**Estado actual:** FALTANTE

**Verificado en codebase:**
- `frontend/src/components/onboarding/OnboardingWizard.tsx` — ejemplos genéricos
- `OnboardingWizard.tsx:44` — código de producto `'PROD-${Date.now()}'` (ya corregido en PR #77)
- Sin ejemplos de productos locales ni copy adaptado

**Brecha específica:**
- Actualización de copy en `OnboardingWizard.tsx`: nombre de empresa placeholder → "Velas Luna de Palmira"
- Ejemplos de productos de muestra: "Vela Aromática", "Confite Artesanal", "Macramé Decorativo"
- Sin nuevas dependencias — cambio de copy y UX únicamente

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P1** | S | 6 |

---

### R7.2 — Métodos de Pago Regionales Visibles en UI

**Requisito:** Nequi y Daviplata como primera opción visual en la UI de cobro.

**Estado actual:** FALTANTE

**Dependencias:** R3.1 (integración Wompi) — sin pagos no hay qué mostrar.

**Brecha específica:**
- `frontend/src/components/facturas/MetodosPagoPanel.tsx` — ordenamiento visual: Nequi > Daviplata > PSE > Tarjeta
- Logos de Nequi y Daviplata como iconos visuales prominentes
- Esfuerzo mínimo si R3.1 ya provee los endpoints

| Severidad | Esfuerzo | Impacto |
|-----------|----------|---------|
| **P1** | S | 7 |

---

## Brechas de Infraestructura (Transversales)

| Brecha | Acción del Propietario | Severidad | Fase Bloqueada |
|--------|----------------------|-----------|---------------|
| S3 bucket `chandelier-documents` — existencia no verificada en AWS | Verificar en AWS Console us-east-1 | P0 | Phase 3 |
| Clerk dev keys (`pk_test_*`) en producción | Migrar a `pk_live_*` / `sk_live_*` en Clerk Dashboard | P1 | Phase 6 |
| Registro WABA (BSP onboarding) — lead time 24–48h | Iniciar cuenta BSP: WATI (wati.io) o 360dialog | P0 | Phase 5 |
| Cuenta Wompi producción — no registrada | Registrar en wompi.com/negocios | P0 | Phase 4 |
| `ANTHROPIC_API_KEY` env var en Railway — no configurada | Agregar via Railway Dashboard → Environment | P0 | Phase 2 |

---

## Registro de Riesgos

| Riesgo | Fase | Probabilidad | Impacto | Mitigación |
|--------|------|-------------|---------|------------|
| API Nequi directa — proceso certificación >2 semanas | 4 | ALTA | ALTA | Usar Wompi (cubre Nequi de forma nativa, sandbox inmediato) |
| WeasyPrint en Railway — `libgobject-2.0-0` ausente en runtime | 3 | ALTA | ALTA | Mantener ReportLab (ya instalado y funcional) |
| Costo spike mensajes marketing WhatsApp | 5 | MEDIA | MEDIA | Solo utility templates para facturas ($0.0008 vs $0.0125 marketing); rate limit por tenant |
| Clerk `unsafeMetadata` usado para flags de plan | 6 | MEDIA | ALTA | Siempre usar `publicMetadata` (solo servidor puede escribir) |
| Corrupción Decimal en output LLM | 2 | BAJA | CRÍTICA | Castear SIEMPRE a `Decimal(str(raw_value))` en Pydantic model antes de almacenar |
| S3 bucket no provisionado en AWS | 3 | MEDIA | ALTA | Verificar antes de iniciar Phase 3; si no existe, crear bucket `chandelier-documents` en us-east-1 |
| Verificación WABA — requisito NIT colombiano | 5 | MEDIA | ALTA | BSP maneja cumplimiento; reduce fricción de verificación Meta |

---

## Tabla Resumen de Brechas

| Req | Descripción | Estado | Severidad | Esfuerzo | Impacto |
|-----|-------------|--------|-----------|----------|---------|
| R1.1 | IA Costeo | FALTANTE | P0 | M | 9 |
| R1.2 | Descripciones IA | FALTANTE | P1 | S | 7 |
| R2.1 | WhatsApp API | FALTANTE | P0 | L | 9 |
| R2.2 | Link pago WhatsApp | FALTANTE | P1 | S | 8 |
| R3.1 | Nequi (Wompi) | FALTANTE | P0 | L | 10 |
| R3.2 | Daviplata (Wompi) | FALTANTE | P1 | S | 9 |
| R3.3 | Bre-b | FALTANTE | P1 | S | 7 |
| R4.1 | PDF Branding | PARCIAL | P0 | M | 8 |
| R4.2 | Catálogo PDF | FALTANTE | P1 | M | 7 |
| R5.1 | Widget DIAN | FALTANTE | P1 | S | 7 |
| R5.2 | Recordatorios DIAN | FALTANTE | P1 | S | 6 |
| R6.1 | Tier gratuito | FALTANTE | P0 | M | 10 |
| R6.2 | Feature flags | FALTANTE | P0 | S | 10 |
| R6.3 | Upgrade flow | FALTANTE | P1 | M | 8 |
| R7.1 | Onboarding local | FALTANTE | P1 | S | 6 |
| R7.2 | UI pagos regionales | FALTANTE | P1 | S | 7 |

**Brechas P0:** 6 (requieren resolución inmediata en Phases 2–6)
**Brechas P1:** 10 (alto valor, planificar una vez P0s resueltos)
**PARCIAL:** 1 (R4.1 — ReportLab existe y operacional, falta capa de branding: `brand_config` + colores)
**EXISTE/COMPLETO:** 0 de los requisitos R1–R7

---

## Estado Verificado del Codebase (Baseline PR #104)

Los siguientes módulos están operacionales en producción y NO son brechas:

| Módulo | Estado | Archivos Clave |
|--------|--------|---------------|
| Auth Clerk → FastAPI JWT | EXISTE | `backend/app/rutas/auth.py`, `middleware/tenant_context.py` |
| Multi-tenancy + RLS | EXISTE | `datos/modelos_tenant.py`, `middleware/tenant_context.py` |
| Productos + Inventario | EXISTE | `rutas/inventarios.py`, `servicios/` |
| Facturas + POS | EXISTE | `rutas/facturas.py`, `rutas/` |
| Recetas + CVU (CIF distribuido) | EXISTE | `rutas/recetas.py`, `servicios/` |
| PDF generation (genérico) | EXISTE | `servicios/servicio_pdf.py` (ReportLab activo) |
| S3 scaffolding (desactivado) | PARCIAL | `servicios/servicio_almacenamiento.py` (`S3_ENABLED=false`) |
| Logo URL por tenant | EXISTE | `datos/modelos_tenant.py:99` (`url_logo = Column(Text)`) |
| Contabilidad | EXISTE | `rutas/contabilidad.py` |
| CRM | PARCIAL | `rutas/crm.py` (flag `CRM_UNDER_CONSTRUCTION=true`) |
| PQRS/Soporte | EXISTE | activo |

---

## Notas Arquitectónicas para Fases 2–7

1. **No modificar `modelos.py` hasta Phase 2+** — restricción activa. Las brechas que requieren nuevas columnas (R4.1 `brand_config`, R3.1 `pagos_externos`) están diferidas correctamente.
2. **No agregar migraciones Alembic hasta Phase 4+** — las brechas P0 de Phase 2 y Phase 3 deben resolverse sin schema changes.
3. **Toda nueva funcionalidad hereda tenant isolation automáticamente** — todo endpoint nuevo debe recibir `tenant_id` via dependency injection del contexto de usuario.
4. **Cálculos financieros: solo `Decimal`** — especialmente crítico para R1.1 (output LLM) y R3.1 (montos de pago).
5. **Freemium enforcement: capa `servicios/` únicamente** — nunca en `rutas/`. Consistente con invariantes arquitectónicos del proyecto.
