# Frontend Theme — Dark Luxury

This document explains the **typography**, **colour system**, and **motion budget** that make the Hils Marketing UI feel premium without veering into kitsch. Every decision here is reflected in:

- `frontend/tailwind.config.js` — design tokens as Tailwind utilities
- `frontend/src/index.css` — CSS variable definitions + reduced-motion baseline
- `shared/constants.js` — exported `THEME` object used by both frontend and (mirrored to) backend
- `.cursor/rules/project-context.mdc` — agent-facing summary of the same values

If you change a token in one place, update **all four**. They are deliberately kept in lockstep.

---

## 1. Typography

### Cormorant Garamond — display / headings

A Garamond-derived serif with high contrast strokes and pronounced bracketed serifs. We use it for every `<h1>`–`<h6>` plus hero copy.

**Why it reads as "luxury" for the PK real-estate audience:**

- Garamond family is the default visual language of high-end property catalogues and architecture monographs (Christie's, Sotheby's, Architectural Digest).
- The condensed-but-tall x-height keeps headlines elegant at large sizes without feeling cramped.
- Locally familiar — DAWN's premium supplements, *Libas*, and most Pakistani luxury collateral use Garamond-family fonts. It signals "considered" rather than "transactional" the way a sans-only headline would.

### Outfit — body / UI

A geometric sans with subtle humanist warmth. Used for **everything** that isn't a heading: body copy, navigation, buttons, form inputs, tabular data.

**Why this specific sans:**

- Lighter weights (300, 400) are crisp at small sizes on Pakistani 96–120 dpi displays, which still dominate the market.
- The wide aperture on `a`/`e`/`g` keeps Roman numerals and currency strings (`Rs 18,50,00,000`) legible — important when listing prices are the primary content.
- Open-source (SIL OFL) — no licensing risk for client-side use, no enterprise font-server overhead.
- Pairs well with Garamond's high contrast: Outfit's even stroke contrast provides visual rest between dense Cormorant headlines.

### The pairing rule

Headings = Cormorant. Everything else = Outfit. Don't mix more weights than these on a single page:

| Element | Family | Weight |
|---------|--------|--------|
| H1 | Cormorant | 500 |
| H2–H4 | Cormorant | 500 |
| Body | Outfit | 400 |
| Eyebrow / uppercase label | Outfit | 500, `tracking-eyebrow` |
| Button label | Outfit | 500, uppercase |

Both fonts are loaded from Google Fonts in a **single** `@import` at the top of `index.css` (one HTTP request, `display=swap` so text paints immediately with the system fallback while the webfont downloads).

---

## 2. Colour system — why CSS variables, not hex

The Tailwind config maps every brand colour to a CSS custom property:

```js
// tailwind.config.js (excerpt)
colors: {
  background: 'rgb(var(--bg-obsidian) / <alpha-value>)',
  primary:    'rgb(var(--accent-champagne) / <alpha-value>)',
  ...
}
```

And the variables are defined once in `index.css`:

```css
:root {
  --bg-obsidian:    5 5 5;          /* #050505 */
  --accent-champagne: 212 175 55;   /* #D4AF37 */
  ...
}
```

### Why space-separated RGB triplets?

So Tailwind's **`<alpha-value>`** substitution works:

```html
<div class="bg-primary/20"></div>   <!-- becomes rgb(212 175 55 / 0.2) -->
```

Without the triplet format you'd have to pre-bake every opacity you want into the config — that's dozens of extra utility classes and a maintenance trap.

### Why CSS variables at all?

Three real wins:

1. **Theme switching at runtime, zero rebuild.** A future "Hils Light" or seasonal palette becomes one CSS rule:
   ```css
   :root[data-theme="light"] {
     --bg-obsidian: 250 250 245;
     --text-high:     12 12 12;
     ...
   }
   ```
   Toggling `<html data-theme="light">` swaps the entire UI. Tailwind utilities don't need to know.

2. **Brand operations can override without touching JS.** Marketing can rebrand a sub-route by setting variables on a parent element — no React state, no prop drilling.

3. **Print / high-contrast accessibility modes** can override variables in `@media` queries without re-rendering anything.

### Palette reference

| Token | Hex | Semantic use |
|-------|-----|--------------|
| `--bg-obsidian` | `#050505` | Page background. Never put pure black `#000000` next to it — it disappears. |
| `--surface-raised` | `#141414` | Cards, sticky navbars, hover surfaces |
| `--surface-elevated` | `#1A1A1A` | Modals, popovers, dropdown menus |
| `--accent-champagne` | `#D4AF37` | Primary CTAs, key icons, gold borders. **Use sparingly** — one champagne element per viewport. |
| `--accent-champagne-on` | `#050505` | Text rendered ON a champagne background (CTA labels) |
| `--text-high` | `#FFFFFF` | Primary text |
| `--text-muted` | `#A1A1AA` | Captions, secondary text, helper copy |
| `--border-subtle` | `#262626` | Hairline dividers |

---

## 3. Motion budget

Premium ≠ slow. Luxury brands use **fewer, faster, more deliberate** animations than mass-market apps.

### Duration guide

| Interaction | Duration | Easing | Where |
|-------------|----------|--------|-------|
| Button hover / tap | **120 ms** | `easeOut` | `components/ui/Button.jsx` |
| Hover state on link, card, icon | **180 ms** | CSS `transition-colors` | Tailwind `duration-base` |
| Page-level enter/exit (route change) | **240 ms** | `easeInOut` | `AnimatePresence` in layout (planned) |
| Modal / dialog open | **200 ms** | `easeOut` | Radix `<Dialog>` (default is fine) |
| Skeleton / shimmer loop | 1500 ms | linear | only when network is the bottleneck |

**Hard rule: micro-interactions stay under 200 ms.** Anything above that registers as "slow" rather than "smooth" — the user starts to wait instead of feeling responsive.

These tokens are also encoded in Tailwind as `duration-fast` (120 ms) and `duration-base` (180 ms), so component code can stay declarative:

```jsx
<button className="transition-colors duration-base hover:text-primary" />
```

### Reduced-motion handling — two layers

1. **CSS layer** (`index.css`):
   ```css
   @media (prefers-reduced-motion: reduce) {
     *, *::before, *::after {
       animation-duration: 0.001ms !important;
       transition-duration: 0.001ms !important;
     }
   }
   ```
   This disables every CSS transition site-wide for users who've asked the OS for reduced motion.

2. **JS layer** (`hooks/usePrefersReducedMotion.js`):
   Framer Motion orchestrates animations from JS, so CSS rules don't reach them. The hook returns `true`/`false` and components gate their variants:
   ```jsx
   const reduced = usePrefersReducedMotion();
   <motion.button whileHover={reduced ? undefined : { scale: 1.02 }} />
   ```

Both layers are mandatory. Don't ship a Framer Motion component without consulting the hook.

---

## 4. Token-change checklist

When you change a brand token (colour, font, duration):

- [ ] Update `frontend/src/index.css` (the source of truth for the running site)
- [ ] Update `frontend/tailwind.config.js` if the *name* of the token changed
- [ ] Update `shared/constants.js` `THEME` export
- [ ] Update the table in `.cursor/rules/project-context.mdc`
- [ ] Update this doc's palette / motion / typography section
- [ ] Bump the visual-regression baseline if Chromatic / Percy is wired in

Skipping step 4 is the most common drift source — the agent will then keep suggesting old values in new components.
