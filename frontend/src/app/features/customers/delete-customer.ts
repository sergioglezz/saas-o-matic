import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  Injector,
  afterNextRender,
  computed,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { Subscription } from 'rxjs';
import { Customer } from '../../core/api/api-models';
import { CustomersApi } from '../../core/api/customers-api';
import { toRequestFailure } from '../../core/api/request-failure';
import { formatCount } from '../../shared/format/numbers';
import { LABELS, T, T7 } from '../../shared/texts';
import { Icon } from '../../shared/ui/icon';

type DeleteState = 'closed' | 'asking' | 'deleting' | 'failed';

/**
 * Spec 007 RF-2 (plan DT-3): «Borrar cliente», its confirmation inside the card and the request.
 * The card decides where to go next: `deleted` after a 204 and `missing` after a 404.
 */
@Component({
  selector: 'app-delete-customer',
  imports: [Icon],
  templateUrl: './delete-customer.html',
  styleUrl: './delete-customer.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DeleteCustomer {
  readonly customer = input.required<Customer>();
  /** How many simulations the history has, or null while it is not known (CA-2.3, D-7). */
  readonly historyTotal = input.required<number | null>();
  readonly deleted = output();
  readonly missing = output();

  private readonly api = inject(CustomersApi);
  private readonly injector = inject(Injector);
  private readonly opener = viewChild.required<ElementRef<HTMLButtonElement>>('opener');
  private readonly box = viewChild<ElementRef<HTMLElement>>('box');
  private request: Subscription | null = null;

  protected readonly T = T;
  protected readonly T7 = T7;
  protected readonly LABELS = LABELS;
  protected readonly state = signal<DeleteState>('closed');

  /** CA-2.3: the number only when the history is loaded; nothing when it is empty. */
  protected readonly historyWarning = computed(() => {
    const total = this.historyTotal();
    if (total === null) {
      return T7.HX;
    }
    if (total === 0) {
      return null;
    }
    return total === 1 ? T7.H1 : T7.HN(formatCount(total));
  });

  constructor() {
    inject(DestroyRef).onDestroy(() => this.request?.unsubscribe());
  }

  /** CA-2.2: nothing is asked of the backend until the user confirms. */
  protected ask(): void {
    if (this.state() === 'closed') {
      this.state.set('asking');
    }
    afterNextRender(() => this.box()?.nativeElement.focus(), { injector: this.injector });
  }

  /** CA-2.4: «Cancelar» or Escape; not while the request is on its way. */
  protected cancel(): void {
    if (this.state() === 'deleting') {
      return;
    }
    this.state.set('closed');
    this.opener().nativeElement.focus();
  }

  /** CA-2.5 to CA-2.8; «Reintentar» repeats the same request. */
  protected confirm(): void {
    if (this.state() === 'deleting') {
      return;
    }
    this.state.set('deleting');
    this.request = this.api.remove(this.customer().id).subscribe({
      next: () => this.deleted.emit(),
      error: (error: unknown) => {
        if (toRequestFailure(error).kind === 'not_found') {
          this.missing.emit();
        } else {
          this.state.set('failed');
        }
      },
    });
  }
}
