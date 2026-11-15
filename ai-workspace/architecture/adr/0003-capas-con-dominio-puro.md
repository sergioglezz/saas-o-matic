# ADR 0003 — Backend en capas con un dominio puro

Estado: aceptado

## Contexto

La prueba evalúa que el código sea limpio, modular y sin archivos masivos (§9 del documento 00), y el 00 limita los archivos a 300 líneas y las funciones a 40 (§6). Las reglas de negocio (precios por tramos, impuestos y validación del identificador fiscal) son lo que más pesa en la calidad del software, y sus tablas de casos (§7) tienen que poder probarse sin servidor web ni base de datos.

## Decisión

Las dependencias van hacia dentro: `api` → `services` → (`repositories`, `domain`) (§5 del 00, principio 3 de la constitución).

- `api`: routers de FastAPI, con sus modelos Pydantic en `schemas`. Solo HTTP; sin lógica de negocio ni SQL.
- `services`: casos de uso que orquestan el dominio y los repositorios.
- `repositories`: único lugar con acceso a la base de datos, cuyos modelos, sesión, migraciones y seed viven en `db`.
- `domain`: funciones puras, sin entrada/salida. No importa FastAPI, SQLAlchemy ni Pydantic.

Las excepciones del dominio no llevan texto para el usuario y se traducen a HTTP en un único punto (§6 del 00, DT-8 del plan de 001). El test `backend/tests/unit/test_domain_architecture.py` lee con `ast` los imports de cada módulo de `app/domain/` y falla si alguno importa SQLAlchemy, Alembic, FastAPI, Pydantic, `app.db`, `app.repositories` o `app.services`: romper la regla rompe la suite.

## Alternativa descartada

Poner las reglas de negocio en los routers o en los modelos del ORM. Probar un tramo o un redondeo exigiría levantar la API o la base de datos, y cada archivo acumularía validación, cálculo y persistencia.

## Consecuencias

- Las reglas se prueban con tests unitarios rápidos, sin base de datos ni servidor (RNF-2 de la spec 001).
- Hay más archivos y un salto más entre el router y el cálculo.
