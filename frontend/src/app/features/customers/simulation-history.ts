import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { Simulation } from '../../core/api/api-models';
import { PagedList } from '../../shared/paged-list';
import { T } from '../../shared/texts';
import { LoadMore } from '../../shared/ui/load-more';
import { RequestError } from '../../shared/ui/request-error';
import { SkeletonCards } from '../../shared/ui/skeleton-cards';
import { SimulationCard } from './simulation-card';

/**
 * Spec 005 RF-10: the history of the customer, newest first as the backend sends it. The card
 * owns the list (plan DT-13); this section only shows its states.
 */
@Component({
  selector: 'app-simulation-history',
  imports: [LoadMore, RequestError, SimulationCard, SkeletonCards],
  template: `
    <div class="stack">
      @switch (list().status()) {
        @case ('loading') {
          <p role="status" class="muted">{{ T.LHI }}</p>
          <app-skeleton-cards [count]="2" [avatar]="false" />
        }
        @case ('error') {
          @if (list().failure(); as failure) {
            <app-request-error [failure]="failure" (retry)="list().retry()" />
          }
        }
        @case ('ready') {
          @if (list().total() === 0) {
            <p role="status" class="empty-state">{{ T.HVA }}</p>
          } @else {
            <ul class="cards two-columns">
              @for (simulation of list().items(); track simulation.id) {
                <li class="anim-rise" [style.--i]="$index">
                  <app-simulation-card [simulation]="simulation" />
                </li>
              }
            </ul>
            <app-load-more [list]="list()" />
          }
        }
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SimulationHistory {
  readonly list = input.required<PagedList<Simulation>>();
  protected readonly T = T;
}
