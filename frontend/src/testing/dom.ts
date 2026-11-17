import { TestBed } from '@angular/core/testing';
import { norm } from './text';

/**
 * Advances the fake clock and then runs change detection. Without zone.js, a change made inside a
 * timer is only painted on the next animation frame; TestBed.tick() paints it without moving the
 * clock, so tests about 299 and 300 ms stay exact.
 */
export async function settle(ms = 0): Promise<void> {
  await vi.advanceTimersByTimeAsync(ms);
  TestBed.tick();
}

export function textOf(node: Element | null | undefined): string {
  return norm(node?.textContent);
}

export function buttons(root: HTMLElement): HTMLButtonElement[] {
  return Array.from(root.querySelectorAll('button'));
}

/** The button whose visible text is exactly `label`, if there is one. */
export function buttonNamed(root: HTMLElement, label: string): HTMLButtonElement | undefined {
  return buttons(root).find((b) => textOf(b) === label);
}

export function linkNamed(root: HTMLElement, label: string): HTMLAnchorElement | undefined {
  return Array.from(root.querySelectorAll('a')).find((a) => textOf(a) === label);
}

/** The form control whose <label> has exactly this text. */
export function controlLabelled<T extends HTMLElement = HTMLInputElement>(
  root: HTMLElement,
  label: string,
): T {
  const found = Array.from(root.querySelectorAll('label')).find((l) => textOf(l) === label);
  const id = found?.htmlFor;
  const control = id ? root.querySelector<T>(`#${CSS.escape(id)}`) : null;
  if (control === null) {
    throw new Error(`No hay ningún control con la etiqueta «${label}»`);
  }
  return control;
}

/** Writes in a text field as a user would: the value, then the `input` event. */
export function typeInto(control: HTMLInputElement | HTMLTextAreaElement, value: string): void {
  control.value = value;
  control.dispatchEvent(new Event('input', { bubbles: true }));
}

/** Chooses an option of a native select, then the `change` event. */
export function choose(select: HTMLSelectElement, value: string): void {
  select.value = value;
  select.dispatchEvent(new Event('change', { bubbles: true }));
}

export function optionTexts(select: HTMLSelectElement): string[] {
  return Array.from(select.options).map((o) => norm(o.text));
}
