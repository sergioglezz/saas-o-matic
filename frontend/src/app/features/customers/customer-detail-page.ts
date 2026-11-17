import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  effect,
  inject,
  input,
  signal,
  untracked,
} from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { Customer } from '../../core/api/api-models';
import { CustomersApi } from '../../core/api/customers-api';
import { RequestFailure, toRequestFailure } from '../../core/api/request-failure';
import { DayPipe } from '../../shared/format/format-pipes';
import { LABELS, T, countryName, planName } from '../../shared/texts';
import { RequestError } from '../../shared/ui/request-error';

type CardState =
  | { readonly status: 'loading' }
  | { readonly status: 'ready'; readonly customer: Customer }
  | { readonly status: 'not_found' }
  | { readonly status: 'error'; readonly failure: RequestFailure };

/** Spec 005 RF-9: the customer card, and below it the simulator and the history. */
@Component({
  selector: 'app-customer-detail-page',
  imports: [RouterLink, DayPipe, RequestError],
  templateUrl: './customer-detail-page.html',
  styleUrl: './customer-detail-page.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CustomerDetailPage {
  /** The `{id}` of the address, as written (CA-9.1, D-21). */
  readonly id = input.required<string>();

  private readonly api = inject(CustomersApi);
  private request: Subscription | null = null;

  protected readonly T = T;
  protected readonly LABELS = LABELS;
  protected readonly countryName = countryName;
  protected readonly planName = planName;
  protected readonly state = signal<CardState>({ status: 'loading' });

  /** CA-9.6 (plan DT-12): only when the navigation that opened the card comes from a new customer. */
  protected readonly registered =
    inject(Router).currentNavigation()?.extras.state?.['registered'] === true;

  constructor() {
    effect(() => {
      const id = this.id();
      untracked(() => this.load(id));
    });
    inject(DestroyRef).onDestroy(() => this.request?.unsubscribe());
  }

  /** CA-9.5 and CA-2.5. */
  protected retry(): void {
    this.load(this.id());
  }

  private load(id: string): void {
    this.request?.unsubscribe();
    this.state.set({ status: 'loading' });
    this.request = this.api.get(id).subscribe({
      next: (customer) => this.state.set({ status: 'ready', customer }),
      error: (error: unknown) => {
        const failure = toRequestFailure(error);
        // CA-9.4: a 404 is the only failure with its own text; it asks for nothing else.
        this.state.set(
          failure.kind === 'not_found' ? { status: 'not_found' } : { status: 'error', failure },
        );
      },
    });
  }
}
