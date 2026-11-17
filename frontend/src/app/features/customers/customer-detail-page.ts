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
import { Customer, Simulation } from '../../core/api/api-models';
import { CustomersApi } from '../../core/api/customers-api';
import { RequestFailure, toRequestFailure } from '../../core/api/request-failure';
import { SimulationsApi } from '../../core/api/simulations-api';
import { DayPipe } from '../../shared/format/format-pipes';
import { PagedList } from '../../shared/paged-list';
import { LABELS, T, countryName, planName } from '../../shared/texts';
import { RequestError } from '../../shared/ui/request-error';
import { Simulator } from '../simulator/simulator';
import { SimulationHistory } from './simulation-history';

type CardState =
  | { readonly status: 'loading' }
  | { readonly status: 'ready'; readonly customer: Customer }
  | { readonly status: 'not_found' }
  | { readonly status: 'error'; readonly failure: RequestFailure };

/** Spec 005 RF-9: the customer card, and below it the simulator and the history. */
@Component({
  selector: 'app-customer-detail-page',
  imports: [RouterLink, DayPipe, RequestError, Simulator, SimulationHistory],
  templateUrl: './customer-detail-page.html',
  styleUrl: './customer-detail-page.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CustomerDetailPage {
  /** The `{id}` of the address, as written (CA-9.1, D-21). */
  readonly id = input.required<string>();

  private readonly api = inject(CustomersApi);
  private readonly simulations = inject(SimulationsApi);
  private request: Subscription | null = null;
  private customerId = 0;

  protected readonly T = T;
  protected readonly LABELS = LABELS;
  protected readonly countryName = countryName;
  protected readonly planName = planName;
  protected readonly state = signal<CardState>({ status: 'loading' });

  /** CA-10.1 (plan DT-13): the card owns the history, asked only once the card is shown (D-17). */
  protected readonly history = new PagedList<Simulation>(
    (offset) => this.simulations.history(this.customerId, offset),
    inject(DestroyRef),
  );

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

  /** CA-10.8 and CA-10.9: the new simulation first, or the first page again. */
  protected onSaved(simulation: Simulation): void {
    if (this.history.status() === 'ready') {
      this.history.prepend(simulation);
    } else {
      this.history.reload();
    }
  }

  /** CA-9.5 and CA-2.5. */
  protected retry(): void {
    this.load(this.id());
  }

  private show(customer: Customer): void {
    this.customerId = customer.id;
    this.state.set({ status: 'ready', customer });
    this.history.reload();
  }

  private load(id: string): void {
    this.request?.unsubscribe();
    this.state.set({ status: 'loading' });
    this.request = this.api.get(id).subscribe({
      next: (customer) => this.show(customer),
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
