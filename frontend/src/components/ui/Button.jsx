/**
 * Button — the only place we orchestrate primary, secondary, and ghost
 * intents. Three variants, three sizes, optional Framer Motion hover.
 *
 * Approach:
 *   1. `class-variance-authority` builds the class string from variant +
 *      size props, so JSX call sites stay short and consistent.
 *   2. Wrapped in `motion.button` so we can co-locate hover/tap micro-
 *      interactions with the visual styles. The animation is gated on
 *      `usePrefersReducedMotion()` to honour OS-level a11y preference.
 *   3. `asChild` (via Radix Slot) lets a `<Link>` or `<a>` adopt these
 *      styles without nesting — e.g. `<Button asChild><Link/></Button>`.
 *
 * Motion budget (see DOCS/frontend-theme.md §motion):
 *   - hover scale: 1.02, 120ms — perceptible but not playful
 *   - tap scale:   0.98, 80ms  — gives mechanical "click" feedback
 *   - no entry / exit animations on the button itself; let the parent
 *     section orchestrate that with AnimatePresence if needed.
 */

import { forwardRef } from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva } from 'class-variance-authority';
import { motion } from 'framer-motion';

import { cn } from '@/lib/cn.js';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion.js';

const buttonVariants = cva(
  // Base styles applied to every variant
  [
    'inline-flex items-center justify-center gap-2',
    'font-sans font-medium uppercase tracking-eyebrow',
    'rounded-sharp select-none whitespace-nowrap',
    'transition-colors duration-base',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background',
    'disabled:pointer-events-none disabled:opacity-50',
  ].join(' '),
  {
    variants: {
      variant: {
        // Champagne gold — main call to action. Use ONCE per viewport.
        primary: [
          'bg-primary text-primary-foreground',
          'hover:bg-primary/90',
        ].join(' '),
        // Outline with gold border — secondary CTA or "learn more"
        secondary: [
          'bg-transparent text-foreground',
          'border border-primary/70',
          'hover:border-primary hover:bg-primary/10',
        ].join(' '),
        // Quietest — text-only, no border. Use for nav, footer, tertiary actions.
        ghost: [
          'bg-transparent text-foreground',
          'hover:bg-primary/10 hover:text-primary',
        ].join(' '),
      },
      size: {
        sm: 'h-9 px-4 text-xs',
        md: 'h-11 px-6 text-sm',
        lg: 'h-14 px-9 text-sm',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  },
);

const MotionButton = motion.button;

/**
 * @param {object} props
 * @param {'primary'|'secondary'|'ghost'} [props.variant='primary']
 * @param {'sm'|'md'|'lg'} [props.size='md']
 * @param {boolean} [props.asChild=false]   render styles into a child element (e.g. Link)
 * @param {string} [props.className]
 * @param {React.ReactNode} props.children
 */
const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', asChild = false, className, children, ...rest },
  ref,
) {
  const reduced = usePrefersReducedMotion();
  const classes = cn(buttonVariants({ variant, size }), className);

  if (asChild) {
    return (
      <Slot ref={ref} className={classes} {...rest}>
        {children}
      </Slot>
    );
  }

  return (
    <MotionButton
      ref={ref}
      className={classes}
      whileHover={reduced ? undefined : { scale: 1.02 }}
      whileTap={reduced ? undefined : { scale: 0.98 }}
      transition={{ duration: 0.12, ease: 'easeOut' }}
      {...rest}
    >
      {children}
    </MotionButton>
  );
});

export { Button, buttonVariants };
