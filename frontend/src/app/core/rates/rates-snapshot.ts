/** CA-3.5: the currencies the app can offer, in this order. */
export const CURRENCY_CODES = ['EUR', 'USD', 'GBP', 'CHF', 'JPY'] as const;

export type CurrencyCode = (typeof CURRENCY_CODES)[number];

/** The five fields of the rates API that the app uses and stores (spec 005 §5.4 and §5.5). */
export interface RatesSnapshot {
  readonly result: 'success';
  readonly base_code: 'EUR';
  readonly rates: Readonly<Record<string, unknown>>;
  readonly time_last_update_unix: number;
  readonly time_next_update_unix: number;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * CA-3.3 and CA-3.13: the same check for the API response and for what the browser has stored.
 * Anything else is treated as if there were no rates.
 */
export function parseRatesSnapshot(value: unknown): RatesSnapshot | null {
  if (!isPlainObject(value)) {
    return null;
  }
  const { result, base_code, rates, time_last_update_unix, time_next_update_unix } = value;
  const valid =
    result === 'success' &&
    base_code === 'EUR' &&
    isPlainObject(rates) &&
    typeof time_last_update_unix === 'number' &&
    typeof time_next_update_unix === 'number';
  if (!valid) {
    return null;
  }
  return { result, base_code, rates, time_last_update_unix, time_next_update_unix };
}

/** CA-3.1 and CA-3.2: at the instant `time_next_update_unix` the rates are already stale. */
export function isFresh(snapshot: RatesSnapshot, nowSeconds: number): boolean {
  return snapshot.time_next_update_unix > nowSeconds;
}

/** The rate of a currency, if the snapshot has a usable one: a finite number above 0. */
export function rateOf(snapshot: RatesSnapshot | null, code: CurrencyCode): number | null {
  if (code === 'EUR') {
    return 1;
  }
  const rate = snapshot?.rates[code];
  return typeof rate === 'number' && Number.isFinite(rate) && rate > 0 ? rate : null;
}

/** CA-3.5: EUR always, and the others only with a usable rate. */
export function offeredCurrencies(snapshot: RatesSnapshot | null): readonly CurrencyCode[] {
  return CURRENCY_CODES.filter((code) => rateOf(snapshot, code) !== null);
}
