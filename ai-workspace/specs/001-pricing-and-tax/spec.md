# 001 — Precios por tramos e impuestos

Estado: aprobada (2026-11-14) · Fuente de verdad: `ai-workspace/specs/00-spec-first.md` · Constitución: `ai-workspace/docs/constitution.md`

Leyenda de origen: **[E]** viene del enunciado y no se puede contradecir; **[P]** es una propuesta del documento 00 o una decisión tomada al aclarar esta spec.

## 1. Contexto y objetivo

El comercial necesita saber en segundos cuánto pagará un cliente al mes según su número de usuarios, con el desglose por tramo y el impuesto de su país. Es el cálculo del que dependen el simulador con slider (UC-4) y el guardado de simulaciones (UC-5), así que tiene que ser exacto, estar en un único sitio y poder probarse sin base de datos ni interfaz.

**Objetivo:** dados un número de usuarios y un país, devolver sin guardar nada el coste mensual con precio acumulativo por tramos, el impuesto del país y el total, todo en céntimos de euro y con el desglose de cada tramo.

**Por qué ahora:** es la primera pieza del orden de construcción (§11, «dominio puro, con tests primero») y la que más pesa en «calidad del software»: el evaluador comprobará los tramos exactos.

## 2. Usuarios

- **Comercial** (único usuario, sin autenticación, §2 [P]): mueve el slider y ve la factura proyectada.
- **Dashboard Angular** (consumidor técnico): llama a la cotización tras cada cambio del slider y pinta el resultado.
- **Evaluadores** (audiencia indirecta): leen esta spec y comprueban que los tests salen de la tabla de casos.

## 3. Historias de usuario

- **HU-1.** Como comercial, quiero introducir un número de usuarios y ver al instante el coste mensual desglosado por tramo para explicar al cliente de dónde sale cada euro.
- **HU-2.** Como comercial, quiero ver el impuesto de su país y el total con impuestos para dar un precio final sin cálculos a mano.
- **HU-3.** Como comercial, quiero recibir un error claro cuando un dato no es válido para corregirlo sin adivinar qué pasa.

## 4. Requisitos funcionales

### RF-1. Coste base acumulativo por tramos

Origen: RN-1 **[E]**, §7.1.

- **CA-1.1** El sistema deberá calcular el subtotal como la suma de lo que cobra cada tramo por los usuarios que caen en él: tramo 1 (usuarios 1 a 10) a 1000 céntimos por usuario, tramo 2 (11 a 50) a 800 y tramo 3 (51 en adelante) a 500.
- **CA-1.2** Cuando se cotizan 60 usuarios, el sistema deberá devolver `subtotal_cents` = 47000, no 30000 (no es precio por volumen).
- **CA-1.3** El sistema deberá producir para cada valor de la tabla 7.1 exactamente el coste base que indica esa tabla.

### RF-2. Desglose por tramo

Origen: §3 «desglose por tramo» **[P]**, ejemplo de §8.3 **[P]**.

- **CA-2.1** El sistema deberá devolver siempre `tiers` con exactamente 3 elementos, ordenados por `tier` 1, 2 y 3, aunque algún tramo tenga 0 unidades.
- **CA-2.2** El sistema deberá devolver en cada tramo los límites fijos `from_users`/`to_users`: 1/10, 11/50 y 51/`null`.
- **CA-2.3** El sistema deberá cumplir en cada tramo que `amount_cents` = `units` × `unit_price_cents`.
- **CA-2.4** El sistema deberá cumplir que la suma de `units` de los 3 tramos es igual a `users` y que la suma de `amount_cents` es igual a `subtotal_cents`.

### RF-3. Validación del número de usuarios

Origen: RN-2 **[P]**, §10 supuestos 8 y 9 **[P]**, aclaración 2 (validación estricta) **[P]**.

- **CA-3.1** El sistema deberá aceptar como `users` cualquier entero JSON entre 0 y 100 000, ambos incluidos.
- **CA-3.2** Cuando `users` es 0, el sistema deberá devolver `subtotal_cents`, `tax_cents` y `total_cents` iguales a 0 y los 3 tramos con `units` = 0.
- **CA-3.3** Si `users` es negativo o mayor que 100 000, entonces el sistema deberá responder 422 con `code` = `validation_error` y un detalle con `field` = `users`.
- **CA-3.4** Si `users` no es un entero JSON (un número con parte decimal, también 15.0; un texto, también "15"; un booleano; `null`), entonces el sistema deberá responder 422 con `code` = `validation_error` y un detalle con `field` = `users`.
- **CA-3.5** Si falta `users`, entonces el sistema deberá responder 422 con `code` = `validation_error` y un detalle con `field` = `users`.

### RF-4. Impuesto según el país

Origen: RN-3 **[E]**, RN-4 **[P]**, §10 supuesto 4 **[P]**.

- **CA-4.1** El sistema deberá aplicar la tasa de impuesto configurada para el país indicado y devolverla en `tax_rate_bp` (puntos básicos: 2100 = 21 %).
- **CA-4.2** El sistema deberá usar estas tasas: ES 2100, PT 2300, FR 2000, DE 1900, IT 2200, GB 2000, US 0.
- **CA-4.3** El sistema deberá cumplir que `total_cents` = `subtotal_cents` + `tax_cents`.
- **CA-4.4** Cuando el país es US, el sistema deberá devolver `tax_rate_bp` = 0, `tax_cents` = 0 y `total_cents` = `subtotal_cents`.

### RF-5. País normalizado y soportado

Origen: RN-4 **[P]**, §10 supuesto 5 **[P]**, aclaración 3 (normalizar) **[P]**.

- **CA-5.1** Cuando `country` llega en minúsculas o con espacios al principio o al final, el sistema deberá pasarlo a mayúsculas, quitar esos espacios y cotizar igual que con el código normalizado («es» y « ES » dan el mismo resultado que «ES»).
- **CA-5.2** Si `country` normalizado no está en la lista de RF-4, entonces el sistema deberá responder 422 con `code` = `validation_error` y un detalle con `field` = `country` y `message` = «País no soportado».
- **CA-5.3** Si falta `country`, es `null`, no es un texto o queda vacío tras normalizarlo, entonces el sistema deberá responder 422 con `code` = `validation_error` y un detalle con `field` = `country`.

### RF-6. Redondeo del impuesto

Origen: RN-5 **[P]**.

- **CA-6.1** El sistema deberá calcular el impuesto en céntimos como `subtotal_cents` × `tax_rate_bp` / 10 000 y redondearlo una sola vez al céntimo entero, con la regla «mitad hacia arriba».
- **CA-6.2** Cuando el cálculo exacto da una fracción de céntimo de 0,5 o más, el sistema deberá redondear al céntimo superior; cuando da menos de 0,5, al inferior.
- **CA-6.3** El sistema no deberá usar en ningún paso del cálculo números en coma flotante: el resultado de los casos de la sección 7 tiene que ser idéntico en todas las ejecuciones.

### RF-7. Formato de los importes

Origen: RN-6 **[P]**, §8.1 **[P]**, constitución principio 4.

- **CA-7.1** El sistema deberá devolver todos los importes como enteros en céntimos de euro, en campos terminados en `_cents`, y las tasas como enteros en puntos básicos, en campos terminados en `_bp`.
- **CA-7.2** El sistema deberá devolver `currency` = `"EUR"` en toda cotización. La conversión a otras divisas no forma parte de esta funcionalidad (RN-7).

### RF-8. Cotización sin guardar

Origen: §3 y §8.2 `POST /pricing/quote` **[P]**, ADR 0004 **[P]**.

- **CA-8.1** Cuando recibe una petición válida en `POST /pricing/quote`, el sistema deberá responder 200 con la cotización completa del contrato (sección 5).
- **CA-8.2** El sistema no deberá guardar nada al cotizar: tras cualquier número de cotizaciones, el número de simulaciones guardadas no cambia.
- **CA-8.3** Cuando recibe dos veces la misma petición, el sistema deberá devolver dos respuestas idénticas.

### RF-9. Rechazo de campos no definidos

Origen: §8.1 «el cliente no envía nunca precios ni totales» **[P]**, aclaración 4 (rechazar) **[P]**.

- **CA-9.1** Si la petición incluye un campo distinto de `users` y `country` (por ejemplo `subtotal_cents` o `tax_rate_bp`), entonces el sistema deberá responder 422 con `code` = `validation_error` y un detalle con `field` igual al nombre de ese campo.

### RF-10. Formato único de error

Origen: §8.4 **[P]**.

- **CA-10.1** Si la petición no es válida por cualquier motivo, entonces el sistema deberá responder con el formato `{"error": {"code", "message", "details"}}`, con `details` como lista de objetos `{field, message}`, un elemento por cada campo inválido.
- **CA-10.2** Si la petición tiene varios campos inválidos a la vez, entonces el sistema deberá incluir en `details` un elemento por cada uno.
- **CA-10.3** Si el cuerpo no es JSON válido o no es un objeto JSON, entonces el sistema deberá responder 422 con `code` = `validation_error`.
- **CA-10.4** Si se produce un fallo inesperado, entonces el sistema deberá responder 500 con `code` = `internal_error` y un mensaje genérico, sin trazas ni detalles internos.
- **CA-10.5** El sistema deberá escribir en español los `message` de los errores.

## 5. Contrato observable

**`POST /pricing/quote`**: cotiza sin guardar.

Petición (JSON, solo estos dos campos):

| Campo | Tipo | Regla |
| --- | --- | --- |
| `users` | entero | 0 ≤ `users` ≤ 100 000; solo se aceptan enteros JSON |
| `country` | texto | Código ISO de 2 letras de la lista soportada; se normaliza a mayúsculas y sin espacios |

Respuesta `200`, ejemplo con `{ "users": 15, "country": "ES" }` (§8.3):

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

Errores (formato de §8.4):

```json
{
  "error": {
    "code": "validation_error",
    "message": "Datos no válidos",
    "details": [ { "field": "country", "message": "País no soportado" } ]
  }
}
```

| HTTP | `code` | Cuándo |
| --- | --- | --- |
| 200 | (sin error) | Petición válida |
| 422 | `validation_error` | `users` fuera de rango o no entero; `country` ausente o no soportado; campo no definido; cuerpo no JSON |
| 500 | `internal_error` | Fallo inesperado, con mensaje genérico |

## 6. Casos de prueba

### 6.1 Precio por tramos (RN-1, RN-2), con país US para aislar el subtotal

| # | `users` | Tramo 1 (units / cents) | Tramo 2 (units / cents) | Tramo 3 (units / cents) | `subtotal_cents` |
| --- | --- | --- | --- | --- | --- |
| P-1 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 |
| P-2 | 1 | 1 / 1000 | 0 / 0 | 0 / 0 | 1000 |
| P-3 | 10 | 10 / 10000 | 0 / 0 | 0 / 0 | 10000 |
| P-4 | 11 | 10 / 10000 | 1 / 800 | 0 / 0 | 10800 |
| P-5 | 15 | 10 / 10000 | 5 / 4000 | 0 / 0 | 14000 |
| P-6 | 50 | 10 / 10000 | 40 / 32000 | 0 / 0 | 42000 |
| P-7 | 51 | 10 / 10000 | 40 / 32000 | 1 / 500 | 42500 |
| P-8 | 60 | 10 / 10000 | 40 / 32000 | 10 / 5000 | 47000 |
| P-9 | 100 | 10 / 10000 | 40 / 32000 | 50 / 25000 | 67000 |
| P-10 | 100000 | 10 / 10000 | 40 / 32000 | 99950 / 49975000 | 50017000 |

### 6.2 Impuestos (RN-3, RN-4)

| # | `users` | `country` | `subtotal_cents` | `tax_rate_bp` | `tax_cents` | `total_cents` |
| --- | --- | --- | --- | --- | --- | --- |
| T-1 | 0 | ES | 0 | 2100 | 0 | 0 |
| T-2 | 1 | PT | 1000 | 2300 | 230 | 1230 |
| T-3 | 11 | DE | 10800 | 1900 | 2052 | 12852 |
| T-4 | 15 | ES | 14000 | 2100 | 2940 | 16940 |
| T-5 | 15 | US | 14000 | 0 | 0 | 14000 |
| T-6 | 51 | FR | 42500 | 2000 | 8500 | 51000 |
| T-7 | 60 | ES | 47000 | 2100 | 9870 | 56870 |
| T-8 | 100 | GB | 67000 | 2000 | 13400 | 80400 |
| T-9 | 10 | IT | 10000 | 2200 | 2200 | 12200 |
| T-10 | 100000 | ES | 50017000 | 2100 | 10503570 | 60520570 |
| T-11 | 15 | "es" | 14000 | 2100 | 2940 | 16940 |
| T-12 | 15 | " ES " | 14000 | 2100 | 2940 | 16940 |

### 6.3 Regla de redondeo (RN-5)

Con las tasas configuradas el impuesto siempre sale exacto, así que estos casos prueban la regla de cálculo con tasas hipotéticas, no a través de la API.

| # | `subtotal_cents` | `tax_rate_bp` | Valor exacto | `tax_cents` esperado |
| --- | --- | --- | --- | --- |
| R-1 | 1000 | 2105 | 210,5 | 211 |
| R-2 | 1000 | 2104 | 210,4 | 210 |
| R-3 | 1000 | 2106 | 210,6 | 211 |
| R-4 | 1 | 5000 | 0,5 | 1 |
| R-5 | 1 | 4999 | 0,4999 | 0 |

### 6.4 Errores (todos 422 con `code` = `validation_error`)

| # | Petición | `field` en `details` |
| --- | --- | --- |
| E-1 | `{"users": -1, "country": "ES"}` | `users` |
| E-2 | `{"users": 100001, "country": "ES"}` | `users` |
| E-3 | `{"users": 1.5, "country": "ES"}` | `users` |
| E-4 | `{"users": 15.0, "country": "ES"}` | `users` |
| E-5 | `{"users": "15", "country": "ES"}` | `users` |
| E-6 | `{"users": true, "country": "ES"}` | `users` |
| E-7 | `{"users": null, "country": "ES"}` | `users` |
| E-8 | `{"country": "ES"}` | `users` |
| E-9 | `{"users": 15, "country": "XX"}` | `country`, con `message` «País no soportado» |
| E-10 | `{"users": 15}` | `country` |
| E-11 | `{"users": 15, "country": ""}` | `country` |
| E-12 | `{"users": 15, "country": 34}` | `country` |
| E-13 | `{"users": 15, "country": "ES", "subtotal_cents": 1}` | `subtotal_cents` |
| E-14 | `{"users": -1, "country": "XX"}` | `users` y `country` (dos elementos) |
| E-15 | cuerpo `no es json` | (sin campo concreto) |
| E-16 | cuerpo `[15, "ES"]` | (sin campo concreto) |

## 7. Requisitos no funcionales

- **RNF-1 Exactitud:** cero uso de coma flotante en el cálculo; todos los casos de la sección 6 dan el resultado exacto (§6 «precisión del dinero» [P]).
- **RNF-2 Testabilidad:** el cálculo de tramos, impuesto y redondeo se puede probar sin servidor HTTP ni base de datos (constitución, principio 3; §5 capas [P]).
- **RNF-3 Configurabilidad:** las tasas por país se configuran como datos, no en la lógica; cambiar o añadir una tasa no exige tocar el cálculo (RN-4, ADR 0006 [P]).
- **RNF-4 Una sola fuente de verdad:** el precio solo lo calcula el backend; el frontend no repite el cálculo (ADR 0004 [P]).
- **RNF-5 Rendimiento:** una cotización responde en menos de 200 ms en local (objetivo, §6 [P]).
- **RNF-6 Seguridad:** los errores no exponen trazas, rutas ni nombres internos (§6 [P]).
- **RNF-7 Idioma:** mensajes de error en español; nombres de campos en inglés y `snake_case` (§6 y §8.1 [P]).
- **RNF-8 Documentación:** el endpoint aparece en la documentación interactiva de la API con su ejemplo de petición y respuesta (§3 [P]).

## 8. Casos límite

- **0 usuarios:** válido, todo a 0 y 3 tramos con 0 unidades (P-1, T-1).
- **Fronteras entre tramos:** 10/11 y 50/51 (P-3, P-4, P-6, P-7).
- **Máximo:** 100 000 se acepta (P-10, T-10) y 100 001 se rechaza (E-2).
- **Enteros disfrazados:** 15.0, "15" y `true` se rechazan (E-4 a E-6).
- **País sin impuesto:** US devuelve tasa 0 con total igual al subtotal (T-5).
- **País en minúsculas o con espacios:** se normaliza (T-11, T-12).
- **Varios errores a la vez:** se informa de todos (E-14).
- **Intento de imponer precios:** un campo de importe en la petición se rechaza (E-13).
- **Redondeo en el 0,5 exacto:** sube al céntimo siguiente (R-1, R-4).

## 9. Fuera de alcance

- Guardar simulaciones, el historial y los campos de almacenamiento y llamadas a la API (RN-8, RN-9, `POST /simulations`): van en una spec posterior.
- Cotizar a partir de un cliente registrado: aquí el país llega en la petición.
- Conversión a otras divisas (RN-7, solo en frontend) y la pantalla del simulador.
- Impuestos especiales: IGIC de Canarias, Ceuta y Melilla, inversión del sujeto pasivo en la UE e impuesto sobre ventas de cada estado de EE. UU. (§7.2).
- Efecto del plan elegido en el precio (§10 supuesto 3).
- Descuentos, promociones, periodos distintos del mensual y prorrateos.
- Autenticación y límites de peticiones.

## 10. Criterios de finalización

- [ ] Cada fila de las tablas 6.1, 6.2, 6.3 y 6.4 tiene un test automático y todos pasan.
- [ ] Cada criterio CA-x de la sección 4 está cubierto por al menos un test que lo cita.
- [ ] `POST /pricing/quote` responde exactamente el ejemplo de la sección 5 con `{ "users": 15, "country": "ES" }`.
- [ ] Ningún cálculo usa coma flotante; se comprueba en la revisión del código.
- [ ] El cálculo de precio e impuesto tiene tests que no levantan servidor ni base de datos.
- [ ] Las tasas por país se leen de configuración de datos, no de la lógica.
- [ ] Tras cotizar, el número de simulaciones guardadas sigue igual.
- [ ] El endpoint aparece en la documentación interactiva con su ejemplo.
- [ ] Lint y tipado pasan sin errores.
- [ ] El código generado por IA está revisado y las correcciones están anotadas en `ai-workspace/ai-review-log.md`.

## 11. Dudas abiertas

- **[NECESITA ACLARACIÓN] D-1. Nombre del campo de usuarios.** La cotización usa `users` (§8.3), pero la simulación usa `active_users` (§8.3, §8.5). Recomendación: mantener `users` en la cotización tal como fija el documento 00 y decidir en la spec de simulaciones si se unifican.
- **[NECESITA ACLARACIÓN] D-2. Devolver el país en la respuesta.** El ejemplo de §8.3 no incluye `country`. Devolverlo normalizado ayudaría al frontend a confirmar con qué país se cotizó, pero cambiaría el contrato de §8.3. Esta spec mantiene el contrato tal cual.
- **[NECESITA ACLARACIÓN] D-3. Valores de las tasas.** Los porcentajes de RN-4 son supuestos de ejemplo (§10 supuesto 4, «Documentar»). Se usan como definitivos salvo que la empresa diga otra cosa.
