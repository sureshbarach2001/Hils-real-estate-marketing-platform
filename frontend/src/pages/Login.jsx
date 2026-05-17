/**
 * /login — sign in to an existing account.
 *
 * Approach:
 *   1. react-hook-form + zodResolver — single source of truth for validation.
 *   2. Mode "onTouched" — errors appear after the user leaves a field,
 *      not while typing (premium feel, less noisy).
 *   3. On submit: POST /api/auth/login via the shared `api` client (cookies
 *      flow automatically thanks to withCredentials), then navigate to /dashboard.
 *   4. Per-field errors come from Zod; the top-level banner shows the
 *      backend's HTTPException detail (401 invalid credentials, 429 locked).
 *   5. Section fades + lifts in on mount; respects prefers-reduced-motion.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { GoogleLogo } from '@phosphor-icons/react';

import { Button } from '@/components/ui/Button.jsx';
import { Input } from '@/components/ui/Input.jsx';
import { api, extractError } from '@/lib/api.js';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion.js';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email.'),
  password: z.string().min(8, 'Password must be at least 8 characters.'),
});

export default function Login() {
  const navigate = useNavigate();
  const reduced = usePrefersReducedMotion();
  const [submitError, setSubmitError] = useState(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
    mode: 'onTouched',
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (values) => {
    setSubmitError(null);
    try {
      await api.post('/api/auth/login', values);
      navigate('/dashboard', { replace: true });
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
      data-testid="login-page"
    >
      <p className="eyebrow">Welcome back</p>
      <h1 className="mt-4 text-4xl font-display">Sign in</h1>
      <p className="mt-3 text-sm text-muted">
        New here?{' '}
        <Link
          to="/signup"
          className="text-primary hover:underline"
          data-testid="login-signup-link"
        >
          Create an account
        </Link>
        .
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
          data-testid="login-email-input"
          error={errors.email?.message}
          {...register('email')}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          placeholder="At least 8 characters"
          data-testid="login-password-input"
          error={errors.password?.message}
          {...register('password')}
        />

        <div className="-mt-1 flex items-center justify-end">
          <Link
            to="/forgot-password"
            className="text-xs text-muted hover:text-primary"
            data-testid="login-forgot-link"
          >
            Forgot password?
          </Link>
        </div>

        {submitError && (
          <p
            role="alert"
            className="border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200"
            data-testid="login-error"
          >
            {submitError}
          </p>
        )}

        <Button
          type="submit"
          variant="primary"
          size="lg"
          disabled={isSubmitting}
          data-testid="login-submit-button"
          className="mt-2"
        >
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </Button>

        <Button
          type="button"
          variant="secondary"
          size="lg"
          disabled
          aria-disabled="true"
          title="Coming soon"
          data-testid="login-google-button"
        >
          <GoogleLogo size={18} weight="bold" />
          Continue with Google (coming soon)
        </Button>
      </form>
    </motion.section>
  );
}
