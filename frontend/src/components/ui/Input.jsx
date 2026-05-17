/**
 * Input — labelled text input with built-in error / hint slot and the
 * dark-luxury surface treatment (#0A0A0A bg, white/10 border, champagne
 * focus ring).
 *
 * Forwards `ref` so react-hook-form's `register(...)` works directly:
 *
 *   <Input label="Email" {...register('email')} error={errors.email?.message} />
 *
 * Accessibility:
 *   - <label htmlFor> matches the generated / supplied id
 *   - aria-describedby points at the error OR hint paragraph (whichever is shown)
 *   - aria-invalid mirrors the error state
 *   - the error paragraph carries role="alert" so screen readers announce it
 */

import { forwardRef, useId } from 'react';

import { cn } from '@/lib/cn.js';

export const Input = forwardRef(function Input(
  {
    label,
    error,
    hint,
    className,
    id: idProp,
    type = 'text',
    ...rest
  },
  ref,
) {
  const auto = useId();
  const id = idProp || auto;
  const errId = `${id}-err`;
  const hintId = `${id}-hint`;

  const describedBy = [error ? errId : null, hint ? hintId : null]
    .filter(Boolean)
    .join(' ') || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={id}
          className="text-xs uppercase tracking-eyebrow text-muted"
        >
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={id}
        type={type}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(
          'h-11 w-full rounded-sharp bg-[#0A0A0A] px-4 text-sm text-foreground',
          'placeholder:text-muted/60',
          'border border-white/10 transition-colors duration-base',
          'focus:outline-none focus:border-primary/50',
          'disabled:cursor-not-allowed disabled:opacity-50',
          error && 'border-red-500/60 focus:border-red-500/80',
          className,
        )}
        {...rest}
      />
      {hint && !error && (
        <p id={hintId} className="text-xs text-muted">
          {hint}
        </p>
      )}
      {error && (
        <p id={errId} role="alert" className="text-xs text-red-400">
          {error}
        </p>
      )}
    </div>
  );
});
