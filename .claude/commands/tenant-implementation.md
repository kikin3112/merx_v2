# Plan de Implementación: Centro de Control SaaS (Estándar Diciembre 2025)

Este documento detalla la arquitectura, características y estrategias de implementación para un Centro de Control SaaS de "Control Total", diseñado para ser robusto, seguro y escalable.

> [!IMPORTANT]
> **Filosofía de Implementación**: "Control Total con UX Acogedora".
> 1.  **UX Humana**: Los límites de plan no son errores, son oportunidades de crecimiento.
> 2.  **Sincronización Total**: Un cambio en el panel admin debe reflejarse en el usuario final en tiempo real.
> 3.  **Configurabilidad Absoluta**: Todo (menús, botones, límites) debe ser un parámetro.

## 1. Arquitectura y Sincronización (Deep Integration)

Para garantizar que los cambios se reflejen en "TODO el sistema" sin romper nada, usaremos una estrategia de **Sincronización Pasiva**.

### 1.1. Propagación de Configuración (Strategy: "Version Header")
*   **Backend**: Agregar un campo `config_version` (timestamp) en `Tenants` y `Usuarios`.
*   **Middleware**: Inyectar header `X-Config-Version: <timestamp>` en *cada* respuesta HTTP.
*   **Frontend (Interceptor)**:
    *   El cliente Axios lee este header en cada respuesta.
    *   Si `server_version > local_version`, dispara un **"Hot Reload"** de la configuración del usuario en segundo plano (`authStore.fetchUser()`).
*   **Resultado**: Si cambias un permiso en el Admin, la siguiente acción del usuario (navegar, click) detectará el cambio y actualizará la UI automáticamente sin recargar la página.

### 1.2. Gestión de Sesiones y "Kill Switch"
*   **Funcionalidad**: Capacidad de revocar sesiones activas instantáneamente.
    *   **Nivel Usuario**: Desconectar a un usuario específico.
    *   **Nivel Tenant**: Desconectar a *todos* los usuarios.
*   **Implementación**: `session_token` en Redis. Middleware verifica validez.

### 1.3. Seguridad y Aislamiento
*   **Tests de Aislamiento**: Suite automatizado que intenta cruzar datos entre tenants ("Canary Tests").
*   **IP Allow-listing**: Configurable por tenant (Feature Enterprise).

---

## 2. Experiencia de Usuario (UX) "Acogedora" y Robusta

El manejo de errores debe ser informativo y amigable, jamás un simple código HTML.

### 2.1. Interceptor de Límites (Plan Limit UX)
En lugar de mostrar un error 403 genérico:
1.  **Backend**: Retorna `402 Payment Required` o `403 Forbidden` con código de error específico: `LIMIT_REACHED_USERS`, `FEATURE_NOT_IN_PLAN`.
2.  **Frontend**:
    *   **Global Error Boundary**: Captura estos códigos.
    *   **Modal "Upsell" Amigable**:
        *   *Titulo*: "¡Tu equipo está creciendo!" (en vez de "Error: Límite excedido").
        *   *Mensaje*: "Has alcanzado el límite de 5 usuarios. Actualiza al plan Pro para ilimitados."
        *   *Acción*: Botón "Ver Planes" que lleva directamente al billing (o abre chat de soporte).
    *   **Visual**: Iconografías amigables, no alertas rojas agresivas.

### 2.2. Modo Mantenimiento "Vivo"
Cuando un tenant está en mantenimiento (Error 503):
*   Mostrar una pantalla de "Estamos mejorando tu experiencia".
*   **Polling Automático**: La pantalla consulta `/api/health` cada 30s. Cuando el sistema vuelve, la página se recarga sola. El usuario no tiene que dar F5.

---

## 3. Motor de "Control Total" (Entitlements & Features)

Para que "tenga la capacidad de cambiar TODO", migraremos de Roles fijos a un sistema de **Features Granulares**.

### 3.1. Arquitectura de Features
*   **Base de Datos**: Columna `features_config` (JSONB) en la tabla `Tenants`.
    *   Estructura: `{ "crm": true, "pos": { "offline_mode": false }, "max_users": 10 }`
*   **Resolución en Cascada**:
    1.  **Plan Base**: El plan define los defaults.
    2.  **Add-ons**: Paquetes extra comprados.
    3.  **Overrides Manuales**: El SuperAdmin puede activar/desactivar CUALQUIER feature específico para un tenant específico (ej. "Regalar módulo CRM por 1 mes").

### 3.2. Frontend: `useFeature` Hook
En lugar de `if (role === 'admin')`, usaremos:
```typescript
const { can } = useFeature();
if (can('module.crm') && can('action.export_pdf')) { ... }
```
Esto permite ocultar/mostrar menús, botones y secciones enteras dinámicamente.

---

## 4. Gestión Avanzada de Planes y Facturación

### 4.1. Motor de Billing Flexible
*   **Entitlements**: Definición abstracta de límites (`api_calls_monthly`, `storage_gb`).
*   **Metering**: Contadores en Redis para uso en tiempo real.
*   **Alertas de Consumo**: NotifyUser al 80%, 90% y 100%.

### 4.2. Ciclo de Vida (Dunning)
*   **Retry Logic Inteligente**: Reintentos automáticos en días 1, 3, 7.
*   **Degradación Graciosa**: Pasar a modo "Read-Only" antes de bloquear totalmente.

---

## 5. Gobernanza y Observabilidad

### 5.1. Feature Flags por Tenant
*   Desacoplar Deploy de Release. Activar características nuevas solo para "Beta Testers" o tenants específicos.

### 5.2. Impersonation (Ghost Mode) Auditado
*   Registro inmutable de acciones realizadas por el staff mientras impersonan a un cliente.
*   Header visual en la UI: "Estás viendo el sistema como [Usuario] de [Tenant]".

### 5.3. Tenant Health Score
*   Algoritmo 0-100 basado en uso, pagos y tickets.
*   Dashboard para identificar churn risk.

---

## 6. UI del Centro de Control (SuperAdmin)

### 6.1. Vista "Cockpit" del Tenant
*   Pestaña **"Features & Limits"**: Una matriz donde el SuperAdmin puede ver y editar (Override) cada permiso individual del tenant en tiempo real.
*   Botón **"Sync Now"**: Fuerza la actualización de caché del tenant.

### 6.2. Dashboard de Operaciones
*   Lista de tenants filtrable por: Versión de Config, Estado, Plan, Health Score.

## Próximos Pasos (Implementación Cautelosa)

1.  **Backend Core**:
    *   Implementar `TenantConfig` y lógica de resolución (Plan + Overrides).
    *   Implementar Header `X-Config-Version`.
2.  **Frontend Core**:
    *   Crear `useFeature` hook.
    *   Implementar "Passive Sync" en interceptor Axios.
    *   Crear componentes de UI para "Plan Limit" y "Maintenance".
3.  **Migración**:
    *   Mapear roles actuales a nuevas Features.
    *   Refactorizar `Sidebar` para usar `useFeature`.
