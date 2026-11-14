# 001 — Precios por tramos e impuestos

Estado: v1.2 aprobada (2026-11-14) · Fuente de verdad: `ai-workspace/specs/00-spec-first.md` · Constitución: `ai-workspace/docs/constitution.md` · Consumida por: `ai-workspace/specs/002-pricing-quote-api/spec.md` y la futura spec de simulaciones

Leyenda de origen: **[E]** viene del enunciado y no se puede contradecir; **[P]** es una propuesta del documento 00 o una decisión tomada al aclarar o revisar esta spec.

## 1. Contexto y objetivo

El comercial necesita saber en segundos cuánto pagará un cliente al mes según su número de usuarios, con el desglose por tramo y el impuesto de su país. Ese cálculo lo usan la cotización en vivo (spec 002) y el guardado de simulaciones (spec posterior), así que tiene que ser exacto, estar en un único sitio y poder probarse sin interfaz ni servidor web.

**Objetivo:** dados un número de usuarios y un código de país ya normalizado, calcular el coste mensual con precio acumulativo por tramos, el impuesto del país según la tabla de tasas configurada y el total, todo en céntimos de euro y con el desglose de cada tramo.

**Alcance:** el núcleo del cálculo y la tabla de tasas de impuesto. Cómo llega la petición, cómo se valida el JSON y cómo se presentan los errores al exterior es la spec 002.

**Por qué ahora:** es la primera pieza del orden de construcción (§11, «dominio puro, con tests primero») y la que más pesa en «calidad del software»: el evaluador comprobará los tramos exactos.

## 2. Usuarios

- **Comercial** (usuario final, de forma indirecta): ve el resultado de este cálculo en el simulador.
- **Specs consumidoras:** la 002 (cotización en vivo) y la futura de simulaciones usan la interfaz de la sección 5.
- **Evaluadores** (audiencia indirecta): leen esta spec y comprueban que los tests salen de las tablas de casos.

## 3. Historias de usuario

- **HU-1.** Como comercial, quiero saber el coste mensual desglosado por tramo para un número de usuarios, para explicar al cliente de dónde sale cada euro.
- **HU-2.** Como comercial, quiero saber el impuesto del país del cliente y el total con impuestos, para dar un precio final sin cálculos a mano.
- **HU-3.** Como spec consumidora, quiero que el cálculo distinga «usuarios no válidos» de «país no soportado», para traducir cada caso al error que corresponda.

## 4. Requisitos funcionales

### RF-1. Coste base acumulativo por tramos

Origen: RN-1 **[E]**, §7.1.

- **CA-1.1** El sistema deberá calcular el subtotal como la suma de lo que cobra cada tramo por los usuarios que caen en él: tramo 1 (usuarios 1 a 10) a 1000 céntimos por usuario, tramo 2 (11 a 50) a 800 y tramo 3 (51 en adelante) a 500.
- **CA-1.2** Cuando se calculan 60 usuarios, el sistema deberá devolver `subtotal_cents` = 47000, no 30000 (no es precio por volumen).
- **CA-1.3** El sistema deberá producir para cada fila de la tabla 6.1 exactamente el desglose y el subtotal que indica.
- **CA-1.4** El sistema deberá calcular `amount_cents` de cada tramo y `subtotal_cents` como productos y sumas exactas de enteros, sin ningún redondeo: el único importe que se redondea es el impuesto (RF-6).

### RF-2. Desglose por tramo

Origen: §3 «desglose por tramo» **[P]**, ejemplo de §8.3 **[P]**.

- **CA-2.1** El sistema deberá devolver siempre `tiers` con exactamente 3 elementos, ordenados por `tier` 1, 2 y 3, aunque algún tramo tenga 0 unidades.
- **CA-2.2** El sistema deberá devolver en cada tramo los límites fijos `from_users`/`to_users`: 1/10, 11/50 y 51/sin límite.
- **CA-2.3** El sistema deberá cumplir en cada tramo que `amount_cents` = `units` × `unit_price_cents`.
- **CA-2.4** El sistema deberá cumplir que la suma de `units` de los 3 tramos es igual a `users` y que la suma de `amount_cents` es igual a `subtotal_cents`.

Nota sobre el tramo 1 **[P]**: el enunciado **[E]** lo describe como «0 a 10». La spec muestra `from_users` = 1 porque el usuario número 0 no existe y con 0 usuarios no se cobra nada. Es una desviación consciente de la redacción, no del cálculo: el importe es idéntico con cualquiera de las dos lecturas (§7.1 del documento 00).

### RF-3. Rango del número de usuarios

Origen: RN-2 **[P]**, §10 supuestos 8 y 9 **[P]**. La validación del formato de entrada (entero JSON, campo ausente, mensajes) está en 002 RF-2.

- **CA-3.1** El sistema deberá aceptar como `users` cualquier número entero entre 0 y 100 000, ambos incluidos.
- **CA-3.2** Cuando `users` es 0, el sistema deberá devolver `subtotal_cents`, `tax_cents` y `total_cents` iguales a 0 y los 3 tramos con `units` = 0.
- **CA-3.3** Si `users` es menor que 0 o mayor que 100 000, entonces el sistema deberá rechazar el cálculo con el error de dominio «usuarios no válidos», sin producir ningún resultado.
- **CA-3.4** Si `users` no es un número entero (también si es un valor lógico verdadero o falso), entonces el sistema deberá rechazar el cálculo con el error de dominio «usuarios no válidos».
- **CA-3.5** Si `users` y el país no son válidos a la vez, entonces el sistema deberá rechazar el cálculo con «usuarios no válidos».

### RF-4. Impuesto según el país

Origen: RN-3 **[E]**, RN-4 **[P]**, §10 supuestos 4 y 5 **[P]**.

- **CA-4.1** El sistema deberá aplicar la tasa de impuesto configurada para el país indicado y devolverla en `tax_rate_bp` (puntos básicos: 2100 = 21 %).
- **CA-4.2** El sistema deberá considerar **soportados** exactamente los países que tienen una tasa configurada.
- **CA-4.3** El sistema deberá tener esta configuración por defecto en cuanto se prepara una base de datos vacía, sin cargar datos de demostración: ES 2100, PT 2300, FR 2000, DE 1900, IT 2200, GB 2000, US 0. La tabla 6.2 se ejecuta con esta configuración.
- **CA-4.4** El sistema deberá cumplir que `total_cents` = `subtotal_cents` + `tax_cents`.
- **CA-4.5** Cuando la tasa del país es 0, el sistema deberá devolver `tax_rate_bp` = 0, `tax_cents` = 0 y `total_cents` = `subtotal_cents`.
- **CA-4.6** Si el país no tiene tasa configurada, entonces el sistema deberá rechazar el cálculo con el error de dominio «país no soportado», sin producir ningún resultado.
- **CA-4.7** El sistema deberá buscar el país con el código exacto recibido, sin normalizarlo: un código en minúsculas, con espacios o vacío se trata como país no soportado. La normalización es de 002 RF-3.

### RF-5. País normalizado y soportado

**Movido a 002 RF-3** (normalización y validación del formato del país). Lo que era CA-5.4 (país sin tasa) se cubre aquí con CA-4.6.

### RF-6. Redondeo del impuesto

Origen: RN-5 **[P]**.

- **CA-6.1** El sistema deberá calcular el impuesto como `subtotal_cents` × `tax_rate_bp` / 10 000 y redondearlo una sola vez al céntimo entero.
- **CA-6.2** Cuando la parte fraccionaria del cálculo exacto es 0,5 o más, el sistema deberá redondear al céntimo superior; cuando es menor que 0,5, al inferior («mitad hacia arriba»).
- **CA-6.3** El sistema deberá producir para cada fila de la tabla 6.3 exactamente el `tax_cents` y el `total_cents` que indica, en todas las ejecuciones.

### RF-7. Formato de los importes

Origen: RN-6 **[P]**, §8.1 **[P]**, constitución principio 4. La representación JSON de los números está en 002 RF-4.

- **CA-7.1** El sistema deberá devolver todos los importes como enteros en céntimos de euro, en campos terminados en `_cents`, y las tasas como enteros en puntos básicos, en campos terminados en `_bp`.
- **CA-7.2** El sistema deberá devolver `currency` = `EUR` en todo resultado. La conversión a otras divisas no forma parte de esta funcionalidad (RN-7).
- **CA-7.3** El sistema deberá devolver en `users` el número de usuarios recibido.

### RF-8 a RF-12

**Movidos a 002**: RF-8 (cotización sin guardar) → 002 RF-1; RF-9 (campos no definidos) → 002 RF-5; RF-10 (formato único de error) → 002 RF-6; RF-11 (cuerpo de la petición) → 002 RF-7; RF-12 (métodos no permitidos) → 002 RF-8.

### RF-13. Configuración de tasas

Origen: RN-4 **[P]**, ADR 0006 **[P]**, revisión QA **[P]**.

- **CA-13.1** El sistema deberá rechazar guardar una tasa configurada que no sea un entero entre 0 y 10 000 bp, ambos incluidos, y conservar la tasa anterior.
- **CA-13.2** Cuando se cambia la tasa configurada de un país, el sistema deberá usar la nueva tasa en los cálculos posteriores sin cambiar el cálculo.
- **CA-13.3** El sistema deberá usar en cada cálculo una única tasa, la configurada en el momento de hacerlo, para todo ese cálculo.

## 5. Contrato observable: interfaz del cálculo

Es lo que ven las specs consumidoras. No define transporte ni formato de intercambio: eso lo fija cada consumidora (002 para la cotización).

**Entradas**

| Dato | Tipo | Regla |
| --- | --- | --- |
| `users` | entero | 0 ≤ `users` ≤ 100 000 (RF-3) |
| `country` | texto | Código de país ya normalizado; debe tener tasa configurada (RF-4) |

**Salida** (ejemplo con `users` = 15 y `country` = ES)

| Campo | Valor |
| --- | --- |
| `users` | 15 |
| `currency` | EUR |
| `tiers[1]` | `tier` 1, `from_users` 1, `to_users` 10, `units` 10, `unit_price_cents` 1000, `amount_cents` 10000 |
| `tiers[2]` | `tier` 2, `from_users` 11, `to_users` 50, `units` 5, `unit_price_cents` 800, `amount_cents` 4000 |
| `tiers[3]` | `tier` 3, `from_users` 51, `to_users` sin límite, `units` 0, `unit_price_cents` 500, `amount_cents` 0 |
| `subtotal_cents` | 14000 |
| `tax_rate_bp` | 2100 |
| `tax_cents` | 2940 |
| `total_cents` | 16940 |

**Errores de dominio**: el cálculo no produce ningún resultado parcial.

| Error | Cuándo |
| --- | --- |
| usuarios no válidos | `users` no es entero o está fuera de 0–100 000 (CA-3.3, CA-3.4); tiene prioridad sobre el siguiente (CA-3.5) |
| país no soportado | `country` sin tasa configurada (CA-4.6, CA-4.7) |

**Configuración de tasas**: datos de país → tasa en bp, con tasas enteras de 0 a 10 000 (RF-13) y los valores por defecto de CA-4.3.

## 6. Casos de prueba

Niveles: **U** = cálculo puro, con la tasa dada directamente y sin base de datos; **D** = cálculo completo con la tabla de tasas real en una base de datos de prueba, sin servidor web. Las versiones HTTP de estos casos están en la spec 002.

### 6.1 Precio por tramos (RN-1, RN-2) · U + D · país US (tasa 0)

| # | `users` | Tramo 1 (units / cents) | Tramo 2 (units / cents) | Tramo 3 (units / cents) | `subtotal_cents` | `tax_cents` | `total_cents` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P-1 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0 | 0 |
| P-2 | 1 | 1 / 1000 | 0 / 0 | 0 / 0 | 1000 | 0 | 1000 |
| P-3 | 10 | 10 / 10000 | 0 / 0 | 0 / 0 | 10000 | 0 | 10000 |
| P-4 | 11 | 10 / 10000 | 1 / 800 | 0 / 0 | 10800 | 0 | 10800 |
| P-5 | 15 | 10 / 10000 | 5 / 4000 | 0 / 0 | 14000 | 0 | 14000 |
| P-6 | 50 | 10 / 10000 | 40 / 32000 | 0 / 0 | 42000 | 0 | 42000 |
| P-7 | 51 | 10 / 10000 | 40 / 32000 | 1 / 500 | 42500 | 0 | 42500 |
| P-8 | 60 | 10 / 10000 | 40 / 32000 | 10 / 5000 | 47000 | 0 | 47000 |
| P-9 | 100 | 10 / 10000 | 40 / 32000 | 50 / 25000 | 67000 | 0 | 67000 |
| P-10 | 100000 | 10 / 10000 | 40 / 32000 | 99950 / 49975000 | 50017000 | 0 | 50017000 |

P-11 (`-0`) se movió a 002 (caso Q-20): es una cuestión de formato JSON.

### 6.2 Impuestos con la configuración por defecto (RN-3, RN-4) · U (con la tasa de la columna) + D

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

T-11 a T-19 (normalización del país) se movieron a 002 (casos Q-11 a Q-19).

### 6.3 Regla de redondeo (RN-5) · U + D con configuración de prueba

En el nivel D se configura para ES la tasa de la columna `tax_rate_bp` antes de calcular. En el nivel U se aplica la regla al subtotal indicado.

| # | `users` | `subtotal_cents` | `tax_rate_bp` | Valor exacto | `tax_cents` | `total_cents` |
| --- | --- | --- | --- | --- | --- | --- |
| R-1 | 1 | 1000 | 2105 | 210,5 | 211 | 1211 |
| R-2 | 1 | 1000 | 2104 | 210,4 | 210 | 1210 |
| R-3 | 1 | 1000 | 2106 | 210,6 | 211 | 1211 |
| R-4 | 1 | 1000 | 5 | 0,5 | 1 | 1001 |
| R-5 | 1 | 1000 | 4 | 0,4 | 0 | 1000 |
| R-6 | 1 | 1000 | 1 | 0,1 | 0 | 1000 |
| R-7 | 100000 | 50017000 | 2105 | 10528578,5 | 10528579 | 60545579 |
| R-8 | 15 | 14000 | 10000 | 14000 | 14000 | 28000 |
| R-9 | 11 | 10800 | 0 | 0 | 0 | 10800 |

### 6.4 Configuración de tasas (RF-4, RF-13) · D con configuración de prueba

| # | Acción | Resultado esperado |
| --- | --- | --- |
| C-1 | Guardar la tasa 10001 bp para ES | Rechazada; ES sigue con su tasa anterior |
| C-2 | Guardar la tasa -1 bp para ES | Rechazada; ES sigue con su tasa anterior |
| C-3 | Guardar la tasa 10000 bp y luego 0 bp para ES | Ambas aceptadas |
| C-4 | Quitar la tasa de PT y calcular 1 usuario en PT | Error de dominio «país no soportado» |
| C-5 | Calcular ES con 15 usuarios, cambiar ES a 2200 bp y volver a calcular | Primero: `tax_cents` 2940; después: `tax_rate_bp` 2200 y `tax_cents` 3080 |
| C-6 | Preparar una base de datos vacía sin datos de demostración y leer las tasas | Exactamente las 7 tasas de CA-4.3 |

### 6.5 Errores de dominio (RF-3, RF-4)

| # | `users` | `country` | Nivel | Resultado esperado |
| --- | --- | --- | --- | --- |
| X-1 | -1 | ES | U + D | usuarios no válidos |
| X-2 | 100001 | ES | U + D | usuarios no válidos |
| X-3 | verdadero (valor lógico) | ES | U | usuarios no válidos |
| X-4 | 15 | XX | D | país no soportado |
| X-5 | 15 | es | D | país no soportado (no se normaliza, CA-4.7) |
| X-6 | 15 | (vacío) | D | país no soportado |
| X-7 | -1 | XX | D | usuarios no válidos (prioridad, CA-3.5) |

## 7. Requisitos no funcionales

- **RNF-1 Exactitud:** todos los casos de las tablas 6.1 a 6.3 dan el resultado exacto al céntimo en todas las ejecuciones (§6 «precisión del dinero» [P]).
- **RNF-2 Testabilidad:** el cálculo de tramos, impuesto y redondeo se puede probar sin base de datos ni servidor web; los casos marcados U lo demuestran (constitución, principio 3).
- **RNF-3 Configurabilidad:** las tasas por país se configuran como datos; cambiar, añadir o quitar una tasa no exige tocar el cálculo (RN-4, ADR 0006 [P]; casos C-1 a C-6).
- **RNF-4 Una sola fuente de verdad:** cualquier importe que muestre o guarde el sistema sale de este cálculo; ninguna otra parte lo repite (ADR 0004 [P]).
- **RNF-5 a RNF-8** (rendimiento, seguridad de los errores, idioma de los mensajes y documentación de la API): **movidos a 002**, porque se refieren al endpoint.

## 8. Casos límite

- **0 usuarios:** válido, todo a 0 y 3 tramos con 0 unidades (P-1, T-1).
- **Fronteras entre tramos:** 10/11 y 50/51 (P-3, P-4, P-6, P-7).
- **Máximo:** 100 000 se acepta (P-10, T-10, R-7); 100 001 se rechaza (X-2).
- **Valor lógico como usuarios:** se rechaza (X-3).
- **País sin impuesto:** tasa 0 con total igual al subtotal (T-5, R-9).
- **País sin normalizar o vacío:** no se normaliza aquí; se rechaza como no soportado (X-5, X-6).
- **Dos errores a la vez:** gana «usuarios no válidos» (X-7).
- **Redondeo:** 0,5 exacto sube, también con el subtotal máximo (R-1, R-4, R-7); tasas extremas 0 y 10 000 bp (R-8, R-9).
- **Configuración:** tasas fuera de rango rechazadas, país sin tasa no soportado, cambio de tasa entre cálculos y valores por defecto sin datos de demostración (C-1 a C-6).

## 9. Fuera de alcance

- El endpoint `POST /pricing/quote`, la validación del JSON de entrada, la normalización del país, los mensajes de error y los códigos HTTP: spec 002.
- Guardar simulaciones, el historial y los campos de almacenamiento y llamadas a la API (RN-8, RN-9, `POST /simulations`): spec posterior.
- Calcular a partir de un cliente registrado: el país llega como dato.
- Conversión a otras divisas (RN-7, solo en frontend) y la pantalla del simulador.
- Impuestos especiales: IGIC de Canarias, Ceuta y Melilla, inversión del sujeto pasivo en la UE e impuesto sobre ventas de cada estado de EE. UU. (§7.2).
- Efecto del plan elegido en el precio (§10 supuesto 3).
- Descuentos, promociones, periodos distintos del mensual y prorrateos.
- Pantalla o endpoint para editar las tasas: solo se cambian como datos (C-1 a C-5).

## 10. Criterios de finalización

**Funcionalidad**

- [ ] Cada fila de las tablas 6.1 a 6.5 tiene un test automático en los niveles que indica (U, D o ambos) y todos pasan.
- [ ] Cada criterio CA-x vigente de la sección 4 está cubierto por al menos un test que lo cita por su identificador.
- [ ] El cálculo con `users` = 15 y `country` = ES devuelve exactamente la salida de la sección 5.
- [ ] Una base de datos recién preparada, sin datos de demostración, contiene las 7 tasas de CA-4.3 (C-6).

**Cumplimiento de la constitución** (comprobación en revisión)

- [ ] Principio 1: no se añade ninguna dependencia sin ADR en `ai-workspace/architecture/adr/` (mypy: ADR 0008).
- [ ] Principio 2: cada commit de código cita el RF-x o CA-x que implementa.
- [ ] Principio 3: el cálculo de precio e impuesto no importa nada del framework web ni del acceso a datos; los tests U lo ejecutan sin servidor ni base de datos.
- [ ] Principio 4: ningún importe ni tasa pasa por números en coma flotante; el esquema de la tabla de tasas se crea con una migración.
- [ ] Principio 5: la suite completa pasa antes de cada commit; cada regla de negocio tiene test U. Los tests de integración del endpoint son de 002.
- [ ] Principio 5: el código generado por IA está revisado y las correcciones están anotadas en `ai-workspace/ai-review-log.md`.
- [ ] Principio 6: `ruff check`, `ruff format --check` y `mypy` pasan sin errores en el backend. ESLint y TypeScript strict no aplican: esta funcionalidad no toca el frontend.

## 11. Decisiones cerradas

- **D-1. Nombre del campo de usuarios:** el cálculo y la cotización usan `users`. Si se unifica con `active_users` se decidirá en la spec de simulaciones.
- **D-2. País en la respuesta de la cotización:** movida a 002.
- **D-3. Valores de las tasas:** los de RN-4 son la configuración por defecto de la entrega (CA-4.3) y se documentan como supuesto en el README (§10 supuesto 4). Como son datos configurables (RF-13), cambiarlos no exige modificar esta spec salvo la tabla 6.2.
- **D-4. División de la spec (v1.2):** esta spec queda en el núcleo del cálculo y la tabla de tasas; el endpoint pasa a la 002. Así cada spec tiene un plan, y el núcleo se construye antes que la API (§11).
- **D-5. Tasas por defecto:** forman parte de la preparación de la base de datos, no de los datos de demostración (CA-4.3, §8.5 del documento 00).

## 12. Historial de cambios

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0 | 2026-11-14 | Versión inicial aprobada |
| 1.1 | 2026-11-14 | Revisión QA: 38 hallazgos resueltos. Mensajes de error fijados; definición de entero JSON; normalización del país acotada; RF-11 (cuerpo), RF-12 (métodos) y RF-13 (configuración de tasas); niveles U/I en los casos; tablas 6.4 y 6.6 nuevas; dudas D-1 a D-3 cerradas; checklist alineado con la constitución. Aprobada |
| 1.2 | 2026-11-14 | División: el endpoint, la validación JSON, la normalización del país, los mensajes y RNF-5 a RNF-8 pasan a la spec 002. Se añaden los errores de dominio (CA-3.3 a CA-3.5, CA-4.6, CA-4.7), los casos C-6 y X-1 a X-7, y las decisiones D-4 y D-5. Los niveles de test pasan a U y D. Ningún comportamiento observable de la v1.1 se pierde: lo que sale de aquí está en 002. Aprobada |
