# Logo Circular & Favicon — Design Document

**Date:** 2026-02-25
**Author:** Branding / Frontend

## Objective

Add the ChandeliERP circular logo as favicon to both the landing page and the ERP frontend, and display the logo in the navigation areas of each app.

## Scope

- **Landing page** (`landing/`): favicon + logo in Navbar
- **Frontend ERP** (`frontend/`): favicon update + logo in Sidebar

## Logo Asset

**Source:** `.claude/ecosystem/nodes/marketing/assets/logo/isotipo.svg`

Design: dark circular background (`#1A1A2E` midnight) with the amber flame + line icon (`#C17B2B`).

**Known bug in source file:** line 1 is missing the opening `<` character (`svg xmlns=...` instead of `<svg xmlns=...`). This is fixed in the output file.

**Output file:** `logo-circular.svg`
- Same design as `isotipo.svg` — NO changes to the logo itself
- Only change: `rx="20"` → `rx="100"` on the background rect (200×200 with radius 100 = perfect circle)
- Bug fix: correct `<svg ...>` opening tag

**CRITICAL — Branding constraint:** The isotipo design (flame shape, colors, proportions) must not be modified in any way. Only the background shape changes from rounded-square to circle.

## Files Changed

| File | Change |
|------|--------|
| `frontend/public/logo-circular.svg` | NEW — circular logo asset |
| `landing/public/logo-circular.svg` | NEW — same file, landing copy |
| `frontend/index.html` | Update favicon href: `chandelier.svg` → `logo-circular.svg` |
| `landing/app/layout.tsx` | Add `icons: { icon: '/logo-circular.svg' }` to metadata |
| `frontend/src/components/layout/Sidebar.tsx` | Replace letter "C" div with `<img>` of logo |
| `landing/app/components/Navbar.tsx` | Add `<img>` before "ChandeliERP" text in brand link |

## UI Placement

### Landing Navbar (before → after)
```
BEFORE: [ ChandeliERP ]  (amber text only)
AFTER:  [ ○ logo ] ChandeliERP  (32px circular image + amber text)
```

### Frontend Sidebar (before → after)
```
BEFORE: [ C ]  (letter in amber rounded square)
AFTER:  [ ○ logo ]  (32px circular image)
```

## Non-Goals

- No changes to `isotipo.svg` (marketing asset, stays as-is)
- No changes to `isotipo.png`
- No new logo versions, colors, or brand variants
- No favicon `.ico` generation (SVG favicons work in all modern browsers)
