/**
 * Shared utilities for Hils Marketing.
 *
 * Pure functions. No DOM, no Node-only APIs. Runs in browser + Node + a
 * Python-import shim for the backend if needed.
 */

import { CURRENCY, COUNTRY } from './constants.js';

/**
 * Format an integer (or numeric string) amount as Pakistani Rupees.
 *
 * @param {number | string} amount - Amount in PKR (no decimals expected for property prices).
 * @param {{ withSymbol?: boolean, maximumFractionDigits?: number }} [opts]
 * @returns {string} e.g. "Rs 18,50,00,000"
 *
 * @example
 *   formatPKR(185000000)              // "Rs 185,000,000"
 *   formatPKR(185000000, { withSymbol: false }) // "185,000,000"
 */
export function formatPKR(amount, opts = {}) {
  const { withSymbol = true, maximumFractionDigits = 0 } = opts;
  const n = typeof amount === 'string' ? Number(amount) : amount;
  if (!Number.isFinite(n)) return withSymbol ? `${CURRENCY.symbol} 0` : '0';
  const formatted = new Intl.NumberFormat(CURRENCY.locale, {
    maximumFractionDigits,
  }).format(n);
  return withSymbol ? `${CURRENCY.symbol} ${formatted}` : formatted;
}

/**
 * Slugify a string for use in URLs.
 *
 * @param {string} input
 * @returns {string} lowercase, hyphen-separated, ASCII-only
 *
 * @example
 *   slugify('Luxury Villa, DHA Phase 6')   // "luxury-villa-dha-phase-6"
 */
export function slugify(input) {
  return String(input ?? '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/**
 * Normalize a Pakistani phone number to E.164 (`+923001234567`).
 * Accepts local (`03001234567`) and intl (`+92 300 1234567`) inputs.
 *
 * @param {string} input
 * @returns {string | null} E.164 number or null if it doesn't look valid.
 *
 * @example
 *   normalizePkPhone('0300 1234567')   // "+923001234567"
 *   normalizePkPhone('+92-300-1234567') // "+923001234567"
 */
export function normalizePkPhone(input) {
  const digits = String(input ?? '').replace(/\D/g, '');
  if (!digits) return null;
  let national;
  if (digits.startsWith('92')) national = digits.slice(2);
  else if (digits.startsWith(COUNTRY.phoneNationalPrefix)) national = digits.slice(1);
  else national = digits;
  if (national.length !== 10) return null;          // PK mobile = 10 digits after country code
  if (!national.startsWith('3')) return null;       // mobile prefixes start with 3
  return `${COUNTRY.callingCode}${national}`;
}

/**
 * Clamp a number into [min, max].
 *
 * @param {number} n
 * @param {number} min
 * @param {number} max
 * @returns {number}
 */
export function clamp(n, min, max) {
  return Math.min(Math.max(n, min), max);
}

/**
 * Return a shallow copy of `obj` with only the listed keys.
 *
 * @template {Record<string, unknown>} T
 * @template {keyof T} K
 * @param {T} obj
 * @param {K[]} keys
 * @returns {Pick<T, K>}
 */
export function pick(obj, keys) {
  const out = {};
  for (const k of keys) {
    if (k in obj) out[k] = obj[k];
  }
  return out;
}
