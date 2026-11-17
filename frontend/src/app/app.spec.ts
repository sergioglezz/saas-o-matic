import { HttpTestingController } from '@angular/common/http/testing';
import { AppHarness, clickAndSettle, reloadApp, startApp } from '../testing/app';
import { choose, linkNamed, settle, textOf } from '../testing/dom';
import { pendingBackend, respondNoConnection } from '../testing/http';
import { FRESH_NOW, RATES_URL, STALE_NOW, answerRates, setNow, storeRates } from '../testing/rates';

const SCREENS = ['/clientes', '/clientes/nuevo', '/clientes/1', '/desconocida'];

function header(app: AppHarness): HTMLElement {
  return app.root.querySelector('header') as HTMLElement;
}

function currencySelect(app: AppHarness): HTMLSelectElement {
  return header(app).querySelector('select') as HTMLSelectElement;
}

function ratesRequestCount(http: HttpTestingController): number {
  return http.match(RATES_URL).length;
}

// Spec 005 RF-1 (CA-1.1 to CA-1.7) and RF-3 between screens (CA-3.11, CA-3.12).
describe('app shell and routes (spec 005 RF-1)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('FI-6: «/» opens the list and changes the address to /clientes (CA-1.2)', async () => {
    const app = await startApp('/');
    expect(app.router.url).toBe('/clientes');
    expect(app.root.querySelector('app-customer-list-page')).not.toBeNull();
  });

  it.each(['/clientes/1/otra', '/desconocida'])(
    'FI-6: %s shows T-NFP with «Volver al listado» and asks the backend nothing (CA-1.3)',
    async (url) => {
      const app = await startApp(url);
      expect(textOf(app.root.querySelector('main'))).toContain('Página no encontrada');
      expect(linkNamed(app.root, 'Volver al listado')?.getAttribute('href')).toBe('/clientes');
      expect(pendingBackend(app.http)).toEqual([]);
      await clickAndSettle(linkNamed(app.root, 'Volver al listado'));
      expect(app.router.url).toBe('/clientes');
    },
  );

  it.each([
    ['/clientes', 'app-customer-list-page'],
    ['/clientes/nuevo', 'app-customer-form-page'],
    ['/clientes/1', 'app-customer-detail-page'],
  ])('FI-7: opening or reloading %s shows that screen (CA-1.1, CA-1.4)', async (url, tag) => {
    const app = await startApp(url);
    expect(app.router.url).toBe(url);
    expect(app.root.querySelector(tag)).not.toBeNull();
  });

  it('FI-8: the name «SaaS-O-Matic» opens /clientes from any screen (CA-1.5)', async () => {
    const app = await startApp('/clientes/1');
    const brand = linkNamed(header(app), 'SaaS-O-Matic');
    expect(brand?.getAttribute('href')).toBe('/clientes');
    await clickAndSettle(brand);
    expect(app.router.url).toBe('/clientes');
  });

  it('CA-1.5: every screen shows the header with the name, the selector and the rates line', async () => {
    for (const url of SCREENS) {
      const app = await reloadApp(url);
      expect(linkNamed(header(app), 'SaaS-O-Matic')).toBeDefined();
      expect(currencySelect(app)).not.toBeNull();
      expect(textOf(header(app))).toContain('Tasas del 16/11/2026');
    }
  });

  it('TC-13: going through the screens and changing currency 3 times asks the rates once (CA-1.6, CA-3.12)', async () => {
    localStorage.clear();
    const app = await startApp('/clientes');
    answerRates(app.http);
    await settle();
    for (const [url, code] of [
      ['/clientes/nuevo', 'USD'],
      ['/clientes/1', 'GBP'],
      ['/clientes', 'CHF'],
    ]) {
      choose(currencySelect(app), code);
      await settle();
      await app.router.navigateByUrl(url);
      await settle();
      expect(currencySelect(app).value).toBe(code);
    }
    expect(ratesRequestCount(app.http)).toBe(0);
  });

  it.each([
    ['TC-1 (fresh)', 'fresh'],
    ['TC-5 (stale, failed)', 'stale'],
    ['TC-8 (unavailable)', 'unavailable'],
    ['TC-14 (loading)', 'loading'],
  ])('TC-16: in %s, T-ATR is a link on the four screens (CA-3.11)', async (_case, state) => {
    localStorage.clear();
    if (state === 'stale') {
      storeRates();
      setNow(STALE_NOW);
    }
    const app = await startApp('/clientes');
    if (state === 'fresh') {
      answerRates(app.http);
    } else if (state !== 'loading') {
      respondNoConnection(app.http.expectOne(RATES_URL));
    }
    await settle();
    for (const url of SCREENS) {
      await app.router.navigateByUrl(url);
      await settle();
      const link = linkNamed(header(app), 'Rates By Exchange Rate API');
      expect(link?.getAttribute('href')).toBe('https://www.exchangerate-api.com');
    }
  });
});
