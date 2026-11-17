import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideLocationMocks } from '@angular/common/testing';
import { Router } from '@angular/router';
import { App } from '../app/app';
import { appConfig } from '../app/app.config';
import { settle } from './dom';

export interface AppHarness {
  readonly fixture: ComponentFixture<App>;
  readonly root: HTMLElement;
  readonly http: HttpTestingController;
  readonly router: Router;
}

/**
 * Starts the real app (its providers, routes and the start of the rates) with the requests
 * answered by the test, and opens `url` as if it were typed or reloaded in the browser.
 */
export async function startApp(url: string): Promise<AppHarness> {
  TestBed.configureTestingModule({
    providers: [...appConfig.providers, provideHttpClientTesting(), provideLocationMocks()],
  });
  const fixture = TestBed.createComponent(App);
  const router = TestBed.inject(Router);
  await router.navigateByUrl(url);
  await settle();
  return {
    fixture,
    root: fixture.nativeElement as HTMLElement,
    http: TestBed.inject(HttpTestingController),
    router,
  };
}

/** The same app opened again at `url`: a reload keeps only the browser storage. */
export async function reloadApp(url: string): Promise<AppHarness> {
  TestBed.resetTestingModule();
  return startApp(url);
}

/** Clicks a link or button and waits for the navigation it starts. */
export async function clickAndSettle(element: HTMLElement | undefined): Promise<void> {
  if (element === undefined) {
    throw new Error('No existe el elemento que se quiere pulsar');
  }
  element.click();
  await settle();
}
