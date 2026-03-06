# Guía de Implementación: Auditoría y Atribución de Transacciones

Esta guía detalla cómo implementar el registro de "quién" y "cuándo" para todas las transacciones del sistema (Ventas, POS, Cotizaciones, Inventario), siguiendo las mejores prácticas de la industria y aprovechando la arquitectura existente de chandelierp.

## 1. Análisis del Estado Actual

Actualmente, los modelos principales (`Ventas`, `Compras`, etc.) heredan de `TenantMixin` y `SoftDeleteMixin`. Esto proporciona:
- `tenant_id`: Separación de datos por empresa.
- `created_at` / `updated_at`: Timestamps básicos (ya existentes).
- `deleted_at`: Soft delete.

**Lo que falta:**
- `created_by`: Identificador del usuario creador.
- `updated_by`: Identificador del último usuario que modificó.
- `deleted_by`: Identificador del usuario que eliminó (ya existe en `SoftDeleteMixin` pero necesita ser poblado).

## 2. Estrategia "State of the Art" (2025/2026)

Para sistemas SaaS modernos, la recomendación es una **Arquitectura de Auditoría Híbrida**:

1.  **Atribución Directa (Operativa):** Añadir columnas `created_by` y `updated_by` directamente en las tablas transaccionales. Esto permite consultas ultra-rápidas (ej: "Ventas de Juan hoy") sin hacer joins complejos con logs.
2.  **Audit Log Inmutable (Seguridad):** Usar la tabla `audit_logs` (ya existente) solo para *cambios de estado* (ej: de Pendiente a Confirmada) y *eventos críticos*, guardando el "antes" y "después" (JSON diff).
3.  **Propagación de Contexto:** Usar `ContextVars` para pasar el usuario actual a la capa de base de datos de forma transparente, evitando pasar `current_user` manualmente en cada función.

---

## 3. Pasos de Implementación Sugeridos

### Paso 1: Actualización de Modelos de Datos

Reemplazar la herencia de `TenantMixin` + `SoftDeleteMixin` por `TenantAuditMixin` en los modelos clave.

**Archivos a modificar:** `backend/app/datos/modelos.py`

**Cambio sugerido:**
```python
# Antes
class Ventas(TenantMixin, SoftDeleteMixin, Base):
    ...

# Después
from .mixins import TenantAuditMixin

class Ventas(TenantAuditMixin, Base):
    ...
```

Esto agregará automáticamente las columnas `created_by` y `updated_by` a:
- `Ventas`
- `Compras`
- `Cotizaciones`
- `MovimientosInventario` (Aquí usar `TenantAuditMixin` aunque no tenga soft delete, o crear un mixin específico `TenantCreationAuditMixin` si no se borran movimientos).
- `OrdenesProduccion`

### Paso 2: Automatización con SQLAlchemy Event Listeners

Para no tener que escribir `venta.created_by = user.id` en cada endpoint, se recomienda usar "Event Listeners" de SQLAlchemy junto con un "Context Manager".

1.  **Context Middleware:** Crear un middleware en FastAPI que capture el usuario del token y lo guarde en una variable de contexto (similar a como ya se hace con `tenant_id` en `backend/app/middleware/tenant_context.py`).
2.  **DB Listener:** Crear un listener `before_flush` en `db.py` que lea ese contexto y llene automáticamente los campos.

**Concepto (No código, solo lógica):**
> "Antes de guardar cualquier registro en la BD, si el modelo tiene columna 'created_by' y está vacío, llenarlo con el ID del usuario del contexto actual."

### Paso 3: Visualización en Frontend

Para que el usuario vea "Juan Pérez" en lugar de "a1b2-c3d4...", se necesitan dos cosas:

1.  **Backend Eager Loading:** En los endpoints de `GET /ventas`, asegurarse de incluir la relación con `created_by` (Usuario).
    *   SQLAlchemy: `query(Ventas).options(joinedload(Ventas.creador))`
2.  **DTOs (Esquemas):** Actualizar los esquemas Pydantic para incluir un campo `creador: UsuarioMiniSchema`.

### Paso 4: Manejo de Fechas y Horas

Para el requerimiento de "registrar la hora":

1.  **Almacenamiento:** Siempre en **UTC** (ya configurado en el servidor).
2.  **Visualización:** El Frontend debe convertir UTC a la hora local del usuario.
    *   *Tip:* Usar librerías como `date-fns` o `Intl.DateTimeFormat` en el frontend usando la zona horaria del navegador.
    *   *Tip Pro:* Guardar la preferencia de zona horaria del usuario en su perfil (`usuarios.timezone`) si trabajan en equipos distribuidos globalmente.

---

## 4. Beneficios de esta Implementación

1.  **Transparencia:** Cada venta, cotización o movimiento de inventario tendrá una "firma" digital del responsable.
2.  **Rendimiento:** Al estar en la misma tabla, los reportes de "Ventas por Vendedor" son inmediatos (índices directos).
3.  **Robustez:** Al usar listeners automáticos, es imposible que un desarrollador "olvide" registrar el usuario en el futuro.
4.  **Cumplimiento:** Cumple con estándares de auditoría financiera (trazabilidad completa).

## 5. Próximos Pasos (Hoja de Ruta)

1.  [ ] Crear migración Alembic para añadir columnas `created_by`/`updated_by` a las tablas.
2.  [ ] Implementar el `UserContextMiddleware`.
3.  [ ] Configurar el `Event Listener` en SQLAlchemy.
4.  [ ] Actualizar los esquemas de lectura (Pydantic) para devolver el nombre del usuario.
