import { useEffect, useState } from 'react';

const QUERY = '(prefers-reduced-motion: reduce)';

/**
 * Returns `true` if the user has requested reduced motion at the OS level.
 *
 * Use this inside Framer Motion components to skip orchestrated enter/exit
 * animations:
 *
 *     const reduced = usePrefersReducedMotion();
 *     <motion.div animate={reduced ? false : { opacity: 1 }} />
 *
 * CSS transitions are also disabled globally in `index.css` via a
 * `@media (prefers-reduced-motion: reduce)` block — this hook covers the
 * JS-orchestrated case (Framer Motion variants, AnimatePresence, etc.).
 *
 * Safe during SSR: defaults to `false` if `window` is unavailable.
 *
 * @returns {boolean}
 */
export function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return false;
    return window.matchMedia(QUERY).matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return undefined;
    const mql = window.matchMedia(QUERY);
    const onChange = (event) => setReduced(event.matches);
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, []);

  return reduced;
}
