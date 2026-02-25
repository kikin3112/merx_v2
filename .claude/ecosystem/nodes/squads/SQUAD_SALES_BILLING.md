# Squad: Sales & Billing

> Cross-functional squad owning the entire revenue flow — from quotation to collection.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L4 — Domain Team |
| **Model** | Spotify Squad (autonomous, cross-functional) |
| **Scope** | `facturas`, `ventas`, `cotizaciones`, `POS`, `cartera`, `medios_pago` |
| **Reports To** | Head of Product (functional), VP Eng (technical) |

---

## Composition

| Role | Responsibility |
|------|---------------|
| **Product Owner** | Prioritizes features: invoicing, sales flow, POS, collections, payment methods |
| **Backend Dev (Senior)** | Billing logic, tax integration (DIAN), collections module, payment processing |
| **Backend Dev** | Quotation endpoints, sales flows, quotation→invoice conversion |
| **Frontend Dev (Senior)** | FacturasPage, VentasPage, POSPage, CotizacionesPage, CarteraPage |
| **QA Engineer** | End-to-end sales flow testing, financial calculations validation |

---

## Module Detail

| Module | Key Features | Complexity |
|--------|-------------|-----------|
| `facturas` | Electronic invoicing, DIAN compliance, credit/debit notes | High |
| `ventas` | Sales orders, multiple payment methods, discounts | Medium |
| `cotizaciones` | Quotation creation, conversion to invoice, expiration | Medium |
| `POS` | Point of sale, quick checkout, cash register | High |
| `cartera` | Accounts receivable, aging, payment tracking, reminders | High |
| `medios_pago` | Payment method configuration, integrations | Medium |

---

## Key Flows

```
Quotation → [Approve] → Sales Order → [Invoice] → Invoice → [Payment] → Collection
                                                       ↓
                                                  DIAN Validation
```

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Product specs | PO + Head Product | | Invoices | End users + Accounting squad |
| Accounting chart | Squad: Accounting | | Payment records | Squad: Accounting |
| Third-party data | Squad: CRM & Thirds | | Sales reports | Data & Analytics guild |
| Payment gateway APIs | External | | POS transactions | Inventory squad (stock updates) |
| Tax configurations | Compliance | | DIAN electronic invoices | DIAN (external) |

---

## Metrics

| Metric | Target |
|--------|--------|
| Sprint velocity stability | ±15% |
| Invoice generation p95 latency | < 500ms |
| DIAN integration success rate | ≥ 99.5% |
| Financial calculation accuracy | 100% |
| Bug escape rate | < 5% |
| Sprint commitment completion | ≥ 80% |

---

## Dependencies

| Depends On | For |
|-----------|-----|
| Squad: Accounting | Automatic journal entries from invoices |
| Squad: CRM & Thirds | Customer/third-party data for invoicing |
| Squad: Inventory | Stock validation for POS/sales |
| Squad: Platform | Multi-tenant context, auth, permissions |
| Guild: Security | DIAN compliance, data encryption |
