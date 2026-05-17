/**
 * PasswordStrength — four-segment bar driven by `scorePassword`.
 *
 * Gold segments fill as the password meets each tier (length, length+,
 * mixed case, digit+symbol). The label below summarises the score and
 * gives concrete guidance when the field is empty.
 *
 * Pure presentational — never gates form submission. The Zod schema in
 * Signup enforces the hard floor (min 8 chars); the server enforces the
 * real rule.
 */

import { cn } from '@/lib/cn.js';
import { scorePassword, STRENGTH_LABELS } from '@/lib/passwordStrength.js';

export function PasswordStrength({ value, testid = 'password-strength' }) {
  const score = scorePassword(value);
  const label = STRENGTH_LABELS[score];

  return (
    <div className="flex flex-col gap-1.5" data-testid={testid}>
      <div className="flex gap-1.5" aria-hidden="true">
        {[0, 1, 2, 3].map((i) => (
          <span
            key={i}
            className={cn(
              'h-1 flex-1 rounded-sharp transition-colors duration-base',
              i < score ? 'bg-primary' : 'bg-white/10',
            )}
          />
        ))}
      </div>
      <p className="text-xs text-muted" data-testid={`${testid}-label`}>
        {value
          ? `Strength: ${label}`
          : 'Use 8+ characters, mixed case, a number, and a symbol.'}
      </p>
    </div>
  );
}
