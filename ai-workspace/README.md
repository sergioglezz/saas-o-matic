# ai-workspace: cómo se construyó SaaS-O-Matic

Esta carpeta documenta el proceso: qué se especificó antes de pedir código a la IA, qué se decidió y por qué, y cómo se revisó lo que la IA generó. El código está en `backend/` y `frontend/`; el [README principal](../README.md) explica cómo arrancarlo.

## Por dónde empezar

| Orden | Documento | Qué contiene |
| --- | --- | --- |
| 1 | [Constitución](docs/constitution.md) | Seis principios que valen para todo el proyecto. Se lee en un minuto |
| 2 | [00-spec-first](specs/00-spec-first.md) | El enunciado analizado: casos de uso, reglas de negocio (RN-x) con sus casos de prueba, contrato de la API, modelo de datos y los 13 supuestos que el enunciado deja abiertos |
| 3 | Una spec completa, por ejemplo la [003](specs/003-customers/spec.md) | Cómo se baja una funcionalidad a requisitos, plan y tareas |
| 4 | [Log de revisión](ai-review-log.md) | 54 fallos reales en lo que generó la IA: cómo se detectaron y cómo se corrigieron |
| 5 | [Prompts clave](prompts.md) | Los prompts que guiaron cada fase, de la constitución a la revisión independiente y la última corrección del autor (P-18) |
| — | [ADR](architecture/adr/) | Las 11 decisiones de arquitectura, una por archivo |

Las reglas permanentes para la IA están en [`AGENTS.md`](../AGENTS.md), en la raíz; `CLAUDE.md` lo importa para que Claude Code las cargue en cada sesión.

## Cómo se trabajó

Cada funcionalidad siguió el mismo ciclo:

1. **Spec:** qué y por qué, sin detalles de implementación. Requisitos (RF) con criterios de aceptación (CA) en notación EARS y una tabla de casos de prueba con los valores límite. La IA pregunta las ambigüedades de una en una, con opciones, y el autor decide.
2. **Revisión de la spec** antes de aprobarla: qué es ambiguo, qué se contradice y qué no se puede probar. En la spec 001 salieron 38 problemas.
3. **Plan:** módulos, modelo de datos, pseudocódigo, decisiones técnicas con su alternativa descartada y una tabla RF → plan → tests. Cuando el plan dependía del comportamiento de una biblioteca, antes se comprobaba con un prototipo desechable.
4. **Tareas:** pequeñas y en orden, cada una con sus RF y un «Hecho cuando» que se puede comprobar.
5. **Tests primero:** salen de las tablas de la spec y se ve que fallan antes de escribir el código. Al cerrar cada fase se pasan la suite completa, el lint y los tipos.
6. **Cierre:** cada CA con un test que lo cita y pasa, el checklist de la spec marcado y la revisión del autor. En las specs 001 a 005, además, instalación desde cero en una copia limpia. Los fallos encontrados van al log.

Todo queda enlazado. Una regla de negocio (RN-4, país sin tasa) da lugar a un requisito (001 RF-4), con su criterio (CA-4.6) y su caso de prueba (X-4). El test cita en su docstring el caso y el criterio que comprueba, y el commit cita el requisito y la tarea: `feat: quote service (001 RF-3, RF-4, RF-13, T-10)`.

## Specs

Cada carpeta tiene `spec.md` (qué), `plan.md` (cómo) y `tasks.md` (pasos; en 001 a 004, con el commit de cada tarea).

| Spec | Qué cubre | CA |
| --- | --- | --- |
| [001](specs/001-pricing-and-tax/spec.md) | Precio por tramos, impuesto por país y tabla de tasas, como dominio puro | 29 |
| [002](specs/002-pricing-quote-api/spec.md) | `POST /pricing/quote`, formato único de error y CORS | 33 |
| [003](specs/003-customers/spec.md) | Clientes: alta con validación de DNI, NIE y CIF, búsqueda, ficha y datos de demostración | 56 |
| [004](specs/004-simulations/spec.md) | Simulaciones: guardado con una instantánea del cálculo e historial | 43 |
| [005](specs/005-frontend/spec.md) | Dashboard en Angular: listado, alta, ficha, simulador en tiempo real y divisas | 117 |
| [006](specs/006-modern-ui/spec.md) | Interfaz moderna: Tailwind CSS, disposición y animaciones | 25 |
| [007](specs/007-delete-customer/spec.md) | Borrar un cliente con todo su historial | 17 |
| [008](specs/008-currency-decimals/spec.md) | Importes en yenes sin decimales: cada divisa con los suyos | 5 |

Las specs 006, 007 y 008 no estaban en el plan inicial. Salieron de usar la aplicación terminada (prompts P-15, P-16 y P-18) y siguieron el mismo proceso. Hoy la suite tiene 1071 tests en el backend y 378 en el frontend.

## Decisiones de arquitectura

| ADR | Decisión |
| --- | --- |
| [0001](architecture/adr/0001-python-fastapi-angular.md) | Backend en Python con FastAPI y frontend en Angular |
| [0002](architecture/adr/0002-importes-en-centimos.md) | Importes en céntimos enteros y tasas en puntos básicos, nunca `float` |
| [0003](architecture/adr/0003-capas-con-dominio-puro.md) | Backend en capas con un dominio puro, vigilado por un test |
| [0004](architecture/adr/0004-cotizacion-en-backend.md) | El backend calcula todos los importes, también la cotización en vivo |
| [0005](architecture/adr/0005-conversion-de-divisa-en-frontend.md) | La conversión de divisa solo en el frontend, con caché y vuelta a EUR |
| [0006](architecture/adr/0006-tasas-de-impuesto-en-tabla.md) | Tasas de impuesto en una tabla, no en el código |
| [0007](architecture/adr/0007-sin-autenticacion.md) | Sin autenticación ni roles |
| [0008](architecture/adr/0008-mypy.md) | Comprobación de tipos con mypy |
| [0009](architecture/adr/0009-control-del-identificador-fiscal.md) | Algoritmo de control del identificador fiscal español |
| [0010](architecture/adr/0010-herramientas-del-frontend.md) | Angular 22, Node 26 y angular-eslint con reglas de capas |
| [0011](architecture/adr/0011-tailwind-css.md) | Tailwind CSS para el diseño |

## Cómo se usó la IA

- **Asistente:** Claude Code, con las reglas de `AGENTS.md` en cada sesión.
- **La IA propone y el autor decide.** Las dudas se resuelven con preguntas de una en una, con opciones y una recomendación, y cada fase termina con una parada para que el autor revise y apruebe (P-02, P-14).
- **Trabaja contra los documentos, no de memoria.** Cada prompt dice qué leer, qué no tocar y cuándo parar.
- **Tiene que demostrar, no afirmar.** Para cerrar una spec, la IA dice qué test cubre cada requisito y con qué resultado (P-11). Así apareció un criterio que se daba por cubierto sin ningún test (entrada 11 del log).
- **Una revisión independiente al final.** Una sesión sin historial previo auditó el proyecto entero en un clon limpio, ejecutándolo todo (P-17); lo que encontró está en las entradas 50 a 53 del log.
- **El autor corrige a la IA.** Al usar la aplicación terminada, el autor vio que los yenes salían con decimales («27.319,14 JPY»). No era un fallo del código, sino una decisión que la IA había tomado en la spec 005 sin preguntarla, y los tests la daban por buena. El autor la corrigió (P-18), y la corrección entró como la spec 008, con tests primero y una nota en cada documento que la cambiaba (entrada 54 del log).

## Glosario de identificadores

Cada identificador vale dentro de su documento: «P-1» es un caso de prueba en la spec 001 y una respuesta del autor en la 005. Para citar uno desde fuera se antepone la spec: «003 CA-6.3».

| ID | Qué es | Dónde |
| --- | --- | --- |
| [E] / [P] | Lo exige el enunciado / es una propuesta o una decisión propia | 00 y specs |
| UC-x, RN-x | Caso de uso y regla de negocio | 00, §2 y §7 |
| RF-x, CA-x.y, RNF-x | Requisito funcional, criterio de aceptación y requisito no funcional | Cada spec |
| D-x | Decisión tomada al redactar una spec | Sección de decisiones de cada spec |
| P-1 a P-5 | Preguntas previas que respondió el autor (specs 005 y 007) o petición del autor (spec 008) | Sección de decisiones de esa spec |
| DT-x | Decisión técnica | Cada plan |
| T-01, T-02… | Tareas | Cada `tasks.md` |
| P-4, T-7, Q-20, TI-3, SV-12… | Casos de prueba: el prefijo indica la tabla | Sección de casos de cada spec |
| U, D, I, C, M | Nivel del caso: unitario, con base de datos, por HTTP, de pantalla o comprobación manual | Sección de casos de cada spec |
| T-CON, T6-CLI, T7-OK… | Textos de la interfaz | Specs 005 a 007 |
| P-01 a P-18 | Prompts | [`prompts.md`](prompts.md) |
| Entrada n | Fallo anotado en el log | [`ai-review-log.md`](ai-review-log.md) |
