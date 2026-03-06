---
phase: 03-imagen-profesional-plantillas-pdf-y-catalogos
plan: 02
subsystem: backend/pdf-branding
tags: [pdf, branding, tenant, colors, wcag, s3, reportlab]
dependency_graph:
  requires: [03-01]
  provides: [branded-pdf-generation]
  affects: [facturas, cotizaciones]
tech_stack:
  added: []
  patterns: [wcag-luminance-formula, s3-key-detection, tenant-color-injection]
key_files:
  created: []
  modified:
    - backend/app/servicios/servicio_pdf.py
    - backend/app/rutas/facturas.py
    - backend/app/rutas/cotizaciones.py
    - backend/tests/test_servicio_pdf.py
decisions:
  - "WCAG luminance threshold 0.5 chosen (simplified formula 0.299R+0.587G+0.114B / 255) — handles coral (#FF9B65→dark) and navy (#1a1a2e→white) correctly"
  - "S3 key detection: NOT startswith('data:') AND NOT startswith('/') — simple and unambiguous"
  - "_crear_estilos() paragraph text colors (#1a1a2e) left unchanged — plan only targets structural table/border colors"
  - "cotizaciones.py uses getattr() defensively for color fields — consistent with existing pattern in that file"
metrics:
  duration: ~180s
  completed_date: "2026-03-06"
  tasks_completed: 2
  files_modified: 4
---

# Phase 03 Plan 02: Tenant Branding in PDF Generation Summary

**One-liner:** ReportLab PDFs now use tenant `color_primario` for table headers, borders, and totals line, with WCAG-compliant text contrast and S3 logo support.

---

## Tasks Completed

| Task | Name | Commit | Key Changes |
|------|------|--------|-------------|
| 1 | WCAG helper + _get_tenant_info() enrichment | ba94725 | `_wcag_text_color()`, `ServicioPDF.__init__` color fields, `facturas.py` color_primario |
| 2 | Branded colors + S3 logo + cotizaciones enrichment | be34e95 | LINEBELOW/LINEABOVE use primary_color, cotizaciones.py colors, valid PNG test fix |

---

## What Was Built

**`_wcag_text_color(hex_color)`** — module-level helper in `servicio_pdf.py`. Takes a hex color string, computes simplified WCAG luminance, returns `#FFFFFF` for dark backgrounds or `#1a1a2e` for light backgrounds. Used to determine readable text color on top of tenant's primary brand color.

**`ServicioPDF.__init__` enrichment** — constructor now reads `color_primario` and `color_secundario` from `tenant_info` dict, storing them as `self.primary_color`, `self.secondary_color`, and `self.text_on_primary`. Defaults: `#1976D2` and `#424242`.

**Brand color propagation** — four structural elements now use `self.primary_color`:
- `_build_header()`: HR line under company info
- `_build_tabla_detalles()`: table header BACKGROUND, TEXTCOLOR (via `self.text_on_primary`), LINEBELOW
- `_build_totales()`: LINEABOVE on total row

**S3 logo detection** in `_build_header()`: logo URLs that don't start with `data:` or `/` are treated as S3 keys. Calls `ServicioAlmacenamiento.obtener_imagen_bytes(key)` via lazy import to avoid circular imports.

**`_get_tenant_info()` in `facturas.py`**: added `color_primario` and `color_secundario` to returned dict.

**`_generar_pdf_cotizacion()` in `cotizaciones.py`**: added `color_primario` and `color_secundario` to `tenant_info` dict using `getattr()` defensively.

---

## Verification Results

```
python -m pytest tests/test_servicio_pdf.py -x -q
→ 7 passed, 1 warning in 0.06s

grep _build_header/_build_tabla_detalles/_build_totales for #1a1a2e
→ 0 occurrences in all three methods

python -c "from app.servicios.servicio_pdf import _wcag_text_color; print(_wcag_text_color('#1a1a2e'), _wcag_text_color('#FFFFFF'))"
→ #FFFFFF #1a1a2e

grep color_primario backend/app/rutas/cotizaciones.py
→ line 37: "color_primario": getattr(tenant, "color_primario", None) or "#1976D2"
```

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Broken PNG bytes in test_pdf_logo_s3_key_detectado**
- **Found during:** Task 2 test run
- **Issue:** The test used a manually crafted "minimal PNG" with broken data stream — ReportLab/PIL raised `OSError: broken data stream when reading image file` during `doc.build()`, preventing the `assert_called_once_with()` from executing
- **Fix:** Replaced with valid 10x10 pixel PNG bytes generated from `PIL Image.new('RGB', (10, 10), (255, 0, 0))`
- **Files modified:** `backend/tests/test_servicio_pdf.py`
- **Commit:** be34e95

---

## Self-Check: PASSED

- backend/app/servicios/servicio_pdf.py: FOUND
- backend/app/rutas/cotizaciones.py: FOUND
- backend/tests/test_servicio_pdf.py: FOUND
- Commit ba94725 (Task 1): FOUND
- Commit be34e95 (Task 2): FOUND
