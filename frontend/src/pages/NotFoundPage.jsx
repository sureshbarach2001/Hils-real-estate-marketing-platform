import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/Button.jsx';

export default function NotFoundPage() {
  return (
    <section className="mx-auto max-w-md px-6 py-32 text-center">
      <p className="eyebrow">404</p>
      <h1 className="mt-4 text-5xl font-display">Page not found</h1>
      <p className="mt-4 text-muted">
        The page you are looking for has moved or no longer exists.
      </p>
      <div className="mt-8 flex justify-center">
        <Button asChild variant="secondary" size="md">
          <Link to="/" data-testid="not-found-back-home">Back to home</Link>
        </Button>
      </div>
    </section>
  );
}
