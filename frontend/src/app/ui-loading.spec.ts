import { AppHarness, startApp } from '../testing/app';
import { expectList } from '../testing/customers';
import { expectHistory, expectQuote, historySection, openCard } from '../testing/detail';
import { settle, textOf } from '../testing/dom';
import { BACKEND } from '../testing/http';
import { FRESH_NOW, setNow, storeRates } from '../testing/rates';
import { VALUE, openSimulator, simulator, typeValue } from '../testing/simulator';
import { ACME, CUSTOMER_PAGE, SIMULATION_1 } from '../testing/spec-data';

/** Skeletons inside `root`, each one hidden from screen readers by itself or an ancestor. */
function skeletons(root: Element | null): Element[] {
  const found = Array.from(root?.querySelectorAll('.skeleton') ?? []);
  for (const skeleton of found) {
    expect(skeleton.closest('[aria-hidden="true"]')).not.toBeNull();
  }
  return found;
}

function main(app: AppHarness): HTMLElement {
  return app.root.querySelector('main') as HTMLElement;
}

// Spec 006 §6.3 (SK-1 to SK-4): RF-4.
describe('loading states (spec 006 §6.3)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('SK-1: the list shows T-LCL and skeletons until it arrives (CA-4.1)', async () => {
    const app = await startApp('/clientes');
    expect(textOf(main(app))).toContain('Cargando clientes…');
    expect(skeletons(main(app)).length).toBeGreaterThanOrEqual(3);
    expectList(app.http).flush(CUSTOMER_PAGE);
    await settle();
    expect(skeletons(main(app))).toEqual([]);
  });

  it('SK-2: the card shows T-LCU and skeletons until it arrives (CA-4.1)', async () => {
    const app = await startApp('/clientes/1');
    expect(textOf(main(app))).toContain('Cargando cliente…');
    expect(skeletons(main(app)).length).toBeGreaterThan(0);
    app.http.expectOne(`${BACKEND}/customers/1`).flush(ACME);
    await settle();
    expect(main(app).querySelector('article .skeleton')).toBeNull();
  });

  it('SK-3: the history shows T-LHI and skeletons until it arrives (CA-4.1)', async () => {
    const app = await openCard();
    expect(textOf(historySection(app))).toContain('Cargando historial…');
    expect(skeletons(historySection(app)).length).toBeGreaterThan(0);
    expectHistory(app.http).flush({ items: [SIMULATION_1], total: 1 });
    await settle();
    expect(skeletons(historySection(app))).toEqual([]);
  });

  it('SK-4: T-UPD comes with a spinning icon hidden from screen readers (CA-4.2)', async () => {
    const app = await openSimulator();
    await typeValue(app, VALUE.users, '60');
    const updating = Array.from(simulator(app).querySelectorAll('p')).find(
      (p) => textOf(p) === 'Actualizando…',
    );
    const icon = updating?.querySelector('.spin');
    expect(icon?.getAttribute('aria-hidden')).toBe('true');
    await settle(300);
    expectQuote(app.http);
  });
});
