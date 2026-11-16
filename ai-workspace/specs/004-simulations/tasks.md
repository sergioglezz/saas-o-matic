# Tareas — 004 Simulaciones

Estado: v1.0 ejecutadas, revisadas y aprobadas por el autor · Spec: `spec.md` v1.0 (aprobada) · Plan: `plan.md` v1.0

## Reglas de ejecución

- **Orden y tamaño:** una tarea cada vez, en orden. No se empieza la siguiente hasta cumplir su «Hecho cuando».
- **Ciclo rojo → verde → revisar:**
  1. Se escriben los tests a partir de las tablas de la spec.
  2. Se confirma que fallan por el motivo esperado.
  3. Se implementa lo mínimo para que pasen.
  4. Se pasa la verificación completa.
- **Verificación completa** (desde `backend/`): `pytest`, `ruff check .`, `ruff format --check .` y `mypy .`, todo sin errores.
- **Tests anteriores:** los 744 tests de 001 a 003 no se modifican y deben pasar en cada tarea. `tests/api/conftest.py` solo se amplía con fixtures nuevas.
- **Tamaño:** ningún archivo supera las 300 líneas ni ninguna función las 40 (`AGENTS.md`).
- **Commits:** uno por tarea, con el prefijo de `AGENTS.md` y los RF/CA que cubre. El autor los autorizó al terminar la fase 5; cada uno se verificó por separado antes de hacer el siguiente.
- **Revisión por bloques:** al cerrar cada fase se revisa contra la spec y el plan, y se anota el estado en la tabla de progreso. Al final, T-14 revisa todas las tareas juntas.
- **Dudas y correcciones:** lo que no resuelvan la spec ni el plan se pregunta al autor. Las correcciones al código generado se anotan en `ai-workspace/ai-review-log.md`.
- **Casos de la spec:** SI (guardados), SN (instantánea), SV (validación), SC (cliente), HI y HP (historial), ER (protocolo y errores), DB (persistencia) y SE (seed). U = sin servidor ni base de datos; D = con base de datos; I = petición HTTP.

## Progreso

| Fase | Tareas | RF | Estado |
| --- | --- | --- | --- |
| 1 — Dominio | T-01 | RF-2, RF-4 | ✅ Completada: 773 tests (28 nuevos y 1 más del test de arquitectura del dominio, que ya recorre `simulations.py`); los 744 anteriores pasan sin tocarlos; ruff y mypy en verde. Revisión de la fase: un docstring de test citaba DT-2 en lugar de la sección 4 del plan, corregido. Commits verificados uno a uno |
| 2 — Persistencia y servicio | T-02 a T-04 | RF-1, RF-3, RF-4, RF-5, RF-7 | ✅ Completada: 849 tests (76 nuevos); los anteriores pasan sin tocarlos, también los que deshacen las migraciones hasta 0001 y `base`; ruff, mypy y `alembic check` en verde; la base de datos local no se tocó. Revisión de la fase: tres fallos propios corregidos (un test que deshacía las filas de su fixture, una expectativa errónea del `id` tras un guardado fallido y un `upgrade()` de 66 líneas, partido en funciones de menos de 40). Commits verificados uno a uno |
| 3 — API | T-05 a T-11 | RF-1 a RF-6, RNF-5 | ✅ Completada: 1041 tests (192 nuevos); los anteriores pasan sin tocarlos (`tests/api/conftest.py` solo gana la fixture `simulation_clock`); ruff, mypy y `alembic check` en verde; ningún archivo pasa de 300 líneas ni ninguna función de 40. T-08 y T-10 no necesitaron código nuevo: sus tests pasaron a la primera y se comprobaron con mutaciones (romper el mapeo de CNS, el orden validación → cliente, `parse_customer_id` y el orden cliente → parámetros), que sí los hacen fallar. Revisión de la fase: tres fallos propios corregidos (un reemplazo de texto demasiado amplio que renombró `without_framework_validation_error`, SI-13 que pasaba sin comprobar que el guardado se hizo, y un test de T-07 que dependía del historial de T-09), y dos añadidos anotados en el plan §2 (`openapi_examples.py` y `MAX_CUSTOMER_ID`). La tabla SV vive una sola vez en `tests/simulations_data.py`. Commits verificados uno a uno |
| 4 — Datos de demostración | T-12 | RF-8 | ✅ Completada: 1051 tests (10 nuevos); los 16 tests del seed de 003, incluido el de `main()`, pasan sin tocarlos; ruff y mypy en verde. Comprobado con el comando real sobre una base de datos temporal: `alembic upgrade head` y dos veces `python -m app.db.seed` dan 10 clientes, 6 simulaciones y 18 tramos, y la segunda ejecución no crea nada. La base de datos local sigue en 0002 (su arranque real es T-13). Revisión de la fase: sin fallos propios que anotar. Commits verificados uno a uno |
| 5 — Cierre | T-13, T-14 | Todos | ✅ Completada. Arranque real sobre una base de datos nueva: guardado (201), cliente inexistente (404), datos inválidos (422), historial paginado, 404 antes que 422, `Allow`, preflight de CORS y `/docs` con `"to_users": null`; servidor parado y base temporal borrada. README con la sección de simulaciones. Copia limpia (solo lo que entraría en un commit) con un entorno virtual nuevo: instalación, migraciones, seed dos veces, `alembic check`, 1051 tests, ruff y mypy en verde. Trazabilidad medida con el resultado de cada test: 43 de 43 CA y 86 de 86 casos en su nivel. los 12 criterios de la sección 10 marcados. Commits: el de documentación `9cd92ae` antes del código y uno por tarea (`5d02c4e` a `5280838`); cada uno, en una copia aparte con un entorno virtual nuevo, pasa la suite completa, ruff, mypy y los límites de tamaño. Correcciones anotadas en el log (entradas 21 a 31). El autor revisó y aprobó el cierre |

## Fase 1 — Dominio (nivel U)

- [x] **T-01. Tipos de la simulación y validación del uso** · ✅ completada · commit `5d02c4e`
  - **RF:** RF-2 (CA-2.3, CA-2.4, en el dominio) y RF-4 (tipos de la instantánea). Plan DT-2. **Depende de:** ninguna.
  - **Archivos:** `app/domain/simulations.py` (`MAX_STORAGE_GB`, `MAX_API_CALLS_PER_MONTH`, `NewSimulation`, `Simulation`, `SimulationPage` y `validate_usage`), `app/domain/errors.py` (`SimulationError`, `InvalidStorageError`, `InvalidApiCallsError` y `UnsupportedCustomerCountryError`) y `tests/unit/test_simulation_domain.py`.
  - **Rojo (U):** `validate_usage` acepta 0 y los máximos; rechaza -1, máximo + 1, `True`, `1.5` y `None` en cada campo, con el error de ese campo.
  - **Hecho cuando:** esos tests pasan y el test de arquitectura del dominio cubre `simulations.py` sin cambios.

## Fase 2 — Persistencia y servicio (nivel D)

- [x] **T-02. Migración 0003 y modelos** · ✅ completada · commit `6bbf745`
  - **RF:** RF-7 (CA-7.1 a CA-7.5) y RF-4 (CA-4.2, columnas de los tramos). Plan §3, DT-5 y DT-12. Casos DB-1, DB-3 a DB-9, DB-12 y DB-13. **Depende de:** T-01.
  - **Archivos:** `app/db/migrations/versions/0003_create_simulations.py`, `app/db/models.py` (`SimulationRecord`, `SimulationTierRecord` y su relación) y `tests/integration/test_simulations_migration.py`.
  - **Rojo (D):** los casos de la lista con inserciones directas en SQL; el índice de CA-7.5; deshacer hasta 0002; `compare_metadata` sin diferencias.
  - **Hecho cuando:** esos casos pasan, las migraciones 0001 y 0002 no cambian y los tests de migración de 001 y 003 (que deshacen hasta 0001 y hasta `base`) siguen en verde.

- [x] **T-03. Repositorio de simulaciones** · ✅ completada · commit `55d6654`
  - **RF:** RF-1 (CA-1.2, CA-1.5), RF-4 (CA-4.2, CA-4.5) y RF-5 (CA-5.2, CA-5.3 en datos). Plan DT-4, DT-6, DT-7 y DT-15. Casos DB-2, DB-10 y DB-11. **Depende de:** T-02.
  - **Archivos:** `app/repositories/simulations.py` (`add` y `list_for_customer`) y `tests/integration/test_simulation_repository.py`.
  - **Rojo (D):** guardar y leer con `to_users` nulo (DB-2); un `PriceQuote` con un tramo 4 en segundo lugar no deja ninguna fila (DB-10); el `id` no se reutiliza (DB-11); el orden por instante e `id` descendentes, el filtro por cliente, `limit`, `offset` y `total`.
  - **Hecho cuando:** esos tests pasan y `add` confirma o deshace la transacción entera.

- [x] **T-04. Servicio de simulaciones** · ✅ completada · commit `59765a7`
  - **RF:** RF-1 (CA-1.6), RF-3 (CA-3.1, CA-3.3, CA-3.4) y RF-4 (CA-4.1, CA-4.3, CA-4.4, CA-4.6). Plan §5 «Guardar», DT-1 a DT-3. **Depende de:** T-03.
  - **Archivos:** `app/services/simulations.py` (`SimulationStore`, `save_simulation` y `list_simulations`) y `tests/integration/test_simulation_service.py`.
  - **Rojo (D):** cliente inexistente → `CustomerNotFoundError`; país sin tasa → `UnsupportedCustomerCountryError` sin guardar nada; importes iguales a `quote` para el país del cliente; con otro almacenamiento y llamadas, mismos importes; tras cambiar la tasa, la simulación guardada no cambia y la nueva usa la tasa nueva; el cliente y las tasas no cambian al guardar.
  - **Hecho cuando:** esos tests pasan y el servicio no contiene ningún cálculo propio.

## Fase 3 — API (nivel I)

- [x] **T-05. Mover el identificador de ruta y la paginación, sin cambiar comportamiento** · ✅ completada · commit `5d70bf4`
  - **RF:** soporte de RF-5 (CA-5.3, CA-5.5). Plan DT-9 y DT-10. **Depende de:** ninguna de 004.
  - **Archivos:** `app/api/identifiers.py` (`parse_customer_id`), `app/schemas/pagination.py` (`PageQuery`), `app/api/customers.py`, `app/schemas/customers.py` y `tests/unit/test_page_query.py`.
  - **Rojo (U):** `PageQuery` con los casos LP de 003 que tocan `limit` y `offset`, y `parse_customer_id` con los `{id}` de FI-3 a FI-8. Hoy fallan porque los módulos no existen.
  - **Hecho cuando:** esos tests pasan y los 744 tests anteriores siguen en verde sin tocarlos: es un cambio de sitio, no de comportamiento.

- [x] **T-06. Esquemas y errores de dominio en la API** · ✅ completada · commit `1b0b489`
  - **RF:** RF-2 (CA-2.1 a CA-2.6, CA-2.8) y RF-4 (CA-4.7). Plan §5 `SimulationCreate`. **Depende de:** T-01.
  - **Archivos:** `app/schemas/simulations.py` (`SimulationCreate`, `SimulationResponse`, `SimulationListResponse`, mensajes y ejemplos), `app/api/error_mapping.py` (tres entradas nuevas) y `tests/unit/test_simulation_schema.py`.
  - **Rojo (U):** los valores de SV-2 a SV-16 sobre el esquema, con el detalle esperado; `-0` llega como 0; `SimulationResponse` no incluye `users` y escribe `"to_users": null`.
  - **Hecho cuando:** esos tests pasan y los mensajes son exactamente los de la sección 5 de la spec.

- [x] **T-07. Guardado válido e instantánea** · ✅ completada · commit `501bef8`
  - **RF:** RF-1 (CA-1.1 a CA-1.3, CA-1.6) y RF-4 (CA-4.1, CA-4.6, CA-4.7). Casos SI-1 a SI-13, SN-1 y SN-2. **Depende de:** T-04 y T-06.
  - **Archivos:** `app/api/simulations.py` (`POST /simulations`), `app/api/dependencies.py` (`get_simulation_store`), `app/main.py`, `tests/api/conftest.py` (reloj ajustable), `tests/api/simulation_requests.py` (clientes de partida y tabla 6.1) y `tests/api/test_simulations_create.py`.
  - **Rojo (I):** SI-1 devuelve exactamente la respuesta de la sección 5; la tabla 6.1 completa; SN-1 compara cada caso con `POST /pricing/quote`; SN-2.
  - **Hecho cuando:** esos casos pasan y el router no contiene reglas de negocio ni importes.

- [x] **T-08. Errores del guardado y cliente de la simulación** · ✅ completada · commit `87ad7c2`
  - **RF:** RF-2 (CA-2.1 a CA-2.8), RF-3 (CA-3.1, CA-3.2, CA-3.4) y RF-1 (CA-1.4). Casos SV-1 a SV-18 y SC-1 a SC-4. **Depende de:** T-07.
  - **Archivos:** `app/api/simulations.py` y `tests/api/test_simulations_validation.py`.
  - **Rojo (I):** las tablas 6.3 y 6.4; tras cada caso, el historial no tiene ninguna simulación.
  - **Hecho cuando:** esos casos pasan; SV-18 da 422 sin 404 y SC-3 da 422 con CNS.

- [x] **T-09. Historial** · ✅ completada · commit `27a68c5`
  - **RF:** RF-5 (CA-5.1 a CA-5.6) y RF-4 (CA-4.3 a CA-4.5). Plan §5 «Historial», DT-8. Casos HI-1 a HI-13, HP-1 a HP-4 y SN-3 a SN-5. **Depende de:** T-05 y T-08.
  - **Archivos:** `app/api/simulations.py` (`GET /customers/{id}/simulations`), `tests/api/test_simulations_history.py` y `tests/api/test_simulations_snapshot.py`.
  - **Rojo (I):** las tablas 6.5 y 6.6 con los datos de partida de 6.5; SN-3 a SN-5 cambiando y quitando tasas con el repositorio de 001.
  - **Hecho cuando:** esos casos pasan; HP-4 da 404 antes que 422 y HI-13 confirma que la ficha no cambia.

- [x] **T-10. Protocolo, errores globales y CORS** · ✅ completada · commit `2a497ca`
  - **RF:** RF-6 (CA-6.1 a CA-6.3). Plan DT-14. Casos ER-1 a ER-10. **Depende de:** T-09.
  - **Archivos:** `tests/api/test_simulations_protocol.py`. No se espera cambiar código: si algún caso falla, se anota en el log antes de tocar nada.
  - **Rojo (I):** la tabla 6.7, con ER-5 forzando un almacén de simulaciones que falla.
  - **Hecho cuando:** esos casos pasan y `/customers`, `/customers/1` y `/pricing/quote` conservan su `Allow`.

- [x] **T-11. Documentación interactiva** · ✅ completada · commit `f311b62`
  - **RF:** RNF-5. Plan DT-11. **Depende de:** T-09.
  - **Archivos:** `app/api/simulations_docs.py` (ejemplos, errores documentados y `restore_simulation_examples`), `app/api/simulations.py`, `app/main.py` y `tests/api/test_simulations_docs.py`.
  - **Rojo (I):** `/openapi.json` tiene las dos rutas con el ejemplo de la sección 5, `"to_users": null` incluido, y sin el 422 propio del framework.
  - **Hecho cuando:** esos tests pasan y los tests de documentación de 002 y 003 siguen en verde.

## Fase 4 — Datos de demostración (nivel D)

- [x] **T-12. Simulaciones de demostración** · ✅ completada · commit `5280838`
  - **RF:** RF-8 (CA-8.1 a CA-8.4). Plan §5 «Seed», DT-13. Casos SE-1 a SE-6. **Depende de:** T-04 y T-06.
  - **Archivos:** `app/repositories/customers.py` (`find_by_tax_id`), `app/db/seed.py` (`DEMO_SIMULATIONS`, `seed_simulations` y `main`) y `tests/integration/test_seed_simulations.py`.
  - **Rojo (D):** la tabla 6.9 y la segunda línea de `main()`.
  - **Hecho cuando:** esos casos pasan, el seed se puede repetir sin duplicar nada y el test de `main()` de 003 sigue en verde sin tocarlo.

## Fase 5 — Cierre

- [x] **T-13. Arranque real y documentación** · ✅ completada · sin commit
  - **RF:** criterios de finalización de la spec (sección 10). **Depende de:** T-11 y T-12.
  - **Archivos:** `README.md` (simulaciones, supuestos de spec D-5 y D-6) y `AGENTS.md` si cambia algún comando.
  - **Comprobación:** con `alembic upgrade head`, `python -m app.db.seed` y `uvicorn app.main:app`, un guardado, un error y un historial por línea de comandos; `/docs` muestra las dos rutas.
  - **Hecho cuando:** todo lo anterior funciona sobre una base de datos nueva y queda descrito en el README.

- [x] **T-14. Revisión conjunta y cierre** · ✅ completada · aprobada por el autor
  - **RF:** todos. **Depende de:** T-13.
  - **Comprobación:** clon limpio con un entorno virtual nuevo (`pytest`, `ruff`, `mypy` y `alembic check`); cada commit de código en verde y citando su RF o CA; cada CA y cada caso con un test que lo cita en su nivel; los criterios de la sección 10 de la spec marcados; las correcciones anotadas en el log.
  - **Hecho cuando:** el autor revisa la spec, el plan y las tareas y aprueba el cierre.
