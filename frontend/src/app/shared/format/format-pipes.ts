import { Pipe, PipeTransform } from '@angular/core';
import { formatDate, formatDateTime } from './dates';
import { MoneyDisplay, formatMoney } from './money';
import { formatCount, formatTaxRate } from './numbers';

// Plan DT-15: pure pipes that receive the currency as an argument, so choosing another one
// formats again without asking anything (CA-4.3).

@Pipe({ name: 'money' })
export class MoneyPipe implements PipeTransform {
  transform(cents: number, display: MoneyDisplay): string {
    return formatMoney(cents, display);
  }
}

@Pipe({ name: 'count' })
export class CountPipe implements PipeTransform {
  transform(value: number): string {
    return formatCount(value);
  }
}

@Pipe({ name: 'taxRate' })
export class TaxRatePipe implements PipeTransform {
  transform(basisPoints: number): string {
    return formatTaxRate(basisPoints);
  }
}

@Pipe({ name: 'dateTime' })
export class DateTimePipe implements PipeTransform {
  transform(iso: string): string {
    return formatDateTime(iso);
  }
}

@Pipe({ name: 'day' })
export class DayPipe implements PipeTransform {
  transform(iso: string): string {
    return formatDate(iso);
  }
}
