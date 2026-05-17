# `shared/`

Plain-JavaScript constants and helpers reused by both `frontend/` and `backend/`. Pure ESM — no React, no FastAPI imports, no Node-only APIs (no `fs`, no `path`). Must run in the browser, in Node, and in a Python-import shim if needed.

| File | Purpose |
|------|---------|
| `constants.js` | Cities, currency, theme tokens, enums |
| `utils.js` | `formatPKR`, `slugify`, and other pure helpers |

## Import patterns

```js
// Frontend (via a Vite alias to ../shared)
import { CITIES, formatPKR } from '@shared/constants';

// Or a relative import
import { formatPKR } from '../../shared/utils.js';
```

For the backend, see [`/DOCS/architecture.md`](../DOCS/architecture.md) §2 for how shared values are mirrored into Python constants (and the script that keeps them in sync).
