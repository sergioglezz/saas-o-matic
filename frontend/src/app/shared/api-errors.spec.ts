import { HttpTestingController, TestRequest } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AppHarness, reloadApp, startApp } from '../../testing/app';
import { fillForm } from '../../testing/customer-form';
import { expectList } from '../../testing/customers';
import { expectHistory, expectQuote, expectSave, openCard } from '../../testing/detail';
import { buttonNamed, choose, settle, textOf } from '../../testing/dom';
import { BACKEND, errorBody, respondError, respondNotJson } from '../../testing/http';
import {
  CURRENCY_KEY,
  FRESH_NOW,
  RATES_KEY,
  RATES_URL,
  setNow,
  storeRates,
} from '../../testing/rates';
import { VALUE, saveButton, typeValue } from '../../testing/simulator';
import {
  ACME,
  CUSTOMER_PAGE,
  NEW_ACME,
  QUOTE_15,
  RATES_RESPONSE,
  SIMULATION_1,
} from '../../testing/spec-data';

const FORBIDDEN_IN_BODIES = /_cents|tax_rate_bp|rate/;

/** Every request still pending, answered or not, must go to the backend or the rates API. */
function expectOnlyKnownHosts(http: HttpTestingController): TestRequest[] {
  const requests = http.match(() => true);
  for (const req of requests) {
    expect(req.request.url === RATES_URL || req.request.url.startsWith(`${BACKEND}/`)).toBe(true);
  }
  return requests;
}

function main(app: AppHarness): HTMLElement {
  return app.root.querySelector('main') as HTMLElement;
}

function bodyKeys(req: TestRequest): string {
  return Object.keys(req.request.body as object).join(',');
}

// Spec 005 §6.13 (ER-1 to ER-6) and CA-5.8: RF-2 on screen, and what leaves the browser.
describe('general errors and what leaves the browser (spec 005 §6.13)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('ER-1: every request of the list, the form and the card goes to http://127.0.0.1:8000 (CA-2.1)', async () => {
    localStorage.clear();
    const list = await startApp('/clientes');
    const atStart = expectOnlyKnownHosts(list.http);
    expect(atStart.map((r) => r.request.url)).toEqual([RATES_URL, `${BACKEND}/customers`]);
    const form = await reloadApp('/clientes/nuevo');
    fillForm(form.root, NEW_ACME);
    buttonNamed(form.root, 'Guardar')?.click();
    await settle();
    expect(expectOnlyKnownHosts(form.http).map((r) => r.request.url)).toContain(
      `${BACKEND}/customers`,
    );
    const card = await reloadApp('/clientes/1');
    card.http.expectOne(`${BACKEND}/customers/1`).flush(ACME);
    await settle();
    const urls = expectOnlyKnownHosts(card.http).map((r) => r.request.url);
    expect(urls).toContain(`${BACKEND}/customers/1/simulations`);
    expect(urls).toContain(`${BACKEND}/pricing/quote`);
  });

  it('ER-2: the bodies of AL-4, CO-1 and GU-2 carry no amount, tax rate nor exchange rate (CA-2.1, CA-5.8)', async () => {
    const form = await startApp('/clientes/nuevo');
    fillForm(form.root, NEW_ACME);
    buttonNamed(form.root, 'Guardar')?.click();
    await settle();
    const created = form.http.expectOne({ method: 'POST', url: `${BACKEND}/customers` });
    expect(bodyKeys(created)).not.toMatch(FORBIDDEN_IN_BODIES);
    TestBed.resetTestingModule();
    const app = await openCard();
    choose(app.root.querySelector('header select') as HTMLSelectElement, 'USD');
    expectHistory(app.http).flush({ items: [], total: 0 });
    const quote = expectQuote(app.http);
    expect(bodyKeys(quote)).toBe('users,country');
    quote.flush(QUOTE_15);
    await settle();
    await typeValue(app, VALUE.storage, '200');
    saveButton(app).click();
    await settle();
    const save = expectSave(app.http);
    expect(save.request.body).toEqual({
      customer_id: 1,
      active_users: 15,
      storage_gb: 200,
      api_calls_per_month: 0,
    });
    expect(bodyKeys(save)).not.toMatch(FORBIDDEN_IN_BODIES);
  });

  it('CA-5.8: with USD chosen, the browser keeps only the currency and the rates', async () => {
    localStorage.clear();
    const app = await startApp('/clientes/1');
    app.http.expectOne(RATES_URL).flush(RATES_RESPONSE);
    app.http.expectOne(`${BACKEND}/customers/1`).flush(ACME);
    await settle();
    choose(app.root.querySelector('header select') as HTMLSelectElement, 'USD');
    expectHistory(app.http).flush({ items: [SIMULATION_1], total: 1 });
    expectQuote(app.http).flush(QUOTE_15);
    await settle();
    const keys = Array.from({ length: localStorage.length }, (_, i) => localStorage.key(i));
    expect(keys.sort()).toEqual([CURRENCY_KEY, RATES_KEY]);
    expect(localStorage.getItem(CURRENCY_KEY)).toBe('USD');
    expect(JSON.parse(localStorage.getItem(RATES_KEY) ?? '')).toEqual(RATES_RESPONSE);
  });

  it('ER-3: a 500 with an HTML Traceback shows only T-SRV (CA-2.4)', async () => {
    const app = await startApp('/clientes');
    respondError(
      expectList(app.http),
      500,
      '<html><pre>Traceback (most recent call last)</pre></html>',
    );
    await settle();
    const text = textOf(main(app));
    expect(text).toContain('Error del servidor. Inténtalo de nuevo');
    for (const hidden of ['Traceback', '500', 'internal_error']) {
      expect(text).not.toContain(hidden);
    }
  });

  it('ER-4: a 200 whose body is not JSON shows T-SRV with «Reintentar» (CA-2.3)', async () => {
    const app = await startApp('/clientes');
    respondNotJson(expectList(app.http));
    await settle();
    expect(textOf(main(app))).toContain('Error del servidor. Inténtalo de nuevo');
    buttonNamed(main(app), 'Reintentar')?.click();
    await settle();
    expectList(app.http).flush(CUSTOMER_PAGE);
  });

  it('ER-5: no answer in 10 s shows T-CON with «Reintentar» (CA-2.2)', async () => {
    const app = await startApp('/clientes');
    const req = expectList(app.http);
    await settle(10000);
    expect(req.cancelled).toBe(true);
    expect(textOf(main(app))).toContain('No se pudo conectar con el servidor');
    expect(buttonNamed(main(app), 'Reintentar')).toBeDefined();
  });

  it('ER-6: a 422 of the list shows T-SRV with «Reintentar», never its code (CA-2.3, CA-2.4)', async () => {
    const app = await startApp('/clientes');
    const details = [{ field: 'q', message: 'Debe tener como máximo 120 caracteres' }];
    respondError(
      expectList(app.http),
      422,
      errorBody('validation_error', 'Datos no válidos', details),
    );
    await settle();
    const text = textOf(main(app));
    expect(text).toContain('Error del servidor. Inténtalo de nuevo');
    expect(text).not.toContain('validation_error');
    expect(buttonNamed(main(app), 'Reintentar')).toBeDefined();
  });
});
