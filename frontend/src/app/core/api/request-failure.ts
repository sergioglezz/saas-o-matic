import { HttpErrorResponse } from '@angular/common/http';
import { TimeoutError } from 'rxjs';
import { ErrorDetail } from './api-models';

/** The rows of spec 005 table 5.3, which each screen turns into its own text. */
export type FailureKind =
  'connection' | 'server' | 'not_found' | 'conflict' | 'validation' | 'client';

export interface RequestFailure {
  readonly kind: FailureKind;
  readonly details: readonly ErrorDetail[];
}

const KIND_BY_STATUS: Readonly<Record<number, FailureKind>> = {
  404: 'not_found',
  409: 'conflict',
  422: 'validation',
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isDetail(value: unknown): value is ErrorDetail {
  return (
    isRecord(value) && typeof value['field'] === 'string' && typeof value['message'] === 'string'
  );
}

/** CA-2.6: the details of the single error format (§8.4 of the 00), as they come. */
function detailsOf(body: Record<string, unknown>): readonly ErrorDetail[] {
  const error = body['error'];
  const details = isRecord(error) ? error['details'] : undefined;
  return Array.isArray(details) ? details.filter(isDetail) : [];
}

function fromHttp(error: HttpErrorResponse): RequestFailure {
  if (error.status === 0) {
    return { kind: 'connection', details: [] };
  }
  // A 2xx here means HttpClient could not parse the body; a 4xx must carry the JSON error format.
  const isClientError = error.status >= 400 && error.status < 500;
  if (!isClientError || !isRecord(error.error)) {
    return { kind: 'server', details: [] };
  }
  return { kind: KIND_BY_STATUS[error.status] ?? 'client', details: detailsOf(error.error) };
}

/**
 * Plan DT-6: every failed request goes through here. No response or more than 10 s is a
 * connection failure (CA-2.2); a 5xx, a body that is not JSON or anything unexpected is a server
 * failure (CA-2.3).
 */
export function toRequestFailure(error: unknown): RequestFailure {
  if (error instanceof TimeoutError) {
    return { kind: 'connection', details: [] };
  }
  if (error instanceof HttpErrorResponse) {
    return fromHttp(error);
  }
  return { kind: 'server', details: [] };
}
