# Deployment

Production deployment runbook for the Hils Marketing platform.

> **Status:** skeleton — fill in concrete commands & screenshots once each service is provisioned.

---

## 1. Target topology

| Layer | Provider | Region |
|-------|----------|--------|
| Frontend | Vercel | Auto (global edge) |
| API | Fly.io **or** Railway | `bom` (Mumbai) — closest to PK |
| MongoDB | MongoDB Atlas | `ap-south-1` |
| PostGIS | Neon **or** Supabase | `ap-south-1` |
| Email | SendGrid **or** Postmark | n/a |
| Stripe | Stripe-hosted | n/a |

Pick one option per layer **before** the first deploy and lock it in this doc.

---

## 2. Pre-deploy checklist

- [ ] All `.env.example` keys have real production values stored in the provider's secret manager
- [ ] `JWT_SECRET_KEY` regenerated (do **not** reuse the dev value): `openssl rand -hex 32`
- [ ] `CORS_ORIGINS` set to the production frontend URL **only** (no `*`, no localhost)
- [ ] Stripe **live** keys + a separately registered live webhook endpoint
- [ ] MongoDB Atlas IP allow-list contains the API host (or `0.0.0.0/0` with auth, if your provider gives no static IPs)
- [ ] DNS records pointed (`hils.pk` → Vercel, `api.hils.pk` → API host)
- [ ] TLS certificates issued (both providers do this automatically)
- [ ] Backup schedule verified on MongoDB Atlas
- [ ] Sentry / log drain configured

---

## 3. Frontend — Vercel

```bash
cd frontend
vercel link            # first time only
vercel --prod          # deploy
```

**What this does:** builds with `vite build`, uploads `dist/`, attaches env vars from the Vercel dashboard, issues TLS.

**Verify:** open `https://hils.pk`, check Network tab → API calls hit `https://api.hils.pk` with `withCredentials`.

---

## 4. API — Fly.io (example)

```bash
cd backend
fly launch --no-deploy --name hils-marketing-api --region bom
# Add secrets one-by-one or in bulk:
fly secrets set MONGODB_URI=... JWT_SECRET_KEY=... STRIPE_SECRET_KEY=... STRIPE_WEBHOOK_SECRET=... CORS_ORIGINS=https://hils.pk
fly deploy
```

**Verify:** `curl https://api.hils.pk/api/health` → `{"status":"ok",...}`.

---

## 5. MongoDB Atlas

1. Create cluster (M0 to start, scale to M10 once traffic justifies it), region `ap-south-1`.
2. Create DB user with **least-privilege** role on `hils_marketing` only.
3. Add the API host's IP (Fly: `fly ips list`) to the access list.
4. Copy the connection string into `MONGODB_URI`.
5. Enable continuous backup (M10+) or scheduled snapshots (M0).

---

## 6. Stripe (live mode)

1. Switch dashboard to **Live mode**.
2. Developers → API keys → copy `sk_live_...` and `pk_live_...` into the API and frontend secrets respectively.
3. Developers → Webhooks → **Add endpoint**: `https://api.hils.pk/api/payments/webhook`. Subscribe to:
   - `checkout.session.completed`
   - `checkout.session.async_payment_succeeded`
   - `checkout.session.async_payment_failed`
4. Copy the new `whsec_...` into `STRIPE_WEBHOOK_SECRET`.
5. Verify with a `$1` test charge in live mode.

---

## 7. Post-deploy smoke test

```bash
# Health
curl https://api.hils.pk/api/health

# Listings (public)
curl https://api.hils.pk/api/listings?page=1\&page_size=5

# Register → login → /users/me (round-trip)
# (Use a throwaway email; expect 201, 200, 200.)
```

---

## 8. Rollback

| Layer | Command |
|-------|---------|
| Vercel | Dashboard → Deployments → **Promote** previous build |
| Fly.io | `fly releases` → `fly deploy --image registry.fly.io/...:<previous>` |
| Mongo schema | Re-run reverse migration from the last `/backend/migrations/` script |

Rollback should take **under 5 minutes** for app code; DB rollbacks are an explicit incident.
