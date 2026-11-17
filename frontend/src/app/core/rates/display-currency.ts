import { Injectable, computed, inject, signal } from '@angular/core';
import { EUR_DISPLAY, MoneyDisplay } from '../../shared/format/money';
import { BrowserStorage } from './browser-storage';
import { ExchangeRates } from './exchange-rates';
import { CurrencyCode, offeredCurrencies, rateOf } from './rates-snapshot';

/** Spec 005 RF-4: the offered currencies, the chosen one and how to show amounts with it. */
@Injectable({ providedIn: 'root' })
export class DisplayCurrency {
  private readonly rates = inject(ExchangeRates);
  private readonly storage = inject(BrowserStorage);

  /** CA-4.6 (D-13): the remembered currency is only replaced when the user chooses another. */
  private readonly remembered = signal(this.storage.readCurrency());

  /** CA-4.2: disabled while the rates load. */
  readonly loading = computed(() => this.rates.status() === 'loading');

  /** CA-3.5; only EUR while the rates load or if there are none. */
  readonly offered = computed(() => offeredCurrencies(this.rates.snapshot()));

  /** CA-4.5 and CA-4.6: the remembered currency if it is offered, EUR otherwise. */
  readonly selected = computed<CurrencyCode>(() => {
    const remembered = this.remembered();
    return this.offered().find((code) => code === remembered) ?? 'EUR';
  });

  /** CA-5.2 and CA-5.3: what the money pipe needs. */
  readonly display = computed<MoneyDisplay>(() => {
    const code = this.selected();
    return code === 'EUR' ? EUR_DISPLAY : { code, rate: rateOf(this.rates.snapshot(), code) };
  });

  /** CA-4.3 and CA-4.4: no request; only the browser storage. */
  choose(code: CurrencyCode): void {
    this.remembered.set(code);
    this.storage.writeCurrency(code);
  }
}
