import { DestroyRef, computed, signal } from '@angular/core';
import { Observable, Subscription } from 'rxjs';
import { Page } from '../core/api/api-models';
import { RequestFailure, toRequestFailure } from '../core/api/request-failure';

export type ListStatus = 'loading' | 'ready' | 'error';
export type MoreStatus = 'idle' | 'loading' | 'error';

interface ListState<T> {
  readonly items: readonly T[];
  readonly total: number;
  readonly status: ListStatus;
  readonly failure: RequestFailure | null;
  readonly moreStatus: MoreStatus;
  readonly moreFailure: RequestFailure | null;
}

/**
 * Spec 005 RF-7 (plan DT-9): a paginated list with «Cargar más», shared by the customer list and
 * the history. Only one request runs at a time: a reload drops the one still pending (CA-6.6).
 */
export class PagedList<T extends { readonly id: number }> {
  private readonly state = signal<ListState<T>>({
    items: [],
    total: 0,
    status: 'loading',
    failure: null,
    moreStatus: 'idle',
    moreFailure: null,
  });
  private request: Subscription | null = null;

  readonly items = computed(() => this.state().items);
  readonly total = computed(() => this.state().total);
  readonly status = computed(() => this.state().status);
  readonly failure = computed(() => this.state().failure);
  readonly moreStatus = computed(() => this.state().moreStatus);
  readonly moreFailure = computed(() => this.state().moreFailure);
  /** CA-7.1 and CA-7.6. */
  readonly hasMore = computed(
    () => this.status() === 'ready' && this.items().length < this.total(),
  );

  constructor(
    private readonly fetchPage: (offset: number) => Observable<Page<T>>,
    destroyRef?: DestroyRef,
  ) {
    destroyRef?.onDestroy(() => this.request?.unsubscribe());
  }

  /** CA-7.7: back to the first page. */
  reload(): void {
    this.request?.unsubscribe();
    this.patch({ status: 'loading', failure: null, moreStatus: 'idle', moreFailure: null });
    this.request = this.fetchPage(0).subscribe({
      next: (page) => this.patch({ items: page.items, total: page.total, status: 'ready' }),
      error: (error: unknown) => this.patch({ status: 'error', failure: toRequestFailure(error) }),
    });
  }

  /** CA-7.2 to CA-7.5. */
  loadMore(): void {
    if (this.status() !== 'ready' || this.moreStatus() === 'loading') {
      return;
    }
    this.patch({ moreStatus: 'loading', moreFailure: null });
    this.request = this.fetchPage(this.items().length).subscribe({
      next: (page) => this.append(page),
      error: (error: unknown) =>
        this.patch({ moreStatus: 'error', moreFailure: toRequestFailure(error) }),
    });
  }

  /** CA-2.5 and CA-7.5: repeats the request that failed. */
  retry(): void {
    if (this.status() === 'error') {
      this.reload();
    } else if (this.moreStatus() === 'error') {
      this.loadMore();
    }
  }

  /** CA-10.8: a new item first, without asking again. */
  prepend(item: T): void {
    const others = this.items().filter((existing) => existing.id !== item.id);
    this.patch({ items: [item, ...others], total: this.total() + 1 });
  }

  private append(page: Page<T>): void {
    const shown = new Set(this.items().map((item) => item.id));
    const added = page.items.filter((item) => !shown.has(item.id));
    this.patch({ items: [...this.items(), ...added], total: page.total, moreStatus: 'idle' });
  }

  private patch(change: Partial<ListState<T>>): void {
    this.state.update((current) => ({ ...current, ...change }));
  }
}
