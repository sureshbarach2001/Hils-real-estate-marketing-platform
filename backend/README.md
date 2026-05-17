# `backend/`

FastAPI service for the Hils Marketing platform. Async MongoDB (Motor), Pydantic models, JWT auth, Stripe Checkout, SMTP email.

## Run

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                # then fill secrets
uvicorn server:app --reload --port 8000
```

Verify: `curl http://localhost:8000/api/health`

## Layout

| Path | Purpose |
|------|---------|
| `server.py` | FastAPI app entry, CORS, router mounting |
| `routes/` | `APIRouter` modules grouped by domain |
| `models/` | Pydantic schemas + Mongo document models |
| `utils/` | DB, auth, Stripe, email, geo helpers |
| `tests/` | Pytest suite (async) |

Full architecture, data flow, and API contracts: see [`/DOCS/architecture.md`](../DOCS/architecture.md) and [`/DOCS/api-reference.md`](../DOCS/api-reference.md).
