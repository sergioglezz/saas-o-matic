import { norm } from '../../../testing/text';
import { currencyDecimals, formatMoney, toMinorUnits } from './money';

// Spec 005 §6.1 (CV-1 to CV-15): RF-5, CA-5.2 to CA-5.4. CV-9, CV-10 and CV-15 showed JPY with
// 2 decimals; spec 008 replaces them with YN-1 to YN-3, below.
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
    ['CV-11', 100, 'USD', 1.005, '1,01 US$'],
    ['CV-12', 1, 'USD', 1.5, '0,02 US$'],
    ['CV-13', 50, 'USD', 1.09, '0,55 US$'],
    ['CV-14', 1, 'USD', 1.4, '0,01 US$'],
  ])('%s: %i cents with %s %d (CA-5.2, CA-5.4)', (_id, cents, code, rate, expected) => {
    expect(norm(formatMoney(cents, { code, rate }))).toBe(expected);
  });
});

// Spec 008 §4.1 (YN-1 to YN-8): RF-1, whole yen rounded half up once on the exact value.
describe('formatMoney in JPY (spec 008 §4.1)', () => {
  it.each([
    ['YN-1', 16940, '27.319 JPY'],
    ['YN-2', 60520570, '97.601.523 JPY'],
    ['YN-3', 0, '0 JPY'],
    ['YN-4', 5000, '8.064 JPY'],
    ['YN-5', 1850, '2.983 JPY'],
    ['YN-6', 1, '2 JPY'],
    ['YN-7', 1000, '1.613 JPY'],
  ])('%s: %i cents with JPY 161.27 (CA-1.2, CA-1.3)', (_id, cents, expected) => {
    expect(norm(formatMoney(cents, { code: 'JPY', rate: 161.27 }))).toBe(expected);
  });

  it('YN-8: the decimals of EUR, USD, GBP, CHF and JPY follow ISO 4217 (CA-1.1)', () => {
    const codes = ['EUR', 'USD', 'GBP', 'CHF', 'JPY'];
    expect(codes.map((code) => currencyDecimals(code))).toEqual([2, 2, 2, 2, 0]);
  });
});

// 005 CA-5.2 and 008 CA-1.2: exact product cents × rate, rounded half up once to the minor unit.
describe('toMinorUnits (spec 005 CA-5.2, spec 008 CA-1.2)', () => {
  it.each([
    [100, 1.005, 101n],
    [1, 1.5, 2n],
    [50, 1.09, 55n],
    [1, 1.4, 1n],
    [16940, 1.0823, 18334n],
    [0, 161.27, 0n],
  ])('%i cents × %d in hundredths', (cents, rate, expected) => {
    expect(toMinorUnits(cents, rate, 2)).toBe(expected);
  });

  it.each([
    [16940, 161.27, 27319n],
    [5000, 161.27, 8064n],
    [1850, 161.27, 2983n],
    [1, 161.27, 2n],
    [0, 161.27, 0n],
  ])('%i cents × %d in whole units', (cents, rate, expected) => {
    expect(toMinorUnits(cents, rate, 0)).toBe(expected);
  });

  it('accepts rates that JavaScript writes with an exponent', () => {
    expect(toMinorUnits(100000, 1e-7, 2)).toBe(0n);
    expect(toMinorUnits(5000000, 1e-7, 2)).toBe(1n);
    expect(toMinorUnits(1, 1e21, 2)).toBe(1000000000000000000000n);
  });
});
