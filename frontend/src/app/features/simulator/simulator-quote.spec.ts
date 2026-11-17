import { TestRequest } from '@angular/common/http/testing';
import { AppHarness } from '../../../testing/app';
import { expectQuote, quoteRequests, termValue, tierRows } from '../../../testing/detail';
import { buttonNamed, choose, settle, textOf } from '../../../testing/dom';
import { errorBody, respondError, respondNoConnection } from '../../../testing/http';
import { FRESH_NOW, RATES_URL, setNow, storeRates } from '../../../testing/rates';
import {
  VALUE,
  openSimulator,
  quoteFor,
  saveButton,
  simulator,
  slide,
  typeValue,
} from '../../../testing/simulator';
import { QUOTE_15, QUOTE_60 } from '../../../testing/spec-data';

const CO_1_ROWS = [
  ['1', '1 a 10', '10', '10,00 €', '100,00 €'],
  ['2', '11 a 50', '5', '8,00 €', '40,00 €'],
  ['3', '51 o más', '0', '5,00 €', '0,00 €'],
];

function shows(app: AppHarness, text: string): boolean {
  return textOf(simulator(app)).includes(text);
}

async function quoteSixtyPending(app: AppHarness): Promise<TestRequest> {
  await typeValue(app, VALUE.users, '60');
  await settle(300);
  return expectQuote(app.http);
}

// Spec 005 §6.11 (CO-1 to CO-16): RF-12, with customer 1 (ES).
describe('simulator quote (spec 005 §6.11)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('FI-1 and CO-1: the initial quote goes at once and shows tiers and totals (CA-12.1, CA-12.6)', async () => {
    const app = await openSimulator({ answerQuote: false });
    const req = expectQuote(app.http);
    expect(req.request.body).toEqual({ users: 15, country: 'ES' });
    req.flush(QUOTE_15);
    await settle();
    expect(tierRows(simulator(app))).toEqual(CO_1_ROWS);
    expect(termValue(simulator(app), 'Subtotal')).toBe('140,00 €');
    expect(termValue(simulator(app), 'Impuesto (21 %)')).toBe('29,40 €');
    expect(termValue(simulator(app), 'Total mensual')).toBe('169,40 €');
  });

  it('CO-2: dragging from 15 to 60 with 50 ms per step makes one request, 300 ms after the last (CA-12.3)', async () => {
    const app = await openSimulator();
    for (let users = 16; users <= 60; users++) {
      await slide(app, users);
      await settle(50);
      expect(quoteRequests(app.http)).toEqual([]);
    }
    await settle(249);
    expect(quoteRequests(app.http)).toEqual([]);
    await settle(1);
    expect(expectQuote(app.http).request.body).toEqual({ users: 60, country: 'ES' });
  });

  it('CO-3: at 299 ms nothing; at 300 ms one request (CA-12.2)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.users, '60');
    await settle(299);
    expect(quoteRequests(app.http)).toEqual([]);
    await settle(1);
    expect(quoteRequests(app.http)).toHaveLength(1);
  });

  it('CO-4: going to 16 and back to 15 within 300 ms asks nothing; saving stays on (CA-12.4)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.users, '16');
    await settle(100);
    await typeValue(app, VALUE.users, '15');
    expect(saveButton(app).disabled).toBe(false);
    await settle(1000);
    expect(quoteRequests(app.http)).toEqual([]);
    expect(saveButton(app).disabled).toBe(false);
  });

  it('CO-5: the answer for 60 arriving after the one for 100 is never shown (CA-12.5)', async () => {
    const app = await openSimulator();
    const sixty = await quoteSixtyPending(app);
    await typeValue(app, VALUE.users, '100');
    await settle(300);
    const hundred = expectQuote(app.http);
    expect(sixty.cancelled).toBe(true);
    hundred.flush({ ...quoteFor(100), total_cents: 100000 });
    await settle();
    expect(termValue(simulator(app), 'Total mensual')).toBe('1.000,00 €');
  });

  it('CO-6: while waiting and while asking, the old quote with T-UPD; saving off (CA-12.7)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.users, '60');
    expect(shows(app, 'Actualizando…')).toBe(true);
    expect(termValue(simulator(app), 'Total mensual')).toBe('169,40 €');
    expect(saveButton(app).disabled).toBe(true);
    await settle(300);
    expect(quoteRequests(app.http)).toHaveLength(1);
    expect(shows(app, 'Actualizando…')).toBe(true);
    expect(saveButton(app).disabled).toBe(true);
  });

  it('CO-7 and CO-8: a failed quote keeps the old one with T-NUP; «Reintentar» asks for 60 (CA-12.8)', async () => {
    const app = await openSimulator();
    respondNoConnection(await quoteSixtyPending(app));
    await settle();
    expect(termValue(simulator(app), 'Total mensual')).toBe('169,40 €');
    expect(shows(app, 'No se pudo actualizar')).toBe(true);
    expect(saveButton(app).disabled).toBe(true);
    buttonNamed(simulator(app), 'Reintentar')?.click();
    await settle();
    const retry = expectQuote(app.http);
    expect(retry.request.body).toEqual({ users: 60, country: 'ES' });
    retry.flush(QUOTE_60);
    await settle();
    expect(shows(app, 'No se pudo actualizar')).toBe(false);
    expect(termValue(simulator(app), 'Total mensual')).toBe('568,70 €');
    expect(saveButton(app).disabled).toBe(false);
  });

  it('CO-9: a failed initial quote shows no amounts, T-NUP and «Reintentar» (CA-12.8)', async () => {
    const app = await openSimulator({ answerQuote: false });
    respondError(expectQuote(app.http), 500, 'x');
    await settle();
    expect(simulator(app).querySelector('table, dl')).toBeNull();
    expect(shows(app, 'No se pudo actualizar')).toBe(true);
    expect(buttonNamed(simulator(app), 'Reintentar')).toBeDefined();
    expect(saveButton(app).disabled).toBe(true);
  });

  it.each([
    ['500', (r: TestRequest) => respondError(r, 500, 'x')],
    ['404', (r: TestRequest) => respondError(r, 404, errorBody('not_found', 'x'))],
    [
      '422 of users',
      (r: TestRequest) =>
        respondError(
          r,
          422,
          errorBody('validation_error', 'x', [{ field: 'users', message: 'y' }]),
        ),
    ],
  ])('CO-10: a %s shows T-NUP with «Reintentar» (CA-12.8)', async (_case, respond) => {
    const app = await openSimulator();
    respond(await quoteSixtyPending(app));
    await settle();
    expect(shows(app, 'No se pudo actualizar')).toBe(true);
    expect(buttonNamed(simulator(app), 'Reintentar')).toBeDefined();
  });

  it('CO-11: «País no soportado» shows T-CNS without «Reintentar» nor amounts (CA-12.9)', async () => {
    const app = await openSimulator();
    const details = [{ field: 'country', message: 'País no soportado' }];
    respondError(await quoteSixtyPending(app), 422, errorBody('validation_error', 'x', details));
    await settle();
    expect(shows(app, 'El país del cliente no está soportado')).toBe(true);
    expect(buttonNamed(simulator(app), 'Reintentar')).toBeUndefined();
    expect(simulator(app).querySelector('table, dl')).toBeNull();
    expect(saveButton(app).disabled).toBe(true);
  });

  it('CO-12: the subtotal is the backend one, not the sum of the tiers (CA-5.1)', async () => {
    const app = await openSimulator({ answerQuote: false });
    expectQuote(app.http).flush({ ...QUOTE_15, subtotal_cents: 14001 });
    await settle();
    expect(termValue(simulator(app), 'Subtotal')).toBe('140,01 €');
  });

  it('CO-13: for 0 users the 3 tiers have 0 units and every amount is 0,00 € (CA-12.6)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.users, '0');
    await settle(300);
    const zero = QUOTE_15.tiers.map((t) => ({ ...t, units: 0, amount_cents: 0 }));
    expectQuote(app.http).flush({
      ...quoteFor(0),
      tiers: zero,
      subtotal_cents: 0,
      tax_cents: 0,
      total_cents: 0,
    });
    await settle();
    expect(tierRows(simulator(app)).map((row) => row[2])).toEqual(['0', '0', '0']);
    expect(tierRows(simulator(app)).map((row) => row[4])).toEqual(['0,00 €', '0,00 €', '0,00 €']);
    expect(termValue(simulator(app), 'Total mensual')).toBe('0,00 €');
  });

  it('CO-14: the quote for 60 users (CA-12.6)', async () => {
    const app = await openSimulator();
    (await quoteSixtyPending(app)).flush(QUOTE_60);
    await settle();
    const rows = tierRows(simulator(app));
    expect(rows.map((row) => row[2])).toEqual(['10', '40', '10']);
    expect(rows.map((row) => row[4])).toEqual(['100,00 €', '320,00 €', '50,00 €']);
    expect(termValue(simulator(app), 'Subtotal')).toBe('470,00 €');
    expect(termValue(simulator(app), 'Impuesto (21 %)')).toBe('98,70 €');
    expect(termValue(simulator(app), 'Total mensual')).toBe('568,70 €');
  });

  it('CO-15: changing the currency converts the quote without asking anything (CA-12.10)', async () => {
    const app = await openSimulator();
    choose(app.root.querySelector('header select') as HTMLSelectElement, 'USD');
    await settle(1000);
    expect(quoteRequests(app.http)).toEqual([]);
    app.http.expectNone(RATES_URL);
    expect(termValue(simulator(app), 'Total mensual')).toBe('183,34 US$');
  });

  it('CO-16: a quote without an answer in 10 s shows T-NUP with «Reintentar» (CA-12.8)', async () => {
    const app = await openSimulator();
    const req = await quoteSixtyPending(app);
    await settle(9999);
    expect(shows(app, 'No se pudo actualizar')).toBe(false);
    await settle(1);
    expect(req.cancelled).toBe(true);
    expect(shows(app, 'No se pudo actualizar')).toBe(true);
    expect(buttonNamed(simulator(app), 'Reintentar')).toBeDefined();
  });
});
