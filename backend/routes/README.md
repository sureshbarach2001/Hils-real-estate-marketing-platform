# `backend/routes/`

One file per domain, each exposing an `APIRouter` mounted under `/api/<domain>`.

## Convention

```python
# routes/listings.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/listings", tags=["listings"])
```

Then mount it in `server.py`:

```python
from routes import listings
app.include_router(listings.router)
```

## Planned modules

| File | Mount | Purpose |
|------|-------|---------|
| `auth.py` | `/api/auth` | Register, login, refresh, logout, forgot/reset password |
| `users.py` | `/api/users` | Profile, account settings |
| `listings.py` | `/api/listings` | CRUD + search for property listings |
| `payments.py` | `/api/payments` | Stripe Checkout Session + webhook |
| `media.py` | `/api/media` | Image uploads (signed URLs) |

Every route validates input via Pydantic. See [`/DOCS/api-reference.md`](../../DOCS/api-reference.md).
