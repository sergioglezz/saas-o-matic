// Data of spec 005, written once for every test (sections 5.4 and 6; ai-review-log entry 20).
import {
  Customer,
  CustomerPage,
  NewCustomer,
  NewSimulation,
  PriceQuote,
  Simulation,
  TierLine,
} from '../app/core/api/api-models';

/** Customer 1 of the C cases (spec 005 §6; 003 §5). */
export const ACME: Customer = {
  id: 1,
  company_name: 'Acme Telecom S.L.',
  tax_id: 'B12345674',
  contact_email: 'compras@acme.example',
  country: 'ES',
  plan: 'business',
  created_at: '2026-11-13T10:00:00Z',
};

/** Body of `POST /customers` in 003 §5 (AL-4). */
export const NEW_ACME: NewCustomer = {
  company_name: 'Acme Telecom S.L.',
  tax_id: 'B12345674',
  contact_email: 'compras@acme.example',
  country: 'ES',
  plan: 'business',
};

/** Starting response of the list cases (spec 005 §6.5). */
export const CUSTOMER_PAGE: CustomerPage = {
  items: [
    ACME,
    {
      id: 5,
      company_name: 'Albion Connect Ltd',
      tax_id: 'GB123456789',
      contact_email: 'purchasing@albion.example',
      country: 'GB',
      plan: 'starter',
      created_at: '2026-11-13T10:05:00Z',
    },
    {
      id: 6,
      company_name: 'Liberty Mesh Inc.',
      tax_id: 'US123456789',
      contact_email: 'procurement@liberty.example',
      country: 'US',
      plan: 'enterprise',
      created_at: '2026-11-13T10:06:00Z',
    },
  ],
  total: 3,
};

/** 1794787200 = 16/11/2026 00:00 UTC; 1794873600 = 17/11/2026 00:00 UTC (spec 005 §5.4). */
export const RATES_LAST_UPDATE = 1794787200;
export const RATES_NEXT_UPDATE = 1794873600;

/** Reference response of the rates API (spec 005 §5.4). */
export const RATES_RESPONSE = {
  result: 'success',
  time_last_update_unix: RATES_LAST_UPDATE,
  time_next_update_unix: RATES_NEXT_UPDATE,
  base_code: 'EUR',
  rates: { EUR: 1, USD: 1.0823, GBP: 0.8452, CHF: 0.9361, JPY: 161.27, MXN: 19.85 },
};

const TIERS_15: readonly TierLine[] = [
  { tier: 1, from_users: 1, to_users: 10, units: 10, unit_price_cents: 1000, amount_cents: 10000 },
  { tier: 2, from_users: 11, to_users: 50, units: 5, unit_price_cents: 800, amount_cents: 4000 },
  { tier: 3, from_users: 51, to_users: null, units: 0, unit_price_cents: 500, amount_cents: 0 },
];

/** Quote of §8.3 of the 00: 15 users in ES. */
export const QUOTE_15: PriceQuote = {
  users: 15,
  currency: 'EUR',
  tiers: TIERS_15,
  subtotal_cents: 14000,
  tax_rate_bp: 2100,
  tax_cents: 2940,
  total_cents: 16940,
};

/** Quote for 60 users in ES (spec 005 CO-14). */
export const QUOTE_60: PriceQuote = {
  users: 60,
  currency: 'EUR',
  tiers: [
    {
      tier: 1,
      from_users: 1,
      to_users: 10,
      units: 10,
      unit_price_cents: 1000,
      amount_cents: 10000,
    },
    {
      tier: 2,
      from_users: 11,
      to_users: 50,
      units: 40,
      unit_price_cents: 800,
      amount_cents: 32000,
    },
    {
      tier: 3,
      from_users: 51,
      to_users: null,
      units: 10,
      unit_price_cents: 500,
      amount_cents: 5000,
    },
  ],
  subtotal_cents: 47000,
  tax_rate_bp: 2100,
  tax_cents: 9870,
  total_cents: 56870,
};

/** Body of `POST /simulations` in 004 §5 (GU-2). */
export const NEW_SIMULATION: NewSimulation = {
  customer_id: 1,
  active_users: 15,
  storage_gb: 200,
  api_calls_per_month: 50000,
};

/** 201 of 004 §5, the simulation of SI-1 (HI-1, GU-3). */
export const SIMULATION_1: Simulation = {
  id: 1,
  ...NEW_SIMULATION,
  currency: 'EUR',
  tiers: TIERS_15,
  subtotal_cents: 14000,
  tax_rate_bp: 2100,
  tax_cents: 2940,
  total_cents: 16940,
  created_at: '2026-11-16T10:00:00Z',
};
