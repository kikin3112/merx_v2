# Squad: Accounting & Finance

> Cross-functional squad owning the financial backbone — journal entries, periods, and regulatory reporting.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L4 — Domain Team |
| **Model** | Spotify Squad |
| **Scope** | `contabilidad`, `configuracion_contable`, `cuentas_contables`, `periodos_contables`, `reportes` |
| **Reports To** | Head of Product (functional), VP Eng (technical) |

---

## Composition

| Role | Responsibility |
|------|---------------|
| **Product Owner** | Prioritizes accounting features, financial reports, period management |
| **Backend Dev (Senior)** | Accounting service, period closing, integration with billing/purchases |
| **Frontend Dev** | ContabilidadPage, ReportesPage, accounting configuration module |
| **QA Engineer** | Journal entry validation, balance verification, regulatory report testing |

---

## Module Detail

| Module | Key Features | Complexity |
|--------|-------------|-----------|
| `contabilidad` | Journal entries (automatic + manual), double-entry bookkeeping | High |
| `configuracion_contable` | Chart of accounts setup, tax configuration, defaults | Medium |
| `cuentas_contables` | Account hierarchy, types, balances | Medium |
| `periodos_contables` | Period open/close, fiscal year management | High |
| `reportes` | Balance sheet, P&L, trial balance, regulatory reports | High |

---

## Key Flows

```
Invoice Created → Auto Journal Entry → Period Balance Updated → Reports Generated
Purchase Created → Auto Journal Entry → Period Balance Updated
Period Closing → Validation → Balance Freeze → New Period Opens
```

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Invoice data | Squad: Sales | | Financial reports | Users + COO |
| Purchase data | Squad: Platform | | Balance data | Data & Analytics guild |
| Inventory costs | Squad: Inventory | | Tax reports | DIAN (external) |
| Tax configuration | Compliance | | Period status | All squads (affects data entry) |

---

## Metrics

| Metric | Target |
|--------|--------|
| Journal entry accuracy (auto-generated) | 100% |
| Reporting generation time | < 5s for standard reports |
| Period closing success rate | 100% |
| Double-entry validation | Zero imbalances |
| Sprint commitment completion | ≥ 80% |

---

## Dependencies

| Depends On | For |
|-----------|-----|
| Squad: Sales | Invoice data for automatic journal entries |
| Squad: Platform | Purchase data, tenant context |
| Squad: Inventory | Inventory valuation for cost accounting |
| Guild: Security | Financial data encryption, compliance |
| Guild: Data & Analytics | Report generation pipelines |
