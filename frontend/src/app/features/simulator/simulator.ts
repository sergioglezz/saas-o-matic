import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { Customer, NewSimulation, Simulation } from '../../core/api/api-models';
import { RequestFailure, toRequestFailure } from '../../core/api/request-failure';
import { SimulationsApi } from '../../core/api/simulations-api';
import { LABELS, T } from '../../shared/texts';
import { Icon } from '../../shared/ui/icon';
import { PriceTotals } from '../../shared/ui/price-totals';
import { TierTable } from '../../shared/ui/tier-table';
import { QuoteFlow } from './quote-flow';
import {
  INITIAL_USERS,
  MAX_API_CALLS,
  MAX_STORAGE_GB,
  MAX_USERS,
  SLIDER_MAX,
  parseCount,
} from './usage-input';

/** The notice under «Guardar simulación» (CA-13.4 and CA-13.6 to CA-13.8). */
export type SaveNotice = 'none' | 'saved' | 'failed' | 'failed-retry' | 'unsupported';

/** Table 5.3, column «Guardar simulación». */
function noticeFor(failure: RequestFailure): SaveNotice {
  if (failure.kind === 'connection' || failure.kind === 'server') {
    return 'failed-retry';
  }
  const unsupported = failure.details.some((d) => d.field === 'customer_id' && d.message === T.CNS);
  return failure.kind === 'validation' && unsupported ? 'unsupported' : 'failed';
}

/** Spec 005 RF-11 to RF-13: the simulator of the customer card. */
@Component({
  selector: 'app-simulator',
  imports: [Icon, PriceTotals, TierTable],
  templateUrl: './simulator.html',
  styleUrl: './simulator.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Simulator implements OnInit {
  readonly customer = input.required<Customer>();
  /** CA-13.4: the card adds the saved simulation to the history (plan DT-13). */
  readonly saved = output<Simulation>();

  private readonly api = inject(SimulationsApi);
  private lastSave: NewSimulation | null = null;

  protected readonly T = T;
  protected readonly LABELS = LABELS;
  protected readonly SLIDER_MAX = SLIDER_MAX;

  /** CA-11.1 (D-3): what is written in each field. */
  protected readonly usersText = signal(String(INITIAL_USERS));
  protected readonly storageText = signal('0');
  protected readonly callsText = signal('0');
  /** CA-11.2 and CA-11.3: the slider stays where it was while the field is not valid. */
  protected readonly sliderValue = signal(INITIAL_USERS);

  protected readonly users = computed(() => parseCount(this.usersText(), MAX_USERS));
  protected readonly storage = computed(() => parseCount(this.storageText(), MAX_STORAGE_GB));
  protected readonly calls = computed(() => parseCount(this.callsText(), MAX_API_CALLS));

  protected readonly saving = signal(false);
  protected readonly saveNotice = signal<SaveNotice>('none');

  protected readonly flow = new QuoteFlow(
    (users) => this.api.quote(users, this.customer().country),
    inject(DestroyRef),
  );

  /** CA-13.1 (P-4): what is seen is what is saved. */
  protected readonly canSave = computed(() => {
    const users = this.users();
    return (
      users !== null &&
      this.storage() !== null &&
      this.calls() !== null &&
      this.flow.outcome() === 'ok' &&
      this.flow.quotedUsers() === users &&
      !this.flow.pending() &&
      !this.saving()
    );
  });

  ngOnInit(): void {
    this.flow.quoteNow(INITIAL_USERS);
  }

  /** CA-13.2. */
  protected save(): void {
    const users = this.users();
    const storage = this.storage();
    const calls = this.calls();
    if (!this.canSave() || users === null || storage === null || calls === null) {
      return;
    }
    this.send({
      customer_id: this.customer().id,
      active_users: users,
      storage_gb: storage,
      api_calls_per_month: calls,
    });
  }

  /** CA-13.6: exactly the body that failed. */
  protected retrySave(): void {
    if (this.lastSave !== null && !this.saving()) {
      this.send(this.lastSave);
    }
  }

  protected onSlider(event: Event): void {
    this.saveNotice.set('none');
    const text = (event.target as HTMLInputElement).value;
    this.usersText.set(text);
    this.sliderValue.set(Number(text));
    this.flow.change(this.users());
  }

  protected onUsers(event: Event): void {
    this.saveNotice.set('none');
    this.usersText.set((event.target as HTMLInputElement).value);
    const users = this.users();
    if (users !== null) {
      this.sliderValue.set(Math.min(users, SLIDER_MAX));
    }
    this.flow.change(users);
  }

  /** CA-12.8: the quote of the current users, at once. */
  protected retryQuote(): void {
    const users = this.users();
    if (users !== null) {
      this.flow.quoteNow(users);
    }
  }

  /** CA-11.9: storage and calls never ask for a quote. */
  protected onStorage(event: Event): void {
    this.saveNotice.set('none');
    this.storageText.set((event.target as HTMLInputElement).value);
  }

  protected onCalls(event: Event): void {
    this.saveNotice.set('none');
    this.callsText.set((event.target as HTMLInputElement).value);
  }

  /** CA-13.3 to CA-13.8; the values and the quote stay as they are (D-19). */
  private send(body: NewSimulation): void {
    this.lastSave = body;
    this.saving.set(true);
    this.saveNotice.set('none');
    this.api.save(body).subscribe({
      next: (simulation) => {
        this.saving.set(false);
        this.saveNotice.set('saved');
        this.saved.emit(simulation);
      },
      error: (error: unknown) => {
        this.saving.set(false);
        this.saveNotice.set(noticeFor(toRequestFailure(error)));
      },
    });
  }
}
