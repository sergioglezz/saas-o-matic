import { AppHarness, clickAndSettle, startApp } from '../../../testing/app';
import {
  FIELD,
  createRequests,
  expectCreate,
  fieldError,
  fillForm,
  selectField,
  textField,
} from '../../../testing/customer-form';
import { buttonNamed, linkNamed, optionTexts, settle, textOf } from '../../../testing/dom';
import { pendingBackend } from '../../../testing/http';
import { FRESH_NOW, setNow, storeRates } from '../../../testing/rates';
import { ACME, NEW_ACME } from '../../../testing/spec-data';

const COUNTRIES = [
  'Alemania',
  'España',
  'Estados Unidos',
  'Francia',
  'Italia',
  'Portugal',
  'Reino Unido',
];

async function openForm(): Promise<AppHarness> {
  return startApp('/clientes/nuevo');
}

function save(app: AppHarness): HTMLButtonElement {
  const button = buttonNamed(app.root, 'Guardar') ?? buttonNamed(app.root, 'Guardando…');
  return button as HTMLButtonElement;
}

async function pressSave(app: AppHarness): Promise<void> {
  save(app).click();
  await settle();
}

// Spec 005 §6.7 (AL-1 to AL-6, AL-15 and AL-17 to AL-20): RF-8.
describe('new customer form (spec 005 §6.7)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('AL-1: five empty labelled fields, the 7 countries and the 3 plans, none chosen (CA-8.1 to CA-8.3)', async () => {
    const app = await openForm();
    for (const label of [FIELD.company, FIELD.taxId, FIELD.email]) {
      expect(textField(app.root, label).value).toBe('');
    }
    const country = selectField(app.root, FIELD.country);
    const plan = selectField(app.root, FIELD.plan);
    expect(optionTexts(country)).toEqual(COUNTRIES);
    expect(optionTexts(plan)).toEqual(['Starter', 'Business', 'Enterprise']);
    expect(country.selectedIndex).toBe(-1);
    expect(plan.selectedIndex).toBe(-1);
    expect(save(app).type).toBe('submit');
    expect(buttonNamed(app.root, 'Cancelar')).toBeDefined();
    expect(linkNamed(app.root, 'Volver al listado')?.getAttribute('href')).toBe('/clientes');
  });

  it('AL-2: «Guardar» with everything empty sends nothing, marks the 5 and focuses «Empresa» (CA-8.5)', async () => {
    const app = await openForm();
    await pressSave(app);
    expect(createRequests(app.http)).toEqual([]);
    for (const label of Object.values(FIELD)) {
      expect(fieldError(app.root, label)).toBe('Campo obligatorio');
    }
    expect(document.activeElement).toBe(textField(app.root, FIELD.company));
  });

  it('AL-3: «Empresa» with only spaces is the only one marked (CA-8.5)', async () => {
    const app = await openForm();
    fillForm(app.root, { ...NEW_ACME, company_name: '   ' });
    await pressSave(app);
    expect(createRequests(app.http)).toEqual([]);
    expect(fieldError(app.root, FIELD.company)).toBe('Campo obligatorio');
    expect(fieldError(app.root, FIELD.taxId)).toBe('');
    expect(document.activeElement).toBe(textField(app.root, FIELD.company));
  });

  it('CA-8.5: the focus goes to the first empty field in the order of the form', async () => {
    const app = await openForm();
    fillForm(app.root, { ...NEW_ACME, contact_email: ' ' });
    await pressSave(app);
    expect(document.activeElement).toBe(textField(app.root, FIELD.email));
  });

  it('AL-4: valid data send exactly the body of 003 §5 (CA-8.7)', async () => {
    const app = await openForm();
    fillForm(app.root, NEW_ACME);
    await pressSave(app);
    expect(expectCreate(app.http).request.body).toEqual(NEW_ACME);
  });

  it('AL-5: a 201 opens the card of the new customer, telling it that it was just registered (CA-8.9)', async () => {
    const app = await openForm();
    fillForm(app.root, NEW_ACME);
    await pressSave(app);
    expectCreate(app.http).flush(ACME, { status: 201, statusText: 'Created' });
    await settle();
    expect(app.router.url).toBe('/clientes/1');
    expect(app.router.lastSuccessfulNavigation()?.extras.state).toEqual({ registered: true });
  });

  it('AL-6: submitting the form, which is what Enter does in a text field, is the same as AL-4', async () => {
    const app = await openForm();
    fillForm(app.root, NEW_ACME);
    const form = app.root.querySelector('main form') as HTMLFormElement;
    expect(form.contains(textField(app.root, FIELD.company))).toBe(true);
    form.dispatchEvent(new Event('submit', { cancelable: true }));
    await settle();
    expect(expectCreate(app.http).request.body).toEqual(NEW_ACME);
  });

  it('AL-15: «Guardar» twice sends one request; T-GDO disabled while waiting (CA-8.8)', async () => {
    const app = await openForm();
    fillForm(app.root, NEW_ACME);
    save(app).click();
    save(app).click();
    await settle();
    expect(createRequests(app.http)).toHaveLength(1);
    expect(textOf(save(app))).toBe('Guardando…');
    expect(save(app).disabled).toBe(true);
    (app.root.querySelector('main form') as HTMLFormElement).dispatchEvent(
      new Event('submit', { cancelable: true }),
    );
    await settle();
    expect(createRequests(app.http)).toEqual([]);
  });

  it('AL-17: native limits of 120, 30 and 254 characters (CA-8.4)', async () => {
    const app = await openForm();
    expect(textField(app.root, FIELD.company).maxLength).toBe(120);
    expect(textField(app.root, FIELD.taxId).maxLength).toBe(30);
    expect(textField(app.root, FIELD.email).maxLength).toBe(254);
  });

  it('CA-8.6: the browser checks nothing else (no email or pattern rules)', async () => {
    const app = await openForm();
    expect(textField(app.root, FIELD.email).type).toBe('text');
    expect(app.root.querySelector('main form')?.hasAttribute('novalidate')).toBe(true);
    expect(app.root.querySelector('main [pattern], main [required]')).toBeNull();
  });

  it('AL-18: the tax id goes as written', async () => {
    const app = await openForm();
    fillForm(app.root, { ...NEW_ACME, tax_id: '12.345.678-z' });
    await pressSave(app);
    expect(expectCreate(app.http).request.body).toEqual({ ...NEW_ACME, tax_id: '12.345.678-z' });
  });

  it('AL-19: «Reino Unido» and «Enterprise» go as GB and enterprise (CA-8.7)', async () => {
    const app = await openForm();
    fillForm(app.root, { ...NEW_ACME, country: 'GB', plan: 'enterprise' });
    expect(selectField(app.root, FIELD.country).selectedOptions[0].text.trim()).toBe('Reino Unido');
    await pressSave(app);
    const body = expectCreate(app.http).request.body as Record<string, string>;
    expect(body['country']).toBe('GB');
    expect(body['plan']).toBe('enterprise');
  });

  it('AL-20: «Cancelar» with data written opens /clientes and sends nothing (CA-8.15)', async () => {
    const app = await openForm();
    fillForm(app.root, NEW_ACME);
    await clickAndSettle(buttonNamed(app.root, 'Cancelar'));
    expect(app.router.url).toBe('/clientes');
    expect(createRequests(app.http)).toEqual([]);
    expect(pendingBackend(app.http).every((r) => r.request.method === 'GET')).toBe(true);
  });
});
