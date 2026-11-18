import { decimalText, exactDecimal, roundHalfUp } from './decimal';

/** How to show an amount: the currency and its rate from EUR (null for EUR itself). */
export interface MoneyDisplay {
  readonly code: string;
  readonly rate: number | null;
}

export const EUR_DISPLAY: MoneyDisplay = { code: 'EUR', rate: null };

const formats = new Map<string, Intl.NumberFormat>();

/**
 * Spec 008 plan DT-3: without fraction digits of its own, Intl uses the decimals of the currency
 * in ISO 4217, the same ones the amount text already has, so it never rounds again.
 */
function moneyFormat(code: string): Intl.NumberFormat {
  let format = formats.get(code);
  if (format === undefined) {
    format = new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: code,
      useGrouping: 'always',
    });
    formats.set(code, format);
  }
  return format;
}

/** Spec 008 CA-1.1 (plan DT-1): the decimals of the currency in ISO 4217, 2 in EUR, 0 in JPY. */
export function currencyDecimals(code: string): number {
  return moneyFormat(code).resolvedOptions().maximumFractionDigits ?? 2;
}

/**
 * 005 CA-5.2 and 008 CA-1.2: cents × rate ÷ 100 in units of the currency, written in its minor
 * units (hundredths with 2 decimals, whole yen with 0). The product is exact and rounded half up
 * once, so 100 cents × 1.005 gives 101 hundredths (005 CV-11) and 1850 cents × 161.27 gives
 * 2983 yen, not the 2984 of rounding 2983.495 to hundredths first (008 YN-5).
 */
export function toMinorUnits(cents: number, rate: number, decimals: number): bigint {
  const { digits, scale } = exactDecimal(rate);
  return roundHalfUp(BigInt(cents) * digits, scale + 2 - decimals);
}

/** 005 CA-5.3 and CA-5.4, 008 CA-1.3: EUR cents as they come; the rest converted one by one. */
export function formatMoney(cents: number, display: MoneyDisplay): string {
  const decimals = currencyDecimals(display.code);
  const minorUnits =
    display.rate === null ? BigInt(cents) : toMinorUnits(cents, display.rate, decimals);
  return moneyFormat(display.code).format(decimalText(minorUnits, decimals));
}
