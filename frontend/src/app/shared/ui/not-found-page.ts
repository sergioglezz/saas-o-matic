import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { T } from '../texts';

/** Spec 005 CA-1.3: any other address, without asking the backend. */
@Component({
  selector: 'app-not-found-page',
  imports: [RouterLink],
  template: `
    <section class="card narrow">
      <h1>{{ T.NFP }}</h1>
      <a routerLink="/clientes">{{ T.VOL }}</a>
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotFoundPage {
  protected readonly T = T;
}
