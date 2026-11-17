import { formatDate, formatDateTime, formatUnixDate } from './dates';

// Spec 005 §6.1, with the Europe/Madrid time zone fixed in src/test-setup.ts (plan DT-2).
describe('dates (spec 005 §6.1, CA-5.7, CA-3.10)', () => {
  it.each([
    ['CV-18', '2026-11-16T10:00:00Z', '16/11/2026 11:00'],
    ['CV-19', '2026-11-16T23:30:00Z', '17/11/2026 00:30'],
    ['CV-20', '2026-07-01T10:00:00Z', '01/07/2026 12:00'],
  ])('%s: %s is %s', (_id, iso, expected) => {
    expect(formatDateTime(iso)).toBe(expected);
  });

  it('CV-21: dates without time', () => {
    expect(formatDate('2026-11-13T10:00:00Z')).toBe('13/11/2026');
    expect(formatUnixDate(1794787200)).toBe('16/11/2026');
  });

  it('uses the 24-hour clock', () => {
    expect(formatDateTime('2026-11-16T21:05:00Z')).toBe('16/11/2026 22:05');
  });
});
