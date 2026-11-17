type DateParts = Partial<Record<Intl.DateTimeFormatPartTypes, string>>;

const DAY: Intl.DateTimeFormatOptions = { day: '2-digit', month: '2-digit', year: 'numeric' };
const DAY_AND_TIME: Intl.DateTimeFormatOptions = {
  ...DAY,
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
};

// The formats are built on each call so they always use the browser's current time zone.
function partsOf(date: Date, options: Intl.DateTimeFormatOptions): DateParts {
  const parts: DateParts = {};
  for (const part of new Intl.DateTimeFormat('es-ES', options).formatToParts(date)) {
    parts[part.type] = part.value;
  }
  return parts;
}

function dayText(date: Date): string {
  const parts = partsOf(date, DAY);
  return `${parts.day}/${parts.month}/${parts.year}`;
}

/**
 * CA-5.7: `dd/mm/aaaa hh:mm` in 24 hours. Intl writes «16/11/2026, 11:00», with a comma, so the
 * text is built from its parts (plan DT-4).
 */
export function formatDateTime(iso: string): string {
  const parts = partsOf(new Date(iso), DAY_AND_TIME);
  return `${parts.day}/${parts.month}/${parts.year} ${parts.hour}:${parts.minute}`;
}

/** CA-5.7: dates without time, such as the customer's `created_at`. */
export function formatDate(iso: string): string {
  return dayText(new Date(iso));
}

/** CA-3.10: {fecha} of the rates notices, from `time_last_update_unix`. */
export function formatUnixDate(seconds: number): string {
  return dayText(new Date(seconds * 1000));
}
