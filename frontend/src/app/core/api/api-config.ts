// Spec 005 RF-2 and RF-3 (D-1, D-5): where the app asks, and for how long it waits.

/** D-1: 127.0.0.1 and not localhost, which adds about 0.2 s per new connection on Windows. */
export const API_BASE_URL = 'http://127.0.0.1:8000';

/** CA-3.2: the only request to the rates API. */
export const RATES_URL = 'https://open.er-api.com/v6/latest/EUR';

/** D-5: no request waits longer than this, so no loading state is endless. */
export const REQUEST_TIMEOUT_MS = 10_000;

/** RF-7: size of every page of the list and of the history. */
export const PAGE_SIZE = 50;
