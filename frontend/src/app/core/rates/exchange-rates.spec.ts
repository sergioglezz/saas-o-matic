import { TestRequest } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { buttonNamed, choose, optionTexts, settle, textOf } from '../../../testing/dom';
import { respondError, respondNoConnection, respondNotJson } from '../../../testing/http';
import {
  FRESH_NOW,
  RATES_URL,
  STALE_NOW,
  answerRates,
  mountBar,
  reloadBar,
  setNow,
  storeRates,
  storedRates,
} from '../../../testing/rates';
import { RATES_RESPONSE } from '../../../testing/spec-data';
import { DisplayCurrency } from './display-currency';

const FIVE = ['EUR (euro)', 'USD (dólar estadounidense)', 'GBP (libra esterlina)'];
const ALL_FIVE = [...FIVE, 'CHF (franco suizo)', 'JPY (yen japonés)'];
const RFL = 'Tasas del 16/11/2026. No se pudieron actualizar';
const RNO = 'Tipos de cambio no disponibles: importes en EUR';

// Spec 005 §6.3 (TC-1 to TC-12, TC-14 and TC-15): RF-3 and CA-4.2.
describe('exchange rates (spec 005 §6.3)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('TC-1: without stored rates, one request; 5 currencies, T-RAT and rates stored (CA-3.2, CA-3.4, CA-3.9)', async () => {
    const { bar, http, select } = await mountBar();
    answerRates(http); // expectOne: exactly one request
    await settle();
    expect(select().disabled).toBe(false);
    expect(optionTexts(select())).toEqual(ALL_FIVE);
    expect(textOf(bar)).toContain('Tasas del 16/11/2026');
    expect(storedRates()).toEqual(RATES_RESPONSE);
    http.verify();
  });

  it('TC-2: fresh stored rates are used without any request (CA-3.1)', async () => {
    storeRates();
    setNow(STALE_NOW - 1);
    const { bar, http, select } = await mountBar();
    http.expectNone(RATES_URL);
    expect(optionTexts(select())).toEqual(ALL_FIVE);
    expect(textOf(bar)).toContain('Tasas del 16/11/2026');
  });

  it('TC-3 and TC-4: stale stored rates are asked again; the new ones are used and stored (CA-3.4)', async () => {
    storeRates();
    setNow(STALE_NOW);
    const { bar, http, select } = await mountBar();
    const newer = { ...RATES_RESPONSE, rates: { ...RATES_RESPONSE.rates, USD: 1.09 } };
    answerRates(http, newer);
    await settle();
    choose(select(), 'USD');
    await settle();
    expect(textOf(bar)).toContain('1 EUR = 1,09 USD');
    expect(storedRates()).toEqual(newer);
  });

  it('TC-5: stale stored rates and no answer: they are used with T-RFL and «Reintentar»', async () => {
    storeRates();
    setNow(STALE_NOW);
    const { bar, http, select } = await mountBar();
    respondNoConnection(http.expectOne(RATES_URL));
    await settle();
    expect(textOf(bar)).toContain(RFL);
    expect(buttonNamed(bar, 'Reintentar')).toBeDefined();
    expect(optionTexts(select())).toEqual(ALL_FIVE);
  });

  it.each([
    ['429', (r: TestRequest) => respondError(r, 429)],
    ['500', (r: TestRequest) => respondError(r, 500, 'x')],
    ['result "error"', (r: TestRequest) => r.flush({ ...RATES_RESPONSE, result: 'error' })],
    ['base_code "USD"', (r: TestRequest) => r.flush({ ...RATES_RESPONSE, base_code: 'USD' })],
    ['a body that is not JSON', respondNotJson],
  ])('TC-6: a response with %s is the same as TC-5 (CA-3.6)', async (_case, respond) => {
    storeRates();
    setNow(STALE_NOW);
    const { bar, http } = await mountBar();
    respond(http.expectOne(RATES_URL));
    await settle();
    expect(textOf(bar)).toContain(RFL);
    expect(storedRates()).toEqual(RATES_RESPONSE);
  });

  it('TC-7: after 10 s the request is dropped and the stored rates are used', async () => {
    storeRates();
    setNow(STALE_NOW);
    const { bar, http } = await mountBar();
    const req = http.expectOne(RATES_URL);
    await settle(9999);
    expect(textOf(bar)).toContain('Cargando tasas…');
    await settle(1);
    expect(req.cancelled).toBe(true);
    await settle();
    expect(textOf(bar)).toContain(RFL);
  });

  it('TC-8: without stored rates and a failure, only EUR with T-RNO (CA-3.7)', async () => {
    const { bar, http, select } = await mountBar();
    respondError(http.expectOne(RATES_URL), 500, 'x');
    await settle();
    expect(optionTexts(select())).toEqual(['EUR (euro)']);
    expect(textOf(bar)).toContain(RNO);
    expect(buttonNamed(bar, 'Reintentar')).toBeDefined();
    expect(TestBed.inject(DisplayCurrency).display()).toEqual({ code: 'EUR', rate: null });
  });

  it('TC-9: «Reintentar» after TC-8 asks again and uses the new rates (CA-3.8)', async () => {
    const { bar, http, select } = await mountBar();
    respondNoConnection(http.expectOne(RATES_URL));
    await settle();
    buttonNamed(bar, 'Reintentar')?.click();
    await settle();
    answerRates(http);
    await settle();
    expect(textOf(bar)).not.toContain(RNO);
    expect(buttonNamed(bar, 'Reintentar')).toBeUndefined();
    expect(optionTexts(select())).toEqual(ALL_FIVE);
    expect(storedRates()).toEqual(RATES_RESPONSE);
  });

  it('TC-10: «Reintentar» after TC-5 that fails again keeps T-RFL (CA-3.8)', async () => {
    storeRates();
    setNow(STALE_NOW);
    const { bar, http } = await mountBar();
    respondNoConnection(http.expectOne(RATES_URL));
    await settle();
    buttonNamed(bar, 'Reintentar')?.click();
    await settle();
    expect(textOf(bar)).toContain('Cargando tasas…');
    respondNoConnection(http.expectOne(RATES_URL));
    await settle();
    expect(textOf(bar)).toContain(RFL);
  });

  it('TC-11: unreadable stored rates are ignored (CA-3.13)', async () => {
    storeRates('esto no es JSON');
    const { bar, http, select } = await mountBar();
    answerRates(http);
    await settle();
    expect(optionTexts(select())).toEqual(ALL_FIVE);
    expect(textOf(bar)).toContain('Tasas del 16/11/2026');
  });

  it('TC-12: without browser storage the app works and nothing is remembered', async () => {
    const unavailable = () => {
      throw new DOMException('No disponible', 'SecurityError');
    };
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(unavailable);
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(unavailable);
    let harness = await mountBar();
    answerRates(harness.http);
    await settle();
    choose(harness.select(), 'GBP');
    await settle();
    expect(harness.select().value).toBe('GBP');
    harness = await reloadBar();
    answerRates(harness.http);
    await settle();
    expect(harness.select().value).toBe('EUR');
  });

  it('TC-14: while the API has not answered, the selector is disabled, T-LRT and EUR', async () => {
    localStorage.setItem('saas-o-matic.currency', 'USD');
    storeRates();
    setNow(STALE_NOW);
    const { bar, http, select } = await mountBar();
    await settle(5000);
    expect(select().disabled).toBe(true);
    expect(textOf(bar)).toContain('Cargando tasas…');
    expect(TestBed.inject(DisplayCurrency).display()).toEqual({ code: 'EUR', rate: null });
    answerRates(http);
  });

  it('TC-15: MXN is never offered (CA-3.5)', async () => {
    const { http, select } = await mountBar();
    answerRates(http);
    await settle();
    expect(optionTexts(select()).join()).not.toContain('MXN');
    expect(Array.from(select().options).map((o) => o.value)).toEqual([
      'EUR',
      'USD',
      'GBP',
      'CHF',
      'JPY',
    ]);
  });
});
