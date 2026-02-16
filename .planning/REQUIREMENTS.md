# Requirements: Chandelier — Reset & Tenant Onboarding

**Defined:** 2026-02-15
**Core Value:** Un tenant debe poder pasar de "cuenta creada" a "empresa operando" en menos de 30 minutos, sin necesidad de soporte técnico, importando sus datos reales desde Excel.

## v1 Requirements

Requirements for milestone v1.0. Each maps to roadmap phases.

### DB Reset

- [ ] **RESET-01**: Superadmin puede ejecutar reset selectivo que limpia datos de desarrollo conservando schema, PUC, planes y superadmin
- [ ] **RESET-02**: Sistema valida integridad pre/post reset (conteos, constraints, foreign keys)
- [ ] **RESET-03**: Sistema registra audit log del reset (quién, cuándo, qué se eliminó)
- [ ] **RESET-04**: Endpoint protegido solo para superadmin con confirmación doble

### Importación Excel

- [ ] **IMPORT-01**: Sistema parsea archivos .xlsx y .csv con detección automática de columnas
- [ ] **IMPORT-02**: Usuario ve preview de datos importados con errores resaltados antes de confirmar
- [ ] **IMPORT-03**: Usuario puede descargar templates .xlsx con headers correctos y 2-3 filas de ejemplo
- [ ] **IMPORT-04**: Sistema valida NIT con dígito de verificación, formatos moneda COP y fechas DD/MM/YYYY
- [ ] **IMPORT-05**: Usuario puede mapear columnas del Excel a campos del sistema

### Wizard Onboarding

- [ ] **WIZARD-01**: Usuario completa Paso 1 obligatorio: datos de empresa (NIT, razón social, dirección, logo, prefijo factura, IVA)
- [ ] **WIZARD-02**: Usuario completa Paso 2 obligatorio: importar productos desde Excel con preview
- [ ] **WIZARD-03**: Usuario completa Paso 3 obligatorio: importar clientes desde Excel con preview
- [ ] **WIZARD-04**: Usuario completa Paso 4 opcional: ajustar stock y costos de productos importados
- [ ] **WIZARD-05**: Usuario completa Paso 5 opcional: asiento de apertura contable con saldos por cuenta PUC
- [ ] **WIZARD-06**: Wizard es accesible post-registro (obligatorio) y desde Configuración (re-importar)

### UX

- [ ] **UX-01**: Usuario puede guardar progreso del wizard y reanudar donde quedó
- [ ] **UX-02**: Sistema muestra barras de progreso, spinners y feedback visual durante imports
- [ ] **UX-03**: Sistema muestra tips contextuales para guiar al usuario en cada paso

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Historial y Cartera

- **HIST-01**: Usuario puede importar facturas históricas con profundidad flexible
- **HIST-02**: Usuario puede cargar saldos de cartera pendientes (cuentas por cobrar/pagar)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Importación desde otros sistemas (Siigo, Alegra) | Complejidad alta, solo Excel/CSV |
| Importación de recetas/BOM desde Excel | Se crean manualmente post-onboarding |
| Migración automática de historial contable completo | Solo asiento de apertura |
| Modo offline durante importación | Requiere conexión estable |
| Facturación electrónica DIAN | Fase 2+ del producto |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| RESET-01 | — | Pending |
| RESET-02 | — | Pending |
| RESET-03 | — | Pending |
| RESET-04 | — | Pending |
| IMPORT-01 | — | Pending |
| IMPORT-02 | — | Pending |
| IMPORT-03 | — | Pending |
| IMPORT-04 | — | Pending |
| IMPORT-05 | — | Pending |
| WIZARD-01 | — | Pending |
| WIZARD-02 | — | Pending |
| WIZARD-03 | — | Pending |
| WIZARD-04 | — | Pending |
| WIZARD-05 | — | Pending |
| WIZARD-06 | — | Pending |
| UX-01 | — | Pending |
| UX-02 | — | Pending |
| UX-03 | — | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 0
- Unmapped: 18 (pending roadmap creation)

---
*Requirements defined: 2026-02-15*
*Last updated: 2026-02-15 after initial definition*
