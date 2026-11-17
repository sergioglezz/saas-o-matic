import { AppHarness } from '../../../testing/app';
import {
  expectHistory,
  expectQuote,
  expectSave,
  historyCards,
  openCard,
  termValue,
  tierRows,
} from '../../../testing/detail';
import { buttonNamed, choose, settle, textOf } from '../../../testing/dom';
import { FRESH_NOW, setNow, storeRates } from '../../../testing/rates';
import { saveButton, simulator, typeValue, VALUE } from '../../../testing/simulator';
import { QUOTE_15, SIMULATION_1 } from '../../../testing/spec-data';

const ORI = 'Conversión orientativa: los importes se calculan y guardan en EUR';

/** Spec 005 §6.4: the card of customer 1 with the starting quote and simulation. */
async function cardWithQuoteAndHistory(): Promise<AppHarness> {
  const app = await openCard();
  expectHistory(app.http).flush({ items: [SIMULATION_1], total: 1 });
  expectQuote(app.http).flush(QUOTE_15);
  await settle();
  return app;
}

async function chooseCurrency(app: AppHarness, code: string): Promise<void> {
  choose(app.root.querySelector('header select') as HTMLSelectElement, code);
  await settle();
}

function totals(root: Element): string[] {
  return ['Subtotal', 'Impuesto (21 %)', 'Total mensual'].map((label) => termValue(root, label));
}

// Spec 005 §6.4 (DV-2 to DV-5), HI-8, CO-15 and GU-12: RF-4 and RF-5 on the customer card.
describe('currency on the customer card (spec 005 §6.4)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('DV-2 and CO-15: USD converts simulator and history at once, asking nothing (CA-4.3, CA-12.10)', async () => {
    const app = await cardWithQuoteAndHistory();
    await chooseCurrency(app, 'USD');
    await settle(1000);
    const usd = ['151,52 US$', '31,82 US$', '183,34 US$'];
    expect(totals(simulator(app))).toEqual(usd);
    expect(totals(historyCards(app)[0])).toEqual(usd);
    app.http.verify();
  });

  it('DV-3: with USD, T-EQ and T-ORI (CA-4.7)', async () => {
    const app = await cardWithQuoteAndHistory();
    await chooseCurrency(app, 'USD');
    const header = textOf(app.root.querySelector('header'));
    expect(header).toContain('1 EUR = 1,0823 USD');
    expect(header).toContain(ORI);
  });

  it('DV-4: back to EUR shows the cents as they come, without T-EQ nor T-ORI (CA-5.3)', async () => {
    const app = await cardWithQuoteAndHistory();
    await chooseCurrency(app, 'USD');
    await chooseCurrency(app, 'EUR');
    expect(termValue(simulator(app), 'Total mensual')).toBe('169,40 €');
    expect(termValue(historyCards(app)[0], 'Total mensual')).toBe('169,40 €');
    const header = textOf(app.root.querySelector('header'));
    expect(header).not.toContain('1 EUR =');
    expect(header).not.toContain(ORI);
  });

  it('DV-5: CHF converts each amount on its own (CA-5.2, D-6)', async () => {
    const app = await cardWithQuoteAndHistory();
    await chooseCurrency(app, 'CHF');
    expect(totals(simulator(app))).toEqual(['131,05 CHF', '27,52 CHF', '158,58 CHF']);
  });

  it('HI-8: the breakdown of the history in USD (CA-5.2)', async () => {
    const app = await cardWithQuoteAndHistory();
    await chooseCurrency(app, 'USD');
    const [card] = historyCards(app);
    buttonNamed(card, 'Ver desglose')?.click();
    await settle();
    const rows = tierRows(card);
    expect(rows.map((row) => row[3])).toEqual(['10,82 US$', '8,66 US$', '5,41 US$']);
    expect(rows.map((row) => row[4])).toEqual(['108,23 US$', '43,29 US$', '0,00 US$']);
    expect(termValue(card, 'Total mensual')).toBe('183,34 US$');
  });

  it('GU-12: with USD, the new card of a 201 is in USD (CA-13.4)', async () => {
    const app = await cardWithQuoteAndHistory();
    await typeValue(app, VALUE.storage, '200');
    await typeValue(app, VALUE.calls, '50000');
    await chooseCurrency(app, 'USD');
    saveButton(app).click();
    await settle();
    expectSave(app.http).flush({ ...SIMULATION_1, id: 2 }, { status: 201, statusText: 'Created' });
    await settle();
    expect(historyCards(app)).toHaveLength(2);
    expect(termValue(historyCards(app)[0], 'Total mensual')).toBe('183,34 US$');
  });
});
