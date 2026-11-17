import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, timeout } from 'rxjs';
import { API_BASE_URL, PAGE_SIZE, REQUEST_TIMEOUT_MS } from './api-config';
import { NewSimulation, PriceQuote, Simulation, SimulationPage } from './api-models';

/**
 * The quote and simulation requests of spec 005 table 5.2 (002 and 004). The bodies carry only
 * the inputs: never an amount, a tax rate or an exchange rate (CA-2.1, RN-7).
 */
@Injectable({ providedIn: 'root' })
export class SimulationsApi {
  private readonly http = inject(HttpClient);

  /** CA-12.1 and CA-12.2. */
  quote(users: number, country: string): Observable<PriceQuote> {
    return this.http
      .post<PriceQuote>(`${API_BASE_URL}/pricing/quote`, { users, country })
      .pipe(timeout(REQUEST_TIMEOUT_MS));
  }

  /** CA-13.2. */
  save(body: NewSimulation): Observable<Simulation> {
    return this.http
      .post<Simulation>(`${API_BASE_URL}/simulations`, body)
      .pipe(timeout(REQUEST_TIMEOUT_MS));
  }

  /** CA-10.1 and CA-7.2. */
  history(customerId: number, offset: number): Observable<SimulationPage> {
    const params = new HttpParams().set('limit', PAGE_SIZE).set('offset', offset);
    return this.http
      .get<SimulationPage>(`${API_BASE_URL}/customers/${customerId}/simulations`, { params })
      .pipe(timeout(REQUEST_TIMEOUT_MS));
  }
}
