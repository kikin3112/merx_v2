# Domain Pitfalls: Tenant Onboarding + Data Import + DB Reset

**Domain:** SaaS multi-tenant ERP/POS with Excel data import and onboarding wizard
**Researched:** 2026-02-15
**Confidence:** MEDIUM (based on training data and project context analysis)

## Executive Summary

Data import and tenant onboarding projects for multi-tenant systems face critical pitfalls around **RLS context management during bulk operations**, **Excel encoding/parsing edge cases**, **accounting precision errors**, and **wizard UX abandonment**. The combination of PostgreSQL RLS + async operations + file uploads + progressive wizards creates unique failure modes not present in single-tenant or simpler systems.

Most dangerous: **Silent data corruption** when RLS context is lost during bulk inserts, leading to cross-tenant data leakage or orphaned records. Second: **Irreversible cost calculation errors** when importing inventory with weighted average costing.

---

## CRITICAL PITFALLS

### Pitfall 1: RLS Context Loss During Bulk Operations

**What goes wrong:**
When using bulk insert operations (SQLAlchemy `bulk_insert_mappings`, raw SQL COPY, or even batched inserts), the PostgreSQL session variable `app.tenant_id_actual` may not be set, causing RLS policies to fail silently. Records get inserted without `tenant_id` or with wrong `tenant_id`, creating orphaned data or cross-tenant leakage.

**Why it happens:**
- Async operations spawn new database connections from the pool
- Each connection needs `SET LOCAL app.tenant_id_actual` at transaction start
- Bulk operations often bypass ORM event hooks that would normally set context
- Transaction retries after deadlock may lose context
- Celery background tasks don't inherit the original request context

**Consequences:**
- **Data corruption:** Products, clients, invoices assigned to wrong tenant
- **Security breach:** Cross-tenant data access
- **Audit nightmare:** No trace of which import created orphaned records
- **Production incident:** Requires manual data surgery to fix

**Prevention:**

1. **Explicit context setting in every transaction:**
```python
# backend/app/services/import_service.py
async def import_productos_bulk(tenant_id: UUID, rows: List[dict]):
    async with db.begin():  # New transaction
        # CRITICAL: Set context FIRST, before any query
        await db.execute(
            text("SET LOCAL app.tenant_id_actual = :tenant_id"),
            {"tenant_id": str(tenant_id)}
        )

        # Verify context was set (fail fast)
        result = await db.execute(text("SELECT current_setting('app.tenant_id_actual', true)"))
        assert result.scalar() == str(tenant_id), "RLS context not set!"

        # Now safe to bulk insert
        # ...
```

2. **Use ORM for imports, not raw SQL:**
Avoid `COPY FROM` or raw `INSERT` statements. Use SQLAlchemy's `add_all()` with explicit `tenant_id` on each model instance. Slower but safer.

3. **Transaction wrapper with context validation:**
```python
from functools import wraps

def with_tenant_context(func):
    @wraps(func)
    async def wrapper(tenant_id: UUID, *args, **kwargs):
        async with db.begin() as trans:
            await db.execute(text("SET LOCAL app.tenant_id_actual = :tid"), {"tid": str(tenant_id)})
            # Verify
            check = await db.execute(text("SELECT current_setting('app.tenant_id_actual', true)"))
            if check.scalar() != str(tenant_id):
                raise RuntimeError(f"RLS context mismatch for {tenant_id}")
            return await func(tenant_id, *args, **kwargs)
    return wrapper
```

4. **Test with RLS enforced:**
Test user should NOT be superuser. Superusers bypass RLS, hiding context bugs.

**Detection:**
- Query `SELECT tenant_id, COUNT(*) FROM productos GROUP BY tenant_id` after import
- If `tenant_id IS NULL` or unexpected tenant_ids appear, context was lost
- Add DB constraint: `CHECK (tenant_id IS NOT NULL)` on all RLS tables
- Monitor Sentry for "RLS policy violation" errors

**Phase to address:** Phase 1 (DB Reset + Import Foundation)
This is the foundational issue. Must be solved before any import feature ships.

---

### Pitfall 2: Weighted Average Cost Corruption on Inventory Import

**What goes wrong:**
When importing historical inventory data, the system must recalculate `precio_costo` using weighted average: `(stock_actual × costo_actual + entrada × costo_nuevo) / (stock_actual + entrada)`. If imports are:
- Applied out of chronological order
- Missing intermediate transactions
- Using snapshot values instead of incremental movements

...the resulting costs will be permanently wrong, corrupting all future COGS calculations and financial reports.

**Why it happens:**
- Excel contains "current stock" snapshot, not movement history
- User imports "we have 100 candles at $5 each" but system expects "we received 100 at $5 on date X"
- Multiple imports (products, then inventory adjustment, then historical invoices) apply in wrong order
- Decimal precision loss: Excel stores floats, DB needs DECIMAL(14,2)

**Consequences:**
- **Incorrect profit margins:** COGS wrong → margin calculations wrong
- **Accounting mismatch:** Inventory valuation doesn't match PUC balance
- **Irreversible without re-import:** Can't recalculate after-the-fact without full movement history
- **Financial reports unusable:** Balance sheet, P&L, cost reports all corrupted

**Prevention:**

1. **Import as atomic transaction with chronological enforcement:**
```python
# Paso 4: Ajuste de inventario inicial
# NOT: "Set stock to 100 at cost $5"
# BUT: "Insert opening inventory movement dated BEFORE any sales"

import_date = datetime(2026, 1, 1)  # User selects "opening date"

for row in excel_inventario:
    # Create movement_stock entry
    movimiento = MovimientosStock(
        tenant_id=tenant_id,
        producto_id=row.producto_id,
        tipo='ajuste',  # Initial inventory adjustment
        cantidad=row.cantidad_inicial,
        costo_por_unidad=row.costo_unitario,
        fecha=import_date,  # MUST be before any historical invoices
        tipo_referencia='import_inicial',
        notas=f"Importación inicial desde Excel: {excel_filename}"
    )

    # Recalculate weighted average
    producto = await db.get(Productos, row.producto_id)
    if producto.stock == 0:
        # First entry, no averaging needed
        producto.precio_costo = row.costo_unitario
    else:
        # Weighted average formula
        total_value = (producto.stock * producto.precio_costo) + (row.cantidad_inicial * row.costo_unitario)
        total_qty = producto.stock + row.cantidad_inicial
        producto.precio_costo = Decimal(total_value / total_qty).quantize(Decimal('0.01'))

    producto.stock += row.cantidad_inicial
```

2. **Validate chronological consistency:**
If importing historical invoices (Step 6), ensure `fecha_emision >= import_date` from Step 4.

3. **Use DECIMAL, never float:**
```python
# Bad
precio_costo = float(excel_row['Costo'])  # Loses precision

# Good
from decimal import Decimal
precio_costo = Decimal(str(excel_row['Costo'])).quantize(Decimal('0.01'))
```

4. **Preview shows calculated cost:**
Before saving, show user:
```
Inventario Inicial:
- Parafina: 50 kg × $15.000 = $750.000
- Cera soya: 30 kg × $18.500 = $555.000

Total inventario valorizado: $1.305.000
¿Confirmar?
```

**Detection:**
- After import, run validation:
  ```sql
  SELECT p.sku, p.stock, p.precio_costo,
         SUM(m.cantidad * m.costo_por_unidad) / SUM(m.cantidad) as costo_calculado
  FROM productos p
  JOIN movimientos_stock m ON m.producto_id = p.id
  WHERE p.tenant_id = $1
  GROUP BY p.id
  HAVING ABS(p.precio_costo - costo_calculado) > 0.01
  ```
- Flag mismatches for manual review

**Phase to address:** Phase 2 (Import Features - Step 4 Inventory Adjustment)
Must implement before any inventory import feature.

---

### Pitfall 3: Database Reset Script Destroys RLS Policies

**What goes wrong:**
A naive DB reset script runs `DROP TABLE ... CASCADE` or `DELETE FROM *`, which:
- Drops RLS policies along with the tables
- Leaves tables in inconsistent state (some with RLS, some without)
- Requires manual re-creation of policies, easy to miss one table
- Breaks existing connections that have cached table schema

**Why it happens:**
- RLS policies are metadata attached to tables
- `DROP TABLE` removes policies
- `TRUNCATE` preserves policies but may cascade unexpectedly
- Copy-pasting production schema SQL may omit `CREATE POLICY` statements
- Developer forgets to re-run migration after reset

**Consequences:**
- **All tenants see each other's data:** RLS disabled but app assumes it's enforced
- **Silent security breach:** No errors, queries just return wrong data
- **Difficult to detect:** Unit tests with single tenant won't catch it

**Prevention:**

1. **Reset script preserves schema + policies:**
```sql
-- scripts/reset_db_for_production.sql

-- Step 1: Disable triggers temporarily
SET session_replication_role = 'replica';

-- Step 2: Delete data, NOT tables
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Exclude: planes, cuentas_puc, usuarios (superadmin), tenants (if preserving seed data)
    FOR r IN (
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename NOT IN ('planes', 'cuentas_puc', 'alembic_version')
    ) LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' RESTART IDENTITY CASCADE';
    END LOOP;
END $$;

-- Step 3: Re-enable triggers
SET session_replication_role = 'origin';

-- Step 4: Verify RLS policies still exist
SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public';
-- If count < expected, ERROR — policies were lost

-- Step 5: Preserve seed data
-- Re-insert planes
INSERT INTO planes (id, nombre, precio_mensual, max_usuarios, max_facturas_mes)
VALUES
    (uuid_generate_v4(), 'Básico', 50000, 2, 100),
    (uuid_generate_v4(), 'Profesional', 120000, 5, 500);

-- Re-insert PUC (40 cuentas)
-- ... (full seed data script)

-- Step 6: Preserve or recreate superadmin user
-- ...
```

2. **Use Alembic migrations, not manual SQL:**
If using `alembic downgrade base && alembic upgrade head`, policies are version-controlled.

3. **Automated policy verification:**
```python
# backend/app/utils/db_health_check.py
async def verify_rls_policies():
    result = await db.execute(text("""
        SELECT tablename FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('productos', 'facturas', 'clientes', 'movimientos_stock', ...)
    """))
    tables_with_rls_required = {row[0] for row in result}

    result = await db.execute(text("""
        SELECT DISTINCT tablename FROM pg_policies WHERE schemaname = 'public'
    """))
    tables_with_policies = {row[0] for row in result}

    missing = tables_with_rls_required - tables_with_policies
    if missing:
        raise RuntimeError(f"RLS policies missing on: {missing}")
```

4. **Run verification after reset:**
```bash
# Makefile
reset-db:
	docker-compose exec backend python scripts/reset_db.py
	docker-compose exec backend python scripts/verify_rls.py  # Fail if policies missing
	docker-compose exec backend python scripts/seed_data.py
```

**Detection:**
- Health check endpoint: `GET /health` → includes RLS policy count
- If policies drop from N to 0, alert
- Manual: `\d+ productos` in psql shows "Policies" section

**Phase to address:** Phase 1 (DB Reset Script)
Absolutely first thing to implement. One mistake here breaks all security.

---

### Pitfall 4: Excel Encoding Hell (Spanish Characters)

**What goes wrong:**
Colombian business names, addresses, product descriptions contain Spanish characters: ñ, á, é, í, ó, ú, ü. Excel files saved on Windows often use Latin-1 or Windows-1252 encoding, not UTF-8. When parsing server-side:
- Characters appear as mojibake: "Señora" → "SeÃ±ora"
- Database rejects non-UTF8 bytes: `ERROR: invalid byte sequence for encoding "UTF8"`
- User sees corrupted data, loses trust in system

**Why it happens:**
- Excel's "Save As CSV" defaults to ANSI (Windows-1252) on Windows
- `.xlsx` files are UTF-8 internally, but `openpyxl`/`pandas` may misdetect encoding
- User uploads file from old Excel version, system assumes UTF-8
- Server runs on Linux (UTF-8) but file was created on Windows (Windows-1252)

**Consequences:**
- **Data loss:** Invalid characters replaced with � or stripped
- **Validation errors:** NIT "García López" fails regex expecting ASCII
- **User frustration:** "Why can't your system handle Spanish?"
- **Support burden:** Manual data fixing

**Prevention:**

1. **Enforce UTF-8 in templates:**
```python
# When generating template Excel files
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.append(['SKU', 'Nombre', 'Descripción'])
ws.append(['VELA-001', 'Vela Aromática Lavanda', 'Cera de soya 100% natural'])

# Force UTF-8 encoding
wb.save('template_productos.xlsx')  # .xlsx is always UTF-8
```

Provide `.xlsx` templates, NOT `.csv`. CSV has ambiguous encoding.

2. **Detect and convert encoding on upload:**
```python
import chardet
from openpyxl import load_workbook

async def parse_excel_with_encoding_detection(file_bytes: bytes, file_extension: str):
    if file_extension == '.csv':
        # Detect encoding
        detection = chardet.detect(file_bytes)
        encoding = detection['encoding'] or 'utf-8'

        # Decode with detected encoding, re-encode to UTF-8
        try:
            text = file_bytes.decode(encoding)
        except UnicodeDecodeError:
            # Fallback to Windows-1252 (common for Colombian Excel)
            text = file_bytes.decode('windows-1252', errors='replace')

        # Parse CSV
        import csv
        rows = list(csv.DictReader(text.splitlines()))

    elif file_extension == '.xlsx':
        # openpyxl handles UTF-8 automatically
        wb = load_workbook(BytesIO(file_bytes))
        ws = wb.active
        rows = [dict(zip(ws[1], row)) for row in ws.iter_rows(min_row=2, values_only=True)]

    return rows
```

3. **UI warning for CSV uploads:**
```tsx
{fileExtension === '.csv' && (
  <Alert variant="warning">
    Los archivos CSV pueden tener problemas de codificación.
    Recomendamos usar formato .xlsx para evitar errores con caracteres especiales (ñ, á, é, etc.)
  </Alert>
)}
```

4. **Validation shows problematic characters:**
In preview, highlight any non-ASCII characters:
```
Producto: Vela Navideña Niño Dios
           ⚠️ Verificar carácter "ñ" se muestra correctamente
```

**Detection:**
- Unit test with sample data: "José María", "Señora López", "Año nuevo"
- If any appear corrupted in DB, encoding issue exists
- Monitor logs for `UnicodeDecodeError`

**Phase to address:** Phase 2 (Import Features - Preview validation)
Handle before any import goes live.

---

### Pitfall 5: NIT Check Digit Validation Missing

**What goes wrong:**
Colombian NITs (tax IDs) have a check digit algorithm. If importing client data without validation:
- User typos NIT: "901234567-3" but correct is "901234567-5"
- System accepts it, creates client
- Later, when generating official documents or integrating with DIAN (Fase 2), NIT is rejected
- All historical invoices now have invalid client NIT, can't be reported to tax authority

**Why it happens:**
- Developer unfamiliar with Colombian NIT format
- Validation seen as "nice to have", not critical
- Check digit algorithm not documented in requirements
- Excel has inconsistent formatting: some rows "901234567-5", others "901234567 5", others just "901234567"

**Consequences:**
- **Tax compliance risk:** Invoices with invalid NITs may be rejected by DIAN
- **Data cleanup nightmare:** Thousands of clients need NIT correction
- **Legal exposure:** Incorrect tax IDs on official documents

**Prevention:**

1. **Implement NIT validation with check digit:**
```python
def validar_nit_colombia(nit: str) -> tuple[bool, str]:
    """
    Validates Colombian NIT with check digit algorithm.
    Returns (is_valid, error_message)

    Format: XXXXXXXXX-D where D is check digit
    Algorithm: Modulo 11 with specific weights
    """
    import re

    # Normalize: remove spaces, dots
    nit = re.sub(r'[.\s]', '', nit)

    # Format: 9 digits + hyphen + 1 check digit
    match = re.match(r'^(\d{9})-(\d)$', nit)
    if not match:
        return False, f"NIT debe tener formato XXXXXXXXX-D (9 dígitos, guión, dígito verificador). Recibido: {nit}"

    number_part, check_digit = match.groups()
    number_part = number_part.zfill(15)  # Pad to 15 digits

    # Check digit calculation (Colombian DIAN algorithm)
    weights = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
    total = sum(int(number_part[i]) * weights[i] for i in range(15))
    remainder = total % 11

    if remainder in (0, 1):
        calculated_check_digit = remainder
    else:
        calculated_check_digit = 11 - remainder

    if int(check_digit) != calculated_check_digit:
        return False, f"Dígito verificador incorrecto. Esperado: {calculated_check_digit}, recibido: {check_digit}"

    return True, ""

# Use in import validation
for row in excel_clientes:
    is_valid, error = validar_nit_colombia(row['NIT'])
    if not is_valid:
        row['_error'] = error  # Show in preview
```

2. **Auto-calculate check digit if missing:**
If user provides "901234567" without check digit, calculate and append it. Show in preview:
```
NIT ingresado: 901234567
NIT corregido: 901234567-5 ✓
```

3. **Template includes example with explanation:**
```
| NIT           | Nombre Cliente | ...
|---------------|----------------|
| 901234567-5   | Velas del Sol  |  <- Ejemplo: 9 dígitos + guión + dígito verificador
```

4. **Accept generic "222222222222" for cash clients:**
Colombia uses NIT "222222222222" for "Cliente Mostrador" (walk-in customers). Don't validate check digit for this.

**Detection:**
- Before saving import, run validation on all NITs
- Count: `SELECT COUNT(*) FROM clientes WHERE nit !~ '^\d{9}-\d$'`
- If > 0, flag for review

**Phase to address:** Phase 2 (Import Features - Step 3 Clients)
Must be in place when client import launches.

---

### Pitfall 6: Wizard Abandonment Due to Mandatory Overload

**What goes wrong:**
Onboarding wizard requires ALL 7 steps before user can access the system. User hits Step 4 (inventory adjustment), doesn't have that data ready, abandons. Never comes back. Activation rate < 30%.

**Why it happens:**
- Designer thinks "complete data = better experience"
- Product manager wants "everything configured upfront"
- No data on what users actually NEED vs. what they WANT to defer
- No "skip for now" option
- Wizard doesn't save progress if user leaves

**Consequences:**
- **Low activation rate:** Users register but never use system
- **Support burden:** "How do I skip this step?"
- **Competitive disadvantage:** Competitor has simpler onboarding
- **Revenue loss:** Users don't convert to paying customers

**Prevention:**

1. **Only 3 steps mandatory (PRD specifies this, enforce it):**
   - Step 1: Company data (required for invoicing)
   - Step 2: Products (required for sales)
   - Step 3: Clients (required for invoicing, can use generic "Mostrador")

   Steps 4-7 are OPTIONAL. Must be clearly labeled and skippable.

2. **Progress saved automatically:**
```tsx
// frontend/src/components/OnboardingWizard.tsx
useEffect(() => {
  // Auto-save every step completion
  const saveProgress = async () => {
    await api.post('/onboarding/save-progress', {
      current_step: currentStep,
      completed_steps: completedSteps,
      data: formData
    });
  };

  const debounced = debounce(saveProgress, 2000);
  debounced();

  return () => debounced.cancel();
}, [currentStep, formData]);
```

3. **Resume from last step:**
On login, if onboarding incomplete:
```tsx
const { data: progress } = useQuery('/onboarding/progress');

if (progress.status === 'incomplete') {
  return <OnboardingWizard initialStep={progress.current_step} />;
}
```

4. **Clear value proposition per step:**
```
Step 4: Inventario Inicial (OPCIONAL)
¿Por qué importar inventario?
✓ Conoce tu stock actual desde el primer día
✓ Calcula costos y márgenes correctamente
✓ Genera reportes de valorización

¿Aún no tienes esta información?
[Omitir por ahora] [Continuar]

Si omites, puedes agregar inventario después desde Configuración.
```

5. **A/B test step order:**
Maybe "Import clients" (Step 3) should be optional too, since "Cliente Mostrador" exists.
Track metrics:
- Users who complete Step 3 vs. skip it
- Activation rate for both cohorts
- Adjust based on data

**Detection:**
- Analytics: Funnel report
  ```
  Step 1 started: 100 users
  Step 1 completed: 95 users (95%)
  Step 2 started: 95 users
  Step 2 completed: 90 users (94.7%)
  Step 3 started: 90 users
  Step 3 completed: 85 users (94.4%)
  Step 4 started: 85 users
  Step 4 completed: 30 users (35.3%)  <- HUGE DROP
  ```
- If any step has < 80% completion, it's too hard or perceived as non-essential

**Phase to address:** Phase 3 (Wizard UX)
Before public launch. Get onboarding right or users won't stick.

---

## MODERATE PITFALLS

### Pitfall 7: Large File Upload Timeout

**What goes wrong:**
User uploads 5MB Excel with 10,000 product rows. Nginx times out at 60s. Request fails, no feedback. User re-uploads, duplicate import.

**Prevention:**
- Increase timeouts: Nginx `client_max_body_size 10M`, `proxy_read_timeout 300s`
- Show progress bar during upload
- Stream parsing: don't load entire file into memory
- Background processing: Upload → job queue → notify via WebSocket when done

**Phase:** Phase 2 (Import Features - File handling)

---

### Pitfall 8: Preview Shows Wrong Data Due to Caching

**What goes wrong:**
User uploads products.xlsx, sees preview with 100 rows. Edits file, re-uploads. Preview still shows old 100 rows due to browser/server cache.

**Prevention:**
- Cache-busting: append `?v=<timestamp>` to preview API URL
- Use POST for preview (not GET), POST is never cached
- Clear preview on new file selection:
  ```tsx
  const handleFileChange = (e) => {
    setPreviewData(null);  // Clear old preview
    setFile(e.target.files[0]);
  };
  ```

**Phase:** Phase 2 (Import Features - Preview)

---

### Pitfall 9: Sequential Invoice Numbers Conflict on Historical Import

**What goes wrong:**
User imports historical invoices FAC-001 to FAC-050. System's `numero_siguiente_factura` is still at 1. Next manual invoice tries to create FAC-001 → duplicate key error.

**Prevention:**
- After importing historical invoices, update `configuracion_tenant.numero_siguiente_factura`:
  ```python
  max_numero = db.query(func.max(Facturas.numero)).filter(
      Facturas.tenant_id == tenant_id
  ).scalar()

  # Extract numeric part: "FAC-050" → 50
  import re
  match = re.search(r'\d+', max_numero)
  if match:
      next_number = int(match.group()) + 1
      config.numero_siguiente_factura = next_number
  ```

**Phase:** Phase 2 (Import Features - Step 6 Historical Invoices)

---

### Pitfall 10: Decimal Precision Loss in Excel

**What goes wrong:**
Excel stores numbers as float64. Cost $10.125 becomes 10.12500000001 or rounds to $10.13. Import into DECIMAL(14,2) field truncates/rounds unexpectedly.

**Prevention:**
```python
from decimal import Decimal, ROUND_HALF_UP

def parse_decimal_from_excel(value, decimal_places=2):
    """Safely convert Excel float to Decimal with correct rounding."""
    if value is None:
        return Decimal('0.00')

    # Convert to string first to avoid float precision issues
    str_value = f"{value:.10f}"  # More precision than needed
    dec = Decimal(str_value).quantize(
        Decimal(10) ** -decimal_places,
        rounding=ROUND_HALF_UP
    )
    return dec
```

**Phase:** Phase 2 (Import Features - Parsing)

---

### Pitfall 11: Orphaned File Storage After Import Failure

**What goes wrong:**
User uploads logo.png in Step 1. Step 2 fails validation. User abandons wizard. logo.png remains in S3 forever, costing money.

**Prevention:**
- Store uploads in temporary location first: `s3://bucket/temp/{session_id}/`
- On wizard completion, move to permanent: `s3://bucket/tenants/{tenant_id}/`
- Cron job deletes temp files > 24h old
- Or use presigned URLs for direct upload, only save URL on final submit

**Phase:** Phase 3 (Wizard UX - File management)

---

### Pitfall 12: Missing Transaction Rollback on Partial Failure

**What goes wrong:**
Importing 1000 products. Product #500 fails validation (duplicate SKU). First 499 are already inserted. User sees error, fix Excel, re-upload. Now have duplicates.

**Prevention:**
- ALL import operations in a single transaction:
  ```python
  async with db.begin():  # Transaction starts
      # All inserts here
      for row in excel_rows:
          producto = Productos(**row)
          db.add(producto)

      # If ANY error occurs before commit, ALL inserts are rolled back
      await db.commit()
  ```
- Never commit until all validations pass
- Preview step catches validation errors BEFORE attempting insert

**Phase:** Phase 2 (Import Features - Transaction safety)

---

## MINOR PITFALLS

### Pitfall 13: Date Format Ambiguity (DD/MM/YYYY vs. MM/DD/YYYY)

**Prevention:**
- Require ISO format in Excel templates: `YYYY-MM-DD`
- Or detect format from first row, ask user to confirm:
  ```
  Detected date format: DD/MM/YYYY
  Example: 15/02/2026 → 2026-02-15
  [Correct] [No, it's MM/DD/YYYY]
  ```

**Phase:** Phase 2 (Import Features - Date parsing)

---

### Pitfall 14: Empty Rows in Excel Treated as Data

**Prevention:**
```python
# Skip empty rows
rows = [row for row in excel_rows if any(row.values())]
```

**Phase:** Phase 2 (Import Features - Parsing)

---

### Pitfall 15: Column Header Case Sensitivity

**Prevention:**
Normalize headers: `header.strip().lower()` before matching expected columns.

**Phase:** Phase 2 (Import Features - Parsing)

---

## PHASE-SPECIFIC WARNINGS

| Phase Topic | Likely Pitfall | Mitigation | Priority |
|-------------|---------------|------------|----------|
| Phase 1: DB Reset | RLS policies lost after reset | Use TRUNCATE, not DROP; verify policies after | CRITICAL |
| Phase 1: DB Reset | Seed data (PUC, planes) not restored | Scripted seed data restore; verify count | HIGH |
| Phase 1: DB Reset | Superadmin user deleted | Exclude `usuarios` table where `es_superadmin=true` | HIGH |
| Phase 2: Product Import | RLS context lost in bulk insert | Explicit SET LOCAL per transaction | CRITICAL |
| Phase 2: Product Import | Encoding issues with ñ, á, é | Force UTF-8, use .xlsx not .csv | HIGH |
| Phase 2: Product Import | Decimal precision loss | Use Decimal, not float | MEDIUM |
| Phase 2: Client Import | NIT check digit not validated | Implement Colombian NIT algorithm | HIGH |
| Phase 2: Client Import | Duplicate clients (same NIT, different names) | Unique constraint + preview flag duplicates | MEDIUM |
| Phase 2: Inventory Import | Weighted average cost wrong | Chronological order enforced; use movements, not snapshots | CRITICAL |
| Phase 2: Inventory Import | Negative stock after import | Validation: `SUM(movements) >= 0` per product | MEDIUM |
| Phase 2: Historical Invoices | Sequential numbers conflict | Update `numero_siguiente_factura` after import | HIGH |
| Phase 2: Historical Invoices | Productos referenced not imported yet | Enforce import order: Products → Inventory → Invoices | HIGH |
| Phase 2: Historical Invoices | Accounting entries for historical invoices | Option: skip auto-entries, only opening balance | MEDIUM |
| Phase 3: Wizard UX | High abandonment rate | Only 3 mandatory steps, save progress | HIGH |
| Phase 3: Wizard UX | User can't resume after browser close | Persist progress server-side, restore on login | MEDIUM |
| Phase 3: Wizard UX | No feedback during long import | Progress bar, show rows processed / total | MEDIUM |

---

## DETECTION STRATEGIES

### 1. Automated Tests

```python
# tests/test_import_pitfalls.py

def test_rls_context_in_bulk_import(db_session, tenant_id):
    """Ensure RLS context is set during bulk operations."""
    # Setup
    products = [{"sku": f"TEST-{i}", "nombre": f"Product {i}"} for i in range(100)]

    # Import
    import_productos_bulk(tenant_id, products)

    # Verify: all products belong to correct tenant
    result = db_session.query(Productos.tenant_id, func.count()).group_by(Productos.tenant_id).all()
    assert len(result) == 1, "Products leaked to other tenants!"
    assert result[0][0] == tenant_id

def test_nit_validation():
    """Test Colombian NIT check digit algorithm."""
    assert validar_nit_colombia("901234567-5")[0] == True
    assert validar_nit_colombia("901234567-3")[0] == False  # Wrong check digit
    assert validar_nit_colombia("901234567")[0] == False    # Missing check digit

def test_weighted_average_cost_calculation():
    """Test inventory cost remains correct after multiple imports."""
    # Initial: 10 units at $5 = $50 total, avg $5
    # Import: 20 units at $8 = $160 total
    # Expected avg: ($50 + $160) / 30 = $7

    producto = Productos(stock=10, precio_costo=Decimal('5.00'))
    apply_inventory_adjustment(producto, cantidad=20, costo=Decimal('8.00'))

    assert producto.stock == 30
    assert producto.precio_costo == Decimal('7.00')

def test_spanish_characters_encoding():
    """Test Excel import preserves Spanish characters."""
    excel_data = [
        {"nombre": "Señora López", "ciudad": "Bogotá"},
        {"nombre": "José María", "ciudad": "Año Nuevo"}
    ]

    imported = parse_excel_with_encoding_detection(excel_data)

    assert imported[0]["nombre"] == "Señora López"  # ñ preserved
    assert imported[1]["ciudad"] == "Año Nuevo"     # ñ preserved
```

### 2. Manual Verification Checklist

After implementing each phase, verify:

**Phase 1 (DB Reset):**
- [ ] Run reset script twice in succession (should be idempotent)
- [ ] Check RLS policy count before/after: `SELECT COUNT(*) FROM pg_policies;`
- [ ] Verify seed data exists: `SELECT COUNT(*) FROM planes; SELECT COUNT(*) FROM cuentas_puc;`
- [ ] Superadmin can log in after reset
- [ ] Create test tenant, verify RLS isolation

**Phase 2 (Import Features):**
- [ ] Upload Excel with Spanish characters (ñ, á, é, í, ó, ú), verify no corruption
- [ ] Import 1000+ rows, verify no timeout
- [ ] Import with deliberate error at row 500, verify rollback (0 rows inserted)
- [ ] Import products, then inventory, verify weighted average cost correct
- [ ] Import client with invalid NIT, verify validation error shown
- [ ] Import historical invoices, create new invoice, verify number doesn't conflict

**Phase 3 (Wizard UX):**
- [ ] Abandon wizard at Step 4, return later, verify progress restored
- [ ] Skip optional steps, verify system usable
- [ ] Complete all 7 steps, verify data appears correctly in main app
- [ ] Upload logo in Step 1, abandon wizard, verify file deleted after 24h

### 3. Production Monitoring

```python
# backend/app/utils/monitoring.py

async def check_data_integrity():
    """Run after every import to detect corruption early."""
    issues = []

    # Check 1: Orphaned records (tenant_id = NULL)
    result = await db.execute(text("""
        SELECT 'productos' as tabla, COUNT(*) as count FROM productos WHERE tenant_id IS NULL
        UNION ALL
        SELECT 'clientes', COUNT(*) FROM clientes WHERE tenant_id IS NULL
        UNION ALL
        SELECT 'facturas', COUNT(*) FROM facturas WHERE tenant_id IS NULL
    """))
    for row in result:
        if row.count > 0:
            issues.append(f"CRITICAL: {row.count} orphaned records in {row.tabla}")

    # Check 2: Negative stock
    result = await db.execute(text("""
        SELECT sku, stock FROM productos WHERE stock < 0
    """))
    for row in result:
        issues.append(f"WARNING: Negative stock for {row.sku}: {row.stock}")

    # Check 3: Cost calculation mismatch
    result = await db.execute(text("""
        SELECT p.sku, p.precio_costo as stored_cost,
               SUM(m.cantidad * m.costo_por_unidad) / SUM(m.cantidad) as calculated_cost
        FROM productos p
        JOIN movimientos_stock m ON m.producto_id = p.id
        GROUP BY p.id
        HAVING ABS(p.precio_costo - calculated_cost) > 0.10
    """))
    for row in result:
        issues.append(f"ERROR: Cost mismatch for {row.sku}: stored={row.stored_cost}, calculated={row.calculated_cost}")

    if issues:
        # Send to Sentry
        for issue in issues:
            logger.error(issue)
        raise DataIntegrityError("\n".join(issues))
```

---

## SOURCES AND CONFIDENCE NOTES

**Confidence Level: MEDIUM**

This research is based on:

1. **Training data (LOW-MEDIUM confidence):**
   - General knowledge of Excel import pitfalls in enterprise systems
   - PostgreSQL RLS behavior and common mistakes
   - Onboarding wizard UX patterns and abandonment causes
   - Colombian NIT validation algorithm (well-documented in Colombian tax authority resources)

2. **Project context analysis (HIGH confidence):**
   - Reviewed `tenant_context.py` middleware implementation
   - Analyzed RLS policy structure and tenant isolation approach
   - PROJECT.md requirements clearly specify progressive wizard (3 mandatory + 4 optional steps)
   - CLAUDE.md technical constraints (multi-tenancy, weighted average costing, decimal precision)

3. **NOT verified with external sources (due to WebSearch unavailable):**
   - Latest Excel parsing library recommendations (openpyxl, pandas) for 2026
   - Recent case studies of similar SaaS import failures
   - Current best practices for onboarding wizard step counts
   - Colombian tax authority's latest NIT validation requirements

**Recommendations for validation:**
- Consult DIAN (Colombian tax authority) official documentation for NIT algorithm confirmation
- Review openpyxl and pandas changelogs for encoding handling changes in 2025-2026
- A/B test wizard step count (3 mandatory vs. 5 mandatory) to determine optimal UX
- Load test bulk import with 10,000+ rows to verify timeout/memory assumptions

**Limitations:**
- No real-world incident reports analyzed (would increase confidence on likelihood/severity)
- No competitor analysis (how do Alegra, Siigo, Zoho handle similar imports?)
- No user research data (actual pain points Colombian microenterprises face with Excel imports)

---

## CONCLUSION

The most critical pitfalls to address immediately (Phase 1):

1. **RLS context loss** — Silent data corruption, cross-tenant leakage (CRITICAL)
2. **DB reset destroys policies** — Security breach, no RLS enforcement (CRITICAL)
3. **Weighted average cost errors** — Irreversible financial data corruption (CRITICAL)

These three can cause **irreversible damage requiring manual data surgery or full re-import**. All others are fixable post-launch with migrations or patches.

The Phase 2-3 pitfalls (encoding, NIT validation, wizard abandonment) are **high-impact for user experience** but won't corrupt data or create security holes if missed initially. They should still be addressed before public launch to avoid support burden and low activation rates.
