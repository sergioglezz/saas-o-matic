import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { BACKEND, queryOf } from '../../../testing/http';
import { ACME, CUSTOMER_PAGE, NEW_ACME } from '../../../testing/spec-data';
import { CustomersApi } from './customers-api';
import { RequestFailure, toRequestFailure } from './request-failure';

describe('CustomersApi (spec 005 table 5.2, CA-2.1)', () => {
  let api: CustomersApi;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(CustomersApi);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    vi.useRealTimers();
  });

  it('ER-1: lists the first page without q', () => {
    let page: unknown;
    api.list('', 0).subscribe((p) => (page = p));
    const req = http.expectOne((r) => r.url === `${BACKEND}/customers`);
    expect(req.request.method).toBe('GET');
    expect(queryOf(req)).toEqual({ limit: '50', offset: '0' });
    req.flush(CUSTOMER_PAGE);
    expect(page).toEqual(CUSTOMER_PAGE);
  });

  it('CA-6.4: sends q as written, and without q if it is only spaces', () => {
    api.list('  zzz  ', 50).subscribe();
    api.list('   ', 0).subscribe();
    const [withText, onlySpaces] = http.match((r) => r.url === `${BACKEND}/customers`);
    expect(queryOf(withText)).toEqual({ q: '  zzz  ', limit: '50', offset: '50' });
    expect(queryOf(onlySpaces)).toEqual({ limit: '50', offset: '0' });
    withText.flush(CUSTOMER_PAGE);
    onlySpaces.flush(CUSTOMER_PAGE);
  });

  it('LI-11: q reaches the backend with its special characters', () => {
    api.list('a&b=c%', 0).subscribe();
    const req = http.expectOne((r) => r.url === `${BACKEND}/customers`);
    expect(queryOf(req)['q']).toBe('a&b=c%');
    req.flush(CUSTOMER_PAGE);
  });

  it('CA-9.1: gets a customer with the id as written', () => {
    api.get('1').subscribe();
    api.get('abc').subscribe();
    http.expectOne({ method: 'GET', url: `${BACKEND}/customers/1` }).flush(ACME);
    http.expectOne({ method: 'GET', url: `${BACKEND}/customers/abc` }).flush(ACME);
  });

  it('CA-8.7: creates a customer with exactly the body it receives, as JSON', () => {
    api.create(NEW_ACME).subscribe();
    const req = http.expectOne({ method: 'POST', url: `${BACKEND}/customers` });
    expect(req.request.body).toEqual(NEW_ACME);
    expect(req.request.detectContentTypeHeader()).toBe('application/json');
    req.flush(ACME, { status: 201, statusText: 'Created' });
  });

  it('DT-7: a request without an answer in 10 s fails as a connection failure', () => {
    vi.useFakeTimers();
    let failure: RequestFailure | undefined;
    api.get('1').subscribe({ error: (e: unknown) => (failure = toRequestFailure(e)) });
    const req = http.expectOne(`${BACKEND}/customers/1`);
    vi.advanceTimersByTime(9999);
    expect(failure).toBeUndefined();
    vi.advanceTimersByTime(1);
    expect(failure?.kind).toBe('connection');
    expect(req.cancelled).toBe(true);
  });
});
