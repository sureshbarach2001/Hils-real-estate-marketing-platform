# API Reference

Base URL: `http://localhost:8000` (dev) or `https://api.hils.pk` (prod).
All endpoints are prefixed with `/api`. Auth uses **httpOnly cookies** — the browser sends them automatically when the frontend uses `fetch(..., { credentials: 'include' })`.

> **Status:** skeleton — endpoints listed here are *planned*. Each must be filled in when its route module lands. See [`./architecture.md`](./architecture.md) §4 for the contract conventions.

---

## Conventions

- **Success bodies** are JSON, snake_case.
- **Errors**: `{ "detail": "human-readable message" }` plus an HTTP status:
  - `400` Pydantic validation failed
  - `401` no / expired token
  - `403` authenticated but not allowed
  - `404` resource missing
  - `409` conflict (e.g. duplicate email)
  - `422` semantic validation error
  - `429` rate-limited (with `Retry-After` header)
- **Pagination**: `?page=1&page_size=20`. Response: `{ items: [...], total, page, page_size }`.
- **Sorting**: `?sort=field,-other_field` (`-` prefix = descending).

---

## Auth — `/api/auth`

Login rate-limited to **5 attempts per IP+email per 15 min** (see `DOCS/auth.md`).

| Method | Path | Auth | Body | Returns |
|--------|------|------|------|---------|
| `POST` | `/api/auth/register` | — | `{ email, password, name, phone? }` | `201 Token` + sets cookies |
| `POST` | `/api/auth/login` | — | `{ email, password }` | `200 Token` + sets cookies |
| `POST` | `/api/auth/logout` | any cookie | — | `204` + clears cookies |
| `GET`  | `/api/auth/me` | access | — | `200 UserResponse` |
| `POST` | `/api/auth/forgot-password` | — | `{ email }` | `204` (always — no email enumeration) |
| `POST` | `/api/auth/reset-password` | — | `{ token, new_password }` | `204` |

> Planned: `POST /api/auth/refresh` (refresh-token rotation). Tracked in `DOCS/auth.md §9`.

---

## Users — `/api/users`

| Method | Path | Auth | Body | Returns |
|--------|------|------|------|---------|
| `GET` | `/api/users/me` | access | — | `UserOut` |
| `PATCH` | `/api/users/me` | access | `UserUpdate` (partial) | `UserOut` |
| `DELETE` | `/api/users/me` | access | — | `204` |

---

## Properties — `/api/properties` & `/api/admin/properties`

Full reference + storage model: [`./properties.md`](./properties.md).

### Public catalogue

| Method | Path | Auth | Returns |
|--------|------|------|---------|
| `GET` | `/api/properties` | — | `PropertyResponse[]` — only `status="active"`; filters: `city`, `purpose=buy\|rent`, `property_type=house\|apartment\|plot\|commercial`, `min_price`, `max_price`, `bedrooms`, `featured`, `q` (text), `lat`+`lng`+`radius_km` (geo), `limit` |
| `GET` | `/api/properties/{property_id}` | — | `PropertyResponse` — 404 if not active |

### Admin write surface

All routes require `role="admin"` (see `utils/security.py::require_admin`).

| Method | Path | Body | Returns |
|--------|------|------|---------|
| `POST` | `/api/admin/properties` | `PropertyCreate` | `201 PropertyResponse` — server generates `property_id` UUID |
| `PUT` | `/api/admin/properties/{property_id}` | `PropertyUpdate` (partial) | `200 PropertyResponse`; `400` on empty body |
| `DELETE` | `/api/admin/properties/{property_id}` | — | `204` — soft delete, flips `status="inactive"` |

---

## Payments — `/api/payments`

| Method | Path | Auth | Body | Returns |
|--------|------|------|------|---------|
| `POST` | `/api/payments/checkout-session` | access | `{ listing_id, plan: "boost_7d" \| "boost_30d" }` | `{ url }` — redirect to Stripe |
| `POST` | `/api/payments/webhook` | Stripe signature | raw event body | `200 {received: true}` |
| `GET` | `/api/payments/me` | access | — | Paginated `PaymentOut[]` |

> The webhook **must** verify `stripe-signature` using `STRIPE_WEBHOOK_SECRET` and be idempotent on `event.id`.

---

## Media — `/api/media`

| Method | Path | Auth | Body | Returns |
|--------|------|------|------|---------|
| `POST` | `/api/media/sign-upload` | access | `{ listing_id, filename, mime }` | `{ url, fields, public_url }` — POST directly to storage |
| `DELETE` | `/api/media/{id}` | owner / admin | — | `204` |

---

## Meta

| Method | Path | Auth | Returns |
|--------|------|------|---------|
| `GET` | `/api/health` | — | `{ status: "ok", service: "hils-marketing-api" }` |
