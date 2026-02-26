# Squad: Inventory & Production

> Cross-functional squad owning stock management, recipes, and manufacturing flows.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L4 — Domain Team |
| **Model** | Spotify Squad |
| **Scope** | `inventarios`, `productos`, `recetas`, `ordenes_produccion` |
| **Reports To** | Head of Product (functional), VP Eng (technical) |

---

## Composition

| Role | Responsibility |
|------|---------------|
| **Product Owner** | Prioritizes stock management, recipes, traceability, production orders |
| **Backend Dev (Senior)** | Inventory service, stock logic, automated alerts, stock movements |
| **Backend Dev** | Recipe modules, composite products, production orders |
| **Frontend Dev** | InventarioPage, RecetasPage, ProductosPage. Mass virtualization (100k+ SKUs) |
| **QA Engineer** | Traceability testing, BOM/recipe calculations, stock consistency |

---

## Module Detail

| Module | Key Features | Complexity |
|--------|-------------|-----------|
| `inventarios` | Stock tracking, movements (in/out/transfer), alerts, multi-warehouse | High |
| `productos` | Product catalog, variants, pricing, categorization | Medium |
| `recetas` | Bill of materials (BOM), ingredient lists, cost calculation | High |
| `ordenes_produccion` | Production orders, work-in-progress, completion, waste tracking | High |

---

## Key Flows

```
Product Created → Stock Initialized → [Sales/POS] → Stock Deducted
                                    → [Purchase] → Stock Added
Recipe Created → Production Order → Raw Materials Consumed → Finished Product Added
```

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Product specs | PO + Head Product | | Stock levels | Squad: Sales (POS validation) |
| Purchase receipts | Squad: Platform (compras) | | Inventory reports | Data & Analytics guild |
| Sales/POS transactions | Squad: Sales | | Cost data | Squad: Accounting |
| Production schedules | PO | | Low-stock alerts | Users + Squad: Platform (SSE) |

---

## Metrics

| Metric | Target |
|--------|--------|
| Stock accuracy (physical vs system) | ≥ 99% |
| Inventory page load (100k SKUs) | < 2s with virtualization |
| Production order completion rate | ≥ 95% |
| BOM calculation accuracy | 100% |
| Sprint commitment completion | ≥ 80% |

---

## Dependencies

| Depends On | For |
|-----------|-----|
| Squad: Sales | POS stock deductions, sales order stock reservation |
| Squad: Accounting | Inventory valuation, cost accounting |
| Squad: Platform | Tenant context, real-time SSE for alerts |
| Guild: Architecture | Data model standards for multi-warehouse |
