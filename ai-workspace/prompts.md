# Prompts clave

Prompts que más influyeron en el proyecto, ordenados por las fases del Spec-Driven Development. Se recogen con el contenido con que se escribieron en las conversaciones con el asistente (Claude Code). En los mensajes más informales, algunos dictados por voz, se ha corregido la redacción (ortografía, puntuación y alguna frase) sin cambiar lo que se pedía. P-07 es la excepción, señalada en su sitio: es un encargo que redactó la propia IA. Los fallos que se encontraron en lo que generó la IA están en [`ai-review-log.md`](ai-review-log.md).

Patrón común a casi todos: dar el contexto y la fuente de verdad, decir qué NO hacer, fijar el formato de salida y **pedir que pare y espere la aprobación** antes de seguir.

| Fase SDD | Prompt | Resultado |
| --- | --- | --- |
| 0. Constitución | [P-01](#p-01--constitución) | [`docs/constitution.md`](docs/constitution.md) |
| 1. Especificar | [P-02](#p-02--plantilla-de-spec), [P-03](#p-03--arranque-de-una-spec-nueva) | `specs/00X-*/spec.md` |
| 2. Aclarar y revisar la spec | [P-04](#p-04--revisión-qa-de-la-spec) | Spec 001 v1.1 (38 hallazgos corregidos) |
| 3. Planificar | [P-05](#p-05--plan-técnico), [P-06](#p-06--aprobar-y-generar-el-plan) | `specs/00X-*/plan.md` |
| Decisiones (ADR) | [P-07](#p-07--adr) | [`architecture/adr/`](architecture/adr/) |
| 4. Tareas | [P-08](#p-08--tareas) | `specs/00X-*/tasks.md` |
| 5. Implementar | [P-09](#p-09--implementación-por-bloques-primera-versión), [P-10](#p-10--implementación-con-tests-primero-versión-final) | Código y tests |
| 6. Verificar y cerrar | [P-11](#p-11--verificación-de-la-spec-requisito-a-requisito), [P-12](#p-12--cierre-y-siguiente-paso) | Trazabilidad RF → test y veredicto |
| Transversal | [P-13](#p-13--cuestionar-el-razonamiento-de-la-ia), [P-14](#p-14--prompts-cortos-de-control) | Control humano del proceso |
| 7. Cambios con la aplicación terminada | [P-15](#p-15--interfaz-moderna), [P-16](#p-16--una-funcionalidad-que-faltaba) | Specs 006 y 007 |
| 8. Revisión independiente | [P-17](#p-17--revisión-independiente-del-proyecto) | Auditoría del proyecto entero (log #50 a #53) |
| 9. Corrección del autor | [P-18](#p-18--el-autor-corrige-a-la-ia-yenes-sin-decimales) | Spec 008 (log #54) |

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

Funcionalidad: <número y nombre, por ejemplo 001-pricing-and-tax> Idea inicial: <una o dos frases>

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

**Por qué influyó:** separa encontrar los problemas de arreglarlos, así el autor ve la lista antes de decidir. Encontró 38 problemas en una spec que ya estaba aprobada (log #3). Después se pidió «arréglalo todo» y se aprobó la v1.1.

---

## Fase 3 · Planificar

### P-05 · Plan técnico

```text
NO escribas código en ningún momento. Vamos a redactar el plan técnico de la
funcionalidad 001-pricing-and-tax de SaaS-O-Matic.

Lee, en este orden: ai-workspace/docs/constitution.md, AGENTS.md,
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

### P-06 · Aprobar y generar el plan

Versión corta usada en la spec 004, una vez aprobada la spec.

```text
Apruebo. Haz el plan: todo debe respetar la constitución y cubrir todos los RF. Marca qué RF cubre cada parte.
```

---

## Decisiones de arquitectura (ADR)

### P-07 · ADR

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

### P-08 · Tareas

```text
A partir de spec.md y plan.md, genera specs/002-pricing-quote-api/tasks.md:
tareas pequeñas (máx. 20-30 min cada una), en orden de dependencia, cada una
con los RF que cubre y una línea "Hecho cuando:" verificable. Usa checkboxes.

Explícame también cada una de forma sencilla, para que la pueda entender, y
verifícalas una a una.
```

**Por qué influyó:** cada tarea queda enlazada a sus RF y tiene un «Hecho cuando» que se puede comprobar. Es la unidad de trabajo que se usó en toda la implementación.

---

## Fase 5 · Implementar

### P-09 · Implementación por bloques (primera versión)

Primero se avanzó tarea a tarea («Empieza T-01», «Commit y T-02»…). Luego se pasó a bloques:

```text
En el tasks.md que estás haciendo, completa las tareas por los bloques que marca el documento: haz las tareas seguidas y después verifícalas, valídalas y márcalas como completadas. Haz un bloque y para; tómate tu tiempo y espera la siguiente orden. Termina la fase en la que estás.
```

### P-10 · Implementación con tests primero (versión final)

```text
Haz las tareas por bloques siguiendo la spec, el plan y lo que dice cada tarea de cada fase. Después de cada fase, revisa tu propio código y comprueba que todo cuadra. Escribe primero los tests y luego el código; al acabar, indica qué RF cubre y para. Empieza por la fase 1.
```

**Por qué influyó:** es la versión mejorada de P-09. Pide tests primero, que la IA revise su propio código, que diga qué RF cubre y que pare al final de cada fase para que el autor revise y apruebe el commit.

---

## Fase 6 · Verificar y cerrar

### P-11 · Verificación de la spec requisito a requisito

```text
Antes de nada, quita las fechas de la documentación de todo el proyecto. Después recorre todos los requisitos de la spec 001.
Para cada uno indica qué test lo cubre y el resultado de ejecutarlo. Si algún RF no está cubierto o falla, dilo claramente. Después comprueba los criterios de finalización y dame un veredicto: ¿la spec está cumplida?
```

**Por qué influyó:** no se fía de que la IA diga «terminado». Descubrió que un criterio (CA-4.2) se daba por cubierto sin que ningún test lo comprobara de verdad, y se añadió ese test (log #11).

### P-12 · Cierre y siguiente paso

```text
Cuando compruebes que todo está bien, haz un commit de todo lo que hemos hecho en la primera spec, haz push a GitHub y deja la spec 001 como completada. Después analiza la documentación para ver cuál es el siguiente paso para dejar el proyecto a punto.
```

**Por qué influyó:** fijó el cierre que se repitió en todas las specs: comprobar, publicar y solo entonces decidir el siguiente paso a partir de la documentación.

---

## Transversal · Control humano del proceso

Mensajes de las specs 001 a 005 que muestran cómo el autor mantuvo el control del proceso. Hay otro ejemplo en la fase 9: en P-18, el autor corrige una decisión que había tomado la IA.

### P-13 · Cuestionar el razonamiento de la IA

```text
¿Por qué quieres empezar con la 003 antes que con la 002? Dame el motivo de tu razonamiento y dime qué orden crees que encaja mejor con el plan.
```

**Por qué influyó:** la IA propuso un orden y el autor pidió que lo justificara antes de aceptarlo. Al final se siguió con la 002.

### P-14 · Prompts cortos de control

Prompts breves y repetidos que muestran cómo el autor fue aprobando y entendiendo cada paso:

- **Aprobar o frenar:** «Aprobada», «Todavía no», «Apruebo tasks.md de 001», «Confirmo, cierra».
- **Entender antes de aprobar** (la constitución pide poder defender el código línea a línea):
  - «Explícame con palabras sencillas por qué lo has dividido»
  - «¿Para qué sirven pyproject.toml y requirements-dev.txt? Explícalo de forma sencilla»
  - «Explícame cada tarea de forma muy sencilla, para que la entienda fácilmente, con analogías»
- **Avanzar con commit:** «Commit y T-02», «Sí, commits», «Sí, fase 2», «Termina la fase 4».

---

## Fase 7 · Cambios con la aplicación terminada

Con las specs 001 a 005 cerradas y publicadas, el autor usó la aplicación como lo haría un comercial y pidió dos cambios más; después de la revisión independiente llegó un tercero (P-18, fase 9). Ninguno se hizo tocando el código sin más: cada uno tuvo su propia spec, con su plan, sus tareas y sus tests primero.

### P-15 · Interfaz moderna

```text
Quiero modernizar la interfaz del dashboard. Puedes usar una librería de estilos conocida si aporta algo, y añadir animaciones discretas, todo con sus tests. Corrige también lo que se ve mal: por ejemplo, el formulario de alta de cliente no está centrado. Si lo ves conveniente, abre una spec nueva y pequeña para esta mejora del frontend, e incluye lo que consideres necesario para que quede bien.
```

**Por qué influyó:** era una petición abierta, sin una librería concreta ni criterios, y se convirtió en la spec 006, con criterios que se pueden comprobar. La librería nueva (Tailwind CSS) entró con su ADR 0011, como pide el principio 1. Las animaciones también se probaron. Dos opciones de Angular se descartaron tras un prototipo: una no aplicaba sus clases en el DOM de los tests y la otra bloqueaba los tests con el reloj simulado.

### P-16 · Una funcionalidad que faltaba

Al usar la aplicación terminada, el autor echó en falta poder borrar un cliente. Lo pidió así:

```text
Crea una funcionalidad nueva que simplemente sea borrar un cliente.
```

La IA no se puso a programar. Primero preguntó qué hacer con las simulaciones del cliente, porque la base de datos impide borrar un cliente que las tiene (004 CA-7.3). El autor respondió:

```text
Sí, que también se borre su historial. Pero ¿es necesario crear una spec entera para este cambio?
```

**Por qué influyó:**

- **Fue una prueba de aceptación hecha por una persona.** Ningún test podía encontrar este hueco: el documento 00 había dejado el borrado fuera de alcance, y la aplicación cumplía todo lo especificado. Solo apareció al usar la aplicación de verdad.
- **El cambio de alcance siguió el mismo proceso que el resto.** A la pregunta del autor, la IA respondió que sí hacía falta una spec, aunque fuera corta. Amplía el alcance del documento 00 (principio 1), y todo cambio de código responde a un requisito de una spec (principio 2). El resultado es la spec 007: spec, plan y 4 tareas, con los tests escritos antes que el código.
- **La decisión de negocio la tomó el autor**: borrar también el historial (decisión P-1 de la spec 007). La IA solo la planteó.
- **Escribir los tests primero destapó algo que el plan no había previsto.** Dos tests de specs anteriores, 003 ER-3 y 004 ER-10, daban por hecho que la ficha no admitía `DELETE`. Se actualizaron sin relajarlos y quedaron anotados (log #43).

---

## Fase 8 · Revisión independiente

### P-17 · Revisión independiente del proyecto

Con todo terminado, el autor abrió una sesión nueva, sin historial, para auditar el proyecto antes de entregarlo.

```text
Actúa como revisor independiente y senior. No has escrito este código y no tienes
historial previo. Tu trabajo es auditar el proyecto SaaS-O-Matic completo y decirme,
con evidencia, si está listo para entregarse como prueba técnica. NO modifiques
ningún archivo, no hagas commits y no corrijas nada: solo informa.

Contexto: aplicación web para que un equipo comercial simule y presupueste
suscripciones SaaS multi-divisa (backend Python/FastAPI + SQLite, frontend
Angular). Se evalúa así: planificación y diseño 35 %, criterio técnico y control de
calidad 25 %, calidad del software 30 %, README y despliegue 10 %. Prioriza los
hallazgos según cuánto afectan a esos cuatro criterios.

Lee primero, en este orden: ai-workspace/docs/constitution.md, AGENTS.md,
ai-workspace/specs/00-spec-first.md y, por cada funcionalidad, su spec.md, plan.md
y tasks.md. Son la fuente de verdad contra la que revisas el código.

Método: verifica ejecutando, no suponiendo. Trabaja en una copia limpia del
repositorio (un clon en un directorio temporal) para no ensuciar el original.
Ejecuta tests, lint, migraciones, seed y el arranque de backend y frontend. Si algo
no puedes ejecutarlo o comprobarlo, dilo y no lo des por bueno.

Revisa estas áreas:
1. Corrección frente a la spec: reglas RN-1 a RN-11 y todas las tablas de casos de
   prueba (precio por tramos, impuestos, identificadores fiscales). Comprueba los
   límites (0, 10/11, 50/51, máximo de usuarios) y ejemplos como 60 usuarios = 470 €
   y 15 usuarios en España = 169,40 €. Comprueba que K/L/M se rechazan.
2. Dinero: busca cualquier uso de float, Decimal, round() o divisiones con importes.
   Debe haber céntimos enteros (*_cents) y puntos básicos (*_bp). La conversión de
   divisa solo en el frontend y nunca se guarda.
3. API: endpoints y códigos (201, 422, 409, 404), formato de error uniforme, que el
   cliente nunca envíe importes, unicidad del identificador fiscal normalizado.
4. Base de datos: claves foráneas activadas, restricciones, migraciones desde cero,
   seed repetible, datos de demostración ficticios.
5. Seguridad: SQL parametrizado, validación de entrada, CORS, secretos (incluye el
   historial de git), fuga de detalles internos en errores, dependencias.
6. Arquitectura y calidad: imports que rompen las capas, archivos de más de 300
   líneas, funciones de más de 40, tipado incompleto, código muerto, TODOs.
7. Frontend: HTTP solo desde servicios, estados de carga, error y vacío en cada
   pantalla, caché y vuelta a EUR si falla la API de divisas, atribución «Rates By
   Exchange Rate API», espera (debounce) del slider, uso a 360 px de ancho, accesibilidad
   básica, TypeScript estricto sin any, sin URLs ni tasas fijadas en el código.
8. Tests: ejecútalos todos, busca tests omitidos o relajados y criterios de
   aceptación de las specs sin test.
9. README: síguelo paso a paso desde un clon limpio. Anota cada paso que falle o
   falte (versiones, .env.example, orden de comandos) y el tiempo hasta ver la app.
10. ai-workspace: constitución, AGENTS.md, specs, planes y tareas coherentes entre
    sí y con el código; ADRs existentes; prompts guardados; ai-review-log con entradas
    reales; resumen del proceso en su README; contradicciones entre documentos.
11. Higiene del repositorio: .gitignore, que no se hayan subido .env, .db,
    node_modules, .venv ni el enunciado original de la prueba. Historial de git: specs
    antes que código, commits pequeños y con prefijos.

Formato de respuesta:
- Veredicto en 5 líneas: listo, casi listo o no listo, y por qué.
- Tabla de hallazgos con ID, gravedad (bloqueante, alta, media o baja), área,
  archivo:línea, qué pasa, evidencia (comando y salida) y arreglo propuesto.
- Checklist de las 11 áreas con APRUEBA, FALLA o NO VERIFICADO.
- Los 5 arreglos más importantes antes de entregar, en orden.
- Hallazgos que podrían ir al ai-review-log.md (solo los reales).
- Qué no pudiste verificar y por qué.

Reglas: no inventes hallazgos; cada uno debe poder reproducirse. Si dudas, márcalo
como «a verificar». Distingue defectos reales de preferencias de estilo. No me pidas
permiso para leer archivos ni para ejecutar tests dentro de la copia temporal.
```

**Por qué influyó:** es la revisión independiente que pedía el documento 00 (§9), hecha por una sesión que no había escrito nada del proyecto. Prohibir tocar archivos y exigir evidencia ejecutada evitó que la IA diera nada por supuesto: clonó el repositorio en una carpeta temporal, pasó tests, lint, migraciones y seed, probó la API por HTTP y la aplicación en un navegador a 360 px. Confirmó lo que se cumplía, encontró cuatro fallos reales que se corrigieron después con la aprobación del autor (log #50 a #53) y avisó de que la revisión de la documentación seguía sin commit.

---

## Fase 9 · Corrección del autor

### P-18 · El autor corrige a la IA: yenes sin decimales

Después de la revisión independiente, el autor usó la aplicación con la divisa en yenes y vio importes como «27.319,14 JPY». El yen no tiene céntimos, así que ese precio no existe en la realidad. No era un fallo del código: era una decisión que la IA había tomado en la spec 005 (D-8). El autor la corrigió así:

```text
Tengo que corregirte una cosa. Al cambiar la divisa a yenes, los importes aparecen con decimales, pero el yen no tiene decimales. Corrígelo para que se muestren sin ellos y lo más parecido a la realidad, ya sea redondeando el importe o, directamente, ocultando los decimales en la conversión. Y documenta el cambio.
```

La IA hizo el cambio con una spec nueva, la 008, y no tocó los documentos aprobados que fijaban los 2 decimales en yenes (el 00, la spec 005 y el ADR 0005), porque `AGENTS.md` pide proponer esos cambios y esperar la aprobación. El autor revisó el resultado y respondió:

```text
Doy por bueno el cambio. Documenta también la corrección en todos los documentos que hablaban de los 2 decimales en yenes, para que no quede ningún hueco, y recoge esta corrección en prompts.md.
```

**Por qué influyó:**

- **El autor corrigió a la IA.** La spec 005 había decidido mostrar 2 decimales también en yenes por seguir al pie de la letra RN-7 («redondeado a 2 decimales»), y lo dejó escrito en D-8. Los tests comprobaban justo eso, así que pasaban: solo una persona mirando la pantalla podía ver que «27.319,14 JPY» no se parece a ningún precio real. Ninguna suite de tests detecta este tipo de error (log #54).
- **La corrección siguió el mismo proceso que el resto.** Primero la spec 008, con los criterios de la 005 que sustituye y cómo se lee RN-7 desde entonces; después los tests, vistos en rojo antes de cambiar el código; y al final una comprobación en un navegador real. Los documentos aprobados solo se tocaron cuando el autor lo aprobó: una nota en cada punto afectado del 00, la spec 005, su plan y el ADR 0005, y una fila en el historial de cambios de la spec 005 (log #53).
- **La IA decidió lo que el autor dejó abierto, y explicó por qué.** Entre redondear y ocultar los decimales, eligió redondear «mitad hacia arriba» una sola vez sobre el valor exacto, la misma regla que el resto de importes (008 D-1 y D-2). El caso que distingue los dos redondeos (YN-5) apareció también en la aplicación real, con la tasa del día: 56.090,496 yenes se muestran como 56.090, no como 56.091.
