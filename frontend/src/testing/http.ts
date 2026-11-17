import { HttpTestingController, TestRequest } from '@angular/common/http/testing';

export const BACKEND = 'http://127.0.0.1:8000';

/** A backend error body in the single format of §8.4 of the 00. */
export function errorBody(
  code: string,
  message: string,
  details: { field: string; message: string }[] = [],
): object {
  return { error: { code, message, details } };
}

export function respondError(
  req: TestRequest,
  status: number,
  body: string | object | null = null,
): void {
  req.flush(body, { status, statusText: 'Error' });
}

/** No response: backend stopped, network down or blocked by CORS (status 0). */
export function respondNoConnection(req: TestRequest): void {
  req.error(new ProgressEvent('error'));
}

/**
 * A 200 whose body is not JSON. HttpClient reports it as an error with status 200 (it cannot parse
 * the body); the testing backend would hand the text over as data, so it is reproduced here.
 */
export function respondNotJson(req: TestRequest): void {
  req.error(new ProgressEvent('error'), { status: 200, statusText: 'OK' });
}

/** The query of a request as the server would read it, from its final URL. */
export function queryOf(req: TestRequest): Record<string, string> {
  const params = new URL(req.request.urlWithParams).searchParams;
  return Object.fromEntries(params.entries());
}

/** Requests to the backend still waiting for an answer. */
export function pendingBackend(http: HttpTestingController): TestRequest[] {
  return http.match((r) => r.url.startsWith(BACKEND));
}
