# Plan técnico — 005 Frontend

Estado: v1.0, pendiente de la revisión del autor junto con la spec · Spec: `spec.md` v1.1 · Constitución: `ai-workspace/docs/constitution.md` · Arquitectura: §5 de `00-spec-first.md` y ADR 0001, 0004, 0005 y 0010 · Base: los contratos de 002, 003 y 004, sin cambios

Antes de escribir este plan se comprobaron con Node las salidas de `Intl` para `es-ES` en las que se apoya el formato de RF-5. El resto del prototipo (runner, DOM simulado, reloj y peticiones falsas) necesitaba una versión de Node compatible con Angular 22 (finalmente Node 26.13.1 LTS, ADR 0010). Se hace en T-01, antes de cualquier código de la aplicación, y su resultado completa la sección 10.

## 1. Resumen y alcance

- **Construye:**
  - El proyecto Angular 22 en `frontend/`, con lint y tests (ADR 0010).
  - El núcleo: el cliente de la API, la clasificación de errores, las tasas de cambio, la divisa elegida y el formato.
  - Las pantallas: listado y búsqueda, alta, ficha con simulador e historial, y página no encontrada.
- **Cubre:** RF-1 a RF-13 y RNF-1 a RNF-11 de la spec. La sección 8 indica qué parte del plan cubre cada RF y cada CA.
- **Reutiliza sin cambiar:** los endpoints de 002 a 004 y su formato de error. El backend no se toca.
- **Fuera:** spec, sección 9.
- **Dependencias:** las del proyecto base de Angular CLI 22 y angular-eslint, solo de desarrollo. **ADR:** 0010 (nuevo), con Node 26 LTS.

## 2. Estructura de módulos

Todo vive en `frontend/src/app/`, con las tres carpetas de §5 del 00: `core/` (cliente de API, tasas y divisa), `features/` (`customers/` y `simulator/`) y `shared/` (formato, componentes de interfaz y textos). Cada componente tiene su plantilla `.html` junto al `.ts` cuando pasa de unas pocas líneas.

| Archivo | Responsabilidad | Puede importar | RF |
| --- | --- | --- | --- |
| `core/api/api-config.ts` | `API_BASE_URL` (`http://127.0.0.1:8000`), `RATES_URL`, `REQUEST_TIMEOUT_MS` (10 000) y `PAGE_SIZE` (50) | Angular (`InjectionToken`) | 2, 3, 7 |
| `core/api/api-models.ts` | Tipos del contrato: `Customer`, `CustomerPage`, `NewCustomer`, `TierLine`, `PriceQuote`, `Simulation`, `SimulationPage`, `NewSimulation`, `ErrorDetail` | Nada | 2 |
| `core/api/request-failure.ts` | `RequestFailure` y `toRequestFailure(error)`: un único punto que clasifica cualquier fallo según la tabla 5.3 | Angular (`HttpErrorResponse`), RxJS (`TimeoutError`) | 2 |
| `core/api/customers-api.ts` | `CustomersApi`: `list(q, offset)`, `get(id)` y `create(body)` | `HttpClient`, `api-config`, `api-models` | 6, 8, 9 |
| `core/api/simulations-api.ts` | `SimulationsApi`: `quote(users, country)`, `save(body)` e `history(customerId, offset)` | Igual | 10, 12, 13 |
| `core/rates/rates-snapshot.ts` | Puro: `RatesSnapshot`, `parseRatesSnapshot`, `isFresh`, `offeredCurrencies` y `CURRENCY_CODES` | Nada | 3, 4 |
| `core/rates/browser-storage.ts` | `BrowserStorage`: lee y escribe la divisa y las tasas; cualquier fallo del almacenamiento cuenta como «no hay nada» | Angular | 3, 4 |
| `core/rates/exchange-rates.ts` | `ExchangeRates`: estado de las tasas (`loading`, `fresh`, `stale`, `unavailable`), `load()` y `retry()` | `HttpClient`, `rates-snapshot`, `browser-storage`, `api-config` | 3 |
| `core/rates/display-currency.ts` | `DisplayCurrency`: divisas ofrecidas, divisa elegida y recordada, `choose(code)` y la tasa activa | `exchange-rates`, `browser-storage` | 4 |
| `shared/format/money.ts` | Puro: `toHundredths(cents, rate)` exacto y `formatMoney(cents, display)` | Nada | 5 |
| `shared/format/numbers.ts` | Puro: `formatCount`, `formatTaxRate`, `formatRate` y `tierRange` | Nada | 5 |
| `shared/format/dates.ts` | Puro: `formatDateTime`, `formatDate` y `formatUnixDate` | Nada | 3, 5 |
| `shared/format/format-pipes.ts` | Pipes puros `money`, `count`, `taxRate`, `dateTime` y `day` sobre las funciones anteriores | Angular, `shared/format` | 5 |
| `shared/texts.ts` | Los textos T-xxx, las etiquetas y los nombres de países, planes y divisas | Nada | RNF-5 |
| `shared/paged-list.ts` | `PagedList<T>`: elementos, `total`, estados, `reload`, `loadMore`, `retry` y `prepend`, sin repetir `id` | Angular (signals), RxJS, `request-failure` | 7, 10 |
| `shared/ui/request-error.ts` | Texto T-CON o T-SRV y botón «Reintentar» | Angular, `texts` | 2 |
| `shared/ui/load-more.ts` | T-MOS y «Cargar más» de una `PagedList` | Angular, `paged-list`, `texts` | 7 |
| `shared/ui/tier-table.ts` | Tabla de desglose (CA-12.6), usada por el simulador y por el historial | Angular, `format-pipes` | 10, 12 |
| `shared/ui/currency-bar.ts` | Selector «Divisa», línea de tasas, avisos, T-EQ, T-ORI y atribución | Angular, `core/rates`, `format`, `texts` | 3, 4 |
| `shared/ui/not-found-page.ts` | T-NFP con «Volver al listado» | Angular, `texts` | 1 |
| `features/customers/customer-list-page.ts` | Buscador con espera, listado, estados y «Cargar más» | Angular, RxJS, `core/api`, `shared` | 6, 7 |
| `features/customers/customer-form-page.ts` | Formulario de alta, envío y errores por campo | Angular (formularios reactivos), `core/api`, `shared` | 8 |
| `features/customers/customer-form-errors.ts` | Puro: reparte los `details` de un 422 o 409 entre los cinco campos y el aviso general | `api-models` | 8 |
| `features/customers/customer-detail-page.ts` | Ficha: carga el cliente y después muestra simulador e historial; T-REG | Angular, `core/api`, `shared`, `simulator`, historial | 9 |
| `features/customers/simulation-history.ts` | Sección del historial con sus estados y «Cargar más» | Angular, `shared` | 10 |
| `features/customers/simulation-card.ts` | Tarjeta de una simulación con «Ver desglose» | Angular, `shared` | 10 |
| `features/simulator/usage-input.ts` | Puro: `parseCount(text, max)` y los máximos de usuarios, almacenamiento y llamadas | Nada | 11 |
| `features/simulator/quote-flow.ts` | `QuoteFlow`: espera de 300 ms, petición, descarte de respuestas viejas, estado de la cotización | Angular (signals), RxJS, `core/api` | 12 |
| `features/simulator/simulator.ts` | Valores de entrada, slider, cotización, guardado y avisos | Angular, `quote-flow`, `usage-input`, `core/api`, `shared` | 11, 12, 13 |
| `app.ts`, `app.html`, `app.routes.ts`, `app.config.ts` | Cabecera con el nombre y la barra de divisa; rutas; proveedores; arranque de las tasas | Angular, `core`, `features`, `shared` | 1, 3 |
| `src/index.html`, `src/styles.css` | `lang="es"`, título y estilos comunes (foco visible, contraste, tarjetas) | — | RNF-3, RNF-4 |
| `src/test-setup.ts` | Zona horaria `Europe/Madrid` para todos los tests | — | Tests |
| `src/testing/spec-data.ts` | Datos de la spec escritos una sola vez: cliente Acme, tasas de 5.4, cotizaciones de 15 y 60 usuarios, simulación de SI-1 | `api-models` | Tests |

**Reglas de capas** (comprobadas por el lint, ADR 0010):

- `shared/format/`, `rates-snapshot.ts`, `usage-input.ts` y `customer-form-errors.ts` son funciones puras: no importan Angular ni RxJS y se prueban sin pantalla (nivel U).
- Solo `core/` importa `HttpClient`: las pantallas piden los datos a `CustomersApi`, `SimulationsApi` y `ExchangeRates` (`AGENTS.md`).
- Ningún archivo calcula importes: solo los convierte y les da formato (RNF-1). Las únicas operaciones con céntimos están en `money.ts`.

## 3. Datos: tipos del contrato y almacenamiento del navegador

No hay base de datos. Los datos son de dos tipos:

- **Tipos del contrato** (`api-models.ts`): copian los campos de las secciones 5 de 003 y 004 y de 002 con los mismos nombres en `snake_case`, porque son el contrato observable. Los importes son `number` enteros en céntimos y solo los convierte `money.ts`.
- **Almacenamiento del navegador** (`browser-storage.ts`), con dos claves y nada más (spec 5.5):

| Clave | Contenido | Se escribe | Se lee |
| --- | --- | --- | --- |
| `saas-o-matic.currency` | Código de la divisa elegida | Al elegir una divisa (CA-4.4) | Al tener tasas (CA-4.5, CA-4.6) |
| `saas-o-matic.rates` | JSON con `rates`, `time_last_update_unix` y `time_next_update_unix` | Con cada respuesta válida (CA-3.4) | Al cargar la app (CA-3.1) y si falla la petición (CA-3.6) |

Lo guardado se valida con la misma función que la respuesta de la API (`parseRatesSnapshot`); si no pasa, se trata como inexistente (CA-3.13).

## 4. Interfaz pública

**Pantallas y peticiones:** las de las secciones 5.1 y 5.2 de la spec, sin añadidos.

**Interna** (pseudocódigo):

```text
# core/api
RequestFailure = { kind: 'connection' | 'server' | 'not_found' | 'conflict' | 'validation' | 'client',
                   details: ErrorDetail[] }
toRequestFailure(error: unknown) -> RequestFailure
CustomersApi.list(q: string, offset: number) -> Observable<CustomerPage>
CustomersApi.get(id: string) -> Observable<Customer>
CustomersApi.create(body: NewCustomer) -> Observable<Customer>
SimulationsApi.quote(users: number, country: string) -> Observable<PriceQuote>
SimulationsApi.save(body: NewSimulation) -> Observable<Simulation>
SimulationsApi.history(customerId: number, offset: number) -> Observable<SimulationPage>
      todas con timeout(REQUEST_TIMEOUT_MS) y sin capturar errores: los clasifica quien llama

# core/rates
RatesSnapshot = { rates: Record<string, number>, lastUpdate: number, nextUpdate: number }
parseRatesSnapshot(value: unknown) -> RatesSnapshot | null          # CA-3.3
isFresh(snapshot, nowSeconds) -> boolean                              # nextUpdate > now
offeredCurrencies(snapshot | null) -> CurrencyCode[]                  # CA-3.5
ExchangeRates: status(), snapshot(), load(), retry()
DisplayCurrency: offered(), selected(), rate() -> number | null, choose(code)

# shared
MoneyDisplay = { code: CurrencyCode, rate: number | null }            # null en EUR
toHundredths(cents, rate) -> bigint                                   # redondeo exacto CA-5.2
formatMoney(cents, display) -> string                                 # CA-5.3, CA-5.4
formatCount(n), formatTaxRate(bp), formatRate(rate), tierRange(from, to)
formatDateTime(iso), formatDate(iso), formatUnixDate(seconds)
PagedList<T extends { id: number }>(fetch: (offset) -> Observable<Page<T>>)
      items(), total(), status(): 'loading' | 'ready' | 'error', failure(),
      moreStatus(): 'idle' | 'loading' | 'error', reload(), loadMore(), retry(), prepend(item)

# features
parseCount(text, max) -> number | null                                # CA-11.5, 11.7, 11.8
fieldErrorsFrom(failure) -> { fields: Partial<Record<CustomerField, string>>, general: boolean }
QuoteFlow(country): change(text), retry(), quote(), state(), pending(), quotedUsers()
```

## 5. Algoritmos

**Conversión exacta (CA-5.2 a CA-5.4):**

```text
toHundredths(cents, rate):
    texto = String(rate)                         # la escritura decimal más corta: "1.005"
    (dígitos, escala) = decimal exacto de texto  # "1.005" -> (1005, 3); admite exponente
    producto = BigInt(cents) * dígitos           # céntimos × tasa, escalado por 10^escala
    return redondeo mitad hacia arriba de producto / 10^escala     # centésimas de la divisa

formatMoney(cents, display):
    centésimas = display.rate es null ? BigInt(cents) : toHundredths(cents, display.rate)
    texto = parte entera + "." + 2 decimales                      # sin pasar por float
    return Intl.NumberFormat("es-ES", { style: "currency", currency: display.code,
           minimumFractionDigits: 2, maximumFractionDigits: 2, useGrouping: "always" }).format(texto)
```

`Intl` acepta el importe como texto decimal y lo formatea sin redondear otra vez. `formatRate` usa la misma vía, con un máximo de 4 decimales.

**Tasas (RF-3):**

```text
ExchangeRates.load():                                 # una vez, desde el arranque de la app
    guardadas = parseRatesSnapshot(storage.rates())
    si guardadas y isFresh(guardadas, ahora): status = fresh; snapshot = guardadas; fin  # CA-3.1
    status = loading                                                                     # CA-4.2
    http.get(RATES_URL).pipe(timeout(10 000)) ->
        éxito con parseRatesSnapshot(respuesta) válido: guardar; status = fresh          # CA-3.4
        cualquier otro caso: status = guardadas ? stale : unavailable                    # CA-3.6, 3.7
retry(): repite la petición sin mirar la caché                                           # CA-3.8
```

**Divisa (RF-4):** `selected` es un `computed`: EUR si `status` es `loading`; si no, la recordada si está en `offered`; si no, EUR. `choose(code)` la guarda (CA-4.4); nunca se borra la recordada (CA-4.6).

**Listas paginadas (RF-7), común al listado y al historial:**

```text
PagedList.reload():   cancela la petición en curso; status = loading; fetch(0)
                      -> items = respuesta.items; total = respuesta.total; status = ready
                      -> error: status = error; failure = toRequestFailure(e)
PagedList.loadMore(): si moreStatus = loading, no hace nada                     # CA-7.4
                      moreStatus = loading; fetch(items.length)
                      -> añade los de id nuevo al final; total = respuesta.total  # CA-7.2, 7.3
                      -> error: moreStatus = error, se conservan los elementos   # CA-7.5
PagedList.retry():    repite la última operación que falló (reload o loadMore)
PagedList.prepend(x): items = [x, ...items]; total + 1                          # CA-10.8
```

**Búsqueda (RF-6):** cada cambio del buscador entra en un `Subject`; `debounceTime(300)` y después `switchMap` a `list.reload()` con el texto. `switchMap` cancela la búsqueda anterior, así que su respuesta nunca llega a la pantalla (CA-6.5, CA-6.6). Un texto vacío o de espacios se envía sin `q`.

**Alta (RF-8):** al enviar, si algún campo recortado está vacío → T-OBL en esos campos y foco en el primero, sin petición. Si no, `create` con los valores tal cual. Con 201, navegación a la ficha con el estado `{ registered: true }`. Con error, `fieldErrorsFrom(failure)` reparte los mensajes (422 y 409); conexión y servidor muestran `request-error`, cuyo «Reintentar» reenvía el último cuerpo.

**Ficha (RF-9):** `get(id)`; con 200 se crean el simulador y la `PagedList` del historial, y solo entonces salen sus peticiones (spec D-17). Con 404, T-NFC y nada más. T-REG se muestra si la navegación trae `registered`.

**Cotización (RF-12):**

```text
QuoteFlow.change(texto):                     # cada cambio del campo o del slider
    valor = parseCount(texto, 100 000)
    cambios.next(valor)                      # también los no válidos: cuentan como «otro cambio»
    pendiente = valor no es null y valor != usuarios de la cotización mostrada

cambios.pipe(debounceTime(300), filter(valor no es null),
             filter(valor != usuarios mostrados o la última falló),       # CA-12.4
             switchMap(valor -> quote(valor, country)))                    # CA-12.5: cancela la anterior
    -> 200: cotización = respuesta; usuarios mostrados = valor; estado = ok
    -> 422 de country «País no soportado»: estado = unsupported           # CA-12.9
    -> otro error: estado = failed, se conserva la cotización              # CA-12.8
    pendiente = false

quote() inicial: sin espera, con 15 usuarios (CA-12.1); retry(): sin espera, con el valor actual.
```

**Guardar (RF-13):**

```text
puedeGuardar = valores válidos y estado = ok y usuarios mostrados = valor actual
               y no pendiente y no guardando                                 # CA-13.1
guardar(): si no puedeGuardar, nada; guardando = true; save(cuerpo)
    -> 201: emitir saved(simulación); aviso T-SOK                            # CA-13.4
    -> 422 de customer_id CNS: T-CNS; -> otro 4xx: T-SKO sin reintento       # CA-13.7, 13.8
    -> conexión o servidor: T-SKO con «Reintentar», mismo cuerpo             # CA-13.6
    guardando = false
Ficha, al recibir saved: historial cargado -> prepend; si no -> reload       # CA-10.8, 10.9
```

## 6. Decisiones técnicas

**Decisiones cerradas que se citan:** cotización en el backend (ADR 0004), conversión solo en el frontend (ADR 0005), sin autenticación (ADR 0007), herramientas del frontend (ADR 0010) y las decisiones D-1 a D-21 de la spec.

| # | Decisión | Por qué | Alternativa descartada | RF |
| --- | --- | --- | --- | --- |
| DT-1 | Angular 22 con Node 26 LTS, proyecto base de la CLI sin renderizado en servidor | Única versión con soporte; elegida por el autor (ADR 0010) | Angular 19 con Node 22.11 | Todos |
| DT-2 | Tests con el runner por defecto y un archivo de arranque que fija la zona `Europe/Madrid` | Las fechas de la spec (CV-18 a CV-21) dependen de la zona; el equipo de cada uno no debe cambiar el resultado | Pasar la zona como parámetro a cada función | 5 |
| DT-3 | Conversión con enteros grandes sobre la escritura decimal de la tasa | `100 × 1.005` en coma flotante da 100,4999…, y la spec exige 1,01 (CV-11 a CV-13) | Multiplicar en coma flotante y redondear | 5 |
| DT-4 | Fechas con hora compuestas por partes (`dd/mm/aaaa` + espacio + `hh:mm`) | Comprobado: `Intl` para `es-ES` escribe «17/11/2026, 00:30», con coma (sección 10) | Usar el formato completo de `Intl` | 5 |
| DT-5 | `useGrouping: "always"` en todos los números | Comprobado: `es-ES` no agrupa 4 cifras por defecto («1234»), y la spec pide «1.234» (D-7) | Agrupar a mano | 5 |
| DT-6 | Las APIs devuelven el error tal cual y `toRequestFailure` lo clasifica en un solo punto | Una única tabla de la spec (5.3) traducida en un único sitio, como el `error_mapping` del backend | Clasificar en cada pantalla | 2 |
| DT-7 | `timeout(10 000)` en cada petición, al backend y a la API de tasas | D-5: ningún estado de carga infinito; el error de tiempo se clasifica como conexión | Sin límite | 2, 3 |
| DT-8 | `debounceTime(300)` sobre todos los cambios y `switchMap` para pedir | Un cambio a un valor no válido también cancela la espera (CA-12.2); `switchMap` cancela la petición anterior, así que una respuesta vieja no llega a pintarse (CA-6.6, CA-12.5) | Comparar números de petición a mano | 6, 12 |
| DT-9 | `PagedList` común al listado y al historial | Las mismas reglas de «Cargar más» (RF-7) con un solo código | Copiar la lógica en las dos pantallas | 7, 10 |
| DT-10 | Campos numéricos como texto con teclado numérico (`inputmode="numeric"`) y slider de rango nativo | Un campo de tipo número del navegador transforma o vacía `1e3` y `-1` antes de que se puedan validar (CA-11.5); el rango nativo ya responde al teclado (CA-11.4) | Campos de tipo número; slider propio | 11 |
| DT-11 | Controles nativos para el teclado, Intro, enlaces y límites de caracteres (`maxlength`) | Accesibles sin código propio; el test C comprueba el control y MA-3 el comportamiento (spec v1.1) | Manejar el teclado a mano | 1, 6, 8, 11 |
| DT-12 | El aviso T-REG viaja en el estado de la navegación; la ficha lo lee de la navegación en curso al crearse (sección 10) | Desaparece al salir y volver a la ficha (FI-9) sin guardar nada | Un parámetro en la dirección | 8, 9 |
| DT-13 | La ficha es dueña de la `PagedList` del historial; el simulador emite `saved` | El simulador no necesita saber nada del historial (CA-10.8, CA-10.9) | Un servicio compartido de historial | 10, 13 |
| DT-14 | Formulario de alta con formularios reactivos tipados, sin validadores de formato | P-2: solo obligatorios y longitudes; los mensajes de formato los da el backend | Validadores de email e identificador | 8 |
| DT-15 | Pipes puros con la divisa como argumento | Cambiar de divisa vuelve a formatear sin pedir nada (CA-4.3) | Convertir en cada componente | 4, 5 |
| DT-16 | `Intl` con `es-ES` directamente, sin registrar los datos de idioma de Angular | Todo el formato está en funciones puras y no se usan los pipes de Angular | Pipes de moneda y fecha de Angular | 5 |
| DT-17 | Llamar al backend en `127.0.0.1:8000` sin proxy | CORS ya autoriza `http://localhost:4200` (002 RF-9); spec D-1 | Un proxy del servidor de desarrollo | 2 |
| DT-18 | CSS propio, sin biblioteca de componentes; tarjetas apiladas y dos columnas desde 768 px | RNF-3 y RNF-9: nada fuera del proyecto base | Una biblioteca de componentes | RNF-3 |
| DT-19 | Textos en `shared/texts.ts`, en un solo sitio | RNF-5 y tests que comparan con la misma constante, como los mensajes del backend | Textos en cada plantilla | Todos |
| DT-20 | Regiones vivas (`role="status"`) para el total, los avisos y los errores; errores de campo enlazados con `aria-describedby` | RNF-4 y MA-9 | Solo texto visible | RNF-4 |

## 7. Estrategia de tests (tests primero)

**Niveles:**

- **U** (`*.spec.ts` junto a cada función pura): `money.spec.ts`, `numbers.spec.ts` y `dates.spec.ts` (CV-1 a CV-23); `usage-input.spec.ts` y `rates-snapshot.spec.ts` (VE-1 a VE-11); `customer-form-errors.spec.ts`.
- **C** (`*.spec.ts` junto a cada servicio o pantalla): el componente se monta con las rutas reales, las peticiones se responden con el controlador de pruebas HTTP de Angular y el reloj es falso. `exchange-rates.spec.ts` y `currency-bar.spec.ts` (TC, DV-1 y DV-6 a DV-11), `app.spec.ts` (RF-1, TC-13, TC-16), `customer-list-page.spec.ts` (LI, CM-1 a CM-11), `customer-form-page.spec.ts` (AL), `customer-detail-page.spec.ts` (FI), `simulation-history.spec.ts` (HI, CM-12), `simulator-inputs.spec.ts` (SM), `simulator-quote.spec.ts` (CO), `simulator-save.spec.ts` (GU), `currency-on-detail.spec.ts` (DV-2 a DV-5) y `api-errors.spec.ts` (ER).
- **M**: MA-1 a MA-9, en el navegador, con el resultado anotado en `tasks.md`.

**Derivación:** cada tabla de la sección 6 se copia una sola vez, como parámetros con el identificador del caso. Los datos repetidos (cliente Acme, tasas de 5.4, cotización de §8.3, simulación de SI-1) viven en `src/testing/spec-data.ts` (entrada 20 del log). Cada bloque de tests cita «spec 005» y los CA que cubre. Los textos se comparan con las constantes de `texts.ts` y con los literales de la spec, con los espacios normalizados.

**Regla para el backend:** no se toca; su suite se ejecuta al final para confirmarlo.

**Orden** (cada paso empieza en rojo):

1. **Base:** proyecto, lint, arranque de los tests y prototipo (sección 10).
2. **Núcleo (U y C):** formato; reglas de entrada y tasas; cliente de API y errores; tasas y divisa. → RF-2 a RF-5, RF-11 (reglas).
3. **Clientes (C):** cabecera, rutas y página no encontrada; listado y «Cargar más»; alta; ficha. → RF-1, RF-6 a RF-9.
4. **Simulador e historial (C):** historial; valores de entrada; cotización; guardado; divisa en la ficha. → RF-10 a RF-13, RF-4.
5. **Cierre:** errores generales; arranque real y comprobaciones manuales; README y `AGENTS.md`; copia limpia y trazabilidad.

## 8. Trazabilidad

| RF | CA | Parte del plan | Casos |
| --- | --- | --- | --- |
| RF-1 Pantallas | 1.1 a 1.7 | `app.routes.ts`, `app.html`, `not-found-page`, DT-11 | FI-6 a FI-8, TC-13, TC-16, LI-1, AL-1 |
| RF-2 Backend y errores | 2.1 a 2.6 | `api-config`, `request-failure`, DT-6, DT-7, DT-17 | ER-1 a ER-6, LI-15, LI-16, FI-5, AL-13 |
| RF-3 Tasas | 3.1 a 3.13 | §5 tasas, `rates-snapshot`, `browser-storage`, DT-7 | TC-1 a TC-16, VE-5 a VE-11, CV-21 |
| RF-4 Selector | 4.1 a 4.7 | §5 divisa, `currency-bar`, DT-15 | DV-1 a DV-11, CV-22 |
| RF-5 Formato | 5.1 a 5.8 | §5 conversión, DT-3 a DT-5, DT-16 | CV-1 a CV-23, CO-12, ER-2 |
| RF-6 Listado | 6.1 a 6.11 | §5 búsqueda, DT-8 | LI-1 a LI-19 |
| RF-7 «Cargar más» | 7.1 a 7.7 | §5 listas paginadas, DT-9 | CM-1 a CM-12 |
| RF-8 Alta | 8.1 a 8.15 | §5 alta, DT-12, DT-14, `customer-form-errors` | AL-1 a AL-20 |
| RF-9 Ficha | 9.1 a 9.6 | §5 ficha, DT-12 | FI-1 a FI-9 |
| RF-10 Historial | 10.1 a 10.9 | DT-9, DT-13, `tier-table` | HI-1 a HI-9, CM-12, GU-3, GU-4, GU-11 |
| RF-11 Entradas | 11.1 a 11.10 | `usage-input`, DT-10, DT-11 | SM-1 a SM-13, VE-1 a VE-4 |
| RF-12 Cotización | 12.1 a 12.10 | §5 cotización, DT-8 | CO-1 a CO-16, FI-1 |
| RF-13 Guardar | 13.1 a 13.8 | §5 guardar, DT-13 | GU-1 a GU-14 |

Los RNF: RNF-1, regla de capas del lint y CO-12; RNF-2, DT-8 y MA-4; RNF-3, DT-18, MA-1 y MA-2; RNF-4, DT-11, DT-20, MA-3, MA-8 y MA-9; RNF-5, `texts.ts`; RNF-6, LI-19, ER-3 y la regla de `HttpClient` del lint; RNF-7, lint y comprobación de tamaños; RNF-8, la sección 7; RNF-9, `package.json` solo con el proyecto base y angular-eslint; RNF-10, MA-7; RNF-11, README.

## 9. Cumplimiento de la constitución

1. **Simplicidad:** el proyecto base de la CLI más angular-eslint, con su ADR (0010). Nada fuera de la spec.
2. **La spec manda:** cada tarea cita sus RF y CA; los commits, cuando el autor los autorice, también.
3. **Capas:** el frontend no calcula importes (RNF-1); las reglas puras no importan Angular; solo `core/` habla HTTP. El lint lo impide.
4. **Dinero exacto:** los importes llegan en céntimos de EUR y solo se convierten para mostrarlos, con enteros grandes y redondeo explícito (DT-3). Nunca se envían ni se guardan convertidos.
5. **Tests y revisión:** tests primero en U y C; las comprobaciones M quedan anotadas; las correcciones al código generado se anotan en el log.
6. **Calidad, seguridad e idioma:** TypeScript estricto sin `any` y lint sin errores; los textos del exterior se muestran como texto literal; interfaz en español y código en inglés.

## 10. Lo que reveló el prototipo

Comprobado con Node 22.11 (ICU 75.1), antes de este plan:

| Comprobación | Resultado | Consecuencia |
| --- | --- | --- |
| Moneda `es-ES` con 2 decimales y agrupación siempre | «1.234,56 €», «1.234,56 US$», «1.234,56 GBP», «1.234,56 CHF», «1.234,56 JPY», con espacio no separable | CA-5.4 se cumple con `Intl`; los tests normalizan el espacio |
| Agrupación por defecto con 4 cifras | «1234»; con `useGrouping: "always"`, «1.234» | DT-5 |
| Porcentaje `es-ES` con hasta 2 decimales | «21 %», «19,5 %», «21,25 %», «0 %», «100 %», «0,01 %» | CA-5.5 con `Intl` |
| Fecha y hora con `Europe/Madrid` | «17/11/2026, 00:30» y «01/07/2026, 12:00» | DT-4: se compone sin la coma |
| `String(1.005)` y `JSON.parse("1.005")` | `"1.005"` y `1.005` | DT-3: la escritura decimal más corta recupera la tasa exacta |

Comprobado en T-01 (17/11/2026) con Node 26.13.1 (ICU 78.3), Angular CLI 22.2.7, TypeScript 6.0, Vitest 5.1 con jsdom y angular-eslint 22.7, en un prototipo fuera del repositorio, ya borrado:

| Comprobación | Resultado | Consecuencia |
| --- | --- | --- |
| Las salidas de `Intl` de la tabla anterior con ICU 78.3 | Idénticas | Nada cambia |
| Tipos de TypeScript para `useGrouping: "always"` e importes como texto en `Intl.NumberFormat` | El proyecto generado usa la biblioteca de ES2022 y no los admite: error de compilación | `tsconfig.json` declara `"lib": ["es2023", "dom"]`. Los navegadores de RNF-10 lo admiten |
| Zona fijada en el archivo de arranque de los tests (`vi.stubEnv('TZ', 'Europe/Madrid')`) | `Intl` y `Date` usan Madrid: «17/11/2026, 00:30» y «12:00» en verano | DT-2 se cumple con `src/test-setup.ts`, declarado en `setupFiles` de `angular.json` |
| Reloj falso de Vitest con `debounceTime(300)` y `timeout(10 000)` | 299 ms sin emitir y 300 ms emite; a los 9 999 ms nada y a los 10 000 ms `TimeoutError`, que cancela la petición | DT-7 y DT-8 se prueban con `vi.useFakeTimers()` |
| `switchMap` con el controlador de pruebas HTTP | La petición anterior queda `cancelled` y su respuesta no llega | LI-12 y CO-5 comprueban la cancelación |
| Aplicación sin zona (opción por defecto de Angular 22) bajo el reloj falso | Los cambios de signals se pintan solos tras `await vi.advanceTimersByTimeAsync(0)` | Los tests C avanzan el reloj con la versión asíncrona |
| Navegación con estado en las pruebas de rutas | `router.currentNavigation()?.extras.state` llega a la pantalla al crearse; `history.state` vale `null` en el DOM simulado; al salir y volver, el estado ya no está | DT-12: la ficha lee T-REG de la navegación en curso al crearse, no de `history.state` |
| Botón desactivado | `click()` no dispara su acción | CM-6, AL-15 y GU-5 se prueban con el botón real |
| Slider nativo en el DOM simulado | `type="range"` con `min`, `max` y `step`; un valor de 250 queda en 200 | SM-4 se comprueba en el control |
| Lo que genera la CLI | `app.ts`, `app.html`, `app.css`, `app.config.ts`, `app.routes.ts` y `app.spec.ts` (sin el sufijo `.component`); scripts `start`, `build`, `watch` y `test`; dependencias de desarrollo `@angular/build`, `@angular/cli`, `@angular/compiler-cli`, `jsdom`, `prettier`, `typescript` y `vitest`; carpeta `.vscode/` | Los nombres de la sección 2 coinciden. `angular-eslint` añade el script `lint` y sus dependencias `eslint`, `typescript-eslint` y `@eslint/js` (ADR 0010) |
| `ng test` | Por defecto vigila los cambios en un terminal interactivo y no aísla los archivos de test entre sí | `angular.json` fija `watch: false`, así que `npm test` hace una sola pasada, como `pytest`. Cada test limpia el almacenamiento del navegador |
| Archivos solo de tests en la compilación | `src/test-setup.ts` usa `vi` y rompía la compilación de producción | `tsconfig.app.json` excluye `src/test-setup.ts` y `src/testing/`; `tsconfig.spec.json` los incluye |
| Lint con las reglas de capas | Falla con `any`, con `HttpClient` fuera de `core/`, con Angular o RxJS en un módulo puro y con una función de 44 líneas; un `HttpClient` dentro de `core/` pasa | Reglas del ADR 0010 más `max-lines` (300) y `max-lines-per-function` (40, salvo en los `*.spec.ts`, cuyos `describe` agrupan casos) |
