/**
 * /reset-password?token=... — complete the password-reset flow.
 *
 * The token arrives in the query string (raw, 32-byte URL-safe value from
 * the backend). We pass it through verbatim — the backend hashes it again
 * for lookup, so we never need to handle it client-side beyond forwarding.
 *
 * UX:
 *   - If no token is present (typed/pasted URL), show an error state.
 *   - On success, show a confirmation panel + redirect to /login after a
 *     short pause so the user can read it.
 *   - Live password match via `refine`.
 */

import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';

import { Button } from '@/components/ui/Button.jsx';
import { Input } from '@/components/ui/Input.jsx';
import { PasswordStrength } from '@/components/ui/PasswordStrength.jsx';
import { api, extractError } from '@/lib/api.js';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion.js';

const REDIRECT_DELAY_MS = 1500;

const resetSchema = z
  .object({
    password: z.string().min(8, 'Password must be at least 8 characters.'),
    confirm: z.string().min(1, 'Please confirm your new password.'),
  })
  .refine((data) => data.password === data.confirm, {
    path: ['confirm'],
    message: 'Passwords do not match.',
  });

export default function ResetPassword() {
  const reduced = usePrefersReducedMotion();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = useMemo(() => params.get('token')?.trim() || '', [params]);

  const [success, setSuccess] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(resetSchema),
    mode: 'onTouched',
    defaultValues: { password: '', confirm: '' },
  });

  const passwordValue = watch('password');

  useEffect(() => {
    if (!success) return undefined;
    const id = setTimeout(
      () => navigate('/login', { replace: true }),
      REDIRECT_DELAY_MS,
    );
    return () => clearTimeout(id);
  }, [success, navigate]);

  const onSubmit = async ({ password }) => {
    setSubmitError(null);
    try {
      await api.post('/api/auth/reset-password', { token, password });
      setSuccess(true);
    } catch (err) {
      setSubmitError(extractError(err).message);
    }
  };

  return (
    <motion.section
      initial={reduced ? false : { opacity: 0, y: 12 }}
      animate={reduced ? undefined : { opacity: 1, y: 0 }}
      transition={{ duration: 0.32, ease: 'easeOut' }}
      className="mx-auto max-w-md px-6 py-20"
      data-testid="reset-password-page"
    >
      <p className="eyebrow">Set a new password</p>
      <h1 className="mt-4 text-4xl font-display">Reset password</h1>

      {!token ? (
        <div
          className="mt-8 flex flex-col gap-6"
          data-testid="reset-missing-token"
        >
          <p className="border border-red-500/40 bg-red-500/10 px-4 py-4 text-sm text-red-200">
            This reset link is missing its token. Please request a fresh link
            from the forgot-password page.
          </p>
          <Button asChild variant="secondary" size="md">
            <Link to="/forgot-password" data-testid="reset-restart-link">
              Request a new link
            </Link>
          </Button>
        </div>
      ) : success ? (
        <div className="mt-8 flex flex-col gap-6" data-testid="reset-success">
          <p
            role="status"
            className="border border-primary/30 bg-primary/5 px-4 py-4 text-sm text-foreground"
          >
            Password updated. Redirecting you to sign in…
          </p>
          <Button asChild variant="primary" size="md">
            <Link to="/login" data-testid="reset-success-login-link">
              Continue to sign in
            </Link>
          </Button>
        </div>
      ) : (
        <>
          <p className="mt-3 text-sm text-muted">
            Choose a new password. You&apos;ll be signed out everywhere — sign
            back in with your new credentials.
          </p>

          <form
            className="mt-10 flex flex-col gap-5"
            onSubmit={handleSubmit(onSubmit)}
            noValidate
          >
            <div className="flex flex-col gap-2">
              <Input
                label="New password"
                type="password"
                autoComplete="new-password"
                placeholder="At least 8 characters"
                data-testid="reset-password-input"
                error={errors.password?.message}
                {...register('password')}
              />
              <PasswordStrength
                value={passwordValue}
                testid="reset-password-strength"
              />
            </div>

            <Input
              label="Confirm new password"
              type="password"
              autoComplete="new-password"
              placeholder="Re-type the password"
              data-testid="reset-confirm-input"
              error={errors.confirm?.message}
              {...register('confirm')}
            />

            {submitError && (
              <p
                role="alert"
                className="border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200"
                data-testid="reset-error"
              >
                {submitError}
              </p>
            )}

            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={isSubmitting}
              data-testid="reset-submit-button"
              className="mt-2"
            >
              {isSubmitting ? 'Updating…' : 'Update password'}
            </Button>

            <Link
              to="/login"
              className="text-center text-xs text-muted hover:text-primary"
              data-testid="reset-back-link"
            >
              Back to sign in
            </Link>
          </form>
        </>
      )}
    </motion.section>
  );
}
