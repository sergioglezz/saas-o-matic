import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  input,
  signal,
} from '@angular/core';
import { Customer } from '../../core/api/api-models';
import { SimulationsApi } from '../../core/api/simulations-api';
import { LABELS, T } from '../../shared/texts';
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

/** Spec 005 RF-11 to RF-13: the simulator of the customer card. */
@Component({
  selector: 'app-simulator',
  imports: [PriceTotals, TierTable],
  templateUrl: './simulator.html',
  styleUrl: './simulator.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Simulator implements OnInit {
  readonly customer = input.required<Customer>();

  private readonly api = inject(SimulationsApi);

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
      !this.flow.pending()
    );
  });

  ngOnInit(): void {
    this.flow.quoteNow(INITIAL_USERS);
  }

  protected onSlider(event: Event): void {
    const text = (event.target as HTMLInputElement).value;
    this.usersText.set(text);
    this.sliderValue.set(Number(text));
    this.flow.change(this.users());
  }

  protected onUsers(event: Event): void {
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
    this.storageText.set((event.target as HTMLInputElement).value);
  }

  protected onCalls(event: Event): void {
    this.callsText.set((event.target as HTMLInputElement).value);
  }
}
