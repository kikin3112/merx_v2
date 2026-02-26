# 🏛️ MERX v2 / Chandelier ERP — Organigrama del Ecosistema

> Modelo organizacional híbrido: **Producto-Ágil con Gobernanza Matricial**.
> Diseñado para escalar de equipo fundador (5–8 personas) a operación completa (40+).

---

## 📐 Diagrama Jerárquico

```
                          ┌─────────────────────────┐
                          │   CEO / Fundador / CTO   │
                          │   (Dirección General)    │
                          └───────────┬─────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
  ┌─────────▼──────────┐   ┌─────────▼──────────┐   ┌─────────▼──────────┐
  │  VP de Producto &   │   │  VP de Ingeniería   │   │  VP de Operaciones  │
  │  Estrategia (CPO)   │   │      (VP Eng)       │   │  & Comercial (COO)  │
  └─────────┬──────────┘   └─────────┬──────────┘   └─────────┬──────────┘
            │                         │                         │
    ┌───────┴───────┐         ┌───────┴───────┐         ┌───────┴───────┐
    │               │         │               │         │               │
 Producto &     UX/UI &    Ingeniería     Infra &     Ventas &      Customer
 Discovery      Diseño     Core ERP      DevOps/     Onboarding    Success &
                                         SecOps                    Soporte
```

---

## 🔷 NIVEL 1 — Dirección Ejecutiva

### CEO / Fundador / CTO
- Visión estratégica del producto y la empresa.
- Decisiones de inversión, partnerships y roadmap de alto nivel.
- Gobernanza final sobre arquitectura y seguridad.
- Responsable ante inversores/stakeholders.

---

## 🔷 NIVEL 2 — Liderazgo Estratégico (C-Suite / VPs)

---

### VP de Producto & Estrategia (CPO)
- Dueño del roadmap de producto y priorización estratégica.
- Define la visión de cada módulo del ERP y su integración.
- Gestiona el backlog unificado y los OKRs de producto.

### VP de Ingeniería (VP Eng)
- Responsable de la calidad técnica, arquitectura y deuda técnica.
- Lidera los equipos de desarrollo backend, frontend e infraestructura.
- Define estándares de código, revisión y procesos de entrega.

### VP de Operaciones & Comercial (COO)
- Gestiona ventas, onboarding de tenants y customer success.
- Define procesos de soporte, SLAs y retención.
- Alinea la operación comercial con las capacidades del producto.

---

## 🔷 NIVEL 3 — Dirección Funcional (Heads / Leads)

---

### 🟦 Pilar: Producto & Diseño

#### Head of Product
- Traduce la estrategia en épicas y user stories.
- Coordina con ingeniería la planificación de sprints.
- Valida que cada release cumpla los criterios de aceptación.

#### Head of UX/UI & Design
- Define el sistema de diseño y los patrones de interacción.
- Responsable de la experiencia de micro-interacciones (React Spring / Framer Motion).
- Asegura consistencia visual y accesibilidad en todos los módulos.

---

### 🟩 Pilar: Ingeniería Core

#### Head of Backend Engineering
- Lidera la arquitectura FastAPI, modelos de datos (SQLAlchemy/Alembic) y servicios.
- Responsable de la lógica multi-tenant, aislamiento de datos y rendimiento de API.
- Tutela los módulos: auth, tenants, servicios contables, inventarios, CRM, ventas, producción.

#### Head of Frontend Engineering
- Lidera la arquitectura React + TypeScript + Vite + Zustand.
- Responsable de virtualización (react-window), SSE, y módulos unificados.
- Asegura rendimiento (100k+ filas), navegación contextual y UX fluida.

#### Head of QA & Testing
- Define la estrategia de testing: unitarios, integración, E2E y seguridad.
- Automatización de pruebas y cobertura de cada módulo del ERP.
- Validación de regresiones en cada ciclo de release.

---

### 🟧 Pilar: Infraestructura, DevOps & Seguridad

#### Head of DevOps & Platform
- Gestiona pipelines CI/CD (GitHub Actions: ci, deploy-frontend, deploy-landing).
- Docker, Railway, Vercel, Nginx: orquestación y despliegue.
- Monitoreo, logging, alertas y escalabilidad de infraestructura.

#### Head of Security (SecOps)
- Lidera los 6 pipelines de seguridad (SAST, DAST, SCA, container, secrets, AI review).
- Gestiona Gitleaks, Semgrep, Bandit, Trivy, OWASP ZAP.
- Define políticas de seguridad, respuesta a incidentes y compliance.

---

### 🟪 Pilar: Operaciones & Comercial

#### Head of Sales & Growth
- Estrategia de adquisición de clientes y upselling.
- Gestión del pipeline comercial y forecasting.
- Coordinación con producto para feedback de mercado.

#### Head of Customer Success & Soporte
- Onboarding de nuevos tenants y capacitación.
- Gestión del módulo PQRS (peticiones, quejas, reclamos, sugerencias).
- Métricas de satisfacción, churn y retención.

---

## 🔷 NIVEL 4 — Equipos de Dominio (Squads Orientados a Producto)

> Cada squad es **cross-funcional**: 1 PM/PO + 2–3 devs + 1 QA + acceso a UX.

---

### 🟦 Squad: Ventas & Facturación
**Alcance**: `facturas`, `ventas`, `cotizaciones`, `POS`, `cartera`, `medios_pago`
| Rol | Descripción |
|-----|-------------|
| Product Owner | Prioriza features de flujo de venta, facturación electrónica, POS y cartera. |
| Backend Dev (Senior) | Lógica de facturación, integración tributaria, módulo de cartera y cobros. |
| Backend Dev | Endpoints de cotizaciones, ventas y flujos de conversión cotización→factura. |
| Frontend Dev (Senior) | Páginas FacturasPage, VentasPage, POSPage, CotizacionesPage, CarteraPage. |
| QA Engineer | Testing de flujos de venta completos y validación de cálculos financieros. |

---

### 🟦 Squad: Inventario & Producción
**Alcance**: `inventarios`, `productos`, `recetas`, `ordenes_produccion`
| Rol | Descripción |
|-----|-------------|
| Product Owner | Prioriza gestión de stock, recetas, trazabilidad y órdenes de producción. |
| Backend Dev (Senior) | Servicio de inventario, lógica de stock, alertas y movimientos automatizados. |
| Backend Dev | Módulos de recetas, productos compuestos y órdenes de producción. |
| Frontend Dev | Páginas InventarioPage, RecetasPage, ProductosPage. Virtualización masiva. |
| QA Engineer | Testing de trazabilidad, cálculos de bom/recetas y consistencia de stock. |

---

### 🟦 Squad: Contabilidad & Finanzas
**Alcance**: `contabilidad`, `configuracion_contable`, `cuentas_contables`, `periodos_contables`, `reportes`
| Rol | Descripción |
|-----|-------------|
| Product Owner | Prioriza contabilidad, reportes financieros, períodos y configuración contable. |
| Backend Dev (Senior) | Servicio contable, cierre de períodos, integración con facturación y compras. |
| Frontend Dev | ContabilidadPage, ReportesPage, módulo de configuración contable. |
| QA Engineer | Validación de asientos contables, balances y reportes regulatorios. |

---

### 🟦 Squad: CRM & Terceros
**Alcance**: `crm`, `terceros`, `pqrs`
| Rol | Descripción |
|-----|-------------|
| Product Owner | Prioriza pipeline de clientes, gestión de terceros y módulo PQRS. |
| Backend Dev | Servicio CRM, módulo de terceros (clientes/proveedores) y PQRS. |
| Frontend Dev | CRMPage, TercerosPage, SoportePage con componentes CRM y soporte. |
| QA Engineer | Testing de flujos CRM, búsqueda de terceros y gestión de PQRS. |

---

### 🟦 Squad: Plataforma & Tenants
**Alcance**: `tenants`, `auth`, `usuarios`, `compras`, `sse`, `health`
| Rol | Descripción |
|-----|-------------|
| Product Owner | Prioriza multi-tenancy, registro, onboarding, permisos y funcionalidades transversales. |
| Backend Dev (Senior) | Servicio de tenants (56k+ líneas), aislamiento multi-tenant, auth JWT y roles/permisos. |
| Backend Dev | Endpoints de compras, SSE (real-time), health checks y gestión de usuarios. |
| Frontend Dev | TenantsPage, LoginPage, RegistroPage, SelectTenantPage, DashboardPage, onboarding. |
| QA Engineer | Testing de aislamiento tenant, penetration tests de auth y validación de permisos. |

---

## 🔷 NIVEL 5 — Funciones Transversales (Guilds / Chapters)

> Equipos horizontales que sirven a **todos los squads** y mantienen estándares.

---

### 🟠 Guild: Arquitectura & Estándares

| Rol | Descripción |
|-----|-------------|
| Arquitecto de Software (Lead) | Define patrones arquitectónicos, revisiones y guidelines cross-squad. Gobierna la deuda técnica. |
| Tech Lead Backend | Estándares FastAPI, patrones de servicios, esquemas de datos y migraciones Alembic. |
| Tech Lead Frontend | Estándares React/TypeScript, sistema de componentes, stores Zustand y hooks. |

---

### 🟠 Guild: DevOps & Infraestructura

| Rol | Descripción |
|-----|-------------|
| SRE / DevOps Engineer (Senior) | Mantiene Docker, Docker Compose, Dockerfiles, Railway, Vercel. Optimiza pipelines. |
| DevOps Engineer | Automatización de CI/CD (9 GitHub Actions workflows). Monitoreo y alertas. |
| DBA / Data Engineer | Gestión de PostgreSQL, optimización de queries, backups, réplicas y migraciones. |

---

### 🟠 Guild: Seguridad (SecOps)

| Rol | Descripción |
|-----|-------------|
| Security Engineer (Lead) | Política de seguridad, auditorías, pentesting y respuesta a incidentes. |
| AppSec Engineer | Mantiene reglas Semgrep, Gitleaks, Bandit. Revisa PRs desde perspectiva de seguridad. |
| Compliance Analyst | Asegura cumplimiento normativo (protección de datos, facturación electrónica, estándares DIAN). |

---

### 🟠 Guild: UX/UI & Design System

| Rol | Descripción |
|-----|-------------|
| UX Designer (Lead) | Research de usuarios, diseño de flujos y validación de usabilidad. |
| UI Designer | Componentes visuales, sistema de diseño, iconografía y motion design. |
| UX Writer / Content | Microcopy, guías de usuario (guia_usuario), tooltips y mensajes del sistema. |

---

### 🟠 Guild: Data & Analytics

| Rol | Descripción |
|-----|-------------|
| Data Analyst | Definición de métricas de negocio, dashboards de reporting y KPIs del ERP. |
| BI Engineer | ETL, pipelines de datos para reportes contables/ventas/inventario. |

---

## 🔷 NIVEL 6 — Gobernanza & Comités

---

### 🔴 Comité de Arquitectura
- **Frecuencia**: Quincenal.
- **Miembros**: VP Eng, Arquitecto, Tech Leads, Head SecOps.
- **Objetivo**: Decisiones técnicas de alto impacto, aprobación de ADRs, revisión de deuda técnica.

### 🔴 Comité de Producto
- **Frecuencia**: Semanal.
- **Miembros**: CPO, Head of Product, Product Owners de cada squad.
- **Objetivo**: Priorización del roadmap, alineación cross-squad, revisión de métricas de producto.

### 🔴 Comité de Seguridad
- **Frecuencia**: Mensual.
- **Miembros**: Head SecOps, Security Engineer, VP Eng, Compliance.
- **Objetivo**: Revisión de hallazgos, actualización de políticas, planning de pentesting.

### 🔴 Comité de Release
- **Frecuencia**: Cada sprint (bi-semanal).
- **Miembros**: VP Eng, Head QA, DevOps Lead, Product Owners.
- **Objetivo**: Go/No-Go de releases, validación de calidad y seguridad pre-despliegue.

---

## 🔷 NIVEL 7 — Roles de Soporte & Operaciones

---

| Rol | Descripción |
|-----|-------------|
| Soporte Técnico N1 | Primer punto de contacto con usuarios finales. Resolución de incidencias básicas vía módulo PQRS. |
| Soporte Técnico N2 | Escalación de incidencias complejas. Diagnóstico en backend/logs. Coordinación con squads. |
| Customer Onboarding Specialist | Configuración inicial de nuevos tenants, migración de datos y capacitación. |
| Technical Writer | Documentación técnica, API docs, guías de integración y changelog. |
| Scrum Master / Agile Coach | Facilitación de ceremonias ágiles, remoción de bloqueos, mejora continua de procesos. |

---

## 🔷 ESCALABILIDAD FUTURA

> Roles y estructuras a activar según el crecimiento del producto y la base de clientes.

---

| Fase | Trigger | Roles / Estructuras a Incorporar |
|------|---------|----------------------------------|
| **Fase 1** (10–20 tenants) | Validación de mercado | Product Marketing Manager, segundo QA, DevOps dedicado |
| **Fase 2** (20–50 tenants) | Crecimiento orgánico | Squad de Integraciones (APIs externas, factura electrónica DIAN), Head of Support |
| **Fase 3** (50–200 tenants) | Escala regional | Squad de Internacionalización (i18n, multi-moneda), Data Engineer dedicado, SRE 24/7 |
| **Fase 4** (200+ tenants) | Enterprise | Squad de AI/ML (predicción de demanda, analytics avanzados), VP de Revenue, Legal/Compliance Officer |
| **Fase 5** (Plataforma) | Marketplace | Ecosystem Manager, Developer Relations, API Partnerships, SDK team |

---

## 🔷 MAPEO MÓDULOS ERP → SQUADS

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MÓDULOS DEL ERP                              │
├──────────────────────┬──────────────────────────────────────────────┤
│ Squad                │ Módulos Backend / Frontend                   │
├──────────────────────┼──────────────────────────────────────────────┤
│ Ventas & Facturación │ facturas, ventas, cotizaciones, POS,        │
│                      │ cartera, medios_pago                         │
├──────────────────────┼──────────────────────────────────────────────┤
│ Inventario &         │ inventarios, productos, recetas,            │
│ Producción           │ ordenes_produccion                           │
├──────────────────────┼──────────────────────────────────────────────┤
│ Contabilidad &       │ contabilidad, configuracion_contable,       │
│ Finanzas             │ cuentas_contables, periodos_contables,      │
│                      │ reportes                                     │
├──────────────────────┼──────────────────────────────────────────────┤
│ CRM & Terceros       │ crm, terceros, pqrs                        │
├──────────────────────┼──────────────────────────────────────────────┤
│ Plataforma &         │ tenants, auth, usuarios, compras, sse,     │
│ Tenants              │ health                                      │
├──────────────────────┼──────────────────────────────────────────────┤
│ Transversal:         │ Docker, CI/CD, Railway, Vercel, PostgreSQL, │
│ DevOps + SecOps      │ Gitleaks, Semgrep, Trivy, ZAP               │
└──────────────────────┴──────────────────────────────────────────────┘
```

---

## 🔷 RESUMEN DE HEADCOUNT POR FASE

| Fase | Headcount Estimado | Squads Activos |
|------|--------------------|----------------|
| Founding (actual) | 5–8 | 2–3 squads combinados |
| Fase 1 | 12–18 | 4 squads + guilds parciales |
| Fase 2 | 20–30 | 5 squads + guilds completas |
| Fase 3 | 30–45 | 6 squads + integraciones + soporte tier |
| Fase 4+ | 45–70+ | 7+ squads + AI/ML + enterprise |

---

> **Modelo de referencia**: Spotify Model (Squads + Guilds + Chapters) adaptado con gobernanza matricial y orientación a producto ERP multi-tenant SaaS.
