// Spec 005 §5.6: every visible text, in one place (plan DT-19, RNF-5).

/** Messages and notices, by their identifier without the «T-» prefix. */
export const T = {
  CON: 'No se pudo conectar con el servidor',
  SRV: 'Error del servidor. Inténtalo de nuevo',
  RET: 'Reintentar',
  LRT: 'Cargando tasas…',
  RAT: (date: string) => `Tasas del ${date}`,
  RFL: (date: string) => `Tasas del ${date}. No se pudieron actualizar`,
  RNO: 'Tipos de cambio no disponibles: importes en EUR',
  EQ: (rate: string, code: string) => `1 EUR = ${rate} ${code}`,
  ORI: 'Conversión orientativa: los importes se calculan y guardan en EUR',
  ATR: 'Rates By Exchange Rate API',
  NEW: 'Nuevo cliente',
  LCL: 'Cargando clientes…',
  EMP: 'Todavía no hay clientes',
  NOR: (text: string) => `Ningún cliente coincide con «${text}»`,
  MOS: (shown: string, total: string) => `Mostrando ${shown} de ${total}`,
  MAS: 'Cargar más',
  LMO: 'Cargando…',
  OBL: 'Campo obligatorio',
  DNV: 'Datos no válidos',
  GDO: 'Guardando…',
  REG: 'Cliente registrado',
  LCU: 'Cargando cliente…',
  NFC: 'Cliente no encontrado',
  NFP: 'Página no encontrada',
  VOL: 'Volver al listado',
  LHI: 'Cargando historial…',
  HVA: 'Este cliente aún no tiene simulaciones',
  USR: 'Debe ser un número entero entre 0 y 100000',
  STO: 'Debe ser un número entero entre 0 y 1000000',
  APC: 'Debe ser un número entero entre 0 y 1000000000',
  UPD: 'Actualizando…',
  NUP: 'No se pudo actualizar',
  CNS: 'El país del cliente no está soportado',
  SOK: 'Simulación guardada',
  SKO: 'No se pudo guardar la simulación',
} as const;

/** Labels and buttons of §5.6. */
export const LABELS = {
  app: 'SaaS-O-Matic',
  currency: 'Divisa',
  search: 'Buscar por empresa o identificador fiscal',
  companyName: 'Empresa',
  taxIdField: 'Identificador fiscal (DNI/NIF/CIF)',
  contactEmail: 'Email de contacto',
  country: 'País',
  plan: 'Plan',
  save: 'Guardar',
  cancel: 'Cancelar',
  taxId: 'Identificador fiscal',
  createdAt: 'Fecha de alta',
  activeUsers: 'Usuarios activos',
  storageField: 'Almacenamiento (GB)',
  storage: 'Almacenamiento',
  apiCalls: 'Llamadas a la API al mes',
  tier: 'Tramo',
  tierUsers: 'Usuarios',
  units: 'Unidades',
  unitPrice: 'Precio por usuario',
  amount: 'Importe',
  subtotal: 'Subtotal',
  tax: (rate: string) => `Impuesto (${rate})`,
  total: 'Total mensual',
  saveSimulation: 'Guardar simulación',
  showBreakdown: 'Ver desglose',
  hideBreakdown: 'Ocultar desglose',
} as const;

/** Spec 006 §5.1: the titles added by the modern interface. */
export const TITLES = {
  customers: 'Clientes',
  simulator: 'Simulador',
  history: 'Historial de simulaciones',
} as const;

export interface Option {
  readonly value: string;
  readonly name: string;
}

/** CA-8.2 (P-1): the 7 countries of RN-4, in alphabetical order of their Spanish name. */
export const COUNTRIES: readonly { readonly code: string; readonly name: string }[] = [
  { code: 'DE', name: 'Alemania' },
  { code: 'ES', name: 'España' },
  { code: 'US', name: 'Estados Unidos' },
  { code: 'FR', name: 'Francia' },
  { code: 'IT', name: 'Italia' },
  { code: 'PT', name: 'Portugal' },
  { code: 'GB', name: 'Reino Unido' },
];

/** CA-8.3: the plans in this order. */
export const PLANS: readonly Option[] = [
  { value: 'starter', name: 'Starter' },
  { value: 'business', name: 'Business' },
  { value: 'enterprise', name: 'Enterprise' },
];

/** CA-4.1: the text of each currency option. */
export const CURRENCY_LABELS: Readonly<Record<string, string>> = {
  EUR: 'EUR (euro)',
  USD: 'USD (dólar estadounidense)',
  GBP: 'GBP (libra esterlina)',
  CHF: 'CHF (franco suizo)',
  JPY: 'JPY (yen japonés)',
};

/** CA-6.2 (D-20): the Spanish name, or the code as it comes if it is not one of the 7. */
export function countryName(code: string): string {
  return COUNTRIES.find((country) => country.code === code)?.name ?? code;
}

/** CA-6.2: «Starter», «Business» or «Enterprise»; anything else as it comes. */
export function planName(plan: string): string {
  return PLANS.find((option) => option.value === plan)?.name ?? plan;
}
