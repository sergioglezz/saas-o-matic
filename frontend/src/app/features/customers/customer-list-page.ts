import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { Subject, debounceTime } from 'rxjs';
import { Customer } from '../../core/api/api-models';
import { CustomersApi } from '../../core/api/customers-api';
import { initials } from '../../shared/format/initials';
import { PagedList } from '../../shared/paged-list';
import { LABELS, T, TITLES, countryName, planName } from '../../shared/texts';
import { Icon } from '../../shared/ui/icon';
import { LoadMore } from '../../shared/ui/load-more';
import { RequestError } from '../../shared/ui/request-error';
import { SkeletonCards } from '../../shared/ui/skeleton-cards';

/** D-4: the wait after the last change of the search box. */
const SEARCH_WAIT_MS = 300;

/** Spec 005 RF-6 and RF-7: search and list of customers. */
@Component({
  selector: 'app-customer-list-page',
  imports: [RouterLink, Icon, LoadMore, RequestError, SkeletonCards],
  templateUrl: './customer-list-page.html',
  styleUrl: './customer-list-page.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CustomerListPage {
  private readonly api = inject(CustomersApi);
  private readonly searches = new Subject<string>();
  /** The text of the search whose results are asked for or shown. */
  private readonly query = signal('');

  protected readonly T = T;
  protected readonly LABELS = LABELS;
  protected readonly TITLES = TITLES;
  protected readonly initials = initials;
  protected readonly countryName = countryName;
  protected readonly planName = planName;
  protected readonly list = new PagedList<Customer>(
    (offset) => this.api.list(this.query(), offset),
    inject(DestroyRef),
  );

  /** CA-6.8 and CA-6.9. */
  protected readonly emptyText = computed(() => {
    const text = this.query().trim();
    return text === '' ? T.EMP : T.NOR(text);
  });

  constructor() {
    // CA-6.4 and CA-6.5; the reload drops the previous search (CA-6.6).
    this.searches.pipe(debounceTime(SEARCH_WAIT_MS), takeUntilDestroyed()).subscribe((text) => {
      this.query.set(text);
      this.list.reload();
    });
    this.list.reload();
  }

  protected search(event: Event): void {
    this.searches.next((event.target as HTMLInputElement).value);
  }
}
