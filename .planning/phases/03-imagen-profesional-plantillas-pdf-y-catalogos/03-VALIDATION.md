---
phase: 3
slug: imagen-profesional-plantillas-pdf-y-catalogos
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (existing) |
| **Config file** | `backend/pytest.ini` (existing) |
| **Quick run command** | `cd backend && pytest tests/test_servicio_pdf.py tests/test_almacenamiento.py -x -q` |
| **Full suite command** | `cd backend && pytest -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && pytest tests/test_servicio_pdf.py tests/test_almacenamiento.py -x -q`
- **After every plan wave:** Run `cd backend && pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | R4.1 | unit | `pytest tests/test_almacenamiento.py::test_subir_imagen -x -q` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | R4.1 | migration | `alembic upgrade head && alembic downgrade -1` | ✅ | ⬜ pending |
| 3-01-03 | 01 | 1 | R4.1 | integration | `pytest tests/test_upload_logo.py -x -q` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | R4.1 | unit | `pytest tests/test_servicio_pdf.py::test_wcag_text_color -x -q` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 1 | R4.1 | unit | `pytest tests/test_servicio_pdf.py::test_pdf_branded_usa_color_tenant -x -q` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 2 | R4.1 | manual | Visual review ConfigPage Marca tab | N/A | ⬜ pending |
| 3-04-01 | 04 | 2 | R4.2 | integration | `pytest tests/test_catalogo_pdf.py::test_catalogo_pdf_endpoint -x -q` | ❌ W0 | ⬜ pending |
| 3-04-02 | 04 | 2 | R4.2 | integration | `pytest tests/test_upload_producto_imagen.py -x -q` | ❌ W0 | ⬜ pending |
| 3-05-01 | 05 | 3 | R4.1+R4.2 | full suite | `pytest -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_almacenamiento.py` — stubs: `test_subir_imagen`, `test_obtener_imagen_bytes`
- [ ] `backend/tests/test_upload_logo.py` — stubs: `test_upload_logo_endpoint`, `test_upload_logo_formato_invalido`, `test_upload_logo_tamaño_excedido`
- [ ] `backend/tests/test_servicio_pdf.py` — añadir stubs: `test_wcag_text_color`, `test_pdf_branded_usa_color_tenant`, `test_pdf_cotizacion_usa_color_tenant`
- [ ] `backend/tests/test_catalogo_pdf.py` — stubs: `test_catalogo_pdf_endpoint`, `test_catalogo_pdf_con_imagenes`, `test_catalogo_pdf_sin_productos`
- [ ] `backend/tests/test_upload_producto_imagen.py` — stubs: `test_upload_imagen_producto`, `test_delete_imagen_producto`

*Existing infrastructure (conftest.py, fixtures) covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Logo visible en PDF generado | R4.1 | Inspección visual del PDF | Emitir factura, abrir PDF, verificar logo en header |
| Colores del tenant en PDF | R4.1 | Inspección visual | Configurar color_primario=#FF0000, emitir factura, verificar header rojo |
| ConfigPage Marca tab funciona | R4.1 | UI interactiva | Subir logo, seleccionar colores, verificar preview |
| CatálogoPage — grid y PDF | R4.2 | UI interactiva | Seleccionar 3 productos, clic "Generar PDF", verificar descarga |
| S3 bucket activo en Railway | R4.1 | Variables de entorno | Verificar S3_ENABLED=true en Railway dashboard |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
