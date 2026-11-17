import { fieldErrorsFrom } from './customer-form-errors';

const EMAIL = { field: 'contact_email', message: 'Debe ser un email válido' };
const TAX_ID = { field: 'tax_id', message: 'El DNI/NIF/CIF no es válido' };
const DUPLICATE = { field: 'tax_id', message: 'Ya existe un cliente con este identificador' };
const COUNTRY = { field: 'country', message: 'País no soportado' };
const BODY = { field: 'body', message: 'El cuerpo debe ser un objeto JSON' };

// Spec 005 RF-8 (CA-8.10, CA-8.11): the details of a 422 or a 409, next to each field.
describe('fieldErrorsFrom (spec 005 CA-8.10 and CA-8.11)', () => {
  it('AL-7 and AL-8: one detail next to its field', () => {
    expect(fieldErrorsFrom([EMAIL])).toEqual({
      fields: { contact_email: ['Debe ser un email válido'] },
      general: false,
    });
    expect(fieldErrorsFrom([TAX_ID]).fields).toEqual({ tax_id: ['El DNI/NIF/CIF no es válido'] });
  });

  it('AL-9: each detail next to its own field', () => {
    expect(fieldErrorsFrom([TAX_ID, EMAIL])).toEqual({
      fields: { tax_id: [TAX_ID.message], contact_email: [EMAIL.message] },
      general: false,
    });
  });

  it('AL-10: the detail of a 409 next to the tax id', () => {
    expect(fieldErrorsFrom([DUPLICATE]).fields).toEqual({ tax_id: [DUPLICATE.message] });
  });

  it('AL-11: «País no soportado» next to the country', () => {
    expect(fieldErrorsFrom([COUNTRY]).fields).toEqual({ country: ['País no soportado'] });
  });

  it('AL-12: a detail of another field asks for T-DNV, and keeps the rest', () => {
    expect(fieldErrorsFrom([BODY])).toEqual({ fields: {}, general: true });
    expect(fieldErrorsFrom([BODY, EMAIL])).toEqual({
      fields: { contact_email: [EMAIL.message] },
      general: true,
    });
  });

  it('CA-8.10: no details at all ask for T-DNV', () => {
    expect(fieldErrorsFrom([])).toEqual({ fields: {}, general: true });
  });

  it('two details of the same field are both shown, in order', () => {
    const other = { field: 'tax_id', message: 'Debe tener entre 5 y 20 letras o dígitos' };
    expect(fieldErrorsFrom([TAX_ID, other]).fields).toEqual({
      tax_id: [TAX_ID.message, other.message],
    });
  });
});
