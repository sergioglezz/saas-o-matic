# AGENTS.md — SaaS-O-Matic

## Proyecto

SaaS-O-Matic es una herramienta interna para que un equipo comercial simule y presupueste suscripciones SaaS multi-divisa para clientes corporativos. Es un monorepo con una API REST en Python 3.12+ (FastAPI, SQLAlchemy 2, Pydantic v2, Alembic) sobre SQLite en `backend/`, y un dashboard Angular en `frontend/`. Todo el proceso (constitución, specs, ADRs, prompts y log de revisión) vive en `ai-workspace/`, con una guía en `ai-workspace/README.md`.

El backend va por capas: `api` → `services` → (`repositories`, `domain`). `domain` solo contiene funciones puras (precios por tramos, impuestos, validación de identificadores fiscales). El backend calcula todos los importes; el frontend solo los muestra y convierte la divisa.

## Comandos

Todos se confirmaron al crear su parte del proyecto (002 T-16, 003 T-19 y 005 T-16): los del backend, con el entorno virtual activado; los del frontend, con Node 26 LTS (ADR 0010) y `npm install` hecho. Si un comando falla, avísame y propón el cambio; no lo inventes.

* Migraciones y datos demo: `cd backend && alembic upgrade head && python -m app.db.seed`. El seed se puede repetir sin duplicar datos.
* Ejecutar backend: `cd backend && uvicorn app.main:app --reload` (API en `http://127.0.0.1:8000`, documentación en `/docs`). Usa `127.0.0.1` y no `localhost`: en Windows, `localhost` añade unos 0,2 s a cada conexión.
* Ejecutar frontend: `cd frontend && npm start` (`http://localhost:4200`, el único origen que admite CORS).
* Tests: `cd backend && pytest` y `cd frontend && npm test` (una sola pasada).
* Lint/formato: `cd backend && ruff check . && ruff format . && mypy .` y `cd frontend && npm run lint`; `npm run build` compila para producción.

## Estilo y convenciones

* Python 3.12+ con type hints completos; TypeScript en modo `strict`, sin `any`.
* Código en inglés: `snake_case` en Python y en los campos de la API, `camelCase`/`PascalCase` en
  TypeScript, archivos de Angular en `kebab-case`.
* Interfaz, mensajes de error y README en español. Commits con prefijos `docs:`, `feat:`, `test:`,
  `fix:` o `chore:`.
* Archivos de menos de 300 líneas y funciones de menos de 40. Comentarios solo para explicar el porqué.
* Dinero siempre en céntimos enteros (`*_cents`) y tasas en puntos básicos (`*_bp`). Nunca `float`.
* Errores de la API con un único formato: `{"error": {"code", "message", "details"}}`.

## Reglas

* Lee `ai-workspace/docs/constitution.md` y la spec activa
  (`ai-workspace/specs/`, con su `plan.md` y `tasks.md` si existen) antes de tocar código. Para el contexto general y las reglas de negocio (RN-x) consulta `ai-workspace/specs/00-spec-first.md`. Si el código y la spec chocan, manda la spec; si algo es ambiguo, pregunta.
* Tests primero: derívalos de la tabla de casos de prueba de la spec. No borres ni relajes un test para que pase.
* Si existe `tasks.md`, trabaja tarea a tarea y no adelantes las siguientes.
* Respeta las capas: sin lógica de negocio en los routers y sin imports de FastAPI o SQLAlchemy en `domain`.
* No añadas sin preguntar: dependencias nuevas (requieren un ADR), autenticación, Docker,
  funcionalidades fuera de la spec ni cambios en la estructura de carpetas.
* No modifiques specs aprobadas ni migraciones ya creadas: propón el cambio y espera mi aprobación.
* Seguridad: SQL solo mediante ORM o consultas parametrizadas; toda entrada validada con Pydantic; sin secretos en el repo (`.env` ignorado, `.env.example` versionado); CORS limitado al origen del frontend; foreign keys de SQLite activadas.
* Frontend: llamadas HTTP solo desde servicios; toda pantalla que consulta datos muestra estados de carga, error y vacío; muestra la atribución «Rates By Exchange Rate API» junto a las tasas.

## Al terminar cualquier tarea

* Ejecuta los tests y el lint de la parte que has tocado. No des la tarea por terminada si algo falla.
* Comprueba los criterios de aceptación de la spec activa y dime cuáles has verificado.
* Resume qué archivos has cambiado y qué decisiones has tomado. Si corregiste un fallo de tu propio
  código, dímelo para anotarlo en `ai-workspace/ai-review-log.md`.
* No hagas commit salvo que te lo pida.
