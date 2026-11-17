import { TestBed } from '@angular/core/testing';
import { startApp } from '../testing/app';
import { expectList } from '../testing/customers';
import { expectHistory, openCard } from '../testing/detail';
import { settle, textOf } from '../testing/dom';
import { BACKEND, errorBody, respondError } from '../testing/http';
import { FRESH_NOW, setNow, storeRates } from '../testing/rates';
import { ACME, CUSTOMER_PAGE } from '../testing/spec-data';

const NARROW = ['card', 'narrow'];

function hasClasses(element: Element | null, classes: string[]): boolean {
  return element !== null && classes.every((name) => element.classList.contains(name));
}

// Spec 006 §6.2 (LY-1 to LY-8): RF-2 and RF-3.
describe('layout and titles (spec 006 §6.2)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('LY-1: the list has the title «Clientes» (CA-3.1)', async () => {
    const app = await startApp('/clientes');
    expect(textOf(app.root.querySelector('main h1'))).toBe('Clientes');
  });

  it.each([
    ['/clientes', 'app-customer-list-page'],
    ['/clientes/nuevo', 'app-customer-form-page'],
    ['/clientes/1', 'app-customer-detail-page'],
    ['/desconocida', 'app-not-found-page'],
  ])('LY-1 and CA-5.1: the screen %s enters with anim-page', async (url, tag) => {
    TestBed.resetTestingModule();
    const app = await startApp(url);
    const root = app.root.querySelector(`${tag} > *`);
    expect(root?.classList.contains('anim-page')).toBe(true);
  });

  it.each(['/clientes/nuevo', '/desconocida'])(
    'LY-2: %s shows a narrow centred card (CA-2.2)',
    async (url) => {
      const app = await startApp(url);
      expect(hasClasses(app.root.querySelector('main .card'), NARROW)).toBe(true);
    },
  );

  it('LY-3: «Cliente no encontrado» is a narrow centred card (CA-2.2)', async () => {
    const app = await startApp('/clientes/999');
    const req = app.http.expectOne(`${BACKEND}/customers/999`);
    respondError(req, 404, errorBody('not_found', 'x'));
    await settle();
    const card = app.root.querySelector('main .card');
    expect(textOf(card)).toContain('Cliente no encontrado');
    expect(hasClasses(card, NARROW)).toBe(true);
  });

  it('LY-4: the card has the sections «Simulador» and «Historial de simulaciones» (CA-3.2)', async () => {
    const app = await openCard();
    const titles = ['Simulador', 'Historial de simulaciones'];
    const sections = Array.from(app.root.querySelectorAll('main section[aria-labelledby]'));
    const named = sections.map((section) => {
      const id = section.getAttribute('aria-labelledby') ?? '';
      const title = app.root.querySelector(`#${CSS.escape(id)}`);
      return title?.tagName === 'H2' && section.contains(title) ? textOf(title) : '';
    });
    expect(named).toEqual(titles);
  });

  it('LY-5: from 1024 px the customer card and the simulator share a grid; the history is below (CA-2.4)', async () => {
    const app = await openCard();
    const grid = app.root.querySelector('main .detail-grid') as HTMLElement;
    expect(grid.classList.contains('lg:grid-cols-3')).toBe(true);
    expect(grid.querySelector('article')).not.toBeNull();
    expect(grid.querySelector('app-simulator')).not.toBeNull();
    expect(grid.querySelector('app-simulation-history')).toBeNull();
  });

  it('LY-6: each plan is a badge with the class of its plan and the text of 005 (CA-3.4)', async () => {
    const app = await startApp('/clientes');
    expectList(app.http).flush(CUSTOMER_PAGE);
    await settle();
    const badges = Array.from(app.root.querySelectorAll('main ul .badge'));
    expect(badges.map((badge) => [textOf(badge), badge.className])).toEqual([
      ['Business', 'badge badge-business'],
      ['Starter', 'badge badge-starter'],
      ['Enterprise', 'badge badge-enterprise'],
    ]);
  });

  it('LY-7: the initials «AT» are hidden from screen readers, in the list and on the card (CA-3.3)', async () => {
    const list = await startApp('/clientes');
    expectList(list.http).flush({ items: [ACME], total: 1 });
    await settle();
    const inList = list.root.querySelector('main ul .avatar');
    expect([textOf(inList), inList?.getAttribute('aria-hidden')]).toEqual(['AT', 'true']);
    TestBed.resetTestingModule();
    const card = await openCard();
    expectHistory(card.http);
    const onCard = card.root.querySelector('main article .avatar');
    expect([textOf(onCard), onCard?.getAttribute('aria-hidden')]).toEqual(['AT', 'true']);
  });

  it('LY-8: icons have no text and are hidden from screen readers (CA-3.5)', async () => {
    const app = await startApp('/clientes');
    const icons = Array.from(app.root.querySelectorAll('app-icon'));
    expect(icons.length).toBeGreaterThan(0);
    for (const icon of icons) {
      expect(icon.getAttribute('aria-hidden')).toBe('true');
      expect(textOf(icon)).toBe('');
    }
  });
});
