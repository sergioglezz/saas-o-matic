import { TestBed } from '@angular/core/testing';
import { DisplayCurrency } from '../../core/rates/display-currency';
import { choose, linkNamed, optionTexts, settle, textOf } from '../../../testing/dom';
import { respondNoConnection } from '../../../testing/http';
import {
  CURRENCY_KEY,
  FRESH_NOW,
  RATES_URL,
  STALE_NOW,
  answerRates,
  mountBar,
  reloadBar,
  setNow,
  storeRates,
} from '../../../testing/rates';
import { RATES_RESPONSE } from '../../../testing/spec-data';

const ORI = 'Conversión orientativa: los importes se calculan y guardan en EUR';

function withoutJpy(): object {
  const rates: Record<string, number> = { ...RATES_RESPONSE.rates };
  delete rates['JPY'];
  return { ...RATES_RESPONSE, rates };
}

// Spec 005 §6.4 (DV-1 and DV-6 to DV-11) and the bar of RF-3 and RF-4.
describe('currency bar (spec 005 §6.4)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
  });

  afterEach(() => vi.useRealTimers());

  it('DV-1: label «Divisa» and the options in order (CA-4.1)', async () => {
    storeRates();
    const { bar, select } = await mountBar();
    expect(textOf(bar.querySelector(`label[for="${select().id}"]`))).toBe('Divisa');
    expect(optionTexts(select())).toEqual([
      'EUR (euro)',
      'USD (dólar estadounidense)',
      'GBP (libra esterlina)',
      'CHF (franco suizo)',
      'JPY (yen japonés)',
    ]);
  });

  it('CA-4.3, CA-4.4 and CA-4.7: choosing USD asks nothing, remembers it and shows T-EQ and T-ORI', async () => {
    storeRates();
    const { bar, select, http } = await mountBar();
    expect(textOf(bar)).not.toContain(ORI);
    choose(select(), 'USD');
    await settle();
    expect(localStorage.getItem(CURRENCY_KEY)).toBe('USD');
    expect(textOf(bar)).toContain('1 EUR = 1,0823 USD');
    expect(textOf(bar)).toContain(ORI);
    expect(TestBed.inject(DisplayCurrency).display()).toEqual({ code: 'USD', rate: 1.0823 });
    http.verify();
  });

  it('DV-6: GBP is still chosen after a reload with fresh rates (CA-4.5)', async () => {
    storeRates();
    const first = await mountBar();
    choose(first.select(), 'GBP');
    await settle();
    const { select, http } = await reloadBar();
    http.expectNone(RATES_URL);
    expect(select().value).toBe('GBP');
  });

  it('DV-7: a remembered JPY missing from the rates gives EUR, and comes back later', async () => {
    localStorage.setItem(CURRENCY_KEY, 'JPY');
    let harness = await mountBar();
    answerRates(harness.http, withoutJpy());
    await settle();
    expect(harness.select().value).toBe('EUR');
    expect(localStorage.getItem(CURRENCY_KEY)).toBe('JPY');
    setNow(STALE_NOW);
    harness = await reloadBar();
    answerRates(harness.http);
    await settle();
    expect(harness.select().value).toBe('JPY');
  });

  it('DV-8: an unknown remembered currency gives EUR (CA-4.6)', async () => {
    localStorage.setItem(CURRENCY_KEY, 'XYZ');
    storeRates();
    const { select } = await mountBar();
    expect(select().value).toBe('EUR');
  });

  it('DV-9: rates failing without stored ones keep the remembered USD (CA-4.6)', async () => {
    localStorage.setItem(CURRENCY_KEY, 'USD');
    const { http, select } = await mountBar();
    respondNoConnection(http.expectOne(RATES_URL));
    await settle();
    expect(optionTexts(select())).toEqual(['EUR (euro)']);
    expect(localStorage.getItem(CURRENCY_KEY)).toBe('USD');
  });

  it('DV-10: without a remembered currency, EUR (CA-4.5)', async () => {
    storeRates();
    const { select } = await mountBar();
    expect(select().value).toBe('EUR');
  });

  it('DV-11: a remembered USD shows EUR while the rates load, and USD when they arrive', async () => {
    localStorage.setItem(CURRENCY_KEY, 'USD');
    const { http, select } = await mountBar();
    expect(select().disabled).toBe(true);
    expect(select().value).toBe('EUR');
    expect(TestBed.inject(DisplayCurrency).display()).toEqual({ code: 'EUR', rate: null });
    answerRates(http);
    await settle();
    expect(select().disabled).toBe(false);
    expect(select().value).toBe('USD');
  });

  it('TC-16: the attribution is a link in every state of the rates (CA-3.11)', async () => {
    const expectAttribution = (bar: HTMLElement) => {
      const link = linkNamed(bar, 'Rates By Exchange Rate API');
      expect(link?.getAttribute('href')).toBe('https://www.exchangerate-api.com');
    };
    storeRates();
    setNow(STALE_NOW);
    const { bar, http } = await mountBar();
    expectAttribution(bar); // TC-14: loading
    respondNoConnection(http.expectOne(RATES_URL));
    await settle();
    expectAttribution(bar); // TC-5: stale
    localStorage.clear();
    const reloaded = await reloadBar();
    respondNoConnection(reloaded.http.expectOne(RATES_URL));
    await settle();
    expectAttribution(reloaded.bar); // TC-8: unavailable
    const fresh = await reloadBar();
    answerRates(fresh.http);
    await settle();
    expectAttribution(fresh.bar); // TC-1: fresh
  });
});
