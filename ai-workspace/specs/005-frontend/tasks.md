# Tareas — 005 Frontend

Estado: v1.0, pendiente de la revisión del autor junto con la spec y el plan · Spec: `spec.md` v1.1 · Plan: `plan.md` v1.0

## Reglas de ejecución

- **Orden y tamaño:** una tarea cada vez, en orden. No se empieza la siguiente hasta cumplir su «Hecho cuando».
- **Ciclo rojo → verde → revisar:**
  1. Se escriben los tests a partir de las tablas de la spec.
  2. Se confirma que fallan por el motivo esperado.
  3. Se implementa lo mínimo para que pasen.
  4. Se pasa la verificación completa.
- **Verificación completa** (desde `frontend/`): tests en una sola pasada, `npm run lint` y la compilación de producción, todo sin errores ni avisos nuevos.
- **Backend:** no se toca. Su suite (`pytest`, `ruff`, `mypy`) se ejecuta en T-17 para confirmarlo.
- **Tamaño:** ningún archivo supera las 300 líneas ni ninguna función las 40 (`AGENTS.md`).
- **Commits:** ninguno sin la autorización del autor (`AGENTS.md`). Si los autoriza, uno por tarea, con el prefijo de `AGENTS.md` y los RF/CA que cubre.
- **Revisión por fases:** al cerrar cada fase se revisa contra la spec y el plan y se anota el estado en la tabla de progreso. Al final, T-17 revisa todas las tareas juntas.
- **Dudas y correcciones:** lo que no resuelvan la spec ni el plan se pregunta al autor. Las correcciones al código generado se presentan al autor para el log (`AGENTS.md`).
- **Casos de la spec:** CV (formato), VE (reglas puras), TC (tasas), DV (divisa), LI (listado), CM («Cargar más»), AL (alta), FI (ficha), HI (historial), SM (entradas), CO (cotización), GU (guardar), ER (errores) y MA (manuales). U = sin pantalla ni red; C = pantalla o servicio con peticiones falsas; M = navegador real.

## Progreso

| Fase | Tareas | RF | Estado |
| --- | --- | --- | --- |
| 1 — Base | T-01 | Soporte de todos | ✅ Completada: Node 26.13.1 LTS (ADR 0010 ajustado), Angular 22.2 sin SSR ni zona, angular-eslint 22.7; `npm test` (una pasada), `npm run lint` y la compilación de producción en verde; el lint falla con `any`, `HttpClient` fuera de `core/`, Angular o RxJS en un módulo puro y una función de 44 líneas (comprobado y revertido); `npm start` sirve en `http://localhost:4200`. El prototipo confirmó el plan salvo tres ajustes anotados en la sección 10: la biblioteca ES2023 en `tsconfig.json`, `watch: false` y los archivos de test fuera de la compilación. DT-12 precisa de dónde se lee T-REG |
| 2 — Núcleo | T-02 a T-05 | RF-2 a RF-5, RF-11 (reglas) | ✅ Completada: 150 tests (148 nuevos) en verde, lint y compilación de producción sin errores ni avisos. Cada tarea empezó en rojo con esbozos que fallaban con «pendiente». Cubiertos CV-1 a CV-23, VE-1 a VE-11, TC-1 a TC-12, TC-14, TC-15, DV-1, DV-6 a DV-11, y ER-1 y ER-2 en el nivel de servicio. Revisión de la fase: un fallo propio corregido en el prototipo de T-01 (un cambio hecho dentro de un temporizador no se pinta hasta el siguiente fotograma; los tests llaman a `TestBed.tick()`), dos errores en mis tests (`match` retira las peticiones y compara la URL con sus parámetros) y una diferencia del plan con la spec corregida en el plan: el navegador guarda los cinco campos de 5.4, no tres (spec 5.5). Añadidos anotados en el plan §2: `decimal.ts`, `rateOf`, `EUR_DISPLAY` y las ayudas de `src/testing/`; `api-config.ts` son constantes |
| 3 — Clientes | T-06 a T-09 | RF-1, RF-6 a RF-9 | ✅ Completada: 242 tests (92 nuevos) en verde, lint y compilación de producción sin errores ni avisos; cada tarea empezó en rojo. Cubiertos FI-1 a FI-9 (la parte de la ficha), TC-13, TC-16, LI-1 a LI-19, CM-1 a CM-11, AL-1 a AL-20 y la parte visible de AL-5 y AL-18 en la ficha. Revisión de la fase: un error propio corregido (una desestructuración con una variable sin usar, que el lint rechazó). Ajustes anotados en el plan: la búsqueda cancela con `PagedList.reload` en lugar de `switchMap`, `fieldErrorsFrom` recibe los `details` y admite varios mensajes por campo, y la ficha recibe el `{id}` como `input` de la ruta. Por el límite de 300 líneas, los casos CM y los fallos del alta van en `customer-list-more.spec.ts` y `customer-form-failures.spec.ts`. Vista rápida del alta en el navegador, sin problemas |
| 4 — Simulador e historial | T-10 a T-14 | RF-4, RF-10 a RF-13 | ✅ Completada: 312 tests (70 nuevos) en verde, lint y compilación de producción sin errores ni avisos. Cubiertos HI-1 a HI-9, CM-12, SM-1 a SM-13, CO-1 a CO-16, GU-1 a GU-14, DV-2 a DV-5 y la petición de historial y cotización de FI-1. Pasaron a la primera, porque el código de una tarea anterior ya los cumplía, nueve casos CO (el flujo de la T-11), los siete de GU-10 (la regla de activación de la T-11) y los de la T-14 (la conversión de la T-05 y la T-10); se comprobaron con mutaciones. Las de GU-10 no fallaron: tres casos pasaban por la condición equivocada (el valor escrito ya era distinto del de la cotización) y se reforzaron hasta que cada mutación hizo fallar el suyo. Añadido anotado en el plan: `price-totals.ts` |
| 5 — Cierre | T-15 a T-17 | Todos | Pendiente |

## Fase 1 — Base

- [x] **T-01. Proyecto Angular, lint, arranque de los tests y prototipo**
  - **RF:** soporte de todos; ADR 0010; plan §2, DT-1, DT-2 y sección 10. **Depende de:** Node 26 LTS instalado (ADR 0010).
  - **Archivos:** `frontend/` generado por la CLI (sin git propio, sin renderizado en servidor, CSS), angular-eslint con la configuración de capas del plan §2, `src/test-setup.ts`, `src/index.html` (`lang="es"`, título) y `src/testing/spec-data.ts`.
  - **Prototipo (fuera del repositorio, desechable):** la zona del arranque llega a las fechas; el reloj falso con `debounceTime` y `timeout`; una petición cancelada por `switchMap` en el controlador de pruebas HTTP; navegación con estado en las pruebas de rutas; un botón desactivado no dispara su acción.
  - **Hecho cuando:** `npm test` (una pasada), `npm run lint` y la compilación pasan con el proyecto vacío; el lint falla con un `any` y con un import de `HttpClient` fuera de `core/` (comprobado y revertido); `npm start` sirve en `http://localhost:4200`; la sección 10 del plan está completa y el plan corregido si algo no coincidía.

## Fase 2 — Núcleo (niveles U y C)

- [x] **T-02. Formato y conversión**
  - **RF:** RF-5 (CA-5.2 a CA-5.7) y RF-3 (CA-3.10), RF-4 (CA-4.7, formato de la tasa). Plan §5 «Conversión exacta», DT-3 a DT-5 y DT-16. Casos CV-1 a CV-23. **Depende de:** T-01.
  - **Archivos:** `shared/format/money.ts`, `numbers.ts`, `dates.ts`, `format-pipes.ts` y sus `*.spec.ts`.
  - **Rojo (U):** la tabla 6.1 completa.
  - **Hecho cuando:** pasa la tabla; las funciones no importan Angular ni RxJS (lint); ninguna conversión pasa por coma flotante.

- [x] **T-03. Reglas de entrada y de tasas**
  - **RF:** RF-11 (CA-11.5, CA-11.7, CA-11.8, en reglas), RF-3 (CA-3.3, CA-3.5, CA-3.13) y RF-1 a RF-4 de soporte. Casos VE-1 a VE-11. **Depende de:** T-01.
  - **Archivos:** `features/simulator/usage-input.ts`, `core/rates/rates-snapshot.ts`, `shared/texts.ts` y sus `*.spec.ts`.
  - **Rojo (U):** la tabla 6.2 completa.
  - **Hecho cuando:** pasa la tabla y las dos funciones son puras.

- [x] **T-04. Cliente de la API y clasificación de errores**
  - **RF:** RF-2 (CA-2.1 a CA-2.4) y la tabla 5.3. Plan DT-6, DT-7 y DT-17. Casos ER-1 y ER-2 en el nivel de servicio. **Depende de:** T-01.
  - **Archivos:** `core/api/api-config.ts`, `api-models.ts`, `request-failure.ts`, `customers-api.ts`, `simulations-api.ts` y sus `*.spec.ts`.
  - **Rojo (C):** cada método pide la ruta, los parámetros y el cuerpo de la tabla 5.2 en `http://127.0.0.1:8000`; `toRequestFailure` da `connection` sin respuesta y a los 10 s, `server` con 5xx y con un 200 que no es JSON, y `not_found`, `conflict`, `validation` y `client` con 404, 409, 422 y otro 4xx, conservando `details`.
  - **Hecho cuando:** esos tests pasan y ningún cuerpo lleva importes ni tasas.

- [x] **T-05. Tasas de cambio y divisa elegida**
  - **RF:** RF-3 (CA-3.1 a CA-3.13) y RF-4 (CA-4.1, CA-4.2, CA-4.4 a CA-4.7). Plan §5 «Tasas» y «Divisa», DT-7. Casos TC-1 a TC-12, TC-14, TC-15, DV-1 y DV-6 a DV-11. **Depende de:** T-02, T-03 y T-04.
  - **Archivos:** `core/rates/browser-storage.ts`, `exchange-rates.ts`, `display-currency.ts`, `shared/ui/currency-bar.ts` y sus `*.spec.ts`.
  - **Rojo (C):** las tablas 6.3 y 6.4 en lo que no necesita la ficha, con el almacenamiento del navegador limpio en cada test y el reloj fijado en los instantes de 5.4.
  - **Hecho cuando:** esos casos pasan, con una sola petición de tasas por carga y ninguna al cambiar de divisa.

## Fase 3 — Clientes (nivel C)

- [x] **T-06. Cabecera, rutas y página no encontrada**
  - **RF:** RF-1 (CA-1.1 a CA-1.7) y RF-3 (CA-3.11, CA-3.12 entre pantallas). Plan DT-11. Casos FI-6, FI-7, FI-8 (nombre de la app), TC-13 y TC-16. **Depende de:** T-05.
  - **Archivos:** `app.ts`, `app.html`, `app.css`, `app.routes.ts`, `app.config.ts`, `shared/ui/not-found-page.ts`, `src/styles.css` y `app.spec.ts`.
  - **Rojo (C):** las direcciones de 5.1 con las pantallas aún vacías; `/` lleva a `/clientes`; las desconocidas muestran T-NFP sin peticiones al backend; la cabecera y la atribución en todas; una sola petición de tasas al recorrerlas.
  - **Hecho cuando:** esos casos pasan.

- [x] **T-07. Listado, búsqueda y «Cargar más»**
  - **RF:** RF-6 (CA-6.1 a CA-6.11), RF-7 (CA-7.1 a CA-7.7) y RF-2 (CA-2.5, CA-2.6). Plan §5 «Listas paginadas» y «Búsqueda», DT-8 y DT-9. Casos LI-1 a LI-19 y CM-1 a CM-11. **Depende de:** T-06.
  - **Archivos:** `shared/paged-list.ts`, `shared/ui/request-error.ts`, `shared/ui/load-more.ts`, `features/customers/customer-list-page.*` y sus `*.spec.ts`.
  - **Rojo (C):** las tablas 6.5 y 6.6 (salvo CM-12), con reloj falso para la espera.
  - **Hecho cuando:** esos casos pasan; LI-12 confirma que la búsqueda vieja se cancela y LI-19 que el texto se muestra literal.

- [x] **T-08. Alta de cliente**
  - **RF:** RF-8 (CA-8.1 a CA-8.15). Plan §5 «Alta», DT-12 y DT-14. Casos AL-1 a AL-20. **Depende de:** T-07.
  - **Archivos:** `features/customers/customer-form-page.*`, `customer-form-errors.ts` y sus `*.spec.ts`.
  - **Rojo (U y C):** la tabla 6.7; `fieldErrorsFrom` con los detalles de AL-7 a AL-12.
  - **Hecho cuando:** esos casos pasan y el navegador no valida nada más que obligatorios y longitudes (AL-7 y AL-8 envían).

- [x] **T-09. Ficha del cliente**
  - **RF:** RF-9 (CA-9.1 a CA-9.6). Plan §5 «Ficha», DT-12. Casos FI-1 (tarjeta), FI-2 a FI-5, FI-7 y FI-9. **Depende de:** T-08.
  - **Archivos:** `features/customers/customer-detail-page.*` y su `*.spec.ts`.
  - **Rojo (C):** la tabla 6.8 en lo que toca a la tarjeta, el 404 y los avisos; el historial y el simulador llegan en la fase 4.
  - **Hecho cuando:** esos casos pasan y un 404 no hace ninguna otra petición.

## Fase 4 — Simulador e historial (nivel C)

- [x] **T-10. Historial de simulaciones**
  - **RF:** RF-10 (CA-10.1 a CA-10.7) y RF-12 (CA-12.6, tabla de desglose). Plan DT-9 y DT-13. Casos HI-1 a HI-7, HI-9, CM-12 y FI-1 (petición del historial). **Depende de:** T-09.
  - **Archivos:** `features/customers/simulation-history.*`, `simulation-card.*`, `shared/ui/tier-table.ts` y sus `*.spec.ts`.
  - **Rojo (C):** la tabla 6.9 salvo HI-8 (divisa, en T-14), con la ficha montada.
  - **Hecho cuando:** esos casos pasan y un error del historial no afecta a la tarjeta del cliente.

- [x] **T-11. Simulador: valores de entrada**
  - **RF:** RF-11 (CA-11.1 a CA-11.10). Plan DT-10 y DT-11. Casos SM-1 a SM-13. **Depende de:** T-10.
  - **Archivos:** `features/simulator/simulator.*` y `simulator-inputs.spec.ts`.
  - **Rojo (C):** la tabla 6.10, respondiendo 200 a las cotizaciones.
  - **Hecho cuando:** esos casos pasan y un valor no válido nunca sale en una petición.

- [x] **T-12. Simulador: cotización en tiempo real**
  - **RF:** RF-12 (CA-12.1 a CA-12.10). Plan §5 «Cotización», DT-8. Casos CO-1 a CO-16 y FI-1 (petición de cotización). **Depende de:** T-11.
  - **Archivos:** `features/simulator/quote-flow.ts`, `simulator.*` y `simulator-quote.spec.ts`.
  - **Rojo (C):** la tabla 6.11 con reloj falso; CO-5 comprueba que la petición vieja queda cancelada.
  - **Hecho cuando:** esos casos pasan y CO-12 confirma que se muestra el subtotal del backend.

- [x] **T-13. Guardar simulación**
  - **RF:** RF-13 (CA-13.1 a CA-13.8) y RF-10 (CA-10.8, CA-10.9). Plan §5 «Guardar», DT-13. Casos GU-1 a GU-14. **Depende de:** T-12.
  - **Archivos:** `features/simulator/simulator.*`, `features/customers/customer-detail-page.*` y `simulator-save.spec.ts`.
  - **Rojo (C):** la tabla 6.12 con la ficha completa.
  - **Hecho cuando:** esos casos pasan; GU-10 confirma los siete estados con el botón desactivado.

- [x] **T-14. Divisa en la ficha**
  - **RF:** RF-4 (CA-4.3), RF-5 (CA-5.1 a CA-5.3) y RF-12 (CA-12.10). Plan DT-15. Casos DV-2 a DV-5, HI-8, CO-15 y GU-12. **Depende de:** T-13.
  - **Archivos:** `features/customers/currency-on-detail.spec.ts` y lo que haga falta en las plantillas.
  - **Rojo (C):** cambiar de divisa con la ficha completa: importes convertidos en simulador e historial, sin ninguna petición.
  - **Hecho cuando:** esos casos pasan.

## Fase 5 — Cierre

- [ ] **T-15. Errores generales y revisión de capas**
  - **RF:** RF-2 (CA-2.2 a CA-2.4), RF-5 (CA-5.8) y RNF-1, RNF-6 y RNF-7. Casos ER-1 a ER-6 en pantalla. **Depende de:** T-14.
  - **Archivos:** `shared/api-errors.spec.ts` y lo que haga falta para que pasen.
  - **Rojo (C):** la tabla 6.13 sobre el listado; ningún cuerpo enviado en los tests de alta, cotización y guardado lleva importes ni tasas; con USD elegido, el almacenamiento del navegador solo contiene la divisa y las tasas (CA-5.8).
  - **Hecho cuando:** esos casos pasan, el lint no tiene excepciones a las reglas de capas y ningún archivo pasa de 300 líneas ni ninguna función de 40.

- [x] **T-16. Arranque real, comprobaciones manuales y documentación**
  - **RF:** criterios de finalización de la spec y RNF-2 a RNF-4, RNF-10 y RNF-11. Casos MA-1 a MA-9. **Depende de:** T-15.
  - **Archivos:** `README.md` (frontend: Node 26, instalación, arranque, dirección `http://localhost:4200`, decisiones visibles) y `AGENTS.md` (comandos del frontend confirmados).
  - **Comprobación:** backend con una base de datos nueva y el seed, frontend con `npm start`; los flujos 1 a 4 del 00 con sus errores; MA-1 a MA-9 con su resultado anotado aquí. Lo que no se pueda comprobar desde este equipo (otros navegadores, lector de pantalla) queda anotado como pendiente del autor.
  - **Hecho cuando:** los flujos funcionan de verdad y el README y `AGENTS.md` describen el frontend.
  - **Resultado (17/11/2026):** backend con una base de datos nueva fuera del repositorio (`DATABASE_URL` en la carpeta temporal de la sesión; la de `backend/` no se tocó), migrada y con el seed; frontend con `npm start`; navegador integrado de la app de escritorio (Chromium). Flujos 1 a 4 del 00 completos con sus errores: un 422 real del identificador junto a su campo y después el alta con T-REG; buscar y abrir la ficha; simular, guardar y ver la tarjeta la primera; cambiar de divisa; backend parado y vuelto a arrancar.

    | # | Ancho | Resultado |
    | --- | --- | --- |
    | MA-1 | 360 px | ✅ tras una corrección. Primero falló: la ficha medía 528 px porque las columnas implícitas de los grids crecían hasta el ancho mínimo de la tabla de tramos. Se fijaron con `minmax(0, 1fr)` y, a 480 px o menos, cada tramo se muestra como un bloque con sus etiquetas. Después, ninguna de las cuatro pantallas se desborda, tampoco en JPY ni con los desgloses abiertos |
    | MA-2 | 1280 px | ✅ ficha, simulador e historial en tarjetas; historial en dos columnas |
    | MA-3 | 1280 px | ✅ flujo 1 solo con teclado: Tab entre campos, letra inicial en los desplegables, Intro envía el alta (AL-6) y, con todo vacío, marca los cinco y lleva el foco a «Empresa». Flujo 3: Intro abre el cliente del listado (LI-17), el slider da 16, 14, 0 y 200 con flecha derecha, dos veces izquierda, Inicio y Fin (SM-10), y se guarda. «Empresa» se queda en 120 caracteres al escribir 134 (AL-17); los límites de 30 y 254 usan el mismo atributo nativo. El foco siempre se ve |
    | MA-4 | 655 px | ✅ «acme», ficha, 60 usuarios (568,70 €), guardar: la tarjeta aparece la primera; con USD, 625,92 US$ en el simulador y en la tarjeta; T-ATR visible |
    | MA-5 | — | ✅ API real: «Tasas del 17/11/2026», las 5 divisas, «1 EUR = 1,1006 USD» |
    | MA-6 | 1280 px | ✅ T-CON con «Reintentar»; tras arrancar el backend, «Reintentar» carga los 11 clientes |
    | MA-7 | — | Solo comprobado en Chromium. **Pendiente del autor:** Firefox, Edge y Safari |
    | MA-8 | — | ✅ por cálculo sobre los colores de `styles.css` (fórmula de WCAG): textos de 4,77:1 a 15,8:1; borde de los controles, 4,55:1 |
    | MA-9 | — | **Pendiente del autor** con un lector de pantalla. Los tests C comprueban que cada error está enlazado con su campo (`aria-describedby`) y que los avisos y el total están en regiones vivas |

    RNF-2: con el backend local, la cotización se ve entre 330 y 350 ms después del último cambio (300 ms de espera más la petición).

- [ ] **T-17. Revisión conjunta y cierre**
  - **RF:** todos. **Depende de:** T-16.
  - **Comprobación:** copia limpia (solo lo que entraría en un commit) con una instalación nueva: tests, lint y compilación; la suite del backend sin cambios; cada CA y cada caso U y C con un test que lo cita y pasa; los criterios de la sección 10 de la spec marcados; las correcciones al código generado listadas para el log.
  - **Hecho cuando:** todo lo anterior está en verde y el autor revisa la spec, el plan y las tareas.
