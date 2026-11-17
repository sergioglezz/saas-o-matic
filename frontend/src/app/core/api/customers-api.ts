import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, timeout } from 'rxjs';
import { API_BASE_URL, PAGE_SIZE, REQUEST_TIMEOUT_MS } from './api-config';
import { Customer, CustomerPage, NewCustomer } from './api-models';

/**
 * The customer requests of spec 005 table 5.2 (003 §5). Errors are not caught here: whoever asks
 * classifies them with `toRequestFailure` (plan DT-6).
 */
@Injectable({ providedIn: 'root' })
export class CustomersApi {
  private readonly http = inject(HttpClient);

  /** CA-6.4 and CA-7.2: `q` as written, and no `q` if it is empty or only spaces. */
  list(query: string, offset: number): Observable<CustomerPage> {
    let params = new HttpParams().set('limit', PAGE_SIZE).set('offset', offset);
    if (query.trim() !== '') {
      params = params.set('q', query);
    }
    return this.http
      .get<CustomerPage>(`${API_BASE_URL}/customers`, { params })
      .pipe(timeout(REQUEST_TIMEOUT_MS));
  }

  /** CA-9.1: the id of the address as written; a non-numeric one gets the backend's 404 (D-21). */
  get(id: string): Observable<Customer> {
    return this.http
      .get<Customer>(`${API_BASE_URL}/customers/${encodeURIComponent(id)}`)
      .pipe(timeout(REQUEST_TIMEOUT_MS));
  }

  /** Spec 007 CA-2.5: no body; the 204 has none either (plan 007 DT-4 explains the name). */
  remove(id: number): Observable<void> {
    return this.http
      .delete<void>(`${API_BASE_URL}/customers/${id}`)
      .pipe(timeout(REQUEST_TIMEOUT_MS));
  }

  /** CA-8.7: the body exactly as the form gives it. */
  create(body: NewCustomer): Observable<Customer> {
    return this.http
      .post<Customer>(`${API_BASE_URL}/customers`, body)
      .pipe(timeout(REQUEST_TIMEOUT_MS));
  }
}
