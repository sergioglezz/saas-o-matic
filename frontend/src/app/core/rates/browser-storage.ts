import { Injectable } from '@angular/core';
import { RatesSnapshot } from './rates-snapshot';

// Spec 005 §5.5 and plan §3: the only two things the browser keeps.
const CURRENCY_KEY = 'saas-o-matic.currency';
const RATES_KEY = 'saas-o-matic.rates';

/**
 * The browser storage, where any failure (blocked, full or unavailable) counts as «nothing is
 * stored» and never stops the app (CA-3.13, TC-12).
 */
@Injectable({ providedIn: 'root' })
export class BrowserStorage {
  readCurrency(): string | null {
    return this.read(CURRENCY_KEY);
  }

  writeCurrency(code: string): void {
    this.write(CURRENCY_KEY, code);
  }

  /** What was stored, still unchecked: `parseRatesSnapshot` decides if it is usable. */
  readRates(): unknown {
    const text = this.read(RATES_KEY);
    if (text === null) {
      return null;
    }
    try {
      return JSON.parse(text) as unknown;
    } catch {
      return null;
    }
  }

  writeRates(snapshot: RatesSnapshot): void {
    this.write(RATES_KEY, JSON.stringify(snapshot));
  }

  private read(key: string): string | null {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  }

  private write(key: string, value: string): void {
    try {
      localStorage.setItem(key, value);
    } catch {
      // Nothing to do: the app keeps working with what it has in memory (TC-12).
    }
  }
}
