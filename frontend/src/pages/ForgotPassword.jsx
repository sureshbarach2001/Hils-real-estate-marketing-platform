/**
 * /forgot-password — start the password-reset flow.
 *
 * Always shows a success message regardless of whether the email exists,
 * to mirror the backend's anti-enumeration response (POST returns 204 in
 * both cases). The wording is deliberately neutral.
 *
 * In `APP_ENV=development` the backend logs the reset token to stdout so
 * the dev can grab it without a real SMTP integration.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';

import { Button } from '@/components/ui/Button.jsx';
import { Input } from '@/components/ui/Input.jsx';
import { api, extractError } from '@/lib/api.js';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion.js';

const forgotSchema = z.object({
  email: z.string().email('Please enter a valid email.'),
});

export default function ForgotPassword() {
  const reduced = usePrefersReducedMotion();
  const [submitted, setSubmitted] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(forgotSchema),
    mode: 'onTouched',
    defaultValues: { email: '' },
  });

  const onSubmit = async (values) => {
    setSubmitError(null);
    try {
      await api.post('/api/auth/forgot-password', values);
      setSubmitted(true);
    } catch (err) {
      // Backend should always 204; only network / 5xx land here.
      setSubmitError(extractError(err).message);
    }
  };

  return (
    <motion.section
      initial={reduced ? false : { opacity: 0, y: 12 }}
      animate={reduced ? undefined : { opacity: 1, y: 0 }}
      transition={{ duration: 0.32, ease: 'easeOut' }}
      className="mx-auto max-w-md px-6 py-20"
      data-testid="forgot-password-page"
    >
      <p className="eyebrow">Account recovery</p>
      <h1 className="mt-4 text-4xl font-display">Forgot password</h1>

      {submitted ? (
        <div className="mt-8 flex flex-col gap-6" data-testid="forgot-success">
          <p className="border border-primary/30 bg-primary/5 px-4 py-4 text-sm text-foreground">
            If an account exists for that email, we have sent a reset link.
            Please check your inbox (and spam folder).
          </p>
          <Button asChild variant="secondary" size="md">
            <Link to="/login" data-testid="forgot-back-to-login">
              Back to sign in
            </Link>
          </Button>
        </div>
      ) : (
        <>
          <p className="mt-3 text-sm text-muted">
            Enter the email you registered with — we&apos;ll send a link to
            choose a new password.
          </p>

          <form
            className="mt-10 flex flex-col gap-5"
            onSubmit={handleSubmit(onSubmit)}
            noValidate
          >
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="you@hils.pk"
              data-testid="forgot-email-input"
              error={errors.email?.message}
              {...register('email')}
            />

            {submitError && (
              <p
                role="alert"
                className="border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200"
                data-testid="forgot-error"
              >
                {submitError}
              </p>
            )}

            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={isSubmitting}
              data-testid="forgot-submit-button"
              className="mt-2"
            >
              {isSubmitting ? 'Sending…' : 'Send reset link'}
            </Button>

            <Link
              to="/login"
              className="text-center text-xs text-muted hover:text-primary"
              data-testid="forgot-back-link"
            >
              Back to sign in
            </Link>
          </form>
        </>
      )}
    </motion.section>
  );
}
