# `frontend/`

React 19 + Vite + Tailwind + Shadcn/ui for the Hils Marketing platform. Dark luxury theme — obsidian `#050505`, champagne gold `#D4AF37`.

## Run

```bash
npm install
cp .env.example .env
npm run dev          # http://localhost:5173
```

## Layout

| Path | Purpose |
|------|---------|
| `src/components/` | Reusable presentational + Shadcn-derived primitives |
| `src/pages/` | Route-level views (Home, ListingDetail, Dashboard, …) |
| `src/hooks/` | Custom hooks (`useAuth`, `useListings`, …) |
| `src/utils/` | API client, formatters, validation schemas |
| `public/` | Static assets served as-is by Vite |

## Conventions

- **JavaScript only** — `.js` / `.jsx`. No TypeScript.
- Every interactive element gets a kebab-case `data-testid`.
- Animations via Framer Motion, gated on `prefers-reduced-motion`.
- Images: lazy-loaded, WebP/AVIF preferred, explicit `width`/`height`.

Full design + architecture: see [`/DOCS/architecture.md`](../DOCS/architecture.md).
