# Tareas — 002 Endpoint de cotización

Estado: aprobado · Spec: `spec.md` v1.1 (aprobada) · Plan: `plan.md` (aprobado)

## Reglas de ejecución

- **Orden y tamaño:** una tarea cada vez, en orden. Cada una cabe en 20-30 minutos. No se empieza la siguiente hasta cumplir su «Hecho cuando».
- **Ciclo rojo → verde → revisar:**
  1. Se escriben los tests a partir de las tablas de la spec.
  2. Se confirma que fallan por el motivo esperado.
  3. Se implementa lo mínimo para que pasen.
  4. Se pasa la verificación completa.
- **Verificación completa** (desde `backend/`): `pytest`, `ruff check .`, `ruff format --check .` y `mypy .`, todo sin errores.
- **Commits:** uno por tarea, con el prefijo de `AGENTS.md` y los RF/CA que cubre, por ejemplo `feat: quote endpoint happy path (002 RF-1, RF-4, T-11)`. Sin commit hasta que el autor lo pida.
- **Dudas y correcciones:** si algo no lo resuelven la spec ni el plan, se para y se pregunta. Las correcciones al código generado se anotan en `ai-workspace/ai-review-log.md`.
- **Casos de la spec:** Q-x (cotizaciones válidas), E-x (errores de validación), O-x (protocolo); U = test sin servidor, I = petición HTTP.

## Progreso

| Fase | Tareas | Estado |
| --- | --- | --- |
| 0 — Preparación | T-01 a T-03 | ✅ Completada: instalación desde cero sin conflictos, los mismos 188 tests tras mover las fixtures, 190 en verde con los de configuración; ruff y mypy en verde |
| 1 — Esqueleto y errores globales | T-04, T-05 | ✅ Completada: 198 tests; ruff y mypy en verde; el test de la barra final detecta la redirección si se reactiva |
| 2 — Piezas de validación | T-06 a T-10 | ✅ Completada: 278 tests (80 nuevos); ruff y mypy en verde; `quote` y `set_tax_rate` sin cambios |
| 3 — Endpoint | T-11 a T-15 | ✅ Completada: 383 tests; los 33 CA con un test que los cita y pasa; los 77 casos de las tablas por HTTP; ruff y mypy en verde |
| 4 — Cierre | T-16 a T-18 | ✅ Completada: arranque real con `uvicorn` y cotización idéntica al ejemplo; p95 de 6,3 ms; clon limpio con entorno virtual nuevo en verde (383 tests, ruff, mypy y `alembic check`); los 15 commits de código en verde uno a uno; 33 CA y 77 casos con un test que los cita y pasa; los 12 puntos de la sección 10 marcados |

## Fase 0 — Preparación

- [x] **T-01. Dependencias de la API** · ✅ completada · commit `37f1ad1`
  - **RF:** soporte de RF-1 a RF-9 (plan §1). **Depende de:** ninguna.
  - **Archivos:** `backend/requirements.txt` (`fastapi`, `pydantic`, `starlette`, `uvicorn`) y `backend/requirements-dev.txt` (`httpx`).
  - **Pasos:** instalar, fijar las versiones exactas instaladas y confirmar que todo lo de 001 sigue igual.
  - **Hecho cuando:** una instalación desde cero con `requirements-dev.txt` funciona y siguen pasando los 188 tests, ruff y mypy.

- [x] **T-02. Fixtures de base de datos compartidas** · ✅ completada · commit `f5ed03d`
  - **RF:** soporte de los tests I (plan §7). **Depende de:** T-01.
  - **Archivos:** `tests/integration/conftest.py` pasa a `tests/conftest.py`; nuevo `tests/api/__init__.py`; se ajusta el import de `tests/integration/test_tax_rates_migration.py`.
  - **Hecho cuando:** pytest recoge exactamente los mismos 188 tests y todos pasan; no cambia ningún test.

- [x] **T-03. Origen del frontend configurable** · ✅ completada · commit `cbab93b`
  - **RF:** RF-9 (CA-9.1). **Depende de:** T-01.
  - **Archivos:** `app/core/config.py` (`get_frontend_origin`), `backend/.env.example` (`FRONTEND_ORIGIN`) y `tests/unit/test_config.py` (test U nuevo de configuración).
  - **Hecho cuando:** un test comprueba que, sin `FRONTEND_ORIGIN`, el valor es `http://localhost:4200` y que, con la variable, se respeta; la verificación completa está en verde.

## Fase 1 — Esqueleto de la API y errores globales

- [x] **T-04. Factoría de la aplicación y dependencias** · ✅ completada · commit `e81dd27`
  - **RF:** base de RF-1 (plan DT-8 y DT-9). **Depende de:** T-02.
  - **Archivos:** `app/main.py` (`create_app`, `app` y `lifespan` con el motor), `app/api/__init__.py` y `app/api/dependencies.py` (`get_db_session` y `get_rate_source`), y `tests/api/conftest.py` (fixture `client` sobre una base de datos migrada temporal).
  - **Hecho cuando:** un test crea la aplicación con una base de datos temporal, `GET /docs` y `GET /openapi.json` responden 200, y `from app.main import app` funciona.

- [x] **T-05. Formato único: 404 y 500** · ✅ completada · commit `033efb2`
  - **RF:** RF-6 (CA-6.1, CA-6.2, CA-6.5, CA-6.6, CA-6.7). Casos O-13 y O-14. **Depende de:** T-04.
  - **Archivos:** `app/core/errors.py` (`ApiError`, `FieldError`, textos de primer nivel y manejadores de 404 y de `Exception`), `app/main.py` (`redirect_slashes = False`) y `tests/api/test_error_format.py`.
  - **Rojo:**
    - O-13 (`GET /no-existe`) y O-14 (`/pricing/quote/` con barra final), que hoy devuelven `{"detail": ...}`.
    - Un 500 provocado con una ruta de prueba que falla: el cuerpo no puede llevar «Traceback» ni el mensaje interno.
  - **Hecho cuando:** O-13 y O-14 devuelven 404 `not_found` «Recurso no encontrado» con `details` vacío y sin redirección, y el 500 de prueba devuelve `internal_error` en JSON sin información interna.

## Fase 2 — Piezas de validación

- [x] **T-06. Normalizar el país** · ✅ completada · commit `a7f76a8`
  - **RF:** RF-3 (CA-3.1, CA-3.2, CA-3.6). **Depende de:** T-01.
  - **Archivos:** `app/schemas/__init__.py`, `app/schemas/pricing.py` (`normalize_country`) y `tests/unit/test_quote_schema.py`.
  - **Rojo (U):**
    - Normaliza los países de Q-11 a Q-19 (`"es"`, `" ES "`, tabulador y salto de línea, minúsculas de cada país).
    - Rechaza los de E-18 a E-25 (`"ESP"`, `"E"`, `"12"`, `"E S"`, ancho completo, espacio no separable, solo espacios, vacío) y también `"ß"`.
  - **Hecho cuando:** pasan todos esos casos U, y el código no usa `str.strip()` sin argumentos ni `str.upper()` (plan DT-3).

- [x] **T-07. Esquema de la petición y traducción de errores** · ✅ completada · commit `df42031`
  - **RF:** RF-2 (CA-2.1 a CA-2.3), RF-3 (CA-3.3, CA-3.5), RF-5 (CA-5.1, CA-5.2) y RF-6 (CA-6.3). **Depende de:** T-06.
  - **Archivos:** `app/schemas/pricing.py` (`QuoteRequest` estricto con `extra="forbid"` y los mensajes de campo), `app/api/validation.py` (`field_errors`) y `tests/unit/test_quote_schema.py`.
  - **Rojo (U):**
    - Con los datos ya decodificados de E-1 a E-16 y E-26 a E-36 (salvo E-35, que necesita la base de datos), `field_errors` devuelve exactamente el `field` y el mensaje de la tabla 6.2.
    - `-0` se acepta como 0.
  - **Hecho cuando:** todos esos casos U pasan, con un solo elemento por campo (E-15) y los dos detalles en E-31 y E-36.

- [x] **T-08. Esquema de la respuesta** · ✅ completada · commit `43fee6c`
  - **RF:** RF-4 (CA-4.1 a CA-4.4). **Depende de:** T-06.
  - **Archivos:** `app/schemas/pricing.py` (`TierLineResponse`, `QuoteResponse.from_quote` y el ejemplo para `/docs`) y `tests/unit/test_quote_schema.py`.
  - **Rojo (U):** `QuoteResponse.from_quote(build_quote(15, 2100))` serializado a JSON es igual al ejemplo de la sección 5 de la spec.
  - **Hecho cuando:** ese JSON coincide campo a campo, con `"to_users": null` en el tramo 3, `"currency": "EUR"` y todos los números enteros.

- [x] **T-09. Saber si un país está soportado** · ✅ completada · commit `d17f835`
  - **RF:** RF-3 (CA-3.4). **Depende de:** T-02.
  - **Archivos:** `app/services/pricing.py` (`country_is_supported`, sin tocar `quote`) y `tests/integration/test_quote_service.py`.
  - **Rojo (D):** `ES` está soportado; `XX`, `es` y `""` no lo están; tras borrar la tasa de `PT`, deja de estarlo.
  - **Hecho cuando:** pasan esos casos y los 188 tests de 001 siguen en verde.

- [x] **T-10. Leer el cuerpo de la petición** · ✅ completada · commit `3b35410`
  - **RF:** RF-7 (CA-7.1 a CA-7.3). **Depende de:** T-05.
  - **Archivos:** `app/api/validation.py` (`read_json_object`) y `tests/unit/test_read_json_object.py`, con peticiones de Starlette construidas a mano, sin servidor.
  - **Rojo (U):**
    - Rechaza con 422 body/BODY los cuerpos de E-37 a E-42.
    - Acepta `application/json; charset=utf-8` (O-1) y `Application/JSON` (O-15).
    - Con claves repetidas gana la última (O-2).
  - **Hecho cuando:** pasan todos esos casos U.

## Fase 3 — Endpoint (nivel I)

- [x] **T-11. Ruta `POST /pricing/quote` y cotizaciones válidas** · ✅ completada · commit `e149fbf`
  - **RF:** RF-1 (CA-1.1 a CA-1.3), RF-3 (CA-3.1, CA-3.6), RF-4 (CA-4.1 a CA-4.4) y RF-7 (CA-7.1 a CA-7.3). **Depende de:** T-07, T-08, T-09 y T-10.
  - **Archivos:** `app/api/pricing.py` (router, camino feliz: leer, validar, `quote` y responder), `app/main.py` (incluir el router) y `tests/api/test_quote_valid.py`.
  - **Rojo (I):** Q-1 a Q-20, O-1, O-2, O-6, O-7, O-9, O-15 y E-37 a E-42. Hoy fallan porque la ruta no existe.
  - **Hecho cuando:**
    - todos esos casos pasan por HTTP;
    - Q-4 devuelve exactamente el ejemplo de la sección 5;
    - las respuestas 200 no llevan `Location` ni `id`;
    - y ningún número de la respuesta tiene decimales.

- [x] **T-12. Errores de validación por HTTP** · ✅ completada · commit `0650756`
  - **RF:** RF-2 (CA-2.1 a CA-2.3), RF-3 (CA-3.2 a CA-3.5), RF-5 (CA-5.1, CA-5.2) y RF-6 (CA-6.1, CA-6.3, CA-6.4). **Depende de:** T-11.
  - **Archivos:**
    - `app/api/pricing.py`: camino de error, es decir, `field_errors` más la comprobación del país con `country_is_supported` (plan DT-4).
    - `app/core/errors.py`: `ApiError` 422 y el mapeo de `UnsupportedCountryError` e `InvalidUsersError`.
    - `tests/api/test_quote_validation_errors.py`.
  - **Rojo (I):** E-1 a E-36. Hoy dan 500 porque los errores de Pydantic y de dominio no se traducen.
  - **Hecho cuando:** E-1 a E-36 devuelven 422 `validation_error` «Datos no válidos» con exactamente los `details` de la tabla 6.2 (comparados como conjunto), incluidos E-17 (que pasa por el error de dominio) y E-35 (los dos errores a la vez).

- [x] **T-13. Métodos no permitidos, fallo interno y tipo de contenido** · ✅ completada · commit `adfc8e4`
  - **RF:** RF-8 (CA-8.1) y RF-6 (CA-6.2, CA-6.5, CA-6.6). **Depende de:** T-12.
  - **Archivos:** `app/core/errors.py` (405 conservando `Allow`) y `tests/api/test_quote_protocol.py`.
  - **Rojo (I):**
    - O-3 y O-4: `GET`, `PUT`, `PATCH`, `DELETE`, `HEAD` y `OPTIONS` sin preflight, que hoy dan `{"detail": ...}`.
    - O-5: la fuente de tasas se sustituye por una que falla.
    - O-8: tipo de contenido de las respuestas.
  - **Hecho cuando:**
    - O-3 y O-4 dan 405 `method_not_allowed` con `Allow: POST` (`HEAD` sin cuerpo);
    - O-5 da 500 `internal_error` sin «Traceback», rutas ni nombres de módulos;
    - y Q-4, E-1, O-3, O-5 y O-13 llevan `Content-Type: application/json`.

- [x] **T-14. CORS limitado al frontend** · ✅ completada · commit `0ae896e`
  - **RF:** RF-9 (CA-9.1 a CA-9.4). **Depende de:** T-03 y T-11.
  - **Archivos:** `app/main.py` (`CORSMiddleware` con el origen configurado, método `POST` y cabecera `Content-Type`) y `tests/api/test_cors.py`.
  - **Rojo (I):** O-10 a O-12. Hoy no hay cabeceras de CORS.
  - **Hecho cuando:**
    - O-10 da 200 con `Access-Control-Allow-Origin: http://localhost:4200`, que permite `POST` y `Content-Type`;
    - O-11, desde otro origen, no lleva esa cabecera;
    - y O-12 es igual que Q-4 y la lleva.

- [x] **T-15. Documentación interactiva** · ✅ completada · commit `db626bd`
  - **RF:** RF-1 y RNF-5. **Depende de:** T-11.
  - **Archivos:** `app/api/pricing.py` (`openapi_extra` con el esquema y el ejemplo de la petición) y `tests/api/test_openapi_docs.py`.
  - **Rojo (I):** `/openapi.json` no describe hoy el cuerpo de `POST /pricing/quote`, porque se lee en crudo (plan DT-1).
  - **Hecho cuando:** `/openapi.json` tiene en `POST /pricing/quote` el esquema de la petición con el ejemplo `{"users": 15, "country": "ES"}` y la respuesta 200 con el ejemplo de la sección 5, y `/docs` responde 200.

## Fase 4 — Cierre

- [x] **T-16. Arranque real con `uvicorn`** · ✅ completada · commit `bf7164b`
  - **RF:** criterio de arranque de la sección 10 de la spec. **Depende de:** T-15.
  - **Archivos:** `AGENTS.md` (el comando queda confirmado).
  - **Pasos:**
    1. `alembic upgrade head` sobre una base de datos vacía.
    2. `cd backend && uvicorn app.main:app --reload`.
    3. Abrir `/docs` y hacer una cotización real por la línea de comandos.
  - **Hecho cuando:** el servidor arranca sin errores, `/docs` responde 200, la cotización `{"users": 15, "country": "ES"}` devuelve exactamente el ejemplo de la sección 5, y `AGENTS.md` marca el comando como confirmado.

- [x] **T-17. Medir el rendimiento (informativo)** · ✅ completada · commit `75ff2fd`
  - **RF:** RNF-2. **Depende de:** T-16.
  - **Archivos:** `README.md` (resultado y método de medición).
  - **Pasos:** con el servidor arrancado, 100 cotizaciones seguidas; calcular el percentil 95.
  - **Hecho cuando:** el README recoge el p95 obtenido, la máquina y el método. Si supera los 200 ms se anota igualmente, porque no bloquea la entrega.

- [x] **T-18. Comprobación final** · ✅ completada
  - **RF:** todos (sección 10 de la spec). **Depende de:** T-17.
  - **Archivos:** `spec.md` (checklist), `tasks.md` (estados), `ai-workspace/ai-review-log.md`.
  - **Pasos:**
    1. Verificación completa en un clon limpio con un entorno virtual nuevo.
    2. Trazabilidad por test: cada CA citado en el docstring de un test que pasa.
    3. Los 77 casos de la spec presentes.
    4. Checklist de la sección 10.
    5. Anotar las correcciones en el log.
  - **Hecho cuando:** los 33 CA y los 77 casos tienen test en verde, todos los puntos de la sección 10 están marcados y cada tarea muestra su estado.

## Trazabilidad

| CA de la spec v1.1 | Tareas |
| --- | --- |
| CA-1.1 a CA-1.3 | T-11 |
| CA-2.1 a CA-2.3 | T-07, T-11 (`-0`), T-12 |
| CA-3.1, CA-3.6 | T-06, T-11 |
| CA-3.2 | T-06, T-12 |
| CA-3.3, CA-3.5 | T-07, T-12 |
| CA-3.4 | T-09, T-12 |
| CA-4.1 a CA-4.4 | T-08, T-11 |
| CA-5.1, CA-5.2 | T-07, T-12 |
| CA-6.1 | T-05, T-12 |
| CA-6.2, CA-6.5, CA-6.6 | T-05, T-13 |
| CA-6.3 | T-07, T-12 |
| CA-6.4 | T-12 |
| CA-6.7 | T-05 |
| CA-7.1 a CA-7.3 | T-10, T-11 |
| CA-8.1 | T-13 |
| CA-9.1 | T-03, T-14 |
| CA-9.2 a CA-9.4 | T-14 |

Reparto de los casos:
- **T-05:** O-13 y O-14.
- **T-11:** Q-1 a Q-20, E-37 a E-42, O-1, O-2, O-6, O-7, O-9 y O-15.
- **T-12:** E-1 a E-36.
- **T-13:** O-3 a O-5 y O-8.
- **T-14:** O-10 a O-12.

Los RNF:
- **RNF-1:** T-11, porque el endpoint solo llama a `quote`.
- **RNF-2:** T-17.
- **RNF-3:** T-13 y T-14.
- **RNF-4:** T-07, T-12 y T-13.
- **RNF-5:** T-15.
