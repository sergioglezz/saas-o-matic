import { expectQuote, quoteRequests, termValue } from '../../../testing/detail';
import { settle } from '../../../testing/dom';
import { FRESH_NOW, setNow, storeRates } from '../../../testing/rates';
import {
  VALUE,
  openSimulator,
  quoteFor,
  saveButton,
  simulator,
  slide,
  slider,
  typeValue,
  valueError,
  valueField,
} from '../../../testing/simulator';

const T_USR = 'Debe ser un número entero entre 0 y 100000';
const T_STO = 'Debe ser un número entero entre 0 y 1000000';
const T_APC = 'Debe ser un número entero entre 0 y 1000000000';

// Spec 005 §6.10 (SM-1 to SM-13): RF-11, with the quotes answered 200.
describe('simulator values (spec 005 §6.10)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('SM-1: slider and field at 15, storage 0 and calls 0 (CA-11.1)', async () => {
    const app = await openSimulator();
    expect(slider(app).value).toBe('15');
    expect(valueField(app, VALUE.users).value).toBe('15');
    expect(valueField(app, VALUE.storage).value).toBe('0');
    expect(valueField(app, VALUE.calls).value).toBe('0');
  });

  it('SM-2: moving the slider to 60 puts 60 in the field (CA-11.2)', async () => {
    const app = await openSimulator();
    await slide(app, 60);
    expect(valueField(app, VALUE.users).value).toBe('60');
  });

  it('SM-3: writing 150 moves the slider (CA-11.2)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.users, '150');
    expect(slider(app).value).toBe('150');
  });

  it.each([201, 100000])(
    'SM-4: writing %i leaves the slider at 200 and quotes it (CA-11.3)',
    async (users) => {
      const app = await openSimulator();
      await typeValue(app, VALUE.users, String(users));
      expect(slider(app).value).toBe('200');
      await settle(300);
      expect(expectQuote(app.http).request.body).toEqual({ users, country: 'ES' });
    },
  );

  it('SM-5: 100001 shows T-USR, asks nothing, disables saving and keeps the quote (CA-11.6)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.users, '100001');
    await settle(1000);
    expect(valueError(app, VALUE.users)).toBe(T_USR);
    expect(valueField(app, VALUE.users).getAttribute('aria-invalid')).toBe('true');
    expect(quoteRequests(app.http)).toEqual([]);
    expect(saveButton(app).disabled).toBe(true);
    expect(termValue(simulator(app), 'Total mensual')).toBe('169,40 €');
  });

  it.each(['', '-1', '1.5', '1e3', 'abc'])(
    'SM-6: %j shows T-USR and asks nothing (CA-11.6, CA-11.10)',
    async (text) => {
      const app = await openSimulator();
      await typeValue(app, VALUE.users, text);
      await settle(1000);
      expect(valueError(app, VALUE.users)).toBe(T_USR);
      expect(quoteRequests(app.http)).toEqual([]);
    },
  );

  it.each([
    ['0', 0],
    ['007', 7],
  ])('SM-7 and SM-8: %j quotes %i users (CA-11.5)', async (text, users) => {
    const app = await openSimulator();
    await typeValue(app, VALUE.users, text);
    await settle(300);
    const req = expectQuote(app.http);
    expect(req.request.body).toEqual({ users, country: 'ES' });
    req.flush(quoteFor(users));
  });

  it('SM-9: after 201, moving the slider to 199 puts 199 in the field (CA-11.3)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.users, '201');
    await slide(app, 199);
    expect(valueField(app, VALUE.users).value).toBe('199');
  });

  it('SM-10: a native range control from 0 to 200 with step 1 (CA-11.4)', async () => {
    const app = await openSimulator();
    const range = slider(app);
    expect([range.type, range.min, range.max, range.step]).toEqual(['range', '0', '200', '1']);
    expect(range.getAttribute('aria-labelledby')).toBeTruthy();
  });

  it('SM-11: storage 1000000 is valid; 1000001, -1 and 1.5 show T-STO and disable saving (CA-11.7)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.storage, '1000000');
    expect(valueError(app, VALUE.storage)).toBe('');
    expect(saveButton(app).disabled).toBe(false);
    for (const text of ['1000001', '-1', '1.5']) {
      await typeValue(app, VALUE.storage, text);
      expect(valueError(app, VALUE.storage)).toBe(T_STO);
      expect(saveButton(app).disabled).toBe(true);
    }
  });

  it('SM-12: calls 1000000000 are valid; 1000000001 shows T-APC and disables saving (CA-11.8)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.calls, '1000000000');
    expect(valueError(app, VALUE.calls)).toBe('');
    expect(saveButton(app).disabled).toBe(false);
    await typeValue(app, VALUE.calls, '1000000001');
    expect(valueError(app, VALUE.calls)).toBe(T_APC);
    expect(saveButton(app).disabled).toBe(true);
  });

  it('SM-13: storage and calls ask nothing and change no amount (CA-11.9)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.storage, '200');
    await typeValue(app, VALUE.calls, '50000');
    await settle(1000);
    expect(quoteRequests(app.http)).toEqual([]);
    expect(termValue(simulator(app), 'Total mensual')).toBe('169,40 €');
  });
});
