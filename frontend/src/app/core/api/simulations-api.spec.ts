import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { BACKEND, queryOf } from '../../../testing/http';
import { NEW_SIMULATION, QUOTE_15, SIMULATION_1 } from '../../../testing/spec-data';
import { RequestFailure, toRequestFailure } from './request-failure';
import { SimulationsApi } from './simulations-api';

const AMOUNT_FIELDS = /_cents|tax_rate_bp|rate/;

describe('SimulationsApi (spec 005 table 5.2, CA-2.1)', () => {
  let api: SimulationsApi;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(SimulationsApi);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    vi.useRealTimers();
  });

  it('CA-12.1: quotes with users and country only, as JSON', () => {
    let quote: unknown;
    api.quote(15, 'ES').subscribe((q) => (quote = q));
    const req = http.expectOne({ method: 'POST', url: `${BACKEND}/pricing/quote` });
    expect(req.request.body).toEqual({ users: 15, country: 'ES' });
    expect(req.request.detectContentTypeHeader()).toBe('application/json');
    req.flush(QUOTE_15);
    expect(quote).toEqual(QUOTE_15);
  });

  it('CA-13.2: saves with exactly the four fields of the simulation', () => {
    api.save(NEW_SIMULATION).subscribe();
    const req = http.expectOne({ method: 'POST', url: `${BACKEND}/simulations` });
    expect(req.request.body).toEqual(NEW_SIMULATION);
    expect(Object.keys(req.request.body as object).join()).not.toMatch(AMOUNT_FIELDS);
    req.flush(SIMULATION_1, { status: 201, statusText: 'Created' });
  });

  it('CA-10.1 and CA-7.2: asks for a page of the history', () => {
    api.history(1, 0).subscribe();
    api.history(1, 50).subscribe();
    const [first, second] = http.match((r) => r.url === `${BACKEND}/customers/1/simulations`);
    expect(first.request.method).toBe('GET');
    expect(queryOf(first)).toEqual({ limit: '50', offset: '0' });
    expect(queryOf(second)).toEqual({ limit: '50', offset: '50' });
    first.flush({ items: [SIMULATION_1], total: 1 });
    second.flush({ items: [], total: 1 });
  });

  it('DT-7: a quote without an answer in 10 s fails as a connection failure', () => {
    vi.useFakeTimers();
    let failure: RequestFailure | undefined;
    api.quote(15, 'ES').subscribe({ error: (e: unknown) => (failure = toRequestFailure(e)) });
    const req = http.expectOne(`${BACKEND}/pricing/quote`);
    vi.advanceTimersByTime(10000);
    expect(failure?.kind).toBe('connection');
    expect(req.cancelled).toBe(true);
  });
});
