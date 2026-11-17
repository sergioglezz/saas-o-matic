import { ChangeDetectionStrategy, Component, inject, input } from '@angular/core';
import { PriceSnapshot } from '../../core/api/api-models';
import { DisplayCurrency } from '../../core/rates/display-currency';
import { MoneyPipe, TaxRatePipe } from '../format/format-pipes';
import { LABELS } from '../texts';

/**
 * Spec 005 CA-10.2 and CA-12.6: «Subtotal», «Impuesto ({tasa})» and «Total mensual», each one the
 * amount the backend sent (CA-5.1), converted on its own (D-6).
 */
@Component({
  selector: 'app-price-totals',
  imports: [MoneyPipe, TaxRatePipe],
  template: `
    <dl class="totals">
      <dt>{{ LABELS.subtotal }}</dt>
      <dd>{{ price().subtotal_cents | money: currency.display() }}</dd>
      <dt>{{ LABELS.tax(price().tax_rate_bp | taxRate) }}</dt>
      <dd>{{ price().tax_cents | money: currency.display() }}</dd>
      <dt class="total">{{ LABELS.total }}</dt>
      <dd class="total">{{ price().total_cents | money: currency.display() }}</dd>
    </dl>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PriceTotals {
  readonly price = input.required<PriceSnapshot>();

  protected readonly currency = inject(DisplayCurrency);
  protected readonly LABELS = LABELS;
}
