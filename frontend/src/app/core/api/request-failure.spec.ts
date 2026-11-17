import { HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { TimeoutError } from 'rxjs';
import { errorBody } from '../../../testing/http';
import { toRequestFailure } from './request-failure';

function httpError(status: number, error: unknown = null): HttpErrorResponse {
  return new HttpErrorResponse({ status, error, headers: new HttpHeaders(), url: 'http://x/' });
}

const DUPLICATE = { field: 'tax_id', message: 'Ya existe un cliente con este identificador' };

// Spec 005 table 5.3 and CA-2.2 to CA-2.4: one single place that classifies every failure.
describe('toRequestFailure (spec 005 table 5.3)', () => {
  it('CA-2.2: no response (status 0) is a connection failure', () => {
    expect(toRequestFailure(httpError(0, new ProgressEvent('error'))).kind).toBe('connection');
  });

  it('CA-2.2: more than 10 s is a connection failure', () => {
    expect(toRequestFailure(new TimeoutError()).kind).toBe('connection');
  });

  it.each([500, 502, 503])('CA-2.3: %i is a server failure', (status) => {
    expect(toRequestFailure(httpError(status, errorBody('internal_error', 'x'))).kind).toBe(
      'server',
    );
  });

  it('CA-2.3: a 200 whose body is not JSON is a server failure', () => {
    const parse = { error: new SyntaxError('Unexpected token'), text: 'no es json' };
    expect(toRequestFailure(httpError(200, parse)).kind).toBe('server');
  });

  it('CA-2.3: a 4xx whose body is not JSON is a server failure', () => {
    expect(toRequestFailure(httpError(404, '<html>Traceback</html>')).kind).toBe('server');
    expect(toRequestFailure(httpError(422, null)).kind).toBe('server');
  });

  it.each([
    [404, 'not_found'],
    [409, 'conflict'],
    [422, 'validation'],
    [400, 'client'],
    [405, 'client'],
    [429, 'client'],
  ])('%i with the error format is %s', (status, kind) => {
    expect(toRequestFailure(httpError(status, errorBody('x', 'y'))).kind).toBe(kind);
  });

  it('CA-2.6: keeps the details as they come', () => {
    const failure = toRequestFailure(httpError(409, errorBody('conflict', 'x', [DUPLICATE])));
    expect(failure).toEqual({ kind: 'conflict', details: [DUPLICATE] });
  });

  it('ignores details without a text field and message', () => {
    const body = { error: { code: 'x', message: 'y', details: [DUPLICATE, { field: 1 }, 'z'] } };
    expect(toRequestFailure(httpError(422, body)).details).toEqual([DUPLICATE]);
    expect(toRequestFailure(httpError(422, { error: { details: 'no' } })).details).toEqual([]);
  });

  it('any other error is a server failure', () => {
    expect(toRequestFailure(new Error('boom'))).toEqual({ kind: 'server', details: [] });
    expect(toRequestFailure(httpError(302, {})).kind).toBe('server');
  });
});
