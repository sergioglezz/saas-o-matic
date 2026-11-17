import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import { RequestFailure } from '../../core/api/request-failure';
import { T } from '../texts';

/**
 * Spec 005 RF-2 outside the simulator: T-CON without an answer, T-SRV for any other failure the
 * screen does not show in its own way (table 5.3), and «Reintentar» (CA-2.5). Never the status,
 * the code or the body of the response (CA-2.4).
 */
@Component({
  selector: 'app-request-error',
  template: `
    <div class="request-error" role="status">
      <p class="error-text">{{ message() }}</p>
      <button type="button" class="secondary" (click)="retry.emit()">{{ T.RET }}</button>
    </div>
  `,
  styles: `
    .request-error {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem 1rem;
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
