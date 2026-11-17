import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { CurrencyBar } from './shared/ui/currency-bar';
import { Icon } from './shared/ui/icon';
import { LABELS } from './shared/texts';

/** Spec 005 CA-1.5: the same header on every screen, with the name, the currency and the rates. */
@Component({
  selector: 'app-root',
  imports: [RouterLink, RouterOutlet, CurrencyBar, Icon],
  templateUrl: './app.html',
  styleUrl: './app.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  protected readonly LABELS = LABELS;
}
