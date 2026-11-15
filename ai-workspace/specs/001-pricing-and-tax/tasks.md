# Tareas — 001 Precios por tramos e impuestos

Estado: aprobado (2026-11-14) · Spec: `spec.md` v1.2 (aprobada) · Plan: `plan.md` (aprobado)

## Progreso

| Fase | Tareas | Estado | Verificación del bloque |
| --- | --- | --- | --- |
| 0 — Preparación | T-01 | ✅ Completada (2026-11-14) | Instalación desde cero; ruff y mypy en verde |
| 1 — Dominio puro | T-02 a T-06 | ✅ Completada (2026-11-15) | 116 tests; ruff y mypy en verde |
| 2 — Datos | T-07 a T-09 | ✅ Completada (2026-11-15) | 144 tests; ruff y mypy en verde; `alembic upgrade head`, `current` y `check` por línea de comandos |
| 3 — Servicio | T-10, T-11 | Pendiente | — |
| 4 — Cierre | T-12 | Pendiente | — |

## Reglas de ejecución

- Se trabaja **una tarea cada vez y en orden**. No se empieza la siguiente hasta que la anterior cumple su «Hecho cuando» (AGENTS.md).
- Cada tarea con código sigue el ciclo **rojo → verde → revisar**:
  1. Se escriben los tests a partir de las tablas de la spec.
  2. Se ejecutan y se confirma que fallan por el motivo esperado.
  3. Se implementa lo mínimo para que pasen.
  4. Se ejecuta la verificación completa.
- **Verificación completa** (desde `backend/`): `pytest`, `ruff check .`, `ruff format --check .` y `mypy .`, todo sin errores.
- **Un commit por tarea**, con el prefijo de AGENTS.md y los requisitos que cubre, por ejemplo `feat: tier breakdown (001 RF-1, RF-2)`. Sin commit hasta que lo pidas.
- Si una tarea descubre algo que la spec o el plan no resuelven, se para y se pregunta. Cada corrección de código generado por la IA se anota en `ai-workspace/ai-review-log.md`.

## Fase 0 — Preparación

### T-01. Esqueleto del backend y herramientas

- **Estado:** ✅ completada (2026-11-14) · commit `1cedbc1`

- **Archivos:**
  - `backend/app/__init__.py` y los paquetes vacíos `domain/`, `services/`, `repositories/`, `db/` y `core/`.
  - `backend/tests/unit/` y `backend/tests/integration/`.
  - `backend/requirements.txt` (SQLAlchemy 2 y Alembic) y `backend/requirements-dev.txt` (`-r requirements.txt`, pytest, ruff y mypy).
  - `backend/pyproject.toml` (ruff; mypy en modo estricto; pytest con `testpaths = tests` y `app` importable sin instalar el paquete).
  - `backend/.env.example` (`DATABASE_URL`).
  - `.gitignore` en la raíz (`.venv`, `.env`, `*.db`, `__pycache__`, `node_modules`).
- **Cubre:** plan §1 y §2, ADR 0008. Ningún RF.
- **Pasos:**
  1. Crear la estructura.
  2. Instalar en un entorno virtual con `pip install -r requirements-dev.txt`.
  3. Fijar en `requirements*.txt` las versiones exactas que se instalen.
- **Hecho cuando:**
  - La instalación funciona desde cero.
  - `ruff check .`, `ruff format --check .` y `mypy .` pasan.
  - `pytest` se ejecuta sin errores de configuración. Con 0 tests sale con «no tests ran», y eso es lo esperado.
  - Los comandos de AGENTS.md que aplican al backend quedan confirmados.

## Fase 1 — Dominio puro (nivel U)

### T-02. Errores de dominio y desglose por tramos

- **Estado:** ✅ completada (2026-11-15) · commit `e0403c5`

- **Archivos:** `app/domain/errors.py`, `app/domain/pricing.py` (`Tier`, `TierLine`, `TIERS`, `MAX_USERS`, `tier_breakdown`) y `tests/unit/test_tier_breakdown.py`.
- **Depende de:** T-01.
- **Cubre:** CA-1.1 a CA-1.4 y CA-2.1 a CA-2.4. Casos P-1 a P-10.
- **Rojo:**
  - Un test parametrizado con P-1 a P-10 que compara, en cada tramo, `units` y `amount_cents`, y la suma de los tramos con `subtotal_cents`.
  - En cada fila se comprueban también los invariantes: 3 tramos ordenados, límites 1/10, 11/50 y 51/`None`, `amount = units × price`, suma de `units` = `users` y suma de `amount_cents` = subtotal.
- **Verde:** el algoritmo de `tier_breakdown` del plan §5, y la jerarquía `PricingError` del plan §4.
- **Hecho cuando:** pasan P-1 a P-10 con todos los invariantes y la verificación completa está en verde.

### T-03. Validación del número de usuarios

- **Estado:** ✅ completada (2026-11-15) · commit `40b5f00`

- **Archivos:** `app/domain/pricing.py` (`validate_users`) y `tests/unit/test_validate_users.py`.
- **Depende de:** T-02.
- **Cubre:** CA-3.1 a CA-3.4. Casos X-1, X-2 y X-3, y los límites 0 y 100 000.
- **Rojo:**
  - 0 y 100 000 se aceptan.
  - −1 y 100 001 lanzan `InvalidUsersError`.
  - `True`, `False`, `15.0` y `"15"` lanzan `InvalidUsersError`.
- **Verde:** `validate_users` con `type(x) is int` y el rango.
- **Hecho cuando:** pasan todos los casos, también los booleanos, y la verificación completa está en verde.

### T-04. Impuesto y redondeo

- **Estado:** ✅ completada (2026-11-15) · commit `4dc076e`

- **Archivos:** `app/domain/tax.py` (`tax_cents` y `validate_rate_bp`) y `tests/unit/test_tax.py`.
- **Depende de:** T-02.
- **Cubre:** CA-6.1 a CA-6.3, y la parte de dominio de CA-13.1. Casos R-1 a R-9 sobre `tax_cents`.
- **Rojo:**
  - R-1 a R-9: `(subtotal, tasa) → tax_cents`.
  - `validate_rate_bp` acepta 0 y 10 000.
  - `validate_rate_bp` rechaza −1, 10 001 y `True` con `InvalidTaxRateError`.
- **Verde:** la fórmula entera `(s·r + 5000) // 10000` y la validación del rango.
- **Hecho cuando:** pasan R-1 a R-9 y los casos de rango, y el módulo no usa `float`, `round()` ni `Decimal`.

### T-05. Resultado completo: `build_quote` y `PriceQuote`

- **Estado:** ✅ completada (2026-11-15) · commit `214c28c`

- **Archivos:** `app/domain/pricing.py` (`PriceQuote` y `build_quote`) y `tests/unit/test_build_quote.py`.
- **Depende de:** T-03 y T-04.
- **Cubre:** CA-4.4, CA-4.5, CA-6.3 y CA-7.1 a CA-7.3. Casos T-1 a T-10 (con la tasa de la columna), R-1 a R-9 y el ejemplo de la sección 5 de la spec.
- **Rojo:**
  - T-1 a T-10 y R-1 a R-9 comparan `subtotal_cents`, `tax_rate_bp`, `tax_cents` y `total_cents`.
  - El ejemplo de 15 usuarios en ES se compara campo a campo, con `currency` = `EUR`.
  - En los resultados, todos los importes son `int`.
- **Verde:** `build_quote` según el plan §5.
- **Hecho cuando:** pasan todos los casos y la verificación completa está en verde.

### T-06. Test de arquitectura del dominio

- **Estado:** ✅ completada (2026-11-15) · commit `bd0aad9`

- **Archivos:** `tests/unit/test_domain_architecture.py`.
- **Depende de:** T-05.
- **Cubre:** el principio 3 de la constitución y RNF-2.
- **Rojo:** hay que demostrar que el test detecta una infracción. Se añade de forma temporal un `import sqlalchemy` en un archivo de dominio, se comprueba que el test falla y se retira el import.
- **Verde:** ningún archivo de `app/domain/` importa `sqlalchemy`, `alembic`, `fastapi`, `pydantic`, `app.db`, `app.repositories` ni `app.services`.
- **Hecho cuando:** el test pasa con el código real y está demostrado que falla con la infracción.

## Fase 2 — Datos (nivel D)

### T-07. Configuración, sesión y modelo `TaxRate`

- **Estado:** ✅ completada (2026-11-15) · commit `aae98cc`

- **Archivos:** `app/core/config.py`, `app/db/session.py`, `app/db/models.py` y `tests/integration/test_session.py`.
- **Depende de:** T-01.
- **Cubre:** el `PRAGMA foreign_keys=ON` del §5 y §8.5 del documento 00, y el modelo de la tabla del plan §3.
- **Rojo:**
  - Una conexión nueva devuelve `PRAGMA foreign_keys` = 1.
  - Sin la variable de entorno, `DATABASE_URL` toma el valor local por defecto, y con la variable definida la respeta.
- **Verde:**
  - `DATABASE_URL` se lee con `os.environ`.
  - Una factoría de motor con un listener `connect` que activa el PRAGMA.
  - El modelo `TaxRate` con los dos CHECK.
- **Hecho cuando:** los tests pasan y la verificación completa está en verde.

### T-08. Alembic y migración `0001_create_tax_rates`

- **Estado:** ✅ completada (2026-11-15) · commit `4891732` · migración congelada desde aquí

- **Archivos:** `backend/alembic.ini`, `app/db/migrations/env.py`, `app/db/migrations/versions/0001_create_tax_rates.py`, `tests/integration/conftest.py` y `tests/integration/test_tax_rates_migration.py`.
- **Depende de:** T-07.
- **Cubre:** CA-4.2 y CA-4.3, y la parte de base de datos de CA-13.1. Caso C-6 y los CHECK del plan §3.
- **Rojo:**
  - Fixture: un SQLite en `tmp_path` con `alembic upgrade head` ejecutado por código.
  - C-6: hay exactamente 7 filas con los valores de CA-4.3.
  - Una inserción directa con 10001, −1, 21.5, «es» o «ESP» falla con un error de integridad.
  - `downgrade` elimina la tabla.
- **Verde:** `env.py` toma la URL de `core.config` (o la de la prueba), y la migración crea la tabla con sus CHECK e inserta las 7 filas en bloque.
- **Hecho cuando:**
  - Los tests pasan.
  - `alembic upgrade head` funciona sobre una base de datos vacía desde la línea de comandos.
  - La migración queda congelada: desde aquí no se edita.

### T-09. Repositorio de tasas

- **Estado:** ✅ completada (2026-11-15) · commit `220c747`

- **Archivos:** `app/repositories/tax_rates.py` (`TaxRateRepository`: `get_rate_bp`, `upsert` y `delete`) y `tests/integration/test_tax_rate_repository.py`.
- **Depende de:** T-08.
- **Cubre:** CA-4.1 y CA-4.7.
- **Rojo:**
  - `get_rate_bp("ES")` devuelve 2100.
  - `get_rate_bp` devuelve `None` para `"XX"`, `"es"` y `""`.
  - `upsert` inserta un país nuevo y actualiza uno existente.
  - `delete` hace que `get_rate_bp` devuelva `None`.
- **Verde:** las consultas con el ORM, sin SQL concatenado.
- **Hecho cuando:** los tests pasan y la verificación completa está en verde.

## Fase 3 — Servicio (nivel D)

### T-10. Servicio `quote`

- **Archivos:** `app/services/pricing.py` (el protocolo `TaxRateSource` y `quote`) y `tests/integration/test_quote_service.py`.
- **Depende de:** T-05 y T-09.
- **Cubre:** CA-3.5, CA-4.1, CA-4.6, CA-4.7 y CA-13.3. Casos P-1 a P-10 (con US), T-1 a T-10, X-1, X-2 y X-4 a X-7, y el ejemplo de la sección 5 de la spec.
- **Rojo:**
  - Todos los casos anteriores, pasando por `quote` con el repositorio real.
  - Un espía que envuelve el repositorio y cuenta exactamente 1 llamada a `get_rate_bp` por cotización.
  - X-7 (−1 usuarios y «XX») devuelve `InvalidUsersError`.
- **Verde:** `quote` según el plan §5: primero los usuarios, luego una sola lectura de la tasa y por último `build_quote`.
- **Hecho cuando:** pasan todos los casos y la verificación completa está en verde.

### T-11. `set_tax_rate` y configuración de tasas

- **Archivos:** `app/services/pricing.py` (`set_tax_rate`) y `tests/integration/test_tax_rate_config.py`.
- **Depende de:** T-10.
- **Cubre:** CA-13.1 y CA-13.2. Casos C-1 a C-5 y R-1 a R-9 en el nivel D.
- **Rojo:**
  - C-1 y C-2: 10001 y −1 se rechazan con `InvalidTaxRateError`, y la tasa de ES no cambia.
  - C-3: se aceptan 10 000 y 0.
  - C-4: tras borrar PT, la cotización devuelve `UnsupportedCountryError`.
  - C-5: el cambio de tasa se refleja en la siguiente cotización.
  - R-1 a R-9: se configura ES con la tasa de la columna y se cotiza.
- **Verde:** `set_tax_rate` valida con `validate_rate_bp` y llama a `upsert`.
- **Hecho cuando:** pasan todos los casos y la verificación completa está en verde.

## Fase 4 — Cierre

### T-12. Comprobación final y documentación

- **Archivos:** `README.md` (solo la sección «Decisiones y supuestos» con las tasas por defecto, D-3) y `ai-workspace/ai-review-log.md`.
- **Depende de:** T-11.
- **Pasos:**
  1. Verificación completa desde cero, en un entorno virtual nuevo.
  2. Comprobar que cada CA vigente de la spec aparece citado en al menos un test, buscando en `tests/`.
  3. Marcar el checklist de la sección 10 de la spec.
  4. Anotar en `ai-review-log.md` las correcciones hechas al código generado.
- **Hecho cuando:** todos los puntos de la sección 10 de la spec están marcados y la spec 001 queda lista para que la consuma la 002.

## Trazabilidad

| CA de la spec v1.2 | Tareas |
| --- | --- |
| CA-1.1 a CA-1.4 | T-02, T-05, T-10 |
| CA-2.1 a CA-2.4 | T-02 |
| CA-3.1 a CA-3.4 | T-03, T-10 |
| CA-3.5 | T-10 |
| CA-4.1 | T-09, T-10 |
| CA-4.2, CA-4.3 | T-08 |
| CA-4.4, CA-4.5 | T-05, T-10 |
| CA-4.6, CA-4.7 | T-09, T-10, T-11 |
| CA-6.1 a CA-6.3 | T-04, T-05, T-11 |
| CA-7.1 a CA-7.3 | T-05 |
| CA-13.1 | T-04, T-08, T-11 |
| CA-13.2 | T-11 |
| CA-13.3 | T-10 |

Todos los casos de la spec quedan asignados: P-1 a P-10 en T-02 y T-10; T-1 a T-10 en T-05 y T-10; R-1 a R-9 en T-04, T-05 y T-11; C-1 a C-5 en T-11; C-6 en T-08; X-1 a X-3 en T-03 (X-1 y X-2 también en T-10); X-4 a X-7 en T-10.
