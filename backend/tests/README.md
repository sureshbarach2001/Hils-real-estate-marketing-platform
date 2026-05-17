# `backend/tests/`

Pytest suite using `pytest-asyncio`. Mirrors the `routes/` layout.

## Run

```bash
# from backend/
pytest -v
pytest -v --tb=short tests/auth/         # one domain
pytest -k "login and not refresh" -v     # by name
```

## Convention

- One folder per domain: `tests/auth/`, `tests/listings/`, etc.
- Each test file matches the route file it covers: `routes/auth.py` → `tests/auth/test_login.py`.
- Use `httpx.AsyncClient` against the app via `ASGITransport` — no live server needed.
- Mongo tests use a throwaway `hils_marketing_test` database, dropped in a session-scoped fixture.
