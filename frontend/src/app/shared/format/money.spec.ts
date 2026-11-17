import { norm } from '../../../testing/text';
import { formatMoney, toHundredths } from './money';

// Spec 005 §6.1 (CV-1 to CV-15): RF-5, CA-5.2 to CA-5.4.
describe('formatMoney (spec 005 §6.1)', () => {
  it.each([
    ['CV-1', 16940, '169,40 €'],
    ['CV-2', 0, '0,00 €'],
    ['CV-3', 123456, '1.234,56 €'],
    ['CV-4', 99999, '999,99 €'],
    ['CV-5', 60520570, '605.205,70 €'],
  ])('%s: %i cents in EUR are shown as they come (CA-5.3, CA-5.4)', (_id, cents, expected) => {
    expect(norm(formatMoney(cents, { code: 'EUR', rate: null }))).toBe(expected);
  });

  it.each([
    ['CV-6', 16940, 'USD', 1.0823, '183,34 US$'],
    ['CV-7', 16940, 'GBP', 0.8452, '143,18 GBP'],
    ['CV-8', 16940, 'CHF', 0.9361, '158,58 CHF'],
    ['CV-9', 16940, 'JPY', 161.27, '27.319,14 JPY'],
    ['CV-10', 60520570, 'JPY', 161.27, '97.601.523,24 JPY'],
    ['CV-11', 100, 'USD', 1.005, '1,01 US$'],
    ['CV-12', 1, 'USD', 1.5, '0,02 US$'],
    ['CV-13', 50, 'USD', 1.09, '0,55 US$'],
    ['CV-14', 1, 'USD', 1.4, '0,01 US$'],
    ['CV-15', 0, 'JPY', 161.27, '0,00 JPY'],
  ])('%s: %i cents with %s %d (CA-5.2, CA-5.4)', (_id, cents, code, rate, expected) => {
    expect(norm(formatMoney(cents, { code, rate }))).toBe(expected);
  });
});

// CA-5.2: exact product cents × rate, rounded half up to hundredths of the currency.
describe('toHundredths (spec 005 CA-5.2)', () => {
  it.each([
    [100, 1.005, 101n],
    [1, 1.5, 2n],
    [50, 1.09, 55n],
    [1, 1.4, 1n],
    [16940, 1.0823, 18334n],
    [0, 161.27, 0n],
  ])('%i cents × %d', (cents, rate, expected) => {
    expect(toHundredths(cents, rate)).toBe(expected);
  });

  it('accepts rates that JavaScript writes with an exponent', () => {
    expect(toHundredths(100000, 1e-7)).toBe(0n);
    expect(toHundredths(5000000, 1e-7)).toBe(1n);
    expect(toHundredths(1, 1e21)).toBe(1000000000000000000000n);
  });
});
