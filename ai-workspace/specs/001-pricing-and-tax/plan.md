# Plan técnico — 001 Precios por tramos e impuestos

Estado: aprobado (2026-11-14) · Spec: `spec.md` v1.2 (aprobada) · Constitución: `ai-workspace/docs/constitution.md` · Arquitectura: §5, §7 y §8 de `00-spec-first.md`

## 1. Resumen y alcance

- **Construye:** el cálculo puro (tramos, impuesto, total), la tabla `tax_rates` con su migración y la función de servicio que une ambos. Es lo que consumirán 002 y la futura spec de simulaciones.
- **Cubre:** RF-1, RF-2, RF-3, RF-4, RF-6, RF-7 y RF-13.
- **No cubre, por diseño:** RF-5 y RF-8 a RF-12, que se movieron a 002 y tendrán su propio plan.
- **Fuera de este plan:** routers, esquemas Pydantic, el manejador de errores HTTP, clientes, simulaciones, el frontend y los datos de demostración.
- **Dependencias:** solo las ya aprobadas. SQLAlchemy 2 y Alembic para ejecución; pytest, ruff y mypy para desarrollo (§5 del 00, ADR 0008). FastAPI se añade con 002.

## 2. Estructura de módulos

| Módulo | Responsabilidad | Puede importar | RF |
| --- | --- | --- | --- |
| `app/domain/pricing.py` | Constante `TIERS`, `MAX_USERS`, `validate_users`, `tier_breakdown`, `build_quote` y los tipos `Tier`, `TierLine` y `PriceQuote` | Biblioteca estándar y `domain.*` | 1, 2, 3, 7 |
| `app/domain/tax.py` | `tax_cents` (redondeo) y `validate_rate_bp` | Biblioteca estándar y `domain.errors` | 6, 13 |
| `app/domain/errors.py` | `PricingError` y sus subclases | Biblioteca estándar | 3, 4, 13 |
| `app/services/pricing.py` | `quote` y `set_tax_rate`; el protocolo `TaxRateSource` | `domain.*` y `repositories.*` (solo para tipos) | 3, 4, 13 |
| `app/repositories/tax_rates.py` | `get_rate_bp`, `upsert` y `delete` sobre `tax_rates` | `db.*` y SQLAlchemy | 4, 13 |
| `app/db/models.py` · `app/db/session.py` | Modelo `TaxRate`; motor y sesión con `PRAGMA foreign_keys=ON` en cada conexión | SQLAlchemy y `core.config` | 4, 13 |
| `app/db/migrations/` (`env.py` y `versions/0001_create_tax_rates.py`) | Crea la tabla e inserta las 7 tasas | Alembic y SQLAlchemy | 4, 13 |
| `app/core/config.py` | `DATABASE_URL`, leída de una variable de entorno con valor por defecto local | Biblioteca estándar | — |

Las dependencias van en una sola dirección: `services → (domain, repositories)` y `repositories → db`. `domain` no importa nada externo (principio 3). Un test de arquitectura lo comprueba (sección 7).

**Seed:** esta funcionalidad no aporta filas al seed. Las tasas por defecto van en la migración (spec D-5); el seed de datos de demostración lo creará la spec de clientes.

## 3. Modelo de datos (RF-4, RF-13)

Tabla `tax_rates`:

| Columna | Tipo | Restricciones |
| --- | --- | --- |
| `country` | TEXT | PRIMARY KEY; `CHECK (country GLOB '[A-Z][A-Z]')` |
| `rate_bp` | INTEGER | NOT NULL; `CHECK (typeof(rate_bp) = 'integer' AND rate_bp BETWEEN 0 AND 10000)` |

El `typeof` es necesario porque SQLite tiene tipado flexible: sin él, una columna INTEGER aceptaría 21.5 como REAL.

Filas que inserta la migración (CA-4.3): ES 2100 · PT 2300 · FR 2000 · DE 1900 · IT 2200 · GB 2000 · US 0.

**Migración `0001_create_tax_rates`:**
- `upgrade`: crea la tabla con los dos CHECK e inserta las 7 filas en bloque.
- `downgrade`: borra la tabla.
- Una vez creada no se edita (AGENTS.md). `customers` y `simulations` llegarán en migraciones posteriores.

**Tramos:** no van en base de datos. Son una constante inmutable del dominio (§8.5 del 00):

```text
TIERS = (
  Tier(number=1, from_users=1,  to_users=10,   unit_price_cents=1000),
  Tier(number=2, from_users=11, to_users=50,   unit_price_cents=800),
  Tier(number=3, from_users=51, to_users=None, unit_price_cents=500),
)
MAX_USERS = 100_000
```

## 4. Interfaz pública del cálculo (pseudocódigo)

```text
# domain/errors.py
class PricingError(Exception)                       # base; sin mensajes para el usuario
class InvalidUsersError(PricingError)               # «usuarios no válidos»  (CA-3.3, CA-3.4)
class UnsupportedCountryError(PricingError): country: str   # «país no soportado» (CA-4.6)
class InvalidTaxRateError(PricingError)             # tasa fuera de 0..10000  (CA-13.1)

# domain/pricing.py — todas son dataclasses congeladas
TierLine(tier, from_users, to_users: int|None, units, unit_price_cents, amount_cents)
PriceQuote(users, currency="EUR", tiers: tuple[TierLine, TierLine, TierLine],
           subtotal_cents, tax_rate_bp, tax_cents, total_cents)

validate_users(users: int) -> int                      lanza InvalidUsersError
tier_breakdown(users: int) -> tuple[TierLine, ...]     # 3 líneas siempre
build_quote(users: int, rate_bp: int) -> PriceQuote    lanza InvalidUsersError, InvalidTaxRateError

# domain/tax.py
validate_rate_bp(rate_bp: int) -> int                  lanza InvalidTaxRateError
tax_cents(subtotal_cents: int, rate_bp: int) -> int

# services/pricing.py — lo que consumen 002 y simulaciones
protocol TaxRateSource: get_rate_bp(country: str) -> int | None
quote(users: int, country: str, rates: TaxRateSource) -> PriceQuote
      lanza InvalidUsersError, UnsupportedCountryError
set_tax_rate(country: str, rate_bp: int, repo: TaxRateRepository) -> None
      lanza InvalidTaxRateError
```

El dominio nunca recibe un país, solo la tasa: es el servicio quien la obtiene.

## 5. Algoritmos, solo con aritmética entera (RF-1, RF-3, RF-4, RF-6, RF-13)

```text
validate_users(users):
    if type(users) is not int: raise InvalidUsersError     # excluye bool (CA-3.4)
    if users < 0 or users > MAX_USERS: raise InvalidUsersError
    return users

tier_breakdown(users):
    for t in TIERS:
        upper = t.to_users if t.to_users is not None else users
        units = max(0, min(users, upper) - (t.from_users - 1))
        emit TierLine(t..., units, t.unit_price_cents, units * t.unit_price_cents)

tax_cents(subtotal, rate_bp):          # mitad hacia arriba, válido porque subtotal·rate ≥ 0
    return (subtotal * rate_bp + 5_000) // 10_000

build_quote(users, rate_bp):
    n = validate_users(users); r = validate_rate_bp(rate_bp)
    lines = tier_breakdown(n); subtotal = sum(l.amount_cents for l in lines)
    tax = tax_cents(subtotal, r)
    return PriceQuote(n, "EUR", lines, subtotal, r, tax, subtotal + tax)

quote(users, country, rates):
    n = validate_users(users)                  # 1.º usuarios: prioridad (CA-3.5)
    rate = rates.get_rate_bp(country)          # una sola lectura (CA-13.3); código exacto (CA-4.7)
    if rate is None: raise UnsupportedCountryError(country)
    return build_quote(n, rate)
```

**Ejemplo trabajado: 15 usuarios en ES**

1. `validate_users(15)` → 15.
2. `get_rate_bp("ES")` → 2100.
3. Tramo 1: `min(15, 10) − 0` = 10 unidades → 10 × 1000 = 10000.
4. Tramo 2: `min(15, 50) − 10` = 5 unidades → 5 × 800 = 4000.
5. Tramo 3: `min(15, 15) − 50` = −35 → 0 unidades → 0.
6. Subtotal = 10000 + 4000 + 0 = 14000.
7. Impuesto = (14000 × 2100 + 5000) // 10000 = 29 405 000 // 10000 = 2940.
8. Total = 14000 + 2940 = 16940. Coincide con la sección 5 de la spec.

Comprobación del redondeo en 0,5 (R-1): (1000 × 2105 + 5000) // 10000 = 2 110 000 // 10000 = 211.

## 6. Decisiones técnicas

**Decisiones ya cerradas, que no se reabren:** céntimos enteros y puntos básicos (ADR 0002), capas con dominio puro (ADR 0003), tasas en tabla (ADR 0006) y mypy (ADR 0008).

| # | Decisión | Por qué | Alternativa descartada | RF |
| --- | --- | --- | --- | --- |
| DT-1 | Redondeo `(s·r + 5000) // 10000` | Exacto y sin otro tipo numérico | `round()` de Python: redondea 210,5 a 210 (redondeo bancario) y falla R-1. `Decimal`: añade un tipo numérico innecesario | 6 |
| DT-2 | Tramos como tupla de dataclasses congeladas | Única fuente, inmutable y tipada | Tabla en base de datos: más complejidad sin requisito que la pida (§8.5 del 00) | 1, 2 |
| DT-3 | `quote` recibe la fuente de tasas como parámetro (`TaxRateSource`) | Tests sin acoplamiento; permite simular el fallo de O-5 en 002 | Importar el repositorio dentro del servicio | 4, 13 |
| DT-4 | La validación de usuarios vive en el dominio, con `type(x) is int` | Es regla de negocio y la reutiliza la spec de simulaciones; excluye `bool` | Confiar solo en la validación de 002 | 3 |
| DT-5 | CHECK en SQLite y además `validate_rate_bp` en el servicio | Defensa también ante escrituras directas y el tipado flexible de SQLite | Validar solo en código | 13 |
| DT-6 | Tasas por defecto en la migración 0001 | CA-4.3 sin depender del seed (decisión del usuario) | Insertarlas en el seed | 4 |
| DT-7 | Una migración por funcionalidad | No se editan migraciones creadas, y las otras tablas aún no tienen spec | Una migración inicial con las 4 tablas | 13 |
| DT-8 | Errores de dominio como excepciones propias sin texto para el usuario | 002 las traduce en un único punto (§6 del 00) | Devolver `None` o códigos | 3, 4 |
| DT-9 | `PriceQuote` con los mismos nombres de campo que el contrato | 002 la serializa sin renombrar nada; mypy la comprueba | Usar un `dict` o un modelo Pydantic dentro del dominio | 7 |
| DT-10 | Los tests D aplican la migración real sobre un SQLite temporal | Prueban los CHECK y las filas por defecto (C-6) | `create_all` de SQLAlchemy | 4, 13 |

## 7. Estrategia de tests (tests primero)

**Cómo se derivan:**
- Cada tabla de la spec se copia como parámetros de pytest, y el identificador de cada caso es el de la fila (`P-4`, `R-7`…).
- El nombre o docstring de cada test cita los CA que cubre.
- Los límites tienen fila propia: 0 (P-1, T-1), 10/11 (P-3, P-4), 50/51 (P-6, P-7), 100 000 (P-10, R-7) y 100 001 (X-2).

**Orden de escritura.** Cada paso empieza en rojo; se confirma que el test falla antes de escribir el código.

1. **U, cálculo** (`tests/unit/`):
   - P-1 a P-10, con los invariantes CA-2.1 a CA-2.4 en cada fila.
   - T-1 a T-10, pasando la tasa de la columna.
   - R-1 a R-9 sobre `tax_cents` y sobre `build_quote`.
   - X-1 a X-3.
   - El ejemplo de la sección 5 de la spec, campo a campo.
2. **Arquitectura** (U): ningún archivo de `app/domain/` importa `sqlalchemy`, `fastapi`, `pydantic` ni `app.repositories` o `app.db`.
3. **D, migración** (`tests/integration/`): C-6 (exactamente 7 filas), y una inserción directa con 10001, −1, 21.5 o «es» falla por los CHECK.
4. **D, servicio** (`tests/integration/`):
   - P-1 a P-10 y T-1 a T-10 a través de `quote`.
   - R-1 a R-9 con la tasa de ES configurada vía `set_tax_rate`.
   - C-1 a C-5, más un espía sobre el repositorio que cuenta exactamente 1 lectura por cotización (CA-13.3).
   - X-1, X-2 y X-4 a X-7.

**Fixture D:** un SQLite en `tmp_path` por test, con `alembic upgrade head` ejecutado por código y una sesión aislada.

**Ejecución:** `pytest`, `ruff check .`, `ruff format --check .` y `mypy .` en modo estricto. Todo en verde antes de cada commit.

## 8. Trazabilidad

| RF | Parte del plan | Tests |
| --- | --- | --- |
| RF-1 | §3 `TIERS`, §5 `tier_breakdown` | P-1 a P-10 (U+D), T-1 a T-10 |
| RF-2 | §4 `TierLine`, §5 | P-1 a P-10 (invariantes), ejemplo de la sección 5 de la spec |
| RF-3 | §5 `validate_users`; orden en `quote` | P-1, P-10, X-1, X-2, X-3, X-7 |
| RF-4 | §3 tabla y migración; §5 `quote` | T-1 a T-10 (D), C-4, C-6, X-4, X-5, X-6 |
| RF-5 | — | **No cubierto: movido a 002 RF-3** |
| RF-6 | §5 `tax_cents` | R-1 a R-9 (U+D), T-1 a T-10 |
| RF-7 | §4 `PriceQuote` | Ejemplo de la sección 5 de la spec; tipos `int` comprobados por mypy |
| RF-8 a RF-12 | — | **No cubiertos: movidos a 002 RF-1 y RF-5 a RF-8** |
| RF-13 | §3 CHECK; §4 `set_tax_rate`; §5 una sola lectura | C-1 a C-5, tests de los CHECK, espía de lecturas |

Todos los RF vigentes de la v1.2 quedan cubiertos.

## 9. Cumplimiento de la constitución

1. **Simplicidad:** sin dependencias fuera del stack aprobado; FastAPI se añade con 002.
2. **La spec manda:** cada commit citará el RF o CA, y la tabla de la sección 8 enlaza RF, plan y tests.
3. **Capas:** el dominio es Python puro, el acceso a SQLite solo está en `repositories/` y el test de arquitectura lo vigila.
4. **Dinero:** solo `int` (céntimos y puntos básicos), redondeo explícito (DT-1) y esquema por migración de Alembic.
5. **Tests y revisión:** tests primero, en U y D, derivados de las tablas; la suite pasa antes de cada commit y cada corrección de la IA se anota en `ai-review-log.md`.
6. **Calidad e idioma:** ruff y mypy en modo estricto; los identificadores en inglés; los errores de dominio no llevan texto para el usuario (los mensajes en español son de 002).

## 10. Dudas abiertas

No quedan dudas abiertas. Las dos que había se aceptaron tal como se propusieron al aprobar el plan:

- **Carpeta de los tests D:** `tests/integration/`, para los tests con base de datos sin HTTP. El §5 del 00 solo preveía `tests/` para «unit (domain) y api».
- **Archivos de configuración:** `pyproject.toml` (configuración de ruff, mypy y pytest) y `requirements-dev.txt` (pytest, ruff y mypy), que incluye `requirements.txt` (SQLAlchemy y Alembic).
