/**
 * Lightweight client-side password strength scorer.
 *
 * Returns an integer 0..4 used by the `<PasswordStrength>` bar in Signup.
 * This is UX feedback only — the server still enforces the real rules
 * (min length, hashing) in `routes/auth.py`. Never gate submission on the
 * client score alone.
 *
 *   0 — empty / unusable
 *   1 — meets the 8-char floor
 *   2 — 12+ chars
 *   3 — also mixes upper + lower case
 *   4 — also has a digit AND a symbol
 */

export function scorePassword(pwd) {
  if (!pwd) return 0;
  let score = 0;
  if (pwd.length >= 8) score++;
  if (pwd.length >= 12) score++;
  if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score++;
  if (/\d/.test(pwd) && /[^A-Za-z0-9]/.test(pwd)) score++;
  return Math.min(score, 4);
}

export const STRENGTH_LABELS = [
  'Too weak',
  'Weak',
  'Fair',
  'Strong',
  'Excellent',
];
