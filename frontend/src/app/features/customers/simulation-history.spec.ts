import { buttonNamed, settle, textOf } from '../../../testing/dom';
import {
  expectHistory,
  historyCards,
  historySection,
  openCard,
  termValue,
  tierHeaders,
  tierRows,
} from '../../../testing/detail';
import { queryOf, respondError } from '../../../testing/http';
import { FRESH_NOW, setNow, storeRates } from '../../../testing/rates';
import { SIMULATION_1 } from '../../../testing/spec-data';
import { Simulation } from '../../core/api/api-models';

const HI_3_ROWS = [
  ['1', '1 a 10', '10', '10,00 €', '100,00 €'],
  ['2', '11 a 50', '5', '8,00 €', '40,00 €'],
  ['3', '51 o más', '0', '5,00 €', '0,00 €'],
];

function simulations(...ids: number[]): Simulation[] {
  return ids.map((id) => ({ ...SIMULATION_1, id }));
}

// Spec 005 §6.9 (HI-1 to HI-7 and HI-9) and CM-12: RF-10, with the card of customer 1.
describe('simulation history (spec 005 §6.9)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('FI-1: once the card is shown, asks for the first page of the history (CA-10.1)', async () => {
    const app = await openCard();
    expect(queryOf(expectHistory(app.http))).toEqual({ limit: '50', offset: '0' });
  });

  it('HI-1: one card per simulation with its values and amounts (CA-10.2)', async () => {
    const app = await openCard();
    expectHistory(app.http).flush({ items: [SIMULATION_1], total: 1 });
    await settle();
    const [card] = historyCards(app);
    expect(textOf(card)).toContain('16/11/2026 11:00');
    expect(termValue(card, 'Usuarios activos')).toBe('15');
    expect(termValue(card, 'Almacenamiento')).toBe('200 GB');
    expect(termValue(card, 'Llamadas a la API al mes')).toBe('50.000');
    expect(termValue(card, 'Subtotal')).toBe('140,00 €');
    expect(termValue(card, 'Impuesto (21 %)')).toBe('29,40 €');
    expect(termValue(card, 'Total mensual')).toBe('169,40 €');
  });

  it('HI-2: the cards keep the order of the response (CA-10.1)', async () => {
    const app = await openCard();
    const items = simulations(3, 2, 1).map((s, i) => ({ ...s, active_users: 30 - i }));
    expectHistory(app.http).flush({ items, total: 3 });
    await settle();
    const users = historyCards(app).map((card) => termValue(card, 'Usuarios activos'));
    expect(users).toEqual(['30', '29', '28']);
  });

  it('HI-3 and HI-4: «Ver desglose» shows the tiers and «Ocultar desglose» hides them (CA-10.3)', async () => {
    const app = await openCard();
    expectHistory(app.http).flush({ items: [SIMULATION_1], total: 1 });
    await settle();
    const [card] = historyCards(app);
    expect(card.querySelector('table')).toBeNull();
    const show = buttonNamed(card, 'Ver desglose') as HTMLButtonElement;
    expect(show.getAttribute('aria-expanded')).toBe('false');
    show.click();
    await settle();
    expect(tierHeaders(card)).toEqual([
      'Tramo',
      'Usuarios',
      'Unidades',
      'Precio por usuario',
      'Importe',
    ]);
    expect(tierRows(card)).toEqual(HI_3_ROWS);
    const hide = buttonNamed(card, 'Ocultar desglose') as HTMLButtonElement;
    expect(hide.getAttribute('aria-expanded')).toBe('true');
    hide.click();
    await settle();
    expect(card.querySelector('table')).toBeNull();
    expect(buttonNamed(card, 'Ver desglose')).toBeDefined();
  });

  it('HI-5: no simulations show T-HVA (CA-10.5)', async () => {
    const app = await openCard();
    expectHistory(app.http).flush({ items: [], total: 0 });
    await settle();
    expect(textOf(historySection(app))).toContain('Este cliente aún no tiene simulaciones');
  });

  it('HI-6: while waiting, T-LHI with the customer card already shown (CA-10.4)', async () => {
    const app = await openCard();
    expect(textOf(historySection(app))).toContain('Cargando historial…');
    expect(textOf(app.root.querySelector('main h1'))).toBe('Acme Telecom S.L.');
  });

  it('HI-7: a 500 shows T-SRV in the history only; «Reintentar» asks again (CA-10.6)', async () => {
    const app = await openCard();
    respondError(expectHistory(app.http), 500, 'x');
    await settle();
    expect(textOf(historySection(app))).toContain('Error del servidor. Inténtalo de nuevo');
    expect(textOf(app.root.querySelector('main h1'))).toBe('Acme Telecom S.L.');
    buttonNamed(historySection(app), 'Reintentar')?.click();
    await settle();
    expectHistory(app.http).flush({ items: [SIMULATION_1], total: 1 });
    await settle();
    expect(historyCards(app)).toHaveLength(1);
  });

  it('HI-9: a tax rate of 0 bp shows «Impuesto (0 %)» «0,00 €» (CA-5.5)', async () => {
    const app = await openCard();
    const untaxed = { ...SIMULATION_1, tax_rate_bp: 0, tax_cents: 0, total_cents: 14000 };
    expectHistory(app.http).flush({ items: [untaxed], total: 1 });
    await settle();
    expect(termValue(historyCards(app)[0], 'Impuesto (0 %)')).toBe('0,00 €');
  });

  it('CM-12: «Cargar más» asks for the next page of the history (CA-10.7)', async () => {
    const app = await openCard();
    const first = Array.from({ length: 50 }, (_, i) => ({ ...SIMULATION_1, id: 60 - i }));
    expectHistory(app.http).flush({ items: first, total: 60 });
    await settle();
    expect(textOf(historySection(app))).toContain('Mostrando 50 de 60');
    buttonNamed(historySection(app), 'Cargar más')?.click();
    await settle();
    expect(queryOf(expectHistory(app.http))).toEqual({ limit: '50', offset: '50' });
  });
});
