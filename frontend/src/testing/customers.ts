import { HttpTestingController, TestRequest } from '@angular/common/http/testing';
import { Customer, CustomerPage } from '../app/core/api/api-models';
import { textOf } from './dom';
import { BACKEND } from './http';
import { ACME } from './spec-data';

export const LIST_URL = `${BACKEND}/customers`;

/** The single pending `GET /customers` (any query). */
export function expectList(http: HttpTestingController): TestRequest {
  return http.expectOne((r) => r.method === 'GET' && r.url === LIST_URL);
}

export function listRequests(http: HttpTestingController): TestRequest[] {
  return http.match((r) => r.method === 'GET' && r.url === LIST_URL);
}

/** `count` customers with consecutive ids, for the pages of «Cargar más». */
export function customers(count: number, firstId = 1): Customer[] {
  return Array.from({ length: count }, (_, index) => {
    const id = firstId + index;
    return { ...ACME, id, company_name: `Cliente ${id}`, tax_id: `X${id}` };
  });
}

export function page(items: Customer[], total = items.length): CustomerPage {
  return { items, total };
}

/** The customers shown in the list, as links. */
export function customerLinks(root: HTMLElement): HTMLAnchorElement[] {
  return Array.from(root.querySelectorAll<HTMLAnchorElement>('main ul a'));
}

export function customerNames(root: HTMLElement): string[] {
  return customerLinks(root).map((link) => textOf(link.querySelector('.name')));
}

export function searchBox(root: HTMLElement): HTMLInputElement {
  return root.querySelector('input[type="search"]') as HTMLInputElement;
}
