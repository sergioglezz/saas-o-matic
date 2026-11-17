import { TestRequest } from '@angular/common/http/testing';
import { AppHarness } from '../../../testing/app';
import {
  expectHistory,
  expectQuote,
  expectSave,
  historyCards,
  historySection,
  openCard,
  saveRequests,
  termValue,
} from '../../../testing/detail';
import { buttonNamed, settle, textOf } from '../../../testing/dom';
import { errorBody, respondError, respondNoConnection } from '../../../testing/http';
import { FRESH_NOW, setNow, storeRates } from '../../../testing/rates';
import {
  VALUE,
  saveButton,
  simulator,
  slider,
  typeValue,
  valueField,
} from '../../../testing/simulator';
import { NEW_SIMULATION, QUOTE_15, SIMULATION_1 } from '../../../testing/spec-data';
import { Simulation } from '../../core/api/api-models';

/** Spec 005 §6.12: 15 users, 200 GB and 50000 calls, with the quote of §8.3 shown. */
async function ready(
  history: { items: Simulation[]; total: number } | null = { items: [], total: 0 },
) {
  const app = await openCard();
  if (history !== null) {
    expectHistory(app.http).flush(history);
  }
  expectQuote(app.http).flush(QUOTE_15);
  await settle();
  await typeValue(app, VALUE.storage, '200');
  await typeValue(app, VALUE.calls, '50000');
  return app;
}

async function pressSave(app: AppHarness): Promise<TestRequest> {
  saveButton(app).click();
  await settle();
  return expectSave(app.http);
}

function created(req: TestRequest, body: Simulation = SIMULATION_1): void {
  req.flush(body, { status: 201, statusText: 'Created' });
}

function says(app: AppHarness, text: string): boolean {
  return textOf(simulator(app)).includes(text);
}

function unsupportedCountry(req: TestRequest): void {
  const details = [{ field: 'country', message: 'País no soportado' }];
  respondError(req, 422, errorBody('validation_error', 'x', details));
}

/** The quote of 60 fails, and so does the one asked again when the users go back to 15. */
async function failingAgainAt15(app: AppHarness, respond: (req: TestRequest) => void) {
  for (const users of ['60', '15']) {
    await typeValue(app, VALUE.users, users);
    await settle(300);
    respond(expectQuote(app.http));
    await settle();
  }
}

function values(app: AppHarness): string[] {
  return [VALUE.users, VALUE.storage, VALUE.calls].map((label) => valueField(app, label).value);
}

// Spec 005 §6.12 (GU-1 to GU-11, GU-13 and GU-14): RF-13, and RF-10 after saving.
describe('save simulation (spec 005 §6.12)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('GU-1 and GU-2: «Guardar simulación» is on and sends exactly the body of 004 §5 (CA-13.2)', async () => {
    const app = await ready();
    expect(saveButton(app).disabled).toBe(false);
    const req = await pressSave(app);
    expect(req.request.body).toEqual(NEW_SIMULATION);
  });

  it('GU-3: the 201 goes first in the history, total + 1, T-SOK, the simulator unchanged (CA-13.4, CA-10.8)', async () => {
    const older = Array.from({ length: 50 }, (_, i) => ({
      ...SIMULATION_1,
      id: 100 + i,
      active_users: 1,
    }));
    const app = await ready({ items: older, total: 60 });
    expect(textOf(historySection(app))).toContain('Mostrando 50 de 60');
    created(await pressSave(app));
    await settle();
    expect(termValue(historyCards(app)[0], 'Usuarios activos')).toBe('15');
    expect(termValue(historyCards(app)[0], 'Total mensual')).toBe('169,40 €');
    expect(textOf(historySection(app))).toContain('Mostrando 51 de 61');
    expect(says(app, 'Simulación guardada')).toBe(true);
    expect(values(app)).toEqual(['15', '200', '50000']);
    expect(termValue(simulator(app), 'Total mensual')).toBe('169,40 €');
  });

  it('GU-4: with an empty history, T-HVA goes and one card appears (CA-10.8)', async () => {
    const app = await ready();
    expect(textOf(historySection(app))).toContain('Este cliente aún no tiene simulaciones');
    created(await pressSave(app));
    await settle();
    expect(textOf(historySection(app))).not.toContain('Este cliente aún no tiene simulaciones');
    expect(historyCards(app)).toHaveLength(1);
  });

  it('GU-5: pressing twice sends one request; T-GDO and the three values disabled (CA-13.3)', async () => {
    const app = await ready();
    saveButton(app).click();
    saveButton(app).click();
    await settle();
    expect(saveRequests(app.http)).toHaveLength(1);
    expect(textOf(saveButton(app))).toBe('Guardando…');
    expect(saveButton(app).disabled).toBe(true);
    for (const label of [VALUE.users, VALUE.storage, VALUE.calls]) {
      expect(valueField(app, label).disabled).toBe(true);
    }
    expect(slider(app).disabled).toBe(true);
  });

  it.each([
    ['no answer', respondNoConnection],
    ['a 500', (r: TestRequest) => respondError(r, 500, 'x')],
  ])('GU-6: %s shows T-SKO; «Reintentar» sends the same body (CA-13.6)', async (_case, respond) => {
    const app = await ready();
    respond(await pressSave(app));
    await settle();
    expect(says(app, 'No se pudo guardar la simulación')).toBe(true);
    expect(historyCards(app)).toEqual([]);
    expect(values(app)).toEqual(['15', '200', '50000']);
    buttonNamed(simulator(app), 'Reintentar')?.click();
    await settle();
    expect(expectSave(app.http).request.body).toEqual(NEW_SIMULATION);
  });

  it('GU-7: the card shows the amounts of the 201, not those of the quote (CA-13.5)', async () => {
    const app = await ready();
    created(await pressSave(app), {
      ...SIMULATION_1,
      tax_rate_bp: 2150,
      tax_cents: 3010,
      total_cents: 17010,
    });
    await settle();
    expect(termValue(historyCards(app)[0], 'Impuesto (21,5 %)')).toBe('30,10 €');
    expect(termValue(historyCards(app)[0], 'Total mensual')).toBe('170,10 €');
  });

  it('GU-8: a 422 «El país del cliente no está soportado» shows T-CNS without «Reintentar» (CA-13.7)', async () => {
    const app = await ready();
    const details = [{ field: 'customer_id', message: 'El país del cliente no está soportado' }];
    respondError(await pressSave(app), 422, errorBody('validation_error', 'x', details));
    await settle();
    expect(says(app, 'El país del cliente no está soportado')).toBe(true);
    expect(buttonNamed(simulator(app), 'Reintentar')).toBeUndefined();
  });

  it('GU-9: a 404 shows T-SKO without «Reintentar» (CA-13.8)', async () => {
    const app = await ready();
    respondError(await pressSave(app), 404, errorBody('not_found', 'x'));
    await settle();
    expect(says(app, 'No se pudo guardar la simulación')).toBe(true);
    expect(buttonNamed(simulator(app), 'Reintentar')).toBeUndefined();
  });

  it.each([
    ['users not valid', (app: AppHarness) => typeValue(app, VALUE.users, 'abc')],
    ['storage not valid', (app: AppHarness) => typeValue(app, VALUE.storage, '-1')],
    ['calls not valid', (app: AppHarness) => typeValue(app, VALUE.calls, '1.5')],
    ['the 300 ms wait', (app: AppHarness) => typeValue(app, VALUE.users, '60')],
    // The value goes back to the 15 of the quote shown, so only the clause under test can
    // disable the button (a different value already disables it through the quote's users).
    [
      'a quote on its way',
      async (app: AppHarness) => {
        await typeValue(app, VALUE.users, '60');
        await settle(300);
        await typeValue(app, VALUE.users, '15');
      },
    ],
    ['a failed quote', (app: AppHarness) => failingAgainAt15(app, respondNoConnection)],
    ['T-CNS', (app: AppHarness) => failingAgainAt15(app, unsupportedCountry)],
  ])('GU-10: with %s, «Guardar simulación» is off (CA-13.1)', async (_case, act) => {
    const app = await ready();
    await act(app);
    expect(saveButton(app).disabled).toBe(true);
  });

  it('GU-11: with the history in error, a 201 asks for its first page again (CA-10.9)', async () => {
    const app = await ready(null);
    respondError(expectHistory(app.http), 500, 'x');
    await settle();
    created(await pressSave(app));
    await settle();
    expectHistory(app.http).flush({ items: [SIMULATION_1], total: 1 });
    await settle();
    expect(historyCards(app)).toHaveLength(1);
  });

  it('CA-10.9: with the history still loading, a 201 drops that request and asks again', async () => {
    const app = await ready(null);
    const loading = expectHistory(app.http);
    created(await pressSave(app));
    await settle();
    expect(loading.cancelled).toBe(true);
    expectHistory(app.http);
  });

  it('GU-13: after T-SOK, changing a value removes it (CA-13.4)', async () => {
    const app = await ready();
    created(await pressSave(app));
    await settle();
    expect(says(app, 'Simulación guardada')).toBe(true);
    await typeValue(app, VALUE.storage, '201');
    expect(says(app, 'Simulación guardada')).toBe(false);
  });

  it('GU-14: saving twice the same values makes 2 requests and 2 cards (D-19)', async () => {
    const app = await ready();
    created(await pressSave(app));
    await settle();
    created(await pressSave(app), { ...SIMULATION_1, id: 2 });
    await settle();
    expect(historyCards(app)).toHaveLength(2);
  });
});
