import { norm } from '../../../testing/text';
import { formatCount, formatRate, formatTaxRate, tierRange } from './numbers';

describe('numbers (spec 005 §6.1)', () => {
  it.each([
    [2100, '21 %'],
    [1950, '19,5 %'],
    [2125, '21,25 %'],
    [0, '0 %'],
    [10000, '100 %'],
    [1, '0,01 %'],
  ])('CV-16: tax rate %i bp is %s (CA-5.5)', (bp, expected) => {
    expect(norm(formatTaxRate(bp))).toBe(expected);
  });

  it.each([
    [0, '0'],
    [15, '15'],
    [1000, '1.000'],
    [50000, '50.000'],
    [100000, '100.000'],
    [1000000000, '1.000.000.000'],
  ])('CV-17: count %i is %s (CA-5.6)', (n, expected) => {
    expect(formatCount(n)).toBe(expected);
  });

  it.each([
    [1.0823, '1,0823'],
    [161.27, '161,27'],
    [0.845234, '0,8452'],
    [1.08, '1,08'],
    [1.23456, '1,2346'],
  ])('CV-22: rate %d in T-EQ is %s (CA-4.7)', (rate, expected) => {
    expect(formatRate(rate)).toBe(expected);
  });

  it('CV-22: the rate is rounded half up on its exact value (CA-4.7)', () => {
    expect(formatRate(1.00005)).toBe('1,0001');
    expect(formatRate(1.00004)).toBe('1');
    expect(formatRate(12345.5)).toBe('12.345,5');
  });

  it.each([
    [1, 10, '1 a 10'],
    [11, 50, '11 a 50'],
    [51, null, '51 o más'],
  ])('CV-23: tier (%i, %s) is %s (CA-12.6)', (from, to, expected) => {
    expect(tierRange(from, to)).toBe(expected);
  });
});
