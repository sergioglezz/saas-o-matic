import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ExchangeRates } from '../app/core/rates/exchange-rates';
import { CurrencyBar } from '../app/shared/ui/currency-bar';
import { settle } from './dom';
import { RATES_LAST_UPDATE, RATES_NEXT_UPDATE, RATES_RESPONSE } from './spec-data';

export const RATES_URL = 'https://open.er-api.com/v6/latest/EUR';

/** The two keys of the browser storage (plan §3, spec 5.5). */
export const RATES_KEY = 'saas-o-matic.rates';
export const CURRENCY_KEY = 'saas-o-matic.currency';

/** An instant while the rates of 5.4 are fresh: 16/11/2026 at 10:00 UTC. */
export const FRESH_NOW = RATES_LAST_UPDATE + 10 * 3600;

/** The first instant at which the rates of 5.4 are stale (VE-10). */
export const STALE_NOW = RATES_NEXT_UPDATE;

export function setNow(seconds: number): void {
  vi.setSystemTime(seconds * 1000);
}

export function storeRates(value: unknown = RATES_RESPONSE): void {
  localStorage.setItem(RATES_KEY, typeof value === 'string' ? value : JSON.stringify(value));
}

export function storedRates(): unknown {
  const text = localStorage.getItem(RATES_KEY);
  return text === null ? null : JSON.parse(text);
}

/** Answers the single pending rates request with the response of 5.4 (or another one). */
export function answerRates(http: HttpTestingController, body: object = RATES_RESPONSE): void {
  http.expectOne(RATES_URL).flush(body);
}

export interface BarHarness {
  readonly bar: HTMLElement;
  readonly http: HttpTestingController;
  readonly select: () => HTMLSelectElement;
}

/**
 * Loads the app as far as the rates go: the currency bar and the start of the rates (which the
 * app does once, when it starts). Calling it again after `TestBed.resetTestingModule()` is a
 * reload: the browser storage is kept.
 */
export async function mountBar(): Promise<BarHarness> {
  TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
  const fixture = TestBed.createComponent(CurrencyBar);
  TestBed.inject(ExchangeRates).load();
  await settle();
  const bar = fixture.nativeElement as HTMLElement;
  return {
    bar,
    http: TestBed.inject(HttpTestingController),
    select: () => bar.querySelector('select') as HTMLSelectElement,
  };
}

export async function reloadBar(): Promise<BarHarness> {
  TestBed.resetTestingModule();
  return mountBar();
}
