# Plan técnico — 004 Simulaciones

Estado: v1.0 aprobado por el autor · Spec: `spec.md` v1.0 (aprobada) · Constitución: `ai-workspace/docs/constitution.md` · Arquitectura: §5, §7.3 y §8 de `00-spec-first.md` · Base: specs y código de 001, 002 y 003

Antes de escribir este plan se comprobaron con un prototipo desechable, fuera del repositorio, los comportamientos de Pydantic, SQLAlchemy, SQLite y FastAPI en los que se apoya. Se montaron las piezas igual que la aplicación real (entrada 17 del log). La sección 10 recoge lo que salió.

## 1. Resumen y alcance

- **Construye:**
  - Los tipos y la validación pura de una simulación (`domain/simulations.py`).
  - Las tablas `simulations` y `simulation_tiers` con su migración, su repositorio y su servicio.
  - `POST /simulations` y `GET /customers/{id}/simulations`.
  - Las simulaciones de demostración en `python -m app.db.seed`.
- **Cubre:** RF-1 a RF-8 y RNF-1 a RNF-6 de la spec. La sección 8 indica qué parte del plan cubre cada RF y cada CA.
- **Reutiliza sin cambiar su comportamiento:** el cálculo y el servicio de cotización de 001, la lectura del cuerpo y los errores de 002, y el cliente, la paginación, el formato de error, la cabecera `Allow` y CORS de 003.
- **Fuera:** el frontend, editar o borrar simulaciones y que el almacenamiento o las llamadas cambien el precio (spec, sección 9).
- **Dependencias:** ninguna nueva. **ADR:** ninguno nuevo; la ampliación de §8.5 (límites del tramo) está decidida en la spec (D-3).

## 2. Estructura de módulos

| Módulo | Responsabilidad | Puede importar | RF |
| --- | --- | --- | --- |
| `app/domain/simulations.py` (nuevo) | `MAX_STORAGE_GB`, `MAX_API_CALLS_PER_MONTH`, los tipos congelados `NewSimulation`, `Simulation` y `SimulationPage`, y `validate_usage` | Biblioteca estándar, `domain.pricing` (`TierLine`) y `domain.errors` | 1, 2, 4, 5 |
| `app/domain/errors.py` (ampliado) | `SimulationError` y sus subclases `InvalidStorageError`, `InvalidApiCallsError` y `UnsupportedCustomerCountryError`, sin texto para el usuario | Biblioteca estándar | 2, 3 |
| `app/services/simulations.py` (nuevo) | `save_simulation` y `list_simulations`; el protocolo `SimulationStore` | `domain.*`, `services.pricing`, `services.customers` y `core.clock` | 1, 3, 4, 5 |
| `app/repositories/simulations.py` (nuevo) | `SimulationRepository`: `add` (una sola transacción) y `list_for_customer` | `db.*`, `domain.*` y SQLAlchemy | 1, 4, 5, 7 |
| `app/repositories/customers.py` (ampliado) | `find_by_tax_id`, solo para el seed | Como en 003 | 8 |
| `app/db/models.py` (ampliado) | `SimulationRecord` y `SimulationTierRecord`, con la relación entre ambos | SQLAlchemy y las constantes de `domain` | 7 |
| `app/db/migrations/versions/0003_create_simulations.py` (nuevo) | Crea las dos tablas, sus restricciones y el índice del historial | Alembic y SQLAlchemy | 7 |
| `app/db/seed.py` (ampliado) | `DEMO_SIMULATIONS`, `seed_simulations` y una segunda línea en `main()` | `schemas`, `services`, `repositories` y `db` | 8 |
| `app/schemas/pagination.py` (nuevo) | `PageQuery` (`limit`, `offset`), sus mensajes y sus límites, sacados de `CustomerListQuery` | `pydantic` | 5 |
| `app/schemas/customers.py` (cambiado) | `CustomerListQuery` hereda de `PageQuery` y añade `q`. Los nombres que ya importan los tests de 003 siguen disponibles aquí | Como en 003 y `schemas.pagination` | 5 |
| `app/schemas/simulations.py` (nuevo) | `SimulationCreate`, `SimulationResponse`, `SimulationListResponse`, los mensajes y los ejemplos | `pydantic`, `domain.*` y `schemas.pricing` (`TierLineResponse`) | 1, 2, 4, 5 |
| `app/api/identifiers.py` (nuevo) | `parse_customer_id(text) -> int`: el 404 de un `{id}` mal formado, sacado de `api/customers.py` | `core.errors` | 5 |
| `app/api/customers.py` (cambiado) | Usa `parse_customer_id`; mismo comportamiento | Como en 003 | 5 |
| `app/api/simulations.py` (nuevo) | Las dos rutas: leen, validan, llaman al servicio y responden | `schemas`, `services`, `api.*` y `core.errors` | 1, 2, 3, 5, 6 |
| `app/api/simulations_docs.py` (nuevo) | Ejemplos y errores documentados de las dos rutas, y `restore_simulation_examples` para el `"to_users": null` | `schemas.simulations` y `core.errors` | RNF-5 |
| `app/api/error_mapping.py` (ampliado) | Las tres entradas nuevas de la tabla error de dominio → respuesta | Como en 003 y `schemas.simulations` | 2, 3 |
| `app/api/dependencies.py` (ampliado) | `get_simulation_store` | Como en 003 | 1, 5 |
| `app/main.py` (ampliado) | Incluye el router de simulaciones y encadena `restore_simulation_examples` en `/openapi.json` | `api`, `core` y `db` | 6, RNF-5 |

Las dependencias siguen `api → services → (domain, repositories)`. Notas:

- `services/simulations.py` usa `quote` de `services/pricing.py` y `get_customer` de `services/customers.py`: el cálculo y la búsqueda del cliente tienen un único dueño (RNF-2).
- `app/core/errors.py` y CORS **no cambian**: el prototipo confirmó que la `Allow` calculada en 003 y la preflight de `GET` y `POST` ya valen para las rutas nuevas (sección 10).
- Los dos cambios en código de 003 (`identifiers.py` y `pagination.py`) solo mueven código. Los 744 tests de 001 a 003 deben pasar sin tocarlos.

## 3. Modelo de datos (RF-7)

Migración `0003_create_simulations`, que depende de `0002`. Las restricciones van con nombre para que `compare_metadata` las compare.

**`simulations`**

| Columna | Tipo | Restricciones | CA |
| --- | --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 1.2 |
| `customer_id` | INTEGER | NOT NULL; FK `fk_simulations_customer_id` → `customers.id`, sin `ON DELETE` (rechaza borrar el cliente) | 7.2, 7.3 |
| `active_users` | INTEGER | NOT NULL; `typeof = 'integer' AND BETWEEN 0 AND 100000` | 7.2 |
| `storage_gb` | INTEGER | NOT NULL; `typeof = 'integer' AND BETWEEN 0 AND 1000000` | 7.2 |
| `api_calls_per_month` | INTEGER | NOT NULL; `typeof = 'integer' AND BETWEEN 0 AND 1000000000` | 7.2 |
| `subtotal_cents` | INTEGER | NOT NULL; `typeof = 'integer' AND >= 0` | 7.2 |
| `tax_rate_bp` | INTEGER | NOT NULL; `typeof = 'integer' AND BETWEEN 0 AND 10000` | 7.2 |
| `tax_cents` | INTEGER | NOT NULL; `typeof = 'integer' AND >= 0` | 7.2 |
| `total_cents` | INTEGER | NOT NULL; `typeof = 'integer' AND total_cents = subtotal_cents + tax_cents` | 7.2 |
| `created_at` | TEXT | NOT NULL; `AAAA-MM-DDTHH:MM:SSZ` | 1.2 |

Índice `ix_simulations_customer_id_created_at` sobre (`customer_id`, `created_at`) (CA-7.5).

**`simulation_tiers`**

| Columna | Tipo | Restricciones | CA |
| --- | --- | --- | --- |
| `simulation_id` | INTEGER | NOT NULL; FK `fk_simulation_tiers_simulation_id` → `simulations.id` | 7.2 |
| `tier` | INTEGER | NOT NULL; `BETWEEN 1 AND 3` | 7.2 |
| `from_users` | INTEGER | NOT NULL; `typeof = 'integer' AND >= 1` (spec D-3) | 4.2 |
| `to_users` | INTEGER | Admite nulo (el tramo abierto); si no es nulo, `typeof = 'integer'` (spec D-3) | 4.2, 4.7 |
| `units` | INTEGER | NOT NULL; `typeof = 'integer' AND >= 0` | 7.2 |
| `unit_price_cents` | INTEGER | NOT NULL; `typeof = 'integer' AND >= 0` | 7.2 |
| `amount_cents` | INTEGER | NOT NULL; `typeof = 'integer' AND >= 0` | 7.2 |

Clave primaria (`simulation_id`, `tier`): impide dos filas del mismo tramo (CA-7.2).

- `upgrade` crea las tablas y el índice; `downgrade` borra primero `simulation_tiers` y luego `simulations`. Las migraciones 0001 y 0002 no se tocan (CA-7.1, CA-7.4).
- La migración escribe los límites como números, porque una migración queda congelada; los modelos importan las constantes del dominio (plan 003, misma regla con `PLANS`).

## 4. Interfaz pública

**HTTP:** el contrato de la sección 5 de la spec, sin añadidos.

**Interna** (pseudocódigo):

```text
# domain/errors.py
class SimulationError(Exception)
class InvalidStorageError(SimulationError)               # storage_gb fuera de rango       (CA-2.3)
class InvalidApiCallsError(SimulationError)              # api_calls_per_month fuera       (CA-2.4)
class UnsupportedCustomerCountryError(SimulationError)   # país del cliente sin tasa       (CA-3.4)

# domain/simulations.py
MAX_STORAGE_GB = 1_000_000 ;  MAX_API_CALLS_PER_MONTH = 1_000_000_000
NewSimulation(customer_id, active_users, storage_gb, api_calls_per_month)
Simulation(id, customer_id, active_users, storage_gb, api_calls_per_month,
           currency, tiers: tuple[TierLine, ...], subtotal_cents, tax_rate_bp, tax_cents,
           total_cents, created_at: str)             # mismos nombres que el contrato
SimulationPage(items: tuple[Simulation, ...], total: int)
validate_usage(storage_gb, api_calls_per_month) -> None
      lanza InvalidStorageError o InvalidApiCallsError (type(x) is int, como validate_users)

# services/simulations.py
protocol SimulationStore:
    add(new: NewSimulation, price: PriceQuote, created_at: str) -> Simulation
    list_for_customer(customer_id: int, limit: int, offset: int) -> SimulationPage
save_simulation(new, customers: CustomerStore, simulations: SimulationStore,
                rates: TaxRateSource, now: datetime) -> Simulation
      lanza InvalidUsersError, InvalidStorageError, InvalidApiCallsError,
            CustomerNotFoundError o UnsupportedCustomerCountryError
list_simulations(customer_id, limit, offset, simulations: SimulationStore) -> SimulationPage

# repositories/customers.py
CustomerRepository.find_by_tax_id(tax_id: str) -> Customer | None

# api/identifiers.py
parse_customer_id(text: str) -> int       # lanza el 404 de 003 CA-6.3

# api/error_mapping.py (entradas nuevas)
InvalidStorageError              -> 422 storage_gb/STO
InvalidApiCallsError             -> 422 api_calls_per_month/APC
UnsupportedCustomerCountryError  -> 422 customer_id/CNS
```

## 5. Algoritmos

**Guardar (RF-1 a RF-4):**

```text
POST /simulations (payload, customers, simulations, rates, now):
    try: request = SimulationCreate.model_validate(payload)     # estricto, extra="forbid"
    except ValidationError:
        raise 422 field_errors(error, SIMULATION_INVALID_MESSAGES)        # RF-2, CA-3.2
    simulation = save_simulation(request.to_new_simulation(), customers, simulations, rates, now)
    return 201, SimulationResponse.from_simulation(simulation)

SimulationCreate:
    customer_id:         int, 1 ≤ x ≤ 2⁶³ − 1                       # CA-2.1
    active_users:        int, 0 ≤ x ≤ MAX_USERS                      # CA-2.2
    storage_gb:          int, 0 ≤ x ≤ MAX_STORAGE_GB                 # CA-2.3
    api_calls_per_month: int, 0 ≤ x ≤ MAX_API_CALLS_PER_MONTH        # CA-2.4

save_simulation(new, customers, simulations, rates, now):
    validate_users(new.active_users)                  # el servicio no se fía del borde
    validate_usage(new.storage_gb, new.api_calls_per_month)
    customer = get_customer(new.customer_id, customers)            # 404     CA-3.1
    try: price = quote(new.active_users, customer.country, rates)  # 001: una sola lectura de tasa
    except UnsupportedCountryError:
        raise UnsupportedCustomerCountryError(customer.id)         # 422 CNS CA-3.4
    return simulations.add(new, price, to_timestamp(now))          # CA-1.2

SimulationRepository.add(new, price, created_at):
    record = SimulationRecord(datos de new, importes de price, created_at,
                              tiers = [SimulationTierRecord(línea) por cada línea de price.tiers])
    session.add(record); commit                     # simulación y tramos en una transacción
    si falla: rollback y relanzar                   # CA-1.5
    return _to_simulation(record)
```

Con la petición validada, `validate_users` y `validate_usage` no pueden fallar desde la API. Están ahí para que el seed y cualquier llamada futura cumplan las mismas reglas (DT-2).

**Historial (RF-5):**

```text
GET /customers/{customer_id}/simulations (customer_id: texto, limit, offset):
    id = parse_customer_id(customer_id)           # 404 si no es un identificador  CA-5.5
    get_customer(id, customers)                   # 404 si no existe               CA-5.5
    try: page = PageQuery.model_validate(limit y offset recibidos)
    except ValidationError: raise 422 LIM / OFF                                     # CA-5.3
    return SimulationListResponse.from_page(list_simulations(id, page.limit, page.offset, ...))

SimulationRepository.list_for_customer(customer_id, limit, offset):
    total = COUNT(*) WHERE customer_id = :customer_id
    items = SELECT ... WHERE customer_id = :customer_id
            ORDER BY created_at DESC, id DESC LIMIT :limit OFFSET :offset           # CA-5.2
            con los tramos cargados en una sola consulta más (selectinload)
    cada elemento se construye con las filas guardadas, sin llamar al cálculo      # CA-4.5
```

**Seed (RF-8):**

```text
DEMO_SIMULATIONS = ((tax_id, active_users, storage_gb, api_calls_per_month), ...)   # tabla 6.9

seed_simulations(session, now) -> int:
    para cada tax_id de DEMO_SIMULATIONS, en orden:
        customer = CustomerRepository.find_by_tax_id(tax_id)
        si no existe o list_for_customer(customer.id, 1, 0).total > 0: saltar      # CA-8.2
        para cada fila de ese tax_id:
            new = SimulationCreate.model_validate({customer_id, ...}).to_new_simulation()
            save_simulation(new, ...)                                              # CA-8.3
    return cuántas creó

main(): seed_customers(...) y después seed_simulations(...); imprime una línea por cada uno.
```

La primera línea de `main()` no cambia; el test de 003 que la lee sigue pasando.

## 6. Decisiones técnicas

**Decisiones cerradas que se citan:** capas (ADR 0003), cotización en el backend (ADR 0004), cuerpo leído a mano y Pydantic estricto (plan 002 DT-1 y DT-2), el repositorio confirma por sí mismo (plan 003 DT-5), reloj inyectable (plan 003 DT-10), parámetros como texto (plan 003 DT-7).

| # | Decisión | Por qué | Alternativa descartada | RF |
| --- | --- | --- | --- | --- |
| DT-1 | La instantánea es el `PriceQuote` que devuelve `quote` de 001, copiado tal cual | Un único cálculo para la cotización y la simulación (RNF-2); `quote` lee la tasa una sola vez (001 CA-13.3) | Calcular en el repositorio o en el router | 4 |
| DT-2 | El servicio vuelve a validar usuarios, almacenamiento y llamadas con reglas del dominio | Las mismas reglas para la API, el seed y cualquier llamada futura (plan 003 DT-2) | Confiar solo en el esquema | 2, 8 |
| DT-3 | Error de dominio propio `UnsupportedCustomerCountryError` | `UnsupportedCountryError` ya se traduce a un detalle sobre `country`, un campo que esta petición no tiene; el detalle debe ir sobre `customer_id` con CNS | Reutilizar el error y traducirlo en el router | 3 |
| DT-4 | Simulación y tramos se guardan a través de la relación del ORM en un único `commit` | Comprobado: si falla el segundo tramo, no queda nada (CA-1.5) | Dos `commit` seguidos | 1, 7 |
| DT-5 | `simulation_tiers` guarda `from_users` y `to_users` | Spec D-3: el historial no depende de la constante actual de tramos (RN-8) | Reconstruirlos al leer | 4, 7 |
| DT-6 | El historial se construye desde las filas guardadas, sin recalcular | CA-4.3 a CA-4.5: el pasado no cambia aunque cambien tasas o tramos | Recalcular con `build_quote` | 4, 5 |
| DT-7 | `ORDER BY created_at DESC, id DESC` | `created_at` tiene precisión de segundos (spec D-9); el texto ISO se ordena como el tiempo | Ordenar solo por `id` | 5 |
| DT-8 | En el historial, el router comprueba el `{id}`, luego el cliente y solo después los parámetros | Spec D-7 y CA-5.5: el 404 va antes que el 422. Es orden de llamadas, no regla de negocio | Validar los parámetros primero, como hace el framework | 5 |
| DT-9 | `PageQuery` compartido, sacado de `CustomerListQuery` | Las mismas reglas y mensajes que `GET /customers` (CA-5.3) con un solo código. Los nombres que importan los tests de 003 siguen en `schemas/customers.py` | Copiar los validadores | 5 |
| DT-10 | `parse_customer_id` compartido, sacado de `api/customers.py` | El mismo 404 en la ficha y en el historial (CA-5.5) | Copiar la expresión regular | 5 |
| DT-11 | `restore_simulation_examples` repone los `null` de los ejemplos en `/openapi.json` | Comprobado: FastAPI sigue quitando los `null` de los ejemplos, y el contrato tiene `"to_users": null` | Ejemplos sin el tramo 3 | RNF-5 |
| DT-12 | `CHECK` con `typeof(...) = 'integer'` en todas las columnas numéricas | Comprobado: sin él, SQLite guardaría `1.5` en una columna INTEGER (DB-5) | Confiar en la afinidad de tipo | 7 |
| DT-13 | El seed pasa por el esquema y el servicio, busca al cliente por `tax_id` y salta los que ya tienen simulaciones | Mismas reglas que la API (CA-8.3) e idempotencia sin lógica propia (CA-8.2) | Insertar filas directamente | 8 |
| DT-14 | No se toca `core/errors.py` ni la configuración de CORS | Comprobado: `Allow: POST` y `Allow: GET` salen solos, y la preflight de `POST` responde 200 | Añadir casos especiales | 6 |
| DT-15 | Los tramos del historial se cargan con `selectinload` | Dos consultas por página en lugar de una por simulación | Carga perezosa | 5 |

## 7. Estrategia de tests (tests primero)

**Niveles y archivos:**

- **U** (`tests/unit/`): `test_simulation_domain.py` (`validate_usage`: límites, negativos, `bool` y `float`) y `test_simulation_schema.py` (reglas de RF-2 en el esquema, `-0`, mensajes y `PageQuery`). Los tests de arquitectura de 001 y 003 ya recorren los módulos nuevos de `domain/` y `api/`.
- **D** (`tests/integration/`): `test_simulations_migration.py` (DB-1, DB-3 a DB-9, DB-12 y DB-13), `test_simulation_repository.py` (DB-2, DB-10, DB-11, orden y paginación), `test_simulation_service.py` (cliente inexistente, país sin tasa, tasa cambiada) y `test_seed_simulations.py` (SE-1 a SE-6).
- **I** (`tests/api/`): `simulation_requests.py` (datos compartidos: clientes de partida, tabla 6.1 e instantes), `test_simulations_create.py` (SI y SN-1, SN-2), `test_simulations_snapshot.py` (SN-3 a SN-5), `test_simulations_validation.py` (SV y SC), `test_simulations_history.py` (HI y HP), `test_simulations_protocol.py` (ER-1 a ER-10) y `test_simulations_docs.py` (RNF-5).

**Derivación:** cada tabla de la sección 6 se copia una sola vez, como parámetros de pytest con el identificador del caso (entrada 20 del log). El docstring de cada test cita «spec 004» y los CA que cubre. `details` se compara como conjunto.

**Fixtures:** las de 001 a 003. `tests/api/conftest.py` se amplía con un reloj ajustable (`10:00:00Z` y `10:05:00Z` del 16-11-2026) sin cambiar ninguna fixture existente.

**Regla para los tests anteriores:** no se modifica ninguno. Los 744 de 001 a 003 pasan en cada tarea.

**Orden** (cada paso empieza en rojo):

1. **Dominio (U):** tipos, `validate_usage` y errores. → RF-2, RF-4.
2. **Persistencia (D):** migración y modelos; repositorio; `find_by_tax_id`; servicio. → RF-1, RF-3, RF-4, RF-5, RF-7.
3. **API (I):** mover `parse_customer_id` y `PageQuery` sin cambiar nada; esquemas; guardado válido e instantánea; validación y cliente; historial; protocolo y CORS; documentación. → RF-1 a RF-6.
4. **Seed (D).** → RF-8.
5. **Cierre:** arranque real, clon limpio, trazabilidad CA → test y revisión conjunta.

## 8. Trazabilidad

| RF | CA | Parte del plan | Casos |
| --- | --- | --- | --- |
| RF-1 Guardar | 1.1 a 1.6 | §5 guardar, DT-4, reloj inyectable | SI-1 a SI-13, DB-10 |
| RF-2 Validación | 2.1 a 2.8 | §5 `SimulationCreate`, DT-2, `error_mapping` | SV-1 a SV-18 |
| RF-3 Cliente | 3.1 a 3.4 | §5 `save_simulation`, DT-3 | SC-1 a SC-4, SV-18 |
| RF-4 Instantánea | 4.1 a 4.7 | DT-1, DT-5, DT-6, §3 `simulation_tiers` | SN-1 a SN-5, SI-1 a SI-9 |
| RF-5 Historial | 5.1 a 5.6 | §5 historial, DT-7 a DT-10, DT-15 | HI-1 a HI-13, HP-1 a HP-4 |
| RF-6 Protocolo y CORS | 6.1 a 6.3 | DT-14, `main.py` | ER-1 a ER-10 |
| RF-7 Persistencia | 7.1 a 7.5 | §3, DT-4, DT-12 | DB-1 a DB-13 |
| RF-8 Seed | 8.1 a 8.4 | §5 seed, DT-13 | SE-1 a SE-6 |

Los RNF: RNF-1, tests de arquitectura (dominio y routers sin base de datos); RNF-2, SN-1 y SE-5 contra `POST /pricing/quote`; RNF-3, SV-13 y ER-5; RNF-4, los textos viven en `schemas/simulations.py`; RNF-5, `test_simulations_docs.py`; RNF-6, `requirements.txt` no cambia.

## 9. Cumplimiento de la constitución

1. **Simplicidad:** ninguna dependencia nueva y nada fuera de la spec. Lo que se reutiliza de 003 se mueve, no se copia.
2. **La spec manda:** cada commit cita el RF o CA de 004 que implementa.
3. **Capas:** el dominio no importa FastAPI ni SQLAlchemy; el SQL vive solo en el repositorio; los routers validan, ordenan llamadas y traducen; los importes salen de `quote` de 001.
4. **Dinero y esquema:** importes en céntimos y tasa en puntos básicos, enteros en todas las capas y comprobados con `typeof` en SQLite. Cada simulación guarda su instantánea completa. El esquema cambia solo con la migración 0003.
5. **Tests y revisión:** tests primero en U, D e I; la suite completa pasa en cada commit; cada regla tiene test unitario y cada endpoint, test de integración; las correcciones se anotan en el log.
6. **Calidad, seguridad e idioma:** ruff y mypy sin errores; Pydantic estricto en toda entrada; consultas por ORM; mensajes en español y código en inglés.

## 10. Lo que reveló el prototipo

| Comprobación | Resultado | Consecuencia |
| --- | --- | --- |
| `-0` en un entero estricto de Pydantic | Llega como 0 | SI-12 sin código propio |
| `customer_id` 9223372036854775808 | Error `less_than_equal` en ese campo | CID con el mensaje del campo |
| `1e0` y `true` como entero estricto | Error `int_type` | SV-4 sin código propio |
| `users` en el cuerpo | `extra_forbidden` | SV-12 con el mensaje de 002 |
| Simulación y tramos por la relación del ORM, con el segundo tramo inválido | `CHECK constraint failed` y no queda ninguna fila nueva | DT-4, DB-10 |
| `active_users` = `1.5` con `CHECK typeof` | Rechazado | DT-12, DB-5 |
| `'15'` y `2.0` en una columna INTEGER | SQLite los convierte a entero y los acepta | Correcto: el valor guardado es un entero |
| `total_cents` distinto de la suma | Rechazado por el `CHECK` | CA-7.2, DB-6 |
| Simulación de un cliente inexistente y tramo de una simulación inexistente | `FOREIGN KEY constraint failed` | CA-7.2, DB-3 |
| Borrar un cliente con simulaciones | `FOREIGN KEY constraint failed` | CA-7.3, DB-9, sin `ON DELETE` |
| `session.get` con 2⁶³ − 1 | Devuelve `None`, sin error | SC-2 |
| Borrar todas las simulaciones y guardar otra | `AUTOINCREMENT` no reutiliza el `id` | CA-1.2, DB-11 |
| Ejemplo con `"to_users": null` en `/openapi.json` | FastAPI quita el `null` | DT-11 |
| `DELETE /customers/1/simulations` y `GET /simulations` sobre la aplicación real | 405 con `Allow: GET` y `Allow: POST`; `/customers` y `/customers/1` conservan su `Allow` | DT-14, ER-1, ER-3, ER-10 |
| Preflight de `POST /simulations` desde `http://localhost:4200` | 200 con `Access-Control-Allow-Origin` | DT-14, ER-7 |
| `POST /simulations/` | 404 sin redirección | ER-4 |

No quedan dudas abiertas. El siguiente paso es `tasks.md`, una tarea por paso de la sección 7.
