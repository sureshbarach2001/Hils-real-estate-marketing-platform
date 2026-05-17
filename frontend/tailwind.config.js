/**
 * Hils Marketing — Tailwind config (dark luxury theme).
 *
 * Approach:
 *   1. Map every brand colour to a CSS custom property (defined in
 *      `src/index.css`). Tailwind utilities (`bg-background`, `text-primary`,
 *      ...) therefore resolve to `var(--bg-obsidian)` etc. This is what makes
 *      future theme switching (light mode, alternate brand) a single CSS
 *      variable swap with zero JS / no rebuild.
 *   2. Pair a refined serif (Cormorant Garamond) for display with a clean
 *      geometric sans (Outfit) for body — see DOCS/frontend-theme.md for
 *      why this combination reads as "premium" in PK real-estate context.
 *   3. Keep the default Tailwind border-radius scale (which includes
 *      `rounded-none`) and add a semantic `sharp` token so component code
 *      can say `rounded-sharp` instead of `rounded-none` — sharp edges are
 *      the brand default, so naming the intent matters.
 */

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Brand surfaces
        background: 'rgb(var(--bg-obsidian) / <alpha-value>)',
        surface: {
          DEFAULT: 'rgb(var(--surface-raised) / <alpha-value>)',
          elevated: 'rgb(var(--surface-elevated) / <alpha-value>)',
        },

        // Primary accent — champagne gold, used sparingly for CTAs + highlights
        primary: {
          DEFAULT: 'rgb(var(--accent-champagne) / <alpha-value>)',
          foreground: 'rgb(var(--accent-champagne-on) / <alpha-value>)',
          soft: 'rgb(var(--accent-champagne-soft) / <alpha-value>)',
        },

        // Text
        foreground: 'rgb(var(--text-high) / <alpha-value>)',
        muted: 'rgb(var(--text-muted) / <alpha-value>)',

        // Subtle hairlines / borders
        border: 'rgb(var(--border-subtle) / <alpha-value>)',
      },

      fontFamily: {
        // `font-display` for headings, hero text, premium accents
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        // `font-sans` for body copy + UI — applied by default via base layer
        sans: ['Outfit', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },

      borderRadius: {
        // Brand default = sharp. Naming it makes intent obvious in JSX.
        sharp: '0',
        hairline: '2px',
      },

      letterSpacing: {
        // Generous tracking on uppercase eyebrows per brand voice
        eyebrow: '0.18em',
      },

      transitionDuration: {
        // Micro-interaction budget (see DOCS/frontend-theme.md §motion)
        fast: '120ms',
        base: '180ms',
      },
    },
  },
  plugins: [],
};
