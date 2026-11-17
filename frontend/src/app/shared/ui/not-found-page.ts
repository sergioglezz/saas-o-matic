import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { T } from '../texts';
import { Icon } from './icon';

/** Spec 005 CA-1.3: any other address, without asking the backend; centred (spec 006 CA-2.2). */
@Component({
  selector: 'app-not-found-page',
  imports: [RouterLink, Icon],
  template: `
    <section class="card narrow anim-page grid justify-items-center gap-4 text-center">
      <span class="grid size-14 place-items-center rounded-full bg-brand-50 text-brand-700">
        <app-icon name="alert" [size]="28" />
      </span>
      <h1>{{ T.NFP }}</h1>
      <a class="button secondary" routerLink="/clientes">
        <app-icon name="back" [size]="16" />{{ T.VOL }}
      </a>
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotFoundPage {
  protected readonly T = T;
}
