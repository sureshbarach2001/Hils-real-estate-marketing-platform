import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/Button.jsx';

export default function HomePage() {
  return (
    <section className="mx-auto max-w-5xl px-6 py-24">
      <p className="eyebrow" data-testid="home-eyebrow">Hils Marketing</p>
      <h1 className="mt-4 text-5xl md:text-7xl font-display leading-tight">
        Premium real estate, <span className="text-primary">curated for Pakistan</span>.
      </h1>
      <p className="mt-6 max-w-2xl text-muted">
        Hand-selected residences and investments across Karachi, Lahore, Islamabad,
        Rawalpindi, and Faisalabad.
      </p>

      <div className="mt-10 flex flex-wrap gap-4">
        <Button asChild variant="primary" size="lg">
          <Link to="/properties" data-testid="home-cta-explore">Explore Listings</Link>
        </Button>
        <Button asChild variant="secondary" size="lg">
          <Link to="/signup" data-testid="home-cta-join">Join the List</Link>
        </Button>
      </div>
    </section>
  );
}
