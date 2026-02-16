# Phase 1: Foundation & Reset - Context

**Gathered:** 2026-02-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Superadmin can reset database safely (clearing all development/tenant data while preserving schema, PUC, planes, and superadmin account) and system can generate downloadable Excel templates for product, client, and inventory imports. Backend can parse uploaded .xlsx and .csv files with automatic column detection.

</domain>

<decisions>
## Implementation Decisions

### Reset scope & safety
- Triggered from a **dedicated admin page** in the UI (no CLI needed)
- Confirmation flow: superadmin must **re-enter their password** to confirm the destructive action
- **Clean slate reset**: deletes ALL tenants, users, and transactional data. Preserves only PUC, planes, schema, and superadmin account
- **Auto-backup before reset**: system creates a pg_dump snapshot before executing, stored locally for recovery
- **Pre-reset summary**: before password confirmation, show row counts per table ("45 products, 12 clients, 3 tenants will be deleted")

### Excel template content
- Three templates available for download: **Products**, **Clients**, **Inventory adjustments**
- Column headers in **Spanish** (matching Colombian user base): 'Nombre', 'Precio Venta', 'NIT', etc.
- Example rows use **candle-specific data**: 'Vela Aromática Lavanda', 'Cera de Soya', realistic Colombian prices and NITs
- Each template includes a **help sheet** (second sheet in .xlsx) explaining each column, valid values, and tips
- 2-3 example rows per template

### Audit trail design
- Audit log captures: **who** (superadmin email/id), **when** (timestamp), **what was deleted** (row counts per table), **backup reference** (path/name of auto-backup)
- Superadmin can **view reset history** from the same admin page: list of past resets with date, who, and what was deleted
- Storage approach: Claude's discretion (database table vs log file — will be decided during planning)

### Claude's Discretion
- Audit log storage mechanism (database table vs log file)
- Auto-backup retention policy (how long snapshots are kept)
- Exact column set per Excel template (based on entity schema)
- Help sheet formatting and content depth
- File parsing error handling strategy (encoding, malformed files)
- Admin page layout and UX details

</decisions>

<specifics>
## Specific Ideas

- Pre-reset summary showing counts gives superadmin confidence about what they're about to delete
- Password re-entry (not "type RESET") because it's familiar and secure without being annoying
- Candle-specific example data in templates so users immediately understand the format with domain-relevant context
- Help sheet in templates reduces support burden — users can self-serve without reading external docs

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-reset*
*Context gathered: 2026-02-15*
