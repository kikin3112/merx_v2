# Frontend Node — Claude Code Instructions

## Scope
Client-side experience: React 19, TypeScript, Vite, Zustand, React Query, SSE, animations.

## Source Code
- Primary: `/frontend/`
- Entry: `frontend/src/main.tsx`
- Pages: `frontend/src/pages/`
- Hooks: `frontend/src/hooks/`
- Stores: `frontend/src/stores/`
- Components: `frontend/src/components/`

## Architecture Rules (NON-NEGOTIABLE)
- Zustand → global app state only (Theme, Auth, User Session).
- React Query → ALL server data. Never cache server data in Zustand manually.
- Container/Presentation pattern: logic in custom hooks, not UI components.
- NEVER use `any` in TypeScript. Use `unknown` or define the interface.
- ALWAYS define Interface for component props.
- Named exports preferred over default exports.

## Performance Rules
- Lists > 100 items → `react-window` virtualization (60fps target).
- Use `React.memo` with efficient selectors.
- SSE connections must implement reconnect logic with fallback.
- Cursor-based pagination for 500+ item lists.

## Key Dependencies
- `@react-spring/web` (NOT `react-spring`) — React 19 compatible.
- `frontend/.npmrc`: `legacy-peer-deps=true` — required for react-window + React 19.

## Run Commands
```bash
npm run dev      # dev (port 5173)
npm run build    # production build
npm run analyze  # bundle analysis
```

## UX Rules
See `ux-rules.md` in this directory.

## Agent
`.claude/agents/frontend-engineer.md`

## Node Details
`NODE.md` in this directory.
