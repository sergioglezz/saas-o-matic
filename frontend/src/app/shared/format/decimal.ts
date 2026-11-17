/**
 * Exact decimal arithmetic for spec 005 RF-5 (plan DT-3): a rate such as 1.005 is taken with the
 * decimals of its shortest writing, never through floating point.
 */
export interface ExactDecimal {
  /** All the digits of the number, without the decimal point. */
  readonly digits: bigint;
  /** How many of those digits are decimals: value = digits / 10^scale. */
  readonly scale: number;
}

const DECIMAL_WRITING = /^(\d+)(?:\.(\d+))?(?:e([+-]\d+))?$/;

export function exactDecimal(value: number): ExactDecimal {
  const match = DECIMAL_WRITING.exec(String(value));
  if (match === null) {
    throw new RangeError(`Se esperaba un número finito no negativo: ${value}`);
  }
  const [, whole, fraction = '', exponent = '0'] = match;
  const scale = fraction.length - Number(exponent);
  const digits = BigInt(whole + fraction);
  return scale >= 0 ? { digits, scale } : { digits: digits * 10n ** BigInt(-scale), scale: 0 };
}

/** digits / 10^shift rounded half up; the values are never negative (amounts and rates). */
export function roundHalfUp(digits: bigint, shift: number): bigint {
  if (shift <= 0) {
    return digits * 10n ** BigInt(-shift);
  }
  const divisor = 10n ** BigInt(shift);
  return (digits + divisor / 2n) / divisor;
}

/** value / 10^decimals written as a plain decimal text that Intl accepts ("1234.56"). */
export function decimalText(value: bigint, decimals: number): `${number}` {
  const text = value.toString().padStart(decimals + 1, '0');
  const written = decimals === 0 ? text : `${text.slice(0, -decimals)}.${text.slice(-decimals)}`;
  return written as `${number}`;
}
