import { TestBed } from '@angular/core/testing';
import { HttpTestingController, TestRequest } from '@angular/common/http/testing';
import { AppHarness } from '../../../testing/app';
import { expectList } from '../../../testing/customers';
import { expectHistory, openCard } from '../../../testing/detail';
import { buttonNamed, settle, textOf } from '../../../testing/dom';
import {
  BACKEND,
  pendingBackend,
  respondError,
  respondNoConnection,
} from '../../../testing/http';
import { FRESH_NOW, setNow, storeRates } from '../../../testing/rates';
import { SIMULATION_1 } from '../../../testing/spec-data';

const DELETE_URL = `${BACKEND}/customers/1`;
const QUESTION = '¿Borrar «Acme Telecom S.L.»?';
const HISTORY_SENTENCES = [
  'Se borrarán también sus',
  'Se borrará también su simulación.',
  'Se borrará también todo su historial de simulaciones.',
];

function deleteRequests(http: HttpTestingController): TestRequest[] {
  return http.match((r) => r.method === 'DELETE' && r.url === DELETE_URL);
}

function confirmation(app: AppHarness): HTMLElement | null {
  return app.root.querySelector<HTMLElement>('[role="alertdialog"]');
}

function press(app: AppHarness, label: string): HTMLButtonElement {
  const button = buttonNamed(app.root, label);
  if (button === undefined) {
    throw new Error(`No hay ningún botón «${label}»`);
  }
  button.click();
  return button;
}

/** The card of Acme with `total` simulations in its history. */
async function cardWithHistory(total: number): Promise<AppHarness> {
  const app = await openCard();
  const items = Array.from({ length: total }, (_, i) => ({ ...SIMULATION_1, id: i + 1 }));
  expectHistory(app.http).flush({ items, total });
  await settle();
  return app;
}

async function askToDelete(app: AppHarness): Promise<void> {
  press(app, 'Borrar cliente');
  await settle();
}

async function confirmDelete(total = 3): Promise<{ app: AppHarness; req: TestRequest }> {
  const app = await cardWithHistory(total);
  await askToDelete(app);
  press(app, 'Sí, borrar');
  await settle();
  const [req] = deleteRequests(app.http);
  return { app, req };
}

// Spec 007 §4.2 (BF-1 to BF-9): RF-2, deleting a customer from its card.
describe('delete a customer (spec 007 §4.2)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('BF-1: the card of Acme has the button «Borrar cliente» (CA-2.1)', async () => {
    const app = await cardWithHistory(0);
    const card = app.root.querySelector('.customer-card');
    expect(buttonNamed(card as HTMLElement, 'Borrar cliente')).toBeDefined();
    expect(confirmation(app)).toBeNull();
  });

  it('BF-2: asks first, with the history and the warning, and asks the backend nothing (CA-2.2, CA-2.3)', async () => {
    const app = await cardWithHistory(3);
    pendingBackend(app.http);
    await askToDelete(app);
    const box = confirmation(app);
    expect(textOf(box)).toContain(QUESTION);
    expect(textOf(box)).toContain('Se borrarán también sus 3 simulaciones.');
    expect(textOf(box)).toContain('Esta acción no se puede deshacer.');
    expect(buttonNamed(box as HTMLElement, 'Sí, borrar')).toBeDefined();
    expect(buttonNamed(box as HTMLElement, 'Cancelar')).toBeDefined();
    expect(box?.contains(document.activeElement)).toBe(true);
    expect(pendingBackend(app.http)).toEqual([]);
  });

  it('BF-3: one simulation, none, or a history not loaded yet (CA-2.3)', async () => {
    const one = await cardWithHistory(1);
    await askToDelete(one);
    expect(textOf(confirmation(one))).toContain('Se borrará también su simulación.');
    TestBed.resetTestingModule(); // the card is opened again in the same test

    const none = await cardWithHistory(0);
    await askToDelete(none);
    for (const sentence of HISTORY_SENTENCES) {
      expect(textOf(confirmation(none))).not.toContain(sentence);
    }
    TestBed.resetTestingModule(); // the card is opened again in the same test

    const loading = await openCard();
    await askToDelete(loading);
    expect(textOf(confirmation(loading))).toContain(
      'Se borrará también todo su historial de simulaciones.',
    );
  });

  it('BF-3: a history that failed gives no number either (CA-2.3)', async () => {
    const app = await openCard();
    respondError(expectHistory(app.http), 500);
    await settle();
    await askToDelete(app);
    expect(textOf(confirmation(app))).toContain(
      'Se borrará también todo su historial de simulaciones.',
    );
  });

  it('BF-4: «Cancelar» closes it without asking and the focus goes back (CA-2.4)', async () => {
    const app = await cardWithHistory(3);
    await askToDelete(app);
    press(app, 'Cancelar');
    await settle();
    expect(confirmation(app)).toBeNull();
    expect(deleteRequests(app.http)).toEqual([]);
    expect(document.activeElement).toBe(buttonNamed(app.root, 'Borrar cliente'));
  });

  it('BF-4: Escape closes it too (CA-2.4)', async () => {
    const app = await cardWithHistory(3);
    await askToDelete(app);
    const box = confirmation(app);
    box?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    await settle();
    expect(confirmation(app)).toBeNull();
    expect(deleteRequests(app.http)).toEqual([]);
    expect(document.activeElement).toBe(buttonNamed(app.root, 'Borrar cliente'));
  });

  it('BF-5: «Sí, borrar» twice makes one DELETE without a body, and waits «Borrando…» (CA-2.5)', async () => {
    const app = await cardWithHistory(3);
    await askToDelete(app);
    const yes = press(app, 'Sí, borrar');
    await settle();
    yes.click();
    await settle();
    const requests = deleteRequests(app.http);
    expect(requests).toHaveLength(1);
    expect(requests[0].request.body).toBeNull();
    expect(textOf(yes)).toBe('Borrando…');
    expect(yes.disabled).toBe(true);
  });

  it('BF-6: after a 204, the list with the notice, which is gone after leaving it (CA-2.6)', async () => {
    const { app, req } = await confirmDelete();
    req.flush(null, { status: 204, statusText: 'No Content' });
    await settle();
    expect(app.router.url).toBe('/clientes');
    expectList(app.http);
    const notice = app.root.querySelector('.notice-success');
    expect(textOf(notice)).toBe('Cliente «Acme Telecom S.L.» borrado');
    expect(notice?.getAttribute('role')).toBe('status');

    await app.router.navigateByUrl('/clientes/nuevo');
    await settle();
    await app.router.navigateByUrl('/clientes');
    await settle();
    expectList(app.http);
    expect(textOf(app.root)).not.toContain('borrado');
  });

  it('BF-7: a 404 shows «Cliente no encontrado» (CA-2.7)', async () => {
    const { app, req } = await confirmDelete();
    respondError(req, 404, {
      error: { code: 'not_found', message: 'Recurso no encontrado', details: [] },
    });
    await settle();
    expect(textOf(app.root.querySelector('h1'))).toBe('Cliente no encontrado');
    expect(confirmation(app)).toBeNull();
  });

  it('BF-8: no answer gives «No se pudo borrar el cliente», and «Reintentar» asks again (CA-2.8)', async () => {
    const { app, req } = await confirmDelete();
    respondNoConnection(req);
    await settle();
    expect(textOf(confirmation(app))).toContain('No se pudo borrar el cliente');
    expect(app.router.url).toBe('/clientes/1');
    expect(textOf(app.root.querySelector('.customer-card h1'))).toBe('Acme Telecom S.L.');

    press(app, 'Reintentar');
    await settle();
    expect(deleteRequests(app.http)).toHaveLength(1);
  });

  it('BF-8: a 500 gives the same message (CA-2.8)', async () => {
    const { app, req } = await confirmDelete();
    respondError(req, 500, {
      error: { code: 'internal_error', message: 'Error interno del servidor', details: [] },
    });
    await settle();
    expect(textOf(confirmation(app))).toContain('No se pudo borrar el cliente');
    expect(textOf(confirmation(app))).not.toContain('500');
    expect(buttonNamed(confirmation(app) as HTMLElement, 'Reintentar')).toBeDefined();
  });

  it('BF-9: the confirmation is an alertdialog named by its question (CA-2.2)', async () => {
    const app = await cardWithHistory(3);
    await askToDelete(app);
    const box = confirmation(app);
    const nameId = box?.getAttribute('aria-labelledby') ?? '';
    expect(textOf(document.getElementById(nameId))).toBe(QUESTION);
  });

  it('CA-2.9: red buttons, and the confirmation and the notice fade in (spec 006)', async () => {
    const app = await cardWithHistory(3);
    expect(buttonNamed(app.root, 'Borrar cliente')?.classList).toContain('danger-outline');
    await askToDelete(app);
    expect(confirmation(app)?.classList).toContain('anim-fade');
    expect(buttonNamed(app.root, 'Sí, borrar')?.classList).toContain('danger');

    press(app, 'Sí, borrar');
    await settle();
    deleteRequests(app.http)[0].flush(null, { status: 204, statusText: 'No Content' });
    await settle();
    expect(app.root.querySelector('.notice-success')?.classList).toContain('anim-fade');
  });
});
