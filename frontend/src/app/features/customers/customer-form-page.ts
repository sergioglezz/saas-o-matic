import { ChangeDetectionStrategy, Component, ElementRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NewCustomer } from '../../core/api/api-models';
import { CustomersApi } from '../../core/api/customers-api';
import { RequestFailure, toRequestFailure } from '../../core/api/request-failure';
import { COUNTRIES, LABELS, PLANS, T } from '../../shared/texts';
import { RequestError } from '../../shared/ui/request-error';
import { CUSTOMER_FIELDS, CustomerField, fieldErrorsFrom } from './customer-form-errors';

/** CA-8.1 and CA-8.4: the three text fields, their labels and their native limits. */
const TEXT_FIELDS = [
  { name: 'company_name', label: LABELS.companyName, max: 120, autocomplete: 'organization' },
  { name: 'tax_id', label: LABELS.taxIdField, max: 30, autocomplete: 'off' },
  { name: 'contact_email', label: LABELS.contactEmail, max: 254, autocomplete: 'email' },
] as const;

function textControl(): FormControl<string> {
  return new FormControl('', { nonNullable: true });
}

/** Spec 005 RF-8: new customer. The browser checks only what is required (P-2, DT-14). */
@Component({
  selector: 'app-customer-form-page',
  imports: [ReactiveFormsModule, RouterLink, RequestError],
  templateUrl: './customer-form-page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CustomerFormPage {
  private readonly api = inject(CustomersApi);
  private readonly router = inject(Router);
  private readonly host: ElementRef<HTMLElement> = inject(ElementRef);
  private lastBody: NewCustomer | null = null;

  protected readonly T = T;
  protected readonly LABELS = LABELS;
  protected readonly COUNTRIES = COUNTRIES;
  protected readonly PLANS = PLANS;
  protected readonly TEXT_FIELDS = TEXT_FIELDS;
  protected readonly form = new FormGroup({
    company_name: textControl(),
    tax_id: textControl(),
    contact_email: textControl(),
    country: textControl(),
    plan: textControl(),
  });
  protected readonly errors = signal<Partial<Record<CustomerField, readonly string[]>>>({});
  protected readonly invalidData = signal(false);
  protected readonly failure = signal<RequestFailure | null>(null);
  protected readonly saving = signal(false);

  constructor() {
    // CA-8.14: changing a field removes only its own messages.
    for (const field of CUSTOMER_FIELDS) {
      this.form.controls[field].valueChanges
        .pipe(takeUntilDestroyed())
        .subscribe(() => this.clearErrors(field));
    }
  }

  /** CA-8.5 to CA-8.8. */
  protected submit(): void {
    if (this.saving()) {
      return;
    }
    const values = this.form.getRawValue();
    const empty = CUSTOMER_FIELDS.filter((field) => values[field].trim() === '');
    if (empty.length > 0) {
      this.showMessages(Object.fromEntries(empty.map((field) => [field, [T.OBL]])), false);
      this.focus(empty[0]);
      return;
    }
    this.send(values);
  }

  /** CA-8.12: exactly the body that failed. */
  protected retry(): void {
    if (this.lastBody !== null) {
      this.send(this.lastBody);
    }
  }

  /** CA-8.15. */
  protected cancel(): void {
    void this.router.navigateByUrl('/clientes');
  }

  protected errorId(field: CustomerField): string | null {
    return this.errors()[field] === undefined ? null : `customer-${field}-error`;
  }

  private send(body: NewCustomer): void {
    this.lastBody = body;
    this.saving.set(true);
    this.showMessages({}, false);
    this.api.create(body).subscribe({
      // CA-8.9: T-REG travels with the navigation (plan DT-12).
      next: (customer) =>
        void this.router.navigate(['/clientes', customer.id], { state: { registered: true } }),
      error: (error: unknown) => {
        this.saving.set(false);
        this.showFailure(toRequestFailure(error));
      },
    });
  }

  /** CA-8.10 to CA-8.12, following table 5.3 for the new customer form. */
  private showFailure(failure: RequestFailure): void {
    if (failure.kind === 'validation' || failure.kind === 'conflict') {
      const { fields, general } = fieldErrorsFrom(failure.details);
      this.showMessages(fields, general);
    } else {
      this.failure.set(failure);
    }
  }

  private showMessages(
    fields: Partial<Record<CustomerField, readonly string[]>>,
    general: boolean,
  ): void {
    this.errors.set(fields);
    this.invalidData.set(general);
    this.failure.set(null);
  }

  private clearErrors(field: CustomerField): void {
    if (this.errors()[field] !== undefined) {
      this.errors.update((current) => {
        const others = { ...current };
        delete others[field];
        return others;
      });
    }
  }

  private focus(field: CustomerField): void {
    this.host.nativeElement.querySelector<HTMLElement>(`#customer-${field}`)?.focus();
  }
}
