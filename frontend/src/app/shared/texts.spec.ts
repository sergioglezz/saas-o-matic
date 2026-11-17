import { COUNTRIES, CURRENCY_LABELS, PLANS, T, countryName, planName } from './texts';

// Spec 005 §5.6 and the texts of RF-4, RF-6 and RF-8.
describe('texts (spec 005 §5.6)', () => {
  it('CA-8.2: the 7 countries of RN-4 in alphabetical order, by their Spanish name', () => {
    expect(COUNTRIES.map((c) => c.name)).toEqual([
      'Alemania',
      'España',
      'Estados Unidos',
      'Francia',
      'Italia',
      'Portugal',
      'Reino Unido',
    ]);
    expect(COUNTRIES.map((c) => c.code)).toEqual(['DE', 'ES', 'US', 'FR', 'IT', 'PT', 'GB']);
  });

  it('CA-6.2: country names, or the code as it comes (LI-3)', () => {
    expect(countryName('ES')).toBe('España');
    expect(countryName('GB')).toBe('Reino Unido');
    expect(countryName('MX')).toBe('MX');
  });

  it('CA-8.3 and CA-6.2: plans in order, with their visible name', () => {
    expect(PLANS.map((p) => p.name)).toEqual(['Starter', 'Business', 'Enterprise']);
    expect(PLANS.map((p) => p.value)).toEqual(['starter', 'business', 'enterprise']);
    expect(planName('business')).toBe('Business');
    expect(planName('otro')).toBe('otro');
  });

  it('CA-4.1: currency options', () => {
    expect(CURRENCY_LABELS).toEqual({
      EUR: 'EUR (euro)',
      USD: 'USD (dólar estadounidense)',
      GBP: 'GBP (libra esterlina)',
      CHF: 'CHF (franco suizo)',
      JPY: 'JPY (yen japonés)',
    });
  });

  it('texts with values', () => {
    expect(T.NOR('zzz')).toBe('Ningún cliente coincide con «zzz»');
    expect(T.MOS('50', '120')).toBe('Mostrando 50 de 120');
    expect(T.RAT('16/11/2026')).toBe('Tasas del 16/11/2026');
    expect(T.RFL('16/11/2026')).toBe('Tasas del 16/11/2026. No se pudieron actualizar');
    expect(T.EQ('1,0823', 'USD')).toBe('1 EUR = 1,0823 USD');
  });

  it('T-USR, T-STO and T-APC match the messages of the backend (004 §5)', () => {
    expect(T.USR).toBe('Debe ser un número entero entre 0 y 100000');
    expect(T.STO).toBe('Debe ser un número entero entre 0 y 1000000');
    expect(T.APC).toBe('Debe ser un número entero entre 0 y 1000000000');
  });
});
