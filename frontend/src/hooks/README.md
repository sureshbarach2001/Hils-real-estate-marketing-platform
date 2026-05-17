# `frontend/src/hooks/`

Custom React hooks. One concern per file.

## Convention

- Prefix every hook name with `use` (`useAuth`, `useListings`, `useDocumentTitle`).
- Hook files are `camelCase.js` matching the export (`useAuth.js`).
- Hooks return plain objects with named fields — avoid tuple returns longer than two elements.
- Hooks that hit the network use the shared `lib/api.js` client and handle `loading` / `error` state explicitly.

## Planned hooks

| File | Purpose |
|------|---------|
| `useAuth.js` | Current user, login/logout, refresh-on-401 |
| `useListings.js` | Paginated listing search + filters |
| `useDocumentTitle.js` | Sets `<title>` for the current page |
| `usePrefersReducedMotion.js` | Reads media query for Framer Motion gating |
