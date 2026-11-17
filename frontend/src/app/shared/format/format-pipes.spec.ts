import { norm } from '../../../testing/text';
import { CountPipe, DateTimePipe, DayPipe, MoneyPipe, TaxRatePipe } from './format-pipes';

// Plan DT-15: pure pipes over the format functions, with the currency as an argument.
describe('format pipes (spec 005 RF-5)', () => {
  it('money converts with the display it receives (CA-4.3, CA-5.2)', () => {
    const pipe = new MoneyPipe();
    expect(norm(pipe.transform(16940, { code: 'EUR', rate: null }))).toBe('169,40 €');
    expect(norm(pipe.transform(16940, { code: 'USD', rate: 1.0823 }))).toBe('183,34 US$');
  });

  it('count, tax rate, date and time, and day', () => {
    expect(new CountPipe().transform(50000)).toBe('50.000');
    expect(norm(new TaxRatePipe().transform(2100))).toBe('21 %');
    expect(new DateTimePipe().transform('2026-11-16T10:00:00Z')).toBe('16/11/2026 11:00');
    expect(new DayPipe().transform('2026-11-13T10:00:00Z')).toBe('13/11/2026');
  });
});
