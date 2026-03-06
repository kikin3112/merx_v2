# Auditoría de Estado del Arte (Estándar 2026) - chandelierp
**Fecha:** 13 de Febrero, 2026
**Responsable:** Senior AI Tech Lead
**Marco de Referencia:** Cloud-Native & Financial Compliance 2026

## 1. Resumen Ejecutivo de Nueva Generación
Si bien el proyecto cumple con los estándares de 2024 (FastAPI modular, RLS), para los estándares de **Diciembre 2026**, se encuentra en un estado de **"Fragilidad Silenciosa"**.
Aunque la lógica de negocio es correcta, el sistema carece de la **Observabilidad Profunda**, **Resiliencia Automática** y **Gobernanza de IA** que exige el mercado actual.

| Dimensión 2026 | Estado | Hallazgo Principal |
| :--- | :---: | :--- |
| **Observabilidad (OpenTelemetry)** | 🔴 Nulo | Ceguera total en transacciones distribuidas. Solo hay logs básicos. |
| **Integridad Financiera** | 🟡 Parcial | RLS sólido, pero sin `with_for_update` (Race Conditions 2026-unacceptable). |
| **Resiliencia (Chaos Ready)** | 🔴 Nulo | El sistema asume que la DB siempre responde. No hay Circuit Breakers. |
| **Seguridad de la Cadena (SBOM)** | 🔴 Nulo | No hay Bill of Materials ni escaneo de vulnerabilidades en CI/CD. |
| **User Journey & RBAC** | 🔴 Crítico | Routing Frontend plano (`App.tsx`). **Sin guardas por Rol**. |
| **UX & Estado (Client-Side)** | 🟡 Frágil | Estado local volátil en POS. Inaceptable para estándares de "Offline-First". |

---

## 2. Auditoría Profunda: Lógica & Integridad (Backend)

### ✅ Fortalezas (Base Sólida)
*   **Aislamiento Multi-Tenant (RLS):** Implementación de "Libro de Texto" en `TenantContextMiddleware`. Cumple estándares de seguridad GDPR/CCPA 2026.
*   **Cálculo de Costos:** Algoritmo de Costo Promedio Ponderado matemáticamente correcto en `ServicioInventario`.

### 🚨 Brechas Críticas (Standard 2026)
1.  **Ausencia de Bloqueo Pesimista (Race Conditions):**
    *   *Estándar 2026:* Sistemas financieros deben garantizar atomicidad dura.
    *   *Hallazgo:* `confirmar_venta` lee stock y luego escribe. En alta concurrencia, venderá stock inexistente.
    *   *Solución:* Implementar `db.query(...).with_for_update()` en transacciones críticas de inventario.

2.  **Logs no Estructurados (JSON):**
    *   *Estándar 2026:* Logs deben ser JSON parseables por agentes de IA para detección de anomalías.
    *   *Hallazgo:* Logs de texto plano (`logger.info("Venta creada...")`). Dificulta la ingestión automática por sistemas de observabilidad.

---

## 3. Auditoría de Frontend: User Journeys & RBAC
### 🚨 Colapso de Segregación en Frontend (Nuevo Hallazgo)
*   **Routing Plano:** `App.tsx` solo verifica `RequireAuth` (autenticación genérica).
*   **Impacto:** Cualquier usuario "Vendedor" puede navegar por URL a `/config`, `/tenants` o `/contabilidad`.
    *   *Backend:* Probablemente rechace la petición (403), pero la **Experiencia de Usuario (Journey)** está rota. El usuario ve una pantalla blanca o de error en lugar de no tener acceso.
*   **Recomendación 2026:**
    *   Implementar `<RoleGuard allowed="['ADMIN']">` envolviendo las rutas sensibles.
    *   Implementar **"Journey Tests"** automatizados (Playwright/Cypress) que naveguen como "Vendedor" y verifiquen que **NO** pueden acceder a rutas de "Admin".

### ⚠️ Fragilidad del POS (Punto de Venta)
*   **Estado Volátil:** `useState` local. Pérdida de datos al recargar.
*   **Validación Reactiva:** Falta UX preventiva (bloquear agregar al carrito si no hay stock).

---

## 4. Auditoría de Infraestructura & Seguridad (DevSecOps)

### ❌ Deuda Técnica de Infraestructura
1.  **Ausencia de SBOM (Software Bill of Materials):**
    *   *Estándar 2026:* Requerido por regulaciones (EU CRA).
2.  **No hay Tests de Caos (Chaos Engineering):**
    *   *Estándar 2026:* Validar recuperación automática.

---

## 5. Plan de Modernización Inmediata (Roadmap to 2026 Standards)

### Fase 1: Blindaje Transaccional & Observabilidad (Semana 1)
1.  **Atomicidad:** Refactorizar servicios de Inventario y Ventas con `with_for_update` y bloques `try/finally`. (**Crítico**)
2.  **Logging Estructurado:** Migrar a JSON logs con Contexto (Tenant ID, User ID).

### Fase 2: Control de Acceso (RBAC) & Frontend (Semana 1-2)
1.  **Frontend Role Guards:** Crear componente `RoleGuard` en `App.tsx` para `/config`, `/contabilidad`, etc.
2.  **State Management:** Migrar POS a Zustand.

### Fase 3: Quality Assurance Automatizado (Mes 1)
1.  **E2E RBAC Suite:** Script de Playwright que:
    *   Login como Vendedor -> Intenta entrar a /config -> Verifica Redirección.
    *   Login como Admin -> Entra a /config -> Verifica Éxito.

---

# 🚀 Implementation Commands
*(Commands generated based on the Audit Report findings above)*

## Backend Hardening
```bash
# 1. Install structured logging dependency
uv pip install python-json-logger

# 2. Create Audit Log Migrations (if needed for new RBAC events)
alembic revision -m "add_audit_rbac_events"

# 3. Verify Database Isolation (RLS Check)
# Run a specific test to confirm RLS is active
pytest tests/security/test_rls_isolation.py
```

## Frontend RBAC & State
```bash
# 1. Install Zustand for Global State (POS & Auth)
cd frontend
npm install zustand @types/zustand

# 2. Install Testing Library for Journey Verification
npm install -D @playwright/test

# 3. Scaffolding RoleGuard Component
# (Manual step: Create src/components/auth/RoleGuard.tsx)
echo "Creating RoleGuard placeholder..."
mkdir -p src/components/auth
touch src/components/auth/RoleGuard.tsx
```

## Quality Assurance
```bash
# 1. Initialize Playwright for E2E Testing
npx playwright install

# 2. Run RBAC Journey Tests (once implemented)
npx playwright test tests/e2e/rbac.spec.ts
```
