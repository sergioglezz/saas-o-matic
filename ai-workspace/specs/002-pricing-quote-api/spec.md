# 002 — Endpoint de cotización (`POST /pricing/quote`)

Estado: borrador v0.1, pendiente de aprobación · Fuente de verdad: `ai-workspace/specs/00-spec-first.md` · Constitución: `ai-workspace/docs/constitution.md` · Depende de: `ai-workspace/specs/001-pricing-and-tax/spec.md` (v1.2)

Leyenda de origen: **[E]** viene del enunciado y no se puede contradecir; **[P]** es una propuesta del documento 00 o una decisión tomada al aclarar o revisar la spec 001. Todo el contenido viene de la spec 001 v1.1 sin cambios de comportamiento; cada requisito indica de qué parte sale.

## 1. Contexto y objetivo

El simulador del dashboard pide una cotización al backend tras cada cambio del slider (UC-4, ADR 0004). Esta spec define ese punto de entrada: cómo se valida la petición, qué devuelve y cómo informa de los errores. El cálculo en sí lo define la spec 001; este endpoint no calcula nada por su cuenta.

**Objetivo:** exponer `POST /pricing/quote`, que recibe usuarios y país, valida y normaliza la entrada, obtiene el resultado del cálculo de 001 y lo devuelve sin guardar nada, con un formato único de error.

## 2. Usuarios

- **Comercial** (único usuario, sin autenticación, §2 [P]): mueve el slider y ve la factura proyectada.
- **Dashboard Angular** (consumidor técnico): llama al endpoint tras cada cambio del slider y pinta el resultado o el error.
- **Evaluadores** (audiencia indirecta): prueban el endpoint desde la documentación interactiva de la API.

## 3. Historias de usuario

- **HU-1.** Como comercial, quiero ver al instante el coste mensual desglosado al mover el slider, para explicarlo al cliente sin esperar.
- **HU-2.** Como comercial, quiero recibir un error claro cuando un dato no es válido, para corregirlo sin adivinar qué pasa.

## 4. Requisitos funcionales

### RF-1. Cotización sin guardar

Origen: antes 001 RF-8 · §3 y §8.2 `POST /pricing/quote` **[P]**, ADR 0004 **[P]**.

- **CA-1.1** Cuando recibe una petición válida en `POST /pricing/quote`, el sistema deberá responder 200 con el resultado del cálculo de 001 para los `users` y el `country` normalizado, con el formato de la sección 5.
- **CA-1.2** El sistema no deberá crear ningún recurso al cotizar: la respuesta es 200 (nunca 201), no incluye cabecera `Location` y no incluye ningún campo `id`.
- **CA-1.3** Cuando recibe dos veces la misma petición con la misma configuración de tasas, el sistema deberá devolver dos respuestas idénticas.

### RF-2. Validación de `users`

Origen: antes 001 CA-3.1 (parte léxica), CA-3.3 (mensaje) y CA-3.4 de la v1.1 · RN-2 **[P]**, aclaración 2 de 001 (validación estricta) **[P]**.

Definición: un **entero JSON** es un número JSON escrito sin parte decimal ni exponente (por ejemplo `15`, `0`, `-0`). `15.0`, `1e2` y `100000.0` no son enteros JSON aunque su valor sea entero.

- **CA-2.1** El sistema deberá aceptar como `users` cualquier entero JSON cuyo valor esté entre 0 y 100 000, ambos incluidos. `-0` se acepta y se trata como 0.
- **CA-2.2** Si `users` está presente pero no es un entero JSON (número con decimales o exponente, texto, booleano, `null`, lista u objeto) o su valor está fuera de 0 a 100 000 (también números enormes), entonces el sistema deberá responder 422 con un único detalle `{field: "users", message: "Debe ser un número entero entre 0 y 100000"}`.
- **CA-2.3** Si falta `users`, entonces el sistema deberá responder 422 con el detalle `{field: "users", message: "Campo obligatorio"}`.

### RF-3. País normalizado y soportado

Origen: antes 001 RF-5 · RN-4 **[P]**, aclaración 3 de 001 (normalizar) **[P]**.

Clasificación: la normalización del país es una **regla de validación de la entrada**, no una regla de negocio; el cálculo de 001 recibe siempre el código ya normalizado (001 CA-4.7).

- **CA-3.1** Cuando `country` es un texto, el sistema deberá quitar los espacios en blanco del principio y del final (solo espacio, tabulador, salto de línea y retorno de carro) y pasar a mayúsculas las letras `a`–`z`.
- **CA-3.2** Si `country`, tras normalizarlo, no son exactamente 2 letras `A`–`Z`, entonces el sistema deberá responder 422 con el detalle `{field: "country", message: "Debe ser un código de país de 2 letras"}`. Esto incluye espacios internos, letras de ancho completo, espacios no separables, dígitos, texto vacío y textos de 1 o de 3 o más caracteres.
- **CA-3.3** Si `country` no es un texto (número, booleano, `null`, lista u objeto), entonces el sistema deberá responder 422 con el detalle `{field: "country", message: "Debe ser un código de país de 2 letras"}`.
- **CA-3.4** Si `country` normalizado tiene formato válido pero no está soportado (001 CA-4.2), entonces el sistema deberá responder 422 con el detalle `{field: "country", message: "País no soportado"}`.
- **CA-3.5** Si falta `country`, entonces el sistema deberá responder 422 con el detalle `{field: "country", message: "Campo obligatorio"}`.
- **CA-3.6** Cuando `country` es válido tras normalizarlo, el sistema deberá cotizar igual que con el código ya normalizado.

### RF-4. Representación JSON de la cotización

Origen: antes 001 CA-7.1 (parte léxica) y CA-7.3 · RN-6 **[P]**, §8.1 **[P]**.

- **CA-4.1** El sistema deberá devolver todos los números de la respuesta como enteros JSON, sin parte decimal ni exponente.
- **CA-4.2** El sistema deberá devolver en `users` el valor recibido como entero (0 si llegó `-0`).
- **CA-4.3** El sistema deberá representar el límite superior abierto del tramo 3 como `"to_users": null`.
- **CA-4.4** El sistema deberá devolver `"currency": "EUR"`.

### RF-5. Rechazo de campos no definidos

Origen: antes 001 RF-9 · §8.1 «el cliente no envía nunca precios ni totales» **[P]**, aclaración 4 de 001 (rechazar) **[P]**.

- **CA-5.1** Si el objeto de la petición incluye un campo distinto de `users` y `country`, entonces el sistema deberá responder 422 con un detalle `{field: <nombre del campo>, message: "Campo no permitido"}` por cada campo no definido.
- **CA-5.2** El sistema deberá distinguir mayúsculas en los nombres de campo: `Users` o `COUNTRY` son campos no definidos y no cuentan como `users` o `country`.

### RF-6. Formato único de error

Origen: antes 001 RF-10 · §8.4 **[P]**.

- **CA-6.1** Si la respuesta es un error, entonces el sistema deberá devolver el cuerpo `{"error": {"code", "message", "details"}}`, donde `details` es siempre una lista (vacía si no aplica) de objetos `{field, message}`.
- **CA-6.2** El sistema deberá usar exactamente estos `code` y `message` de primer nivel: 422 `validation_error` «Datos no válidos»; 405 `method_not_allowed` «Método no permitido»; 500 `internal_error` «Error interno del servidor».
- **CA-6.3** El sistema deberá incluir en `details` un único elemento por cada campo inválido, aunque el campo incumpla varias reglas, y uno por cada campo no definido. Si `users` y `country` son inválidos a la vez, deberán aparecer los dos.
- **CA-6.4** El sistema no deberá garantizar el orden de `details`; los tests comparan la lista como conjunto.
- **CA-6.5** Si se produce un fallo inesperado, entonces el sistema deberá responder 500 con `details` vacío y sin trazas, rutas de archivo ni nombres internos en el cuerpo.
- **CA-6.6** El sistema deberá responder con `Content-Type: application/json` en todos los casos, de éxito y de error.

### RF-7. Cuerpo de la petición

Origen: antes 001 RF-11 · §8.1 «JSON en UTF-8» **[P]**.

- **CA-7.1** El sistema deberá aceptar el cuerpo como JSON solo si la cabecera `Content-Type` es `application/json`, con o sin parámetro `charset`.
- **CA-7.2** Si falta `Content-Type`, no es `application/json`, el cuerpo está vacío, no es JSON válido o no es un objeto JSON (lista, texto, número, `null`), entonces el sistema deberá responder 422 con el único detalle `{field: "body", message: "El cuerpo debe ser un objeto JSON"}`.
- **CA-7.3** Cuando el objeto JSON repite una clave, el sistema deberá usar el último valor de esa clave.

### RF-8. Métodos no permitidos

Origen: antes 001 RF-12.

- **CA-8.1** Si llega a `/pricing/quote` una petición `GET`, `PUT`, `PATCH` o `DELETE`, entonces el sistema deberá responder 405 con `code` = `method_not_allowed`, `details` vacío y la cabecera `Allow: POST`.

## 5. Contrato observable

**`POST /pricing/quote`**: cotiza sin guardar. Cabecera de petición: `Content-Type: application/json`.

Petición (objeto JSON con solo estos dos campos, sensibles a mayúsculas):

| Campo | Tipo | Regla |
| --- | --- | --- |
| `users` | entero JSON | 0 ≤ `users` ≤ 100 000; sin parte decimal ni exponente |
| `country` | texto | Tras quitar espacios exteriores y pasar a mayúsculas: 2 letras `A`–`Z` de un país soportado |

Respuesta `200` (`Content-Type: application/json`, sin `Location`), ejemplo con `{ "users": 15, "country": "ES" }` (§8.3):

```json
{
  "users": 15,
  "currency": "EUR",
  "tiers": [
    { "tier": 1, "from_users": 1,  "to_users": 10,   "units": 10, "unit_price_cents": 1000, "amount_cents": 10000 },
    { "tier": 2, "from_users": 11, "to_users": 50,   "units": 5,  "unit_price_cents": 800,  "amount_cents": 4000 },
    { "tier": 3, "from_users": 51, "to_users": null, "units": 0,  "unit_price_cents": 500,  "amount_cents": 0 }
  ],
  "subtotal_cents": 14000,
  "tax_rate_bp": 2100,
  "tax_cents": 2940,
  "total_cents": 16940
}
```

Error (formato de §8.4):

```json
{
  "error": {
    "code": "validation_error",
    "message": "Datos no válidos",
    "details": [ { "field": "country", "message": "País no soportado" } ]
  }
}
```

| HTTP | `code` | `message` | Cuándo |
| --- | --- | --- | --- |
| 200 | (sin error) | — | Petición válida |
| 405 | `method_not_allowed` | Método no permitido | `GET`, `PUT`, `PATCH` o `DELETE` (con `Allow: POST`) |
| 422 | `validation_error` | Datos no válidos | Cualquier fallo de RF-2, RF-3, RF-5 y RF-7 |
| 500 | `internal_error` | Error interno del servidor | Fallo inesperado |

Mensajes de `details` (únicos textos posibles):

| `field` | `message` | Cuándo |
| --- | --- | --- |
| `users` | Campo obligatorio | Falta `users` |
| `users` | Debe ser un número entero entre 0 y 100000 | `users` no es entero JSON o está fuera de rango (equivale al error de dominio «usuarios no válidos» de 001) |
| `country` | Campo obligatorio | Falta `country` |
| `country` | Debe ser un código de país de 2 letras | `country` no es texto o no son 2 letras `A`–`Z` tras normalizar |
| `country` | País no soportado | Formato válido sin tasa configurada (equivale al error de dominio «país no soportado» de 001) |
| (nombre del campo) | Campo no permitido | Campo no definido |
| `body` | El cuerpo debe ser un objeto JSON | Cabecera, cuerpo vacío, JSON inválido o no objeto |

## 6. Casos de prueba

Todos son de nivel **I** (integración: petición HTTP al endpoint, con la configuración de tasas por defecto de 001 CA-4.3 salvo que se diga otra cosa).

### 6.1 Cotizaciones válidas

Q-1 a Q-10: las peticiones `{"users": u, "country": c}` de 001 T-1 a T-10 responden 200 con exactamente los mismos `subtotal_cents`, `tax_rate_bp`, `tax_cents` y `total_cents` de esa tabla. Q-4 (15, ES) responde además exactamente el ejemplo de la sección 5.

| # | `users` | `country` | `subtotal_cents` | `tax_rate_bp` | `tax_cents` | `total_cents` |
| --- | --- | --- | --- | --- | --- | --- |
| Q-11 | 15 | `"es"` | 14000 | 2100 | 2940 | 16940 |
| Q-12 | 15 | `" ES "` | 14000 | 2100 | 2940 | 16940 |
| Q-13 | 15 | `"\tEs\n"` | 14000 | 2100 | 2940 | 16940 |
| Q-14 | 1 | `"pt"` | 1000 | 2300 | 230 | 1230 |
| Q-15 | 1 | `"fr"` | 1000 | 2000 | 200 | 1200 |
| Q-16 | 1 | `"de"` | 1000 | 1900 | 190 | 1190 |
| Q-17 | 1 | `"it"` | 1000 | 2200 | 220 | 1220 |
| Q-18 | 1 | `"gb"` | 1000 | 2000 | 200 | 1200 |
| Q-19 | 1 | `"us"` | 1000 | 0 | 0 | 1000 |
| Q-20 | `-0` | `"US"` | 0 (y `users` = 0) | 0 | 0 | 0 |

Correspondencia con 001 v1.1: Q-11 a Q-19 = T-11 a T-19; Q-20 = P-11.

### 6.2 Errores de validación · todos 422 `validation_error` «Datos no válidos»

Mensajes abreviados: **OBL** = «Campo obligatorio»; **USR** = «Debe ser un número entero entre 0 y 100000»; **FMT** = «Debe ser un código de país de 2 letras»; **NSP** = «País no soportado»; **NPE** = «Campo no permitido»; **BODY** = «El cuerpo debe ser un objeto JSON».

| # | Petición | `details` esperado (como conjunto) |
| --- | --- | --- |
| E-1 | `{"users": -1, "country": "ES"}` | users/USR |
| E-2 | `{"users": 100001, "country": "ES"}` | users/USR |
| E-3 | `{"users": 1.5, "country": "ES"}` | users/USR |
| E-4 | `{"users": 15.0, "country": "ES"}` | users/USR |
| E-5 | `{"users": 1e2, "country": "ES"}` | users/USR |
| E-6 | `{"users": 100000.0, "country": "ES"}` | users/USR |
| E-7 | `{"users": 0.0, "country": "ES"}` | users/USR |
| E-8 | `{"users": "15", "country": "ES"}` | users/USR |
| E-9 | `{"users": "", "country": "ES"}` | users/USR |
| E-10 | `{"users": true, "country": "ES"}` | users/USR |
| E-11 | `{"users": null, "country": "ES"}` | users/USR |
| E-12 | `{"users": [], "country": "ES"}` | users/USR |
| E-13 | `{"users": {}, "country": "ES"}` | users/USR |
| E-14 | `{"users": 99999999999999999999, "country": "ES"}` | users/USR |
| E-15 | `{"users": -1.5, "country": "ES"}` | users/USR (un solo elemento) |
| E-16 | `{"country": "ES"}` | users/OBL |
| E-17 | `{"users": 15, "country": "XX"}` | country/NSP |
| E-18 | `{"users": 15, "country": "ESP"}` | country/FMT |
| E-19 | `{"users": 15, "country": "E"}` | country/FMT |
| E-20 | `{"users": 15, "country": "12"}` | country/FMT |
| E-21 | `{"users": 15, "country": "E S"}` | country/FMT |
| E-22 | `{"users": 15, "country": "ＥＳ"}` (ancho completo) | country/FMT |
| E-23 | `{"users": 15, "country": " ES"}` (espacio no separable) | country/FMT |
| E-24 | `{"users": 15, "country": "   "}` | country/FMT |
| E-25 | `{"users": 15, "country": ""}` | country/FMT |
| E-26 | `{"users": 15, "country": 34}` | country/FMT |
| E-27 | `{"users": 15, "country": null}` | country/FMT |
| E-28 | `{"users": 15, "country": ["ES"]}` | country/FMT |
| E-29 | `{"users": 15, "country": {"code": "ES"}}` | country/FMT |
| E-30 | `{"users": 15}` | country/OBL |
| E-31 | `{}` | users/OBL, country/OBL |
| E-32 | `{"users": 15, "country": "ES", "subtotal_cents": 1}` | subtotal_cents/NPE |
| E-33 | `{"users": 15, "country": "ES", "subtotal_cents": 1, "tax_rate_bp": 0}` | subtotal_cents/NPE, tax_rate_bp/NPE |
| E-34 | `{"users": -1, "country": "ES", "subtotal_cents": 1}` | users/USR, subtotal_cents/NPE |
| E-35 | `{"users": -1, "country": "XX"}` | users/USR, country/NSP |
| E-36 | `{"Users": 15, "country": "ES"}` | Users/NPE, users/OBL |
| E-37 | cuerpo `no es json` | body/BODY |
| E-38 | cuerpo `[15, "ES"]` | body/BODY |
| E-39 | cuerpo `null` | body/BODY |
| E-40 | cuerpo vacío (0 bytes) | body/BODY |
| E-41 | `{"users": 15, "country": "ES"}` con `Content-Type: text/plain` | body/BODY |
| E-42 | `{"users": 15, "country": "ES"}` sin cabecera `Content-Type` | body/BODY |

### 6.3 Protocolo y comportamiento general

| # | Petición o situación | Resultado esperado |
| --- | --- | --- |
| O-1 | `{"users": 15, "country": "ES"}` con `Content-Type: application/json; charset=utf-8` | 200, igual que Q-4 |
| O-2 | `{"users": 1, "users": 15, "country": "ES"}` (clave repetida) | 200, igual que Q-4 |
| O-3 | `GET /pricing/quote` | 405 `method_not_allowed` «Método no permitido», `details` vacío, `Allow: POST` |
| O-4 | `PUT`, `PATCH` y `DELETE /pricing/quote` | Igual que O-3 |
| O-5 | Fallo interno forzado en la prueba (fuente de tasas no disponible) | 500 `internal_error` «Error interno del servidor», `details` vacío; el cuerpo no contiene «Traceback», rutas de archivo ni nombres de módulos |
| O-6 | La petición de Q-4 enviada dos veces | Dos respuestas idénticas |
| O-7 | Cualquier respuesta 200 | Sin cabecera `Location` y sin campo `id` |
| O-8 | Respuestas de Q-4, E-1, O-3 y O-5 | `Content-Type: application/json` |
| O-9 | Cualquier respuesta 200 | Todos los números del cuerpo son enteros JSON, sin decimales ni exponente |

## 7. Requisitos no funcionales

- **RNF-1 Una sola fuente de verdad** (antes 001 RNF-4): el endpoint no calcula importes; los obtiene del cálculo de 001 (ADR 0004 [P]).
- **RNF-2 Rendimiento** (antes 001 RNF-5; informativo, no bloquea la entrega): en la máquina de desarrollo, con el servidor ya arrancado, el percentil 95 de 100 cotizaciones secuenciales queda por debajo de 200 ms (§6 [P]). Se mide una vez y el resultado se anota en el README.
- **RNF-3 Seguridad** (antes 001 RNF-6): los errores no exponen trazas, rutas ni nombres internos (§6 [P]; caso O-5).
- **RNF-4 Idioma** (antes 001 RNF-7): los únicos textos de error posibles son los de la sección 5, todos en español; los nombres de campo van en inglés y `snake_case` (§6 y §8.1 [P]).
- **RNF-5 Documentación** (antes 001 RNF-8): el endpoint aparece en la documentación interactiva de la API con su ejemplo de petición y respuesta (§3 [P]).

## 8. Casos límite

- **`-0`:** se acepta como 0 (Q-20).
- **Enteros disfrazados:** `15.0`, `1e2`, `100000.0`, `0.0`, `"15"` y `true` se rechazan (E-4 a E-10).
- **Números enormes:** se rechazan sin error interno (E-14).
- **Un campo con varios fallos:** un único elemento en `details` (E-15).
- **País con formato raro:** minúsculas, espacios exteriores, tabuladores y saltos de línea se normalizan (Q-11 a Q-19); espacios internos, ancho completo, espacio no separable, 1 o 3 letras y dígitos se rechazan (E-18 a E-25).
- **País de tipo incorrecto:** número, `null`, lista y objeto (E-26 a E-29).
- **Usuarios y país inválidos a la vez:** se informa de los dos (E-35).
- **Cuerpo vacío o raro:** `{}`, cuerpo sin bytes, `null`, lista, JSON inválido y cabecera incorrecta o ausente (E-31, E-37 a E-42).
- **Campos no definidos:** solos, varios a la vez, combinados con otros errores y con mayúsculas distintas (E-32 a E-36).
- **Clave repetida:** gana el último valor (O-2).
- **Métodos no permitidos y fallo interno:** O-3 a O-5.

## 9. Fuera de alcance

- Las reglas del cálculo (tramos, impuesto, redondeo, tabla de tasas): spec 001.
- Guardar simulaciones y el historial: spec posterior.
- La pantalla del simulador y la conversión de divisas: specs de frontend.
- Autenticación y límites de peticiones.
- Límite de tamaño del cuerpo: es una herramienta interna sin exposición pública (§6 del documento 00); se documenta en el README.
- Rutas distintas de `/pricing/quote` exacta (por ejemplo con barra final) y peticiones `OPTIONS` de CORS: su comportamiento lo fija la configuración general de la API, no esta spec.

## 10. Criterios de finalización

**Funcionalidad**

- [ ] Cada caso de las tablas 6.1 a 6.3 (Q-1 a Q-20, E-1 a E-42, O-1 a O-9) tiene un test de integración y todos pasan.
- [ ] Cada criterio CA-x de la sección 4 está cubierto por al menos un test que lo cita por su identificador.
- [ ] `POST /pricing/quote` responde exactamente el ejemplo de la sección 5 con `{ "users": 15, "country": "ES" }`.
- [ ] El endpoint aparece en la documentación interactiva con su ejemplo.
- [ ] RNF-2 medido una vez y anotado en el README.

**Cumplimiento de la constitución** (comprobación en revisión)

- [ ] Principio 1: no se añade ninguna dependencia sin ADR en `ai-workspace/architecture/adr/`.
- [ ] Principio 2: cada commit de código cita el RF-x o CA-x de esta spec que implementa.
- [ ] Principio 3: el endpoint solo valida, normaliza y traduce; no contiene reglas de precio ni de impuesto ni accede a la base de datos directamente.
- [ ] Principio 5: la suite completa pasa antes de cada commit, y el endpoint tiene tests de integración (todos los casos de la sección 6).
- [ ] Principio 5: el código generado por IA está revisado y las correcciones están anotadas en `ai-workspace/ai-review-log.md`.
- [ ] Principio 6: `ruff check`, `ruff format --check` y `mypy` pasan sin errores en el backend; toda entrada se valida.

## 11. Decisiones cerradas

- **D-1. Nombre del campo de usuarios:** `users`, como fija §8.3 (compartida con 001 D-1).
- **D-2. País en la respuesta:** no se devuelve; se mantiene el contrato de §8.3 (antes 001 D-2).

No hay dudas abiertas.

## 12. Historial de cambios

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 0.1 | 2026-11-14 | Borrador creado al dividir la spec 001 (v1.2). Contenido movido desde 001 v1.1 sin cambios de comportamiento; los casos T-11 a T-19 y P-11 pasan a ser Q-11 a Q-20 |
