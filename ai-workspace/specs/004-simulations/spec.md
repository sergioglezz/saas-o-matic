# 004 — Simulaciones: guardado e historial

Estado: v1.0 aprobada por el autor, con las decisiones D-1 a D-11 confirmadas · Fuente de verdad: `ai-workspace/specs/00-spec-first.md` · Constitución: `ai-workspace/docs/constitution.md` · Depende de: specs 001 (v1.2), 002 (v1.1) y 003 (v1.0), todas completadas

Leyenda de origen: **[E]** viene del enunciado y no se puede contradecir; **[P]** es una propuesta del documento 00 o una decisión tomada al redactar esta spec. Las decisiones nuevas están en la sección 11 para que el autor las confirme o las cambie.

## 1. Contexto y objetivo

El comercial simula el consumo de un cliente, guarda la simulación y consulta después su historial (UC-4, UC-5 y UC-3). Es el segundo de los dos `POST` obligatorios del enunciado. La cotización en vivo (002) ya calcula sin guardar; esta spec guarda ese mismo cálculo junto al cliente y lo devuelve en su historial.

**Objetivo:** exponer `POST /simulations` y `GET /customers/{id}/simulations` sobre las tablas `simulations` y `simulation_tiers`, con una instantánea del cálculo de 001 que no cambia aunque cambien después las tasas o las tarifas (RN-8), y el formato único de error de 002 y 003. Incluye simulaciones de demostración en el seed.

**Cierra dos decisiones aplazadas:** el nombre del campo de usuarios (001 D-1) y qué ocurre con un cliente cuyo país deja de estar soportado (003 D-7).

## 2. Usuarios

- **Comercial** (único usuario, sin autenticación): guarda simulaciones y consulta el historial de un cliente.
- **Dashboard Angular** (consumidor técnico): el simulador guarda con `POST /simulations` y la ficha del cliente pinta el historial. Ambos se construyen en una spec de frontend posterior.
- **Evaluadores** (audiencia indirecta): prueban los endpoints desde `/docs` y ven historiales de ejemplo tras cargar el seed.

## 3. Historias de usuario

- **HU-1.** Como comercial, quiero guardar la simulación que estoy viendo, para presentársela al cliente más adelante.
- **HU-2.** Como comercial, quiero que una simulación guardada muestre siempre las mismas cifras, para que un presupuesto enviado no cambie solo.
- **HU-3.** Como comercial, quiero ver las simulaciones de un cliente de la más reciente a la más antigua, para retomar la última conversación.
- **HU-4.** Como evaluador, quiero ver historiales de ejemplo tras cargar el seed, para probar el dashboard sin crear datos a mano.

## 4. Requisitos funcionales

### RF-1. Guardar una simulación

Origen: §3 y §8.2 `POST /simulations` **[E]**, UC-5, §8.3 **[P]**.

- **CA-1.1** Cuando recibe una petición válida en `POST /simulations` para un cliente existente con país soportado, el sistema deberá guardar la simulación y responder 201 con `id`, `customer_id`, `active_users`, `storage_gb`, `api_calls_per_month`, la instantánea del cálculo (RF-4) y `created_at`, con el formato de la sección 5.
- **CA-1.2** El sistema deberá asignar como `id` un entero positivo creciente que no se reutiliza, y como `created_at` el instante del guardado con el formato de 003 CA-1.3 (`2026-11-16T10:00:00Z`).
- **CA-1.3** Cuando una simulación se ha guardado, el sistema deberá devolverla con los mismos datos en el historial de su cliente (RF-5).
- **CA-1.4** Si la petición no es válida, el cliente no existe o su país no está soportado, entonces el sistema no deberá guardar nada.
- **CA-1.5** El sistema deberá guardar la simulación y su desglose por tramo de una sola vez: si falla cualquier parte del guardado, no queda ni la simulación ni ninguna fila de su desglose.
- **CA-1.6** Guardar una simulación no deberá modificar el cliente ni las tasas de impuesto.

### RF-2. Validación de la petición

Origen: §3 y §8.3 **[E]** para los campos, RN-2 y RN-9 **[P]** para los rangos. Reutiliza sin cambios la definición de entero JSON de 002 RF-2, el cuerpo de la petición de 002 RF-7 y los campos no definidos de 002 RF-5.

- **CA-2.1** `customer_id` deberá ser un entero JSON entre 1 y 9 223 372 036 854 775 807. Si no, detalle `{field: "customer_id", message: "Debe ser un número entero positivo"}`.
- **CA-2.2** `active_users` deberá cumplir lo mismo que `users` en la cotización (002 CA-2.1 y CA-2.2): entero JSON entre 0 y 100 000, con `-0` tratado como 0. Si no, detalle `{field: "active_users", message: "Debe ser un número entero entre 0 y 100000"}`.
- **CA-2.3** `storage_gb` deberá ser un entero JSON entre 0 y 1 000 000. Si no, detalle `{field: "storage_gb", message: "Debe ser un número entero entre 0 y 1000000"}`.
- **CA-2.4** `api_calls_per_month` deberá ser un entero JSON entre 0 y 1 000 000 000. Si no, detalle `{field: "api_calls_per_month", message: "Debe ser un número entero entre 0 y 1000000000"}`.
- **CA-2.5** Si falta alguno de los cuatro campos, entonces el sistema deberá responder 422 con el detalle `{field: <campo>, message: "Campo obligatorio"}`.
- **CA-2.6** Si el objeto incluye un campo distinto de los cuatro definidos, entonces el sistema deberá responder 422 con `{field: <nombre>, message: "Campo no permitido"}` por cada uno. Esto incluye `users`, `country`, cualquier importe (`subtotal_cents`, `total_cents`…), `id`, `created_at` y los nombres con otras mayúsculas: el cliente nunca envía precios ni totales (§8.1).
- **CA-2.7** Si el cuerpo no es un objeto JSON con `Content-Type: application/json`, entonces el sistema deberá responder 422 con el único detalle `{field: "body", message: "El cuerpo debe ser un objeto JSON"}` (002 CA-7.1 a CA-7.3).
- **CA-2.8** El sistema deberá informar a la vez de todos los campos inválidos, con un único detalle por campo y sin orden garantizado (002 CA-6.3 y CA-6.4).

### RF-3. Cliente de la simulación

Origen: §8.2 (`POST /simulations` responde 404) **[E]**, 003 D-7 **[P]**.

- **CA-3.1** Si `customer_id` es válido pero no existe ningún cliente con ese `id`, entonces el sistema deberá responder 404 con `code` = `not_found`, `message` «Recurso no encontrado» y `details` vacío.
- **CA-3.2** Si la petición tiene algún error de validación (RF-2), entonces el sistema deberá responder 422 con esos errores, sin comprobar si el cliente existe.
- **CA-3.3** El sistema deberá calcular la simulación con el país guardado en el cliente; la petición no lleva país (CA-2.6).
- **CA-3.4** Si el país del cliente no tiene ahora tasa configurada (001 CA-4.6), entonces el sistema deberá responder 422 con el único detalle `{field: "customer_id", message: "El país del cliente no está soportado"}`.

### RF-4. Instantánea del cálculo

Origen: RN-8 **[P]**, constitución principio 4, §8.3 «la misma instantánea de precio que `POST /pricing/quote`» **[P]**, ADR 0004.

- **CA-4.1** El sistema deberá obtener los importes del cálculo de 001 para `active_users` y el país del cliente, igual que la cotización: con los mismos datos y la misma configuración de tasas, `currency`, `tiers`, `subtotal_cents`, `tax_rate_bp`, `tax_cents` y `total_cents` coinciden exactamente con los de `POST /pricing/quote` para `{users: active_users, country: <país del cliente>}`.
- **CA-4.2** El sistema deberá guardar, por simulación, la tasa aplicada, el subtotal, el impuesto, el total y una fila por cada uno de los 3 tramos con su número, sus límites (`from_users`, `to_users`), sus unidades, su precio unitario y su importe.
- **CA-4.3** Cuando se cambia la tasa de un país después de guardar una simulación, el sistema deberá seguir devolviendo esa simulación con la tasa y los importes con que se guardó. Las simulaciones nuevas usan la tasa nueva (001 CA-13.2).
- **CA-4.4** Cuando el país de un cliente deja de estar soportado, el sistema deberá seguir devolviendo sus simulaciones ya guardadas.
- **CA-4.5** El sistema deberá devolver las simulaciones guardadas desde lo que guardó, sin volver a calcularlas.
- **CA-4.6** `storage_gb` y `api_calls_per_month` no deberán cambiar ningún importe (RN-9).
- **CA-4.7** El sistema deberá devolver todos los números como enteros JSON, `"currency": "EUR"` y el límite superior abierto del tramo 3 como `"to_users": null` (002 CA-4.1, CA-4.3 y CA-4.4).

### RF-5. Historial de un cliente

Origen: §3 «historial de simulaciones de un cliente, de más reciente a más antigua» **[E]**, §8.2 `GET /customers/{id}/simulations` **[P]**.

- **CA-5.1** Cuando recibe `GET /customers/{id}/simulations` y el cliente existe, el sistema deberá responder 200 con `{"items": [...], "total": n}`, donde cada elemento es el mismo objeto que devolvió el 201 de esa simulación.
- **CA-5.2** El sistema deberá incluir solo las simulaciones de ese cliente, ordenadas por `created_at` de la más reciente a la más antigua y, a igualdad, por `id` descendente.
- **CA-5.3** El sistema deberá paginar con `limit` y `offset` con las mismas reglas, valores por defecto y mensajes que `GET /customers` (003 CA-5.6, CA-5.8, CA-5.10 y CA-5.11), y devolver en `total` el número de simulaciones del cliente sin aplicar la paginación.
- **CA-5.4** Cuando el cliente existe pero no tiene simulaciones, el sistema deberá responder 200 con `items` vacío y `total` = 0.
- **CA-5.5** Si no existe ningún cliente con ese `id`, o `{id}` no es un identificador según 003 CA-6.3, entonces el sistema deberá responder 404 `not_found` «Recurso no encontrado» con `details` vacío, aunque `limit` u `offset` tampoco sean válidos.
- **CA-5.6** `GET /customers/{id}` no cambia: sigue devolviendo solo los datos del cliente (003 RF-6).

### RF-6. Protocolo, errores y CORS en las rutas nuevas

Origen: 002 RF-6, RF-8 y RF-9; 003 RF-7 y RF-8 **[P]**. No cambia nada de lo que ya cumplen.

- **CA-6.1** Las dos rutas deberán cumplir el formato único de error (002 RF-6 y 003 RF-7): 404 con barra final y sin redirección, 500 `internal_error` sin detalles internos y `Content-Type: application/json` en éxitos y errores.
- **CA-6.2** Si llega un método no admitido que no es una preflight de CORS, entonces el sistema deberá responder 405 `method_not_allowed` con `Allow: POST` en `/simulations` y `Allow: GET` en `/customers/{id}/simulations`. Las rutas existentes conservan su `Allow`.
- **CA-6.3** Cuando llega un `POST` a `/simulations` o un `GET` al historial desde el origen del frontend, el sistema deberá incluir `Access-Control-Allow-Origin` con ese origen y aceptar su preflight (200). Desde otro origen, no deberá incluir esa cabecera.

### RF-7. Persistencia

Origen: §8.5 **[P]** (ampliado por la decisión D-3), constitución principio 4.

- **CA-7.1** El sistema deberá crear las tablas `simulations` y `simulation_tiers` con una migración nueva, sin modificar las migraciones 0001 y 0002. Una base de datos recién preparada no tiene ninguna simulación.
- **CA-7.2** La base de datos deberá rechazar por sí misma:
  - una simulación de un cliente inexistente, o una fila de desglose de una simulación inexistente;
  - `active_users`, `storage_gb` o `api_calls_per_month` que no sean enteros dentro de los rangos de RF-2;
  - importes negativos o que no sean enteros, una `tax_rate_bp` fuera de 0 a 10 000, o un `total_cents` distinto de `subtotal_cents` + `tax_cents`;
  - un número de tramo fuera de 1 a 3, o dos filas con el mismo tramo para una simulación;
  - cualquier columna vacía (`NULL`), salvo `to_users`.
- **CA-7.3** La base de datos deberá rechazar borrar un cliente que tiene simulaciones.
- **CA-7.4** Deshacer la migración deberá borrar `simulations` y `simulation_tiers` y dejar intactas `customers` y `tax_rates`.
- **CA-7.5** El sistema deberá tener un índice por (`customer_id`, `created_at`) para el historial (§8.5).

### RF-8. Datos de demostración

Origen: §3 «carga datos de demostración con un script de seed» **[P]**, 003 D-12.

- **CA-8.1** Cuando se ejecuta `python -m app.db.seed`, el sistema deberá crear, además de los clientes de 003, las 6 simulaciones de la tabla de la sección 6.9, que cubren los tres tramos y un país con tasa 0.
- **CA-8.2** El sistema deberá crear las simulaciones de un cliente de demostración solo si ese cliente, buscado por su `tax_id`, no tiene ninguna simulación. Así el seed se puede repetir sin duplicar nada y completa una base de datos que ya tenía los clientes de 003.
- **CA-8.3** Las simulaciones de demostración deberán pasar por las mismas reglas y el mismo cálculo que `POST /simulations`.
- **CA-8.4** El seed no deberá modificar los clientes, las tasas ni las simulaciones que ya existan.

## 5. Contrato observable

Convenciones de §8.1: JSON en UTF-8, campos en `snake_case`, fechas ISO 8601 UTC, importes en céntimos y tasas en puntos básicos.

**`POST /simulations`**: calcula y guarda una simulación. Cabecera `Content-Type: application/json`.

| Campo | Tipo | Regla |
| --- | --- | --- |
| `customer_id` | entero JSON | 1 a 9 223 372 036 854 775 807; el cliente debe existir |
| `active_users` | entero JSON | 0 a 100 000 |
| `storage_gb` | entero JSON | 0 a 1 000 000 |
| `api_calls_per_month` | entero JSON | 0 a 1 000 000 000 |

Petición (§8.3):

```json
{
  "customer_id": 1,
  "active_users": 15,
  "storage_gb": 200,
  "api_calls_per_month": 50000
}
```

Respuesta `201`, para un cliente de `ES` y con el reloj en `2026-11-16T10:00:00Z`:

```json
{
  "id": 1,
  "customer_id": 1,
  "active_users": 15,
  "storage_gb": 200,
  "api_calls_per_month": 50000,
  "currency": "EUR",
  "tiers": [
    { "tier": 1, "from_users": 1,  "to_users": 10,   "units": 10, "unit_price_cents": 1000, "amount_cents": 10000 },
    { "tier": 2, "from_users": 11, "to_users": 50,   "units": 5,  "unit_price_cents": 800,  "amount_cents": 4000 },
    { "tier": 3, "from_users": 51, "to_users": null, "units": 0,  "unit_price_cents": 500,  "amount_cents": 0 }
  ],
  "subtotal_cents": 14000,
  "tax_rate_bp": 2100,
  "tax_cents": 2940,
  "total_cents": 16940,
  "created_at": "2026-11-16T10:00:00Z"
}
```

La instantánea (`currency` a `total_cents`) es la respuesta de la cotización sin `users`, que ya viene en `active_users` (decisión D-2).

**`GET /customers/{id}/simulations?limit=&offset=`**: historial del cliente. Respuesta `200`:

```json
{
  "items": [ { "id": 1, "customer_id": 1, "active_users": 15, "...": "el mismo objeto del 201" } ],
  "total": 1
}
```

| Parámetro | Por defecto | Regla |
| --- | --- | --- |
| `limit` | 50 | Entero de 1 a 100, solo dígitos |
| `offset` | 0 | Entero de 0 a 1 000 000, solo dígitos |

**Respuestas**

| HTTP | `code` | `message` | Cuándo |
| --- | --- | --- | --- |
| 201 | — | — | Simulación guardada |
| 200 | — | — | Historial; también una preflight de CORS aceptada |
| 404 | `not_found` | Recurso no encontrado | Cliente inexistente (en el cuerpo o en la ruta), `{id}` que no es un identificador, ruta inexistente o con barra final |
| 405 | `method_not_allowed` | Método no permitido | Método que la ruta no admite (con `Allow`) |
| 422 | `validation_error` | Datos no válidos | Cualquier fallo de RF-2, CA-3.4 o de `limit` y `offset` |
| 500 | `internal_error` | Error interno del servidor | Fallo inesperado |

**Mensajes de `details`** (únicos textos posibles en estas rutas):

| `field` | `message` | Abreviatura |
| --- | --- | --- |
| cualquiera de los cuatro | Campo obligatorio | OBL |
| `customer_id` | Debe ser un número entero positivo | CID |
| `customer_id` | El país del cliente no está soportado | CNS |
| `active_users` | Debe ser un número entero entre 0 y 100000 | USR |
| `storage_gb` | Debe ser un número entero entre 0 y 1000000 | STO |
| `api_calls_per_month` | Debe ser un número entero entre 0 y 1000000000 | APC |
| (nombre del campo) | Campo no permitido | NPE |
| `body` | El cuerpo debe ser un objeto JSON | BODY |
| `limit` | Debe ser un número entero entre 1 y 100 | LIM |
| `offset` | Debe ser un número entero entre 0 y 1000000 | OFF |

## 6. Casos de prueba

Niveles: **U** = función pura, sin base de datos ni servidor; **D** = con una base de datos de prueba migrada, sin servidor; **I** = petición HTTP. Las cifras están comprobadas con código.

**Clientes de partida** de las tablas 6.1 a 6.6, creados por la API en este orden, con las tasas por defecto (001 CA-4.3):

| `id` | `company_name` | `tax_id` | `country` | Tasa |
| --- | --- | --- | --- | --- |
| 1 | Acme Telecom S.L. | B12345674 | ES | 2100 |
| 2 | Lusitânia Cloud Lda | PT123456789 | PT | 2300 |
| 3 | Nordwind Systeme GmbH | DE123456789 | DE | 1900 |
| 4 | Hexagone Réseaux SAS | FR12345678901 | FR | 2000 |
| 5 | Albion Connect Ltd | GB123456789 | GB | 2000 |
| 6 | Liberty Mesh Inc. | US123456789 | US | 0 |

### 6.1 Guardados válidos · I · con el reloj fijado en `2026-11-16T10:00:00Z`

Salvo que se indique otra cosa, `storage_gb` = 200 y `api_calls_per_month` = 50 000.

| # | `customer_id` | `active_users` | `subtotal_cents` | `tax_rate_bp` | `tax_cents` | `total_cents` |
| --- | --- | --- | --- | --- | --- | --- |
| SI-1 | 1 | 15 | 14000 | 2100 | 2940 | 16940 (exactamente la respuesta de la sección 5) |
| SI-2 | 1 | 0 | 0 | 2100 | 0 | 0 (los tres tramos con 0 unidades) |
| SI-3 | 2 | 1 | 1000 | 2300 | 230 | 1230 |
| SI-4 | 3 | 11 | 10800 | 1900 | 2052 | 12852 |
| SI-5 | 6 | 15 | 14000 | 0 | 0 | 14000 |
| SI-6 | 4 | 51 | 42500 | 2000 | 8500 | 51000 |
| SI-7 | 1 | 60 | 47000 | 2100 | 9870 | 56870 (tramos: 10/10000, 40/32000, 10/5000) |
| SI-8 | 5 | 100 | 67000 | 2000 | 13400 | 80400 |
| SI-9 | 1 | 100000, con `storage_gb` 1000000 y `api_calls_per_month` 1000000000 | 50017000 | 2100 | 10503570 | 60520570 |

| # | Situación | Resultado esperado |
| --- | --- | --- |
| SI-10 | SI-1 con `storage_gb` 0 y `api_calls_per_month` 0 | 201 |
| SI-11 | Dos guardados seguidos | `id` 1 y 2 |
| SI-12 | SI-1 con `active_users` escrito como `-0` | 201 con `active_users` = 0 y los importes de SI-2 |
| SI-13 | SI-1 y después `GET /customers/1` y `GET /customers` | El cliente no ha cambiado |

### 6.2 Instantánea · I

| # | Situación | Resultado esperado |
| --- | --- | --- |
| SN-1 | Cada caso SI-1 a SI-9 comparado con `POST /pricing/quote` para `{users: active_users, country: <país del cliente>}` | `currency`, `tiers`, `subtotal_cents`, `tax_rate_bp`, `tax_cents` y `total_cents` idénticos |
| SN-2 | Tres guardados con 15 usuarios para el cliente 1: 200/50000, 0/0 y 1000000/1000000000 | Los tres con los mismos importes (RN-9) |
| SN-3 | SI-1, cambiar la tasa de ES a 2150 y leer el historial del cliente 1 | La simulación sigue con 2100, 2940 y 16940 |
| SN-4 | Tras SN-3, guardar otra vez SI-1 | 2150, 3010 y 17010 |
| SN-5 | SI-3, quitar la tasa de PT y leer el historial del cliente 2 | 200 con la simulación de SI-3 intacta |

### 6.3 Errores de validación del guardado · I · todos 422 `validation_error` «Datos no válidos»

Salvo que se indique otra cosa, los campos que no aparecen llevan los valores de SI-1.

| # | Cambio sobre SI-1 | `details` esperado (como conjunto) |
| --- | --- | --- |
| SV-1 | Cuerpo `{}` | los cuatro campos / OBL |
| SV-2 | `customer_id` `"1"` (texto) | customer_id/CID |
| SV-3 | `customer_id` 0 y, en otra petición, -1 | customer_id/CID en las dos |
| SV-4 | `customer_id` `1.0`, `1e0`, `true` y `null` | customer_id/CID en las cuatro |
| SV-5 | `customer_id` 9223372036854775808 | customer_id/CID |
| SV-6 | `active_users` 100001 y, en otra petición, -1 | active_users/USR en las dos |
| SV-7 | `active_users` `15.5`, `1e1`, `"15"` y `null` | active_users/USR en las cuatro |
| SV-8 | `storage_gb` -1 y 1000001 | storage_gb/STO en las dos |
| SV-9 | `storage_gb` `1.5`, `"200"` y `false` | storage_gb/STO en las tres |
| SV-10 | `api_calls_per_month` -1 y 1000000001 | api_calls_per_month/APC en las dos |
| SV-11 | `api_calls_per_month` `2.0` y `[]` | api_calls_per_month/APC en las dos |
| SV-12 | `users` en lugar de `active_users` | users/NPE, active_users/OBL |
| SV-13 | Campos añadidos `total_cents` 0 y `country` `ES` | total_cents/NPE, country/NPE |
| SV-14 | Campos añadidos `id` y `created_at` | id/NPE, created_at/NPE |
| SV-15 | `Active_Users` en lugar de `active_users` | Active_Users/NPE, active_users/OBL |
| SV-16 | Los cuatro campos inválidos (`"x"`, -1, -1, -1) | customer_id/CID, active_users/USR, storage_gb/STO, api_calls_per_month/APC |
| SV-17 | Cuerpo `no es json`, cuerpo `[1]` y cuerpo válido con `Content-Type: text/plain` | body/BODY en los tres |
| SV-18 | `customer_id` 999 (inexistente) y `active_users` -1 | active_users/USR, sin 404 (CA-3.2) |

Tras cada caso, el historial del cliente 1 tiene `total` = 0 (CA-1.4).

### 6.4 Cliente de la simulación · I

| # | Situación | Resultado esperado |
| --- | --- | --- |
| SC-1 | SI-1 con `customer_id` 999 | 404 `not_found` «Recurso no encontrado», `details` vacío |
| SC-2 | SI-1 con `customer_id` 9223372036854775807 | El mismo 404, sin error interno |
| SC-3 | Quitar la tasa de PT y guardar una simulación del cliente 2 | 422 con customer_id/CNS |
| SC-4 | Tras SC-1 a SC-3, leer los historiales de los clientes 1 y 2 | `total` = 0 en los dos |

### 6.5 Historial · I

Datos de partida: con el reloj en `10:00:00Z`, SI-1 para el cliente 1 (`id` 1); con el reloj en `10:05:00Z`, SI-7 (`id` 2) y SI-2 (`id` 3) para el cliente 1 y SI-3 (`id` 4) para el cliente 2. El cliente 3 no tiene simulaciones.

| # | Petición | `id` de `items`, en orden | `total` |
| --- | --- | --- | --- |
| HI-1 | `GET /customers/1/simulations` | 3, 2, 1 | 3 |
| HI-2 | `GET /customers/2/simulations` | 4 | 1 |
| HI-3 | `GET /customers/3/simulations` | (vacío) | 0 |
| HI-4 | `GET /customers/1/simulations?limit=2` | 3, 2 | 3 |
| HI-5 | `GET /customers/1/simulations?limit=2&offset=2` | 1 | 3 |
| HI-6 | `GET /customers/1/simulations?offset=3` | (vacío) | 3 |
| HI-7 | `GET /customers/1/simulations?limit=1&limit=2` | 3, 2 | 3 |
| HI-8 | `GET /customers/1/simulations?desconocido=1` | 3, 2, 1 | 3 |

| # | Petición o situación | Resultado esperado |
| --- | --- | --- |
| HI-9 | Cada elemento de HI-1 y HI-2 | Igual, campo a campo, al 201 de su guardado |
| HI-10 | `GET /customers/999/simulations` | 404 `not_found`, `details` vacío |
| HI-11 | `{id}` = `abc`, `0`, `-1`, `1.5`, `01` y `99999999999999999999` | El mismo 404 en los seis, sin error interno |
| HI-12 | `GET /customers/1/simulations/` (barra final) | El mismo 404, sin redirección |
| HI-13 | `GET /customers/1` tras HI-1 | 200 con los datos del cliente, sin simulaciones (CA-5.6) |

### 6.6 Parámetros inválidos del historial · I · con los datos de 6.5

| # | Petición | Resultado esperado |
| --- | --- | --- |
| HP-1 | `limit=0`, `limit=101`, `limit=abc`, `limit=` y `limit=%2B5` sobre el cliente 1 | 422 con limit/LIM en las cinco |
| HP-2 | `offset=-1`, `offset=1000001` y `offset=x` sobre el cliente 1 | 422 con offset/OFF en las tres |
| HP-3 | `limit=0&offset=-1` sobre el cliente 1 | 422 con limit/LIM y offset/OFF |
| HP-4 | `limit=0` sobre el cliente 999 y sobre `{id}` = `abc` | 404 en los dos (CA-5.5) |

### 6.7 Protocolo, errores globales y CORS · I

| # | Petición o situación | Resultado esperado |
| --- | --- | --- |
| ER-1 | `GET`, `PUT`, `PATCH`, `DELETE` y `OPTIONS` sin preflight sobre `/simulations` | 405 `method_not_allowed`, `details` vacío, `Allow: POST` |
| ER-2 | `HEAD /simulations` | 405 con `Allow: POST` y sin cuerpo |
| ER-3 | `POST`, `PUT`, `PATCH` y `DELETE` sobre `/customers/1/simulations` | 405 con `Allow: GET` |
| ER-4 | `POST /simulations/` (barra final) | 404 `not_found`, sin redirección |
| ER-5 | Fallo interno forzado (almacén de simulaciones no disponible) en las dos rutas | 500 `internal_error`, `details` vacío, sin «Traceback», rutas de archivo ni nombres de módulos |
| ER-6 | SI-1 con `Origin: http://localhost:4200` | 201 con `Access-Control-Allow-Origin: http://localhost:4200` |
| ER-7 | Preflight de `POST /simulations` y de `GET /customers/1/simulations` desde `http://localhost:4200` | 200 con `Access-Control-Allow-Origin` |
| ER-8 | SI-1 y la preflight de ER-7 con `Origin: http://otro-origen.example` | Sin `Access-Control-Allow-Origin` |
| ER-9 | Respuestas de SI-1, HI-1, SV-1, SC-1, HI-10 y ER-1 | `Content-Type: application/json` |
| ER-10 | Métodos no permitidos sobre `/customers`, `/customers/1` y `/pricing/quote` | Siguen dando `Allow: GET, POST`, `Allow: GET` y `Allow: POST` |

### 6.8 Persistencia · D

| # | Acción | Resultado esperado |
| --- | --- | --- |
| DB-1 | Preparar una base de datos vacía | Existen `simulations` y `simulation_tiers`, con 0 filas |
| DB-2 | Guardar una simulación con sus 3 tramos y leerla | Mismos valores que se guardaron, con `to_users` nulo en el tramo 3 |
| DB-3 | Insertar directamente una simulación de un cliente inexistente, y un tramo de una simulación inexistente | Rechazadas |
| DB-4 | Insertar directamente una simulación con `active_users` -1 y otra con 100001; lo mismo con `storage_gb` y `api_calls_per_month` en sus límites | Rechazadas |
| DB-5 | Insertar directamente una simulación con `active_users` 1.5 | Rechazada |
| DB-6 | Insertar directamente una simulación con `total_cents` distinto de `subtotal_cents` + `tax_cents`, otra con un importe negativo y otra con `tax_rate_bp` 10001 | Rechazadas |
| DB-7 | Insertar directamente un tramo 0, un tramo 4 y dos filas del tramo 1 para la misma simulación | Rechazados |
| DB-8 | Insertar directamente filas con una columna `NULL` (salvo `to_users`) | Rechazadas |
| DB-9 | Borrar un cliente que tiene simulaciones | Rechazado; el cliente y sus simulaciones siguen |
| DB-10 | Forzar un fallo al guardar el segundo tramo | No queda la simulación ni ningún tramo (CA-1.5) |
| DB-11 | Borrar la última simulación y guardar otra | El nuevo `id` no reutiliza el borrado |
| DB-12 | Deshacer la migración de simulaciones | Desaparecen las dos tablas; `customers` conserva sus filas y `tax_rates` sus 7 tasas |
| DB-13 | Comparar los modelos con la base de datos migrada | Sin diferencias, índice de CA-7.5 incluido |

### 6.9 Datos de demostración · D

Simulaciones de demostración (clientes de 003 RF-10):

| Cliente (`tax_id`) | `active_users` | `storage_gb` | `api_calls_per_month` | `total_cents` |
| --- | --- | --- | --- | --- |
| Acme Telecom S.L. (B12345674, ES) | 15 | 200 | 50000 | 16940 |
| Acme Telecom S.L. (B12345674, ES) | 60 | 500 | 250000 | 56870 |
| Lusitânia Cloud Lda (PT123456789, PT) | 1 | 10 | 1000 | 1230 |
| Nordwind Systeme GmbH (DE123456789, DE) | 11 | 100 | 20000 | 12852 |
| Albion Connect Ltd (GB123456789, GB) | 100 | 1000 | 1000000 | 80400 |
| Liberty Mesh Inc. (US123456789, US) | 51 | 300 | 100000 | 42500 |

| # | Acción | Resultado esperado |
| --- | --- | --- |
| SE-1 | Ejecutar el seed sobre una base de datos preparada | 10 clientes y las 6 simulaciones de la tabla |
| SE-2 | Ejecutarlo otra vez | Siguen siendo 10 clientes y 6 simulaciones |
| SE-3 | Ejecutarlo sobre una base de datos con los 10 clientes de demostración y ninguna simulación | Crea las 6 simulaciones y ningún cliente |
| SE-4 | Ejecutarlo cuando Acme Telecom ya tiene una simulación creada por la API | Acme conserva solo la suya; los otros 4 clientes reciben sus simulaciones |
| SE-5 | Comparar cada simulación de demostración con la cotización de sus usuarios y su país | Importes idénticos |
| SE-6 | Leer las tasas y los clientes antes y después | Sin cambios |

## 7. Requisitos no funcionales

- **RNF-1 Capas:** los importes salen del servicio de cotización de 001; ni el router ni el repositorio calculan nada (constitución, principio 3; ADR 0004). El acceso a `simulations` y `simulation_tiers` vive solo en la capa de repositorio, y los routers no llegan a la base de datos (003 RNF-1).
- **RNF-2 Una sola fuente de verdad:** el cálculo de una simulación y el de la cotización son el mismo código (SN-1, SE-5).
- **RNF-3 Seguridad:** consultas solo mediante el ORM; toda entrada validada con Pydantic en modo estricto; el cliente no puede enviar importes (CA-2.6); los errores no exponen trazas, rutas ni nombres internos (ER-5).
- **RNF-4 Idioma:** los únicos textos de error posibles son los de la sección 5, en español; los nombres de campo, en inglés y `snake_case`.
- **RNF-5 Documentación:** los dos endpoints aparecen en la documentación interactiva con su ejemplo de petición y de respuesta, incluido `"to_users": null`.
- **RNF-6 Simplicidad:** no se añade ninguna dependencia.

## 8. Casos límite

- **Cero usuarios:** se guarda con todos los importes a 0 (SI-2, SI-12).
- **Máximos:** 100 000 usuarios y los máximos de almacenamiento y llamadas (SI-9); un valor por encima se rechaza (SV-6, SV-8, SV-10).
- **Tipos parecidos a enteros:** `1.0`, `1e0`, textos, booleanos y `null` se rechazan en los cuatro campos (SV-2 a SV-11).
- **Importes enviados por el cliente:** se rechazan como campos no permitidos (SV-13).
- **Nombre de la cotización:** `users` no vale como `active_users` (SV-12).
- **Validación antes que existencia:** SV-18; en el historial, la existencia va antes que los parámetros (HP-4).
- **Tasa cambiada o país retirado después de guardar:** el historial no cambia (SN-3 a SN-5); guardar una nueva para un país retirado da 422 (SC-3).
- **Mismo instante:** dos simulaciones del mismo segundo se ordenan por `id` (HI-1).
- **Guardado a medias:** imposible por la transacción única (DB-10).
- **Identificador de ruta raro:** texto, cero, negativo, decimal, ceros a la izquierda y número enorme (HI-11).

## 9. Fuera de alcance

- Editar o borrar simulaciones, y borrar clientes (§3 del 00).
- Que el almacenamiento o las llamadas a la API cambien el precio: pendiente de la respuesta de Andrea (§10 supuesto 1). Si cambia, será otra spec.
- Leer una simulación suelta (`GET /simulations/{id}`), comparar simulaciones o generar un PDF.
- Guardar la divisa de visualización o el tipo de cambio: la conversión es solo presentación (RN-7).
- Las pantallas del simulador y del historial: spec de frontend.
- Autenticación y registro de qué comercial guardó cada simulación (ADR 0007).

## 10. Criterios de finalización

**Funcionalidad**

- [ ] Cada caso de las tablas 6.1 a 6.9 tiene un test automático en el nivel que indica y todos pasan.
- [ ] Cada criterio CA-x de la sección 4 está cubierto por al menos un test que lo cita por su identificador y pasa.
- [ ] `POST /simulations` con el ejemplo de la sección 5 devuelve exactamente la respuesta de la sección 5 (con el reloj fijado).
- [ ] Los dos endpoints aparecen en la documentación interactiva con su ejemplo.
- [ ] Con el servidor arrancado de verdad, un guardado y un historial por línea de comandos funcionan, y `python -m app.db.seed` carga las 6 simulaciones.
- [ ] Todos los tests de 001, 002 y 003 siguen pasando sin haberlos modificado.

**Cumplimiento de la constitución** (comprobación en revisión)

- [ ] Principio 1: no se añade ninguna dependencia.
- [ ] Principio 2: cada commit de código cita el RF-x o CA-x de esta spec que implementa.
- [ ] Principio 3: los routers no contienen reglas de negocio ni SQL; los importes salen del cálculo de 001.
- [ ] Principio 4: el esquema cambia solo con una migración nueva; 0001 y 0002 no se tocan; cada simulación guarda su instantánea.
- [ ] Principio 5: la suite completa pasa en cada commit; cada endpoint tiene test de integración; las correcciones al código generado están anotadas en `ai-workspace/ai-review-log.md`.
- [ ] Principio 6: `ruff check`, `ruff format --check` y `mypy` pasan sin errores; toda entrada se valida.

## 11. Decisiones tomadas al redactar

Todas son **[P]** y el autor las confirmó al aprobar la spec. Ninguna contradice el enunciado; D-3 amplía §8.5 del documento 00.

- **D-1. Nombre del campo de usuarios (cierra 001 D-1).** La simulación usa `active_users`, como §8.3 y §8.5; la cotización sigue con `users`, porque 002 está cerrada. Enviar `users` a `POST /simulations` es un campo no permitido (SV-12). Alternativa: aceptar los dos nombres, que complica la validación sin ganar nada.
- **D-2. Forma de la instantánea en la respuesta.** Los campos de la cotización menos `users`, que repetiría `active_users`. Alternativa: incluir también `users` para que el frontend reutilice el mismo tipo tal cual.
- **D-3. Límites del tramo en la instantánea.** `simulation_tiers` guarda también `from_users` y `to_users`, que §8.5 no lista. Sin ellos, el historial tendría que reconstruir los límites con la constante actual del dominio y cambiaría si cambian los tramos, en contra de RN-8. Alternativa: seguir §8.5 al pie de la letra y reconstruirlos.
- **D-4. Cliente cuyo país deja de estar soportado (cierra 003 D-7).** No se puede guardar una simulación nueva (422 CNS sobre `customer_id`, SC-3), pero su historial se sigue leyendo (SN-5). Se usa 422 porque §8.4 ya clasifica «país no soportado» como error de validación.
- **D-5. Rangos de almacenamiento y llamadas.** RN-9 solo pide enteros ≥ 0. Se fijan máximos de 1 000 000 GB y 1 000 000 000 llamadas al mes para rechazar valores absurdos y números que SQLite no puede guardar. Son supuestos para documentar en el README junto a §10 supuesto 9.
- **D-6. Los cuatro campos son obligatorios.** Almacenamiento y llamadas no cambian el precio, pero el enunciado los registra en cada simulación; un valor por defecto escondería un olvido del formulario.
- **D-7. Cliente inexistente en el cuerpo.** 404, como fija §8.2, aunque el identificador viaje en el cuerpo y no en la ruta; siempre después de validar (SV-18). En el historial, el 404 va antes que los parámetros (HP-4), porque sin cliente no hay nada que paginar.
- **D-8. Historial paginado.** §8.2 no lo pide, pero se reutilizan `limit`, `offset` y la forma `{items, total}` de `GET /customers` para que la respuesta no crezca sin límite y el frontend use un único patrón.
- **D-9. Orden del historial a igualdad de instante.** Por `id` descendente: `created_at` tiene precisión de segundos.
- **D-10. Seed de simulaciones.** Seis simulaciones en cinco clientes, solo para clientes de demostración sin ninguna simulación (CA-8.2), de modo que también completa una base de datos sembrada con la 003.
- **D-11. Sin cabecera `Location` en el 201**, como en 003 D-8.

## 12. Historial de cambios

| Versión | Cambio |
| --- | --- |
| 1.0 | Versión inicial. Pendiente de la revisión del autor |
| 1.0 (aprobación) | Sin cambios en los requisitos. El autor aprobó la spec y confirmó las decisiones D-1 a D-11 |
