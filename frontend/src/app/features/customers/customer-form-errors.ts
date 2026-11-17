import { ErrorDetail } from '../../core/api/api-models';

export type CustomerField = 'company_name' | 'tax_id' | 'contact_email' | 'country' | 'plan';

/** CA-8.1 and CA-8.5: the five fields, in the order of the form. */
export const CUSTOMER_FIELDS: readonly CustomerField[] = [
  'company_name',
  'tax_id',
  'contact_email',
  'country',
  'plan',
];

export interface FieldErrors {
  readonly fields: Partial<Record<CustomerField, readonly string[]>>;
  /** CA-8.10: T-DNV, when a detail names another field or there are no details. */
  readonly general: boolean;
}

function isCustomerField(field: string): field is CustomerField {
  return (CUSTOMER_FIELDS as readonly string[]).includes(field);
}

/**
 * CA-8.10 and CA-8.11: each `message` of a 422 or a 409 next to the field its `field` names, as
 * it comes (CA-2.6).
 */
export function fieldErrorsFrom(details: readonly ErrorDetail[]): FieldErrors {
  const fields: Partial<Record<CustomerField, string[]>> = {};
  let general = details.length === 0;
  for (const { field, message } of details) {
    if (isCustomerField(field)) {
      fields[field] = [...(fields[field] ?? []), message];
    } else {
      general = true;
    }
  }
  return { fields, general };
}
