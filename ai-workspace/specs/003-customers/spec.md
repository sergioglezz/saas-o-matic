# 003 — Clientes: registro, búsqueda y ficha

Estado: v1.0 · ✅ implementada y verificada por delegación expresa del autor, con los 13 criterios de finalización cumplidos · ✅ Completada, revisada y aprobada por el autor, con las decisiones D-1 a D-14 confirmadas · Fuente de verdad: `ai-workspace/specs/00-spec-first.md` · Constitución: `ai-workspace/docs/constitution.md` · Depende de: specs 001 (v1.2) y 002 (v1.1), ambas completadas

Leyenda de origen: **[E]** viene del enunciado y no se puede contradecir; **[P]** es una propuesta del documento 00 o una decisión tomada al redactar esta spec. Las decisiones nuevas están en la sección 11 para que el autor las confirme o las cambie.

## 1. Contexto y objetivo

El comercial necesita registrar clientes corporativos, encontrarlos y abrir su ficha (UC-1, UC-2 y UC-3). Es el primero de los dos `POST` obligatorios del enunciado, y la futura spec de simulaciones necesita que el cliente exista para calcular con su país.

**Objetivo:** exponer `POST /customers`, `GET /customers` y `GET /customers/{id}` sobre una tabla `customers`, con la validación estricta del identificador fiscal español, la unicidad del identificador y el formato único de error de 002. Incluye el script de datos de demostración con clientes inventados.

**Alcance adicional:** al añadir rutas con parámetros, el formato único de error de 002 (RF-6) deja de estar protegido solo por casualidad. Esta spec lo cierra para cualquier error que genere el framework (RF-7; entrada 16 de `ai-review-log.md`).

## 2. Usuarios

- **Comercial** (único usuario, sin autenticación): registra, busca y consulta clientes.
- **Dashboard Angular** (consumidor técnico): pinta el listado, la ficha y los errores junto a cada campo.
- **Spec de simulaciones** (consumidora futura): leerá el cliente y su país.
- **Evaluadores** (audiencia indirecta): prueban los endpoints desde `/docs` y cargan los datos de demostración con un comando.

## 3. Historias de usuario

- **HU-1.** Como comercial, quiero registrar un cliente con sus datos fiscales, para poder presupuestarle después.
- **HU-2.** Como comercial, quiero que un identificador fiscal español mal escrito se rechace al momento, para no guardar datos que luego no sirven.
- **HU-3.** Como comercial, quiero buscar por nombre o por identificador fiscal, para encontrar un cliente en segundos.
- **HU-4.** Como comercial, quiero abrir la ficha de un cliente, para ver sus datos.
- **HU-5.** Como evaluador, quiero cargar clientes de ejemplo con un comando, para ver el dashboard con datos.

## 4. Requisitos funcionales

### RF-1. Registrar un cliente

Origen: §3 y §8.2 `POST /customers` **[E]**, §8.3 **[P]**.

- **CA-1.1** Cuando recibe una petición válida en `POST /customers`, el sistema deberá guardar el cliente y responder 201 con `id`, `company_name`, `tax_id`, `contact_email`, `country`, `plan` y `created_at`, con el formato de la sección 5.
- **CA-1.2** El sistema deberá guardar y devolver los valores ya normalizados: `company_name` sin espacios sobrantes (CA-2.1), `tax_id` normalizado (CA-3.1), `contact_email` sin espacios exteriores (CA-2.2) y `country` en mayúsculas (CA-2.3).
- **CA-1.3** El sistema deberá asignar como `id` un entero positivo creciente que no se reutiliza, y como `created_at` el instante del alta en UTC, escrito como texto ISO 8601 con precisión de segundos y sufijo `Z` (por ejemplo `2026-11-13T10:00:00Z`).
- **CA-1.4** Cuando un cliente se ha registrado, el sistema deberá devolverlo con los mismos datos en `GET /customers/{id}` y en `GET /customers`.
- **CA-1.5** Si la petición no es válida o entra en conflicto con otro cliente, entonces el sistema no deberá guardar nada.

### RF-2. Validación de los campos

Origen: §3 y §8.3 **[E]** para los campos, **[P]** para las reglas concretas. Reutiliza sin cambios el cuerpo de la petición de 002 RF-7 y los campos no definidos de 002 RF-5.

- **CA-2.1** `company_name` deberá ser un texto. El sistema deberá quitarle los espacios en blanco del principio y del final y dejar en un solo espacio cada grupo interior de espacios en blanco. El resultado deberá tener entre 1 y 120 caracteres, todos imprimibles (sin caracteres de control). Si no, detalle `{field: "company_name", message: "Debe tener entre 1 y 120 caracteres"}`.
- **CA-2.2** `contact_email` deberá ser un texto. El sistema deberá quitarle los espacios exteriores (espacio, tabulador, salto de línea y retorno de carro) y guardarlo sin cambiar mayúsculas. El resultado deberá tener como máximo 254 caracteres y la forma `local@dominio`:
  - `local`: de 1 a 64 caracteres entre letras `A`–`Z` y `a`–`z`, dígitos y ``.!#$%&'*+/=?^_`{|}~-``;
  - `dominio`: dos o más etiquetas separadas por punto, cada una de 1 a 63 letras `A`–`Z` y `a`–`z`, dígitos o guiones, sin empezar ni acabar en guion.

  Si no, detalle `{field: "contact_email", message: "Debe ser un email válido"}`.
- **CA-2.3** `country` deberá cumplir lo mismo que en la cotización (002 CA-3.1 a CA-3.4): se normaliza, deben ser 2 letras `A`–`Z` y el país debe estar soportado (001 CA-4.2). Mensajes: «Debe ser un código de país de 2 letras» y «País no soportado».
- **CA-2.4** `plan` deberá ser exactamente `starter`, `business` o `enterprise`, sin normalizar y distinguiendo mayúsculas. Si no, detalle `{field: "plan", message: "Debe ser starter, business o enterprise"}`. El plan no cambia ningún precio.
- **CA-2.5** Si falta alguno de los cinco campos, entonces el sistema deberá responder 422 con el detalle `{field: <campo>, message: "Campo obligatorio"}`.
- **CA-2.6** Si un campo está presente pero no es un texto (número, booleano, `null`, lista u objeto), entonces el sistema deberá responder 422 con el mensaje de formato de ese campo; para `tax_id`, «Debe tener entre 5 y 20 letras o dígitos».
- **CA-2.7** Si el objeto incluye un campo distinto de los cinco definidos (también `id`, `created_at` o un nombre con otras mayúsculas), entonces el sistema deberá responder 422 con `{field: <nombre>, message: "Campo no permitido"}` por cada uno.
- **CA-2.8** Si el cuerpo no es un objeto JSON con `Content-Type: application/json`, entonces el sistema deberá responder 422 con el único detalle `{field: "body", message: "El cuerpo debe ser un objeto JSON"}` (002 CA-7.1 a CA-7.3).
- **CA-2.9** El sistema deberá informar a la vez de todos los campos inválidos, con un único detalle por campo (002 CA-6.3) y sin orden garantizado (002 CA-6.4).

### RF-3. Identificador fiscal

Origen: RN-10 **[E]** (España) y **[P]** (resto), RN-11 **[P]**, §7.4. La convención del control del CIF está en el ADR 0009.

- **CA-3.1** El sistema deberá normalizar `tax_id` antes de validarlo: quitar en cualquier posición los espacios en blanco (espacio, tabulador, salto de línea y retorno de carro), los guiones `-` y los puntos `.`, y pasar a mayúsculas las letras `a`–`z`.
- **CA-3.2** Formato básico, para cualquier país: tras normalizar, `tax_id` deberá tener entre 5 y 20 caracteres, solo letras `A`–`Z` y dígitos. Si no, detalle `{field: "tax_id", message: "Debe tener entre 5 y 20 letras o dígitos"}`.
- **CA-3.3** Si `country` normalizado es `ES`, el identificador deberá ser además un DNI, un NIE o un CIF con el carácter de control correcto (CA-3.4 a CA-3.6). Si no, detalle `{field: "tax_id", message: "El DNI/NIF/CIF no es válido"}`.
- **CA-3.4** DNI: 8 dígitos y una letra. La letra deberá ser la que ocupa la posición (número mod 23) en `TRWAGMYFPDXBNJZSQVHLCKE`.
- **CA-3.5** NIE: `X`, `Y` o `Z`, 7 dígitos y una letra. Se sustituye `X`→0, `Y`→1 y `Z`→2 y se aplica el cálculo del DNI.
- **CA-3.6** CIF: una letra de entidad de `ABCDEFGHJNPQRSUVW`, 7 dígitos y un carácter de control. Con A = suma de los dígitos 2.º, 4.º y 6.º, y B = suma, para los dígitos 1.º, 3.º, 5.º y 7.º, de las cifras de su doble, el dígito de control es (10 − (A + B) mod 10) mod 10, y su letra equivalente es la de esa posición en `JABCDEFGHI`. El control deberá ser la letra para las entidades `N`, `P`, `Q`, `R`, `S` y `W`; el dígito para `A`, `B`, `E` y `H`; y cualquiera de los dos para el resto.
- **CA-3.7** Si `country` es `ES` y el identificador normalizado empieza por `K`, `L` o `M`, entonces el detalle deberá ser `{field: "tax_id", message: "Tipo de identificador no soportado"}`.
- **CA-3.8** Si `country` es otro país soportado, el sistema deberá aplicar solo el formato básico, aunque el identificador tenga forma de DNI.
- **CA-3.9** Si `country` falta, no es válido o no está soportado, el sistema deberá aplicar a `tax_id` solo el formato básico, de modo que se informe de los dos campos a la vez.

### RF-4. Identificador fiscal único

Origen: §3 «rechaza un identificador fiscal ya registrado» **[P]**, flujo 1, §8.4.

- **CA-4.1** Si el `tax_id` normalizado ya pertenece a otro cliente, sea del país que sea, entonces el sistema deberá responder 409 con `code` = `conflict`, `message` «El recurso ya existe» y el único detalle `{field: "tax_id", message: "Ya existe un cliente con este identificador"}`.
- **CA-4.2** El sistema deberá comparar los identificadores ya normalizados: `12.345.678-z` entra en conflicto con `12345678Z`.
- **CA-4.3** Si la petición tiene además algún error de validación, entonces el sistema deberá responder 422 con esos errores, sin mencionar el conflicto.
- **CA-4.4** El sistema deberá garantizar la unicidad en la base de datos, de modo que tampoco puedan guardarse dos clientes iguales con dos altas simultáneas ni con una escritura que no pase por la API.

### RF-5. Listar y buscar clientes

Origen: §3 «buscar por nombre o por identificador fiscal» **[E]**, §8.2 y §8.3 **[P]**.

- **CA-5.1** Cuando recibe `GET /customers`, el sistema deberá responder 200 con `{"items": [...], "total": n}`, donde cada elemento tiene los campos de CA-1.1.
- **CA-5.2** Cuando `q` falta, está vacío o solo tiene espacios en blanco, el sistema deberá considerar todos los clientes.
- **CA-5.3** Cuando hay `q`, el sistema deberá considerar los clientes que cumplen al menos una de estas condiciones:
  - su `company_name` contiene `q` (con los espacios tratados como en CA-2.1), sin distinguir mayúsculas de minúsculas, tampoco en letras no ASCII como `ñ` o las vocales con tilde;
  - su `tax_id` contiene `q` normalizado como un identificador (CA-3.1), siempre que esa normalización no quede vacía.
- **CA-5.4** El sistema deberá tratar `q` como texto literal: `%`, `_` y las comillas no tienen ningún significado especial.
- **CA-5.5** El sistema deberá ordenar el resultado por `company_name` sin distinguir mayúsculas y, a igualdad, por `id` ascendente.
- **CA-5.6** El sistema deberá devolver en `items` como máximo `limit` clientes a partir de la posición `offset` del resultado ordenado. `limit` vale 50 si falta y `offset` vale 0.
- **CA-5.7** El sistema deberá devolver en `total` el número de clientes que cumplen `q`, sin aplicar `limit` ni `offset`.
- **CA-5.8** Si `limit` no es un entero entre 1 y 100 escrito solo con dígitos `0`–`9`, entonces el sistema deberá responder 422 con `{field: "limit", message: "Debe ser un número entero entre 1 y 100"}`. Si `offset` no es un entero entre 0 y 1 000 000 escrito solo con dígitos, con `{field: "offset", message: "Debe ser un número entero entre 0 y 1000000"}`. Un valor vacío, con signo, con espacios o con decimales no es válido.
- **CA-5.9** Si `q`, con los espacios tratados como en CA-2.1, tiene más de 120 caracteres, entonces el sistema deberá responder 422 con `{field: "q", message: "Debe tener como máximo 120 caracteres"}`.
- **CA-5.10** Cuando un parámetro se repite, el sistema deberá usar su último valor. Los parámetros no definidos se ignoran.
- **CA-5.11** Cuando ningún cliente cumple `q`, o `offset` es mayor o igual que `total`, el sistema deberá responder 200 con `items` vacío y el `total` real.

### RF-6. Ficha de un cliente

Origen: §3 «abrir la ficha de un cliente» **[E]**, §8.2 **[P]**.

- **CA-6.1** Cuando recibe `GET /customers/{id}` y el cliente existe, el sistema deberá responder 200 con sus datos (campos de CA-1.1).
- **CA-6.2** Si no existe ningún cliente con ese `id`, entonces el sistema deberá responder 404 con `code` = `not_found`, `message` «Recurso no encontrado» y `details` vacío.
- **CA-6.3** Si `{id}` no es un entero positivo escrito solo con dígitos y sin ceros a la izquierda (`abc`, `0`, `-1`, `1.5`, `01`), o es mayor que 9 223 372 036 854 775 807, entonces el sistema deberá responder el mismo 404: ese texto no identifica a ningún cliente.

### RF-7. Formato único de error en toda la API

Origen: 002 RF-6 «el formato vale para cualquier ruta de la API, presente o futura» **[P]**, §8.4, entrada 16 de `ai-review-log.md`. Amplía 002 RF-6 y RF-8 sin cambiar nada de lo que ya cumplen.

- **CA-7.1** El sistema deberá usar para el 409 el `code` `conflict` y el `message` de primer nivel «El recurso ya existe».
- **CA-7.2** Si llega a una ruta existente un método que no admite y no es una preflight de CORS, entonces el sistema deberá responder 405 `method_not_allowed` con la cabecera `Allow` con **todos** los métodos que admite esa ruta: `GET, POST` en `/customers` y `GET` en `/customers/{id}`. `/pricing/quote` sigue respondiendo `Allow: POST`.
- **CA-7.3** Si el framework rechaza un parámetro por su tipo antes de llegar al código de la API, entonces el sistema deberá responder 422 `validation_error` «Datos no válidos» con un detalle `{field: <nombre del parámetro>, message: "Valor no válido"}` por parámetro.
- **CA-7.4** Si el framework genera cualquier otro error HTTP (un estado distinto de 404 y 405), entonces el sistema deberá responder ese mismo estado con `code` = `http_error`, `message` «Error en la petición» y `details` vacío, sin el texto interno del error.
- **CA-7.5** Las rutas de esta spec deberán cumplir 002 RF-6 igual que la cotización: 404 `not_found` con barra final (`/customers/`), 500 `internal_error` sin detalles internos ante un fallo inesperado y `Content-Type: application/json` en éxitos y errores.

### RF-8. CORS para las rutas nuevas

Origen: 002 RF-9 **[P]**.

- **CA-8.1** Cuando llega un `GET` o un `POST` a las rutas de clientes desde el origen del frontend, el sistema deberá incluir `Access-Control-Allow-Origin` con ese origen.
- **CA-8.2** Cuando llega una preflight desde el origen del frontend con `Access-Control-Request-Method` `GET` o `POST`, el sistema deberá aceptarla (200).
- **CA-8.3** Si la petición llega desde otro origen, entonces el sistema no deberá incluir `Access-Control-Allow-Origin`.

### RF-9. Persistencia

Origen: §8.5 **[P]**, constitución principio 4.

- **CA-9.1** El sistema deberá crear la tabla `customers` con una migración nueva, sin modificar la migración 0001. Una base de datos recién preparada no tiene ningún cliente.
- **CA-9.2** La base de datos deberá rechazar por sí misma una fila con el `tax_id` repetido, con un `plan` distinto de los tres, con un `country` que no sean 2 letras mayúsculas, con un `company_name` vacío o de más de 120 caracteres, o con cualquier columna vacía (`NULL`).
- **CA-9.3** Deshacer la migración deberá borrar `customers` y dejar intacta `tax_rates`.

### RF-10. Datos de demostración

Origen: §3 «carga datos de demostración con un script de seed» **[P]**, §6 «datos de demo cargables con un comando» **[E]**.

- **CA-10.1** Cuando se ejecuta `python -m app.db.seed` sobre una base de datos preparada, el sistema deberá crear 10 clientes inventados que cubren los 7 países soportados y los 3 planes.
- **CA-10.2** Cuando se ejecuta otra vez, el sistema no deberá duplicar clientes ni fallar: un cliente cuyo `tax_id` ya existe se deja como está.
- **CA-10.3** Los clientes de demostración deberán pasar por las mismas reglas que `POST /customers` (RF-2 a RF-4).
- **CA-10.4** El seed no deberá modificar las tasas de impuesto ni los clientes que ya existan.

## 5. Contrato observable

Convenciones de §8.1: JSON en UTF-8, campos en `snake_case`, fechas ISO 8601 UTC.

**`POST /customers`**: registra un cliente. Cabecera `Content-Type: application/json`.

| Campo | Tipo | Regla |
| --- | --- | --- |
| `company_name` | texto | 1 a 120 caracteres imprimibles tras quitar los espacios sobrantes |
| `tax_id` | texto | Tras normalizar, 5 a 20 letras o dígitos; con `country` = `ES`, DNI, NIE o CIF con control correcto; único |
| `contact_email` | texto | `local@dominio`, hasta 254 caracteres |
| `country` | texto | 2 letras de un país soportado, tras normalizar |
| `plan` | texto | `starter`, `business` o `enterprise` |

Petición:

```json
{
  "company_name": "Acme Telecom S.L.",
  "tax_id": "B12345674",
  "contact_email": "compras@acme.example",
  "country": "ES",
  "plan": "business"
}
```

Respuesta `201`:

```json
{
  "id": 1,
  "company_name": "Acme Telecom S.L.",
  "tax_id": "B12345674",
  "contact_email": "compras@acme.example",
  "country": "ES",
  "plan": "business",
  "created_at": "2026-11-13T10:00:00Z"
}
```

**`GET /customers?q=&limit=&offset=`**: lista o busca. Respuesta `200`:

```json
{
  "items": [
    {
      "id": 1,
      "company_name": "Acme Telecom S.L.",
      "tax_id": "B12345674",
      "contact_email": "compras@acme.example",
      "country": "ES",
      "plan": "business",
      "created_at": "2026-11-13T10:00:00Z"
    }
  ],
  "total": 1
}
```

| Parámetro | Por defecto | Regla |
| --- | --- | --- |
| `q` | sin filtro | Hasta 120 caracteres; busca en el nombre y en el identificador |
| `limit` | 50 | Entero de 1 a 100, solo dígitos |
| `offset` | 0 | Entero de 0 a 1 000 000, solo dígitos |

**`GET /customers/{id}`**: ficha. Respuesta `200` con el mismo objeto que el `201` del alta.

**Respuestas**

| HTTP | `code` | `message` | Cuándo |
| --- | --- | --- | --- |
| 201 | — | — | Cliente registrado |
| 200 | — | — | Listado, búsqueda o ficha; también una preflight de CORS aceptada |
| 404 | `not_found` | Recurso no encontrado | Cliente inexistente, `{id}` que no es un identificador, ruta inexistente o con barra final |
| 405 | `method_not_allowed` | Método no permitido | Método que la ruta no admite (con `Allow`) |
| 409 | `conflict` | El recurso ya existe | `tax_id` ya registrado |
| 422 | `validation_error` | Datos no válidos | Cualquier fallo de RF-2, RF-3 y CA-5.8 a CA-5.9 |
| 500 | `internal_error` | Error interno del servidor | Fallo inesperado |
| otro | `http_error` | Error en la petición | Cualquier otro error HTTP que genere el framework |

**Mensajes de `details`** (únicos textos posibles en estas rutas):

| `field` | `message` | Abreviatura |
| --- | --- | --- |
| cualquiera de los cinco | Campo obligatorio | OBL |
| `company_name` | Debe tener entre 1 y 120 caracteres | NOM |
| `tax_id` | Debe tener entre 5 y 20 letras o dígitos | TID |
| `tax_id` | El DNI/NIF/CIF no es válido | ESP |
| `tax_id` | Tipo de identificador no soportado | KLM |
| `tax_id` | Ya existe un cliente con este identificador | DUP (solo con 409) |
| `contact_email` | Debe ser un email válido | EML |
| `country` | Debe ser un código de país de 2 letras | FMT |
| `country` | País no soportado | NSP |
| `plan` | Debe ser starter, business o enterprise | PLN |
| (nombre del campo) | Campo no permitido | NPE |
| `body` | El cuerpo debe ser un objeto JSON | BODY |
| `limit` | Debe ser un número entero entre 1 y 100 | LIM |
| `offset` | Debe ser un número entero entre 0 y 1000000 | OFF |
| `q` | Debe tener como máximo 120 caracteres | QLN |
| (nombre del parámetro) | Valor no válido | Solo en CA-7.3 |

## 6. Casos de prueba

Niveles: **U** = función pura, sin base de datos ni servidor; **D** = con una base de datos de prueba migrada, sin servidor; **I** = petición HTTP. Todos los identificadores son sintéticos y sus caracteres de control están comprobados con código.

### 6.1 Identificador fiscal español (RN-10) · U · `country` = `ES`

| # | Entrada | Resultado | Motivo |
| --- | --- | --- | --- |
| TI-1 | `12345678Z` | válido | DNI correcto |
| TI-2 | `12345678A` | ESP | Letra de control incorrecta |
| TI-3 | `1234567Z` | ESP | Faltan dígitos |
| TI-4 | `00000000T` | válido | Resto 0 corresponde a `T` |
| TI-5 | `12.345.678-z` | válido, queda `12345678Z` | Se normaliza |
| TI-6 | `X1234567L` | válido | NIE con `X` |
| TI-7 | `Y1234567X` | válido | NIE con `Y` |
| TI-8 | `Z1234567R` | válido | NIE con `Z` |
| TI-9 | `X1234567A` | ESP | Letra incorrecta |
| TI-10 | `B12345674` | válido | CIF con control de dígito |
| TI-11 | `B12345675` | ESP | Control incorrecto |
| TI-12 | `N1234567D` | válido | CIF con control de letra |
| TI-13 | `N12345674` | ESP | La entidad `N` exige letra |
| TI-14 | `K1234567X` | KLM | `K`, `L` y `M` no soportados |
| TI-15 | `L1234567X` y `M1234567X` | KLM | Igual que TI-14 |
| TI-16 | `B1234567D` | ESP | La entidad `B` exige dígito |
| TI-17 | `C12345674` | válido | La entidad `C` admite dígito |
| TI-18 | `C1234567D` | válido | La entidad `C` admite letra |
| TI-19 | `P1234567D` | válido | La entidad `P` exige letra |
| TI-20 | `A00000000` | válido | Control 0 como dígito |
| TI-21 | `Q0000000J` | válido | Control 0 como letra `J` |
| TI-22 | `I1234567D` | ESP | `I` no es una letra de entidad |
| TI-23 | `x-1234567-l` | válido, queda `X1234567L` | NIE normalizado |
| TI-24 | `123456789` | ESP | 9 dígitos sin letra |
| TI-25 | `99999999R` | válido | DNI más alto |
| TI-26 | `B1234567` | ESP | Falta el control |
| TI-27 | `T1234567X` | ESP | `T` no es entidad ni prefijo de NIE |

Los casos TI-1 a TI-14 son la tabla de §7.4 del documento 00.

### 6.2 Normalización y formato básico (RN-10, RN-11) · U

| # | Entrada | `country` | Resultado |
| --- | --- | --- | --- |
| TG-1 | `PT123456789` | PT | válido |
| TG-2 | `1234` | PT | TID (4 caracteres) |
| TG-3 | `12345` | PT | válido (5 caracteres) |
| TG-4 | 20 letras `A` | PT | válido |
| TG-5 | 21 letras `A` | PT | TID |
| TG-6 | `ab-12.34 5` | FR | válido, queda `AB12345` |
| TG-7 | `ABC$1234` | FR | TID |
| TG-8 | `12345678A` | FR | válido: fuera de España no se aplica el control |
| TG-9 | `ÑB12345` | DE | TID (letra no ASCII) |
| TG-10 | texto vacío | DE | TID |
| TG-11 | `- . -` | DE | TID (vacío tras normalizar) |
| TG-12 | `1234` | ES | TID: el formato básico va antes que el control español |

### 6.3 Altas válidas · I · con el reloj fijado en `2026-11-13T10:00:00Z`

| # | Petición | Resultado esperado |
| --- | --- | --- |
| AL-1 | El ejemplo de la sección 5 | 201 con exactamente la respuesta de la sección 5 |
| AL-2 | `company_name` «`  Acme   Telecom  S.L. `», `tax_id` `b-12.345.674`, `contact_email` «` compras@acme.example `», `country` «` es `», `plan` `business` | 201 con los mismos valores que AL-1 |
| AL-3 | Dos altas seguidas con identificadores distintos | `id` 1 y 2 |
| AL-4 | Un alta y después `GET /customers/{id}` y `GET /customers` | Los tres devuelven el mismo cliente |
| AL-5 | Cliente de `PT` con `tax_id` `PT123456789` y `plan` `starter` | 201 |
| AL-6 | Cliente de `ES` con el DNI `12345678Z` y `plan` `enterprise` | 201 |
| AL-7 | `company_name` de 120 caracteres | 201 |
| AL-8 | `contact_email` de 254 caracteres | 201 |
| AL-9 | Un alta por cada país soportado (ES, PT, FR, DE, IT, GB, US) | 201 en las siete |

### 6.4 Errores de validación del alta · I · todos 422 `validation_error` «Datos no válidos»

Salvo que se indique otra cosa, los campos que no aparecen en la columna llevan los valores de AL-1.

| # | Cambio sobre AL-1 | `details` esperado (como conjunto) |
| --- | --- | --- |
| VA-1 | Cuerpo `{}` | los cinco campos / OBL |
| VA-2 | `company_name` vacío | company_name/NOM |
| VA-3 | `company_name` solo con espacios | company_name/NOM |
| VA-4 | `company_name` de 121 caracteres | company_name/NOM |
| VA-5 | `company_name` = `5` (número) | company_name/NOM |
| VA-6 | `company_name` con un carácter de control (`\u0000`) | company_name/NOM |
| VA-7 | `tax_id` `12345678A` | tax_id/ESP |
| VA-8 | `tax_id` `K1234567X` | tax_id/KLM |
| VA-9 | `tax_id` `1234` y `country` `PT` | tax_id/TID |
| VA-10 | `tax_id` = `null` | tax_id/TID |
| VA-11 | `tax_id` `1234` (con `ES`) | tax_id/TID |
| VA-12 | `contact_email` `sin-arroba` | contact_email/EML |
| VA-13 | `contact_email` `a@b` | contact_email/EML |
| VA-14 | `contact_email` de 255 caracteres | contact_email/EML |
| VA-15 | `contact_email` = `7` (número) | contact_email/EML |
| VA-16 | `contact_email` `a b@c.es`, `a@@b.es`, `a@-b.es` y `ñ@b.es` | contact_email/EML en los cuatro |
| VA-17 | `country` `XX` | country/NSP |
| VA-18 | `country` `ESP` | country/FMT |
| VA-19 | Sin `country` y con `tax_id` `12345678A` | country/OBL (solo ese: CA-3.9) |
| VA-20 | `plan` `premium` | plan/PLN |
| VA-21 | `plan` `Business` | plan/PLN |
| VA-22 | `plan` = `null` | plan/PLN |
| VA-23 | Campo añadido `"id": 7` | id/NPE |
| VA-24 | `Company_Name` en lugar de `company_name`, y `created_at` añadido | Company_Name/NPE, created_at/NPE, company_name/OBL |
| VA-25 | `company_name` vacío, `tax_id` `12345678A`, `contact_email` `x` y `plan` `x` | company_name/NOM, tax_id/ESP, contact_email/EML, plan/PLN |
| VA-26 | `country` `XX` y `tax_id` `12` | country/NSP, tax_id/TID |
| VA-27 | `country` `xx` y `plan` `x` | country/NSP, plan/PLN |
| VA-28 | Cuerpo `no es json`, cuerpo `[1]` y cuerpo válido con `Content-Type: text/plain` | body/BODY en los tres |

Tras cada caso, `GET /customers` devuelve `total` = 0 (CA-1.5).

### 6.5 Conflictos · I

| # | Situación | Resultado esperado |
| --- | --- | --- |
| CO-1 | AL-1 dos veces | La segunda: 409 `conflict` «El recurso ya existe» con tax_id/DUP |
| CO-2 | AL-6 y después otro cliente con `tax_id` `12.345.678-z` | 409 |
| CO-3 | Cliente de `FR` con `tax_id` `B12345674` después de AL-1 | 409: la unicidad no depende del país |
| CO-4 | AL-1 y después la misma petición con `contact_email` `x` | 422 con contact_email/EML, sin conflicto |
| CO-5 | Tras CO-1, `GET /customers` | `total` = 1 |

### 6.6 Listado y búsqueda · I

Datos de partida, creados por la API en este orden:

| `id` | `company_name` | `tax_id` | `country` |
| --- | --- | --- | --- |
| 1 | Zeta Redes S.A. | A00000000 | ES |
| 2 | acme telecom s.l. | B12345674 | ES |
| 3 | COMPAÑÍA Ñandú | 12345678Z | ES |
| 4 | Telefónica Demo | PT123456789 | PT |
| 5 | 100% Fibra GmbH | DE1234567 | DE |
| 6 | Acme Cloud Ltd | GB7654321 | GB |

| # | Petición | `id` de `items`, en orden | `total` |
| --- | --- | --- | --- |
| LI-1 | sin parámetros | 5, 6, 2, 3, 4, 1 | 6 |
| LI-2 | `q=ACME` | 6, 2 | 2 |
| LI-3 | `q=compañía ñ` | 3 | 1 |
| LI-4 | `q=b1234` | 2 | 1 |
| LI-5 | `q=12.345.678-z` | 3 | 1 |
| LI-6 | `q=` con tres espacios | 5, 6, 2, 3, 4, 1 | 6 |
| LI-7 | `q=inexistente` | (vacío) | 0 |
| LI-8 | `q=%` | 5 | 1 |
| LI-9 | `q=_` | (vacío) | 0 |
| LI-10 | `limit=2` | 5, 6 | 6 |
| LI-11 | `limit=2&offset=4` | 4, 1 | 6 |
| LI-12 | `offset=6` | (vacío) | 6 |
| LI-13 | `q=acme&limit=1` | 6 | 2 |
| LI-14 | `q='; DROP TABLE customers;--` | (vacío) | 0, y después LI-1 sigue dando 6 |
| LI-15 | `limit=1&limit=3` | 5, 6, 2 | 6 |
| LI-16 | `desconocido=1` | 5, 6, 2, 3, 4, 1 | 6 |
| LI-17 | `q=telefonica` (sin tilde) | (vacío) | 0: las tildes no se equiparan |
| LI-18 | `q=  acme   telecom ` | 2 | 1 |
| LI-19 | sin parámetros, sobre una base de datos sin clientes | (vacío) | 0 |
| LI-20 | `limit=100` y `limit=1&offset=1000000` | 6 elementos, y vacío | 6 |

### 6.7 Parámetros inválidos del listado · I · todos 422 `validation_error`

| # | Petición | `details` esperado |
| --- | --- | --- |
| LP-1 | `limit=0` | limit/LIM |
| LP-2 | `limit=101` | limit/LIM |
| LP-3 | `limit=abc` | limit/LIM |
| LP-4 | `limit=1.5` | limit/LIM |
| LP-5 | `limit=-1` | limit/LIM |
| LP-6 | `limit=` (vacío) | limit/LIM |
| LP-7 | `limit=%2B5` (`+5`) | limit/LIM |
| LP-8 | `limit=%205` (espacio y 5) | limit/LIM |
| LP-9 | `limit=٥` (dígito no ASCII) | limit/LIM |
| LP-10 | `offset=-1` | offset/OFF |
| LP-11 | `offset=1000001` | offset/OFF |
| LP-12 | `offset=x` | offset/OFF |
| LP-13 | `offset=99999999999999999999999999999999` | offset/OFF |
| LP-14 | `limit=0&offset=-1` | limit/LIM, offset/OFF |
| LP-15 | `q` de 121 caracteres | q/QLN |

### 6.8 Ficha · I · con un único cliente de `id` 1

| # | Petición | Resultado esperado |
| --- | --- | --- |
| FI-1 | `GET /customers/1` | 200 con el cliente |
| FI-2 | `GET /customers/999` | 404 `not_found` «Recurso no encontrado», `details` vacío |
| FI-3 | `GET /customers/abc` | el mismo 404 |
| FI-4 | `GET /customers/0` | el mismo 404 |
| FI-5 | `GET /customers/-1` | el mismo 404 |
| FI-6 | `GET /customers/1.5` | el mismo 404 |
| FI-7 | `GET /customers/01` | el mismo 404 |
| FI-8 | `GET /customers/99999999999999999999` | el mismo 404, sin error interno |
| FI-9 | `GET /customers/1/` (barra final) | el mismo 404, sin redirección |

### 6.9 Protocolo, errores globales y CORS · I

| # | Petición o situación | Resultado esperado |
| --- | --- | --- |
| ER-1 | `PUT`, `PATCH`, `DELETE` y `OPTIONS` sin preflight sobre `/customers` | 405 `method_not_allowed`, `details` vacío, `Allow: GET, POST` |
| ER-2 | `HEAD /customers` | 405 con `Allow: GET, POST` y sin cuerpo |
| ER-3 | `POST`, `PUT`, `PATCH` y `DELETE` sobre `/customers/1` | 405 con `Allow: GET` |
| ER-4 | `GET /customers/` y `POST /customers/` (barra final) | 404 `not_found`, sin redirección |
| ER-5 | Fallo interno forzado (almacén de clientes no disponible) en las tres rutas | 500 `internal_error`, `details` vacío, sin «Traceback», rutas de archivo ni nombres de módulos |
| ER-6 | Ruta de prueba con un parámetro de ruta y uno de query tipados como enteros, llamada con textos | 422 `validation_error` con un detalle «Valor no válido» por parámetro |
| ER-7 | Ruta de prueba que lanza un error HTTP 418 con un texto interno | 418 `http_error` «Error en la petición», `details` vacío, sin el texto interno |
| ER-8 | `GET /customers` con `Origin: http://localhost:4200` | 200 con `Access-Control-Allow-Origin: http://localhost:4200` |
| ER-9 | Preflight de `GET` y de `POST` sobre `/customers` desde `http://localhost:4200` | 200 con `Access-Control-Allow-Origin` |
| ER-10 | `GET /customers` y su preflight con `Origin: http://otro-origen.example` | Sin `Access-Control-Allow-Origin` |
| ER-11 | Respuestas de AL-1, LI-1, FI-1, CO-1, VA-1, FI-2 y ER-1 | `Content-Type: application/json` |
| ER-12 | `GET`, `PUT` y `DELETE` sobre `/pricing/quote` | Siguen dando 405 con `Allow: POST` |

### 6.10 Persistencia · D

| # | Acción | Resultado esperado |
| --- | --- | --- |
| DB-1 | Preparar una base de datos vacía | Existe `customers`, con 0 filas |
| DB-2 | Guardar dos clientes con el mismo `tax_id` sin pasar por la API | El segundo se rechaza como identificador duplicado y solo queda uno |
| DB-3 | Insertar directamente una fila con `plan` = `gold` | Rechazada |
| DB-4 | Insertar directamente una fila con `country` = `es` | Rechazada |
| DB-5 | Insertar directamente una fila con `company_name` vacío, y otra con 121 caracteres | Rechazadas |
| DB-6 | Insertar directamente una fila con una columna `NULL` | Rechazada |
| DB-7 | Borrar el último cliente y guardar otro | El nuevo `id` no reutiliza el borrado |
| DB-8 | Deshacer la migración de clientes | `customers` desaparece y `tax_rates` conserva sus 7 filas |
| DB-9 | Comparar los modelos con la base de datos migrada | Sin diferencias |

### 6.11 Datos de demostración · D

| # | Acción | Resultado esperado |
| --- | --- | --- |
| SE-1 | Ejecutar el seed sobre una base de datos preparada | 10 clientes; cubren los 7 países y los 3 planes |
| SE-2 | Ejecutarlo otra vez | Siguen siendo 10 |
| SE-3 | Validar cada cliente de demostración con las reglas del alta | Todos válidos; los de `ES` tienen el control correcto |
| SE-4 | Ejecutarlo con un cliente ya registrado que usa el `tax_id` de uno de demostración | No falla, no cambia ese cliente y crea los otros 9 |
| SE-5 | Leer las tasas antes y después | Las mismas 7 |

## 7. Requisitos no funcionales

- **RNF-1 Capas:** el algoritmo del identificador fiscal es Python puro, sin FastAPI, Pydantic ni SQLAlchemy, y se prueba sin base de datos ni servidor (constitución, principio 3; tablas 6.1 y 6.2). El acceso a `customers` vive solo en la capa de repositorio.
- **RNF-2 Seguridad:** consultas solo mediante el ORM, con `q` como dato y nunca como SQL (LI-8, LI-9, LI-14); toda entrada validada con Pydantic; los errores no exponen trazas, rutas ni nombres internos (ER-5, ER-7).
- **RNF-3 Idioma:** los únicos textos de error posibles son los de la sección 5, en español; los nombres de campo, en inglés y `snake_case`.
- **RNF-4 Documentación:** los tres endpoints aparecen en la documentación interactiva con su ejemplo de petición y de respuesta.
- **RNF-5 Datos personales:** los clientes de demostración son inventados, con identificadores sintéticos y correos de dominios `.example` (§6 del 00).
- **RNF-6 Simplicidad:** no se añade ninguna dependencia; el email se valida con una regla propia (decisión D-1).

## 8. Casos límite

- **Identificador con separadores o minúsculas:** se normaliza antes de validar, de guardar y de comparar (TI-5, TI-23, AL-2, CO-2, LI-5).
- **Controles del CIF:** entidades que exigen letra, que exigen dígito y que admiten ambos (TI-10 a TI-13, TI-16 a TI-21).
- **NIF especiales:** `K`, `L` y `M` se rechazan con su propio mensaje (TI-14, TI-15).
- **Identificador con forma española en otro país:** no se le aplica el control (TG-8), pero sigue siendo único (CO-3).
- **País inválido junto a otros errores:** se informa de todo a la vez (VA-19, VA-26, VA-27).
- **Longitudes en el límite:** 120 y 121 caracteres en el nombre, 254 y 255 en el email, 5 y 20 en el identificador (AL-7, AL-8, VA-4, VA-14, TG-2 a TG-5).
- **Validación antes que conflicto:** CO-4.
- **Búsqueda:** mayúsculas no ASCII, comodines de SQL, comillas, solo espacios y tildes (LI-3, LI-6, LI-8, LI-9, LI-14, LI-17).
- **Paginación:** más allá del final, límites extremos y parámetros repetidos (LI-11, LI-12, LI-15, LI-20).
- **Identificador de ruta raro:** texto, cero, negativo, decimal, ceros a la izquierda y número enorme (FI-3 a FI-8).
- **Métodos no permitidos:** la cabecera `Allow` lista todos los métodos de la ruta (ER-1 a ER-3, ER-12).

## 9. Fuera de alcance

- Editar o borrar clientes (§3 del 00).
- Simulaciones y su historial: spec posterior. La ficha de esta spec solo devuelve los datos del cliente.
- Las pantallas del dashboard: specs de frontend.
- Equiparar letras con y sin tilde en la búsqueda, y el orden alfabético español de la `ñ`.
- Direcciones de correo con caracteres no ASCII o con comillas, y comprobar que el buzón existe.
- Identificadores fiscales de otros países más allá del formato básico; NIF `K`, `L` y `M`; validar que el identificador exista en la AEAT.
- Autenticación, límites de peticiones y de tamaño del cuerpo (ADR 0007; 002 sección 9).

## 10. Criterios de finalización

**Funcionalidad**

- [x] Cada caso de las tablas 6.1 a 6.11 tiene un test automático en el nivel que indica y todos pasan.
- [x] Cada criterio CA-x de la sección 4 está cubierto por al menos un test que lo cita por su identificador y pasa.
- [x] `POST /customers` con el ejemplo de la sección 5 devuelve exactamente la respuesta de la sección 5 (con el reloj fijado).
- [x] Los tres endpoints aparecen en la documentación interactiva con su ejemplo.
- [x] Con el servidor arrancado de verdad, un alta, una búsqueda y una ficha por línea de comandos funcionan, y `python -m app.db.seed` carga los 10 clientes. El comando queda confirmado en `AGENTS.md`.
- [x] Todos los tests de 001 y 002 siguen pasando sin haberlos modificado.

**Cumplimiento de la constitución** (comprobación en revisión)

- [x] Principio 1: no se añade ninguna dependencia; el ADR 0009 documenta la convención del CIF.
- [x] Principio 2: cada commit de código cita el RF-x o CA-x de esta spec que implementa (los 19 commits con código, comprobados en T-20).
- [x] Principio 3: el algoritmo del identificador no importa nada del framework ni del acceso a datos; los routers no contienen reglas de negocio ni SQL.
- [x] Principio 4: el esquema cambia solo con una migración nueva; la 0001 no se toca.
- [x] Principio 5: la suite completa pasa en cada commit, comprobado uno a uno en un clon limpio; cada regla de negocio tiene test unitario y cada endpoint, test de integración.
- [x] Principio 5: las correcciones al código generado están anotadas en `ai-workspace/ai-review-log.md` (entradas 17 a 20). El autor revisó la spec y el trabajo realizado y lo aprobó.
- [x] Principio 6: `ruff check`, `ruff format --check` y `mypy` pasan sin errores; toda entrada se valida.

## 11. Decisiones tomadas al redactar

El autor delegó la redacción y confirmó estas decisiones **[P]** al revisar la spec. Ninguna contradice el enunciado ni el documento 00.

- **D-1. Email sin biblioteca.** Se valida con una regla propia (CA-2.2), parecida a la de los formularios HTML. `EmailStr` de Pydantic exige instalar `email-validator`, una dependencia nueva que pediría un ADR. Alternativa si se prefiere: añadirla con su ADR.
- **D-2. Textos del 409.** Primer nivel «El recurso ya existe», genérico como los demás (002 CA-6.2); el texto del flujo 1 del 00, «Ya existe un cliente con este identificador», va en el detalle de `tax_id` para que el formulario lo pinte junto al campo.
- **D-3. `{id}` mal formado.** Responde 404 y no 422: es parte de la dirección, no un dato de entrada.
- **D-4. Búsqueda sin distinguir mayúsculas también en `ñ` y tildes.** SQLite solo lo hace con letras ASCII, así que se registra una función propia en la conexión. No se equiparan letras con y sin tilde.
- **D-5. Orden del listado.** Por nombre y, a igualdad, por `id`. El 00 no lo fija.
- **D-6. Espacios en `company_name`.** «Sin espacios sobrantes» (§8.3) se interpreta como quitar los exteriores y compactar los interiores.
- **D-7. `country` sin clave foránea a `tax_rates`.** §8.5 no la pide, y 001 permite quitar una tasa (caso C-4). Qué hacer con un cliente cuyo país deja de estar soportado es de la spec de simulaciones.
- **D-8. Sin cabecera `Location` en el 201.** El 00 no la menciona y la respuesta ya lleva el `id`.
- **D-9. Límite de `offset`.** 1 000 000, para rechazar con 422 los números que SQLite no puede usar.
- **D-10. `plan` sin normalizar.** Lo elige un desplegable; `Business` se rechaza.
- **D-11. Índice de `company_name`.** Se crea porque lo pide §8.5, aunque la búsqueda por fragmento no puede aprovecharlo.
- **D-12. El seed solo crea clientes.** Las simulaciones de demostración llegarán con su spec.
- **D-13. `Allow` completa.** El framework solo devuelve los métodos de una de las rutas que comparten dirección; se calcula la lista completa.
- **D-14. Unicidad del identificador entre países.** §8.5 define `tax_id` como único, sin el país.

No hay dudas abiertas que bloqueen la implementación.

## 12. Historial de cambios

| Versión | Cambio |
| --- | --- |
| 1.0 | Versión inicial, redactada por delegación del autor tras comprobar con un prototipo desechable los comportamientos de FastAPI, Starlette, Pydantic y SQLite en los que se apoya |
| 1.0 (cierre) | Sin cambios en los requisitos. Implementada según `plan.md` y `tasks.md`: 744 tests en verde (383 de 001 y 002, sin modificar ninguno), verificación completa en un clon limpio con un entorno virtual nuevo y en cada commit de código, los 56 CA con al menos un test que los cita y pasa, y los 151 casos con test en su nivel. Dos decisiones del plan se corrigieron al implementar (entradas 17 y 18 del log) y la documentación dejó de anunciar el 422 propio del framework (entrada 19) |
| 1.0 (revisión) | Sin cambios en los requisitos. Revisión del autor tras una verificación independiente en un clon limpio con un entorno virtual nuevo (744 tests, ruff, mypy, `alembic check` y el seed dos veces), la trazabilidad de los 56 CA y los 151 casos, y un arranque real con alta, duplicado, búsqueda, ficha y cotización. El autor confirmó las decisiones D-1 a D-14. Spec cerrada |
