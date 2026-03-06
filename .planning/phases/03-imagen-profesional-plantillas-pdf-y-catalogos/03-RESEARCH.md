# Phase 3 Research: Imagen Profesional — Plantillas PDF y Catálogos

**Date:** 2026-03-06
**Status:** RESEARCH COMPLETE

---

## Codebase Audit — Estado Actual

### servicio_pdf.py
- Ya usa ReportLab con `SimpleDocTemplate`, `Table`, `TableStyle`, `RLImage`
- `_build_header()` maneja logo VIA: `data:` (base64) O path de filesystem
- **GAP CRÍTICO**: NO soporta S3 keys — si `url_logo` es un S3 key (`tenants/abc/logo.png`), fallará silenciosamente en el `except Exception: pass`
- Todos los colores están **hardcodeados**: `#1a1a2e` para headers, `#555555` para subtítulos — NO usa `color_primario` del tenant
- `tenant_info` dict se pasa desde `_get_tenant_info()` en `facturas.py` — actualmente incluye `url_logo` pero no `color_primario`/`color_secundario`

### servicio_almacenamiento.py
- `subir_pdf(contenido, tenant_id, tipo, nombre_archivo)` → key `{tenant_id}/{tipo}/{uuid}-{nombre}.pdf`
- `obtener_url_presigned(key)` → URL con expiración `S3_PRESIGNED_URL_EXPIRY` (config, actualmente 24h; cambiar a 3600s=1h)
- `eliminar_archivo(key)` → delete from S3
- **GAP**: No hay método `subir_imagen()` — necesario para logos y fotos de productos
- `is_enabled` property lee `settings.S3_ENABLED`

### Tenants model (modelos_tenant.py)
```
url_logo: Column(Text)              # ← ya existe, guardar S3 key aquí
color_primario: Column(String(20))  # default "#1976D2" ← ya existe
color_secundario: Column(String(20)) # default "#424242" ← ya existe
```
**NO se requiere migración para Tenants.**

### Productos model (modelos.py)
- Campos actuales: `codigo_interno`, `nombre`, `descripcion`, `categoria`, `precio_venta`, etc.
- **GAP**: NO tiene `imagen_s3_key` — necesario para fotos en catálogo
- **Migración requerida**: `ALTER TABLE productos ADD COLUMN imagen_s3_key TEXT;`

### facturas.py — Endpoint existente
- `GET /{factura_id}/pdf` — ya hace: S3 presigned redirect si `factura.url_pdf` existe, else genera on-the-fly
- `_get_tenant_info()` — pasa `url_logo` pero NO `color_primario`/`color_secundario`
- PDF generation al emitir factura: sube a S3 y guarda key en `factura.url_pdf`
- **NO necesitamos nuevo endpoint** para descarga de facturas — el existente ya es correcto

### Config settings
```python
S3_ENABLED: bool = False
S3_BUCKET: str = "chandelier-documents"
S3_PRESIGNED_URL_EXPIRY: int  # actualmente ? — cambiar default a 3600
S3_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_ENDPOINT_URL
```

### useNavigation.ts
- Grupo `id:'comercial'` con paths `/comercial, /ventas, /pos, /crm, /terceros` — necesita `/catalogo`
- Item existente: `{ to: '/comercial', label: 'Gestión', ... }` — añadir `{ to: '/catalogo', label: 'Catálogo', ... }`

### ConfigPage.tsx
- No tiene sistema de tabs actualmente — necesita añadir tabs con `cv-badge cursor-pointer` pills
- Nueva pestaña "Marca" para logo + colores

---

## Plan Breakdown Recomendado

### Plan 01: Fundación S3 + Migración (Wave 1)
**Objetivo:** Infraestructura para subir imágenes + migración Alembic
- `ServicioAlmacenamiento.subir_imagen(contenido, tenant_id, sub_path)` → key flexible
- `ServicioAlmacenamiento.subir_logo(contenido, tenant_id, extension)` → `tenants/{id}/logo.{ext}`
- Migración Alembic: `add_imagen_s3_key_to_productos`
- Backend endpoint: `POST /tenants/me/logo` — upload logo, subir S3, guardar key en `url_logo`
- Backend endpoint: `GET /tenants/me/brand` — retorna `{url_logo, color_primario, color_secundario}`
- **CHECKPOINT HUMANO**: verificar `S3_ENABLED=true` + `S3_BUCKET` en Railway producción
- Tests: `test_subir_imagen`, `test_upload_logo_endpoint`

### Plan 02: PDF Branding (Wave 1 paralelo con Plan 01)
**Objetivo:** ServicioPDF usa colores del tenant + logo desde S3
- `_get_tenant_info()` en `facturas.py` añade `color_primario`, `color_secundario`
- `ServicioPDF.__init__` acepta `color_primario`, `color_secundario` del `tenant_info`
- `_build_header()`: si `url_logo` es S3 key → download via `ServicioAlmacenamiento.obtener_imagen_bytes(key)` → RLImage
- Reemplazar hardcoded `#1a1a2e` con `self.primary_color` en `_build_header`, `_build_tabla_detalles`, `_build_totales`
- Helper `_wcag_text_color(hex_color)` — retorna `#FFFFFF` o `#1a1a2e` según luminancia WCAG
- Mismo cambio para cotizaciones (`generar_cotizacion_pdf`)
- Tests: `test_pdf_con_colores_tenant`, `test_wcag_contrast`

### Plan 03: ConfigPage — Pestaña "Marca" (Wave 2)
**Objetivo:** UI para upload de logo, pickers de color, preview
- Tab pills en ConfigPage (Carbon Vivo `cv-badge cursor-pointer`)
- `MarcaTab` component: logo upload dropzone + preview + `color_primario` picker + `color_secundario` picker
- Preview inline del header del PDF (CSS simulado, no PDF real)
- React Query: `useMutation` para `POST /tenants/me/logo`, `PATCH /tenants/{id}` para colores
- Tests: visual manual (renderizado)

### Plan 04: CatálogoPage + Endpoint PDF (Wave 2 paralelo con Plan 03)
**Objetivo:** Página de catálogo + PDF generado en backend
- Backend: `POST /productos/catalogo-pdf` — recibe `{producto_ids: [uuid], ...}` → StreamingResponse PDF
- `ServicioPDF.generar_catalogo_pdf(productos, tenant_info)` → grid 2-col, logo, colores, imagen por producto
- Backend: `POST /productos/{id}/imagen` — upload imagen producto → S3 → guarda `imagen_s3_key`
- Backend: `DELETE /productos/{id}/imagen` — borrar imagen S3 + limpiar campo
- Frontend: `CatálogoPage.tsx` — grid de productos con checkboxes, sticky "Generar PDF ({N})" bar
- `useNavigation.ts` — añadir `/catalogo` al grupo Gestión
- `App.tsx` — añadir ruta `/catalogo` → `CatálogoPage`
- Tests: `test_catalogo_pdf_endpoint`, `test_upload_producto_imagen`

### Plan 05: Validación E2E (Wave 3)
**Objetivo:** Tests de integración + smoke test producción
- pytest: 15+ tests nuevos (upload logo, PDF branded, catálogo PDF, WCAG contrast)
- Smoke test producción: verificar S3 bucket activo, subir logo de prueba, generar PDF branded
- Documentar en SUMMARY.md

---

## Decisiones Técnicas Clave

### Logo desde S3 en ReportLab
```python
# En _build_header(), si url_logo parece S3 key (no empieza con 'data:' ni '/static/'):
storage = ServicioAlmacenamiento()
if storage.is_enabled:
    img_bytes = storage.obtener_imagen_bytes(key)
    if img_bytes:
        logo_img = RLImage(io.BytesIO(img_bytes), width=3*cm, height=3*cm)
```

### Añadir `obtener_imagen_bytes(key)` a ServicioAlmacenamiento
```python
def obtener_imagen_bytes(self, key: str) -> Optional[bytes]:
    if not self.is_enabled or not self._client:
        return None
    response = self._client.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return response["Body"].read()
```

### WCAG contrast helper
```python
def _wcag_text_color(hex_color: str) -> str:
    """Returns #FFFFFF or #1a1a2e based on WCAG luminance."""
    c = hex_color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#FFFFFF" if luminance < 0.5 else "#1a1a2e"
```

### Catálogo PDF — estructura 2 columnas
```python
# Página carta, 2 productos por fila
# Por producto: imagen (3cm×3cm) + nombre + descripción (máx 80 chars) + precio
# Header: logo + nombre empresa + "Catálogo de Productos" + fecha
# Footer: "chandelierp" + número de página
```

### Upload logo endpoint
```python
@router.post("/me/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin")),
):
    # Validar: content_type in {"image/jpeg", "image/png"}, size <= 2MB
    # Subir a S3: tenants/{tenant_id}/logo.{ext}
    # Guardar key en tenant.url_logo
    # Retornar {"url_logo": key}
```

---

## Validation Architecture

### Dimension 1 — Unit Tests
- `test_subir_imagen` — ServicioAlmacenamiento.subir_imagen con mock S3
- `test_wcag_text_color` — verifica blanco/oscuro para colores claros y oscuros
- `test_pdf_branded_usa_color_tenant` — ServicioPDF genera con color tenant, no hardcoded
- `test_catalogo_pdf_dos_productos` — genera catálogo básico

### Dimension 2 — Integration Tests (pytest + DB)
- `test_upload_logo_endpoint` — POST /tenants/me/logo → 200, url_logo actualizado en DB
- `test_upload_logo_formato_invalido` — .gif → 422
- `test_upload_logo_tamaño_excedido` — >2MB → 422
- `test_catalogo_pdf_endpoint` — POST /productos/catalogo-pdf con IDs → StreamingResponse PDF
- `test_upload_producto_imagen` → imagen en DB
- `test_pdf_factura_usa_branding` — factura emitida usa color_primario del tenant

### Dimension 3 — Verificación Humana
- Confirmar S3_ENABLED=true en Railway
- Generar factura con logo y verificar PDF en navegador
- Abrir CatálogoPage, seleccionar 2 productos, descargar PDF

## RESEARCH COMPLETE
