# `frontend/src/components/`

Reusable presentational and behavioural components.

## Convention

- **One file per component**, named in `PascalCase` (`ListingCard.jsx`).
- Co-locate small subcomponents in the same file; promote to their own file once reused.
- Shadcn/ui primitives live under `components/ui/` and are customized to the dark-luxury theme.
- Every interactive element gets a kebab-case `data-testid`:
  ```jsx
  <button data-testid="listing-card-favorite" />
  ```
- Use named exports (default export only for page modules).

## Suggested groups

- `components/ui/` — Shadcn primitives (Button, Card, Dialog, …)
- `components/layout/` — Header, Footer, Container
- `components/listings/` — ListingCard, ListingGrid, ListingMap
- `components/forms/` — Input wrappers, FormField, ZodForm
