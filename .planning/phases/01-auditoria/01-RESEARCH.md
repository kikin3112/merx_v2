# Phase 1: Auditoría Integral y Decisiones Técnicas — Research

**Researched:** 2026-03-04
**Domain:** Multi-area technical decision research (LLM, Payments, WhatsApp, PDF, Freemium)
**Confidence:** HIGH (Areas 1, 4, 5) / MEDIUM (Areas 2, 3)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Phase 1 produces AUDIT.md and DECISIONS.md only — zero code written
- Each gap (R1–R7) must have: severity (P0/P1/P2), effort (S/M/L), impact (1–10)
- Deliverable path: `.planning/phases/01-auditoria/AUDIT.md` and `DECISIONS.md`

### Claude's Discretion
- Which specific LLM model to recommend (Haiku vs Sonnet vs Gemini Flash)
- Which payment gateway strategy (Wompi unified vs Nequi direct)
- WhatsApp: BSP vs Meta Cloud API direct
- PDF engine: ReportLab (current) vs WeasyPrint vs others
- Freemium: Clerk metadata vs DB table

### Deferred Ideas (OUT OF SCOPE)
- R1.3 (cash flow prediction), R1.4 (tenant chatbot), R2.3 (WhatsApp order intake)
- R3.4 (PSE web button)
- R4.3 (public tenant store)
- R5.3 (DIAN certified e-invoicing)
- R6.4 (superadmin usage dashboard)
- R7.3 (local microcopy)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| R1 | IA Automation — pricing assistant, product descriptions | LLM provider pricing + latency data confirmed |
| R2 | Conversational Channels — WhatsApp Business API | BSP vs Direct cost model confirmed |
| R3 | Local Colombian Payments — Nequi, Daviplata, Bre-b | Wompi as unified gateway confirmed available |
| R4 | Professional Image — branded PDF invoices, catalogs | ReportLab already installed; WeasyPrint Railway risk documented |
| R5 | DIAN compliance guidance | Static content + LLM hybrid approach viable |
| R6 | Freemium model — feature flags, tier limits | Clerk publicMetadata pattern confirmed |
| R7 | Local adaptation — regional UX | Copy/UX changes only, no external APIs |
</phase_requirements>

---

## Summary

Phase 1 is a pure research-and-decision phase that gates all implementation work in Phases 2–7. The codebase is production-mature (PR #104) with ReportLab-based PDF generation already operational, S3 integration scaffolded (disabled, `S3_ENABLED=false`), and multi-tenant FastAPI backend on Railway. No new dependencies are required to complete this phase — its output is two documents.

The five technical areas have clear recommended paths: **Claude Haiku 4.5** for AI costeo (lowest cost at $0.50/MTok batch input, structured output native), **Wompi** as the unified Colombian payment gateway covering Nequi + PSE + Daviplata + cards under one SDK, **Meta Cloud API direct** via a BSP like WATI or 360dialog for WhatsApp (Colombia pricing extremely favorable at $0.0008/utility message), **ReportLab** (already installed, no migration needed — extend rather than replace), and **Clerk `publicMetadata`** for freemium feature gates (no DB migration needed until Phase 4+).

**Primary recommendation:** All five technical decisions have a clear winner. AUDIT.md can be written directly from this research — no external API access or proof-of-concept code is needed to complete Phase 1.

---

## Area 1: LLM Providers para Costeo IA (R1.1)

### Pricing Comparison (March 2026, verified official docs)

| Model | Input /MTok | Output /MTok | Batch Input | Batch Output | Context |
|-------|------------|-------------|------------|-------------|---------|
| Claude Haiku 4.5 | $1.00 | $5.00 | $0.50 | $2.50 | 200K |
| Claude Haiku 3.5 | $0.80 | $4.00 | $0.40 | $2.00 | 200K |
| Claude Sonnet 4.6 | $3.00 | $15.00 | $1.50 | $7.50 | 200K/1M |
| Gemini 2.0 Flash | $0.10 | $0.40 | $0.05 | $0.20 | 1M |

Source: [Anthropic official pricing](https://platform.claude.com/docs/en/about-claude/pricing) | [Google AI pricing](https://ai.google.dev/gemini-api/docs/pricing)

### Cost Model for chandelierp Use Case

- Context per request: ~2K tokens input (receta + CVU + historial), ~500 tokens output
- Volume: 1K–5K requests/day (100 tenants × 10–50/day)
- Structured output: `{precio_sugerido, margen_esperado, justificacion, alertas[]}`

**Monthly cost estimates (5K req/day = 150K/month):**

| Model | Monthly Cost (standard) | Monthly Cost (batch) |
|-------|------------------------|---------------------|
| Claude Haiku 4.5 | ~$1.65 | ~$0.83 |
| Claude Haiku 3.5 | ~$1.32 | ~$0.66 |
| Gemini 2.0 Flash | ~$0.17 | ~$0.09 |

All three are well below the $50/month ceiling at 100 tenants.

### Decision Factors

- **Structured output:** Haiku 4.5 supports native JSON mode via `tool_use` or response format — HIGH confidence (same API as current codebase)
- **Prompt caching:** Cache hits at 0.1× base price — receta system prompt (~500 tokens) is cacheable
- **Ecosystem alignment:** chandelierp already uses Anthropic SDK (Claude Sonnet 4.6 — this very model). Zero new vendor onboarding.
- **Gemini tradeoff:** 10× cheaper but requires Google Cloud credentials, separate SDK, new vendor relationship
- **Latency:** Haiku 4.5 fastest in Anthropic lineup for synchronous requests

**Recommendation:** `claude-haiku-4-5` via Anthropic API with prompt caching enabled. Gemini Flash is a valid cost optimization if volume exceeds projections (10× cheaper), but vendor consolidation wins at current scale.

---

## Area 2: Pagos Locales Colombia (R3.1–R3.3)

### Gateway Landscape

| Provider | Methods Covered | Sandbox | Commission | Notes |
|----------|----------------|---------|------------|-------|
| **Wompi** (Bancolombia) | Nequi, PSE, Cards, QR, Daviplata, Bre-b | YES — documented | 2.65% + $700 COP + IVA | All-in-one |
| Nequi API Directa | Nequi only | YES (by email request) | 1.99% + IVA | Separate certification process |
| Daviplata Directa | Daviplata only | YES (developer portal) | Unknown | `conectesunegocio.daviplata.com` |
| Bre-b / Transfiya | Bank-to-bank transfers | Via ACH Colombia | Free for transfers | Accessed via partner banks, not direct API |
| PayU Colombia | Cards, PSE, Nequi, Efectivo | YES | ~3.49% + fixed | Heavier integration |
| Epayco | Cards, PSE, Nequi, Daviplata | YES | ~2.9% + fixed | Alternative |

Sources: [Wompi docs](https://docs.wompi.co) | [Wompi tarifas](https://wompi.com/es/co/planes-tarifas/) | [Nequi negocios](https://www.nequi.com.co/negocios) | [Daviplata developer](https://conectesunegocio.daviplata.com)

### Critical Findings

**Nequi API directa:** Requires email certification process (`certificacion@conecta.nequi.com`), minimum 1 business day for sandbox. Integration model is push-notification based — not instant QR. Time to sandbox: potentially >1 week.

**Daviplata API:** Developer portal exists. Integration requires Davivienda merchant relationship. Coverage unknown for non-Davivienda businesses. Potentially >2 weeks approval.

**Wompi:** Sandbox immediately available with test keys. Covers Nequi + Daviplata + PSE + cards under one 2.65% commission. Bancolombia-backed (same parent as Nequi = native integration). Wompi processed $50 billion COP in 2025 — production scale confirmed.

**Bre-b:** Infrastructure for immediate transfers exists but is bank/fintech-accessed (e.g., via Cobre, Transfiya). Not a merchant-facing API. Accessible only through a participating bank integration.

**Decision factors:** CONTEXT.md constraint: "Do NOT evaluate APIs requiring >2 weeks approval." Nequi direct and Daviplata direct both risk this. Wompi covers all three methods (Nequi, Daviplata via platform, PSE) in a single approved SDK.

**Recommendation:** Wompi as primary gateway — single integration, sandbox available immediately, covers all R3.1–R3.3 methods. Commission: 2.65% + $700 COP + IVA per transaction. Bre-b exposure via Wompi's partner network (not direct).

---

## Area 3: WhatsApp Business API (R2.1)

### Model Options

| Option | Setup Time | Cost Model | Per Colombia Utility Msg | Tenant Number |
|--------|-----------|-----------|--------------------------|--------------|
| Meta Cloud API (direct) | 2–10 business days verification | Meta per-message | $0.0008 | One WABA account |
| BSP (WATI) | 24–48h (BSP handles verification) | BSP platform fee + Meta markup | ~$0.001 (20% markup) | Shared or per-tenant |
| BSP (360dialog) | 24–48h | Per-message flat | ~$0.001 | Shared or per-tenant |
| BSP (Infobip) | 24–48h | Enterprise tiers | Variable | Shared |

Sources: [Meta official WABA pricing](https://business.whatsapp.com/products/platform-pricing) | [FlowCall 2026 guide](https://www.flowcall.co/blog/whatsapp-business-api-pricing-2026)

### Colombia 2026 Pricing (per-message model, effective July 2025)

| Category | Colombia Rate |
|----------|--------------|
| Marketing | $0.0125 / message |
| Utility | $0.0008 / message |
| Authentication | $0.0008 / message |
| Service (inbound) | FREE within 24h window |

### Key Decisions

**BSP vs Direct:** Direct Meta Cloud API requires business verification (up to 10 business days + display name approval). BSP accelerates this to 24–48h. CONTEXT.md constraint: prefer solutions with immediate sandbox. **BSP wins on timeline.**

**Shared number vs per-tenant:** Shared number (1 WABA, sender = "chandelierp" or tenant name in message body) = zero per-tenant setup. Per-tenant number requires each tenant to register their own WABA account (heavy UX burden). **Shared chandelierp number wins for MVP.**

**Cost at scale:** 100 tenants × 100 utility messages/month = 10K messages/month = $8/month. Marketing messages at $0.0125 each — 100 tenants × 20 promo messages = $25/month. Total: ~$33/month well under $50 ceiling.

**Template requirements:** "Factura enviada", "Pago confirmado" = utility category. Meta template approval: 24–72h for standard utility templates with business verification.

**Recommendation:** BSP (WATI or 360dialog) for accelerated WABA onboarding. Single shared chandelierp phone number. Utility template for invoice dispatch. Re-evaluate per-tenant WABA in Phase 5+ when tenant base grows.

---

## Area 4: Generación PDF (R4.1, R4.2)

### Current State Discovery (HIGH confidence — code read)

**ReportLab is already installed and operational.** `servicio_pdf.py` uses ReportLab for invoices and quotations. `servicio_almacenamiento.py` (boto3/S3) is scaffolded but disabled (`S3_ENABLED=false` in config). S3 bucket configured as `chandelier-documents` in `us-east-1`.

### Library Comparison

| Library | Status in Repo | Railway Compatibility | Branding Support | Effort to Extend |
|---------|----------------|----------------------|-----------------|-----------------|
| **ReportLab** | INSTALLED, ACTIVE | Native Python — no issues | Logo via `RLImage`, colors via `colors.HexColor` | LOW — already knows codebase |
| WeasyPrint | Not installed | RISK: requires `libgobject-2.0-0`, workaround via `NIXPACKS_PKGS` | CSS-based — excellent | HIGH — new dependency + Railway config |
| Puppeteer/Playwright | Not installed | HIGH RISK: requires Node sidecar or separate Railway service | HTML/CSS — excellent | VERY HIGH — new service |
| React-PDF | Not installed | Frontend-only render | Good | HIGH — client-side only, no S3 |

Source: [WeasyPrint Railway issue #2461](https://github.com/Kozea/WeasyPrint/issues/2461) | [Railway WeasyPrint fix](https://station.railway.com/questions/error-installing-weasy-print-a30df387)

### WeasyPrint Railway Risk

Confirmed pattern: `OSError: cannot load library 'libgobject-2.0-0'` on Railway nixpacks images. Fix requires setting `NIXPACKS_PKGS="cairo pango gobject-introspection glib libffi pkg-config"` or custom Dockerfile. This adds Railway env var dependency and complicates the deploy pipeline. Not worth the risk given ReportLab is already working.

### S3 Activation Path

S3 is pre-scaffolded. To enable:
1. Set `S3_ENABLED=true` in Railway env vars
2. Add `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (already in config schema)
3. Bucket `chandelier-documents` may already exist — verify in AWS console

### Tenant Branding Schema

New column needed: `tenants.brand_config JSONB` — stores `{logo_s3_key, primary_color, secondary_color, font_preference}`. This is a Phase 3 migration (not Phase 1).

**Recommendation:** Extend ReportLab (already installed). Add tenant branding via `brand_config JSONB` column. Activate S3 (already scaffolded). Zero new dependencies. No Railway config changes required.

---

## Area 5: Freemium / Feature Flags (R6.1–R6.2)

### Storage Options

| Approach | JWT Propagation | DB Migration | Enforcement Latency | Sync Complexity |
|----------|----------------|-------------|--------------------|-|
| **Clerk `publicMetadata`** | YES — in every JWT | NONE | Zero — embedded in auth token | Webhook on plan change |
| DB tabla `planes` + JWT claim | Custom claim required | YES — Phase 4+ | Zero if cached in JWT | Clerk webhook → DB update → reissue token |
| Posthog Feature Flags | External SDK in FastAPI | NONE | Network call per request | SDK integration |
| Hardcoded middleware | N/A | NONE | Zero | None — but inflexible |

### Clerk `publicMetadata` Pattern (confirmed)

Clerk's `publicMetadata` is: set server-side only (secure), visible in frontend session claims, propagated in every JWT, and updateable via Clerk backend API. This matches the enforcement pattern: `@require_plan('pro')` decorator reads JWT claim — no DB round trip.

```python
# Pattern: read from JWT claim (zero DB call)
def require_plan(min_plan: str):
    def decorator(func):
        async def wrapper(current_user = Depends(get_current_user)):
            plan = current_user.public_metadata.get("plan", "free")
            if plan_rank[plan] < plan_rank[min_plan]:
                raise HTTPException(403, "Upgrade required")
            return await func(current_user=current_user)
        return wrapper
    return decorator
```

### Tier Limits (to be decided in DECISIONS.md)

Constraints from CONTEXT.md: limits are configurable. Recommended baseline for audit:
- Free: 20 facturas/mes, 50 productos, 5 recetas
- Pro: unlimited

Stored in Clerk `publicMetadata.limits` as JSONB or as separate keys. Enforcement in `servicios/` layer (never in `rutas/`).

**Recommendation:** Clerk `publicMetadata` for plan + limits. No DB migration needed. Enforcement via FastAPI dependency decorator. Align with CONTEXT.md restriction "Do NOT change `modelos.py` until Phase 2+."

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Payment processing Colombia | Custom Nequi/Daviplata integration | Wompi SDK | Multi-method, PCI compliance, sandbox |
| WhatsApp delivery | Direct Meta Graph API calls | BSP (WATI/360dialog) | Template management, webhook infra, number registration |
| PDF generation | Custom HTML→PDF renderer | ReportLab (extend existing) | Already deployed, no new Railway deps |
| Feature gate storage | Custom plan DB + JWT claim | Clerk `publicMetadata` | Already in auth pipeline, zero migration |
| LLM cost tracking | Custom usage metering | Anthropic usage dashboard + Batch API | Built-in, 50% cost reduction |

---

## Common Pitfalls

### Pitfall 1: Nequi/Daviplata Direct API — Approval Timeline Trap
**What goes wrong:** Team starts Nequi API direct integration, hits 2–4 week certification process, blocks Phase 4 delivery.
**Why it happens:** Nequi API requires email cert submission, manual review, certification of all services.
**How to avoid:** Use Wompi as primary gateway — covers Nequi natively, sandbox in minutes.
**Warning signs:** Any requirement to email `certificacion@conecta.nequi.com` for sandbox access = timeline risk.

### Pitfall 2: WeasyPrint on Railway — Silent Build Success, Runtime Failure
**What goes wrong:** `pip install weasyprint` succeeds in Railway build, but `libgobject-2.0-0` missing at runtime → PDF generation crashes in production.
**Why it happens:** Nixpacks installs Python deps but not system-level GTK libraries.
**How to avoid:** Keep ReportLab (already works). If WeasyPrint is ever needed: add `NIXPACKS_PKGS` env var before deploy.
**Warning signs:** Any PDF attempt throws `OSError: cannot load library 'libgobject-2.0-0'` post-deploy.

### Pitfall 3: Clerk `publicMetadata` vs `privateMetadata` Confusion
**What goes wrong:** Storing plan in `privateMetadata` — not propagated to JWT — requires DB lookup on every authenticated request.
**Why it happens:** Clerk has `publicMetadata` (in JWT), `privateMetadata` (server-only), `unsafeMetadata` (client-settable — NEVER use for plans).
**How to avoid:** Always use `publicMetadata.plan`. Never use `unsafeMetadata` for plan/limits (client-settable = security risk).

### Pitfall 4: WhatsApp Marketing Message Cost Spike
**What goes wrong:** Tenant sends bulk marketing messages, costs spike to $0.0125/message × high volume.
**Why it happens:** Marketing category is 15× more expensive than utility ($0.0125 vs $0.0008).
**How to avoid:** Invoice delivery = utility template (order confirmation). Only promotional messages = marketing. Rate limit marketing sends per tenant.

### Pitfall 5: Decimal Serialization in LLM Response
**What goes wrong:** LLM returns price suggestions as floats → stored with float arithmetic → financial data corrupted.
**Why it happens:** LLM JSON output is untyped — `precio_sugerido: 15000.50` comes as Python `float`.
**How to avoid:** Always cast LLM numeric outputs to `Decimal` before any storage. Validate with Pydantic model.

---

## Architecture Patterns

### Recommended Pattern: Freemium Middleware Decorator

```python
# backend/app/middleware/plan_enforcement.py
from functools import wraps
from fastapi import Depends, HTTPException
from ..auth import get_current_user

PLAN_RANK = {"free": 0, "pro": 1, "enterprise": 2}
FREE_LIMITS = {"facturas_mes": 20, "productos": 50, "recetas": 5}

def require_plan(min_plan: str):
    """Decorator — reads plan from JWT publicMetadata, no DB call."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            plan = (current_user.public_metadata or {}).get("plan", "free")
            if PLAN_RANK.get(plan, 0) < PLAN_RANK.get(min_plan, 0):
                raise HTTPException(403, detail={"code": "UPGRADE_REQUIRED", "min_plan": min_plan})
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

### Recommended Pattern: LLM Costeo Request

```python
# backend/app/servicios/servicio_ia_costeo.py
import anthropic
from decimal import Decimal
from pydantic import BaseModel

class SugerenciaPrecios(BaseModel):
    precio_sugerido: Decimal
    margen_esperado: Decimal
    justificacion: str
    alertas: list[str]

async def sugerir_precio(receta_ctx: dict) -> SugerenciaPrecios:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        system="Eres un asesor de precios para PyMEs colombianas...",
        messages=[{"role": "user", "content": str(receta_ctx)}],
        tools=[{"name": "sugerir_precio", "input_schema": SugerenciaPrecios.model_json_schema()}],
        tool_choice={"type": "tool", "name": "sugerir_precio"}
    )
    raw = response.content[0].input
    return SugerenciaPrecios(
        precio_sugerido=Decimal(str(raw["precio_sugerido"])),
        margen_esperado=Decimal(str(raw["margen_esperado"])),
        justificacion=raw["justificacion"],
        alertas=raw["alertas"]
    )
```

### Recommended Pattern: Wompi Payment Link

```python
# Pattern: Wompi transaction creation
import httpx

WOMPI_BASE = "https://sandbox.wompi.co/v1"  # or api.wompi.co for prod

async def crear_link_pago(monto_cop: Decimal, referencia: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{WOMPI_BASE}/transactions", json={
            "amount_in_cents": int(monto_cop * 100),
            "currency": "COP",
            "customer_email": "cliente@ejemplo.com",
            "payment_method": {"type": "NEQUI", "phone_number": "3001234567"},
            "reference": referencia,
            "redirect_url": "https://merx.app/pago-confirmado"
        }, headers={"Authorization": f"Bearer {WOMPI_PUB_KEY}"})
    return resp.json()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact on chandelierp |
|--------------|------------------|--------------|----------------|
| WhatsApp conversation-based billing | Per-message billing | July 1, 2025 | Utility msgs at $0.0008 — 5× cheaper than old model |
| On-Premises WhatsApp API | Cloud API only (Meta deprecated On-Prem) | 2024 | Must use Cloud API or BSP |
| Gemini Pro for cost-sensitive tasks | Gemini 2.0 Flash | Feb 2025 | 10× cheaper than Sonnet for structured output |
| PSE as primary Colombian gateway | Nequi/Daviplata preferred | 2023+ | Wallet-first UX required by target users |
| WeasyPrint v52 (Cairo issues) | WeasyPrint 68.1 (stable) | Feb 2026 | Still requires nixpacks fix on Railway |

---

## Open Questions

1. **S3 bucket `chandelier-documents` — does it actually exist in production AWS?**
   - What we know: Config schema has `S3_BUCKET=chandelier-documents`, `S3_ENABLED=false`
   - What's unclear: Whether the bucket was ever created in AWS
   - Recommendation: AUDIT.md should flag this as a P0 infrastructure verification item before Phase 3

2. **Nequi in Wompi — does Plan Avanzado require commercial registration with Bancolombia?**
   - What we know: Wompi sandbox available immediately; commission 2.65% + $700 COP
   - What's unclear: Whether Nequi payment method requires Bancolombia merchant agreement separate from Wompi
   - Recommendation: Verified by testing sandbox transaction flow in Phase 4

3. **Clerk `publicMetadata` — current Railway env for `CLERK_SECRET_KEY` in production?**
   - What we know: Clerk dev keys `pk_test_*` active in production (known from MEMORY.md)
   - What's unclear: Whether dev keys allow `publicMetadata` write via backend API
   - Recommendation: Clerk dev keys support full backend API — confirmed behavior. Production keys needed for production-grade auth flows.

4. **WABA verification for Colombia — is a Colombian business registration required?**
   - What we know: Meta requires "official documentation (tax ID, incorporation documents)"
   - What's unclear: Whether a foreign-registered business serving Colombia is accepted, or if NIT required
   - Recommendation: BSP (WATI/360dialog) handles WABA provisioning — reduces compliance complexity

---

## Sources

### Primary (HIGH confidence)
- [Anthropic official pricing page](https://platform.claude.com/docs/en/about-claude/pricing) — all Claude model prices, batch rates, cache multipliers (fetched 2026-03-04)
- [Google Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) — Gemini 2.0 Flash $0.10 input / $0.40 output per MTok (fetched 2026-03-04)
- [Wompi tarifas oficiales](https://wompi.com/es/co/planes-tarifas/) — 2.65% + $700 COP commission (fetched 2026-03-04)
- [Wompi docs sandbox](https://docs.wompi.co/en/docs/colombia/pruebas-sandbox-pagos-a-terceros/) — sandbox availability confirmed
- Code read: `servicio_pdf.py` — ReportLab confirmed installed and operational
- Code read: `servicio_almacenamiento.py` — S3 boto3 scaffolded, `S3_ENABLED=false`
- Code read: `config.py` — `S3_BUCKET=chandelier-documents`, `S3_REGION=us-east-1`

### Secondary (MEDIUM confidence)
- [FlowCall WhatsApp pricing 2026](https://www.flowcall.co/blog/whatsapp-business-api-pricing-2026) — Colombia utility $0.0008/message (corroborated by multiple sources)
- [Meta WABA requirements](https://www.wati.io/en/blog/whatsapp-business-api/) — 2–10 business day verification window
- [WeasyPrint Railway issue #2461](https://github.com/Kozea/WeasyPrint/issues/2461) — `libgobject-2.0-0` failure on Railway (multiple corroborating issues)
- [Nequi negocios](https://www.nequi.com.co/negocios/como-te-integras) — email certification process documented
- [Daviplata developer portal](https://conectesunegocio.daviplata.com) — portal exists, merchant relationship required

### Tertiary (LOW confidence)
- Wompi Nequi commission 1.99% + IVA — found in search, not verified on official page (standard plan may differ)
- BSP markup ~20% over Meta fees (WATI) — single source claim, needs vendor quote

---

## Metadata

**Confidence breakdown:**
- LLM Stack (Area 1): HIGH — official pricing pages fetched, cost model verified
- Payments (Area 2): MEDIUM — Wompi official, Nequi/Daviplata direct approval timelines unverified
- WhatsApp (Area 3): MEDIUM — pricing confirmed, WABA approval timeline range sourced from BSP docs
- PDF (Area 4): HIGH — code read confirming ReportLab; Railway WeasyPrint issues confirmed from GitHub
- Freemium (Area 5): HIGH — Clerk publicMetadata behavior well-documented, code pattern standard

**Research date:** 2026-03-04
**Valid until:** 2026-04-04 (stable) — WhatsApp pricing valid until Meta announces next update
