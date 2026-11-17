// Spec 005 §5.2: the types of the backend contract (003 §5, 004 §5 and §8.3 of the 00), with the
// same snake_case names. Amounts are whole cents in EUR and only `money.ts` converts them.

export interface ErrorDetail {
  readonly field: string;
  readonly message: string;
}

export interface Page<T> {
  readonly items: readonly T[];
  readonly total: number;
}

export interface NewCustomer {
  readonly company_name: string;
  readonly tax_id: string;
  readonly contact_email: string;
  readonly country: string;
  readonly plan: string;
}

export interface Customer extends NewCustomer {
  readonly id: number;
  readonly created_at: string;
}

export type CustomerPage = Page<Customer>;

export interface TierLine {
  readonly tier: number;
  readonly from_users: number;
  readonly to_users: number | null;
  readonly units: number;
  readonly unit_price_cents: number;
  readonly amount_cents: number;
}

/** The price snapshot shared by the quote and the saved simulation. */
export interface PriceSnapshot {
  readonly currency: string;
  readonly tiers: readonly TierLine[];
  readonly subtotal_cents: number;
  readonly tax_rate_bp: number;
  readonly tax_cents: number;
  readonly total_cents: number;
}

export interface PriceQuote extends PriceSnapshot {
  readonly users: number;
}

export interface NewSimulation {
  readonly customer_id: number;
  readonly active_users: number;
  readonly storage_gb: number;
  readonly api_calls_per_month: number;
}

export interface Simulation extends NewSimulation, PriceSnapshot {
  readonly id: number;
  readonly created_at: string;
}

export type SimulationPage = Page<Simulation>;
