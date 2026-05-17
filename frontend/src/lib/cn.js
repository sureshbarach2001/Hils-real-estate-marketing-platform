import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Concatenate Tailwind class names, deduplicating conflicting utilities.
 *
 * `clsx` handles conditional classes (objects, arrays, falsy values),
 * `twMerge` ensures `bg-red-500` is overridden when you append `bg-blue-500`
 * later in the list — so component variants compose cleanly with overrides.
 *
 * @example
 *   cn('px-4 py-2', isActive && 'bg-primary', className)
 *
 * @param  {...any} inputs
 * @returns {string}
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
