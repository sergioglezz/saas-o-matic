import { HttpTestingController, TestRequest } from '@angular/common/http/testing';
import { NewCustomer } from '../app/core/api/api-models';
import { choose, controlLabelled, textOf, typeInto } from './dom';
import { BACKEND } from './http';

export const CREATE_URL = `${BACKEND}/customers`;

/** The labels of CA-8.1. */
export const FIELD = {
  company: 'Empresa',
  taxId: 'Identificador fiscal (DNI/NIF/CIF)',
  email: 'Email de contacto',
  country: 'País',
  plan: 'Plan',
} as const;

export function expectCreate(http: HttpTestingController): TestRequest {
  return http.expectOne((r) => r.method === 'POST' && r.url === CREATE_URL);
}

export function createRequests(http: HttpTestingController): TestRequest[] {
  return http.match((r) => r.method === 'POST' && r.url === CREATE_URL);
}

export function textField(root: HTMLElement, label: string): HTMLInputElement {
  return controlLabelled<HTMLInputElement>(root, label);
}

export function selectField(root: HTMLElement, label: string): HTMLSelectElement {
  return controlLabelled<HTMLSelectElement>(root, label);
}

/** Fills the five fields as the user would. */
export function fillForm(root: HTMLElement, values: NewCustomer): void {
  typeInto(textField(root, FIELD.company), values.company_name);
  typeInto(textField(root, FIELD.taxId), values.tax_id);
  typeInto(textField(root, FIELD.email), values.contact_email);
  choose(selectField(root, FIELD.country), values.country);
  choose(selectField(root, FIELD.plan), values.plan);
}

export function formValues(root: HTMLElement): NewCustomer {
  return {
    company_name: textField(root, FIELD.company).value,
    tax_id: textField(root, FIELD.taxId).value,
    contact_email: textField(root, FIELD.email).value,
    country: selectField(root, FIELD.country).value,
    plan: selectField(root, FIELD.plan).value,
  };
}

/**
 * The message shown next to a field, found through the field's `aria-describedby`, so the test
 * also checks that the message is tied to its field (RNF-4).
 */
export function fieldError(root: HTMLElement, label: string): string {
  const control = controlLabelled(root, label);
  const ids = (control.getAttribute('aria-describedby') ?? '').split(' ').filter(Boolean);
  return ids.map((id) => textOf(root.querySelector(`#${CSS.escape(id)}`))).join(' ');
}
