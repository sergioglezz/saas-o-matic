import { PriceQuote } from '../app/core/api/api-models';
import { AppHarness } from './app';
import { expectHistory, expectQuote, openCard } from './detail';
import { buttonNamed, controlLabelled, settle, textOf, typeInto } from './dom';
import { QUOTE_15 } from './spec-data';

/** The labels of CA-11.1. */
export const VALUE = {
  users: 'Usuarios activos',
  storage: 'Almacenamiento (GB)',
  calls: 'Llamadas a la API al mes',
} as const;

/** A 200 for any number of users (the amounts are those of §8.3; only `users` changes). */
export function quoteFor(users: number): PriceQuote {
  return { ...QUOTE_15, users };
}

/**
 * The card of customer 1 with the simulator shown: the history answered empty and the initial
 * quote answered with §8.3, unless the test wants to answer them itself.
 */
export async function openSimulator(options: { answerQuote?: boolean } = {}): Promise<AppHarness> {
  const app = await openCard();
  expectHistory(app.http).flush({ items: [], total: 0 });
  if (options.answerQuote ?? true) {
    expectQuote(app.http).flush(QUOTE_15);
  }
  await settle();
  return app;
}

export function simulator(app: AppHarness): HTMLElement {
  return app.root.querySelector('app-simulator') as HTMLElement;
}

export function valueField(app: AppHarness, label: string): HTMLInputElement {
  return controlLabelled<HTMLInputElement>(simulator(app), label);
}

export function slider(app: AppHarness): HTMLInputElement {
  return simulator(app).querySelector('input[type="range"]') as HTMLInputElement;
}

export async function typeValue(app: AppHarness, label: string, text: string): Promise<void> {
  typeInto(valueField(app, label), text);
  await settle();
}

export async function slide(app: AppHarness, value: number): Promise<void> {
  typeInto(slider(app), String(value));
  await settle();
}

export function saveButton(app: AppHarness): HTMLButtonElement {
  const root = simulator(app);
  return (buttonNamed(root, 'Guardar simulación') ??
    buttonNamed(root, 'Guardando…')) as HTMLButtonElement;
}

/** The message tied to a value through its `aria-describedby`. */
export function valueError(app: AppHarness, label: string): string {
  const id = valueField(app, label).getAttribute('aria-describedby');
  return id ? textOf(simulator(app).querySelector(`#${CSS.escape(id)}`)) : '';
}
