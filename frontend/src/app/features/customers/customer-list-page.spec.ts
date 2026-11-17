import { AppHarness, clickAndSettle, startApp } from '../../../testing/app';
import {
  customerLinks,
  customerNames,
  expectList,
  listRequests,
  page,
  searchBox,
} from '../../../testing/customers';
import {
  buttonNamed,
  controlLabelled,
  linkNamed,
  settle,
  textOf,
  typeInto,
} from '../../../testing/dom';
import { queryOf, respondError, respondNoConnection } from '../../../testing/http';
import { FRESH_NOW, setNow, storeRates } from '../../../testing/rates';
import { ACME, CUSTOMER_PAGE } from '../../../testing/spec-data';

const NO_QUERY = { limit: '50', offset: '0' };

async function openList(): Promise<AppHarness> {
  const app = await startApp('/clientes');
  return app;
}

async function search(app: AppHarness, text: string, wait = 300): Promise<void> {
  typeInto(searchBox(app.root), text);
  await settle(wait);
}

function main(app: AppHarness): HTMLElement {
  return app.root.querySelector('main') as HTMLElement;
}

// Spec 005 §6.5 (LI-1 to LI-19): RF-6, and RF-2 on the list.
describe('customer list (spec 005 §6.5)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('LI-1: empty search, the first page and the customers in order (CA-6.1, CA-6.3)', async () => {
    const app = await openList();
    const box = controlLabelled(app.root, 'Buscar por empresa o identificador fiscal');
    expect(box.value).toBe('');
    const req = expectList(app.http);
    expect(queryOf(req)).toEqual(NO_QUERY);
    req.flush(CUSTOMER_PAGE);
    await settle();
    expect(customerNames(app.root)).toEqual([
      'Acme Telecom S.L.',
      'Albion Connect Ltd',
      'Liberty Mesh Inc.',
    ]);
  });

  it('LI-2 and LI-3: company, tax id, country and plan of each customer (CA-6.2)', async () => {
    const app = await openList();
    const mexican = { ...ACME, id: 7, country: 'MX' };
    expectList(app.http).flush(page([ACME, mexican]));
    await settle();
    const [acme, other] = customerLinks(app.root).map((link) => textOf(link));
    for (const text of ['Acme Telecom S.L.', 'B12345674', 'España', 'Business']) {
      expect(acme).toContain(text);
    }
    expect(other).toContain('MX');
    expect(other).not.toContain('España');
  });

  it('LI-4 and LI-5: the search goes 300 ms after the last change, not at 299 (CA-6.4)', async () => {
    const app = await openList();
    expectList(app.http).flush(CUSTOMER_PAGE);
    await search(app, 'acme', 299);
    expect(listRequests(app.http)).toEqual([]);
    await settle(1);
    expect(queryOf(expectList(app.http))).toEqual({ ...NO_QUERY, q: 'acme' });
  });

  it('LI-6: several changes less than 300 ms apart make one request (CA-6.5)', async () => {
    const app = await openList();
    expectList(app.http).flush(CUSTOMER_PAGE);
    for (const text of ['a', 'ac', 'acm']) {
      await search(app, text, 100);
    }
    await search(app, 'acme');
    const requests = listRequests(app.http);
    expect(requests.map((r) => queryOf(r)['q'])).toEqual(['acme']);
  });

  it('LI-7 and LI-8: no results show T-NOR with the trimmed text; q keeps its spaces (CA-6.9)', async () => {
    const app = await openList();
    expectList(app.http).flush(CUSTOMER_PAGE);
    await search(app, '  zzz  ');
    const req = expectList(app.http);
    expect(queryOf(req)['q']).toBe('  zzz  ');
    req.flush(page([]));
    await settle();
    expect(textOf(main(app))).toContain('Ningún cliente coincide con «zzz»');
    expect(linkNamed(main(app), 'Nuevo cliente')).toBeDefined();
  });

  it.each(['', '   '])('LI-9: the search %j goes without q (CA-6.4)', async (text) => {
    const app = await openList();
    expectList(app.http).flush(CUSTOMER_PAGE);
    await search(app, 'acme');
    expectList(app.http).flush(page([ACME]));
    await search(app, text);
    expect(queryOf(expectList(app.http))).toEqual(NO_QUERY);
  });

  it('LI-10: no customers and no search show T-EMP and «Nuevo cliente» (CA-6.8)', async () => {
    const app = await openList();
    expectList(app.http).flush(page([]));
    await settle();
    expect(textOf(main(app))).toContain('Todavía no hay clientes');
    expect(linkNamed(main(app), 'Nuevo cliente')).toBeDefined();
  });

  it('LI-11: q reaches the backend as written', async () => {
    const app = await openList();
    expectList(app.http).flush(CUSTOMER_PAGE);
    await search(app, 'a&b=c%');
    expect(queryOf(expectList(app.http))['q']).toBe('a&b=c%');
  });

  it('LI-12: an old search is dropped and only the last one is shown (CA-6.6)', async () => {
    const app = await openList();
    expectList(app.http).flush(CUSTOMER_PAGE);
    await search(app, 'ac');
    const slow = expectList(app.http);
    await search(app, 'acme');
    const fast = expectList(app.http);
    expect(slow.cancelled).toBe(true);
    fast.flush(page([ACME]));
    await settle();
    expect(customerNames(app.root)).toEqual(['Acme Telecom S.L.']);
  });

  it('LI-13: the search box has a native limit of 120 characters (CA-6.3)', async () => {
    const app = await openList();
    expect(searchBox(app.root).maxLength).toBe(120);
  });

  it('LI-14: while waiting, T-LCL and the search box stays editable (CA-6.7)', async () => {
    const app = await openList();
    expect(textOf(main(app))).toContain('Cargando clientes…');
    expect(searchBox(app.root).disabled).toBe(false);
    expect(searchBox(app.root).readOnly).toBe(false);
  });

  it('LI-15: no answer shows T-CON; «Reintentar» repeats the same search and keeps the text (CA-6.10)', async () => {
    const app = await openList();
    expectList(app.http).flush(CUSTOMER_PAGE);
    await search(app, 'acme');
    respondNoConnection(expectList(app.http));
    await settle();
    expect(textOf(main(app))).toContain('No se pudo conectar con el servidor');
    expect(searchBox(app.root).value).toBe('acme');
    buttonNamed(main(app), 'Reintentar')?.click();
    await settle();
    expect(queryOf(expectList(app.http))).toEqual({ ...NO_QUERY, q: 'acme' });
    expect(textOf(main(app))).toContain('Cargando clientes…');
  });

  it('LI-16: a 500 shows T-SRV with «Reintentar» (CA-2.3)', async () => {
    const app = await openList();
    respondError(expectList(app.http), 500, 'x');
    await settle();
    expect(textOf(main(app))).toContain('Error del servidor. Inténtalo de nuevo');
    expect(buttonNamed(main(app), 'Reintentar')).toBeDefined();
  });

  it('LI-17: each customer is a link to its card (CA-6.11)', async () => {
    const app = await openList();
    expectList(app.http).flush(CUSTOMER_PAGE);
    await settle();
    const acme = customerLinks(app.root)[0];
    expect(acme.getAttribute('href')).toBe('/clientes/1');
    await clickAndSettle(acme);
    expect(app.router.url).toBe('/clientes/1');
  });

  it('LI-18: «Nuevo cliente» opens the form (CA-6.3)', async () => {
    const app = await openList();
    await clickAndSettle(linkNamed(main(app), 'Nuevo cliente'));
    expect(app.router.url).toBe('/clientes/nuevo');
  });

  it('LI-19: a company name that looks like HTML is shown as text (RNF-6)', async () => {
    const app = await openList();
    expectList(app.http).flush(page([{ ...ACME, company_name: '<b>Acme</b>' }]));
    await settle();
    expect(customerNames(app.root)).toEqual(['<b>Acme</b>']);
    expect(main(app).querySelector('ul b')).toBeNull();
  });
});
