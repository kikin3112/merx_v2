# Procedimiento: Crear Tenant en Producción

## Importante

**El proyecto está en producción.** Todas las operaciones contra la base de datos deben ejecutarse en Railway, NO en local.

## Conexión a Producción

### Backend URL
```
https://backend-production-14545.up.railway.app
```

### Railway CLI
```bash
# Verificar conexión
railway status
# Project: merx-backend
# Environment: production
# Service: backend

# Ver logs
railway logs --lines 50

# Ejecutar comando en contenedor
railway ssh -s backend -e production "comando"

# Variables de entorno
railway variables
```

### Base de Datos
```
Host: postgres.railway.internal (interno)
Port: 5432
Database: railway
```

---

## Método 1: Crear Tenant via SSH + Python

### Paso 1: Crear el tenant, usuario admin y configuración base

```bash
railway ssh -s backend -e production "cd /app && python -c \"
import sys
sys.stdout.reconfigure(encoding='utf-8')

from backend.app.datos.db import SessionLocal
from backend.app.datos.modelos_tenant import Tenants, Planes, UsuariosTenants, Suscripciones
from backend.app.datos.modelos import Usuarios, Terceros, Secuencias
from backend.app.utils.seguridad import hash_password
from datetime import datetime, timezone, timedelta

db = SessionLocal()

# DATOS DEL NUEVO TENANT
TENANT_DATA = {
    'nombre': 'Nombre Empresa',
    'slug': 'nombre-empresa',  # URL-friendly, sin espacios
    'nit': '123456789',        # O None si no tiene
    'email_contacto': 'contacto@empresa.com',
    'telefono': '3001234567',
    'direccion': 'Dirección de la empresa',
}

ADMIN_DATA = {
    'nombre': 'Admin Empresa',
    'email': 'admin@empresa.com',
    'password': 'password123',  # Usuario debe cambiar después
}

# Verificar si ya existe
existing = db.query(Tenants).filter(Tenants.slug == TENANT_DATA['slug']).first()
if existing:
    print(f'ERROR: Tenant ya existe: {existing.nombre}')
    db.close()
    sys.exit(1)

# Obtener plan default
plan = db.query(Planes).filter(Planes.es_default == True).first() or db.query(Planes).first()

# Crear tenant
tenant = Tenants(
    nombre=TENANT_DATA['nombre'],
    slug=TENANT_DATA['slug'],
    nit=TENANT_DATA.get('nit'),
    email_contacto=TENANT_DATA['email_contacto'],
    telefono=TENANT_DATA.get('telefono'),
    direccion=TENANT_DATA.get('direccion'),
    plan_id=plan.id,
    estado='activo',
    fecha_inicio_suscripcion=datetime.now(timezone.utc),
    fecha_fin_suscripcion=datetime.now(timezone.utc) + timedelta(days=365),
)
db.add(tenant)
db.flush()
print(f'Tenant creado: {tenant.nombre} (ID: {tenant.id})')

# Crear usuario admin
admin = Usuarios(
    nombre=ADMIN_DATA['nombre'],
    email=ADMIN_DATA['email'],
    password_hash=hash_password(ADMIN_DATA['password']),
    rol='admin',
    estado=True,
    es_superadmin=False,
)
db.add(admin)
db.flush()
print(f'Usuario creado: {admin.email}')

# Relacionar admin con tenant
rel = UsuariosTenants(
    usuario_id=admin.id,
    tenant_id=tenant.id,
    rol='admin',
    esta_activo=True,
    es_default=True,
)
db.add(rel)

# Crear suscripción
sub = Suscripciones(
    tenant_id=tenant.id,
    plan_id=plan.id,
    periodo_inicio=datetime.now(timezone.utc),
    periodo_fin=datetime.now(timezone.utc) + timedelta(days=365),
    estado='activo',
)
db.add(sub)

# Crear cliente mostrador
cliente = Terceros(
    tenant_id=tenant.id,
    tipo_documento='NIT',
    numero_documento='222222222222',
    nombre='CLIENTE MOSTRADOR',
    tipo_tercero='CLIENTE',
    email='mostrador@empresa.com',
    estado=True,
)
db.add(cliente)

# Crear secuencias
secuencias = [
    {'nombre': 'COMPRAS', 'prefijo': 'CMP-', 'siguiente_numero': 1, 'longitud_numero': 6},
    {'nombre': 'COTIZACIONES', 'prefijo': 'COT-', 'siguiente_numero': 1, 'longitud_numero': 6},
    {'nombre': 'ORDENES_PRODUCCION', 'prefijo': 'OP-', 'siguiente_numero': 1, 'longitud_numero': 6},
    {'nombre': 'ASIENTOS', 'prefijo': 'ASI-', 'siguiente_numero': 1, 'longitud_numero': 6},
    {'nombre': 'FACTURAS', 'prefijo': 'FAC-', 'siguiente_numero': 1, 'longitud_numero': 6},
]
for seq_data in secuencias:
    seq = Secuencias(tenant_id=tenant.id, **seq_data)
    db.add(seq)

db.commit()
print('TENANT CREADO EXITOSAMENTE')
print(f'Tenant ID: {tenant.id}')
print(f'Admin Email: {ADMIN_DATA[\"email\"]}')
print(f'Admin Password: {ADMIN_DATA[\"password\"]}')
db.close()
\""
```

---

## Método 2: Importar Productos desde CSV

### Paso 1: Preparar el CSV

Formato requerido:
```csv
Codigo;Producto;Categoria;Costo;Precio venta;Stock actual
P001;PRODUCTO EJEMPLO 50 GR;ESENCIAS;10000;15000;5
```

### Paso 2: Mapeo de categorías

| Categoría CSV | Sistema |
|---------------|---------|
| ESENCIAS | Insumo |
| CERAS | Insumo |
| PABILOS | Insumo |
| ENVASES | Insumo |
| (otros) | Insumo |

### Paso 3: Script de importación

Subir el CSV a Railway y ejecutar:

```bash
# Si el archivo está en el repo (necesita redeploy)
railway ssh -s backend -e production "cd /app && python -m backend.app.utils.import_products /app/data/products.csv <tenant_slug>"

# O ejecutar inline para importaciones pequeñas
railway ssh -s backend -e production "cd /app && python -c \"
# ... código de importación ...
\""
```

---

## Método 3: Importar Clientes

```bash
railway ssh -s backend -e production "cd /app && python -c \"
import sys
sys.stdout.reconfigure(encoding='utf-8')

from backend.app.datos.db import SessionLocal
from backend.app.datos.modelos_tenant import Tenants
from backend.app.datos.modelos import Terceros

db = SessionLocal()

# Obtener tenant
tenant = db.query(Tenants).filter(Tenants.slug == 'tenant-slug').first()

# Datos de clientes
clientes = [
    {'nombre': 'Cliente 1', 'nit': '123456789', 'email': 'cliente1@email.com', 'telefono': '3001111111'},
    {'nombre': 'Cliente 2', 'nit': '987654321', 'email': 'cliente2@email.com', 'telefono': '3002222222'},
]

for c in clientes:
    cliente = Terceros(
        tenant_id=tenant.id,
        tipo_documento='NIT',
        numero_documento=c['nit'],
        nombre=c['nombre'],
        tipo_tercero='CLIENTE',
        email=c.get('email'),
        telefono=c.get('telefono'),
        estado=True,
    )
    db.add(cliente)

db.commit()
print(f'{len(clientes)} clientes importados')
db.close()
\""
```

---

## Método 4: Importar Proveedores

```bash
railway ssh -s backend -e production "cd /app && python -c \"
import sys
sys.stdout.reconfigure(encoding='utf-8')

from backend.app.datos.db import SessionLocal
from backend.app.datos.modelos_tenant import Tenants
from backend.app.datos.modelos import Terceros

db = SessionLocal()

tenant = db.query(Tenants).filter(Tenants.slug == 'tenant-slug').first()

proveedores = [
    {'nombre': 'Proveedor 1', 'nit': '111111111', 'email': 'prov1@email.com'},
]

for p in proveedores:
    prov = Terceros(
        tenant_id=tenant.id,
        tipo_documento='NIT',
        numero_documento=p['nit'],
        nombre=p['nombre'],
        tipo_tercero='PROVEEDOR',
        email=p.get('email'),
        estado=True,
    )
    db.add(prov)

db.commit()
print(f'{len(proveedores)} proveedores importados')
db.close()
\""
```

---

## Verificación

### Verificar tenant creado
```bash
railway ssh -s backend -e production "cd /app && python -c \"
from backend.app.datos.db import SessionLocal
from backend.app.datos.modelos_tenant import Tenants
from backend.app.datos.modelos import Usuarios

db = SessionLocal()
for t in db.query(Tenants).all():
    print(f'{t.nombre} | slug: {t.slug} | estado: {t.estado}')
db.close()
\""
```

### Verificar productos importados
```bash
railway ssh -s backend -e production "cd /app && python -c \"
from backend.app.datos.db import SessionLocal
from backend.app.datos.modelos_tenant import Tenants
from backend.app.datos.modelos import Productos

db = SessionLocal()
tenant = db.query(Tenants).filter(Tenants.slug == 'tenant-slug').first()
productos = db.query(Productos).filter(Productos.tenant_id == tenant.id).count()
print(f'Tenant: {tenant.nombre}')
print(f'Productos: {productos}')
db.close()
\""
```

### Probar login
```bash
curl -X POST https://backend-production-14545.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@empresa.com", "password": "password123"}'
```

---

## Tenants Actuales en Producción

| Tenant | Slug | Email Admin |
|--------|------|-------------|
| Velas Aromáticas Demo | velas-demo | admin@example.com |
| Luz De Luna | luz-de-luna | luzdelunavelas30@gmail.com |

---

## Notas Importantes

1. **Siempre usar Railway CLI** - Los cambios locales NO afectan producción
2. **Verificar antes de crear** - Usar `db.query(Tenants).filter(Tenants.slug == ...)` para evitar duplicados
3. **Passwords temporales** - El usuario debe cambiar su password después del primer login
4. **Commit de cambios** - Si se modifica código, hacer commit + push + `railway redeploy --yes`

---

*Última actualización: 2026-02-17*
