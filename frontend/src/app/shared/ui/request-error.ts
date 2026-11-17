import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import { RequestFailure } from '../../core/api/request-failure';
import { T } from '../texts';
import { Icon } from './icon';

/**
 * Spec 005 RF-2 outside the simulator: T-CON without an answer, T-SRV for any other failure the
 * screen does not show in its own way (table 5.3), and «Reintentar» (CA-2.5). Never the status,
 * the code or the body of the response (CA-2.4).
 */
@Component({
  selector: 'app-request-error',
  imports: [Icon],
  template: `
    <div class="notice notice-error request-error" role="status">
      <app-icon name="alert" [size]="16" />
      <p>{{ message() }}</p>
      <button type="button" class="secondary compact" (click)="retry.emit()">
        <app-icon name="refresh" [size]="16" />{{ T.RET }}
      </button>
    </div>
  `,
  styles: `
    .request-error {
      display: flex;
      gap: 0.5rem 0.75rem;
    }
    p {
      margin: 0;
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RequestError {
  readonly failure = input.required<RequestFailure>();
  readonly retry = output();

  protected readonly T = T;
  protected readonly message = computed(() =>
    this.failure().kind === 'connection' ? T.CON : T.SRV,
  );
}
