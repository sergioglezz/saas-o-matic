# Plan técnico — 002 Endpoint de cotización

**Estado:** ✅ ejecutado · **Spec:** [spec.md](spec.md) v1.1 · **Se apoya en:** §5, §6 y §8 de [00-spec-first](../00-spec-first.md), y en la spec y el código de 001

Los comportamientos de FastAPI, Starlette y Pydantic en los que se apoya este plan se comprobaron antes de escribirlo, con un prototipo desechable fuera del repositorio. La sección 10 recoge lo que reveló.

## 1. Resumen y alcance

- **Construye:**
  - La aplicación FastAPI (`app.main:app`), con el formato único de error global, CORS y `POST /pricing/quote`.
  - El endpoint solo valida, normaliza y traduce; el importe lo calcula el servicio `quote` de 001.
- **Cubre:** RF-1 a RF-9, RNF-1 a RNF-5 y el criterio de arranque con `uvicorn`.
- **Fuera:** clientes, simulaciones y el frontend. No cambian las reglas de cálculo ni la base de datos: no hay migración nueva.
- **Dependencias** (ninguna fuera del stack del §5 del 00 ni de `AGENTS.md`, así que no necesitan ADR; ver ADR 0001):
  - Ejecución: `fastapi`, `pydantic` (v2) y `starlette`, que se importan directamente, y `uvicorn` para servir la API.
  - Desarrollo: `httpx`, que usa el cliente de pruebas.
  - Se fijan las versiones exactas que se instalen.

## 2. Estructura de módulos

| Módulo | Responsabilidad | Puede importar | RF |
| --- | --- | --- | --- |
| `app/main.py` | `create_app(database_url=None, frontend_origin=None)` y `app = create_app()`; registra el CORS, los manejadores de error y el router; desactiva `redirect_slashes`; crea y libera el motor de base de datos en el `lifespan` | `api`, `core`, `db` | 6, 9 |
| `app/api/pricing.py` | Router `POST /pricing/quote`: lee el cuerpo, valida, llama al servicio y devuelve la respuesta. Sin reglas de negocio ni SQL | `schemas`, `services`, `api.validation`, `api.dependencies` | 1, 3, 5 |
| `app/api/validation.py` | `read_json_object(request)` (cuerpo y `Content-Type`) y `field_errors(validation_error, invalid_messages)` (errores de Pydantic al formato de la spec). Reutilizable por specs futuras | `core.errors`, `pydantic` | 2, 3, 5, 7 |
| `app/api/dependencies.py` | `get_db_session` (una sesión por petición) y `get_rate_source` (`TaxRateRepository`). Se pueden sustituir en los tests | `db`, `repositories` | 1 |
| `app/schemas/pricing.py` | `QuoteRequest` (estricto, `extra="forbid"`), `normalize_country`, los mensajes de los campos, y `QuoteResponse`/`TierLineResponse` con su ejemplo para `/docs` | `pydantic`, `domain.pricing` (solo para tipos) | 2, 3, 4, 5 |
| `app/core/errors.py` | `ApiError` y `FieldError`; los textos de primer nivel; manejadores globales (ver la sección 4); el mapeo de errores de dominio a HTTP en un único punto (§6 del 00) | `fastapi`, `starlette`, `domain.errors` | 6, 8 |
| `app/core/config.py` (ampliado) | `get_frontend_origin()`: `FRONTEND_ORIGIN`, por defecto `http://localhost:4200` | Biblioteca estándar | 9 |
| `app/services/pricing.py` (ampliado) | Nueva función `country_is_supported(country, rates) -> bool`. `quote` no cambia | Como en 001 | 3 |

Las dependencias siguen `api → services → (domain, repositories)`. `api` no importa `repositories` salvo en `dependencies.py`, que es el punto de inyección. El test de arquitectura de 001 sigue vigilando `domain/`.

## 3. Modelo de datos

No hay cambios. Se reutilizan la tabla `tax_rates` y la migración 0001 de 001. La API lee las tasas con `TaxRateRepository` a través de `get_rate_source`. Si la base de datos no está migrada, la consulta falla y responde 500 (CA-6.5).

## 4. Interfaz pública

**HTTP:** el contrato de la sección 5 de la spec, sin añadidos.

**Interna** (pseudocódigo):

```text
# app/core/errors.py
FieldError(field: str, message: str)
ApiError(status: int, code: str, message: str, details: list[FieldError] = [], headers: dict = {})
register_error_handlers(app):
    ApiError                         -> su estado y el cuerpo {"error": {code, message, details}}
    StarletteHTTPException 404       -> 404 not_found «Recurso no encontrado»
    StarletteHTTPException 405       -> 405 method_not_allowed «Método no permitido», conservando la cabecera Allow
    UnsupportedCountryError          -> 422 con country / «País no soportado»
    InvalidUsersError                -> 422 con users / «Debe ser un número entero entre 0 y 100000»
    Exception                        -> 500 internal_error «Error interno del servidor», details vacío

# app/api/validation.py
async read_json_object(request) -> dict[str, object]     lanza ApiError 422 body/BODY
field_errors(error: ValidationError, invalid_messages: dict[str, str]) -> list[FieldError]

# app/schemas/pricing.py
normalize_country(value: str) -> str                     lanza ValueError si no son 2 letras A-Z
QuoteRequest(users: int [estricto, 0..MAX_USERS], country: str [estricto, normalizado])
QuoteResponse.from_quote(quote: PriceQuote) -> QuoteResponse

# app/services/pricing.py
country_is_supported(country: str, rates: TaxRateSource) -> bool
```

## 5. Algoritmos

**Lectura del cuerpo (RF-7):**

```text
read_json_object(request):
    media_type = cabecera Content-Type hasta el primer ";", sin espacios y en minúsculas
    si media_type != "application/json": ApiError 422 body/BODY          # E-41, E-42; O-15 pasa
    raw = await request.body()
    try: data = json.loads(raw.decode("utf-8"))                          # repetidas: gana la última (O-2)
    except (UnicodeDecodeError, JSONDecodeError): ApiError 422 body/BODY  # E-37, E-40
    si data no es dict: ApiError 422 body/BODY                           # E-38, E-39
    return data
```

**Validación y cotización (RF-1 a RF-3 y RF-5):**

```text
post_quote(data, rates):
    try:
        request = QuoteRequest.model_validate(data)                      # strict=True, extra="forbid"
    except ValidationError as error:
        details = field_errors(error, {"users": USR, "country": FMT})
        # E-35: si el país no tiene error de formato, se comprueba también su soporte
        si "country" no está en details y "country" está en data:
            country = normalize_country(data["country"])
            si not country_is_supported(country, rates): details += country/NSP
        raise ApiError 422 validation_error (details)
    result = quote(request.users, request.country, rates)                # UnsupportedCountryError -> NSP
    return QuoteResponse.from_quote(result)
```

**Errores de Pydantic al formato de la spec:**

```text
field_errors(error, invalid_messages):
    por cada error, en orden; field = str(loc[0]); un solo elemento por campo (E-15):
        type == "missing"         -> field / «Campo obligatorio»      # E-16, E-30, E-31
        type == "extra_forbidden" -> field / «Campo no permitido»     # E-32 a E-34, E-36
        otro                      -> field / invalid_messages[field]  # USR o FMT
```

**Normalización del país (RF-3):**

```text
normalize_country(value):
    trimmed = value.strip(" \t\n\r")                 # NO str.strip(): quitaría el espacio no separable (E-23)
    upper = trimmed.translate(a-z -> A-Z)            # NO str.upper(): "ß".upper() da "SS"
    si upper no cumple ^[A-Z]{2}$: raise ValueError  # E-18 a E-25
    return upper
```

**Ejemplo trabajado.** Petición `{"users": -1, "country": "xx"}` (variante de E-35):
1. `read_json_object` da `{"users": -1, "country": "xx"}`.
2. Pydantic falla solo en `users` (`greater_than_equal`), lo que da users/USR. `country` pasa: `normalize_country("xx")` devuelve `"XX"`.
3. Como `country` no tiene error, se comprueba si está soportado: `country_is_supported("XX")` es falso, así que se añade country/NSP.
4. Respuesta: 422 `validation_error` con los dos detalles (CA-6.3).

## 6. Decisiones técnicas

**Decisiones cerradas que se citan:** cotización en el backend (ADR 0004), capas (ADR 0003), céntimos y puntos básicos (ADR 0002), FastAPI (ADR 0001).

| # | Decisión | Por qué | Alternativa descartada | RF |
| --- | --- | --- | --- | --- |
| DT-1 | Leer el cuerpo en crudo y validarlo con `QuoteRequest.model_validate` | Control total y explícito de los 6 casos de cuerpo inválido (E-37 a E-42) y de su detalle `body`; no depende de cómo cada versión de FastAPI clasifica esos errores. El esquema se publica en `/docs` con `openapi_extra` | Declarar el modelo como parámetro del endpoint y traducir los errores internos de FastAPI | 7 |
| DT-2 | Pydantic en modo estricto con `extra="forbid"` | Comprobado: rechaza `15.0`, `1e2`, `true`, `"15"` y `null` como `int_type`; acepta `-0` como 0; informa a la vez de un campo que falta y de uno que sobra | Modo flexible: convierte `"15"` en 15 y rompe E-8 | 2, 5 |
| DT-3 | `strip(" \t\n\r")` y mayúsculas solo para ASCII | Comprobado: `str.strip()` quita el espacio no separable y `"ß".upper()` da `"SS"`; las dos cosas incumplirían la spec | `str.strip().upper()` | 3 |
| DT-4 | Comprobar el soporte del país también cuando falla `users`, con `country_is_supported` del servicio | E-35 exige los dos errores, y `quote` se para en el de usuarios (001 CA-3.5) | Llamar a `quote` (se detiene antes) o consultar el repositorio desde el router (rompe las capas) | 3, 6 |
| DT-5 | Manejadores globales en `core/errors.py`, y todos los textos en un solo módulo por capa | El §6 del 00 pide un único punto de mapeo; el formato vale para cualquier ruta futura (CA-6.7) | Montar los errores en cada endpoint | 6, 8 |
| DT-6 | `app.router.redirect_slashes = False` | Comprobado: así `/pricing/quote/` da 404 y no una redirección 307 (CA-6.7, O-14) | Dejar la redirección por defecto | 6 |
| DT-7 | `CORSMiddleware` (viene con FastAPI) con el origen de `FRONTEND_ORIGIN`, el método `POST` y la cabecera `Content-Type` | Comprobado: la preflight autorizada da 200 con la cabecera; desde otro origen no la lleva | `allow_origins=["*"]`, que rompe RF-9 | 9 |
| DT-8 | Factoría `create_app(...)` y dependencias inyectables | Los tests usan una base de datos temporal y, para O-5, una fuente de tasas que falla, sin tocar globales | Una aplicación y un motor globales | 1, 6 |
| DT-9 | Endpoint síncrono (`def`) y lectura del cuerpo en una dependencia asíncrona | FastAPI ejecuta el endpoint en un hilo, así que la consulta síncrona a SQLite no bloquea el servidor | Un endpoint `async` con consultas síncronas | 1 |

Consecuencia aceptada: un 500 lo genera Starlette por fuera de la capa de CORS, así que sale sin `Access-Control-Allow-Origin` (comprobado) y el navegador solo verá «error de red». El simulador lo trata igual que cualquier otro fallo de cotización (flujo 3 del 00).

## 7. Estrategia de tests (tests primero)

**Niveles:**
- **U** (sin servidor): `tests/unit/test_quote_schema.py`. Cubre `normalize_country` (normaliza y rechaza, incluido «ß»), `QuoteRequest` y `field_errors`.
- **I** (petición HTTP): `tests/api/`, la carpeta que prevé el §5 del 00. Usa `TestClient` sobre `create_app(database_url=<SQLite migrado temporal>)` con `raise_server_exceptions=False`, para que O-5 devuelva la respuesta 500 en lugar de lanzar la excepción.

**Fixtures:** las de base de datos de 001 (`alembic_config`, `database_url`, `migrated_engine` y `session`) pasan de `tests/integration/conftest.py` a `tests/conftest.py`, para compartirlas con `tests/api/`. Se ajusta el import de `test_tax_rates_migration.py`; no cambia ningún test.

**Derivación:** cada tabla de la sección 6 de la spec se copia como parámetros de pytest, con el identificador del caso (`Q-4`, `E-35`, `O-11`) y el CA en el docstring. Los cuerpos se envían en crudo (`content=` y cabeceras explícitas) para reproducir exactamente `1e2`, `-0`, las claves repetidas, `\u00a0` y la ausencia de `Content-Type`. `details` se compara como conjunto (CA-6.4). O-9 analiza la respuesta con un `parse_float` que falla si aparece algún decimal.

**Orden** (cada paso empieza en rojo):
1. Errores globales: 404, 405 (con `Allow`; `HEAD` y `OPTIONS`) y 500 con una ruta que falla a propósito.
2. Cuerpo: E-37 a E-42, O-1, O-2 y O-15.
3. Esquema (U), y luego E-1 a E-36 por HTTP.
4. Cotizaciones válidas: Q-1 a Q-20, O-6, O-7 y O-9.
5. CORS: O-10 a O-12.
6. `/docs` y `/openapi.json` con el ejemplo (RNF-5).
7. Arranque real con `uvicorn` y la medición de RNF-2.

## 8. Trazabilidad

| RF | Parte del plan | Tests |
| --- | --- | --- |
| RF-1 | §2 router, §5 `post_quote`, servicio `quote` de 001 | Q-1 a Q-20, O-6, O-7 |
| RF-2 | §4 `QuoteRequest` estricto, rango 0..`MAX_USERS` | E-1 a E-16, Q-20 (U y I) |
| RF-3 | §5 `normalize_country`, DT-4 | Q-11 a Q-19, E-17 a E-30, E-35 (U y I) |
| RF-4 | §4 `QuoteResponse` | Q-4, Q-20, O-9 |
| RF-5 | DT-2 `extra="forbid"`, `field_errors` | E-32 a E-36 |
| RF-6 | §4 `register_error_handlers`, DT-5, DT-6 | Todos los E, O-3 a O-5, O-8, O-13, O-14 |
| RF-7 | §5 `read_json_object` | E-37 a E-42, O-1, O-2, O-15 |
| RF-8 | Starlette 405 más el manejador que conserva `Allow` | O-3, O-4 |
| RF-9 | DT-7 `CORSMiddleware` | O-10 a O-12 |

Los RNF también quedan cubiertos:
- **RNF-1:** el endpoint no calcula; solo llama a `quote`.
- **RNF-2:** se mide en el paso 7.
- **RNF-3:** O-5 y O-10 a O-12.
- **RNF-4:** los textos de error están en `core/errors.py` y `schemas/pricing.py`.
- **RNF-5:** test de `/openapi.json`.

## 9. Cumplimiento de la constitución

1. **Simplicidad:** solo dependencias del stack del 00 (ADR 0001); nada fuera de la spec.
2. **La spec manda:** cada commit citará el RF o CA de 002, y la sección 8 enlaza RF, plan y tests.
3. **Capas:** el router valida y traduce, sin reglas de negocio ni SQL; el mapeo de errores de dominio a HTTP está en un único módulo.
4. **Dinero:** la API transporta los enteros del dominio sin convertirlos; O-9 comprueba que no aparece ningún decimal.
5. **Tests y revisión:** tests primero en U e I, derivados de las tablas; la suite completa pasa antes de cada commit; las correcciones se anotan en el log.
6. **Calidad y seguridad:** ruff y mypy estrictos; toda entrada se valida con Pydantic; CORS limitado; los errores no exponen información interna.

## 10. Dudas abiertas

No quedan dudas abiertas. La que había se cerró al aprobar el plan: la spec pasó a v1.1 con el ajuste propuesto.

- **D-1 (cerrada). Preflight de CORS aceptada frente a CA-6.6.** El prototipo muestra que `CORSMiddleware` responde a la preflight autorizada con 200 y `text/plain` (cuerpo «OK»). CA-6.6 exige JSON en todo salvo `HEAD` y las preflight *rechazadas*. Propuesta: una v1.1 de la spec que excluya de CA-6.6 **todas** las respuestas preflight, aceptadas o rechazadas, porque son respuestas del protocolo CORS y no de la API. Es un cambio de una línea y no afecta a ningún caso. La alternativa es una preflight propia en JSON: más código, sin beneficio para el usuario.
