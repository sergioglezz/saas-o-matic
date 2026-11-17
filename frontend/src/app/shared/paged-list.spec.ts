import { HttpErrorResponse } from '@angular/common/http';
import { Observable, Subscriber } from 'rxjs';
import { Page } from '../core/api/api-models';
import { PagedList } from './paged-list';

interface Item {
  readonly id: number;
}

interface PendingPage {
  readonly offset: number;
  readonly subscriber: Subscriber<Page<Item>>;
  settled: boolean;
  cancelled: boolean;
}

function items(...ids: number[]): Item[] {
  return ids.map((id) => ({ id }));
}

// Spec 005 RF-7 (plan DT-9): the same «Cargar más» rules for the list and the history.
describe('PagedList (spec 005 RF-7)', () => {
  let pages: PendingPage[];
  let list: PagedList<Item>;

  const answer = (index: number, page: Page<Item>) => {
    pages[index].settled = true;
    pages[index].subscriber.next(page);
    pages[index].subscriber.complete();
  };

  const fail = (index: number, error: unknown) => {
    pages[index].settled = true;
    pages[index].subscriber.error(error);
  };

  beforeEach(() => {
    pages = [];
    list = new PagedList<Item>(
      (offset) =>
        new Observable<Page<Item>>((subscriber) => {
          const pending: PendingPage = { offset, subscriber, settled: false, cancelled: false };
          pages.push(pending);
          return () => (pending.cancelled = !pending.settled);
        }),
    );
  });

  it('reload asks for offset 0 and shows the page (CA-7.3)', () => {
    list.reload();
    expect(list.status()).toBe('loading');
    answer(0, { items: items(1, 2), total: 3 });
    expect(pages.map((p) => p.offset)).toEqual([0]);
    expect(list.status()).toBe('ready');
    expect(list.items()).toEqual(items(1, 2));
    expect(list.total()).toBe(3);
    expect(list.hasMore()).toBe(true);
  });

  it('a new reload drops the request still pending (CA-6.6)', () => {
    list.reload();
    list.reload();
    expect(pages[0].cancelled).toBe(true);
    answer(1, { items: items(9), total: 1 });
    expect(list.items()).toEqual(items(9));
  });

  it('loadMore asks from the number shown and adds only new ids (CA-7.2, CM-10)', () => {
    list.reload();
    answer(0, { items: items(1, 2), total: 4 });
    list.loadMore();
    expect(pages.map((p) => p.offset)).toEqual([0, 2]);
    expect(list.moreStatus()).toBe('loading');
    answer(1, { items: items(2, 3, 4), total: 5 });
    expect(list.items()).toEqual(items(1, 2, 3, 4));
    expect(list.total()).toBe(5);
    expect(list.moreStatus()).toBe('idle');
  });

  it('loadMore does nothing while a page is pending (CA-7.4)', () => {
    list.reload();
    answer(0, { items: items(1), total: 3 });
    list.loadMore();
    list.loadMore();
    expect(pages.map((p) => p.offset)).toEqual([0, 1]);
  });

  it('a failed page keeps the items and retry repeats it (CA-7.5)', () => {
    list.reload();
    answer(0, { items: items(1), total: 3 });
    list.loadMore();
    fail(1, new HttpErrorResponse({ status: 0 }));
    expect(list.items()).toEqual(items(1));
    expect(list.moreStatus()).toBe('error');
    expect(list.moreFailure()?.kind).toBe('connection');
    list.retry();
    expect(pages.map((p) => p.offset)).toEqual([0, 1, 1]);
  });

  it('a failed reload shows the error and retry repeats it (CA-2.5)', () => {
    list.reload();
    fail(0, new HttpErrorResponse({ status: 500, error: 'x' }));
    expect(list.status()).toBe('error');
    expect(list.failure()?.kind).toBe('server');
    list.retry();
    expect(pages.map((p) => p.offset)).toEqual([0, 0]);
    expect(list.status()).toBe('loading');
  });

  it('a reload also drops a pending «Cargar más» (CA-7.7)', () => {
    list.reload();
    answer(0, { items: items(1), total: 3 });
    list.loadMore();
    list.reload();
    expect(pages[1].cancelled).toBe(true);
    expect(list.moreStatus()).toBe('idle');
  });

  it('prepend adds the item first and adds 1 to the total (CA-10.8)', () => {
    list.reload();
    answer(0, { items: items(1), total: 1 });
    list.prepend({ id: 2 });
    expect(list.items()).toEqual(items(2, 1));
    expect(list.total()).toBe(2);
  });
});
