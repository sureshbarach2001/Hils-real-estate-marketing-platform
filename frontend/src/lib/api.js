/**
 * Axios client + error normaliser for the Hils Marketing frontend.
 *
 * - `withCredentials: true` so the browser sends httpOnly auth cookies on
 *   every request (the backend reads them in `utils/security.py`).
 * - `extractError` turns Pydantic 422 + plain-`detail` 4xx responses into a
 *   consistent `ApiError` shape that forms can render either as a top-level
 *   banner (`message`) or per-field (`fields`).
 *
 * Usage:
 *   try {
 *     await api.post('/api/auth/login', values);
 *   } catch (err) {
 *     const apiErr = extractError(err);
 *     setError(apiErr.message);
 *     // or, for field-level:
 *     Object.entries(apiErr.fields || {}).forEach(([k, v]) => setError(k, { message: v }));
 *   }
 */

import axios from 'axios';

const baseURL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

export class ApiError extends Error {
  constructor(message, { status = 0, fields = null } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fields = fields;
  }
}

/**
 * Normalise any axios failure into a UI-renderable shape.
 *
 *  - FastAPI Pydantic 422 -> { message, fields: { email: '...', password: '...' } }
 *  - FastAPI HTTPException -> { message: detail }
 *  - Network / 5xx        -> generic message
 */
export function extractError(err) {
  if (err?.response) {
    const { status, data } = err.response;

    if (Array.isArray(data?.detail)) {
      const fields = {};
      for (const item of data.detail) {
        const loc = Array.isArray(item.loc)
          ? item.loc.filter((p) => p !== 'body')
          : [];
        const field = loc.join('.');
        if (field) fields[field] = item.msg || 'Invalid value';
      }
      return new ApiError('Please correct the errors below.', {
        status,
        fields,
      });
    }

    if (typeof data?.detail === 'string') {
      return new ApiError(data.detail, { status });
    }

    return new ApiError('Request failed. Please try again.', { status });
  }

  return new ApiError(
    err?.message || 'Network error. Check your connection and try again.',
    { status: 0 },
  );
}
