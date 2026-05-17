/**
 * /signup — create a new customer account.
 *
 * Approach:
 *   1. react-hook-form + Zod for client-side validation. Mirrors the
 *      backend's RegisterRequest (email, password>=8, name 2..120, optional
 *      PK phone — required here for UX).
 *   2. `watch('password')` drives the live <PasswordStrength> bar.
 *   3. A required terms checkbox gates submission (`z.literal(true)`).
 *   4. Server-side per-field errors (Pydantic 422) are merged back into
 *      RHF with `setError`, so phone-format or duplicate-email problems
 *      land on the right field.
 *   5. Section fades in via Framer Motion; honours prefers-reduced-motion.
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
import { PasswordStrength } from '@/components/ui/PasswordStrength.jsx';
import { api, extractError } from '@/lib/api.js';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion.js';

const PK_PHONE = /^(?:\+?92|0)3\d{9}$/;

const signupSchema = z.object({
  name: z
    .string()
    .min(2, 'Name must be at least 2 characters.')
    .max(120, 'Name must be 120 characters or fewer.'),
  email: z.string().email('Please enter a valid email.'),
  phone: z
    .string()
    .regex(PK_PHONE, 'Use a Pakistani mobile (+92XXXXXXXXXX or 03XXXXXXXXX).'),
  password: z.string().min(8, 'Password must be at least 8 characters.'),
  acceptTerms: z.literal(true, {
    errorMap: () => ({ message: 'You must accept the terms to continue.' }),
  }),
});

export default function Signup() {
  const navigate = useNavigate();
  const reduced = usePrefersReducedMotion();
  const [submitError, setSubmitError] = useState(null);

  const {
    register,
    handleSubmit,
    watch,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(signupSchema),
    mode: 'onTouched',
    defaultValues: {
      name: '',
      email: '',
      phone: '',
      password: '',
      acceptTerms: false,
    },
  });

  const passwordValue = watch('password');

  const onSubmit = async (values) => {
    setSubmitError(null);
    const { acceptTerms: _ignored, ...payload } = values;
    try {
      await api.post('/api/auth/register', payload);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      const apiErr = extractError(err);
      if (apiErr.fields) {
        for (const [field, message] of Object.entries(apiErr.fields)) {
          setError(field, { type: 'server', message });
        }
      }
      setSubmitError(apiErr.message);
    }
  };

  return (
    <motion.section
      initial={reduced ? false : { opacity: 0, y: 12 }}
      animate={reduced ? undefined : { opacity: 1, y: 0 }}
      transition={{ duration: 0.32, ease: 'easeOut' }}
      className="mx-auto max-w-md px-6 py-20"
      data-testid="signup-page"
    >
      <p className="eyebrow">Create account</p>
      <h1 className="mt-4 text-4xl font-display">Join Hils</h1>
      <p className="mt-3 text-sm text-muted">
        Already a member?{' '}
        <Link
          to="/login"
          className="text-primary hover:underline"
          data-testid="signup-login-link"
        >
          Sign in
        </Link>
        .
      </p>

      <form
        className="mt-10 flex flex-col gap-5"
        onSubmit={handleSubmit(onSubmit)}
        noValidate
      >
        <Input
          label="Full name"
          type="text"
          autoComplete="name"
          placeholder="Ali Raza"
          data-testid="signup-name-input"
          error={errors.name?.message}
          {...register('name')}
        />
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="you@hils.pk"
          data-testid="signup-email-input"
          error={errors.email?.message}
          {...register('email')}
        />
        <Input
          label="Mobile (Pakistan)"
          type="tel"
          autoComplete="tel"
          placeholder="+923001234567"
          data-testid="signup-phone-input"
          error={errors.phone?.message}
          {...register('phone')}
        />

        <div className="flex flex-col gap-2">
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            placeholder="At least 8 characters"
            data-testid="signup-password-input"
            error={errors.password?.message}
            {...register('password')}
          />
          <PasswordStrength
            value={passwordValue}
            testid="signup-password-strength"
          />
        </div>

        <label className="mt-2 flex items-start gap-3 text-sm text-muted">
          <input
            type="checkbox"
            className="mt-0.5 h-4 w-4 cursor-pointer rounded-sharp border border-white/20 bg-[#0A0A0A] accent-primary"
            data-testid="signup-terms-checkbox"
            aria-describedby={errors.acceptTerms ? 'signup-terms-err' : undefined}
            {...register('acceptTerms')}
          />
          <span>
            I agree to the{' '}
            <Link to="/terms" className="text-primary hover:underline">
              terms of service
            </Link>{' '}
            and{' '}
            <Link to="/privacy" className="text-primary hover:underline">
              privacy policy
            </Link>
            .
          </span>
        </label>
        {errors.acceptTerms && (
          <p
            id="signup-terms-err"
            role="alert"
            className="-mt-3 text-xs text-red-400"
            data-testid="signup-terms-error"
          >
            {errors.acceptTerms.message}
          </p>
        )}

        {submitError && (
          <p
            role="alert"
            className="border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200"
            data-testid="signup-error"
          >
            {submitError}
          </p>
        )}

        <Button
          type="submit"
          variant="primary"
          size="lg"
          disabled={isSubmitting}
          data-testid="signup-submit-button"
          className="mt-2"
        >
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </Button>

        <Button
          type="button"
          variant="secondary"
          size="lg"
          disabled
          aria-disabled="true"
          title="Coming soon"
          data-testid="signup-google-button"
        >
          <GoogleLogo size={18} weight="bold" />
          Continue with Google (coming soon)
        </Button>
      </form>
    </motion.section>
  );
}
