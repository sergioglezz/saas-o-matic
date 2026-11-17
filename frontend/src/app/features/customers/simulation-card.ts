import { ChangeDetectionStrategy, Component, input, signal } from '@angular/core';
import { Simulation } from '../../core/api/api-models';
import { CountPipe, DateTimePipe } from '../../shared/format/format-pipes';
import { LABELS } from '../../shared/texts';
import { PriceTotals } from '../../shared/ui/price-totals';
import { TierTable } from '../../shared/ui/tier-table';

/** Spec 005 CA-10.2 and CA-10.3 (D-18): a saved simulation, with its breakdown folded. */
@Component({
  selector: 'app-simulation-card',
  imports: [CountPipe, DateTimePipe, PriceTotals, TierTable],
  templateUrl: './simulation-card.html',
  styleUrl: './simulation-card.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SimulationCard {
  readonly simulation = input.required<Simulation>();

  protected readonly LABELS = LABELS;
  protected readonly open = signal(false);

  protected toggle(): void {
    this.open.update((open) => !open);
  }
}
