/**
 * App — top-level routing for Hils Marketing.
 *
 * Approach:
 *   1. Router-only concerns live here. Layout chrome (header / footer) will
 *     be added once those components exist in `src/components/layout/`.
 *   2. Pages are imported eagerly for now (small surface, no measurable
 *      TTI cost). Switch to `lazy(() => import(...))` per route once any
 *      route bundle exceeds ~30 KB gzip.
 *   3. The Router itself is mounted in `main.jsx` so this component stays
 *      easy to unit-test with a custom router wrapper.
 */

import { Route, Routes } from 'react-router-dom';

import HomePage from '@/pages/HomePage.jsx';
import Login from '@/pages/Login.jsx';
import Signup from '@/pages/Signup.jsx';
import ForgotPassword from '@/pages/ForgotPassword.jsx';
import ResetPassword from '@/pages/ResetPassword.jsx';
import PropertiesPage from '@/pages/PropertiesPage.jsx';
import DashboardPage from '@/pages/DashboardPage.jsx';
import AdminPage from '@/pages/AdminPage.jsx';
import NotFoundPage from '@/pages/NotFoundPage.jsx';

export default function App() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/properties" element={<PropertiesPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </main>
  );
}
