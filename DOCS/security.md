# Security

Concrete, enforceable security model for the Hils Marketing platform. The agent rule `.cursor/rules/security.mdc` is the **short** version; this doc is the long version.

---

## 1. Threat model (in scope)

| Threat | Mitigation |
|--------|-----------|
| Credential stuffing on `/auth/login` | Bcrypt + rate-limit 5/15 min/IP + generic "invalid credentials" message |
| Session theft via XSS | httpOnly cookies — JS cannot read tokens. CSP headers on the frontend. |
| CSRF on cookie-auth requests | SameSite=Lax cookies + state-changing endpoints require JSON content-type (browsers don't send `Content-Type: application/json` from cross-origin forms by default) |
| SQL/NoSQL injection | Pydantic validation + Motor parameterized queries (no raw `$where`) |
| Card data leakage | **Never** handled by us — Stripe Checkout only |
| Webhook spoofing | `stripe.Webhook.construct_event` with `STRIPE_WEBHOOK_SECRET` |
| Replay attacks on webhooks | Idempotency keyed on `event.id` stored in `payments.stripe_event_id` (unique index) |
| Account enumeration on `/forgot-password` | Always return `204` regardless of whether the email exists |
| PII in logs | Structured logging with allow-listed fields; passwords/tokens/CNIC explicitly redacted |

---

## 2. Authentication

### Passwords

- Hashing: **bcrypt** (`passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")`)
- Cost factor: default 12; revisit yearly.
- Min length: 10 chars; rejected if found in HIBP top-100k list (optional v2).

### JWT

| Token | TTL | Storage | Rotates on |
|-------|-----|---------|-----------|
| `access_token` | 12 h | httpOnly + Secure + SameSite=Lax cookie | Issued on login / refresh |
| `refresh_token` | 7 d | httpOnly + Secure + SameSite=Lax cookie | **Every** `/auth/refresh` (rotation) |

- Algorithm: `HS256` with `JWT_SECRET_KEY` (≥ 32 random bytes).
- Claims: `sub` (user id), `iat`, `exp`, `type` (`access`|`refresh`), `jti` (rotation tracking).
- Refresh tokens are stored server-side (`sessions` collection) so we can revoke. On rotation, the old `jti` is marked `revoked`.

### Cookies

```
Set-Cookie: access_token=...;  HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=43200
Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax; Path=/api/auth/refresh; Max-Age=604800
```

In **dev** (HTTP localhost) `Secure` is dropped.

---

## 3. Input validation

- **Backend**: every endpoint accepts a Pydantic model. Models use `model_config = ConfigDict(extra="forbid")` to reject unknown fields.
- **Frontend**: every form uses a Zod schema co-located in `frontend/src/utils/schemas/`.
- **Phone numbers**: validated as Pakistani format (`+92` or `03XX`), normalised to E.164 before persistence.
- **File uploads**: validated by MIME + magic bytes; max 10 MB per image.

---

## 4. Stripe

- **No raw card data** — ever. Frontend redirects to Stripe Checkout; we receive the result via webhook.
- Webhook handler:
  1. Reads raw body (do **not** parse before signature check).
  2. `stripe.Webhook.construct_event(body, sig_header, STRIPE_WEBHOOK_SECRET)`.
  3. Upserts `payments` by `(stripe_event_id)` — unique index makes the operation idempotent.
- Live and test keys live in separate env vars; CI must never have access to live keys.

---

## 5. Rate limiting

`slowapi` middleware with per-IP keys.

| Group | Limit |
|-------|-------|
| `/api/auth/*` | 5 / 15 minutes |
| `/api/listings` GET | 60 / minute |
| `/api/listings` POST/PATCH/DELETE | 20 / minute |
| `/api/payments/*` | 30 / minute |
| everything else | 120 / minute |

Exceeded → `429 Too Many Requests` with `Retry-After` header.

---

## 6. CORS

- Origins from `CORS_ORIGINS` env (comma-separated).
- Production default: only `https://hils.pk` (and any explicitly approved subdomains).
- `allow_credentials=True` is mandatory for cookie auth — **so wildcard `*` is forbidden**.

---

## 7. Logging & PII

**Never log**: plaintext or hashed passwords, full JWTs (mask to first 6 chars + `...`), Stripe API keys, CNICs, full names paired with phone/email, full IBANs.

**Always log**: request id, user id (Mongo `_id`), endpoint + method, status code, latency.

Use structured JSON logs with an allow-list. Stack traces go to Sentry, **not** stdout in production.

---

## 8. Secrets

- All secrets in `.env` (local) or the provider's secret manager (production). Never in source.
- `.env.example` lists every variable with empty/placeholder values.
- Rotate `JWT_SECRET_KEY`, `STRIPE_*`, and SMTP credentials **at least every 90 days** and immediately if a leak is suspected.
- Loaded + validated on startup via `pydantic-settings` (`BaseSettings`). Missing required keys → process refuses to boot.
