# 007 — Borrar cliente

Estado: v1.0 · Pendiente de la revisión del autor · Fuente de verdad: `ai-workspace/specs/00-spec-first.md` · Constitución: `ai-workspace/docs/constitution.md` · Depende de: specs 003, 004, 005 y 006

Leyenda de origen: **[E]** viene del enunciado; **[P]** es una propuesta, una petición del autor o una decisión D-x de la sección 9.

## 1. Contexto y objetivo

El documento 00 dejó «borrar clientes» fuera de alcance como propuesta (§3) **[P]**, y las specs 003, 004 y 005 lo repitieron. Con esta spec, el 00 ya lo recoge en §3 y en la tabla de endpoints (§8.2). El autor pide ahora poder borrar un cliente **[P]**, y decidió que al borrarlo se borre también su historial de simulaciones (P-1).

**De dónde sale esta spec:** la aplicación ya estaba terminada (specs 001 a 006). Al usarla, el autor vio que no había forma de borrar un cliente y lo pidió en una petición nueva (prompt P-19 de `ai-workspace/prompts.md`). La funcionalidad no se añadió directamente al código. Pasó por el mismo proceso que el resto (spec, plan, tareas y tests primero), porque amplía el alcance que fijó el documento 00 (constitución, principios 1 y 2). Antes de escribir la spec, la IA preguntó qué hacer con el historial del cliente, que era la única decisión de negocio abierta (P-1).

**Objetivo:** borrar un cliente desde su ficha, después de una confirmación que dice cuánto historial se pierde, y que el backend borre el cliente y todas sus simulaciones en una sola transacción.

**Por qué así:** el comercial elimina clientes de prueba o que ya no lo son, sin dejar simulaciones huérfanas. Pedir confirmación y decir cuántas simulaciones se pierden evita un borrado por error, porque no se puede deshacer.

**Relación con la spec 004:** su CA-7.3 sigue en vigor: la base de datos rechaza borrar un cliente que tiene simulaciones. Esta spec no la cambia ni toca ninguna migración. El servicio de borrado quita primero las simulaciones y después el cliente, de forma explícita y en la misma transacción, así que la regla sigue protegiendo frente a cualquier otro borrado.

## 2. Requisitos funcionales

### RF-1. Borrar en el backend

Origen: petición del autor **[P]**, P-1; D-1 a D-4.

- **CA-1.1** Cuando llega `DELETE /customers/{id}` de un cliente que existe, el sistema deberá borrar sus simulaciones con sus tramos y después el cliente, y responder 204 sin cuerpo.
- **CA-1.2** El sistema deberá hacer todo el borrado en una sola transacción: si algo falla, no deberá borrar nada.
- **CA-1.3** Si el cliente no existe o `{id}` no es un identificador (las mismas reglas que 003 CA-6.3), entonces el sistema deberá responder 404 con el formato único de error y no borrar nada.
- **CA-1.4** El sistema no deberá tocar los clientes ni las simulaciones de otros clientes.
- **CA-1.5** Después de borrar, el identificador fiscal deberá quedar libre para un alta nueva, y el `id` del cliente no deberá volver a usarse (003 CA-1.3).
- **CA-1.6** El sistema deberá anunciar `DELETE` en la cabecera `Allow` de `/customers/{id}` («DELETE, GET») y aceptarlo en CORS desde el origen del frontend.
- **CA-1.7** El sistema deberá documentar la ruta en `/docs` con sus respuestas 204 y 404.
- **CA-1.8** La regla de 004 CA-7.3 deberá seguir cumpliéndose: la base de datos rechaza borrar directamente un cliente con simulaciones.

### RF-2. Borrar desde la ficha

Origen: petición del autor **[P]**; 005 RF-9 y RF-2; D-5 a D-9.

- **CA-2.1** El sistema deberá mostrar en la tarjeta del cliente el botón T7-BTN «Borrar cliente».
- **CA-2.2** Cuando el usuario pulsa «Borrar cliente», el sistema deberá mostrar, sin pedir nada al backend, una confirmación con la pregunta T7-ASK «¿Borrar «{empresa}»?», el aviso del historial de CA-2.3, la frase T7-IRR «Esta acción no se puede deshacer.» y los botones T7-YES «Sí, borrar» y «Cancelar». La confirmación deberá recibir el foco y tener la pregunta como nombre accesible.
- **CA-2.3** El aviso del historial deberá ser T7-HN «Se borrarán también sus {n} simulaciones.» con el `total` del historial cuando sea mayor que 1, T7-H1 «Se borrará también su simulación.» cuando sea 1, ninguno cuando sea 0, y T7-HX «Se borrará también todo su historial de simulaciones.» si el historial aún no ha cargado o falló.
- **CA-2.4** Cuando el usuario pulsa «Cancelar» o la tecla Escape, el sistema deberá cerrar la confirmación sin pedir nada y devolver el foco a «Borrar cliente».
- **CA-2.5** Cuando el usuario pulsa «Sí, borrar», el sistema deberá pedir `DELETE /customers/{id}` sin cuerpo y, mientras espera, mostrar el botón desactivado con T7-BDO «Borrando…»; pulsarlo otra vez no deberá hacer ninguna petición.
- **CA-2.6** Cuando el backend responde 204, el sistema deberá abrir `/clientes` y mostrar allí el aviso T7-OK «Cliente «{empresa}» borrado», que desaparece al salir del listado.
- **CA-2.7** Si el backend responde 404, entonces el sistema deberá mostrar T-NFC «Cliente no encontrado» (005 CA-9.4).
- **CA-2.8** Si el borrado falla por cualquier otro motivo, entonces el sistema deberá mostrar dentro de la confirmación T7-KO «No se pudo borrar el cliente» con «Reintentar», que repite la misma petición, y no cambiar nada más.
- **CA-2.9** El sistema deberá seguir el diseño de la spec 006: botón de peligro, confirmación con un fundido y avisos con `anim-fade`.

## 3. Contrato observable

**`DELETE /customers/{id}`**

| Respuesta | Cuándo |
| --- | --- |
| 204, sin cuerpo | Cliente borrado, con todas sus simulaciones |
| 404 `not_found` «Recurso no encontrado» | Cliente inexistente o `{id}` que no es un identificador |
| 405 con `Allow: DELETE, GET` | `POST`, `PUT` o `PATCH` sobre `/customers/{id}` |

**Textos nuevos**

| ID | Texto |
| --- | --- |
| T7-BTN | Borrar cliente |
| T7-ASK | ¿Borrar «{empresa}»? |
| T7-HN | Se borrarán también sus {n} simulaciones. |
| T7-H1 | Se borrará también su simulación. |
| T7-HX | Se borrará también todo su historial de simulaciones. |
| T7-IRR | Esta acción no se puede deshacer. |
| T7-YES | Sí, borrar |
| T7-BDO | Borrando… |
| T7-OK | Cliente «{empresa}» borrado |
| T7-KO | No se pudo borrar el cliente |

`{n}` sigue el formato de números de 005 CA-5.6.

## 4. Casos de prueba

Niveles: **D** = servicio y repositorio con una base de datos de prueba; **I** = petición HTTP; **C** = pantalla en el DOM simulado, como en 005; **M** = navegador real.

### 4.1 Backend · D e I

| # | Nivel | Situación | Resultado esperado |
| --- | --- | --- | --- |
| BR-1 | I | Borrar un cliente sin simulaciones | 204 sin cuerpo; su ficha da 404 y el listado tiene uno menos |
| BR-2 | I | Borrar un cliente con 2 simulaciones | 204; no quedan sus simulaciones ni sus tramos; las de otro cliente siguen |
| BR-3 | I | Borrar el cliente 999 | 404 `not_found`; no se borra nada |
| BR-4 | I | `{id}` igual a `abc`, `0`, `01` y `-1` | 404 en los cuatro |
| BR-5 | I | Borrar dos veces el mismo cliente | 204 y después 404 |
| BR-6 | I | `POST`, `PUT` y `PATCH` sobre `/customers/1` | 405 con `Allow: DELETE, GET` |
| BR-7 | I | Preflight de `DELETE` desde `http://localhost:4200` | 200 con `DELETE` entre los métodos permitidos |
| BR-8 | D | El borrado del cliente falla después de quitar sus simulaciones | Ni el cliente ni sus simulaciones se borran |
| BR-9 | I | Dar de alta otra vez el identificador fiscal borrado | 201 con un `id` nuevo, mayor que el borrado |
| BR-10 | I | `/openapi.json` | `DELETE /customers/{customer_id}` con 204 y 404, este con el formato único |
| BR-11 | D | Borrar con SQL un cliente con simulaciones, sin pasar por el servicio | Rechazado (004 CA-7.3, DB-9 sin cambios) |

### 4.2 Frontend · C

| # | Situación | Resultado esperado |
| --- | --- | --- |
| BF-1 | Ficha de Acme cargada | Botón «Borrar cliente» |
| BF-2 | Pulsar «Borrar cliente» con 3 simulaciones en el historial | Confirmación con «¿Borrar «Acme Telecom S.L.»?», «Se borrarán también sus 3 simulaciones.» y «Esta acción no se puede deshacer.», con el foco dentro; ninguna petición nueva |
| BF-3 | El historial tiene 1, 0, o aún carga | «Se borrará también su simulación.»; ninguna frase de historial; «Se borrará también todo su historial de simulaciones.» |
| BF-4 | «Cancelar» y, en otra prueba, Escape | Se cierra; ninguna petición; el foco vuelve a «Borrar cliente» |
| BF-5 | «Sí, borrar» dos veces seguidas | Una sola `DELETE http://127.0.0.1:8000/customers/1` sin cuerpo; botón «Borrando…» desactivado |
| BF-6 | El borrado responde 204 | `/clientes` con «Cliente «Acme Telecom S.L.» borrado»; al salir y volver, el aviso ya no está |
| BF-7 | El borrado responde 404 | «Cliente no encontrado» |
| BF-8 | Sin respuesta; en otra prueba, 500 | «No se pudo borrar el cliente» con «Reintentar», que repite la `DELETE` |
| BF-9 | Confirmación abierta | Tiene `role="alertdialog"` y su nombre accesible es la pregunta |

### 4.3 Comprobaciones manuales · M

| # | Comprobación | Resultado esperado |
| --- | --- | --- |
| MA-1 | Con el seed, borrar un cliente con historial desde la ficha | Desaparece del listado con el aviso; su ficha da «Cliente no encontrado» |
| MA-2 | Solo con teclado: abrir la confirmación, cancelar con Escape y borrar | Funciona; el foco siempre se ve |

## 5. Requisitos no funcionales

- **RNF-1 Capas:** el router solo valida y responde; el servicio decide el orden del borrado; cada repositorio toca solo sus tablas (constitución, principio 3).
- **RNF-2 Sin dependencias nuevas** y sin migraciones nuevas.
- **RNF-3 Calidad:** ruff, mypy, ESLint y TypeScript estricto sin errores; archivos de menos de 300 líneas y funciones de menos de 40.

## 6. Casos límite

- Borrar dos veces, o desde dos pestañas: la segunda da 404 (BR-5, BF-7).
- El historial aún no ha cargado: el aviso no da una cifra que no conoce (BF-3).
- Un fallo a mitad del borrado no deja simulaciones sin cliente ni un cliente sin parte de su historial (BR-8).

## 7. Fuera de alcance

- Deshacer un borrado, papelera o borrado lógico.
- Borrar desde el listado, borrar varios a la vez y editar clientes.
- Borrar una simulación suelta.

## 8. Criterios de finalización

- [x] Cada caso D, I y C de la sección 4 tiene un test que lo cita y pasa.
- [x] Las suites del backend y del frontend pasan, y los tests anteriores que cambian por el nuevo contrato están anotados: la cabecera `Allow` de 003 ER-3 y de 004 ER-10.
- [x] MA-1 y MA-2 comprobados en un navegador real.
- [x] ruff, mypy, lint y compilación del frontend sin errores.

## 9. Decisiones

- **P-1. Respuesta del autor:** al borrar un cliente se borra también su historial. Descartada: permitir borrar solo clientes sin simulaciones.
- **D-1. 204 sin cuerpo:** el frontend ya conoce el historial y no necesita nada más.
- **D-2. Borrado explícito en el servicio, no `ON DELETE CASCADE`:** no hace falta ninguna migración, y la regla de 004 CA-7.3 sigue protegiendo frente a otros borrados.
- **D-3. Una sola transacción** compartida por los dos repositorios, que usan la misma sesión de la petición.
- **D-4. Mismas reglas de `{id}` que la ficha** (003 CA-6.3): lo que no es un identificador da 404.
- **D-5. Borrar solo desde la ficha:** es donde se ve el cliente completo y su historial antes de borrarlo.
- **D-6. Confirmación dentro de la tarjeta**, no un diálogo modal del navegador: se maneja con el teclado y se prueba en el DOM simulado de los tests.
- **D-7. La cifra del aviso sale del historial cargado**, sin otra petición; si no se conoce, el aviso no la da.
- **D-8. Tras borrar, vuelta al listado con un aviso**, que viaja en el estado de la navegación como T-REG (005 DT-12).
- **D-9. Botón de peligro en rojo** con el tema de 006 (contraste de 6,5:1).

## 10. Historial de cambios

| Versión | Cambio |
| --- | --- |
| 1.0 | Versión inicial, tras la respuesta del autor (P-1) |
| 1.0 | Sin cambios de requisitos: §1 explica de dónde sale la petición, y §8 cita también 004 ER-10, el segundo test anterior afectado por CA-1.6 (encontrado en T-02) |
