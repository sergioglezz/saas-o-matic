import { AppHarness, startApp } from '../../../testing/app';
import {
  customerNames,
  customers,
  expectList,
  listRequests,
  page,
  searchBox,
} from '../../../testing/customers';
import { buttonNamed, settle, textOf, typeInto } from '../../../testing/dom';
import { queryOf, respondNoConnection } from '../../../testing/http';
import { FRESH_NOW, setNow, storeRates } from '../../../testing/rates';

function main(app: AppHarness): HTMLElement {
  return app.root.querySelector('main') as HTMLElement;
}

function loadMoreButton(app: AppHarness): HTMLButtonElement | undefined {
  return buttonNamed(main(app), 'Cargar más') ?? buttonNamed(main(app), 'Cargando…');
}

/** The list open with its first page already shown. */
async function listWith(first: ReturnType<typeof page>): Promise<AppHarness> {
  const app = await startApp('/clientes');
  expectList(app.http).flush(first);
  await settle();
  return app;
}

async function clickLoadMore(app: AppHarness): Promise<void> {
  loadMoreButton(app)?.click();
  await settle();
}

// Spec 005 §6.6 (CM-1 to CM-11): RF-7 on the customer list.
describe('«Cargar más» in the customer list (spec 005 §6.6)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('CM-1: total 120 and 50 shown: T-MOS and «Cargar más» (CA-7.1)', async () => {
    const app = await listWith(page(customers(50), 120));
    expect(textOf(main(app))).toContain('Mostrando 50 de 120');
    expect(buttonNamed(main(app), 'Cargar más')).toBeDefined();
  });

  it('CM-2 and CM-3: each page asks from the number shown until all are shown (CA-7.2, CA-7.6)', async () => {
    const app = await listWith(page(customers(50), 120));
    await clickLoadMore(app);
    const second = expectList(app.http);
    expect(queryOf(second)).toEqual({ limit: '50', offset: '50' });
    second.flush(page(customers(50, 51), 120));
    await settle();
    expect(customerNames(app.root)).toHaveLength(100);
    expect(textOf(main(app))).toContain('Mostrando 100 de 120');
    await clickLoadMore(app);
    const third = expectList(app.http);
    expect(queryOf(third)['offset']).toBe('100');
    third.flush(page(customers(20, 101), 120));
    await settle();
    expect(customerNames(app.root)).toHaveLength(120);
    expect(textOf(main(app))).not.toContain('Mostrando');
    expect(loadMoreButton(app)).toBeUndefined();
  });

  it('CM-4: total 50 with 50 shown: no T-MOS nor «Cargar más» (CA-7.6)', async () => {
    const app = await listWith(page(customers(50), 50));
    expect(textOf(main(app))).not.toContain('Mostrando');
    expect(loadMoreButton(app)).toBeUndefined();
  });

  it('CM-5: total 51 with 50 shown (CA-7.1)', async () => {
    const app = await listWith(page(customers(50), 51));
    expect(textOf(main(app))).toContain('Mostrando 50 de 51');
  });

  it('CM-6: pressing twice makes one request; the button shows T-LMO disabled (CA-7.4)', async () => {
    const app = await listWith(page(customers(50), 120));
    const button = loadMoreButton(app) as HTMLButtonElement;
    button.click();
    button.click();
    await settle();
    expect(listRequests(app.http)).toHaveLength(1);
    const waiting = loadMoreButton(app) as HTMLButtonElement;
    expect(textOf(waiting)).toBe('Cargando…');
    expect(waiting.disabled).toBe(true);
    waiting.click();
    await settle();
    expect(listRequests(app.http)).toEqual([]);
  });

  it('CM-7: a failed page keeps the 50 and «Reintentar» repeats offset=50 (CA-7.5)', async () => {
    const app = await listWith(page(customers(50), 120));
    await clickLoadMore(app);
    respondNoConnection(expectList(app.http));
    await settle();
    expect(customerNames(app.root)).toHaveLength(50);
    expect(textOf(main(app))).toContain('No se pudo conectar con el servidor');
    buttonNamed(main(app), 'Reintentar')?.click();
    await settle();
    expect(queryOf(expectList(app.http))['offset']).toBe('50');
  });

  it('CM-8: the next page of a search keeps q (CA-7.2)', async () => {
    const app = await listWith(page(customers(50), 120));
    typeInto(searchBox(app.root), 'acme');
    await settle(300);
    expectList(app.http).flush(page(customers(50), 70));
    await settle();
    await clickLoadMore(app);
    expect(queryOf(expectList(app.http))).toEqual({ q: 'acme', limit: '50', offset: '50' });
  });

  it('CM-9: with 100 shown, a new search goes back to offset 0 (CA-7.7)', async () => {
    const app = await listWith(page(customers(50), 120));
    await clickLoadMore(app);
    expectList(app.http).flush(page(customers(50, 51), 120));
    await settle();
    typeInto(searchBox(app.root), 'zz');
    await settle(300);
    const req = expectList(app.http);
    expect(queryOf(req)).toEqual({ q: 'zz', limit: '50', offset: '0' });
    req.flush(page(customers(2, 500), 2));
    await settle();
    expect(customerNames(app.root)).toEqual(['Cliente 500', 'Cliente 501']);
  });

  it('CM-10: an id already shown appears once (CA-7.2)', async () => {
    const app = await listWith(page(customers(50), 120));
    await clickLoadMore(app);
    expectList(app.http).flush(page(customers(50, 50), 120));
    await settle();
    expect(customerNames(app.root)).toHaveLength(99);
    expect(customerNames(app.root).filter((n) => n === 'Cliente 50')).toHaveLength(1);
  });

  it('CM-11: the total of the last page is the one shown (CA-7.3)', async () => {
    const app = await listWith(page(customers(50), 120));
    await clickLoadMore(app);
    expectList(app.http).flush(page(customers(50, 51), 121));
    await settle();
    expect(textOf(main(app))).toContain('Mostrando 100 de 121');
  });
});
