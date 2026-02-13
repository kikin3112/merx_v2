# CHANDELIER ERP/POS - PRD TÉCNICO

## VISIÓN
Sistema ERP/POS SaaS multi-tenant para microempresas de candelería en Colombia. Automatiza facturación, inventario, contabilidad y reportes con RLS nativo.

## ALCANCE MVP

### IN SCOPE
- Auth JWT + Multi-tenancy (RLS PostgreSQL)
- CRUD Productos + Inventario (valorización promedio ponderado)
- **Recetas velas (BOM)**: Materias primas → Productos terminados
- **Calculadora márgenes**: Costo + margen deseado → Precio sugerido
- CRM Clientes básico
- Cotizaciones
- Facturación informal (PDF, sin DIAN)
- POS mobile-first
- Contabilidad automática (PUC Colombia, ~40 cuentas)
- Dashboard + reportes básicos
- Reportes avanzados
- Storage S3/R2 (PDFs, logos)
- Pagos online Wompi (cobro suscripciones SaaS)

### OUT SCOPE (Fase 2+)
- Facturación electrónica DIAN
- Compras (solo ajustes manuales inventario)
- WhatsApp Business API
- Pagos online Wompi (para que tenants cobren a sus clientes)
- Modo offline

## STACK TECNOLÓGICO

### Backend
- FastAPI 0.110+
- PostgreSQL 16 (RLS habilitado)
- SQLAlchemy 2.0 (async)
- Alembic (migraciones)
- Celery + Redis (tareas async)
- Pydantic v2 (validación)
- boto3 (S3/R2)
- ReportLab (PDF generación)

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Zustand (state)
- React Query (API cache)
- Axios

### Infraestructura
- Docker Compose (dev/prod)
- Nginx (reverse proxy)
- Let's Encrypt (SSL)
- Sentry (error tracking)
- UptimeRobot (monitoring)

## ENTIDADES CORE

### Globales (Sin RLS)
```
planes
├── id: UUID PK
├── nombre: VARCHAR(50) UNIQUE
├── precio_mensual: DECIMAL(10,2)
├── max_usuarios: INTEGER
├── max_facturas_mes: INTEGER
└── caracteristicas: JSONB

tenants
├── id: UUID PK
├── nombre: VARCHAR(200)
├── slug: VARCHAR(100) UNIQUE
├── url_logo: VARCHAR(500)
├── plan_id: UUID FK
├── estado: ENUM(activo, suspendido, cancelado)
├── creado_en: TIMESTAMP
└── actualizado_en: TIMESTAMP

suscripciones
├── id: UUID PK
├── tenant_id: UUID FK
├── plan_id: UUID FK
├── estado: ENUM(activa, suspendida, cancelada, vencida)
├── fecha_inicio: DATE
├── fecha_fin: DATE NULL
├── fecha_proximo_pago: DATE
├── metodo_pago: VARCHAR(50) NULL (wompi, manual)
├── referencia_pago: VARCHAR(200) NULL (transaction_id Wompi)
└── creado_en: TIMESTAMP
    INDEX(tenant_id, estado)
    INDEX(fecha_proximo_pago)

pagos_suscripcion
├── id: UUID PK
├── suscripcion_id: UUID FK
├── monto: DECIMAL(10,2)
├── fecha_pago: DATE
├── metodo: VARCHAR(50) (wompi, manual)
├── estado: ENUM(pendiente, aprobado, rechazado, reembolsado)
├── referencia_externa: VARCHAR(200) (transaction_id Wompi)
├── metadata: JSONB NULL
└── creado_en: TIMESTAMP
    INDEX(suscripcion_id, fecha_pago DESC)

usuarios
├── id: UUID PK
├── email: VARCHAR(100) UNIQUE
├── hash_password: VARCHAR(255)
├── es_superadmin: BOOLEAN DEFAULT false
├── creado_en: TIMESTAMP
└── ultimo_acceso: TIMESTAMP

usuarios_tenants
├── usuario_id: UUID FK
├── tenant_id: UUID FK
├── rol: ENUM(admin, vendedor, contador)
├── esta_activo: BOOLEAN DEFAULT true
└── creado_en: TIMESTAMP
    PK(usuario_id, tenant_id)
    RLS: tenant_id = current_setting('app.tenant_id_actual')::uuid
```

### Por Tenant (Con RLS)
```
configuracion_tenant
├── tenant_id: UUID PK FK
├── prefijo_factura: VARCHAR(10) DEFAULT 'FAC'
├── numero_siguiente_factura: INTEGER DEFAULT 1
├── resolucion_dian: VARCHAR(100) NULL
├── tarifa_iva_default: DECIMAL(5,2) DEFAULT 19.00
└── dias_alerta_vencimiento: INTEGER DEFAULT 7

categorias
├── id: UUID PK
├── tenant_id: UUID FK
├── nombre: VARCHAR(100)
├── padre_id: UUID FK NULL (jerarquía)
└── creado_en: TIMESTAMP
    UNIQUE(tenant_id, nombre)

productos
├── id: UUID PK
├── tenant_id: UUID FK
├── sku: VARCHAR(50)
├── nombre: VARCHAR(200)
├── categoria_id: UUID FK NULL
├── tipo: ENUM(producto_terminado, materia_prima)
├── precio_venta: DECIMAL(12,2)
├── precio_costo: DECIMAL(12,2)
├── stock: INTEGER DEFAULT 0
├── tarifa_iva: DECIMAL(5,2)
├── alerta_stock_min: INTEGER DEFAULT 5
├── creado_en: TIMESTAMP
└── actualizado_en: TIMESTAMP
    UNIQUE(tenant_id, sku)
    INDEX(tenant_id, tipo)

recetas
├── id: UUID PK
├── tenant_id: UUID FK
├── producto_id: UUID FK (producto_terminado)
├── rendimiento: INTEGER DEFAULT 1 (unidades que produce)
└── creado_en: TIMESTAMP
    UNIQUE(tenant_id, producto_id)

recetas_detalles
├── id: UUID PK
├── receta_id: UUID FK
├── materia_prima_id: UUID FK (productos.tipo = materia_prima)
├── cantidad: DECIMAL(10,4)
└── unidad: VARCHAR(20) (g, ml, ud)
    INDEX(receta_id)

movimientos_stock
├── id: UUID PK
├── tenant_id: UUID FK
├── producto_id: UUID FK
├── tipo: ENUM(entrada, salida, ajuste, produccion)
├── cantidad: INTEGER
├── tipo_referencia: VARCHAR(50) (factura, ajuste, produccion)
├── id_referencia: UUID NULL
├── costo_por_unidad: DECIMAL(12,2)
├── usuario_id: UUID FK
└── creado_en: TIMESTAMP
    INDEX(tenant_id, producto_id, creado_en DESC)

clientes
├── id: UUID PK
├── tenant_id: UUID FK
├── nombre: VARCHAR(200)
├── nit: VARCHAR(50)
├── email: VARCHAR(100)
├── telefono: VARCHAR(20)
├── direccion: TEXT
├── retencion_iva: BOOLEAN DEFAULT false
├── creado_en: TIMESTAMP
└── actualizado_en: TIMESTAMP
    UNIQUE(tenant_id, nit)

facturas
├── id: UUID PK
├── tenant_id: UUID FK
├── numero: VARCHAR(50)
├── cliente_id: UUID FK
├── fecha_emision: DATE
├── fecha_vencimiento: DATE
├── subtotal: DECIMAL(12,2)
├── total_iva: DECIMAL(12,2)
├── total: DECIMAL(12,2)
├── estado: ENUM(borrador, emitida, pagada, anulada)
├── notas: TEXT NULL
├── url_pdf: VARCHAR(500) NULL
├── creado_por: UUID FK
├── creado_en: TIMESTAMP
└── anulada_en: TIMESTAMP NULL
    UNIQUE(tenant_id, numero)
    INDEX(tenant_id, estado, fecha_emision DESC)

cotizaciones
├── id: UUID PK
├── tenant_id: UUID FK
├── numero: VARCHAR(50)
├── cliente_id: UUID FK
├── fecha_emision: DATE
├── fecha_vencimiento: DATE
├── subtotal: DECIMAL(12,2)
├── total_iva: DECIMAL(12,2)
├── total: DECIMAL(12,2)
├── estado: ENUM(borrador, enviada, aceptada, rechazada, convertida)
├── notas: TEXT NULL
├── url_pdf: VARCHAR(500) NULL
├── factura_id: UUID FK NULL (si fue convertida)
├── creado_por: UUID FK
└── creado_en: TIMESTAMP
    UNIQUE(tenant_id, numero)
    INDEX(tenant_id, estado, fecha_emision DESC)

cotizaciones_detalles
├── id: UUID PK
├── cotizacion_id: UUID FK
├── producto_id: UUID FK
├── descripcion: VARCHAR(200)
├── cantidad: INTEGER
├── precio_unitario: DECIMAL(12,2)
├── descuento: DECIMAL(12,2) DEFAULT 0
├── tarifa_iva: DECIMAL(5,2)
├── subtotal: DECIMAL(12,2)
├── valor_iva: DECIMAL(12,2)
└── total: DECIMAL(12,2)
    INDEX(cotizacion_id)

facturas_detalles
├── id: UUID PK
├── factura_id: UUID FK
├── producto_id: UUID FK
├── descripcion: VARCHAR(200)
├── cantidad: INTEGER
├── precio_unitario: DECIMAL(12,2)
├── descuento: DECIMAL(12,2) DEFAULT 0
├── tarifa_iva: DECIMAL(5,2)
├── subtotal: DECIMAL(12,2)
├── valor_iva: DECIMAL(12,2)
└── total: DECIMAL(12,2)
    INDEX(factura_id)

cuentas_puc
├── id: UUID PK
├── codigo: VARCHAR(10) UNIQUE
├── nombre: VARCHAR(200)
├── nivel: INTEGER (1-4)
├── padre_id: UUID FK NULL
├── tipo: ENUM(activo, pasivo, patrimonio, ingreso, gasto)
└── acepta_movimientos: BOOLEAN

asientos_contables
├── id: UUID PK
├── tenant_id: UUID FK
├── numero: INTEGER
├── fecha: DATE
├── tipo_origen: VARCHAR(50) (factura, compra, ajuste)
├── id_referencia: UUID NULL
├── notas: TEXT NULL
├── creado_por: UUID FK
└── creado_en: TIMESTAMP
    UNIQUE(tenant_id, numero)
    INDEX(tenant_id, fecha DESC)

asientos_detalles
├── id: UUID PK
├── asiento_id: UUID FK
├── cuenta_puc_id: UUID FK
├── debe: DECIMAL(14,2) DEFAULT 0
├── haber: DECIMAL(14,2) DEFAULT 0
└── descripcion: VARCHAR(200)
    INDEX(asiento_id)
    CHECK(debe > 0 OR haber > 0)
    CHECK(debe = 0 OR haber = 0)
```

## REGLAS DE NEGOCIO

### Multi-Tenancy
- Header obligatorio: `X-Tenant-ID: <uuid>`
- Middleware valida: usuario tiene acceso al tenant
- `SET LOCAL app.tenant_id_actual = '<uuid>'` antes de cada query
- RLS bloquea acceso entre tenants automáticamente
- Un tenant puede tener varios usuarios con rol de vendedor; solo un usuario para admin y NINGUNO de superadmin.

### Productos
- SKU único por tenant
- Stock no puede ser negativo (validación app + DB constraint)
- `precio_venta` y `precio_costo` > 0
- Costo promedio ponderado: `(stock_actual × costo_actual + entrada × costo_nuevo) / (stock_actual + entrada)`

### Recetas (BOM)
- Solo productos `tipo=producto_terminado` pueden tener receta
- Materias primas deben tener `tipo=materia_prima`
- Al producir N unidades:
  1. Crear movimiento_stock `tipo=produccion` para producto terminado (+N)
  2. Crear movimientos_stock `tipo=salida` para cada materia prima (-cantidad × N)
  3. Validar stock suficiente de materias primas antes de producir

### Calculadora Márgenes
- Input: `precio_costo`, `margen_deseado` (%)
- Output: `precio_venta_sugerido = precio_costo / (1 - margen_deseado/100)`
- Ejemplo: Costo $1.614, margen 60% → Precio $4.035

### Facturación
- Numeración secuencial por tenant: `{prefijo}-{numero}`
- Estados: borrador → emitida → pagada/anulada
- Al emitir factura:
  1. Generar PDF (ReportLab) → Subir a S3
  2. Guardar `url_pdf` en DB
  3. Crear movimientos_stock `tipo=salida` por cada detalle
  4. Crear asiento contable automático
- Al anular: Reversar movimientos stock + crear asiento de anulación

### Cotizaciones
- Numeración secuencial independiente: `COT-{numero}`
- Estados: borrador → enviada → aceptada/rechazada/convertida
- NO afecta inventario hasta convertir a factura
- Al convertir a factura:
  1. Crear factura (estado=borrador) con datos de cotización
  2. Actualizar cotización (estado=convertida, factura_id=nueva_factura)
  3. Generar PDF factura
- Validez: `fecha_vencimiento` define vigencia de precios

### Suscripciones SaaS (Wompi)
- Cada tenant tiene 1 suscripción activa
- Estados: activa → suspendida/cancelada/vencida
- Flujo pago:
  1. Usuario selecciona plan
  2. Redirect a Wompi checkout (API)
  3. Wompi callback → Webhook `/api/webhooks/wompi`
  4. Crear registro `pagos_suscripcion` (estado=aprobado)
  5. Actualizar `suscripciones.fecha_proximo_pago` (+30 días)
  6. Si pago falla 3 veces → Suspender tenant
- Renovación automática: Cron job verifica `fecha_proximo_pago` cada día

### Inventario
- Movimientos trazables: cada entrada/salida con referencia
- Valorización: Stock × Costo Promedio Ponderado
- Alertas: Si `stock < alerta_stock_min` → Notificar dashboard

### Contabilidad
- PUC Colombia pre-cargado (~40 cuentas esenciales)
- Asientos balanceados: `SUM(debe) = SUM(haber)` (validación crítica)
- Asientos automáticos en:
  - Venta: DEBE 1105 (Caja), HABER 4135 (Ventas) + 2408 (IVA)
  - Producción: DEBE 1435 (Inventario PT), HABER 1430 (Inventario MP)
- Cierre mensual: Generar asientos de cierre (manual o automático)

### CRM
- Cliente genérico pre-creado: "Cliente Mostrador" (nit: 222222222222)
- NIT único por tenant
- `retencion_iva = true` → No cobrar IVA en facturas

## FLUJOS CRÍTICOS

### 1. Registro Tenant
```
POST /api/tenants
├── Validar plan_id existe
├── Crear tenant (estado=activo)
├── Crear usuario admin
├── Crear registro usuarios_tenants (rol=admin)
├── Crear configuracion_tenant (defaults)
├── Crear cliente genérico "Mostrador"
├── Enviar email bienvenida (Celery async)
└── Return { tenant_id, usuario_id, token_acceso }
```

### 2. Login Multi-Tenant
```
POST /api/autenticacion/login
├── Validar email + password (bcrypt)
├── Buscar tenants del usuario (usuarios_tenants)
├── Generar JWT (exp 1h) + Refresh token (exp 7d)
└── Return { token_acceso, token_refresco, tenants: [{ id, nombre, rol }] }

Headers posteriores:
├── Authorization: Bearer <token_acceso>
└── X-Tenant-ID: <tenant_seleccionado>
```

### 3. Crear Producto con Receta
```
POST /api/productos
├── Crear producto (tipo=producto_terminado)
└── Return producto_id

POST /api/recetas
├── Body: { producto_id, rendimiento, detalles: [{ materia_prima_id, cantidad, unidad }] }
├── Validar producto es producto_terminado
├── Validar materias primas existen y son materia_prima
├── Crear receta + recetas_detalles
└── Return receta_id
```

### 4. Producir Velas (Aplicar Receta)
```
POST /api/recetas/{id}/producir
├── Body: { cantidad_producir: 50 }
├── Obtener receta con detalles
├── FOR EACH materia_prima:
│   ├── cantidad_necesaria = detalle.cantidad × cantidad_producir
│   ├── Validar stock >= cantidad_necesaria
│   └── Crear movimiento_stock (tipo=salida, cantidad=-cantidad_necesaria)
├── Crear movimiento_stock (tipo=produccion, cantidad=+cantidad_producir × rendimiento)
├── Actualizar productos.stock (atomic update)
└── Return { movimientos_creados, stock_actualizado }
```

### 5. Emitir Factura
```
POST /api/facturas
├── Body: { cliente_id, detalles: [{ producto_id, cantidad, precio_unitario }] }
├── Validar stock disponible para cada producto
├── Calcular subtotal, IVA, total
├── Crear factura (estado=borrador)
├── Crear facturas_detalles
├── Generar número secuencial (atomic increment)
└── Return factura_id

POST /api/facturas/{id}/emitir
├── Validar estado=borrador
├── FOR EACH detalle:
│   └── Crear movimiento_stock (tipo=salida, id_referencia=factura_id)
├── Actualizar productos.stock (atomic)
├── Generar PDF (ReportLab) → bytes
├── Subir PDF a S3 → url_pdf
├── Actualizar factura (estado=emitida, url_pdf)
├── Crear asiento contable automático
└── Return { factura, url_pdf }
```

### 6. Asiento Contable Venta
```python
# Al emitir factura
def crear_asiento_venta(factura):
    asiento = AsientoContable(
        tipo_origen='factura',
        id_referencia=factura.id,
        fecha=factura.fecha_emision
    )
    
    # DEBE Caja
    AsientoDetalle(
        cuenta_puc_id='1105',  # Caja
        debe=factura.total,
        descripcion=f"Venta según {factura.numero}"
    )
    
    # HABER Ventas
    AsientoDetalle(
        cuenta_puc_id='4135',  # Comercio al por mayor/menor
        haber=factura.subtotal,
        descripcion=f"Venta según {factura.numero}"
    )
    
    # HABER IVA por pagar
    if factura.total_iva > 0:
        AsientoDetalle(
            cuenta_puc_id='2408',  # IVA por pagar
            haber=factura.total_iva,
            descripcion=f"IVA venta {factura.numero}"
        )
    
    # Validar balance
    assert sum(debe) == sum(haber)
    guardar(asiento)
```

### 7. Convertir Cotización a Factura
```
POST /api/cotizaciones/{id}/convertir
├── Validar cotización estado=enviada o aceptada
├── Crear factura (estado=borrador) con:
│   ├── cliente_id = cotizacion.cliente_id
│   ├── fecha_emision = hoy
│   ├── Copiar todos los detalles
│   └── Generar nuevo número factura
├── Actualizar cotizacion:
│   ├── estado = convertida
│   └── factura_id = nueva_factura.id
└── Return { factura_id, numero_factura }
```

### 8. Webhook Wompi (Pago Suscripción)
```
POST /api/webhooks/wompi
├── Validar signature Wompi (HMAC)
├── Body: { event: "transaction.updated", data: { id, status, amount, reference } }
├── Buscar suscripcion por reference
├── IF status == "APPROVED":
│   ├── Crear pago_suscripcion (estado=aprobado)
│   ├── Actualizar suscripcion:
│   │   ├── estado = activa
│   │   ├── fecha_proximo_pago = fecha_pago + 30 días
│   │   └── referencia_pago = transaction_id
│   └── Enviar email confirmación (Celery)
├── IF status == "DECLINED":
│   ├── Crear pago_suscripcion (estado=rechazado)
│   ├── Incrementar contador_fallos
│   └── IF contador_fallos >= 3:
│       └── Suspender tenant
└── Return 200 OK
```

## DISEÑO FRONTEND

### Sistema de Diseño

#### Paleta de Colores
```
Primarios:
- Brand Primary: #EC4899 (Rosa - aromático/femenino)
- Brand Secondary: #8B5CF6 (Violeta - representa velas/místico)
- Success: #10B981 (Verde - confirmaciones)
- Warning: #F59E0B (Ámbar - alertas stock)
- Error: #EF4444 (Rojo - errores/anulaciones)
- Info: #3B82F6 (Azul - informativo)

Neutrales:
- Gray 50-900 (Tailwind scale)
- Backgrounds: white, gray-50, gray-100
- Text: gray-900 (primario), gray-600 (secundario), gray-400 (disabled)

Estados:
- Hover: primario -10% luminosidad
- Active: primario -20% luminosidad
- Disabled: gray-300
- Focus: ring-2 ring-primary ring-offset-2
```

#### Tipografía
```
Font Family: Inter (sistema), fallback: system-ui, sans-serif
Escalas:
- Display: 32px / 2rem (bold) - Títulos principales
- H1: 24px / 1.5rem (semibold) - Títulos sección
- H2: 20px / 1.25rem (semibold) - Subtítulos
- H3: 18px / 1.125rem (medium) - Cards headers
- Body: 16px / 1rem (regular) - Texto base
- Small: 14px / 0.875rem (regular) - Labels, hints
- Tiny: 12px / 0.75rem (medium) - Badges, timestamps

Line Height:
- Headings: 1.2
- Body: 1.5
- Condensed: 1.3 (tablas, listas densas)
```

#### Espaciado
```
Sistema 4px base:
- xs: 4px (0.25rem)
- sm: 8px (0.5rem)
- md: 16px (1rem)
- lg: 24px (1.5rem)
- xl: 32px (2rem)
- 2xl: 48px (3rem)
- 3xl: 64px (4rem)

Aplicación:
- Padding cards: lg (24px)
- Margin entre secciones: xl (32px)
- Gap lists: md (16px)
- Buttons padding: sm horizontal, xs vertical (8px/4px)
```

#### Bordes y Sombras
```
Border Radius:
- sm: 4px (inputs, badges)
- md: 8px (cards, buttons)
- lg: 12px (modales, dropdowns)
- full: 9999px (avatars, pills)

Shadows:
- sm: 0 1px 2px rgba(0,0,0,0.05) - Cards hover
- md: 0 4px 6px rgba(0,0,0,0.07) - Dropdowns
- lg: 0 10px 15px rgba(0,0,0,0.1) - Modales
- xl: 0 20px 25px rgba(0,0,0,0.15) - Overlays
```

### Responsive Breakpoints
```
Mobile: 320px - 767px (diseño base, 1 columna)
Tablet: 768px - 1023px (2 columnas, sidebar colapsable)
Desktop: 1024px - 1439px (sidebar fijo, 3 columnas)
Wide: 1440px+ (máximo 1600px contenedor)

Touch Targets Mobile:
- Mínimo: 44×44px (Apple HIG)
- Óptimo: 48×48px
- Spacing entre targets: 8px mínimo
```

### Arquitectura de Información

#### Navegación Principal (Desktop)
```
Sidebar izquierdo (240px ancho):
├── Logo + Tenant selector (dropdown)
├── Búsqueda global (⌘K)
├── Secciones:
│   ├── 📊 Dashboard
│   ├── 🛒 Ventas
│   │   ├── POS
│   │   ├── Facturas
│   │   ├── Cotizaciones
│   │   └── Clientes
│   ├── 📦 Inventario
│   │   ├── Productos
│   │   ├── Recetas
│   │   ├── Movimientos
│   │   |── Alertas Stock
|   |   └── Proveedores
│   ├── 💰 Contabilidad
│   │   ├── Asientos
│   │   ├── PUC
│   │   └── Reportes / Estados financieros
│   └── ⚙️ Configuración
│       ├── Empresa
│       ├── Usuarios
│       └── Suscripción
└── User menu (bottom)
    ├── Avatar + nombre
    ├── Configuración cuenta
    └── Cerrar sesión

Estados Sidebar:
- Expanded (default desktop): Íconos + labels
- Collapsed (tablet): Solo íconos, tooltip on hover
- Mobile: Hamburger menu, overlay full-screen
```

#### Navegación Mobile
```
Bottom Tab Bar (60px altura):
├── 🏠 Inicio (Dashboard)
├── 💰 Vender (POS directo)
├── 📦 Productos
└── ⚙️ Más (resto menú)

Header Top:
├── Hamburger menu (sidebar full)
├── Título página
└── Actions contextuales (3-dot menu)
```

### Páginas Clave - Layouts

#### 1. Dashboard (Vista General)
```
Layout Desktop (3 columnas):
┌─────────────────────────────────────────────┐
│ Header: "Dashboard" + selector período      │
├─────────────┬─────────────┬─────────────────┤
│ KPI Card    │ KPI Card    │ KPI Card        │
│ Ventas Hoy  │ Stock Bajo  │ Pendientes Cobro│
│ $X.XXX.XXX  │ 12 items    │ $XXX.XXX        │
│ +XX% vs ayer│ ⚠️ Crítico  │ 5 facturas      │
├─────────────┴─────────────┴─────────────────┤
│ Gráfico: Ventas últimos 7 días (line chart) │
│ Interactivo, tooltips, leyenda              │
├──────────────────────┬──────────────────────┤
│ Top 5 Productos      │ Últimas Ventas       │
│ • Vela Lavanda $XXX  │ #FAC-001 $XXX (hoy)  │
│ • Vela Vainilla $XXX │ #FAC-002 $XXX (hoy)  │
│ (Lista + mini spark) │ (Ver todas →)        │
└──────────────────────┴──────────────────────┘

Mobile (Stack vertical):
- KPIs: Horizontal scroll cards
- Gráfico: Full width, touch pan/zoom
- Listas: Colapsadas, "Ver más" expandible
```

#### 2. POS (Punto de Venta)
```
Layout Desktop (2 paneles):
┌──────────────────┬─────────────────────┐
│ Productos        │ Carrito             │
│ [🔍 Buscar...]   │ Cliente: [Select ▼] │
│                  │                     │
│ Grid 3×N:        │ Items:              │
│ ┌──────┐┌──────┐ │ • Vela Lavanda      │
│ │ IMG  ││ IMG  │ │   2× $10k = $20k    │
│ │Vela 1││Vela 2│ │   [−] [2] [+] [🗑️] │
│ │$10k  ││$12k  │ │                     │
│ └──────┘└──────┘ │ • Vela Vainilla     │
│ (Click agregar)  │   1× $12k = $12k    │
│                  │   [−] [1] [+] [🗑️] │
│ Categorías tabs  │                     │
│ [Todas][Aromas]  │ ─────────────────── │
│                  │ Subtotal:    $32k   │
│                  │ IVA (19%):   $6.1k  │
│                  │ TOTAL:       $38.1k │
│                  │                     │
│                  │ [💰 COBRAR]         │
│                  │ (Primary, grande)   │
└──────────────────┴─────────────────────┘

Mobile (Tabs):
- Tab 1: Productos grid (2 columnas)
- Tab 2: Carrito full-screen
- FAB "Ver carrito" badge contador
- Modal Cobrar: Full-screen, steps
```

#### 3. Facturas (Lista)
```
Layout Desktop:
┌─────────────────────────────────────────────┐
│ Header: "Facturas" + [➕ Nueva Factura]     │
│ Filtros: [Estado ▼][Cliente ▼][Fecha 📅]   │
├─────────────────────────────────────────────┤
│ Tabla responsive:                           │
│ ┌───────┬──────────┬─────────┬─────┬─────┐ │
│ │Número │Cliente   │Fecha    │Total│Est. │ │
│ ├───────┼──────────┼─────────┼─────┼─────┤ │
│ │FAC-001│María Gómez│12 Feb  │$38k │Emitida│
│ │FAC-002│Juan Díaz  │11 Feb  │$50k │Pagada │
│ │ (Click fila → Ver detalle factura)      │ │
│ └───────┴──────────┴─────────┴─────┴─────┘ │
│                                             │
│ Paginación: ← 1 [2] 3 ... 10 →             │
└─────────────────────────────────────────────┘

Estados visuales:
- Borrador: badge gray
- Emitida: badge blue
- Pagada: badge green
- Anulada: badge red + strikethrough

Mobile:
- Cards verticales (no tabla)
- Swipe actions: Ver / Compartir / Anular
- Infinite scroll
```

#### 4. Productos (Lista + Editor)
```
Layout Desktop:
┌──────────────────┬─────────────────────┐
│ Lista Productos  │ Editor Producto     │
│ [🔍 Buscar]      │ (Panel derecho)     │
│ [➕ Nuevo]       │                     │
│                  │ [Foto producto]     │
│ Cards list:      │ 📷 Upload           │
│ ┌──────────────┐ │                     │
│ │🕯️ Vela Lavan │ │ Nombre: [Input]     │
│ │SKU: VEL-001  │ │ SKU: [Input]        │
│ │Stock: 45 uds │ │ Categoría: [Select] │
│ │$10.000       │ │ Tipo: [Radio]       │
│ │[Editar][...]│ │ ○ Producto terminado│
│ └──────────────┘ │ ○ Materia prima     │
│                  │                     │
│ (Selected state) │ Costo: $[Input]     │
│                  │ Precio: $[Input]    │
│ Filtros sidebar: │ IVA: [Select %]     │
│ □ Stock bajo     │ Stock: [Number]     │
│ □ Sin stock      │ Alerta mín: [Number]│
│ □ Solo MP        │                     │
│                  │ ┌─────────────────┐ │
│                  │ │💡 Margen: 60%   │ │
│                  │ │Sugerido: $4.035 │ │
│                  │ └─────────────────┘ │
│                  │ (Calculadora auto)  │
│                  │                     │
│                  │ [Guardar][Cancelar] │
└──────────────────┴─────────────────────┘

Mobile:
- Lista full-screen
- Editor: Modal full-screen
- Formulario: Stack vertical, steps si complejo
```

#### 5. Recetas (BOM)
```
Layout Desktop:
┌─────────────────────────────────────────────┐
│ "Receta: Vela Aromática Lavanda 200g"      │
│ Producto final: [Select ▼] Rendimiento: [1]│
├─────────────────────────────────────────────┤
│ Materias Primas:                            │
│ ┌─────────────────────────────────────────┐ │
│ │ • Cera soya vegetal                     │ │
│ │   Cantidad: [180] [g ▼]                 │ │
│ │   Stock disponible: 5.2 kg ✓            │ │
│ │   [🗑️ Eliminar]                         │ │
│ ├─────────────────────────────────────────┤ │
│ │ • Fragancia lavanda                     │ │
│ │   Cantidad: [18] [ml ▼]                 │ │
│ │   Stock disponible: 850 ml ✓            │ │
│ │   [🗑️ Eliminar]                         │ │
│ ├─────────────────────────────────────────┤ │
│ │ + Agregar materia prima                 │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ 📊 Simulador Producción                 │ │
│ │ Producir: [50] unidades                 │ │
│ │                                         │ │
│ │ Necesitas:                              │ │
│ │ • Cera soya: 9.0 kg (Disponible: 5.2)  │ │
│ │   ⚠️ FALTAN 3.8 kg                      │ │
│ │ • Fragancia: 900 ml (Disponible: 850)  │ │
│ │   ⚠️ FALTAN 50 ml                       │ │
│ │                                         │ │
│ │ [❌ Stock insuficiente]                 │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ [💾 Guardar Receta] [🏭 Producir Ahora]   │
└─────────────────────────────────────────────┘

Estados:
- Verde: Stock OK
- Amarillo: Stock justo (<20%)
- Rojo: Stock insuficiente
```

### Componentes Reutilizables

#### KPI Card
```
Estructura:
┌─────────────────────┐
│ 📊 Título KPI       │
│ $1,234,567          │ (Display, bold)
│ +15.3% vs período   │ (Small, color estado)
│ ▲ Mini sparkline    │ (Opcional)
└─────────────────────┘

Estados:
- Positivo: texto green-600, ▲ icon
- Negativo: texto red-600, ▼ icon
- Neutral: texto gray-600, ─ icon

Interacción:
- Hover: elevate shadow
- Click: Drill-down modal/página
```

#### Tabla Responsive
```
Desktop: Tabla HTML estándar
- Zebra striping (alternate gray-50)
- Hover row: bg-primary-50
- Sticky header (scroll vertical)
- Sort columns: Click header, icon ↕
- Actions: 3-dot menu última columna

Tablet: Tabla compacta
- Columnas prioritarias visibles
- Resto: Expandible row on click

Mobile: Card list
- Cada row = Card
- Layout: Flex vertical
- Swipe actions: Actions drawer
```

#### Modal Pattern
```
Backdrop: rgba(0,0,0,0.5)
Container: 
- Desktop: max-width 600px, centrado
- Mobile: Full-screen
- Padding: lg (24px)
- Border radius: lg (12px desktop)

Header:
- Título (H2)
- Close button (×) top-right

Body:
- Content scrollable
- Max height: 80vh

Footer:
- Actions right-aligned
- [Cancelar (secondary)] [Confirmar (primary)]
```

#### Toast Notifications
```
Posición: Top-right desktop, bottom mobile
Duración: 3s (success/info), 5s (warning/error)
Dismissible: ✕ button

Variantes:
- Success: green bg, checkmark icon
- Error: red bg, alert icon
- Warning: amber bg, warning icon
- Info: blue bg, info icon

Animación:
- Enter: slide-in + fade
- Exit: fade-out
```

### Interacciones y Estados

#### Loading States
```
Skeleton Screens:
- Tablas: Animated pulse bars
- Cards: Gray blocks pulsing
- Botones: Spinner + disabled state
- Imágenes: Placeholder gradient

Progressive Loading:
- Dashboard: KPIs primero, luego gráficos
- Listas: Visible items, lazy load más
```

#### Empty States
```
Ilustración + mensaje + CTA:

"Sin productos aún"
[Ilustración vela apagada]
"Crea tu primer producto para empezar"
[➕ Crear Producto]

"Sin facturas este mes"
[Ilustración calendario vacío]
"Emite tu primera factura"
[➕ Nueva Factura]
```

#### Error States
```
Inline Errors (Forms):
- Borde input: red
- Mensaje bajo input: red-600, small
- Icon: ⚠️ left del mensaje

Page Errors (500, 404):
- Centrado, ilustración amigable
- Mensaje error técnico: Colapsable
- [🏠 Ir al Dashboard]

Network Errors:
- Toast: "Sin conexión, reintentando..."
- Badge offline: Header superior
```

#### Form Validation
```
Real-time:
- onBlur para emails, NITs
- onChange para passwords (strength)
- Debounce 300ms en búsquedas

Visual Feedback:
- Valid: green checkmark right input
- Invalid: red ⚠️ + mensaje
- Required: asterisco * label
- Optional: "(opcional)" texto gray

Submit:
- Disabled hasta form válido
- Loading spinner en botón
- Scroll to first error si falla
```

### Micro-animaciones
```
Hover Buttons:
- Transform: translateY(-1px)
- Shadow: Increase
- Duration: 150ms ease-out

Click/Active:
- Transform: scale(0.98)
- Duration: 100ms

Page Transitions:
- Fade + slide-up: 200ms
- Cambio tabs: Fade: 150ms

Number Counters (KPIs):
- CountUp animation: 1s ease
- Trigger: On viewport enter

Loading Spinners:
- Rotate: 360deg infinite
- Duration: 1s linear
```

### Temas y Branding

#### Identidad Visual
```
Logo: Vela estilizada + "Chandelier"
- Versión completa: Sidebar
- Isotipo: Favicon, mobile collapsed

Ilustraciones:
- Estilo: Flat, colores suaves
- Uso: Empty states, onboarding, errores
- Paleta: Mismo brand colors

Iconografía:
- Librería: Heroicons (outline + solid)
- Tamaño: 20px (inline), 24px (standalone)
- Color: Hereda texto o custom
```

#### Dark Mode (Fase 2)
```
Preparar CSS variables:
--bg-primary: white / gray-900
--text-primary: gray-900 / gray-100
--border: gray-200 / gray-700

Toggle: User menu
Persistencia: localStorage
```

## RESTRICCIONES TÉCNICAS

### Performance
- Queries con tenant_id en WHERE siempre (RLS es safety net, no performance)
- Índices compuestos: `(tenant_id, campo_consulta_frecuente)`
- N+1 queries: Usar eager loading (SQLAlchemy `joinedload`, `selectinload`)
- Paginación obligatoria: `?page=1&limit=50` (max 100)

### Seguridad
- Passwords: bcrypt rounds=12
- JWT: HS256, secret rotable, exp 1h
- Rate limiting: 100 req/min por IP (slowapi)
- CORS: Whitelist origins específicos
- SQL Injection: Siempre usar ORM, nunca raw SQL con f-strings
- XSS: Sanitizar inputs en frontend

### Storage
- S3/R2 buckets:
  - `chandelier-logos` (público-read)
  - `chandelier-facturas` (privado, presigned URLs 24h)
- Naming: `{tenant_id}/{tipo}/{uuid}.{ext}`
- Max upload: 2MB logos, 5MB PDFs

### Validaciones
- Soft deletes: `deleted_at TIMESTAMP NULL`, nunca `DELETE FROM`
- Atomic updates: `UPDATE ... SET stock = stock + $1 WHERE id = $2`
- Transacciones: Wrap operaciones multi-tabla en `async with session.begin()`
- Constraints DB: `CHECK (stock >= 0)`, `UNIQUE (tenant_id, sku)`

## CONVENCIONES

### Código
- Python: PEP 8, type hints obligatorios
- TypeScript: strict mode, no `any`
- Nombres archivos: snake_case (Python), camelCase (TS)
- Commits: Conventional Commits (`feat:`, `fix:`, `refactor:`)

### API
- Endpoints: `/api/v1/{recurso}`
- Métodos: GET (list), POST (create), PUT (update), DELETE (soft delete)
- Responses: `{ data: {...}, error: null }` o `{ data: null, error: "mensaje" }`
- HTTP codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Error

### Base Datos
- Tablas: plural, snake_case (`productos`, `facturas_detalles`)
- Columnas: snake_case (`fecha_emision`, `precio_unitario`)
- PKs: UUID v4 siempre
- Timestamps: `creado_en`, `actualizado_en` (auto-managed)
- Soft deletes: `deleted_at TIMESTAMP NULL DEFAULT NULL`

## SUPUESTOS

- Tenants son microempresas (1-5 usuarios, <1000 facturas/mes)
- Usuarios tienen conexión internet estable (no offline mode en MVP)
- Impresoras térmicas no requeridas en MVP (PDF descargable)
- Facturas sin firma digital DIAN suficiente para MVP
- Storage S3 compatible (AWS S3, Cloudflare R2, DigitalOcean Spaces)
- Emails transaccionales: SMTP genérico (SendGrid, Mailgun, SES)
- Reportes avanzados incluyen:
  - Rentabilidad por producto/categoría/período
  - Análisis ABC inventario
  - Proyección flujo caja
  - Comparativas período (MoM, YoY)
  - Top clientes por ventas
  - Análisis márgenes por línea producto

## NO-OBJETIVOS MVP

- Facturación electrónica DIAN (Fase 2)
- Multi-moneda
- Multi-idioma
- Inventario por ubicación/bodega
- Códigos de barras
- Integración contable externa (Siigo, Alegra)
- App móvil nativa
- Modo offline/PWA
- Nómina
- Reportes personalizables
- Exportación masiva (solo Excel básico)