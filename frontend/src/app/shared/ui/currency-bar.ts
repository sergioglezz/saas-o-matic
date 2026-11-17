import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { DisplayCurrency } from '../../core/rates/display-currency';
import { ExchangeRates } from '../../core/rates/exchange-rates';
import { CurrencyCode } from '../../core/rates/rates-snapshot';
import { formatUnixDate } from '../format/dates';
import { formatRate } from '../format/numbers';
import { CURRENCY_LABELS, LABELS, T } from '../texts';

/** Spec 005 RF-3 and RF-4: selector, rates line, notices, T-EQ, T-ORI and attribution. */
@Component({
  selector: 'app-currency-bar',
  templateUrl: './currency-bar.html',
  styleUrl: './currency-bar.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CurrencyBar {
  protected readonly rates = inject(ExchangeRates);
  protected readonly currency = inject(DisplayCurrency);
  protected readonly T = T;
  protected readonly LABELS = LABELS;
  protected readonly CURRENCY_LABELS = CURRENCY_LABELS;

  /** CA-3.10: {fecha} of T-RAT and T-RFL. */
  protected readonly updated = computed(() => {
    const snapshot = this.rates.snapshot();
    return snapshot === null ? '' : formatUnixDate(snapshot.time_last_update_unix);
  });

  /** CA-4.7: T-EQ, only with a currency other than EUR. */
  protected readonly equivalence = computed(() => {
    const display = this.currency.display();
    return display.rate === null ? null : T.EQ(formatRate(display.rate), display.code);
  });

  protected choose(event: Event): void {
    this.currency.choose((event.target as HTMLSelectElement).value as CurrencyCode);
  }
}
