import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { CountPipe } from '../format/format-pipes';
import { PagedList } from '../paged-list';
import { T } from '../texts';
import { RequestError } from './request-error';

/** Spec 005 RF-7: T-MOS and «Cargar más» under a list that shows less than its total. */
@Component({
  selector: 'app-load-more',
  imports: [CountPipe, RequestError],
  template: `
    @if (list().hasMore()) {
      <div class="load-more">
        <p role="status">{{ T.MOS(list().items().length | count, list().total() | count) }}</p>
        @if (list().moreFailure(); as failure) {
          <app-request-error [failure]="failure" (retry)="list().retry()" />
        } @else {
          <button
            type="button"
            class="secondary"
            [disabled]="list().moreStatus() === 'loading'"
            (click)="list().loadMore()"
          >
            {{ list().moreStatus() === 'loading' ? T.LMO : T.MAS }}
          </button>
        }
      </div>
    }
  `,
  styles: `
    .load-more {
      display: grid;
      justify-items: center;
      gap: 0.5rem;
      margin-top: 1rem;
    }
    p {
      margin: 0;
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoadMore {
  readonly list = input.required<PagedList<{ readonly id: number }>>();
  protected readonly T = T;
}
