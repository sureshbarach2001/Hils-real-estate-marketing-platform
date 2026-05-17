# `frontend/src/`

Application source. Entry point is `main.jsx` (added when the React app is scaffolded).

| Subfolder | Purpose |
|-----------|---------|
| `components/` | Reusable building blocks |
| `pages/` | Top-level route views |
| `hooks/` | Custom React hooks |
| `utils/` | API client, formatters, shared validation schemas |

Cross-app constants (cities, currency, theme tokens) live in [`/shared/constants.js`](../../shared/constants.js) and are imported from both `frontend` and `backend` (via a build alias).
