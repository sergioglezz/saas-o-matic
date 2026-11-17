import { ChangeDetectionStrategy, Component, inject, input } from '@angular/core';
import { TierLine } from '../../core/api/api-models';
import { DisplayCurrency } from '../../core/rates/display-currency';
import { CountPipe, MoneyPipe } from '../format/format-pipes';
import { tierRange } from '../format/numbers';
import { LABELS } from '../texts';

/**
 * Spec 005 CA-12.6: one row per tier, also those with 0 units, in the chosen currency. Used by
 * the simulator and by each simulation of the history (CA-10.3).
 */
@Component({
  selector: 'app-tier-table',
  imports: [CountPipe, MoneyPipe],
  template: `
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th scope="col">{{ LABELS.tier }}</th>
            <th scope="col">{{ LABELS.tierUsers }}</th>
            <th scope="col" class="number">{{ LABELS.units }}</th>
            <th scope="col" class="number">{{ LABELS.unitPrice }}</th>
            <th scope="col" class="number">{{ LABELS.amount }}</th>
          </tr>
        </thead>
        <tbody>
          @for (line of tiers(); track line.tier) {
            <tr>
              <th scope="row">{{ line.tier }}</th>
              <td>{{ range(line) }}</td>
              <td class="number">{{ line.units | count }}</td>
              <td class="number">{{ line.unit_price_cents | money: currency.display() }}</td>
              <td class="number">{{ line.amount_cents | money: currency.display() }}</td>
            </tr>
          }
        </tbody>
      </table>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TierTable {
  readonly tiers = input.required<readonly TierLine[]>();

  protected readonly currency = inject(DisplayCurrency);
  protected readonly LABELS = LABELS;

  protected range(line: TierLine): string {
    return tierRange(line.from_users, line.to_users);
  }
}
