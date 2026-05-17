# `backend/utils/`

Cross-cutting helpers, one concern per file.

## Planned modules

| File | Purpose |
|------|---------|
| `config.py` | `Settings(BaseSettings)` — loads + validates env on startup |
| `db.py` | Motor client, index creation, lifecycle hooks |
| `auth.py` | Password hashing, JWT encode/decode, `get_current_user` dep |
| `stripe_client.py` | Checkout Session helpers + webhook verification |
| `email.py` | `aiosmtplib` send wrapper + Jinja2 template loader |
| `geo.py` | PostGIS / geo distance helpers for listing search |
| `rate_limit.py` | `slowapi` limiter shared across `/auth/*` routes |

Each helper is **stateless** (or holds singletons created via `lru_cache`). No business logic here — that lives in `routes/`.
