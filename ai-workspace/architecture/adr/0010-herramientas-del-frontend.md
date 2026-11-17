# ADR 0010 — Herramientas del frontend: Angular 22, Node 24 y angular-eslint

Estado: propuesto (redactado con el plan de la spec 005; pendiente de la revisión del autor)

## Contexto

La ADR 0001 fija Angular para el frontend, con «el runner por defecto de Angular» para los tests, pero no fija versiones ni herramienta de lint. El principio 6 de la constitución exige que ESLint y TypeScript strict pasen sin errores, y `AGENTS.md` define el comando `npm run lint`, que un proyecto Angular recién creado no trae. Por el principio 1, todo lo que no forma parte del stack necesita un ADR, como el 0008 hizo con mypy.

Al planificar la spec 005 (noviembre de 2026), la versión con soporte de Angular es la 22, que exige Node ^22.22.3, ^24.15.0 o ≥ 26. El equipo tenía Node 22.11.0, que solo admite Angular 19, sin soporte desde mayo de 2026. El autor decidió actualizar a Node 24 LTS.

## Decisión

- **Node 24 LTS** para el frontend. El README lo indica junto a la versión de Python.
- **Angular 22**, con el proyecto base que genera Angular CLI en `frontend/`: componentes standalone, sin renderizado en servidor y con TypeScript en modo estricto. Sus dependencias (Angular, RxJS, TypeScript y las del runner) son el «proyecto base» al que se refiere RNF-9 de la spec 005.
- **Tests con el runner por defecto de Angular 22** (Vitest con un DOM simulado), tal como lo genera la CLI. No se añade ningún runner ni navegador de pruebas.
- **Lint con angular-eslint**, añadido con su esquema oficial (`ng add angular-eslint`). Es una dependencia solo de desarrollo y define `npm run lint`. Su configuración, además de las reglas recomendadas:
  - prohíbe `any` explícito (`AGENTS.md`);
  - limita los imports para respetar las capas: las funciones puras de formato y de reglas no importan Angular ni RxJS, y fuera de `core/` nadie importa el cliente HTTP (`AGENTS.md`: «llamadas HTTP solo desde servicios»).

## Alternativa descartada

- **Angular 19 con Node 22.11:** sin cambiar el equipo, pero sin parches de seguridad y con tests que necesitan un navegador real (Karma).
- **Solo `tsc --noEmit` como lint:** comprobaría los tipos, pero no las reglas de Angular, el `any` explícito ni las capas, y no cumpliría el principio 6.
- **Un runner o una herramienta de pruebas de extremo a extremo** (por ejemplo, con un navegador automatizado): sería otra dependencia para comprobar lo que cubren las pruebas manuales MA-1 a MA-9 de la spec 005.

## Consecuencias

- Quien levante el proyecto necesita Node 24; el README lo dice antes del primer comando.
- `npm run lint` falla si alguien rompe las capas del frontend o usa `any`, igual que mypy en el backend.
- Las pruebas de componentes se ejecutan sin navegador. Lo que depende de comportamientos nativos (teclado, límite de caracteres al escribir) se comprueba a mano (spec 005 v1.1, MA-3).
- Actualizar Angular de versión mayor exige revisar este ADR.
