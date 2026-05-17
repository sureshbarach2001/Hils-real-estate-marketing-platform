# Setup Guide — Local Development

Get the full stack running on your machine in under 10 minutes.

---

## 1. Prerequisites

| Tool | Min version | Check | Install |
|------|-------------|-------|---------|
| Python | 3.11 | `python --version` | <https://www.python.org/downloads/> |
| Node.js | 20 LTS | `node --version` | <https://nodejs.org/> |
| MongoDB | 6.0 (local) **or** Atlas account | `mongod --version` | <https://www.mongodb.com/try/download/community> |
| Git | any recent | `git --version` | <https://git-scm.com/> |
| Stripe CLI (optional, for webhooks) | latest | `stripe --version` | <https://docs.stripe.com/stripe-cli> |

**What each is for:**

- **Python 3.11+** — runs FastAPI; `async`/`await` MongoDB needs ≥ 3.10.
- **Node 20 LTS** — Vite 6 requires Node ≥ 18; 20 is the current LTS.
- **MongoDB** — primary data store. A local instance works; Atlas free tier is also fine.
- **Stripe CLI** — forwards Stripe webhooks to `localhost` so payment flows work end-to-end.

---

## 2. Clone & install

```bash
# 1. Clone
git clone <repo-url> hils-marketing
cd hils-marketing

# 2. Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then edit values — see "Env vars" below

# 3. Frontend (new terminal)
cd ../frontend
npm install
cp .env.example .env
```

### What each command does

| Command | What it does | What it changes | How to verify |
|---------|--------------|-----------------|---------------|
| `python -m venv .venv` | Creates an isolated Python env | New `.venv/` folder | `ls .venv/` shows `bin/` (or `Scripts/`) |
| `pip install -r requirements.txt` | Installs FastAPI, Motor, Pydantic, etc. | Packages into `.venv` | `pip list \| grep fastapi` |
| `cp .env.example .env` | Seeds a real env file from the template | New `.env` (gitignored) | `cat .env` |
| `npm install` | Installs React, Vite, Tailwind, Shadcn deps | New `node_modules/` + `package-lock.json` | `ls node_modules/react` |

---

## 3. Env vars to fill

Both `.env` files start as `.env.example` and need real values for:

| Var | Where | Required | Where to get |
|-----|-------|----------|--------------|
| `MONGODB_URI` | backend | yes | Local: `mongodb://localhost:27017`. Atlas: dashboard → Connect |
| `JWT_SECRET_KEY` | backend | yes | Run `openssl rand -hex 32` |
| `STRIPE_SECRET_KEY` | backend | for payments | Stripe dashboard → Developers → API keys |
| `STRIPE_WEBHOOK_SECRET` | backend | for payments | `stripe listen` prints it on first run |
| `SMTP_PASSWORD` | backend | for email | Your SMTP provider |
| `VITE_STRIPE_PUBLISHABLE_KEY` | frontend | for payments | Same Stripe dashboard, **publishable** key |

---

## 4. Run

Three terminals, in order:

### Terminal 1 — Mongo (skip if using Atlas)

```bash
mongod --dbpath ~/data/db
```

**Expected output**

```
{"t": "...", "s":"I", "msg":"Waiting for connections", "attr":{"port":27017}}
```

### Terminal 2 — Backend

```bash
cd backend
source .venv/bin/activate
uvicorn server:app --reload --port 8000
```

**Expected output**

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Smoke test:

```bash
curl http://localhost:8000/api/health
# {"status":"ok","service":"hils-marketing-api"}
```

### Terminal 3 — Frontend

```bash
cd frontend
npm run dev
```

**Expected output**

```
  VITE v6.0.x  ready in 312 ms
  ➜  Local:   http://localhost:5173/
```

Open <http://localhost:5173>.

### Terminal 4 — Stripe webhooks (only when testing payments)

```bash
stripe listen --forward-to http://localhost:8000/api/payments/webhook
```

Copy the `whsec_...` it prints into `backend/.env` as `STRIPE_WEBHOOK_SECRET`, then restart the backend.

---

## 5. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: fastapi` | Wrong Python env active | `source backend/.venv/bin/activate`, re-run |
| `pymongo.errors.ServerSelectionTimeoutError` | Mongo not running / wrong URI | Start `mongod` or fix `MONGODB_URI` |
| CORS error in browser console | Frontend origin missing from `CORS_ORIGINS` | Add `http://localhost:5173` to `backend/.env`, restart |
| `401 Unauthorized` on every request | Cookies blocked — third-party context | Use `localhost`, not `127.0.0.1`. Both ends on `localhost`. |
| `Invalid webhook signature` | Wrong `STRIPE_WEBHOOK_SECRET` | Restart `stripe listen`, copy the fresh `whsec_...` |
| `EADDRINUSE :::8000` | Port already in use | `lsof -i :8000` → `kill <pid>` or use `--port 8001` |
| Tailwind classes don't apply | PostCSS / Tailwind config missing | Confirm `tailwind.config.js` exists; re-run `npm run dev` |
