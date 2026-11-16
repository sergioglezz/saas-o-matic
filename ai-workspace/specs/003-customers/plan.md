# Plan técnico — 003 Clientes

Estado: v1.0, redactado y ejecutado por delegación del autor, revisado y aprobado por el autor · Spec: `spec.md` v1.0 · Constitución: `ai-workspace/docs/constitution.md` · Arquitectura: §5, §7.4 y §8 de `00-spec-first.md` · Base: specs y código de 001 y 002

Los comportamientos de FastAPI, Starlette, Pydantic y SQLite en los que se apoya este plan se comprobaron antes de escribirlo, con un prototipo desechable fuera del repositorio. La sección 10 recoge lo que reveló.

## 1. Resumen y alcance

- **Construye:**
  - El validador puro del identificador fiscal (`domain/tax_id.py`).
  - La tabla `customers` con su migración, su repositorio y su servicio.
  - `POST /customers`, `GET /customers` y `GET /customers/{id}`.
  - El formato único de error para todo lo que genera el framework, y la cabecera `Allow` completa.
  - El script de datos de demostración (`python -m app.db.seed`).
- **Cubre:** RF-1 a RF-10 y RNF-1 a RNF-6.
- **Fuera:** simulaciones, edición o borrado de clientes y el frontend. No cambian el cálculo de 001 ni el contrato de la cotización de 002.
- **Dependencias:** ninguna nueva. El email se valida con una expresión regular propia (spec D-1).
- **ADR:** 0009 (control del identificador fiscal).

## 2. Estructura de módulos

| Módulo | Responsabilidad | Puede importar | RF |
| --- | --- | --- | --- |
| `app/domain/tax_id.py` (nuevo) | `normalize_tax_id` y `validate_tax_id(value, country)`: formato básico y control de DNI, NIE y CIF | Biblioteca estándar y `domain.errors` | 3 |
| `app/domain/customers.py` (nuevo) | `PLANS` y los tipos congelados `NewCustomer`, `Customer` y `CustomerPage` | Biblioteca estándar | 1, 5 |
| `app/domain/errors.py` (ampliado) | `CustomerError` y sus subclases, sin texto para el usuario | Biblioteca estándar | 3, 4, 6 |
| `app/services/customers.py` (nuevo) | `register_customer`, `search_customers` y `get_customer`; el protocolo `CustomerStore` | `domain.*`, `services.pricing` y `core.clock` | 1, 3, 4, 5, 6 |
| `app/repositories/customers.py` (nuevo) | `CustomerRepository`: `add`, `get` y `search` sobre `customers` | `db.*`, `domain.*` y SQLAlchemy | 4, 5, 9 |
| `app/db/models.py` (ampliado) | Modelo `CustomerRecord` | SQLAlchemy y `domain.customers` (solo `PLANS`) | 9 |
| `app/db/session.py` (ampliado) | Registra la función SQL `casefold` en cada conexión | SQLAlchemy y `sqlite3` | 5 |
| `app/db/migrations/versions/0002_create_customers.py` (nuevo) | Crea `customers` con sus restricciones y su índice | Alembic y SQLAlchemy | 9 |
| `app/db/seed.py` (nuevo) | Clientes de demostración y `main()` | `schemas`, `services`, `repositories` y `db` | 10 |
| `app/schemas/customers.py` (nuevo) | `CustomerCreate`, `CustomerListQuery`, `CustomerResponse`, `CustomerListResponse`, los mensajes y los ejemplos | `pydantic`, `domain.*` y `schemas.pricing` (país) | 1, 2, 3, 5 |
| `app/api/customers.py` (nuevo) | Los tres endpoints: leen, validan, llaman al servicio y responden | `schemas`, `services`, `api.*` y `core.errors` | 1, 2, 5, 6 |
| `app/api/customers_docs.py` (nuevo, añadido en T-17) | Ejemplos y errores documentados de las tres rutas, y la limpieza del 422 propio del framework en `/openapi.json`. Separado para que el router siga siendo corto | `schemas.customers` y `core.errors` | RNF-4 |
| `app/api/countries.py` (nuevo) | `unsupported_country_detail`: añade «País no soportado» cuando hay otros errores. Lo usan la cotización y el alta | `schemas.pricing`, `services.pricing` y `core.errors` | 2 |
| `app/api/error_mapping.py` (nuevo) | El único punto donde un error de dominio se convierte en respuesta HTTP | `domain.errors`, `schemas.*`, `api.validation` y `core.errors` | 4, 6, 7 |
| `app/api/validation.py` (ampliado) | `field_errors` respeta el mensaje de un validador que lanza `InvalidFieldError` | Como en 002 | 2, 3 |
| `app/api/dependencies.py` (ampliado) | `get_customer_store` y `get_now` | `db`, `repositories`, `services` y `core.clock` | 1 |
| `app/core/errors.py` (cambiado) | Formato único: `ApiError`, 404, 405 con `Allow` completa, 409, errores de validación y HTTP del framework, 500, y `InvalidFieldError` para los validadores con mensaje propio. Ya no conoce ninguna funcionalidad | `fastapi` y `starlette` | 7 |
| `app/core/clock.py` (nuevo) | `utc_now()` y `to_timestamp(datetime) -> str` | Biblioteca estándar | 1 |
| `app/main.py` (ampliado) | Incluye el router de clientes, registra el mapeo de errores y permite `GET` en CORS | `api`, `core` y `db` | 7, 8 |

Las dependencias siguen `api → services → (domain, repositories)`. Dos notas:

- `core/errors.py` deja de importar `schemas` y `domain` (entrada 16 del log). El mapeo de errores de dominio pasa a `api/error_mapping.py`, que sigue siendo un único punto (§6 del 00). Un test de arquitectura nuevo vigila que `app/core/` no importe ninguna otra capa.
- `db/seed.py` es un script de entrada, como `main.py`: por eso puede importar capas superiores aunque esté en `db/`, que es donde lo sitúan el §5 del 00 y el comando de `AGENTS.md`.

## 3. Modelo de datos (RF-9)

Tabla `customers` (§8.5 del 00), creada por la migración `0002_create_customers`:

| Columna | Tipo | Restricciones |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT (no reutiliza identificadores) |
| `company_name` | TEXT | NOT NULL; `CHECK (length(company_name) BETWEEN 1 AND 120)`; índice `ix_customers_company_name` |
| `tax_id` | TEXT | NOT NULL; UNIQUE (`uq_customers_tax_id`) |
| `contact_email` | TEXT | NOT NULL |
| `country` | TEXT | NOT NULL; `CHECK (country GLOB '[A-Z][A-Z]')` |
| `plan` | TEXT | NOT NULL; `CHECK (plan IN ('starter', 'business', 'enterprise'))` |
| `created_at` | TEXT | NOT NULL; ISO 8601 UTC, `AAAA-MM-DDTHH:MM:SSZ` |

- `upgrade` crea la tabla y el índice; `downgrade` los borra. La migración 0001 no se toca.
- Sin clave foránea de `country` a `tax_rates` (spec D-7).
- El texto `AAAA-MM-DDTHH:MM:SSZ` se ordena igual que el tiempo, lo que servirá al historial de simulaciones.

## 4. Interfaz pública

**HTTP:** el contrato de la sección 5 de la spec, sin añadidos.

**Interna** (pseudocódigo):

```text
# domain/errors.py
class CustomerError(Exception)
class InvalidTaxIdFormatError(CustomerError)       # formato básico            (CA-3.2)
class InvalidSpanishTaxIdError(CustomerError)      # control español           (CA-3.3)
class UnsupportedTaxIdTypeError(CustomerError)     # NIF K, L y M              (CA-3.7)
class DuplicateTaxIdError(CustomerError)           # identificador ya usado    (CA-4.1)
class CustomerNotFoundError(CustomerError)         # cliente inexistente       (CA-6.2)

# domain/tax_id.py
normalize_tax_id(value: str) -> str
validate_tax_id(value: str, country: str | None) -> str     # devuelve el normalizado
      lanza InvalidTaxIdFormatError, InvalidSpanishTaxIdError, UnsupportedTaxIdTypeError

# domain/customers.py
PLANS = ("starter", "business", "enterprise")
NewCustomer(company_name, tax_id, contact_email, country, plan)
Customer(id, company_name, tax_id, contact_email, country, plan, created_at: str)
CustomerPage(items: tuple[Customer, ...], total: int)

# services/customers.py
protocol CustomerStore:
    add(new: NewCustomer, created_at: str) -> Customer      lanza DuplicateTaxIdError
    get(customer_id: int) -> Customer | None
    search(name_fragment: str, tax_id_fragment: str, limit: int, offset: int) -> CustomerPage
register_customer(new, customers: CustomerStore, rates: TaxRateSource, now: datetime) -> Customer
search_customers(q: str, limit: int, offset: int, customers: CustomerStore) -> CustomerPage
get_customer(customer_id: int, customers: CustomerStore) -> Customer    lanza CustomerNotFoundError

# core/errors.py
ApiError, FieldError, error_response                        # sin cambios
not_found() -> ApiError
conflict(details) -> ApiError
register_error_handlers(app):
    ApiError                   -> su estado y su cuerpo
    RequestValidationError     -> 422, un detalle «Valor no válido» por parámetro    (CA-7.3)
    StarletteHTTPException 404 -> 404 not_found
    StarletteHTTPException 405 -> 405 con Allow calculada sobre todas las rutas      (CA-7.2)
    StarletteHTTPException *   -> ese estado, http_error «Error en la petición»      (CA-7.4)
    Exception                  -> 500 internal_error

# api/error_mapping.py
register_domain_error_handlers(app)     # la tabla única error de dominio -> ApiError
```

## 5. Algoritmos

**Identificador fiscal (RF-3):**

```text
normalize_tax_id(value):
    quitar " ", "\t", "\n", "\r", "-" y "." en cualquier posición; a-z -> A-Z (solo ASCII)

validate_tax_id(value, country):
    tax_id = normalize_tax_id(value)
    si no cumple ^[A-Z0-9]{5,20}$: raise InvalidTaxIdFormatError          # CA-3.2
    si country != "ES": return tax_id                                     # CA-3.8, CA-3.9
    si tax_id[0] en "KLM": raise UnsupportedTaxIdTypeError                # CA-3.7
    si es DNI, NIE o CIF válido: return tax_id
    raise InvalidSpanishTaxIdError                                        # CA-3.3

DNI: ^\d{8}[A-Z]$   y letra == TABLA[int(dígitos) % 23]
NIE: ^[XYZ]\d{7}[A-Z]$   -> sustituir X/Y/Z por 0/1/2 y aplicar el DNI
CIF: ^[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]$
     a = suma de los dígitos 2.º, 4.º y 6.º
     b = suma de las cifras del doble de los dígitos 1.º, 3.º, 5.º y 7.º
     d = (10 - (a + b) % 10) % 10 ;  letra = "JABCDEFGHI"[d]
     entidad en "NPQRSW": control == letra
     entidad en "ABEH":   control == str(d)
     resto:               control en (str(d), letra)
```

Ejemplo trabajado, `B12345674`: a = 2 + 4 + 6 = 12; b = 2 + 6 + (1 + 0) + (1 + 4) = 14; d = (10 − 26 mod 10) mod 10 = 4. La entidad `B` exige dígito, y el control es `4`: válido. Para `N1234567D`, la letra es `JABCDEFGHI`[4] = `D`: válido.

**Alta (RF-1 a RF-4):**

```text
POST /customers (payload, customers, rates, now):
    try: request = CustomerCreate.model_validate(payload)        # estricto, extra="forbid"
    except ValidationError:
        details = field_errors(error, mensajes de formato)
        details += unsupported_country_detail(payload, details, rates)     # VA-26, VA-27
        raise 422
    return 201, register_customer(request.to_new_customer(), customers, rates, now)

CustomerCreate valida cada campo (el país se declara antes que tax_id):
    company_name: " ".join(value.split()); 1..120 e imprimible
    contact_email: strip(" \t\n\r"); <= 254 y expresión regular de CA-2.2
    country: normalize_country (002)
    plan: uno de PLANS
    tax_id: validate_tax_id(value, país ya validado o None)
            los errores español y K/L/M llevan su mensaje (InvalidFieldError); el básico, el de formato

register_customer(new, customers, rates, now):
    si el país no tiene tasa: raise UnsupportedCountryError       # VA-17
    tax_id = validate_tax_id(new.tax_id, new.country)             # el servicio no se fía del borde
    return customers.add(new con tax_id, to_timestamp(now))       # DuplicateTaxIdError -> 409
```

**Unicidad (RF-4):** no hay consulta previa. `CustomerRepository.add` guarda y confirma; si SQLite rechaza la fila por la restricción única de `tax_id`, deshace la transacción y lanza `DuplicateTaxIdError`. Así la regla tiene un único dueño, la base de datos, y no hay carrera entre dos altas (CA-4.4).

**Búsqueda (RF-5):**

```text
search_customers(q, limit, offset, customers):
    text = " ".join(q.split())
    return customers.search(text.casefold(), normalize_tax_id(text), limit, offset)

CustomerRepository.search(name_fragment, tax_id_fragment, limit, offset):
    condiciones = []
    si name_fragment:   instr(casefold(company_name), :name_fragment) > 0
    si tax_id_fragment: instr(tax_id, :tax_id_fragment) > 0
    filtro = OR de las condiciones, o ninguno si no hay
    total = COUNT con el filtro
    items = SELECT con el filtro ORDER BY casefold(company_name), id LIMIT :limit OFFSET :offset
```

`instr` busca un fragmento literal, así que `%` y `_` no son comodines (CA-5.4), y todos los valores viajan como parámetros.

**Parámetros del listado (CA-5.8 a CA-5.10):** la ruta los declara como textos opcionales, de modo que el framework nunca los rechaza y aparecen en `/docs`. `CustomerListQuery` los valida: `limit` y `offset` deben cumplir `^[0-9]+$` (solo dígitos ASCII) y estar en rango.

**Identificador de ruta (CA-6.3):** se declara como texto; si no cumple `^[1-9][0-9]{0,18}$` o supera 2⁶³ − 1, responde 404 sin consultar la base de datos.

**Cabecera `Allow` (CA-7.2):** en un 405 se recorren las rutas de la aplicación y se unen los métodos de todas las que coinciden con la dirección pedida.

## 6. Decisiones técnicas

**Decisiones cerradas que se citan:** capas (ADR 0003), cuerpo leído a mano y Pydantic estricto (plan 002 DT-1 y DT-2), una migración por funcionalidad (plan 001 DT-7), control del identificador (ADR 0009).

| # | Decisión | Por qué | Alternativa descartada | RF |
| --- | --- | --- | --- | --- |
| DT-1 | El control español se invoca desde el validador de `tax_id` del esquema, con el país ya validado (`info.data`) | Comprobado: el validador ve el país validado aunque llegue después en el JSON, y no lo ve si falló. Así se informa de todos los campos a la vez (VA-25) | Validar el identificador solo en el servicio: se pararía en el primer error | 2, 3 |
| DT-2 | El servicio vuelve a validar país e identificador | El dominio no depende del borde: el seed y cualquier llamada futura pasan por las mismas reglas (plan 001 DT-4) | Confiar en el esquema | 3, 10 |
| DT-3 | Un validador que necesita otro texto lanza `InvalidFieldError` (un `ValueError` propio con su mensaje), y `field_errors` lo respeta | Un campo puede fallar por tres motivos con tres textos (TID, ESP, KLM). No cambia nada para la cotización. Corregida al implementar T-11: la primera versión usaba `PydanticCustomError`, que obligaba a importar `pydantic_core`, un paquete que `requirements.txt` no declara (entrada 18 del log) | Un mensaje por campo, como en 002 | 3 |
| DT-4 | La unicidad la decide la restricción UNIQUE; `add` traduce el error de SQLite | Un solo dueño de la regla y sin carrera. Comprobado: el texto del error es `UNIQUE constraint failed: customers.tax_id` | Consultar antes de insertar | 4 |
| DT-5 | `CustomerRepository.add` confirma la transacción | El alta es una única escritura; confirmar en el router rompería las capas, y hacerlo al cerrar la dependencia llegaría tarde para informar de un 409 | Confirmar en la dependencia de sesión | 1, 4 |
| DT-6 | Función SQL `casefold`, registrada en cada conexión junto al `PRAGMA` | Comprobado: `lower()` de SQLite deja `Ñ` y `Í` como están; con `str.casefold` la búsqueda y el orden ignoran mayúsculas en cualquier letra | `LIKE`, que además obliga a escapar comodines | 5 |
| DT-7 | `limit`, `offset` e `{id}` declarados como texto y validados por código propio | Comprobado: tipados como enteros, el framework responde con su propio formato y acepta `+5` o espacios. Además evita depender de cómo clasifica cada versión esos errores | Tiparlos como `int` | 5, 6 |
| DT-8 | Manejadores globales para `RequestValidationError` y para cualquier estado HTTP | Red de seguridad: si una ruta futura tipa un parámetro, el formato único se mantiene (entrada 16 del log) | Dejar el formato por defecto | 7 |
| DT-9 | `Allow` calculada sobre todas las rutas que coinciden | Comprobado: con `GET` y `POST` en `/customers`, Starlette responde `Allow: GET` | Aceptar la cabecera incompleta | 7 |
| DT-10 | Reloj inyectable (`get_now`) | AL-1 compara la respuesta exacta, con `created_at` incluido | Comparar con una expresión regular | 1 |
| DT-11 | `created_at` como texto en el dominio y en la base de datos | El 00 pide fechas en texto ISO 8601 UTC; un único formato, sin conversiones al leer | `datetime` con zona en el modelo | 1 |
| DT-12 | `CORSMiddleware` permite también `GET` | Comprobado: una preflight de `GET` con solo `POST` permitido responde 400 | Dejar solo `POST` | 8 |
| DT-13 | El seed llama al esquema y al servicio, y salta los duplicados | Mismas reglas que la API (CA-10.3) e idempotencia sin lógica propia (CA-10.2) | Insertar filas directamente | 10 |
| DT-14 | Mensajes de dominio de la cotización: siguen en `schemas/pricing.py`; el mapeo se muda a `api/error_mapping.py` | `core` vuelve a ser genérico sin mover ni tocar ningún test de 002 | Dejar el mapeo en `core` | 7 |

## 7. Estrategia de tests (tests primero)

**Niveles y archivos:**

- **U** (`tests/unit/`): `test_tax_id.py` (tablas 6.1 y 6.2), `test_customer_schema.py` (campos, parámetros del listado y errores `api.*`), `test_clock.py` y `test_core_architecture.py`. El test de arquitectura de 001 ya cubre los módulos nuevos de `app/domain/`.
- **D** (`tests/integration/`): `test_customers_migration.py` (DB-1, DB-3 a DB-6, DB-8, DB-9), `test_customer_repository.py` (DB-2, DB-7 y la búsqueda), `test_customer_service.py` y `test_seed.py` (SE-1 a SE-5).
- **I** (`tests/api/`): `test_customers_create.py` (AL, VA, CO), `test_customers_list.py` (LI, LP), `test_customers_detail.py` (FI), `test_customers_protocol.py` (ER-1 a ER-5 y ER-8 a ER-12), `test_error_format_global.py` (ER-6, ER-7 y el 409) y `test_customers_docs.py`.

**Derivación:** cada tabla de la sección 6 se copia como parámetros de pytest con el identificador del caso; el docstring de cada test cita «spec 003» en el archivo y los CA que cubre. `details` se compara como conjunto.

**Fixtures:** las de 001 y 002 (`database_url`, `migrated_engine`, `session`, `app`, `client`). Las de clientes fijan el reloj en `2026-11-13T10:00:00Z` con `dependency_overrides[get_now]`.

**Regla para los tests anteriores:** no se modifica ninguno. Los 383 de 001 y 002 deben seguir pasando en cada tarea.

**Orden** (cada paso empieza en rojo):

1. Errores globales, con rutas de prueba: arquitectura de `core`, errores del framework, 409 y `Allow`.
2. Dominio: normalización y formato básico; DNI y NIE; CIF y K/L/M.
3. Persistencia: migración y modelo; repositorio; servicio.
4. API: esquemas; alta válida; errores y conflictos; listado; ficha; protocolo y CORS; documentación.
5. Seed.
6. Arranque real y comprobación final.

## 8. Trazabilidad

| RF | Parte del plan | Casos |
| --- | --- | --- |
| RF-1 | §5 alta, DT-5, DT-10, DT-11 | AL-1 a AL-9 |
| RF-2 | §5 `CustomerCreate`, DT-1 | VA-1 a VA-28 |
| RF-3 | §5 identificador, DT-1 a DT-3, ADR 0009 | TI-1 a TI-27, TG-1 a TG-12, VA-7 a VA-11 |
| RF-4 | §5 unicidad, DT-4 | CO-1 a CO-5, DB-2 |
| RF-5 | §5 búsqueda y parámetros, DT-6, DT-7 | LI-1 a LI-20, LP-1 a LP-15 |
| RF-6 | §5 identificador de ruta, DT-7 | FI-1 a FI-9 |
| RF-7 | §4 `register_error_handlers`, DT-8, DT-9, DT-14 | ER-1 a ER-7, ER-11, ER-12 |
| RF-8 | DT-12 | ER-8 a ER-10 |
| RF-9 | §3 | DB-1 a DB-9 |
| RF-10 | DT-13 | SE-1 a SE-5 |

Los RNF: RNF-1, test de arquitectura y tablas 6.1 y 6.2 sin base de datos; RNF-2, LI-8, LI-9, LI-14, ER-5 y ER-7; RNF-3, los textos viven en `schemas/` y `core/errors.py`; RNF-4, `test_customers_docs.py`; RNF-5, datos del seed; RNF-6, `requirements.txt` no cambia.

## 9. Cumplimiento de la constitución

1. **Simplicidad:** ninguna dependencia nueva; nada fuera de la spec.
2. **La spec manda:** cada commit cita el RF o CA de 003.
3. **Capas:** el identificador fiscal es Python puro; el SQL vive solo en el repositorio; los routers validan y traducen; `core` no conoce funcionalidades.
4. **Dinero y esquema:** esta spec no maneja importes; el esquema cambia con la migración 0002.
5. **Tests y revisión:** tests primero en U, D e I; la suite completa pasa en cada commit; las correcciones se anotan en el log.
6. **Calidad, seguridad e idioma:** ruff y mypy estrictos; toda entrada validada con Pydantic; consultas por ORM; textos al usuario en español.

## 10. Lo que reveló el prototipo

| Comprobación | Resultado | Consecuencia |
| --- | --- | --- |
| 405 en una dirección con `GET` y `POST` | Starlette responde `Allow: GET`: solo la primera ruta | DT-9 |
| Parámetro de query repetido | FastAPI se queda con el último valor | CA-5.10 sin código propio |
| Parámetros tipados como `int` con texto | 422 con el formato propio de FastAPI | DT-7 y DT-8 |
| Error HTTP con otro estado (418) | Sale con `{"detail": ...}` | DT-8 |
| `GET` con `Origin` y solo `POST` permitido en CORS | Lleva `Access-Control-Allow-Origin`, pero su preflight responde 400 | DT-12 |
| Validador de campo con `info.data` | Ve el país validado sea cual sea el orden del JSON; no lo ve si el país falló | DT-1 |
| `PydanticCustomError` | Conserva el tipo y el mensaje propios en `errors()`, pero se importa de `pydantic_core`. Un `ValueError` propio llega igual, en `ctx["error"]` | DT-3 |
| `lower()` de SQLite con `COMPAÑÍA` | Devuelve `compaÑÍa` | DT-6 |
| Función `casefold` registrada en la conexión, con `instr` | Encuentra `compañía ñ`; `%` y `_` son literales; el orden ignora mayúsculas | DT-6 |
| Duplicar `tax_id` | `IntegrityError` con `UNIQUE constraint failed: customers.tax_id` | DT-4 |
| `AUTOINCREMENT` tras borrar el último | No reutiliza el identificador | CA-1.3, DB-7 |
| `OFFSET` enorme | `OverflowError` | Límite de `offset` (spec D-9) |
| Caracteres de control de §7.4 | Los 14 casos coinciden con el cálculo | Tabla 6.1 |

No quedan dudas abiertas. Las decisiones que el autor aún no ha confirmado están en la sección 11 de la spec.
