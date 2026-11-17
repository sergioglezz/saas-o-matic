import { decimalText, exactDecimal, roundHalfUp } from './decimal';

// Plan DT-5: es-ES does not group 4-digit numbers by default, and the spec wants «1.000» (D-7).
const COUNT_FORMAT = new Intl.NumberFormat('es-ES', {
  maximumFractionDigits: 0,
  useGrouping: 'always',
});

const TAX_FORMAT = new Intl.NumberFormat('es-ES', {
  style: 'percent',
  maximumFractionDigits: 2,
});

const RATE_FORMAT = new Intl.NumberFormat('es-ES', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 4,
  useGrouping: 'always',
});

/** CA-5.6: users, units, storage, calls, {n} and {total}. */
export function formatCount(value: number): string {
  return COUNT_FORMAT.format(value);
}

/** CA-5.5: basis points as a percentage; 2125 bp is the exact fraction 0.2125. */
export function formatTaxRate(basisPoints: number): string {
  return TAX_FORMAT.format(decimalText(BigInt(basisPoints), 4));
}

/** CA-4.7: the rate of T-EQ, rounded half up to 4 decimals at most, without trailing zeros. */
export function formatRate(rate: number): string {
  const { digits, scale } = exactDecimal(rate);
  return RATE_FORMAT.format(decimalText(roundHalfUp(digits, scale - 4), 4));
}

/** CA-12.6: «{from_users} a {to_users}», or «{from_users} o más» for the open tier. */
export function tierRange(fromUsers: number, toUsers: number | null): string {
  const from = formatCount(fromUsers);
  return toUsers === null ? `${from} o más` : `${from} a ${formatCount(toUsers)}`;
}
