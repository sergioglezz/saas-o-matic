import { TestRequest } from '@angular/common/http/testing';
import { AppHarness, startApp } from '../../../testing/app';
import {
  FIELD,
  expectCreate,
  fieldError,
  fillForm,
  formValues,
  textField,
} from '../../../testing/customer-form';
import { buttonNamed, settle, textOf, typeInto } from '../../../testing/dom';
import { errorBody, respondError, respondNoConnection } from '../../../testing/http';
import { FRESH_NOW, setNow, storeRates } from '../../../testing/rates';
import { NEW_ACME } from '../../../testing/spec-data';

const EMAIL = { field: 'contact_email', message: 'Debe ser un email válido' };
const TAX_ID = { field: 'tax_id', message: 'El DNI/NIF/CIF no es válido' };
const DUPLICATE = { field: 'tax_id', message: 'Ya existe un cliente con este identificador' };

function invalid(...details: { field: string; message: string }[]): object {
  return errorBody('validation_error', 'Datos no válidos', details);
}

/** Opens the form, fills it with `values`, presses «Guardar» and returns the request. */
async function submitted(values = NEW_ACME): Promise<{ app: AppHarness; req: TestRequest }> {
  const app = await startApp('/clientes/nuevo');
  fillForm(app.root, values);
  (app.root.querySelector('main button[type="submit"]') as HTMLButtonElement).click();
  await settle();
  return { app, req: expectCreate(app.http) };
}

function main(app: AppHarness): HTMLElement {
  return app.root.querySelector('main') as HTMLElement;
}

// Spec 005 §6.7 (AL-7 to AL-14 and AL-16): RF-8, the answers that are not a 201.
describe('new customer form, failures (spec 005 §6.7)', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    setNow(FRESH_NOW);
    storeRates();
  });

  afterEach(() => vi.useRealTimers());

  it('AL-7: an email «abc» is sent, and the 422 is shown next to «Email de contacto» (CA-8.6, CA-8.10)', async () => {
    const values = { ...NEW_ACME, contact_email: 'abc' };
    const { app, req } = await submitted(values);
    expect(req.request.body).toEqual(values);
    respondError(req, 422, invalid(EMAIL));
    await settle();
    expect(fieldError(app.root, FIELD.email)).toBe('Debe ser un email válido');
    expect(formValues(app.root)).toEqual(values);
  });

  it('AL-8: a tax id «12345678A» is sent, and its 422 is shown next to the tax id', async () => {
    const values = { ...NEW_ACME, tax_id: '12345678A' };
    const { app, req } = await submitted(values);
    expect(req.request.body).toEqual(values);
    respondError(req, 422, invalid(TAX_ID));
    await settle();
    expect(fieldError(app.root, FIELD.taxId)).toBe('El DNI/NIF/CIF no es válido');
    expect(formValues(app.root)).toEqual(values);
  });

  it('AL-9: each message next to its field, without T-DNV (CA-8.10)', async () => {
    const { app, req } = await submitted();
    respondError(req, 422, invalid(TAX_ID, EMAIL));
    await settle();
    expect(fieldError(app.root, FIELD.taxId)).toBe(TAX_ID.message);
    expect(fieldError(app.root, FIELD.email)).toBe(EMAIL.message);
    expect(textOf(main(app))).not.toContain('Datos no válidos');
  });

  it('AL-10: a 409 shows its message next to the tax id (CA-8.11)', async () => {
    const { app, req } = await submitted();
    respondError(req, 409, errorBody('conflict', 'El recurso ya existe', [DUPLICATE]));
    await settle();
    expect(fieldError(app.root, FIELD.taxId)).toBe('Ya existe un cliente con este identificador');
    expect(formValues(app.root)).toEqual(NEW_ACME);
  });

  it('AL-11: «País no soportado» next to «País»', async () => {
    const { app, req } = await submitted();
    respondError(req, 422, invalid({ field: 'country', message: 'País no soportado' }));
    await settle();
    expect(fieldError(app.root, FIELD.country)).toBe('País no soportado');
  });

  it('AL-12: a detail of «body» shows T-DNV above the form (CA-8.10)', async () => {
    const { app, req } = await submitted();
    respondError(
      req,
      422,
      invalid({ field: 'body', message: 'El cuerpo debe ser un objeto JSON' }),
    );
    await settle();
    const form = main(app).querySelector('form') as HTMLFormElement;
    const notice = Array.from(main(app).querySelectorAll('[role="status"]')).find(
      (n) => textOf(n) === 'Datos no válidos',
    );
    expect(notice).toBeDefined();
    expect(notice?.compareDocumentPosition(form)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(formValues(app.root)).toEqual(NEW_ACME);
  });

  it.each([
    ['no answer', respondNoConnection, 'No se pudo conectar con el servidor'],
    [
      'a 500',
      (r: TestRequest) => respondError(r, 500, 'x'),
      'Error del servidor. Inténtalo de nuevo',
    ],
    [
      'a 404',
      (r: TestRequest) => respondError(r, 404, errorBody('not_found', 'x')),
      'Error del servidor. Inténtalo de nuevo',
    ],
  ])(
    'AL-13: %s shows its message; «Reintentar» sends the same body (CA-8.12)',
    async (_case, respond, message) => {
      const { app, req } = await submitted();
      respond(req);
      await settle();
      expect(textOf(main(app))).toContain(message);
      expect(formValues(app.root)).toEqual(NEW_ACME);
      buttonNamed(main(app), 'Reintentar')?.click();
      await settle();
      expect(expectCreate(app.http).request.body).toEqual(NEW_ACME);
    },
  );

  it.each([
    ['422', (r: TestRequest) => respondError(r, 422, invalid(EMAIL))],
    ['409', (r: TestRequest) => respondError(r, 409, errorBody('conflict', 'x', [DUPLICATE]))],
    ['no answer', respondNoConnection],
    ['500', (r: TestRequest) => respondError(r, 500, 'x')],
  ])(
    'AL-14: after a %s the five fields keep what was written (CA-8.13)',
    async (_case, respond) => {
      const { app, req } = await submitted();
      respond(req);
      await settle();
      expect(formValues(app.root)).toEqual(NEW_ACME);
    },
  );

  it('CA-8.12: «Reintentar» sends the body that failed, not what was written later', async () => {
    const { app, req } = await submitted();
    respondNoConnection(req);
    await settle();
    typeInto(textField(app.root, FIELD.company), 'Otra');
    buttonNamed(main(app), 'Reintentar')?.click();
    await settle();
    expect(expectCreate(app.http).request.body).toEqual(NEW_ACME);
  });

  it('AL-16: changing the tax id removes only its message (CA-8.14)', async () => {
    const { app, req } = await submitted();
    respondError(req, 422, invalid(TAX_ID, EMAIL));
    await settle();
    typeInto(textField(app.root, FIELD.taxId), 'B12345674');
    await settle();
    expect(fieldError(app.root, FIELD.taxId)).toBe('');
    expect(fieldError(app.root, FIELD.email)).toBe(EMAIL.message);
  });

  it('CA-8.14: changing a field marked «Campo obligatorio» removes its mark', async () => {
    const app = await startApp('/clientes/nuevo');
    (app.root.querySelector('main button[type="submit"]') as HTMLButtonElement).click();
    await settle();
    typeInto(textField(app.root, FIELD.company), 'Acme');
    await settle();
    expect(fieldError(app.root, FIELD.company)).toBe('');
    expect(fieldError(app.root, FIELD.taxId)).toBe('Campo obligatorio');
  });
});
