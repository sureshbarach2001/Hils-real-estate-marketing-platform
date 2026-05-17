/**
 * Shared constants for Hils Marketing.
 *
 * Pure ESM. Used by both `frontend/` and `backend/` (the backend mirrors these
 * into Python via `scripts/sync_constants.py`).
 */

/** Supported Pakistani cities for listings (primary launch markets). */
export const CITIES = Object.freeze([
  'Karachi',
  'Lahore',
  'Islamabad',
  'Rawalpindi',
  'Faisalabad',
]);

/** Listing purpose values — lowercase to match backend enum + API query params. */
export const LISTING_PURPOSES = Object.freeze(['buy', 'rent']);

/**
 * Property types we support at launch.
 * Lowercase — must match `backend/models/property.py::PropertyType`.
 */
export const PROPERTY_TYPES = Object.freeze([
  'house',
  'apartment',
  'plot',
  'commercial',
]);

/**
 * Property status — `active` is the only public state.
 * `inactive` is the soft-delete tombstone. `sold` / `rented` keep the record
 * visible for analytics but hide it from the public catalogue.
 */
export const PROPERTY_STATUS = Object.freeze([
  'active',
  'inactive',
  'sold',
  'rented',
]);

/** Currency metadata — used by `formatPKR`. */
export const CURRENCY = Object.freeze({
  code: 'PKR',
  symbol: 'Rs',
  locale: 'en-PK',
});

/** Country defaults. */
export const COUNTRY = Object.freeze({
  iso2: 'PK',
  callingCode: '+92',
  phoneNationalPrefix: '0',
});

/**
 * Dark-luxury design tokens. Keep in sync with:
 *   - frontend/tailwind.config.js (colour map)
 *   - frontend/src/index.css      (`:root` CSS variables)
 *   - .cursor/rules/project-context.mdc (table for the agent)
 */
export const THEME = Object.freeze({
  bgObsidian: '#050505',
  surfaceRaised: '#141414',
  surfaceElevated: '#1A1A1A',
  accentChampagne: '#D4AF37',
  accentChampagneSoft: 'rgba(212, 175, 55, 0.12)',
  textHigh: '#FFFFFF',
  textMuted: '#A1A1AA',
  borderSubtle: '#262626',
});

/** Map defaults — centered on Pakistan, suitable for a country-wide overview. */
export const MAP_DEFAULTS = Object.freeze({
  center: { lat: 30.3753, lng: 69.3451 },
  zoom: 6,
  tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  attribution: '&copy; OpenStreetMap contributors',
});

/** Standard pagination shape. */
export const PAGINATION = Object.freeze({
  defaultPage: 1,
  defaultPageSize: 20,
  maxPageSize: 100,
});

/** User roles — must match backend enum (`models/user.py::Role`). */
export const ROLES = Object.freeze(['admin', 'agent', 'customer']);
