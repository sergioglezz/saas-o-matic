import { HttpTestingController, TestRequest } from '@angular/common/http/testing';
import { AppHarness, clickAndSettle, startApp } from '../../../testing/app';
import { expectCreate, fillForm } from '../../../testing/customer-form';
import { expectList } from '../../../testing/customers';
import { buttonNamed, linkNamed, settle, textOf } from '../../../testing/dom';
import { BACKEND, errorBody, pendingBackend, respondError } from '../../../testing/http';
import { FRESH_NOW, setNow, storeRates } from '../../../testing/rates';
import { ACME, CUSTOMER_PAGE, NEW_ACME } from '../../../testing/spec-data';

function expectCustomer(http: HttpTestingController, id = '1'): TestRequest {
  return http.expectOne({ method: 'GET', url: `${BACKEND}/customers/${id}` });
}

function main(app: AppHarness): HTMLElement {
  return app.root.querySelector('main') as HTMLElement;
}

/** The value next to a label of the customer card (CA-9.3). */
function cardValue(app: AppHarness, label: string): string {
  const term = Array.from(main(app).querySelectorAll('dt')).find((dt) => textOf(dt) === label);
  return textOf(term?.nextElementSibling);
}

async function registerAcme(app: AppHarness, created = ACME): Promise<void> {
  fillForm(app.root, NEW_ACME);
  buttonNamed(app.root, 'Guardar')?.click();
  await settle();
  expectCreate(app.http).flush(created, { status: 201, statusText: 'Created' });
  await settle();
}

// Spec 005 §6.8 (FI-1 to FI-9): RF-9, and the end of the new customer flow (AL-5, AL-18).
describe('customer card (spec 005 §6.8)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('FI-1: asks for the customer and shows its card (CA-9.1, CA-9.3)', async () => {
    const app = await startApp('/clientes/1');
    expectCustomer(app.http).flush(ACME);
    await settle();
    expect(textOf(main(app).querySelector('h1'))).toBe('Acme Telecom S.L.');
    expect(cardValue(app, 'Identificador fiscal')).toBe('B12345674');
    expect(cardValue(app, 'Email de contacto')).toBe('compras@acme.example');
    expect(cardValue(app, 'País')).toBe('España');
    expect(cardValue(app, 'Plan')).toBe('Business');
    expect(cardValue(app, 'Fecha de alta')).toBe('13/11/2026');
  });

  it('FI-2: while waiting, T-LCU and nothing else is asked (CA-9.2)', async () => {
    const app = await startApp('/clientes/1');
    expect(textOf(main(app))).toContain('Cargando cliente…');
    expect(pendingBackend(app.http).map((r) => r.request.urlWithParams)).toEqual([
      `${BACKEND}/customers/1`,
    ]);
  });

  it.each(['999', 'abc'])(
    'FI-3 and FI-4: /clientes/%s answered with 404 shows T-NFC and asks nothing else (CA-9.4)',
    async (id) => {
      const app = await startApp(`/clientes/${id}`);
      respondError(expectCustomer(app.http, id), 404, errorBody('not_found', 'x'));
      await settle();
      expect(textOf(main(app))).toContain('Cliente no encontrado');
      expect(linkNamed(main(app), 'Volver al listado')).toBeDefined();
      expect(buttonNamed(main(app), 'Reintentar')).toBeUndefined();
      expect(pendingBackend(app.http)).toEqual([]);
    },
  );

  it('FI-5: a 500 shows T-SRV; «Reintentar» asks again and loads the card (CA-9.5)', async () => {
    const app = await startApp('/clientes/1');
    respondError(expectCustomer(app.http), 500, 'x');
    await settle();
    expect(textOf(main(app))).toContain('Error del servidor. Inténtalo de nuevo');
    buttonNamed(main(app), 'Reintentar')?.click();
    await settle();
    expectCustomer(app.http).flush(ACME);
    await settle();
    expect(textOf(main(app).querySelector('h1'))).toBe('Acme Telecom S.L.');
  });

  it('FI-7: opening or reloading /clientes/1 shows the card (CA-1.4)', async () => {
    const app = await startApp('/clientes/1');
    expectCustomer(app.http).flush(ACME);
    await settle();
    expect(app.router.url).toBe('/clientes/1');
    expect(cardValue(app, 'Identificador fiscal')).toBe('B12345674');
  });

  it('FI-8: «Volver al listado» opens /clientes (CA-1.7)', async () => {
    const app = await startApp('/clientes/1');
    expectCustomer(app.http).flush(ACME);
    await settle();
    await clickAndSettle(linkNamed(main(app), 'Volver al listado'));
    expect(app.router.url).toBe('/clientes');
  });

  it('AL-5 and FI-9: T-REG after a new customer, gone after leaving and coming back (CA-9.6)', async () => {
    const app = await startApp('/clientes/nuevo');
    await registerAcme(app);
    expectCustomer(app.http).flush(ACME);
    await settle();
    expect(textOf(main(app))).toContain('Cliente registrado');
    await clickAndSettle(linkNamed(main(app), 'Volver al listado'));
    expectList(app.http).flush(CUSTOMER_PAGE);
    await settle();
    await clickAndSettle(
      main(app).querySelector<HTMLAnchorElement>('a[href="/clientes/1"]') ?? undefined,
    );
    expectCustomer(app.http).flush(ACME);
    await settle();
    expect(textOf(main(app))).not.toContain('Cliente registrado');
  });

  it('a card opened from the list does not show T-REG', async () => {
    const app = await startApp('/clientes/1');
    expectCustomer(app.http).flush(ACME);
    await settle();
    expect(textOf(main(app))).not.toContain('Cliente registrado');
  });

  it('AL-18: the card shows the tax id as the backend stored it', async () => {
    const app = await startApp('/clientes/nuevo');
    const stored = { ...ACME, tax_id: '12345678Z' };
    await registerAcme(app, stored);
    expectCustomer(app.http).flush(stored);
    await settle();
    expect(cardValue(app, 'Identificador fiscal')).toBe('12345678Z');
  });
});
