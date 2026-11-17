import { RATES_RESPONSE } from '../../../testing/spec-data';
import { isFresh, offeredCurrencies, parseRatesSnapshot } from './rates-snapshot';

function withRates(rates: unknown): unknown {
  return { ...RATES_RESPONSE, rates };
}

function without(value: object, key: string): Record<string, unknown> {
  const copy: Record<string, unknown> = { ...value };
  delete copy[key];
  return copy;
}

function offeredFor(response: unknown): readonly string[] {
  return offeredCurrencies(parseRatesSnapshot(response));
}

// Spec 005 §6.2 (VE-5 to VE-11): RF-3, CA-3.3, CA-3.5 and CA-3.13.
describe('rates snapshot (spec 005 §6.2)', () => {
  it('VE-5: the rates of 5.4 offer EUR, USD, GBP, CHF and JPY, in that order (CA-3.5)', () => {
    expect(offeredFor(RATES_RESPONSE)).toEqual(['EUR', 'USD', 'GBP', 'CHF', 'JPY']);
  });

  it('VE-6: without JPY (CA-3.5)', () => {
    expect(offeredFor(withRates(without(RATES_RESPONSE.rates, 'JPY')))).toEqual([
      'EUR',
      'USD',
      'GBP',
      'CHF',
    ]);
  });

  it('VE-7: rates that are 0, negative, text or null are not offered (CA-3.5)', () => {
    const rates = { EUR: 1, USD: 0, GBP: -1, CHF: '0.93', JPY: null };
    expect(offeredFor(withRates(rates))).toEqual(['EUR']);
  });

  it('VE-8: empty rates offer only EUR (CA-3.5)', () => {
    expect(offeredFor(withRates({}))).toEqual(['EUR']);
  });

  it('VE-9: EUR is offered even without its key (CA-3.5)', () => {
    expect(offeredFor(withRates(without(RATES_RESPONSE.rates, 'EUR')))).toEqual([
      'EUR',
      'USD',
      'GBP',
      'CHF',
      'JPY',
    ]);
  });

  it('without rates at all, only EUR is offered (CA-3.7)', () => {
    expect(offeredCurrencies(null)).toEqual(['EUR']);
  });

  it.each([
    [1794873599, true],
    [1794873600, false],
    [1794873601, false],
  ])('VE-10: at %i the rates are fresh: %s (CA-3.1, CA-3.2)', (now, expected) => {
    const snapshot = parseRatesSnapshot(RATES_RESPONSE);
    expect(snapshot).not.toBeNull();
    expect(isFresh(snapshot!, now)).toBe(expected);
  });

  it.each([
    ['result "error"', { ...RATES_RESPONSE, result: 'error' }],
    ['base_code "USD"', { ...RATES_RESPONSE, base_code: 'USD' }],
    ['without rates', without(RATES_RESPONSE, 'rates')],
    ['rates as a list', withRates([1, 2])],
    ['without time_next_update_unix', without(RATES_RESPONSE, 'time_next_update_unix')],
    ['time_last_update_unix as text', { ...RATES_RESPONSE, time_last_update_unix: '1794787200' }],
  ])('VE-11: a response with %s is not valid (CA-3.3)', (_case, response) => {
    expect(parseRatesSnapshot(response)).toBeNull();
  });

  it.each([null, undefined, 'texto', 42, [], { ...RATES_RESPONSE, rates: null }])(
    'CA-3.13: %j is not a valid snapshot',
    (value) => {
      expect(parseRatesSnapshot(value)).toBeNull();
    },
  );

  it('keeps the five fields of 5.4, which are what the browser stores (spec 5.5)', () => {
    expect(parseRatesSnapshot({ ...RATES_RESPONSE, provider: 'x', documentation: 'y' })).toEqual(
      RATES_RESPONSE,
    );
  });
});
