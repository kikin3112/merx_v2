# Chandelier — Reset & Tenant Onboarding

## What This Is

Sistema de reset de base de datos y wizard de inicialización de tenants para Chandelier ERP/POS. Permite limpiar el sistema para producción y ofrece un flujo de onboarding progresivo donde el superadmin o el dueño de empresa configura completamente un tenant — datos de empresa, catálogo de productos, clientes, inventario, contabilidad de apertura y migración de historial — dejándolo listo para operar desde el día 1.

## Current Milestone: v1.0 Reset & Tenant Onboarding

**Goal:** Preparar Chandelier para producción con reset de datos de desarrollo y wizard de onboarding que permita a cualquier empresa configurarse completamente importando sus datos desde Excel.

**Target features:**
- Reset de base de datos (conservar schema, PUC, planes, superadmin)
- Wizard de onboarding progresivo (3 pasos obligatorios + 4 opcionales)
- Importación Excel con preview y validación
- Templates descargables con ejemplos
- Flujo usable por superadmin y dueño de empresa

## Core Value

Un tenant debe poder pasar de "cuenta creada" a "empresa operando" en menos de 30 minutos, sin necesidad de soporte técnico, importando sus datos reales desde Excel.

## Requirements

### Validated

- ✓ Auth JWT + multi-tenancy con RLS — existing
- ✓ CRUD productos con inventario y promedio ponderado — existing
- ✓ Recetas/BOM — existing
- ✓ Facturación con PDF y S3 — existing
- ✓ Cotizaciones con conversión a factura — existing
- ✓ Contabilidad automática con PUC Colombia — existing
- ✓ CRM clientes/proveedores — existing
- ✓ Cartera (cuentas por cobrar/pagar) — existing
- ✓ POS mobile-first — existing
- ✓ Reportes avanzados — existing
- ✓ Dashboard KPIs — existing
- ✓ Frontend completo responsive (17 páginas) — existing
- ✓ Docker + CI/CD + health checks — existing

### Active

- [ ] Reset de base de datos conservando schema, PUC, planes y superadmin
- [ ] Wizard de onboarding post-registro (obligatorio)
- [ ] Wizard accesible desde Configuración (re-importar después)
- [ ] Paso 1 obligatorio: Datos de empresa (NIT, razón social, dirección, logo, prefijo factura, config IVA)
- [ ] Paso 2 obligatorio: Import productos desde Excel con preview y validación
- [ ] Paso 3 obligatorio: Import clientes desde Excel con preview y validación
- [ ] Paso 4 opcional: Ajuste de inventario inicial (stock y costos)
- [ ] Paso 5 opcional: Asiento de apertura contable detallado por cuenta PUC
- [ ] Paso 6 opcional: Importación de facturas históricas (profundidad flexible)
- [ ] Paso 7 opcional: Carga de saldos de cartera pendientes
- [ ] Templates Excel descargables (.xlsx) con headers + 2-3 filas de ejemplo
- [ ] Preview de importación con errores resaltados antes de confirmar
- [ ] Flujo usable tanto por superadmin como por dueño de empresa

### Out of Scope

- Importación desde otros sistemas (Siigo, Alegra) — complejidad alta, solo Excel/CSV
- Importación de recetas/BOM desde Excel — se crean manualmente post-onboarding
- Migración automática de historial contable completo — solo asiento de apertura
- Modo offline durante importación — requiere conexión

## Context

Chandelier está al ~90% de completitud para MVP. El backend tiene 22 routers, el frontend 17 páginas, todo con RLS y Docker. Lo que falta para ir a producción es:

1. **Limpieza de datos**: El sistema tiene datos de desarrollo. Necesita un reset limpio conservando estructura y datos base (PUC, planes, superadmin).

2. **Onboarding de tenants**: No existe flujo para que una empresa nueva se configure completamente. Hoy habría que crear todo manualmente vía API/UI. El wizard resuelve esto.

3. **Importación Excel**: Las microempresas de candelería típicamente tienen sus datos en hojas de cálculo. El sistema debe consumir esos archivos directamente.

4. **Primera empresa real**: El primer tenant será la empresa del fundador. Los datos son reales — productos, clientes, precios, stock — no demo.

### Estado técnico actual
- Backend: FastAPI + SQLAlchemy async + PostgreSQL 16 con RLS
- Frontend: React 18 + TypeScript + Vite + Tailwind + Zustand + React Query
- Infraestructura: Docker Compose, Nginx, health checks
- Testing: Concurrencia + RBAC (pytest)
- Sin migraciones Alembic generadas (modelos definidos, migraciones pendientes)

## Constraints

- **Stack**: FastAPI backend, React frontend — no cambiar stack existente
- **Excel format**: .xlsx y .csv — las microempresas usan Excel/Google Sheets
- **UX**: Wizard progresivo — 3 pasos obligatorios rápidos, resto opcional
- **Validación**: Preview-first — nunca guardar sin que el usuario confirme
- **Multi-tenancy**: Todo el onboarding opera dentro del contexto RLS del tenant
- **Compatibilidad**: No romper funcionalidad existente del ERP/POS

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Progresivo (3 oblig + 4 opcionales) | Reducir fricción de entrada sin sacrificar completitud | — Pending |
| Preview antes de guardar | Evitar errores silenciosos en importación masiva | — Pending |
| Templates con ejemplo | Las microempresas necesitan ver el formato esperado | — Pending |
| Conservar superadmin en reset | Evitar lockout del administrador del sistema | — Pending |
| Asiento apertura detallado PUC | Empresas existentes necesitan contabilidad precisa desde día 1 | — Pending |
| Excel como formato principal | Es lo que usan las microempresas colombianas | — Pending |

---
*Last updated: 2026-02-15 after milestone v1.0 started*
