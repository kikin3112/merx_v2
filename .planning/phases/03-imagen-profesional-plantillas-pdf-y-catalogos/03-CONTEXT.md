# Phase 3: Imagen Profesional — Plantillas PDF y Catálogos — Context

**Gathered:** 2026-03-06
**Status:** Ready for planning
**Source:** discuss-phase session (2026-03-06 morning, decisions recovered from memory obs #1987)

<domain>
## Phase Boundary

Entregar documentos profesionales con branding del tenant: facturas PDF con logo y
colores del negocio, y catálogo de productos descargable/compartible por WhatsApp.

**En scope:**
- Logo upload por tenant → S3 → aplicado en PDFs de facturas y cotizaciones
- Colores configurables (color_primario, color_secundario) aplicados en PDFs
- Nueva pestaña "Marca" en ConfigPage para gestionar logo + colores + preview
- Catálogo PDF: selección manual de productos, imagen por producto, streaming
- Pre-signed URLs para PDFs de facturas (1 hora de expiración)
- Nueva página /catalogo en frontend

**Fuera de scope:**
- Múltiples templates de factura
- Editor WYSIWYG de PDF
- Notificaciones WhatsApp (Phase 5)
- Pagos (Phase 4)

</domain>

<decisions>
## Implementation Decisions

### Motor PDF
- **Motor:** ReportLab — ya instalado, ya usado en `servicio_pdf.py` para facturas
- **NO WeasyPrint, NO Puppeteer** — evitar dependencias adicionales en Railway

### Logo Upload
- **Mecanismo:** file upload desde ConfigPage → S3 bucket existente → path `tenants/{tenant_id}/logo.png`
- **Campo DB:** `url_logo` en tabla `Tenants` — YA EXISTE, no requiere migración
- **Formatos aceptados:** JPG y PNG únicamente, máximo 2MB
- **Fallback:** sin logo → PDF muestra solo nombre de empresa (comportamiento actual)
- **Aplica a:** facturas Y cotizaciones (ambos documentos)

### Colores en PDF
- **Aplicación:** Header + headers tabla + totals box + footer (máximo branding)
- **Texto sobre colores:** auto-contraste por luminancia WCAG (blanco u oscuro según el color)
- **Campos DB:** `color_primario` y `color_secundario` en tabla `Tenants` — YA EXISTEN, no requiere migración
- **Default `color_primario`:** `#1976D2` (ya en DB)

### ConfigPage — Pestaña "Marca"
- **Nueva pestaña** "Marca" en la ConfigPage existente
- **Contenido:** logo upload + preview de logo actual + color_primario picker + color_secundario picker
- **Preview inline:** muestra header PDF con colores seleccionados (sin generar PDF real, solo CSS)
- **Guardado:** PATCH `/api/v1/tenants/{id}` con campos existentes

### Pre-signed URLs para Facturas PDF
- **Patrón:** VentasPage llama `GET /facturas/{id}/pdf-url` → recibe pre-signed URL con expiración 1h → abre nueva pestaña
- **DB:** `url_pdf` guarda S3 key (no URL directa)
- **React Query:** sin cacheo de la URL (siempre fresca para evitar expiración)
- **Backend:** S3 `generate_presigned_url` con `ExpiresIn=3600`

### Catálogo PDF
- **Selección:** manual por checkboxes — el usuario elige qué productos incluir
- **Contenido por producto:** nombre + descripción + precio + imagen (si existe)
- **Fotos de productos:** upload desde ficha de producto → S3 `tenants/{tenant_id}/products/{product_id}.jpg` → guardado en campo `imagen_s3_key`
- **Frontend:** nueva página `/catalogo` — grid de tarjetas con checkboxes + barra sticky "Generar PDF"
- **Sidebar:** nuevo item "Catálogo" en grupo Gestión (ex-Comercial)
- **Streaming:** catálogo PDF siempre streamed como response (no cachear en S3)

### Migración Alembic
- **Una sola columna nueva:** `Productos.imagen_s3_key` (Text, nullable)
- `Tenants.url_logo`, `color_primario`, `color_secundario` YA EXISTEN — NO migrar

### S3 Strategy
- **Facturas PDF:** S3 cache (ya implementado), pre-signed URLs 1h expiración
- **Catálogo PDF:** siempre streaming, no guardar en S3
- **Graceful degradation:** si S3 falla → streaming sin guardar (facturas)
- **Plan 03-01** debe incluir checkpoint de verificación humana del bucket S3 (similar a 02-05 con OPENROUTER_API_KEY)

### Verificación humana requerida (Plan 03-01)
- Confirmar que el bucket S3 está configurado correctamente en producción
- Variable `AWS_S3_BUCKET` en Railway production environment
- Sin esto, el logo upload y las pre-signed URLs no funcionarán

</decisions>

<specifics>
## Specific Ideas

### Estructura de archivos a crear/modificar
**Backend:**
- `backend/app/servicios/servicio_pdf.py` — extender con branded PDF (logo + colores)
- `backend/app/rutas/facturas.py` — agregar `GET /facturas/{id}/pdf-url`
- `backend/app/rutas/productos.py` — agregar `GET /productos/catalogo-pdf`
- `backend/app/rutas/tenants.py` (o similar) — upload logo endpoint
- Migración Alembic: `add_imagen_s3_key_to_productos`

**Frontend:**
- `frontend/src/pages/CatalogoPage.tsx` — nueva página
- `frontend/src/components/config/MarcaTab.tsx` — nueva pestaña en ConfigPage
- `frontend/src/hooks/useNavigation.ts` — agregar "Catálogo" al sidebar

### Campos Tenants existentes (confirmar en modelos_tenant.py)
```python
url_logo: str | None  # S3 key o URL
color_primario: str | None  # hex, default #1976D2
color_secundario: str | None  # hex
brand_config: dict | None  # JSONB — revisar si existe o agregar
```

### ReportLab branding approach
```python
def _apply_tenant_branding(canvas, tenant):
    primary = tenant.color_primario or "#1976D2"
    text_color = _wcag_contrast_color(primary)
    # Header rectangle with primary color
    # Logo image if url_logo exists (download from S3 or use cached)
    # Footer with secondary color
```

</specifics>

<deferred>
## Deferred Ideas

- Editor visual de templates PDF (demasiado complejo para esta fase)
- Múltiples templates por tenant (v3+)
- Envío directo por WhatsApp desde catálogo (Phase 5)
- QR code en facturas PDF (future)
- Firma digital en PDFs (future)

</deferred>

---

*Phase: 03-imagen-profesional-plantillas-pdf-y-catalogos*
*Context gathered: 2026-03-06 via discuss-phase (recovered from memory)*
