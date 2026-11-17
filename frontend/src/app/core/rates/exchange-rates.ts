import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { timeout } from 'rxjs';
import { RATES_URL, REQUEST_TIMEOUT_MS } from '../api/api-config';
import { BrowserStorage } from './browser-storage';
import { RatesSnapshot, isFresh, parseRatesSnapshot } from './rates-snapshot';

/**
 * loading: waiting for the API (CA-4.2); fresh: rates without a failure notice (CA-3.9);
 * stale: stored rates after a failure (CA-3.6); unavailable: no rates at all (CA-3.7).
 */
export type RatesStatus = 'loading' | 'fresh' | 'stale' | 'unavailable';

interface RatesState {
  readonly status: RatesStatus;
  readonly snapshot: RatesSnapshot | null;
}

/** Spec 005 RF-3: the rates are asked only when the app starts and on «Reintentar» (CA-3.12). */
@Injectable({ providedIn: 'root' })
export class ExchangeRates {
  private readonly http = inject(HttpClient);
  private readonly storage = inject(BrowserStorage);
  private readonly state = signal<RatesState>({ status: 'loading', snapshot: null });
  private started = false;

  readonly status = computed(() => this.state().status);
  readonly snapshot = computed(() => this.state().snapshot);

  /** CA-3.1 and CA-3.2: once per load of the app. */
  load(): void {
    if (this.started) {
      return;
    }
    this.started = true;
    const stored = this.stored();
    if (stored !== null && isFresh(stored, Date.now() / 1000)) {
      this.state.set({ status: 'fresh', snapshot: stored });
      return;
    }
    this.fetch();
  }

  /** CA-3.8: asks again without looking at what is stored. */
  retry(): void {
    if (this.state().status !== 'loading') {
      this.fetch();
    }
  }

  private fetch(): void {
    this.state.set({ status: 'loading', snapshot: null });
    this.http
      .get<unknown>(RATES_URL)
      .pipe(timeout(REQUEST_TIMEOUT_MS))
      .subscribe({
        next: (body) => this.receive(parseRatesSnapshot(body)),
        error: () => this.receive(null),
      });
  }

  /** CA-3.4, CA-3.6 and CA-3.7. */
  private receive(received: RatesSnapshot | null): void {
    if (received !== null) {
      this.storage.writeRates(received);
      this.state.set({ status: 'fresh', snapshot: received });
      return;
    }
    const stored = this.stored();
    this.state.set({ status: stored === null ? 'unavailable' : 'stale', snapshot: stored });
  }

  private stored(): RatesSnapshot | null {
    return parseRatesSnapshot(this.storage.readRates());
  }
}
