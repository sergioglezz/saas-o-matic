import { MAX_API_CALLS, MAX_STORAGE_GB, MAX_USERS, parseCount } from './usage-input';

// Spec 005 §6.2 (VE-1 to VE-4): RF-11, CA-11.5, CA-11.7 and CA-11.8.
describe('parseCount (spec 005 §6.2)', () => {
  it.each([
    ['0', 0],
    ['15', 15],
    ['007', 7],
    ['100000', 100000],
  ])('VE-1: users %j are valid: %i (CA-11.5)', (text, expected) => {
    expect(parseCount(text, MAX_USERS)).toBe(expected);
  });

  it.each(['', '-1', '+5', '1.5', '1,5', '1e3', 'abc', '100001', ' 15', '15 ', '１５'])(
    'VE-2: users %j are not valid (CA-11.6)',
    (text) => {
      expect(parseCount(text, MAX_USERS)).toBeNull();
    },
  );

  it('VE-3: storage from 0 to 1000000 (CA-11.7)', () => {
    expect(parseCount('0', MAX_STORAGE_GB)).toBe(0);
    expect(parseCount('1000000', MAX_STORAGE_GB)).toBe(1000000);
    for (const text of ['-1', '1000001', '1.5', '']) {
      expect(parseCount(text, MAX_STORAGE_GB)).toBeNull();
    }
  });

  it('VE-4: API calls from 0 to 1000000000 (CA-11.8)', () => {
    expect(parseCount('0', MAX_API_CALLS)).toBe(0);
    expect(parseCount('1000000000', MAX_API_CALLS)).toBe(1000000000);
    for (const text of ['-1', '1000000001', '2.0', '']) {
      expect(parseCount(text, MAX_API_CALLS)).toBeNull();
    }
  });

  it('a very long run of digits is out of range, not a rounded number', () => {
    expect(parseCount('99999999999999999999999', MAX_API_CALLS)).toBeNull();
  });
});
