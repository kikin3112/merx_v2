# Logo Circular & Favicon Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the ChandeliERP circular logo as favicon in both apps and display it in the landing Navbar and ERP Sidebar.

**Architecture:** Create a single `logo-circular.svg` file (corrected + circular version of `isotipo.svg`) and distribute it to both `frontend/public/` and `landing/public/`. Wire it up in 4 places: 2 favicons, 2 nav components.

**Tech Stack:** SVG (static asset), React (Sidebar), Next.js metadata API (landing favicon), HTML (frontend favicon)

---

## CRITICAL BRANDING CONSTRAINT

The isotipo design (flame shape, amber color `#C17B2B`, gold line `#D4A843`, proportions, opacity layers) **must not change**. The only modifications to the SVG source are:
1. Fix missing `<` on opening tag
2. Change background rect `rx="20"` → `rx="100"` (rounded square → circle)

---

### Task 1: Create `logo-circular.svg`

**Files:**
- Create: `frontend/public/logo-circular.svg`

**Step 1: Write the file**

Create `frontend/public/logo-circular.svg` with the following exact content (corrected from `isotipo.svg` — bug fix on line 1, `rx` changed to 100):

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <title>ChandeliERP Isotipo</title>
  <rect width="200" height="200" fill="#1A1A2E" rx="100"/>
  <g transform="translate(0, 5)">
    <path d="M 100 185
  C 52 170 38 140 48 108
  C 55 84 68 65 74 42
  C 82 55 80 78 84 90
  C 90 70 94 42 90 22
  C 112 48 120 80 110 102
  C 122 88 128 68 122 48
  C 148 72 152 108 136 128
  C 145 116 145 140 130 158
  C 120 172 110 184 100 185 Z" fill="#C17B2B" opacity="0.15"/>
    <path d="M 100 185
  C 52 170 38 140 48 108
  C 55 84 68 65 74 42
  C 82 55 80 78 84 90
  C 90 70 94 42 90 22
  C 112 48 120 80 110 102
  C 122 88 128 68 122 48
  C 148 72 152 108 136 128
  C 145 116 145 140 130 158
  C 120 172 110 184 100 185 Z" fill="#C17B2B"/>
    <line x1="48" y1="178" x2="128" y2="130" stroke="#D4A843" stroke-width="4"
          stroke-linecap="round"/>
  </g>
</svg>
```

**Step 2: Verify in browser**

Open `frontend/public/logo-circular.svg` in a browser (or VS Code SVG preview).
Expected: circular dark badge with amber flame, no XML errors.

**Step 3: Copy to landing**

```bash
mkdir -p landing/public
cp frontend/public/logo-circular.svg landing/public/logo-circular.svg
```

**Step 4: Commit**

```bash
git checkout -b feat/logo-circular
git add frontend/public/logo-circular.svg landing/public/logo-circular.svg
git commit -m "feat(branding): add logo-circular.svg to frontend and landing public assets"
```

---

### Task 2: Update frontend favicon

**Files:**
- Modify: `frontend/index.html:5-6`

**Step 1: Read the file**

Open `frontend/index.html`. Current lines 5-6:
```html
<link rel="icon" type="image/svg+xml" href="/chandelier.svg" />
<link rel="shortcut icon" href="/chandelier.svg" />
```

**Step 2: Replace both href values**

```html
<link rel="icon" type="image/svg+xml" href="/logo-circular.svg" />
<link rel="shortcut icon" href="/logo-circular.svg" />
```

**Step 3: Verify**

Run `npm run dev` in `frontend/`. Open http://localhost:5173 in browser.
Expected: browser tab shows the circular amber flame icon.

**Step 4: Commit**

```bash
git add frontend/index.html
git commit -m "feat(branding): update frontend favicon to logo-circular.svg"
```

---

### Task 3: Update landing favicon

**Files:**
- Modify: `landing/app/layout.tsx:11-20`

**Step 1: Read the file**

Open `landing/app/layout.tsx`. Current `metadata` object (lines 11-20):
```ts
export const metadata: Metadata = {
  title: 'ChandeliERP — ERP para Candelería',
  description: 'Sistema ERP completo para PyMEs de candelería. Inventario, POS, Facturación, Contabilidad y CRM. Prueba gratis 14 días.',
  keywords: ['ERP', 'candelería', 'inventario', 'POS', 'facturación', 'PyME', 'Colombia'],
  openGraph: {
    title: 'ChandeliERP — ERP para Candelería',
    description: 'Sistema ERP completo para PyMEs de candelería. Prueba gratis 14 días.',
    type: 'website',
  },
};
```

**Step 2: Add icons field**

```ts
export const metadata: Metadata = {
  title: 'ChandeliERP — ERP para Candelería',
  description: 'Sistema ERP completo para PyMEs de candelería. Inventario, POS, Facturación, Contabilidad y CRM. Prueba gratis 14 días.',
  keywords: ['ERP', 'candelería', 'inventario', 'POS', 'facturación', 'PyME', 'Colombia'],
  icons: { icon: '/logo-circular.svg' },
  openGraph: {
    title: 'ChandeliERP — ERP para Candelería',
    description: 'Sistema ERP completo para PyMEs de candelería. Prueba gratis 14 días.',
    type: 'website',
  },
};
```

**Step 3: Verify**

Run `npm run dev` in `landing/` (port 3001). Open http://localhost:3001 in browser.
Expected: browser tab shows the circular amber flame icon.

**Step 4: Commit**

```bash
git add landing/app/layout.tsx
git commit -m "feat(branding): add favicon to landing page via Next.js metadata"
```

---

### Task 4: Add logo to landing Navbar

**Files:**
- Modify: `landing/app/components/Navbar.tsx:23-27`

**Step 1: Read the file**

Open `landing/app/components/Navbar.tsx`. The brand link (lines 23-27):
```tsx
<Link href="/" className="flex items-center gap-2">
  <span className="text-2xl font-bold text-amber-500">
    ChandeliERP
  </span>
</Link>
```

**Step 2: Add logo image before the text**

```tsx
<Link href="/" className="flex items-center gap-2">
  <img src="/logo-circular.svg" alt="ChandeliERP logo" className="h-8 w-8" />
  <span className="text-2xl font-bold text-amber-500">
    ChandeliERP
  </span>
</Link>
```

**Step 3: Verify**

With `npm run dev` running in `landing/`, open http://localhost:3001.
Expected: Navbar shows circular dark logo (32px) to the left of "ChandeliERP" text. Logo is not distorted, proportions are correct.

**Step 4: Commit**

```bash
git add landing/app/components/Navbar.tsx
git commit -m "feat(branding): add circular logo to landing Navbar"
```

---

### Task 5: Add logo to frontend Sidebar

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.tsx:13-16`

**Step 1: Read the file**

Open `frontend/src/components/layout/Sidebar.tsx`. The brand section (lines 13-16):
```tsx
<div className="flex items-center gap-2 px-4 py-5 border-b border-gray-100">
  <div className="h-8 w-8 rounded-lg bg-primary-500 flex items-center justify-center">
    <span className="text-white font-bold text-sm">C</span>
  </div>
  <div className="min-w-0">
```

**Step 2: Replace the "C" placeholder with the logo image**

```tsx
<div className="flex items-center gap-2 px-4 py-5 border-b border-gray-100">
  <img src="/logo-circular.svg" alt="Chandelier" className="h-8 w-8 shrink-0" />
  <div className="min-w-0">
```

**Step 3: Verify**

With `npm run dev` running in `frontend/`, log in and open the sidebar.
Expected: Sidebar shows the circular dark logo (32px) where the letter "C" used to be. Logo is crisp, no distortion.

**Step 4: Commit**

```bash
git add frontend/src/components/layout/Sidebar.tsx
git commit -m "feat(branding): replace letter placeholder with circular logo in Sidebar"
```

---

### Task 6: Open PR

**Step 1: Push branch**

```bash
git push -u origin feat/logo-circular
```

**Step 2: Create PR**

```bash
gh pr create \
  --title "feat(branding): add circular logo as favicon and in navigation" \
  --body "Adds logo-circular.svg (fixed + circular isotipo) as favicon for both apps and displays it in the landing Navbar and ERP Sidebar. Branding constraint: zero changes to isotipo design — only background rx 20→100."
```

**Step 3: Verify CI passes**

```bash
gh pr checks
```

Expected: all checks green (frontend build + landing build).
