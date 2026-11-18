# ADR 0001 — Backend en Python con FastAPI y frontend en Angular

Estado: aceptado

## Contexto

El enunciado pide una API REST con base de datos y un dashboard web que se comunican entre sí, y solo fija dos piezas: SQLite como base de datos y `open.er-api.com` como servicio de tipos de cambio (§1 y §5 del documento 00). El resto del stack queda libre. El stack de la oferta es Python con FastAPI y Angular.

## Decisión

- `backend/`: Python 3.12+ con FastAPI, Pydantic v2 para validar toda entrada en el borde de la API, SQLAlchemy 2 para el acceso a datos y Alembic para las migraciones, sobre SQLite. Tests con pytest y httpx.
- `frontend/`: Angular con componentes standalone, signals y HttpClient; RxJS solo para la espera tras escribir (debounce) y la cancelación de peticiones. Tests con el runner por defecto de Angular (Vitest, concretado en el ADR 0010).

Las dos partes viven en un único repositorio. El principio 1 de la constitución cierra este stack: cualquier dependencia, servicio o herramienta que no esté aquí necesita su propio ADR, como el 0008 (mypy).

## Alternativa descartada

Otro stack que el enunciado también permite. Se descarta porque no aporta nada que pida el enunciado y aleja la entrega del stack de la oferta.

## Consecuencias

- FastAPI publica la documentación OpenAPI en `/docs` sin trabajo adicional.
- El formato de error 422 de FastAPI no es el de la API (§8.4 del 00), así que un único manejador lo adapta.
- Hay que instalar dos entornos, Python y Node: el README indica sus versiones y los pasos para levantar ambos (§6 del 00).
- SQLite basta para decenas de usuarios simultáneos; el límite se documenta en el README (§6 del 00).
