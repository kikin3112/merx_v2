# Plan Estratégico de Refinamiento, Mejoramiento y Optimización del Módulo Contable

---

## 1. Resumen Ejecutivo

El módulo contable actual de **chandelierp** opera como un sistema funcional básico con capacidades de asientos manuales, contabilización automática de ventas/anulaciones y balance de prueba. Sin embargo, presenta brechas significativas frente al estado del arte 2025 en:

- **Modelado contable**: Sin terceros en asientos, sin centros de costo, sin períodos contables, sin cierre fiscal
- **Integridad transaccional**: Códigos de cuentas PUC hardcodeados, sin uso de `ConfiguracionContable`, sin validaciones de período
- **Reportes financieros**: Solo balance de prueba; faltan libro diario, libro mayor, estado de resultados, balance general
- **Auditoría**: Sin log de cambios granular, sin bloqueo de períodos cerrados, sin trazabilidad completa
- **Automatización**: Solo ventas y anulaciones; faltan compras, producción, nómina, cartera
- **Integración normativa**: Sin soporte explícito para NIIF/NIC, sin retenciones, sin facturación electrónica DIAN
- **Frontend**: Vista única sin formularios de creación, sin gestión de plan de cuentas, sin reportes interactivos

**Impacto esperado**: Transformar el módulo de un registro contable básico a un sistema contable robusto, auditable, normativo y escalable para PyMEs colombianas.

---

## 2. Estado del Arte 2025 — Síntesis Estructurada

### 2.1 Arquitectura y Diseño Modular

| Tendencia | Descripción |
|---|---|
| **Servicio contable desacoplado** | Engine contable como servicio independiente con API interna clara; cada módulo (ventas, compras, inventario) publica eventos contables |
| **Event-Driven Accounting** | Asientos generados por eventos de negocio (venta confirmada, compra recibida, producción completada), no por llamadas directas |
| **Configuración sobre código** | Mapeos cuenta-concepto parametrizables por tenant, eliminando códigos hardcodeados |
| **Períodos contables formales** | Apertura, cierre parcial y cierre definitivo de períodos fiscales con bloqueo de movimientos |

### 2.2 Integridad Transaccional y Consistencia

| Práctica | Implementación |
|---|---|
| **Partida doble verificada** | Validación a nivel de DB con CHECK constraint `SUM(debito) = SUM(credito)` por asiento + trigger |
| **Inmutabilidad de asientos cerrados** | Asientos en períodos cerrados no se modifican; se generan asientos de ajuste/reversión |
| **Idempotencia** | Cada transacción contable tiene un `idempotency_key` (ej: `VENTA-{id}-{version}`) para prevenir duplicados |
| **Decimal preciso** | `Numeric(15,2)` como mínimo; `Numeric(18,4)` recomendado para cálculos intermedios |
| **Reconciliación automática** | Verificación periódica de que saldos contables coinciden con saldos operativos |

### 2.3 Tolerancia a Fallos y Resiliencia

| Estrategia | Aplicación |
|---|---|
| **Transacciones atómicas** | Asiento + detalles + actualización de saldos en una sola transacción DB con `SAVEPOINT` |
| **Retry con backoff** | Para operaciones de secuencia numérica bajo concurrencia |
| **Dead letter queue** | Eventos contables fallidos se almacenan para reprocesamiento |
| **Validación pre-commit** | Toda validación de negocio antes del flush/commit; fallo temprano con mensajes descriptivos |
| **Estado intermedio robusto** | Asientos en estado `BORRADOR` antes de `CONTABILIZADO`; nunca se crean directamente como activos |

### 2.4 Automatización Contable y Validaciones

| Funcionalidad | Estado del arte |
|---|---|
| **Templates de asientos** | Plantillas configurables por tipo de operación con variables (total, IVA, base gravable) |
| **Contabilización multi-evento** | Ventas, compras, producción, nómina, inventario, cartera — todos generan asientos automáticos |
| **Validación de cuenta** | Verificar que la cuenta acepta movimiento, que es del nivel correcto, que no está inactiva |
| **Alertas proactivas** | Notificación cuando el balance no cuadra, cuando hay cuentas sin movimiento prolongado, o retenciones sin aplicar |
| **Motor de reglas contables** | Reglas configurables tipo: "Si tipo_tercero = PROVEEDOR AND total > X → aplicar retención Y al Z%" |

### 2.5 Experiencia de Usuario en Sistemas Financieros

| Principio | Aplicación |
|---|---|
| **Formularios guiados** | Wizard para asientos manuales con autocompletado de cuentas por código/nombre |
| **Vista previa en tiempo real** | Mostrar balance del asiento mientras se edita, indicando si cuadra |
| **Dashboard contable** | KPIs: saldo de cuentas principales, asientos del período, alertas de cierre |
| **Drill-down** | Balance de prueba → clic en cuenta → movimientos de la cuenta → clic en asiento → detalle |
| **Exportación** | PDF, Excel, CSV para todos los reportes financieros |
| **Modo lectura para auditores** | Rol con acceso de solo lectura a toda la información contable |

### 2.6 Auditoría, Trazabilidad y Control

| Control | Mecanismo |
|---|---|
| **Audit log inmutable** | Tabla separada con cada cambio: quién, cuándo, qué campo, valor anterior, valor nuevo |
| **Número de asiento secuencial** | Secuencia sin huecos por período fiscal, verificable |
| **Hash de integridad** | Hash SHA-256 del contenido del asiento para detectar manipulación post-cierre |
| **Aprobación de asientos** | Flujo: Borrador → Pendiente Aprobación → Aprobado → Contabilizado |
| **Segregación de funciones** | Quien crea no aprueba; quien aprueba no puede crear asientos propios |

### 2.7 Cumplimiento Normativo (Colombia + Adaptable)

| Requisito | Detalle |
|---|---|
| **PUC Decreto 2650/93** | Plan de cuentas jerárquico de 6 niveles con clases 1-9 |
| **NIIF para PyMEs (Grupo 2)** | Tercera edición (feb 2025): nuevo modelo de ingresos (5 pasos, NIIF 15), instrumentos financieros (NIIF 9) |
| **Retención en la fuente** | ICA, IVA, renta — cálculo automático según tipo y monto de transacción |
| **Facturación electrónica DIAN** | CUFE, resolución de numeración, documento soporte electrónico |
| **Información exógena** | Generación de reportes para la DIAN con formatos normados |
| **Cierre fiscal** | Cancelación de cuentas 4/5/6, determinación de resultado del ejercicio, asiento de cierre |

### 2.8 Rendimiento y Escalabilidad

| Técnica | Beneficio |
|---|---|
| **Índices compuestos** | `(tenant_id, fecha, tipo_asiento)`, `(tenant_id, cuenta_id, fecha)` para queries de balance |
| **Vistas materializadas** | Saldos acumulados por cuenta y período, actualizados periódicamente |
| **Paginación server-side** | Cursor-based para listados de asientos con miles de registros |
| **Caché de plan de cuentas** | PUC rara vez cambia; cacheable por tenant con invalidación explícita |
| **Query optimizado para balance** | Uso de `window functions` y CTEs en lugar de múltiples JOINs |

---

## 3. Diagnóstico Estratégico del Módulo Actual

> **Supuestos explícitos**: El diagnóstico se basa en el análisis directo del código fuente actual, no en supuestos teóricos.

### 3.1 Componentes Analizados

| Componente | Archivo | Estado |
|---|---|---|
| Modelo `CuentasContables` | `backend/app/datos/modelos.py` L860-894 | ✅ Sólido — Jerárquico, 6 niveles, naturaleza, acepta_movimiento |
| Modelo `ConfiguracionContable` | `backend/app/datos/modelos.py` L901-923 | ⚠️ Existe pero **no se usa** en el servicio |
| Modelo `AsientosContables` | `backend/app/datos/modelos.py` L930-961 | ⚠️ Funcional pero sin tercero, sin período, sin aprobación |
| Modelo `DetallesAsiento` | `backend/app/datos/modelos.py` L968-1003 | ✅ Sólido — CHECK constraints, débito XOR crédito |
| Servicio `ServicioContabilidad` | `backend/app/servicios/servicio_contabilidad.py` | ⚠️ Códigos PUC hardcodeados, solo ventas/anulaciones |
| Ruta `contabilidad.py` | `backend/app/rutas/contabilidad.py` | ⚠️ CRUD básico, sin update/delete, sin validaciones avanzadas |
| Ruta `cuentas_contables.py` | `backend/app/rutas/cuentas_contables.py` | ⚠️ Solo GET lista, sin CRUD completo |
| Frontend `ContabilidadPage.tsx` | `frontend/src/pages/ContabilidadPage.tsx` | ⚠️ Vista lectura, sin formularios, sin reportes |
| Integración ventas | `backend/app/rutas/ventas.py` | ✅ Llama `crear_asiento_venta` al confirmar |
| Integración facturas | `backend/app/rutas/facturas.py` | ✅ Llama `crear_asiento_venta` y `crear_asiento_anulacion_venta` |

### 3.2 Hallazgos Críticos

#### 🔴 Crítico — Códigos PUC Hardcodeados
```python
# servicio_contabilidad.py líneas 134-136
cuenta_caja = self._obtener_cuenta_por_codigo("1105")
cuenta_ventas = self._obtener_cuenta_por_codigo("4135")
cuenta_iva = self._obtener_cuenta_por_codigo("2408")
```
**Problema**: Si un tenant configura cuentas PUC diferentes, el sistema falla silenciosamente (retorna `None`). Existe `ConfiguracionContable` pero no se utiliza.

#### 🔴 Crítico — Sin Períodos Contables
No existe concepto de período fiscal. Se pueden crear asientos en cualquier fecha pasada o futura sin restricción.

#### 🟡 Importante — Sin Tercero en Asientos
Los asientos no registran contra qué tercero se realizó la operación, perdiendo trazabilidad financiera esencial.

#### 🟡 Importante — Sin Automatización de Compras
Las compras (`Compras` model existe) no generan asientos contables automáticos.

#### 🟡 Importante — Reportes Financieros Mínimos
Solo balance de prueba. No existen: libro diario, libro mayor, estado de resultados, balance general.

#### 🟠 Moderado — Sin Flujo de Aprobación
Los asientos se crean directamente como `ACTIVO`. No hay estado `BORRADOR` ni flujo de aprobación.

#### 🟠 Moderado — Sin Retenciones
No hay cálculo ni registro de retenciones (fuente, ICA, IVA) en transacciones.

---

## 4. Plan de Mejora por Áreas — CON DETALLES DE IMPLEMENTACIÓN

---

### Fase 1 — Corrección de Fundamentos (Integridad Contable)

#### 1.1 Eliminar códigos PUC hardcodeados

**Archivos a modificar:**
- `backend/app/servicios/servicio_contabilidad.py` — Refactorizar `crear_asiento_venta`, `crear_asiento_anulacion_venta`
- `backend/app/rutas/ventas.py` — Actualizar llamadas
- `backend/app/rutas/facturas.py` — Actualizar llamadas

**Implementación:**

1. Crear método privado `_obtener_cuenta_configurada(concepto: str) -> CuentasContables` en `ServicioContabilidad`:
   - Busca en `ConfiguracionContable` por `concepto` y `tenant_id`
   - Retorna la cuenta asociada (débito o crédito según parámetro)
   - Si no encuentra, lanza `ValueError` con mensaje: `"Configuración contable '{concepto}' no encontrada. Configure las cuentas en Contabilidad > Configuración."`
   - NUNCA retornar `None` silenciosamente

2. Definir conceptos estándar como constantes en `backend/app/utils/constantes_contables.py`:
   - `VENTA_COBRO = "VENTA_COBRO"` (débito: cuenta de caja/banco)
   - `VENTA_INGRESO = "VENTA_INGRESO"` (crédito: cuenta de ingresos)
   - `VENTA_IVA = "VENTA_IVA"` (crédito: IVA por pagar)
   - `COMPRA_PAGO = "COMPRA_PAGO"` (crédito: cuenta de caja/CxP)
   - `COMPRA_GASTO = "COMPRA_GASTO"` (débito: inventario/gasto)
   - `COMPRA_IVA = "COMPRA_IVA"` (débito: IVA descontable)
   - `PRODUCCION_PT = "PRODUCCION_PT"` (débito: inventario producto terminado)
   - `PRODUCCION_MP = "PRODUCCION_MP"` (crédito: inventario materia prima)
   - `CARTERA_CXC = "CARTERA_CXC"` (débito: cuentas por cobrar)
   - `CARTERA_CXP = "CARTERA_CXP"` (crédito: cuentas por pagar)

3. Crear migración Alembic `add_default_configuracion_contable`:
   - INSERT en `configuracion_contable` para cada tenant existente con los conceptos estándar y cuentas PUC por defecto (1105, 4135, 2408, etc.)
   - Validar que las cuentas PUC existen para el tenant antes de insertar

4. Modificar seed de onboarding de tenant (`backend/app/servicios/servicio_tenant.py` o similar):
   - Al crear tenant nuevo, insertar automáticamente todas las configuraciones contables estándar con cuentas PUC por defecto

5. Reescribir `crear_asiento_venta`:
   - Reemplazar `self._obtener_cuenta_por_codigo("1105")` → `self._obtener_cuenta_configurada(VENTA_COBRO)`
   - Reemplazar `self._obtener_cuenta_por_codigo("4135")` → `self._obtener_cuenta_configurada(VENTA_INGRESO)`
   - Reemplazar `self._obtener_cuenta_por_codigo("2408")` → `self._obtener_cuenta_configurada(VENTA_IVA)`
   - Mismo patrón para `crear_asiento_anulacion_venta`

6. Crear endpoint CRUD para `ConfiguracionContable` en `backend/app/rutas/configuracion_contable.py`:
   - `GET /contabilidad/configuracion` — Lista todas las configuraciones del tenant
   - `PUT /contabilidad/configuracion/{concepto}` — Actualiza cuenta débito/crédito de un concepto
   - Roles: `admin`, `contador`

**Validación:** Ejecutar test que cree venta con tenant que tiene cuentas PUC diferentes a las estándar → debe funcionar correctamente.

---

#### 1.2 Períodos Contables

**Archivos a crear:**
- `backend/app/datos/modelos.py` — Nuevo modelo `PeriodosContables`
- `backend/app/rutas/periodos_contables.py` — Nuevo router
- `backend/app/servicios/servicio_contabilidad.py` — Agregar validación de período
- Migración Alembic: `add_periodos_contables`

**Implementación:**

1. Modelo `PeriodosContables` en `modelos.py`:
   - Hereda de `TenantMixin, Base`
   - Campos: `id` (UUID PK), `anio` (Integer, NOT NULL), `mes` (Integer 1-12, NOT NULL), `estado` (String: ABIERTO, CERRADO_PARCIAL, CERRADO), `fecha_cierre` (DateTime nullable), `cerrado_por` (UUID FK usuarios nullable), `created_at`, `updated_at`
   - CHECK: `mes >= 1 AND mes <= 12`
   - CHECK: `estado IN ('ABIERTO', 'CERRADO_PARCIAL', 'CERRADO')`
   - Índice UNIQUE: `(tenant_id, anio, mes)`

2. Agregar `periodo_id` (UUID FK nullable) a `AsientosContables`:
   - FK a `periodos_contables.id` con `ondelete="RESTRICT"`
   - Índice compuesto: `(tenant_id, periodo_id)`

3. Método `_validar_periodo(fecha: date)` en `ServicioContabilidad`:
   - Extraer año y mes de la fecha
   - Buscar período en DB; si no existe → crear automáticamente en estado ABIERTO (auto-apertura)
   - Si existe y estado == CERRADO → `ValueError("El período {mes}/{año} está cerrado. No se pueden registrar movimientos.")`
   - Retornar el `periodo_id` encontrado/creado

4. Integrar `_validar_periodo` en `crear_asiento()` (L38-117 actual):
   - Llamar ANTES de crear el asiento
   - Asignar `periodo_id` al asiento creado

5. Router `periodos_contables.py`:
   - `GET /contabilidad/periodos` — Lista períodos del tenant con conteo de asientos por período
   - `POST /contabilidad/periodos/{anio}/{mes}/cerrar` — Cierra período (valida balance cuadrado antes)
   - `POST /contabilidad/periodos/{anio}/{mes}/reabrir` — Reabre período (solo admin, registra motivo en log)
   - Roles: `admin` para cerrar/reabrir, `admin`+`contador` para listar

6. Migración Alembic:
   - Crear tabla `periodos_contables`
   - Agregar columna `periodo_id` a `asientos_contables`
   - Script de datos: crear períodos ABIERTOS para todos los meses que tengan asientos existentes, asignar `periodo_id` a asientos existentes basado en su fecha

**Validación:** Intentar crear asiento en período cerrado → debe fallar. Crear en período abierto → debe funcionar y tener `periodo_id` asignado.

---

#### 1.3 Tercero en Asientos

**Archivos a modificar:**
- `backend/app/datos/modelos.py` — Agregar campo a `AsientosContables`
- `backend/app/servicios/servicio_contabilidad.py` — Propagar tercero
- `backend/app/rutas/contabilidad.py` — Aceptar tercero en creación manual
- `backend/app/datos/esquemas.py` — Agregar `tercero_id` al schema de creación
- `frontend/src/types/index.ts` — Agregar campo al tipo
- Migración Alembic: `add_tercero_to_asientos`

**Implementación:**

1. En `AsientosContables` agregar:
   - `tercero_id = Column(UUID(as_uuid=True), ForeignKey("terceros.id", ondelete="RESTRICT"), nullable=True)`
   - Relación: `tercero = relationship("Terceros")`
   - Nuevo índice: `Index('idx_asientos_tenant_tercero', 'tenant_id', 'tercero_id')`

2. En `crear_asiento()`, agregar parámetro `tercero_id: Optional[UUID] = None` y asignar al objeto

3. En `crear_asiento_venta()` y `crear_asiento_anulacion_venta()`, agregar parámetro `tercero_id` y pasarlo a `crear_asiento()`

4. En `ventas.py` y `facturas.py`, pasar `tercero_id=venta.tercero_id` al llamar al servicio contable

5. En los tipos frontend, agregar `tercero_id: string | null` y `tercero_nombre?: string` a `AsientoContable`

6. Migración: `ALTER TABLE asientos_contables ADD COLUMN tercero_id UUID REFERENCES terceros(id)`

**Validación:** Crear venta → asiento generado debe tener `tercero_id` del cliente. Verificar en listado de asientos.

---

### Fase 2 — Automatización Contable Completa

#### 2.1 Asientos Automáticos de Compras

**Archivos a modificar:**
- `backend/app/servicios/servicio_contabilidad.py` — Nuevos métodos
- `backend/app/rutas/compras.py` — Integrar contabilización

**Implementación:**

1. Agregar método `crear_asiento_compra(fecha, subtotal, total_iva, total, documento_referencia, tercero_id)`:
   - DÉBITO: cuenta `COMPRA_GASTO` por `subtotal` (inventario o gasto según config)
   - DÉBITO: cuenta `COMPRA_IVA` por `total_iva` (si > 0, IVA descontable)
   - CRÉDITO: cuenta `COMPRA_PAGO` por `total` (CxP o caja)
   - Usar `_obtener_cuenta_configurada()` para todas las cuentas
   - `tipo_asiento = "COMPRAS"`

2. Agregar método `crear_asiento_anulacion_compra(...)`:
   - Inversión exacta del asiento de compra
   - `documento_referencia = f"ANUL-{doc_ref}"`

3. En `compras.py`, al cambiar estado a `RECIBIDA`:
   - Llamar `servicio_cont.crear_asiento_compra(...)` con datos de la compra
   - Pasar `tercero_id` del proveedor

4. Al anular compra:
   - Llamar `servicio_cont.crear_asiento_anulacion_compra(...)`

**Validación:** Recibir compra → verificar asiento con débito en inventario y crédito en CxP. Anular → verificar reversión.

---

#### 2.2 Asientos de Producción

**Archivos a modificar:**
- `backend/app/servicios/servicio_contabilidad.py` — Nuevo método
- `backend/app/rutas/recetas.py` (endpoint `/producir`) — Integrar

**Implementación:**

1. Agregar método `crear_asiento_produccion(fecha, costo_mp, costo_mo, costo_total, documento_referencia)`:
   - DÉBITO: cuenta `PRODUCCION_PT` por `costo_total` (inventario producto terminado)
   - CRÉDITO: cuenta `PRODUCCION_MP` por `costo_mp` (inventario materia prima)
   - CRÉDITO: cuenta `PRODUCCION_MO` por `costo_mo` (mano de obra, si > 0)
   - `tipo_asiento = "PRODUCCION"`

2. Agregar tipo `PRODUCCION_MO` a constantes contables y configuración

3. En `recetas.py` endpoint `/producir`, después de crear movimiento de inventario, llamar al servicio contable

**Validación:** Producir receta → verificar asiento con débito PT y crédito MP + MO.

---

#### 2.3 Asientos de Cartera

**Archivos a modificar:**
- `backend/app/servicios/servicio_contabilidad.py` — Nuevo método
- `backend/app/rutas/cartera.py` — Integrar en registro de pago

**Implementación:**

1. Agregar `crear_asiento_pago_cartera(fecha, valor, tipo_cartera, documento_referencia, tercero_id)`:
   - Si `tipo_cartera == "COBRAR"` (cobro a cliente): DÉBITO caja, CRÉDITO CxC
   - Si `tipo_cartera == "PAGAR"` (pago a proveedor): DÉBITO CxP, CRÉDITO caja
   - `tipo_asiento = "OTRO"` (o agregar "CARTERA" a los tipos válidos)

2. Agregar `"CARTERA"` al CHECK constraint de `tipo_asiento` en `AsientosContables` (requiere migración)

3. En `cartera.py` al registrar pago, llamar al servicio contable

**Validación:** Registrar pago de cartera CxC → verificar asiento débito caja, crédito CxC.

---

#### 2.4 Motor de Templates Contables (Fase avanzada)

**Archivos a crear:**
- `backend/app/datos/modelos.py` — Nuevos modelos `TemplateAsiento`, `TemplateAsientoLinea`
- `backend/app/servicios/servicio_contabilidad.py` — Método genérico `crear_asiento_desde_template`
- `backend/app/rutas/templates_contables.py` — CRUD de templates
- Migración Alembic

**Implementación:**

1. Modelo `TemplateAsiento`:
   - `id`, `tenant_id`, `nombre`, `tipo_asiento`, `concepto_template` (con placeholders como `{documento_referencia}`), `es_sistema` (bool, protege templates predeterminados), `estado`

2. Modelo `TemplateAsientoLinea`:
   - `id`, `template_id`, `configuracion_contable_concepto` (referencia al concepto en `ConfiguracionContable`), `lado` (DEBITO/CREDITO), `variable` (ej: "total", "subtotal", "total_iva"), `descripcion_template`

3. Método `crear_asiento_desde_template(template_nombre, variables: dict, fecha, tercero_id, documento_referencia)`:
   - Buscar template por nombre y tenant
   - Para cada línea del template: resolver la cuenta desde `ConfiguracionContable`, obtener el monto de `variables[linea.variable]`, asignar a débito/crédito según `linea.lado`
   - Llamar a `crear_asiento()` con los detalles resueltos

4. Reescribir `crear_asiento_venta`, `crear_asiento_compra`, etc. como wrappers que llaman a `crear_asiento_desde_template` con el template y variables correspondientes

**Validación:** Crear template personalizado → usar para generar asiento → verificar que funciona igual que los métodos actuales.

---

### Fase 3 — Reportes Financieros

#### 3.1 Libro Diario

**Archivos a crear/modificar:**
- `backend/app/rutas/contabilidad.py` — Nuevo endpoint
- `frontend/src/pages/ContabilidadPage.tsx` — Nueva pestaña

**Implementación:**

1. Endpoint `GET /contabilidad/libro-diario`:
   - Parámetros: `fecha_inicio`, `fecha_fin`, `tipo_asiento`, `skip`, `limit`
   - Query: JOINar `AsientosContables` → `DetallesAsiento` → `CuentasContables`
   - Filtrar por `estado = "CONTABILIZADO"` (o `"ACTIVO"` según la fase actual)
   - Retornar lista plana: `fecha`, `numero_asiento`, `cuenta_codigo`, `cuenta_nombre`, `concepto`, `debito`, `credito`, `documento_referencia`, `tercero_nombre`
   - Incluir totales: `total_debito`, `total_credito`, `total_registros`
   - Ordenar por `fecha ASC, numero_asiento ASC`

2. En frontend: tabla con columnas fijas, filtros por fecha y tipo, paginación server-side, botón exportar

---

#### 3.2 Libro Mayor

**Implementación:**

1. Endpoint `GET /contabilidad/libro-mayor/{cuenta_id}`:
   - Parámetros: `fecha_inicio`, `fecha_fin`, `skip`, `limit`
   - Query: `DetallesAsiento` filtrado por `cuenta_id` + JOIN `AsientosContables`
   - Calcular `saldo_acumulado` con window function o acumulado en Python
   - Retornar: `fecha`, `numero_asiento`, `concepto`, `documento_referencia`, `debito`, `credito`, `saldo_acumulado`
   - Incluir `saldo_anterior` (suma de movimientos antes de `fecha_inicio`)

2. Endpoint `GET /contabilidad/libro-mayor` (resumen):
   - Lista de cuentas con movimiento en el período, con totales débito/crédito/saldo
   - Drill-down: clic en cuenta → redirige al detalle con `cuenta_id`

---

#### 3.3 Estado de Resultados

**Implementación:**

1. Endpoint `GET /contabilidad/estado-resultados`:
   - Parámetros: `fecha_inicio`, `fecha_fin`
   - Query: Sumar débitos y créditos por cuenta, filtrar por clases PUC:
     - Clase 4 (Ingresos): saldo = créditos - débitos
     - Clase 5 (Gastos): saldo = débitos - créditos
     - Clase 6 (Costos): saldo = débitos - créditos
   - Calcular: `utilidad_bruta = ingresos - costos`, `utilidad_operacional = utilidad_bruta - gastos`, `utilidad_neta = utilidad_operacional`
   - Retornar estructura jerárquica agrupada por clase y grupo de cuenta
   - Incluir campo `periodo_anterior` para comparativo (mismos meses del año anterior)

---

#### 3.4 Balance General

**Implementación:**

1. Endpoint `GET /contabilidad/balance-general`:
   - Parámetro: `fecha_corte`
   - Query: Sumar todos los movimientos hasta `fecha_corte` por cuenta:
     - Clase 1 (Activos): saldo = débitos - créditos
     - Clase 2 (Pasivos): saldo = créditos - débitos
     - Clase 3 (Patrimonio): saldo = créditos - débitos
   - Verificar ecuación: `activos = pasivos + patrimonio`
   - Retornar estructura jerárquica con totales por clase y grupo
   - Flag `cuadrado: bool` indicando si la ecuación se cumple

---

#### 3.5 Auxiliar por Tercero

**Implementación:**

1. Endpoint `GET /contabilidad/auxiliar-tercero`:
   - Parámetros: `tercero_id` (opcional), `fecha_inicio`, `fecha_fin`, `cuenta_id` (opcional)
   - Si `tercero_id`: movimientos del tercero con saldo acumulado
   - Si no: resumen por tercero (nombre, total débito, total crédito, saldo)
   - Requiere que `tercero_id` exista en `AsientosContables` (Fase 1.3)

---

### Fase 4 — Auditoría y Control

#### 4.1 Flujo de Estados de Asiento

**Archivos a modificar:**
- `backend/app/datos/modelos.py` — Actualizar CHECK constraint de estado
- `backend/app/servicios/servicio_contabilidad.py` — Lógica de transiciones
- `backend/app/rutas/contabilidad.py` — Nuevos endpoints

**Implementación:**

1. Migración: Actualizar CHECK de `estado` en `AsientosContables` a: `('BORRADOR', 'PENDIENTE_APROBACION', 'CONTABILIZADO', 'ANULADO')`
   - Migrar datos existentes: `ACTIVO` → `CONTABILIZADO`

2. Nuevos endpoints:
   - `POST /contabilidad/asientos/{id}/enviar-aprobacion` — BORRADOR → PENDIENTE_APROBACION
   - `POST /contabilidad/asientos/{id}/aprobar` — PENDIENTE_APROBACION → CONTABILIZADO
   - `POST /contabilidad/asientos/{id}/rechazar` — PENDIENTE_APROBACION → BORRADOR (con motivo)
   - `POST /contabilidad/asientos/{id}/anular` — CONTABILIZADO → ANULADO (genera asiento de reversión)

3. Asientos automáticos (ventas, compras, etc.) se crean directamente como `CONTABILIZADO`
4. Asientos manuales se crean como `BORRADOR`
5. Solo asientos `CONTABILIZADO` aparecen en reportes financieros

---

#### 4.2 Log de Auditoría Contable

**Archivos a crear:**
- `backend/app/datos/modelos.py` — Modelo `AuditLogContable`
- Migración Alembic

**Implementación:**

1. Modelo `AuditLogContable`:
   - `id` (UUID PK), `tenant_id`, `asiento_id` (FK), `accion` (CREACION, APROBACION, RECHAZO, ANULACION, MODIFICACION), `usuario_id` (FK), `timestamp` (DateTime server_default now), `detalle` (JSONB: campos modificados, motivo, etc.)
   - SIN `updated_at` — tabla solo INSERT
   - Índice: `(tenant_id, asiento_id)`, `(tenant_id, timestamp)`

2. Método `_registrar_auditoria(asiento_id, accion, detalle)` en `ServicioContabilidad`
3. Llamar en cada transición de estado y al crear asiento
4. Endpoint `GET /contabilidad/asientos/{id}/auditoria` — Retorna historial de acciones del asiento

---

#### 4.3 Cierre Fiscal

**Implementación:**

1. Endpoint `POST /contabilidad/cierre-fiscal/{anio}`:
   - Verificar que todos los períodos del año estén cerrados
   - Verificar balance cuadrado
   - Generar asiento de cierre: cancelar saldos de clases 4, 5, 6 contra cuenta de utilidad/pérdida del ejercicio (clase 3)
   - Marcar año como cerrado (flag en períodos o tabla separada)
   - Rol: solo `admin`

---

### Fase 5 — Cumplimiento Normativo

#### 5.1 Retenciones

**Archivos a crear:**
- `backend/app/datos/modelos.py` — Modelos `TiposRetencion`, `RetencionesAplicadas`
- `backend/app/servicios/servicio_retenciones.py`
- `backend/app/rutas/retenciones.py`
- Migración Alembic

**Implementación:**

1. `TiposRetencion`: `id`, `tenant_id`, `nombre` (Rete-Fuente, Rete-ICA, Rete-IVA), `base_minima` (UVT), `porcentaje`, `cuenta_contable_id`, `estado`
2. `RetencionesAplicadas`: `id`, `tenant_id`, `tipo_retencion_id`, `asiento_id`, `transaccion_tipo` (VENTA/COMPRA), `transaccion_id`, `base`, `porcentaje_aplicado`, `valor`
3. Servicio: al crear asiento automático, verificar si aplica retención según tipo de tercero y monto; si aplica, agregar línea adicional al asiento
4. CRUD de tipos de retención y reporte de retenciones aplicadas por período

---

#### 5.2 Centros de Costo

**Implementación:**

1. Modelo `CentrosCosto`: `id`, `tenant_id`, `codigo`, `nombre`, `estado`, `created_at`
   - Índice UNIQUE: `(tenant_id, codigo)`
2. Agregar `centro_costo_id` (UUID FK nullable) a `DetallesAsiento`
3. Migración + actualizar servicio para aceptar `centro_costo_id` en detalles
4. Reportes: filtro por centro de costo en todos los reportes existentes

---

#### 5.3 Preparación NIIF

**Implementación:**
1. Agregar `clasificacion_niif` (String nullable) a `CuentasContables`
2. Mapeo PUC → NIIF en seed
3. Endpoint para reporte NIIF que agrupa y presenta según clasificación internacional

---

### Fase 6 — Experiencia de Usuario

#### 6.1 Reestructuración del Frontend Contable

**Archivos a crear/modificar:**
- `frontend/src/pages/ContabilidadPage.tsx` — Refactorizar con tabs
- `frontend/src/pages/contabilidad/AsientosTab.tsx` — Listado + formulario creación
- `frontend/src/pages/contabilidad/PlanCuentasTab.tsx` — CRUD de cuentas
- `frontend/src/pages/contabilidad/ReportesTab.tsx` — Sub-navegación de reportes
- `frontend/src/pages/contabilidad/ConfiguracionTab.tsx` — ConfiguracionContable + Períodos
- `frontend/src/api/endpoints.ts` — Nuevos endpoints

**Implementación:**

1. Tabs principales: Asientos | Plan de Cuentas | Reportes | Configuración
2. Tab Asientos: tabla con filtros (fecha, tipo, estado, tercero), botón "Nuevo Asiento Manual", modal/drawer de creación con:
   - Selector de fecha (validado contra período abierto)
   - Selector de tipo de asiento
   - Campo concepto
   - Tabla dinámica de líneas: selector de cuenta (autocompletado por código/nombre), débito, crédito, descripción
   - Indicador de balance en tiempo real: `total_debito - total_credito` con color verde (= 0) o rojo (!= 0)
   - Botón guardar solo habilitado cuando balance = 0
3. Tab Plan de Cuentas: árbol jerárquico con expand/collapse, botón agregar subcuenta, activar/desactivar
4. Tab Reportes: sub-tabs para cada reporte (Libro Diario, Libro Mayor, Balance de Prueba, Estado de Resultados, Balance General, Auxiliar Tercero) con exportación
5. Tab Configuración: tabla editable de `ConfiguracionContable`, gestión de períodos (abrir/cerrar)

---

#### 6.2 y 6.3 — Reportes Interactivos y Dashboard Contable

**Implementación:**

1. Cada reporte usa componente tabla reutilizable con:
   - Filtros de período (selector de mes/año o rango de fechas)
   - Botón exportar PDF (generar en backend con `reportlab` o `weasyprint`) y Excel (con `openpyxl`)
   - Drill-down: filas clickeables que navegan al detalle
2. Dashboard contable como sub-ruta o widget en el dashboard principal:
   - Cards con KPIs: Activos totales, Pasivos totales, Patrimonio, Utilidad del período
   - Gráfico de barras: Ingresos vs Gastos por mes (últimos 6 meses)
   - Lista de asientos pendientes de aprobación (si existe flujo)
   - Alerta de períodos próximos a cerrar

---

### Fase 7 — Rendimiento y Escalabilidad

#### 7.1 Optimización de Queries

**Implementación:**

1. Migración con nuevos índices:
   - `CREATE INDEX idx_detalles_asiento_cuenta_fecha ON detalles_asiento(tenant_id, cuenta_id) INCLUDE (debito, credito)`
   - `CREATE INDEX idx_asientos_periodo ON asientos_contables(tenant_id, periodo_id, estado)`
2. Reescribir `obtener_balance_prueba` usando CTE:
   - CTE 1: filtrar asientos por tenant, estado, fechas
   - CTE 2: sumar débitos/créditos por cuenta_id con JOIN al CTE 1
   - SELECT final: JOIN con cuentas_contables para nombres

---

#### 7.2 Saldos Pre-calculados

**Implementación:**

1. Modelo `SaldosCuenta`: `id`, `tenant_id`, `cuenta_id` (FK), `periodo_id` (FK), `saldo_inicial`, `total_debitos`, `total_creditos`, `saldo_final`
   - Índice UNIQUE: `(tenant_id, cuenta_id, periodo_id)`
2. Al contabilizar asiento: actualizar saldos atómicamente en la misma transacción
3. Balance de prueba consulta `SaldosCuenta` en lugar de recalcular por agregación
4. Comando de recalculo: endpoint `POST /contabilidad/recalcular-saldos` para sincronizar si hay inconsistencias

---

#### 7.3 Paginación Eficiente

**Implementación:**
1. Cambiar paginación de offset-based a cursor-based en listados de asientos usando `(fecha, id)` como cursor
2. Frontend: implementar infinite scroll o paginación con cursor en la tabla de asientos
3. Detalles de asiento: cargar con `selectinload` solo al ver detalle individual, no en listado

---

## 5. Priorización: Impacto vs Esfuerzo

| # | Mejora | Impacto | Esfuerzo | Prioridad |
|---|---|---|---|---|
| 1 | Eliminar PUC hardcodeado + usar `ConfiguracionContable` | 🔴 Crítico | 🟢 Bajo | **P0 — Inmediata** |
| 2 | Períodos contables | 🔴 Crítico | 🟡 Medio | **P0 — Inmediata** |
| 3 | Tercero en asientos | 🟡 Alto | 🟢 Bajo | **P1 — Corto plazo** |
| 4 | Asientos automáticos de compras | 🟡 Alto | 🟡 Medio | **P1 — Corto plazo** |
| 5 | Libro diario y libro mayor | 🟡 Alto | 🟡 Medio | **P1 — Corto plazo** |
| 6 | Estado de resultados y balance general | 🟡 Alto | 🟡 Medio | **P2 — Medio plazo** |
| 7 | Flujo de aprobación de asientos | 🟠 Medio | 🟡 Medio | **P2 — Medio plazo** |
| 8 | Asientos de producción y cartera | 🟠 Medio | 🟡 Medio | **P2 — Medio plazo** |
| 9 | Frontend contable completo | 🟡 Alto | 🔴 Alto | **P2 — Medio plazo** |
| 10 | Log de auditoría contable | 🟠 Medio | 🟢 Bajo | **P2 — Medio plazo** |
| 11 | Motor de templates contables | 🟡 Alto | 🔴 Alto | **P3 — Largo plazo** |
| 12 | Retenciones | 🟠 Medio | 🔴 Alto | **P3 — Largo plazo** |
| 13 | Centros de costo | 🟠 Medio | 🟡 Medio | **P3 — Largo plazo** |
| 14 | Cierre fiscal | 🟡 Alto | 🔴 Alto | **P3 — Largo plazo** |
| 15 | Saldos pre-calculados | 🟢 Optimización | 🟡 Medio | **P3 — Largo plazo** |
| 16 | Dashboard contable | 🟠 Medio | 🟡 Medio | **P3 — Largo plazo** |
| 17 | Preparación NIIF | 🟢 Estratégico | 🟡 Medio | **P4 — Futuro** |

---

## 6. Roadmap Sugerido

### Estimación por Fase

| Fase | Alcance | Estimación |
|---|---|---|
| **P0** | Fundamentos de integridad | 1-2 semanas |
| **P1** | Automatización + reportes básicos | 2-3 semanas |
| **P2** | Reportes avanzados + control + frontend | 3-4 semanas |
| **P3** | Normativo + optimización + templates | 4-5 semanas |
| **P4** | NIIF completo | Según demanda |

**Tiempo total estimado**: 10-14 semanas de desarrollo incremental.

**Secuencia de ejecución recomendada por eficiencia:**
1. P0 completa (1.1 → 1.2 → 1.3) — cada ítem depende del anterior
2. P1: 2.1 y 3.1 pueden ejecutarse en paralelo; 3.2 depende de 3.1
3. P2: 4.1 antes de 4.2; 3.3 y 3.4 en paralelo; 6.1 puede iniciar con 3.3
4. P3: 2.4 primero (simplifica todo lo demás); luego 5.1, 5.2, 4.3 secuenciales; 7.1-7.3 al final

---

## 7. Checklist Técnico de Validación Final

### Integridad Contable
- [ ] Todo asiento cumple partida doble: `SUM(debito) = SUM(credito)` ≠ 0
- [ ] Cada línea de asiento tiene débito > 0 XOR crédito > 0 (nunca ambos)
- [ ] Cuentas usadas en asientos son de último nivel (`acepta_movimiento = true`)
- [ ] No existen asientos con fecha fuera de un período abierto
- [ ] No existen asientos modificados en períodos cerrados
- [ ] Números de asiento son secuenciales sin huecos dentro de cada período
- [ ] Balance de prueba cuadra: `total_debitos = total_creditos` en todo momento

### Configuración
- [ ] `ConfiguracionContable` tiene conceptos definidos para todos los tipos de asiento automático
- [ ] Ningún código PUC está hardcodeado en el servicio
- [ ] Seed de configuración contable se ejecuta en onboarding de tenant
- [ ] Error explícito si falta configuración contable al intentar contabilizar

### Automatización
- [ ] Venta confirmada → asiento automático con cuentas configurables
- [ ] Anulación de venta → asiento de reversión
- [ ] Compra recibida → asiento automático
- [ ] Pago de cartera → asiento automático
- [ ] Producción completada → asiento automático
- [ ] Todos los asientos automáticos incluyen `documento_referencia` y `tercero_id`

### Reportes
- [ ] Balance de prueba con filtros de período y verificación de cuadre
- [ ] Libro diario completo con paginación
- [ ] Libro mayor por cuenta con saldo acumulado
- [ ] Estado de resultados por período
- [ ] Balance general a fecha
- [ ] Auxiliar por tercero

### Auditoría
- [ ] Toda acción contable queda registrada en log de auditoría
- [ ] Asientos manuales pasan por flujo de aprobación antes de afectar saldos
- [ ] No es posible eliminar asientos; solo anular con asiento de reversión
- [ ] Períodos cerrados son inmutables

### Seguridad y Roles
- [ ] Solo roles `admin` y `contador` pueden crear asientos
- [ ] Solo `admin` puede cerrar períodos
- [ ] Log de auditoría es inmutable (no UPDATE, no DELETE)
- [ ] Aislamiento por tenant verificado en todas las queries contables

### Rendimiento
- [ ] Índices compuestos cubren las queries principales de reportes
- [ ] Balance de prueba responde en < 2 segundos para tenants con < 10,000 asientos
- [ ] Paginación server-side en todos los listados
- [ ] Plan de cuentas cacheado donde sea posible

### Frontend
- [ ] Formulario de creación de asientos con validación de balance en tiempo real
- [ ] Autocompletado de cuentas por código y nombre
- [ ] CRUD de plan de cuentas
- [ ] Todos los reportes con exportación PDF/Excel
- [ ] Drill-down funcional: balance → cuenta → asiento → detalle
