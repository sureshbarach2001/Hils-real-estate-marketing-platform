# `frontend/src/pages/`

Top-level route views, wired up in the router.

## Convention

- **One file per route**, `PascalCase.jsx` (`HomePage.jsx`, `ListingDetailPage.jsx`).
- Pages use **default exports** (router config imports them lazily).
- Pages compose components from `components/` — they should contain almost no styling of their own beyond layout.
- Each page sets its document title via a `useDocumentTitle("...")` hook.

## Planned pages

| File | Route |
|------|-------|
| `HomePage.jsx` | `/` |
| `ListingsPage.jsx` | `/listings` |
| `ListingDetailPage.jsx` | `/listings/:slug` |
| `LoginPage.jsx` | `/login` |
| `RegisterPage.jsx` | `/register` |
| `DashboardPage.jsx` | `/dashboard` |
| `PaymentSuccessPage.jsx` | `/payments/success` |
