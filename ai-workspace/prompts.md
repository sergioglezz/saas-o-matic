# Prompts clave

Prompts que más influyeron en el proyecto, ordenados por las fases del Spec-Driven Development. Se copian **tal cual** se escribieron en las conversaciones con el asistente (Claude Code), con sus erratas. La excepción son P-18 y P-19: fueron mensajes muy informales, en parte dictados por voz, y se recogen redactados, con el mismo contenido y sin añadir nada. Cada uno lo indica. Los fallos que se encontraron en lo que generó la IA están en [`ai-review-log.md`](ai-review-log.md).

Patrón común a casi todos: dar el contexto y la fuente de verdad, decir qué NO hacer, fijar el formato de salida y **pedir que pare y espere la aprobación** antes de seguir.

| Fase SDD | Prompt | Resultado |
| --- | --- | --- |
| 0. Constitución | [P-01](#p-01--constitución) | [`docs/constitution.md`](docs/constitution.md) |
| 1. Especificar | [P-02](#p-02--plantilla-de-spec), [P-03](#p-03--arranque-de-una-spec-nueva) | `specs/00X-*/spec.md` |
| 2. Aclarar y revisar la spec | [P-04](#p-04--revisión-qa-de-la-spec), [P-05](#p-05--corrección-sobre-la-propuesta-de-la-ia) | Spec 001 v1.1 (38 hallazgos corregidos) |
| 3. Planificar | [P-06](#p-06--plan-técnico), [P-07](#p-07--aprobar-y-generar-el-plan) | `specs/00X-*/plan.md` |
| Decisiones (ADR) | [P-08](#p-08--adr) | [`architecture/adr/`](architecture/adr/) |
| 4. Tareas | [P-09](#p-09--tareas) | `specs/00X-*/tasks.md` |
| 5. Implementar | [P-10](#p-10--implementación-por-bloques-primera-versión), [P-11](#p-11--implementación-con-tests-primero-versión-final) | Código y tests |
| 6. Verificar y cerrar | [P-12](#p-12--verificación-de-la-spec-requisito-a-requisito), [P-13](#p-13--cierre-y-siguiente-paso) | Trazabilidad RF → test y veredicto |
| 7. Cambios con la aplicación terminada | [P-18](#p-18--interfaz-moderna), [P-19](#p-19--una-funcionalidad-que-faltaba) | Specs 006 y 007 |
| Transversal | [P-14](#p-14--cuestionar-el-razonamiento-de-la-ia) a [P-17](#p-17--prompts-cortos-de-control) | Control humano del proceso |

---

## Fase 0 · Constitución

### P-01 · Constitución

```text
Vamos a crear la constitución de un proyecto nuevo: SaaS-O-Matic, una aplicación web para que un equipo comercial simule y presupueste suscripciones SaaS multi-divisa (backend en Python con FastAPI y SQLite, frontend en Angular). Es una prueba técnica de 6 días en la que se evalúa el proceso de ingeniería con IA, así que todo el código debe poder explicarse y defenderse línea a línea.

Proponme un docs/constitution.md con 6 principios innegociables, cortos y verificables, que cubran: simplicidad del stack y del alcance, relación entre spec y código, separación entre lógica de negocio, API y base de datos, tratamiento del dinero y persistencia de datos, política de tests y revisión del código generado por IA, y calidad, seguridad e idioma del código y los mensajes. Máximo 15 líneas en total. No escribas código ni crees otros archivos. Espera mi aprobación.
```

**Por qué influyó:** fijó las reglas que se aplicaron en todas las fases siguientes. Limita el tamaño (6 principios, 15 líneas), exige que sean verificables y obliga a parar antes de aprobar. La primera versión tenía dos fallos que se corrigieron (log #1 y #2).

---

## Fase 1 · Especificar

### P-02 · Plantilla de spec

Plantilla reutilizada para cada funcionalidad, cambiando solo la línea «Funcionalidad».

```text
NO escribas código en ningún momento. Vamos a redactar la especificación de una funcionalidad de SaaS-O-Matic, una aplicación web para que un equipo comercial simule y presupueste suscripciones SaaS multi-divisa.

Lee ai-workspace/docs/constitution.md. El documento 00-spec-first.md recoge las reglas de negocio (RN-x), los casos de prueba, el contrato de API y los supuestos (sección 10): es la fuente de verdad. Lo marcado [E] viene del enunciado y no se puede contradecir; lo marcado [P] es una propuesta que puede refinarse.

Funcionalidad: <número y nombre, por ejemplo 001-pricing and-tax> Idea inicial: <una o dos frases>

Tu trabajo:
1. Hazme preguntas de UNA en UNA para eliminar las ambigüedades que sigan abiertas (casos límite, comportamiento ante errores, qué queda fuera). Máximo 6. No me preguntes lo que el documento ya resuelve. En cada pregunta ofrece 2-3 opciones y tu recomendación. Si no queda ninguna ambigüedad real, dímelo y pasa al punto 2.
2. Con mis respuestas, genera ai-workspace/specs/<número-nombre>/spec.md con esta estructura:
   - contexto y objetivo
   - usuarios
   - historias de usuario
   - requisitos funcionales numerados (RF-x), cada uno con criterios de aceptación en notación EARS en español, indicando de qué RN-x o sección del documento sale y si es [E] o [P]
   - contrato observable: solo lo que ve el exterior (entradas, salidas, códigos y formato de error), sin detalles internos
   - casos de prueba: tabla entrada → salida esperada, con valores límite
   - requisitos no funcionales
   - casos límite
   - fuera de alcance
   - criterios de finalización (checklist verificable)
   - dudas abiertas, marcadas como [NECESITA ACLARACIÓN]
3. Notación EARS: «El sistema deberá…» (siempre); «Cuando <evento>, el sistema deberá…»; «Mientras <estado>, el sistema deberá…»; «Si <condición no deseada>, entonces el sistema deberá…»; «Donde <característica opcional>, el sistema deberá…». Cada criterio debe poder convertirse en un test sin interpretación.
4. El QUÉ y el POR QUÉ. Nada de arquitectura, librerías, estructura de carpetas ni nombres de archivos de código: eso irá en el plan.
5. Cuando termines, dame un resumen de 5 líneas y espera mi revisión. No pases a la siguiente funcionalidad ni al plan, y no modifiques otros archivos.
```

**Por qué influyó:** es el prompt más importante del proyecto. Las preguntas de una en una con recomendación hacen que las decisiones las tome el autor. Los criterios EARS y la tabla de casos de prueba son de donde salen después los tests. Cada requisito queda enlazado a su regla de negocio (RN-x) y marcado como [E] o [P].

### P-03 · Arranque de una spec nueva

Versión corta usada para la spec 004, cuando el proceso ya estaba asentado en `AGENTS.md`.

```text
Lee AGENTS.md, ai-workspace/docs/constitution.md y ai-workspace/specs/00-spec-first.md. Las specs 001, 002 y 003 están completadas. Vamos con la siguiente: [simulaciones / frontend].
```

**Por qué influyó:** al tener las reglas en `AGENTS.md` y en la constitución, ya no hacía falta repetir la plantilla entera. Basta con decirle qué leer.

---

## Fase 2 · Aclarar y revisar la spec

### P-04 · Revisión QA de la spec

```text
Revisa specs/001-pricing-and-tax/spec.md como si fueras un QA muy profesional. Lista: (1) ambigüedades restantes, (2) contradicciones entre requisitos, (3) casos límite no cubiertos, (4) conflictos con docs/constitution.md. No propongas soluciones todavía: solo detecta. Formato: lista numerada.
```

**Por qué influyó:** separa encontrar los problemas de arreglarlos, así el autor ve la lista antes de decidir. Encontró 38 problemas en una spec que ya estaba aprobada (log #3). Después se pidió «arreglalo todo» y se aprobó la v1.1.

### P-05 · Corrección sobre la propuesta de la IA

```text
ya renombre la carpeta a ai-workspace, esta el archivo 00-spec-first.md, y lo del dinero arreglalo para que se almacene bien en la base de datos
```

**Por qué influyó:** la IA había propuesto `Decimal` y guardar el tipo de cambio, lo que contradecía RN-6 y RN-7. Este prompt hizo que se reescribiera el principio del dinero: céntimos enteros, puntos básicos y nada de conversión guardada (log #1).

---

## Fase 3 · Planificar

### P-06 · Plan técnico

```text
NO escribas código en ningún momento. Vamos a redactar el plan técnico de la
funcionalidad 001-pricing-and-tax de SaaS-O-Matic.

Lee, en este orden: ai-workspace/constitution/constitution.md, AGENTS.md,
ai-workspace/specs/00-spec-first.md (sobre todo las secciones 5, 7 y 8) y
ai-workspace/specs/001-pricing-and-tax/spec.md. Si encuentras contradicciones
entre estos documentos, avísame antes de planificar y espera mi respuesta.

Alcance: esta funcionalidad es el núcleo del cálculo (precio por tramos,
impuesto por país y total) y la tabla de tasas de impuesto. El endpoint
POST /pricing/quote, el guardado de simulaciones, los clientes y todo el
frontend pertenecen a otras specs: no los planifiques aquí. Describe solo la
interfaz pública del cálculo que esas specs consumirán.

Genera ai-workspace/specs/001-pricing-and-tax/plan.md con:
1. Resumen y alcance: qué RF cubre este plan y qué deja fuera.
2. Estructura de módulos: qué módulos intervienen (dominio, servicio,
   repositorio, migración y seed), la responsabilidad de cada uno y qué
   dependencias tiene permitidas según las capas de la constitución.
3. Modelo de datos: la tabla de tasas de impuesto (columnas, tipos,
   restricciones, filas de ejemplo) y cómo se representan los tramos de precio,
   con un ejemplo. Incluye la migración y el seed.
4. Interfaz pública del cálculo, en pseudocódigo: firmas, entradas, salidas y
   errores de dominio. El dominio no accede a la base de datos: el servicio
   obtiene la tasa y se la pasa.
5. Algoritmos en pseudocódigo: precio acumulativo por tramos, impuesto con
   redondeo definido y total, solo con aritmética entera. Incluye un ejemplo
   trabajado paso a paso (15 usuarios en España).
6. Decisiones técnicas, cada una con su justificación y su alternativa
   descartada, y el RF al que sirve. No reabras las decisiones ya cerradas en la
   sección 5 del documento (céntimos enteros, capas con dominio puro, tasas en
   tabla): cítalas.
7. Estrategia de tests: qué se prueba en cada capa, cómo se derivan de la tabla
   de casos de prueba de la spec (incluidos los límites 0, 10/11 y 50/51 y el
   máximo de usuarios), y en qué orden se escriben (tests primero).
8. Tabla de trazabilidad: cada RF → parte del plan que lo cubre → tests que lo
   verifican. Si algún RF no queda cubierto, dilo.
9. Cumplimiento de la constitución: una línea por principio indicando cómo lo
   respeta este plan.
10. Dudas abiertas, marcadas como [NECESITA ACLARACIÓN].

Reglas: todo debe respetar la constitución y cubrir todos los RF. Marca en cada
parte qué RF cubre. Sin código real: solo pseudocódigo y firmas. Sin dependencias
nuevas. Sé concreto y evita relleno (máximo unas 200 líneas). No generes
tasks.md ni modifiques otros archivos. Cuando termines, dame un resumen de 5
líneas y espera mi revisión.
```

**Por qué influyó:** pedir que avisara de contradicciones antes de planificar sacó a la luz que la spec 001 mezclaba el núcleo del cálculo con el endpoint. Se dividió en 001 (núcleo) y 002 (endpoint) (log #5). La tabla de trazabilidad RF → plan → tests se mantuvo en todas las specs siguientes.

### P-07 · Aprobar y generar el plan

Versión corta usada en la spec 004, una vez aprobada la spec.

```text
apruebo y realiza el plan, Todo debe respetar la constitución y cubrir todos los RF. Marca qué RF cubre cada parte.
```

---

## Decisiones de arquitectura (ADR)

### P-08 · ADR

> Este encargo **no lo escribió el autor a mano**: es el resumen que generó el asistente al abrir una sesión aparte para escribir los ADR que faltaban, después de que el autor aprobara hacerlo. Se incluye porque produjo los ADR 0001 a 0007. Se omite una línea final con una ruta local de notas.

```text
Background (from the session that started this one):
SaaS-O-Matic es una prueba técnica de Spec-Driven Development: una API FastAPI + SQLite y un dashboard Angular para que un equipo comercial presupueste suscripciones SaaS multi-divisa. El proceso se documenta en `ai-workspace/` (constitución, specs, plan, tareas, ADR y log de revisión) y pesa más que el código en la evaluación. La spec 001 (precios por tramos e impuestos) ya está implementada y publicada. La spec y el plan citan los ADR 0002, 0003, 0004 y 0006 como decisiones cerradas, pero de la serie solo existe el 0008 (mypy). El autor ha pedido que la documentación no lleve fechas. Toda la documentación va en español; el código y los identificadores, en inglés.

Task:
Escribe los siete ADR que lista la tabla «Decisiones de arquitectura» de la sección 5 de `ai-workspace/specs/00-spec-first.md`, uno por archivo, en `ai-workspace/architecture/adr/`: `0001-python-fastapi-angular.md`, `0002-importes-en-centimos.md`, `0003-capas-con-dominio-puro.md`, `0004-cotizacion-en-backend.md`, `0005-conversion-de-divisa-en-frontend.md`, `0006-tasas-de-impuesto-en-tabla.md` y `0007-sin-autenticacion.md`.

Formato: igual que el ADR existente `ai-workspace/architecture/adr/0008-mypy.md`. Título, «Estado: aceptado» **sin fecha**, Contexto, Decisión, Alternativa descartada y Consecuencias. En español y cortos (unas 15-25 líneas cada uno).

Contenido: sale de `00-spec-first.md` (secciones 5, 6, 7 y 10) y de `ai-workspace/docs/constitution.md`. No inventes decisiones nuevas ni contradigas esos documentos. Donde ya hay implementación, cítala:
- 0002: `backend/app/domain/tax.py`, céntimos y puntos básicos.
- 0003: `backend/tests/unit/test_domain_architecture.py`.
- 0006: tabla `tax_rates`, migración `backend/app/db/migrations/versions/0001_create_tax_rates.py`.

Comprueba que las referencias a «ADR 0002», «ADR 0003», «ADR 0004» y «ADR 0006» en `ai-workspace/specs/001-pricing-and-tax/` y `ai-workspace/specs/002-pricing-quote-api/` encajan con lo que escribes.

Trabajas en la misma carpeta que otra sesión: toca solo archivos dentro de `ai-workspace/architecture/adr/`, no hagas commit y no cambies de rama.

Hecho cuando: existen los 7 archivos, ninguno lleva fechas, y al terminar resumes en una tabla qué decide cada ADR y de qué sección del 00 sale.
```

---

## Fase 4 · Tareas

### P-09 · Tareas

```text
A partir de spec.md y plan.md, genera specs/002-pricing-quote-api/tasks.md:
tareas pequeñas (máx. 20-30 min cada una), en orden de dependencia, cada una
con los RF que cubre y una línea "Hecho cuando:" verificable. Usa checkboxes.

Y explícame cada una de manera simple, que lo pueda entender y verifícalas una a una
```

**Por qué influyó:** cada tarea queda enlazada a sus RF y tiene un «Hecho cuando» que se puede comprobar. Es la unidad de trabajo que se usó en toda la implementación.

---

## Fase 5 · Implementar

### P-10 · Implementación por bloques (primera versión)

Primero se avanzó tarea a tarea («Empieza T-01», «Commit y T-02»…). Luego se pasó a bloques:

```text
En la documentación de tasks que estas haciendo ahora mismo , quiero que completes las tareas por bloques que se muestran en la documentación, haz las tareas seguidas y después verifica, valida y márcala como completada. Realiza un bloque y para, tomate tu tiempo y espera la siguiente orden. Finaliza la fase en la que estas.
```

### P-11 · Implementación con tests primero (versión final)

```text
haz las tareas por bloques siguiendo la spec, el plan y lo que dice cada tarea de cada fase, después de cada fase comprueba tu propio codigo, si todo cuadra. Escribe primero los tests, luego el código y al acabar indica qué RF cubre y parate. Realiza la fase 1.
```

**Por qué influyó:** es la versión mejorada de P-10. Pide tests primero, que la IA revise su propio código, que diga qué RF cubre y que pare al final de cada fase para que el autor revise y apruebe el commit.

---

## Fase 6 · Verificar y cerrar

### P-12 · Verificación de la spec requisito a requisito

```text
Quiero que quites las fechas de la documentación de todo el proyecto antes de nada, después recorre todos los requisitos de la spec 001.
Para cada uno indica: qué test lo cubre, y el resultado de ejecutarlo. Si algún RF no está cubierto o falla, dilo claramente. Después comprueba los criterios de finalización y dame un veredicto: ¿la spec está cumplida?
```

**Por qué influyó:** no se fía de que la IA diga «terminado». Descubrió que un criterio (CA-4.2) se daba por cubierto sin que ningún test lo comprobara de verdad, y se añadió ese test (log #11).

### P-13 · Cierre y siguiente paso

```text
Mira, he vuelto a renombrar el archivo porque al final va a ser mucho más lío. Cambiar todas las referencias a ese archivo, posiblemente ponerle un dígito. Así que lo he vuelto a renombrar. Ahora quiero, al comprobar que está todo bien, todo listo y perfecto, pues quiero que hagas un commit de todas las cosas que hemos hecho de la primera spec y hagas un push ya al GitHub y dejemos ese spec primero por completado. Y quiero que analices ahora también la documentación y para ver cuál es el nuevo paso que hay que tomar para tener este proyecto a punto.
```

---

## Fase 7 · Cambios con la aplicación terminada

Con las specs 001 a 005 cerradas y publicadas, el autor usó la aplicación como lo haría un comercial y pidió dos cambios más. Ninguno se hizo tocando el código sin más: cada uno tuvo su propia spec, con su plan, sus tareas y sus tests primero.

### P-18 · Interfaz moderna

*Mensaje informal, recogido aquí redactado.*

```text
Quiero modernizar la interfaz del dashboard. Puedes usar una librería de estilos conocida si aporta algo, y añadir animaciones discretas, todo con sus tests. Corrige también lo que se ve mal: por ejemplo, el formulario de alta de cliente no está centrado. Si lo ves conveniente, abre una spec nueva y pequeña para esta mejora del frontend, e incluye lo que consideres necesario para que quede bien.
```

**Por qué influyó:** era una petición abierta, sin una librería concreta ni criterios, y se convirtió en la spec 006, con criterios que se pueden comprobar. La librería nueva (Tailwind CSS) entró con su ADR 0011, como pide el principio 1. Las animaciones también se probaron. Dos opciones de Angular se descartaron tras un prototipo: una no aplicaba sus clases en el DOM de los tests y la otra bloqueaba los tests con el reloj simulado.

### P-19 · Una funcionalidad que faltaba

Al usar la aplicación terminada, el autor echó en falta poder borrar un cliente. Lo pidió así (mensajes informales, recogidos aquí redactados):

```text
Crea una funcionalidad nueva: borrar un cliente.
```

La IA no se puso a programar. Primero preguntó qué hacer con las simulaciones del cliente, porque la base de datos impide borrar un cliente que las tiene (004 CA-7.3). El autor respondió:

```text
Sí, que se borre también su historial de simulaciones. ¿Hace falta una spec completa para un cambio así?
```

**Por qué influyó:**

- **Fue una prueba de aceptación hecha por una persona.** Ningún test podía encontrar este hueco: el documento 00 había dejado el borrado fuera de alcance, y la aplicación cumplía todo lo especificado. Solo apareció al usar la aplicación de verdad.
- **El cambio de alcance siguió el mismo proceso que el resto.** A la pregunta del autor, la IA respondió que sí hacía falta una spec, aunque fuera corta. Amplía el alcance del documento 00 (principio 1), y todo cambio de código responde a un requisito de una spec (principio 2). El resultado es la spec 007: spec, plan y 4 tareas, con los tests escritos antes que el código.
- **La decisión de negocio la tomó el autor**: borrar también el historial (decisión P-1 de la spec 007). La IA solo la planteó.
- **Escribir los tests primero destapó algo que el plan no había previsto.** Dos tests de specs anteriores, 003 ER-3 y 004 ER-10, daban por hecho que la ficha no admitía `DELETE`. Se actualizaron sin relajarlos y quedaron anotados (log #43).

Al cerrar la spec, el autor pidió dejar constancia de cómo surgió la funcionalidad. Está en el §1 de la spec 007, en el README, en el paso 5 de «Cómo se revisa» del log de revisión y en este documento.

---

## Transversal · Control humano del proceso

### P-14 · Cuestionar el razonamiento de la IA

```text
porque quieres empezar con la 003 antes de la 002? dame una motivo de tu razonamiento y que crees que es mejor seguir para cuadrar mejor el plan
```

**Por qué influyó:** la IA propuso un orden y el autor pidió que lo justificara antes de aceptarlo. Al final se siguió con la 002.

### P-15 · Delegar trabajo largo…

```text
Vale, yo me voy ya a trabajar, así que te quiero dejar un recado. Te quiero dejar que termines tú solito toda la spec 002, que hagas los commits necesarios, como hemos estado haciendo. Sin ningún problema, no hace falta que me pregunte ni nada. Hagan la comprobación de todo el spec 002 y crees el nuevo spec 003. Con el spec, con el plan, con las tasks, y te pongas a hacer las tasks, ¿vale? Como también hemos hablado muchas veces, por bloques. Hacerlo por bloques, cada task, revisarla, y después cuando termines, revisar todas las tasks juntas y todo. Ve revisando contra el proceso para que todo vaya saliendo acorde al plan. Yo ya revisaré cuando hayas terminado la spec 003. Así que ya sabes lo que hacer. Mucha suerte.
```

### P-16 · …y revisarlo después

```text
lee toda la documentacion del proyecto, ya que fable ha terminado las spec 002 y 003, pero quiero que me expliques de manera simple y que lo pueda entender toda la spec 003 y las tareas que ha realizado y si necesita algun cambio la parte del documento, y si todo esta bien haz commit y push para dejar eso cerrado
```

**Por qué influyeron (P-15 y P-16):** el autor delegó dos specs enteras, pero no las dio por buenas hasta revisarlas en otra sesión y que se las explicaran. Se publicaron después de esa revisión.

### P-17 · Prompts cortos de control

Prompts breves y repetidos que muestran cómo el autor fue aprobando y entendiendo cada paso:

- **Aprobar o frenar:** «Aprobada», «Todavía no», «Apruebo tasks.md de 001», «Confirmo, cierra».
- **Entender antes de aprobar** (la constitución pide poder defender el código línea a línea):
  - «explicame con palabras simples porque lo has dividido»
  - «para que valen pyproject.toml y requirements-dev.txt, explicalo de manera simple»
  - «explicame cada tarea muy simple que lo pueda entender facil y con analigias»
- **Avanzar con commit:** «Commit y T-02», «Sí, commits», «Sí, fase 2», «finaliza con la fase 4».
