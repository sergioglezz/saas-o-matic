import { HttpTestingController, TestRequest } from '@angular/common/http/testing';
import { AppHarness, startApp } from './app';
import { settle, textOf } from './dom';
import { BACKEND } from './http';
import { ACME } from './spec-data';

export const HISTORY_URL = `${BACKEND}/customers/1/simulations`;
export const QUOTE_URL = `${BACKEND}/pricing/quote`;
export const SAVE_URL = `${BACKEND}/simulations`;

export function expectHistory(http: HttpTestingController): TestRequest {
  return http.expectOne((r) => r.method === 'GET' && r.url === HISTORY_URL);
}

export function historyRequests(http: HttpTestingController): TestRequest[] {
  return http.match((r) => r.method === 'GET' && r.url === HISTORY_URL);
}

export function expectQuote(http: HttpTestingController): TestRequest {
  return http.expectOne((r) => r.method === 'POST' && r.url === QUOTE_URL);
}

export function quoteRequests(http: HttpTestingController): TestRequest[] {
  return http.match((r) => r.method === 'POST' && r.url === QUOTE_URL);
}

export function expectSave(http: HttpTestingController): TestRequest {
  return http.expectOne((r) => r.method === 'POST' && r.url === SAVE_URL);
}

export function saveRequests(http: HttpTestingController): TestRequest[] {
  return http.match((r) => r.method === 'POST' && r.url === SAVE_URL);
}

/** Opens /clientes/1 and answers the card with customer 1 (Acme, ES). */
export async function openCard(): Promise<AppHarness> {
  const app = await startApp('/clientes/1');
  app.http.expectOne({ method: 'GET', url: `${BACKEND}/customers/1` }).flush(ACME);
  await settle();
  return app;
}

export function historySection(app: AppHarness): HTMLElement {
  return app.root.querySelector('app-simulation-history') as HTMLElement;
}

export function historyCards(app: AppHarness): HTMLElement[] {
  return Array.from(app.root.querySelectorAll<HTMLElement>('app-simulation-history article'));
}

/** The value next to a label in a list of terms (`dt`/`dd`) inside `root`. */
export function termValue(root: Element, label: string): string {
  const term = Array.from(root.querySelectorAll('dt')).find((dt) => textOf(dt) === label);
  return textOf(term?.nextElementSibling);
}

/** The rows of a tier table as texts: tier, users, units, price per user and amount. */
export function tierRows(root: Element): string[][] {
  return Array.from(root.querySelectorAll('tbody tr')).map((row) =>
    Array.from(row.querySelectorAll('th, td')).map((cell) => textOf(cell)),
  );
}

export function tierHeaders(root: Element): string[] {
  return Array.from(root.querySelectorAll('thead th')).map((cell) => textOf(cell));
}
