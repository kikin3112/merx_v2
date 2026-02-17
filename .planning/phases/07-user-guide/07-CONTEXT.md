# Phase 7 Context: User Guide PDF

## User Request

Create a PDF user guide for Chandelier ERP/POS system with the following specifications:

### Requirements

1. **PDF Document** - Generate a comprehensive PDF document
2. **Current Functionalities Only** - Document only features currently implemented in the system
3. **Guided Creation** - Creation process should be guided/step-by-step
4. **Structure** - Must include:
   - Quick Start (getting started guide)
   - Functionalities (all system features)
   - Manual (detailed instructions)

### Research Requirement

Research the state of the art as of December 2025 for creating effective user manuals and guides that are:
- Easy to understand
- Effective for onboarding
- Professionally structured

## Current System Functionalities (from CLAUDE.md)

The system currently includes:

1. **Authentication & Multi-tenancy**
   - JWT authentication
   - Multi-tenant RLS PostgreSQL
   - User roles (admin, vendedor, contador)

2. **Products & Inventory**
   - CRUD Products
   - Inventory with weighted average costing
   - Stock alerts

3. **Recipes (BOM)**
   - Bill of Materials for finished products
   - Raw materials tracking
   - Production calculations

4. **Margin Calculator**
   - Cost + desired margin → suggested price
   - Formula: price = cost / (1 - margin/100)

5. **CRM Clients**
   - Client management
   - NIT tracking
   - Retention handling

6. **Quotations**
   - Create quotations
   - Convert to invoices
   - Validity dates

7. **Billing (PDF)**
   - Invoice generation
   - PDF export (without DIAN)
   - Numbering by tenant

8. **POS (Mobile-first)**
   - Point of sale interface
   - Product grid
   - Cart management

9. **Accounting**
   - PUC Colombia (~40 accounts)
   - Automatic entries
   - Balance verification

10. **Dashboard & Reports**
    - KPI cards
    - Sales charts
    - Basic reports

11. **Advanced Reports**
    - Profitability analysis
    - ABC inventory analysis
    - Cash flow projection

12. **Storage**
    - S3/R2 for PDFs and logos

13. **Online Payments (Wompi)**
    - Subscription payments
    - Webhook handling

## Decisions

- Document in Spanish (Colombian market)
- Include screenshots descriptions
- Use professional formatting
- Print-friendly layout

## Deferred Ideas

- Video tutorials (out of scope - only PDF)
- Interactive HTML guide (out of scope - PDF only)
- Multi-language support (out of scope)
