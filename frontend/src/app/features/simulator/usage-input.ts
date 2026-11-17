// Spec 005 RF-11: limits of the three simulator values, the same as the backend (004 §5).
export const MAX_USERS = 100_000;
export const MAX_STORAGE_GB = 1_000_000;
export const MAX_API_CALLS = 1_000_000_000;

/** P-3: the slider goes from 0 to 200; the field accepts up to MAX_USERS. */
export const SLIDER_MAX = 200;

export const INITIAL_USERS = 15;

const DIGITS_ONLY = /^[0-9]+$/;

/**
 * CA-11.5, CA-11.7 and CA-11.8: only the digits 0 to 9, with leading zeros allowed («007» is 7),
 * and a number from 0 to `max`. Anything else (empty, sign, decimals, exponent) is not valid.
 */
export function parseCount(text: string, max: number): number | null {
  if (!DIGITS_ONLY.test(text)) {
    return null;
  }
  const value = Number(text);
  return value <= max ? value : null;
}
