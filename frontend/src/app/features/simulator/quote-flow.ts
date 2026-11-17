import { DestroyRef, computed, signal } from '@angular/core';
import { Observable, Subject, Subscription, debounceTime } from 'rxjs';
import { PriceQuote } from '../../core/api/api-models';

/** D-4: the wait after the last change of the users (§6 of the 00: 200 to 300 ms). */
export const QUOTE_WAIT_MS = 300;

/** The result of the last quote that finished. */
export type QuoteOutcome = 'none' | 'ok' | 'failed';

interface QuoteState {
  /** The last 200, kept while a new one is asked (CA-12.7). */
  readonly quote: PriceQuote | null;
  /** The users of that quote. */
  readonly quotedUsers: number | null;
  readonly outcome: QuoteOutcome;
  /** A change to a valid value is waiting the 300 ms. */
  readonly waiting: boolean;
  readonly inFlight: boolean;
}

/** Spec 005 RF-12 (plan §5 «Cotización»): the quote of the simulator, in real time. */
export class QuoteFlow {
  private readonly changes = new Subject<number | null>();
  private request: Subscription | null = null;
  private readonly state = signal<QuoteState>({
    quote: null,
    quotedUsers: null,
    outcome: 'none',
    waiting: false,
    inFlight: false,
  });

  readonly quote = computed(() => this.state().quote);
  readonly quotedUsers = computed(() => this.state().quotedUsers);
  readonly outcome = computed(() => this.state().outcome);
  /** CA-12.7 and CA-13.1: a change waiting the 300 ms or a quote on its way. */
  readonly pending = computed(() => this.state().waiting || this.state().inFlight);

  constructor(
    private readonly fetchQuote: (users: number) => Observable<PriceQuote>,
    destroyRef: DestroyRef,
  ) {
    const waits = this.changes
      .pipe(debounceTime(QUOTE_WAIT_MS))
      .subscribe((users) => this.afterWait(users));
    destroyRef.onDestroy(() => {
      waits.unsubscribe();
      this.request?.unsubscribe();
    });
  }

  /** CA-12.2 and CA-12.3: every change, also to a value that is not valid (null). */
  change(users: number | null): void {
    this.patch({ waiting: users !== null && !this.shows(users) });
    this.changes.next(users);
  }

  /** CA-12.1: without waiting. */
  quoteNow(users: number): void {
    this.ask(users);
  }

  private afterWait(users: number | null): void {
    this.patch({ waiting: false });
    if (users === null) {
      return;
    }
    if (this.shows(users)) {
      this.cancel(); // CA-12.4
      return;
    }
    this.ask(users);
  }

  /** The quote shown, without an error, is the one of these users. */
  private shows(users: number): boolean {
    const { outcome, quotedUsers } = this.state();
    return outcome === 'ok' && quotedUsers === users;
  }

  /** CA-12.5: a new request drops the one on its way, so an old answer never shows. */
  private ask(users: number): void {
    this.request?.unsubscribe();
    this.patch({ inFlight: true });
    this.request = this.fetchQuote(users).subscribe({
      next: (quote) => this.patch({ quote, quotedUsers: users, outcome: 'ok', inFlight: false }),
      error: () => this.patch({ outcome: 'failed', inFlight: false }),
    });
  }

  private cancel(): void {
    this.request?.unsubscribe();
    this.request = null;
    this.patch({ inFlight: false });
  }

  private patch(change: Partial<QuoteState>): void {
    this.state.update((current) => ({ ...current, ...change }));
  }
}
