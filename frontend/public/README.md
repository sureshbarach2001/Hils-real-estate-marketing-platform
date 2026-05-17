# `frontend/public/`

Static assets served by Vite **as-is** (no bundling, no hashing).

Use for:

- `favicon.ico`, `favicon.svg`, `apple-touch-icon.png`
- `robots.txt`, `sitemap.xml`
- Open Graph preview images
- Brand assets referenced by absolute URL

Anything that should be optimised, hashed, or imported into components belongs under `src/` instead.
