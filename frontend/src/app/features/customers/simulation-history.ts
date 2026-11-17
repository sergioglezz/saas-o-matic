import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { Simulation } from '../../core/api/api-models';
import { PagedList } from '../../shared/paged-list';
import { T } from '../../shared/texts';
import { LoadMore } from '../../shared/ui/load-more';
import { RequestError } from '../../shared/ui/request-error';
import { SimulationCard } from './simulation-card';

/**
 * Spec 005 RF-10: the history of the customer, newest first as the backend sends it. The card
 * owns the list (plan DT-13); this section only shows its states.
 */
@Component({
  selector: 'app-simulation-history',
  imports: [LoadMore, RequestError, SimulationCard],
  template: `
    <section class="stack">
      @switch (list().status()) {
        @case ('loading') {
          <p role="status">{{ T.LHI }}</p>
        }
        @case ('error') {
          @if (list().failure(); as failure) {
            <app-request-error [failure]="failure" (retry)="list().retry()" />
          }
        }
        @case ('ready') {
          @if (list().total() === 0) {
            <p role="status">{{ T.HVA }}</p>
          } @else {
            <ul class="cards two-columns">
              @for (simulation of list().items(); track simulation.id) {
                <li><app-simulation-card [simulation]="simulation" /></li>
              }
            </ul>
            <app-load-more [list]="list()" />
          }
        }
      }
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SimulationHistory {
  readonly list = input.required<PagedList<Simulation>>();
  protected readonly T = T;
}
