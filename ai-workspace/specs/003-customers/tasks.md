# Tareas — 003 Clientes

Estado: v1.0, redactadas y ejecutadas por delegación del autor, revisadas y aprobadas por el autor · Spec: `spec.md` v1.0 · Plan: `plan.md` v1.0

## Reglas de ejecución

- **Orden y tamaño:** una tarea cada vez, en orden. No se empieza la siguiente hasta cumplir su «Hecho cuando».
- **Ciclo rojo → verde → revisar:**
  1. Se escriben los tests a partir de las tablas de la spec.
  2. Se confirma que fallan por el motivo esperado.
  3. Se implementa lo mínimo para que pasen.
  4. Se pasa la verificación completa.
- **Verificación completa** (desde `backend/`): `pytest`, `ruff check .`, `ruff format --check .` y `mypy .`, todo sin errores.
- **Tests anteriores:** los 383 tests de 001 y 002 no se modifican y deben pasar en cada tarea.
- **Commits:** uno por tarea, con el prefijo de `AGENTS.md` y los RF/CA que cubre. El autor autorizó hacerlos sin preguntar en esta spec.
- **Revisión por bloques:** al cerrar cada fase se revisa contra la spec y el plan, y se anota el estado en la tabla de progreso. Al final, T-20 revisa todas las tareas juntas.
- **Dudas y correcciones:** lo que no resuelvan la spec ni el plan se decide con el criterio más conservador y se anota como decisión para el autor. Las correcciones al código generado se anotan en `ai-workspace/ai-review-log.md`.
- **Casos de la spec:** TI y TG (identificador), AL (altas), VA (validación), CO (conflictos), LI y LP (listado), FI (ficha), ER (protocolo y errores), DB (persistencia) y SE (seed). U = sin servidor ni base de datos; D = con base de datos; I = petición HTTP.

## Progreso

| Fase | Tareas | Estado |
| --- | --- | --- |
| 1 — Errores globales | T-01 a T-03 | ✅ Completada: 394 tests (11 nuevos); ruff y mypy en verde; los 383 tests de 001 y 002 pasan sin tocarlos. Un fallo propio corregido en T-03 (entrada 17 del log) |
| 2 — Dominio del identificador fiscal | T-04 a T-06 | ✅ Completada: 462 tests (68 nuevos); tablas 6.1 y 6.2 completas sin base de datos ni servidor; el test de arquitectura del dominio cubre `tax_id.py`; ruff y mypy en verde |
| 3 — Persistencia | T-07 a T-10 | ✅ Completada: 531 tests (69 nuevos); migración 0002 sin tocar la 0001; los modelos coinciden con el esquema migrado; ruff y mypy en verde |
| 4 — API | T-11 a T-17 | ✅ Completada: 720 tests (189 nuevos); las tablas 6.3 a 6.9 pasan por HTTP; ningún archivo supera las 300 líneas ni ninguna función las 40; ruff y mypy en verde. Una decisión del plan corregida en T-11 (entrada 18 del log) |
| 5 — Datos de demostración | T-18 | ✅ Completada: 736 tests (16 nuevos); el seed es idempotente y usa el mismo esquema y servicio que la API; ruff y mypy en verde |
| 6 — Cierre | T-19, T-20 | ✅ Completada: arranque real con alta, búsqueda, ficha y seed; clon limpio con entorno virtual nuevo en verde (744 tests, ruff, mypy y `alembic check`); los 18 commits de código de las tareas en verde uno a uno y todos citan su RF o CA; 56 CA y 151 casos con un test que los cita y pasa, cada caso en su nivel; revisión conjunta con dos mejoras en los tests (entrada 20 del log); los 13 puntos de la sección 10 marcados. El autor revisó y aprobó la spec |

## Fase 1 — Errores globales (nivel I con rutas de prueba)

- [x] **T-01. `core` deja de conocer las funcionalidades** · ✅ completada · commit `1014ff4`
  - **RF:** soporte de RF-7 (plan DT-14; entrada 16 del log). **Depende de:** ninguna.
  - **Archivos:** `app/api/error_mapping.py` (nuevo, con el mapeo de los dos errores de dominio de la cotización), `app/core/errors.py` (sin imports de `schemas` ni `domain`), `app/main.py` y `tests/unit/test_core_architecture.py`.
  - **Rojo (U):** un test que lee los imports de cada módulo de `app/core/` y falla si alguno importa `app.api`, `app.schemas`, `app.services`, `app.repositories`, `app.domain` o `app.db`. Hoy falla por `core/errors.py`.
  - **Hecho cuando:** ese test pasa y los 383 tests anteriores siguen en verde sin tocarlos: es un cambio de sitio, no de comportamiento.

- [x] **T-02. Errores del framework y 409 en el formato único** · ✅ completada · commit `e1a4be8`
  - **RF:** RF-7 (CA-7.1, CA-7.3, CA-7.4). Casos ER-6 y ER-7. **Depende de:** T-01.
  - **Archivos:** `app/core/errors.py` (`conflict`, `not_found`, manejador de `RequestValidationError` y de cualquier estado HTTP) y `tests/api/test_error_format_global.py`.
  - **Rojo (I):** ER-6 (ruta de prueba con parámetros enteros llamada con textos), ER-7 (ruta de prueba que lanza un 418 con un texto interno) y una ruta de prueba que lanza `conflict(...)`. Hoy las dos primeras responden `{"detail": ...}`.
  - **Hecho cuando:** ER-6 da 422 con un detalle «Valor no válido» por parámetro; ER-7 da 418 `http_error` «Error en la petición» sin el texto interno; el 409 sale con `conflict` «El recurso ya existe» y su detalle.

- [x] **T-03. Cabecera `Allow` completa** · ✅ completada · commit `b2356a0`
  - **RF:** RF-7 (CA-7.2). Caso ER-12. **Depende de:** T-02.
  - **Archivos:** `app/core/errors.py` (métodos de todas las rutas que coinciden) y `tests/api/test_error_format_global.py`.
  - **Rojo (I):** dos rutas de prueba en la misma dirección, una `GET` y otra `POST`; un `DELETE` debe responder `Allow: GET, POST`. Hoy responde solo `GET`.
  - **Hecho cuando:** ese test pasa y ER-12 confirma que `/pricing/quote` sigue con `Allow: POST`.

## Fase 2 — Dominio del identificador fiscal (nivel U)

- [x] **T-04. Normalización y formato básico** · ✅ completada · commit `b38b20d`
  - **RF:** RF-3 (CA-3.1, CA-3.2, CA-3.8, CA-3.9). Casos TG-1 a TG-12. **Depende de:** ninguna.
  - **Archivos:** `app/domain/errors.py` (`CustomerError` y sus cinco subclases), `app/domain/tax_id.py` (`normalize_tax_id` y `validate_tax_id` sin el control español) y `tests/unit/test_tax_id.py`.
  - **Rojo (U):** TG-1 a TG-11 y la normalización de TI-5 y TI-23.
  - **Hecho cuando:** pasan esos casos; con `country` distinto de `ES` o ausente solo se aplica el formato básico. TG-12 se completa en T-05.

- [x] **T-05. DNI y NIE** · ✅ completada · commit `1781b77`
  - **RF:** RF-3 (CA-3.3 a CA-3.5). Casos TI-1 a TI-9, TI-23 a TI-25 y TG-12. **Depende de:** T-04.
  - **Archivos:** `app/domain/tax_id.py` y `tests/unit/test_tax_id.py`.
  - **Rojo (U):** esos casos con `country` = `ES`. Hoy los inválidos se aceptan.
  - **Hecho cuando:** pasan todos, y un identificador español que no es DNI ni NIE se rechaza como «español no válido».

- [x] **T-06. CIF y NIF no soportados** · ✅ completada · commit `3f96e48`
  - **RF:** RF-3 (CA-3.3, CA-3.6, CA-3.7). Casos TI-10 a TI-22, TI-26 y TI-27. **Depende de:** T-05.
  - **Archivos:** `app/domain/tax_id.py` y `tests/unit/test_tax_id.py`.
  - **Rojo (U):** esos casos. Hoy los CIF válidos se rechazan y `K`, `L` y `M` no tienen su propio error.
  - **Hecho cuando:** pasan las tablas 6.1 y 6.2 completas y el test de arquitectura de 001 sigue en verde con el módulo nuevo.

## Fase 3 — Persistencia (nivel D)

- [x] **T-07. Tabla `customers`: modelo y migración** · ✅ completada · commit `ebd2954`
  - **RF:** RF-9 (CA-9.1 a CA-9.3). Casos DB-1, DB-3 a DB-6, DB-8 y DB-9. **Depende de:** T-04.
  - **Archivos:** `app/domain/customers.py` (`PLANS`, `NewCustomer`, `Customer`, `CustomerPage`), `app/db/models.py` (`CustomerRecord`), `app/db/migrations/versions/0002_create_customers.py` y `tests/integration/test_customers_migration.py`.
  - **Rojo (D):** esos casos. Hoy la tabla no existe.
  - **Hecho cuando:** pasan; la migración 0001 no cambia; el test de 001 que deshace todas las migraciones sigue en verde.

- [x] **T-08. Repositorio: guardar y leer** · ✅ completada · commit `83d7ea5`
  - **RF:** RF-1 (CA-1.3), RF-4 (CA-4.4). Casos DB-2 y DB-7. **Depende de:** T-07.
  - **Archivos:** `app/repositories/customers.py` (`add` y `get`) y `tests/integration/test_customer_repository.py`.
  - **Rojo (D):** guardar y leer un cliente; DB-2 (el duplicado lanza `DuplicateTaxIdError` y solo queda uno); DB-7 (no se reutiliza el `id`); `get` de un `id` inexistente devuelve `None`.
  - **Hecho cuando:** pasan, y tras un duplicado la sesión sigue utilizable.

- [x] **T-09. Repositorio: búsqueda** · ✅ completada · commit `4f9b9ec`
  - **RF:** RF-5 (CA-5.3 a CA-5.7). **Depende de:** T-08.
  - **Archivos:** `app/db/session.py` (función SQL `casefold`), `app/repositories/customers.py` (`search`) y `tests/integration/test_customer_repository.py`.
  - **Rojo (D):** sobre los seis clientes de la tabla 6.6: sin filtro, por fragmento de nombre con `ñ` y tildes, por fragmento de identificador, comodines literales, orden, `limit`, `offset` y `total`.
  - **Hecho cuando:** pasan, y los tests de sesión de 001 siguen en verde.

- [x] **T-10. Servicio de clientes y reloj** · ✅ completada · commit `dac845d`
  - **RF:** RF-1 (CA-1.2, CA-1.3, CA-1.5), RF-3 (CA-3.3), RF-4 (CA-4.1, CA-4.2), RF-5 (CA-5.2, CA-5.3) y RF-6 (CA-6.1, CA-6.2). **Depende de:** T-06 y T-09.
  - **Archivos:** `app/core/clock.py`, `app/services/customers.py`, `tests/unit/test_clock.py` y `tests/integration/test_customer_service.py`.
  - **Rojo (D):** alta con identificador sin normalizar (queda normalizado y con el `created_at` del reloj); país sin tasa; identificador español inválido; duplicado con otro formato; búsqueda con `q` vacío, con espacios y con un identificador con separadores; ficha existente e inexistente.
  - **Hecho cuando:** pasan, y un alta rechazada no deja ninguna fila.

## Fase 4 — API (niveles U e I)

- [x] **T-11. Esquemas de clientes** · ✅ completada · commit `8ee56cd`
  - **RF:** RF-2 (CA-2.1 a CA-2.7, CA-2.9), RF-3 (CA-3.3, CA-3.7, CA-3.9) y RF-5 (CA-5.8 a CA-5.10). **Depende de:** T-10.
  - **Archivos:** `app/schemas/customers.py`, `app/api/validation.py` (mensajes propios con `InvalidFieldError`) y `tests/unit/test_customer_schema.py`.
  - **Rojo (U):** con los datos ya decodificados de VA-1 a VA-27 (salvo los que necesitan la base de datos: VA-17, VA-26 y VA-27), `field_errors` devuelve exactamente los detalles de la tabla 6.4; y con los parámetros de LP-1 a LP-15, los de la tabla 6.7.
  - **Hecho cuando:** pasan, los tests de `field_errors` de 002 no cambian y `CustomerResponse` serializa el ejemplo de la sección 5.

- [x] **T-12. `POST /customers`: altas válidas** · ✅ completada · commit `e0d73ad`
  - **RF:** RF-1 (CA-1.1 a CA-1.4). Casos AL-1 a AL-9. **Depende de:** T-11.
  - **Archivos:** `app/api/customers.py` (ruta del alta y lectura mínima de la ficha y el listado solo si AL-4 lo necesita: se deja para T-14 y T-15), `app/api/dependencies.py` (`get_customer_store`, `get_now`), `app/main.py`, `tests/api/customer_requests.py` y `tests/api/test_customers_create.py`.
  - **Rojo (I):** AL-1 a AL-3 y AL-5 a AL-9. AL-4 se escribe en T-15, cuando existen las dos lecturas.
  - **Hecho cuando:** AL-1 devuelve exactamente la respuesta de la sección 5 y el resto pasa.

- [x] **T-13. `POST /customers`: validación y conflictos** · ✅ completada · commit `98c3d95`
  - **RF:** RF-2 (CA-2.1 a CA-2.9), RF-3 (CA-3.2, CA-3.3, CA-3.7 a CA-3.9), RF-4 (CA-4.1 a CA-4.3), RF-1 (CA-1.5). Casos VA-1 a VA-28 y CO-1 a CO-4. **Depende de:** T-12.
  - **Archivos:** `app/api/customers.py` (camino de error), `app/api/countries.py` (compartido con la cotización), `app/api/pricing.py` (usa el compartido), `app/api/error_mapping.py` (errores de clientes) y `tests/api/test_customers_create.py`.
  - **Rojo (I):** esos casos. Hoy dan 500 porque los errores no se traducen.
  - **Hecho cuando:** los detalles coinciden como conjunto con las tablas 6.4 y 6.5, y ningún caso rechazado deja una fila.

- [x] **T-14. `GET /customers`: listado y búsqueda** · ✅ completada · commit `411cab8`
  - **RF:** RF-5 (CA-5.1 a CA-5.11). Casos LI-1 a LI-20, LP-1 a LP-15 y CO-5. **Depende de:** T-13.
  - **Archivos:** `app/api/customers.py` y `tests/api/test_customers_list.py`.
  - **Rojo (I):** esos casos. Hoy la ruta responde 405.
  - **Hecho cuando:** cada fila de las tablas 6.6 y 6.7 devuelve los `id`, el orden y el `total` indicados.

- [x] **T-15. `GET /customers/{id}`: ficha** · ✅ completada · commit `28e32ee`
  - **RF:** RF-6 (CA-6.1 a CA-6.3), RF-1 (CA-1.4). Casos FI-1 a FI-9 y AL-4. **Depende de:** T-14.
  - **Archivos:** `app/api/customers.py` y `tests/api/test_customers_detail.py`.
  - **Rojo (I):** esos casos. Hoy la ruta no existe.
  - **Hecho cuando:** pasan, y FI-8 no produce un error interno.

- [x] **T-16. Protocolo, fallo interno y CORS** · ✅ completada · commit `5646baf`
  - **RF:** RF-7 (CA-7.2, CA-7.5) y RF-8 (CA-8.1 a CA-8.3). Casos ER-1 a ER-5 y ER-8 a ER-11. **Depende de:** T-15.
  - **Archivos:** `app/main.py` (`GET` en CORS) y `tests/api/test_customers_protocol.py`.
  - **Rojo (I):** ER-9 (la preflight de `GET` responde hoy 400). El resto debe pasar ya con lo construido; si alguno falla, se corrige aquí.
  - **Hecho cuando:** pasan todos, y los tests de CORS de 002 siguen en verde.

- [x] **T-17. Documentación interactiva** · ✅ completada · commit `e6fa3cd`
  - **RF:** RNF-4. **Depende de:** T-15.
  - **Archivos:** `app/api/customers.py` (cuerpo y ejemplos declarados) y `tests/api/test_customers_docs.py`.
  - **Rojo (I):** `/openapi.json` no describe hoy el cuerpo de `POST /customers`, porque se lee a mano.
  - **Hecho cuando:** las tres operaciones aparecen con su ejemplo de petición y de respuesta, y los parámetros del listado con su descripción.

## Fase 5 — Datos de demostración (nivel D)

- [x] **T-18. Seed de clientes** · ✅ completada · commit `f8f1d3a`
  - **RF:** RF-10 (CA-10.1 a CA-10.4), RNF-5. Casos SE-1 a SE-5. **Depende de:** T-10 y T-11.
  - **Archivos:** `app/db/seed.py` y `tests/integration/test_seed.py`.
  - **Rojo (D):** esos casos. Hoy el módulo no existe.
  - **Hecho cuando:** pasan, y `python -m app.db.seed` sobre una base de datos migrada imprime cuántos clientes ha creado.

## Fase 6 — Cierre

- [x] **T-19. Arranque real** · ✅ completada · commit `cd8264d`
  - **RF:** criterio de arranque de la sección 10 de la spec. **Depende de:** T-18.
  - **Archivos:** `AGENTS.md` (el comando de migraciones y seed queda confirmado) y `README.md` (decisiones y supuestos de clientes).
  - **Pasos:**
    1. `alembic upgrade head && python -m app.db.seed` sobre una base de datos vacía.
    2. `uvicorn app.main:app --reload`.
    3. Un alta, una búsqueda y una ficha por la línea de comandos, y abrir `/docs`.
  - **Hecho cuando:** todo responde como dice la spec y los dos archivos quedan actualizados.

- [x] **T-20. Comprobación final** · ✅ completada
  - **RF:** todos (sección 10 de la spec). **Depende de:** T-19.
  - **Archivos:** `spec.md` (checklist), `tasks.md` (estados) y `ai-workspace/ai-review-log.md`.
  - **Pasos:**
    1. Verificación completa en un clon limpio con un entorno virtual nuevo.
    2. Verificación de cada commit de código, uno a uno.
    3. Trazabilidad por test: cada CA citado en el docstring de un test que pasa.
    4. Los 151 casos de la spec presentes en su nivel.
    5. Revisión conjunta del código contra la spec y el plan.
    6. Checklist de la sección 10 y anotación de las correcciones en el log.
  - **Hecho cuando:** los 56 CA y los 151 casos tienen test en verde, todos los puntos de la sección 10 están marcados o llevan su excepción anotada, y cada tarea muestra su estado.

## Trazabilidad

| CA de la spec | Tareas |
| --- | --- |
| CA-1.1 | T-12 |
| CA-1.2, CA-1.3 | T-08, T-10, T-12 |
| CA-1.4 | T-15 |
| CA-1.5 | T-10, T-13 |
| CA-2.1 a CA-2.7, CA-2.9 | T-11, T-13 |
| CA-2.8 | T-13 |
| CA-3.1, CA-3.2, CA-3.8, CA-3.9 | T-04, T-11, T-13 |
| CA-3.3 a CA-3.7 | T-05, T-06, T-11, T-13 |
| CA-4.1 a CA-4.3 | T-10, T-13 |
| CA-4.4 | T-08 |
| CA-5.1, CA-5.11 | T-14 |
| CA-5.2 a CA-5.7 | T-09, T-10, T-14 |
| CA-5.8 a CA-5.10 | T-11, T-14 |
| CA-6.1 a CA-6.3 | T-10, T-15 |
| CA-7.1, CA-7.3, CA-7.4 | T-02 |
| CA-7.2 | T-03, T-16 |
| CA-7.5 | T-16 |
| CA-8.1 a CA-8.3 | T-16 |
| CA-9.1 a CA-9.3 | T-07 |
| CA-10.1 a CA-10.4 | T-18 |

Reparto de los casos: TG en T-04; TI en T-05 y T-06; DB en T-07 y T-08; AL en T-12 y T-15; VA y CO en T-13; LI, LP y CO-5 en T-14; FI en T-15; ER-6, ER-7 y ER-12 en T-02 y T-03; el resto de ER en T-16; SE en T-18.
