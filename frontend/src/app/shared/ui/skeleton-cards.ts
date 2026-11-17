import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

/**
 * Spec 006 CA-4.1: placeholders with the shape of the cards that are about to arrive, hidden from
 * screen readers (the loading text of spec 005 stays for them).
 */
@Component({
  selector: 'app-skeleton-cards',
  host: { 'aria-hidden': 'true', class: 'block' },
  template: `
    <ul class="cards" [class.two-columns]="columns() === 2">
      @for (card of cards(); track card) {
        <li class="card skeleton-card">
          @if (avatar()) {
            <span class="skeleton size-10 rounded-full"></span>
          }
          <span class="grid flex-1 gap-2">
            <span class="skeleton h-4 w-3/5"></span>
            <span class="skeleton h-3 w-4/5"></span>
          </span>
        </li>
      }
    </ul>
  `,
  styles: `
    .skeleton-card {
      display: flex;
      align-items: center;
      gap: 0.875rem;
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SkeletonCards {
  readonly count = input(4);
  readonly columns = input<1 | 2>(2);
  readonly avatar = input(true);

  protected readonly cards = computed(() => Array.from({ length: this.count() }, (_, i) => i));
}
