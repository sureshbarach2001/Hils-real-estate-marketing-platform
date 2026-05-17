# `frontend/src/utils/`

Pure helpers, API client, and shared validation schemas.

## Convention

- All exports are pure functions — no React imports here.
- Zod schemas live in `utils/schemas/` and are imported by both forms and the API client.

## Planned modules

| File | Purpose |
|------|---------|
| `api.js` | Fetch wrapper — base URL from `VITE_API_BASE_URL`, `credentials: 'include'`, typed `ApiError` |
| `formatters.js` | `formatPKR`, `formatDate`, `formatRelative` |
| `cn.js` | `clsx` + `tailwind-merge` wrapper used by all components |
| `schemas/auth.js` | `loginSchema`, `registerSchema` (Zod) |
| `schemas/listing.js` | `listingCreateSchema`, `listingSearchSchema` (Zod) |

Re-use [`/shared/utils.js`](../../../shared/utils.js) when a helper is also needed by the backend (e.g. `slugify`).
