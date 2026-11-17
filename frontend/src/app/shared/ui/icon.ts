import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

/**
 * Spec 006 CA-3.5 (plan DT-6): decorative icons drawn in the project, without text and hidden
 * from screen readers, so the texts and accessible names of spec 005 do not change.
 */
const PATHS = {
  search: ['M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14', 'M20 20l-4-4'],
  plus: ['M12 5v14', 'M5 12h14'],
  back: ['M19 12H5', 'M11 6l-6 6 6 6'],
  check: ['M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18', 'M8 12l3 3 5-6'],
  alert: ['M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18', 'M12 8v5', 'M12 16.5v.5'],
  refresh: ['M20 12a8 8 0 1 1-2.3-5.7', 'M20 4v5h-5'],
  sliders: ['M4 7h16', 'M4 17h16', 'M9 4v6', 'M15 14v6'],
  clock: ['M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18', 'M12 7v5l3 2'],
  logo: ['M6 19V12', 'M12 19V6', 'M18 19v-9'],
} as const;

export type IconName = keyof typeof PATHS;

@Component({
  selector: 'app-icon',
  host: { 'aria-hidden': 'true', class: 'inline-flex shrink-0' },
  template: `
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      focusable="false"
      [attr.width]="size()"
      [attr.height]="size()"
    >
      @for (d of paths(); track $index) {
        <path [attr.d]="d" />
      }
    </svg>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Icon {
  readonly name = input.required<IconName>();
  readonly size = input(18);

  protected readonly paths = computed(() => PATHS[this.name()]);
}
