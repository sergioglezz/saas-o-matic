import { TestBed } from '@angular/core/testing';
import { AppHarness, startApp } from '../testing/app';
import { expectCreate, fillForm } from '../testing/customer-form';
import { customers, expectList, page } from '../testing/customers';
import { expectHistory, expectQuote, expectSave, openCard } from '../testing/detail';
import { buttonNamed, choose, settle, textOf } from '../testing/dom';
import { BACKEND, respondNoConnection } from '../testing/http';
import { RATES_URL, FRESH_NOW, setNow, storeRates } from '../testing/rates';
import { VALUE, openSimulator, saveButton, simulator, typeValue } from '../testing/simulator';
import { ACME, NEW_ACME, QUOTE_60, SIMULATION_1 } from '../testing/spec-data';

function riseIndexes(items: Element[]): string[] {
  return items.map((item) =>
    item.classList.contains('anim-rise')
      ? (item as HTMLElement).style.getPropertyValue('--i')
      : 'sin animación',
  );
}

function listItems(app: AppHarness): Element[] {
  return Array.from(app.root.querySelectorAll('main ul li')).filter((li) => li.querySelector('a'));
}

/** The innermost element that shows exactly `text`, and whether it (or a container) fades in. */
function fadesIn(root: Element, text: string): boolean {
  const all = Array.from(root.querySelectorAll('p, div, span'));
  const shown = all.filter((element) => textOf(element) === text).pop();
  return shown?.closest('.anim-fade') !== null && shown !== undefined;
}

function totalsPanel(app: AppHarness): Element | null {
  return simulator(app).querySelector('.totals-panel');
}

// Spec 006 §6.4 (AN-1 to AN-7): RF-5.
describe('animations (spec 006 §6.4)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('AN-1: the customer cards rise one after another (CA-5.2)', async () => {
    const app = await startApp('/clientes');
    expectList(app.http).flush(page(customers(3)));
    await settle();
    expect(riseIndexes(listItems(app))).toEqual(['0', '1', '2']);
  });

  it('AN-2: the cards of «Cargar más» go on with their position (CA-5.2)', async () => {
    const app = await startApp('/clientes');
    expectList(app.http).flush(page(customers(50), 120));
    await settle();
    buttonNamed(app.root, 'Cargar más')?.click();
    await settle();
    expectList(app.http).flush(page(customers(50, 51), 120));
    await settle();
    expect(riseIndexes(listItems(app)).slice(49, 52)).toEqual(['49', '50', '51']);
  });

  it('AN-3: the simulation cards rise one after another (CA-5.2)', async () => {
    const app = await openCard();
    const items = [3, 2, 1].map((id) => ({ ...SIMULATION_1, id }));
    expectHistory(app.http).flush({ items, total: 3 });
    await settle();
    const cards = Array.from(app.root.querySelectorAll('app-simulation-history li'));
    expect(riseIndexes(cards)).toEqual(['0', '1', '2']);
  });

  it('AN-4: T-REG, T-SOK, T-CON and T-RNO fade in (CA-5.3)', async () => {
    const created = await startApp('/clientes/nuevo');
    fillForm(created.root, NEW_ACME);
    buttonNamed(created.root, 'Guardar')?.click();
    await settle();
    expectCreate(created.http).flush(ACME, { status: 201, statusText: 'Created' });
    await settle();
    created.http.expectOne(`${BACKEND}/customers/1`).flush(ACME);
    await settle();
    expect(fadesIn(created.root, 'Cliente registrado')).toBe(true);

    TestBed.resetTestingModule();
    const saved = await openSimulator();
    saveButton(saved).click();
    await settle();
    expectSave(saved.http).flush(
      { ...SIMULATION_1, id: 2 },
      { status: 201, statusText: 'Created' },
    );
    await settle();
    expect(fadesIn(saved.root, 'Simulación guardada')).toBe(true);

    TestBed.resetTestingModule();
    localStorage.clear();
    const list = await startApp('/clientes');
    respondNoConnection(expectList(list.http));
    respondNoConnection(list.http.expectOne(RATES_URL));
    await settle();
    expect(fadesIn(list.root, 'No se pudo conectar con el servidor')).toBe(true);
    expect(fadesIn(list.root, 'Tipos de cambio no disponibles: importes en EUR')).toBe(true);
  });

  it('AN-5: an unfolded breakdown fades in (CA-5.4)', async () => {
    const app = await openCard();
    expectHistory(app.http).flush({ items: [SIMULATION_1], total: 1 });
    await settle();
    const card = app.root.querySelector('app-simulation-history article') as HTMLElement;
    buttonNamed(card, 'Ver desglose')?.click();
    await settle();
    expect(card.querySelector('table')?.closest('.anim-expand')).not.toBeNull();
  });

  it('AN-6: each new quote flashes the totals in a new block (CA-5.5)', async () => {
    const app = await openSimulator();
    const first = totalsPanel(app);
    expect(first?.classList.contains('anim-flash')).toBe(true);
    await typeValue(app, VALUE.users, '60');
    await settle(300);
    expectQuote(app.http).flush(QUOTE_60);
    await settle();
    const second = totalsPanel(app);
    expect(second?.classList.contains('anim-flash')).toBe(true);
    expect(second).not.toBe(first);
  });

  it('AN-7: changing the currency keeps the same totals block, without a new flash (CA-5.5)', async () => {
    const app = await openSimulator();
    const before = totalsPanel(app);
    choose(app.root.querySelector('header select') as HTMLSelectElement, 'USD');
    await settle();
    expect(textOf(before)).toContain('US$');
    expect(totalsPanel(app)).toBe(before);
  });
});
