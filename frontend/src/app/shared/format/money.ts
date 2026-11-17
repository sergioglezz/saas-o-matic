import { decimalText, exactDecimal, roundHalfUp } from './decimal';

/** How to show an amount: the currency and its rate from EUR (null for EUR itself). */
export interface MoneyDisplay {
  readonly code: string;
  readonly rate: number | null;
}

export const EUR_DISPLAY: MoneyDisplay = { code: 'EUR', rate: null };

/**
 * CA-5.2: cents × rate ÷ 100 in units of the currency is cents × rate in hundredths. The product
 * is exact and rounded half up once, so 100 cents × 1.005 gives 101 hundredths (CV-11).
 */
export function toHundredths(cents: number, rate: number): bigint {
  const { digits, scale } = exactDecimal(rate);
  return roundHalfUp(BigInt(cents) * digits, scale);
}

const formats = new Map<string, Intl.NumberFormat>();

function moneyFormat(code: string): Intl.NumberFormat {
  let format = formats.get(code);
  if (format === undefined) {
    format = new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: code,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      useGrouping: 'always',
    });
    formats.set(code, format);
  }
  return format;
}

/** CA-5.3 and CA-5.4: EUR cents as they come; other currencies converted amount by amount. */
export function formatMoney(cents: number, display: MoneyDisplay): string {
  const hundredths = display.rate === null ? BigInt(cents) : toHundredths(cents, display.rate);
  return moneyFormat(display.code).format(decimalText(hundredths, 2));
}
