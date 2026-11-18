# Spec-First — SaaS-O-Matic

## 1. Visión del producto

SaaS-O-Matic es una herramienta interna con la que el equipo comercial simula, optimiza y presupuesta suscripciones SaaS multi-divisa para clientes corporativos. Un comercial calcula en segundos cuánto pagaría un cliente al mes según su número de usuarios, guarda la simulación y la ve en la divisa que prefiera.

- **Qué es:** prueba técnica de Spec-Driven Development. Se entrega una API REST con base de datos y un dashboard web que se comunican entre sí.
- **Repositorio:** `saas-o-matic`, con una carpeta `ai-workspace/` en la raíz que documenta el proceso.

Este documento es la fuente de verdad de todas las specs: cada una concreta una parte de él. Leyenda: **[Enunciado]** o **[E]** es lo que dice la prueba; **[Propuesta]** o **[P]** es una decisión que el enunciado no fija.

## 2. Usuarios y casos de uso

Hay un único tipo de usuario: el comercial de Roams, que presupuesta suscripciones para clientes corporativos. **[Enunciado]** habla solo de «nuestro equipo comercial»; no menciona roles, login ni permisos.

**[Propuesta]** Sin autenticación ni roles: todo usuario que abre la app puede hacer todo. Se documenta como decisión de alcance en un ADR y en el README.

**Las 3 acciones principales del comercial**

1. Registrar un cliente corporativo.
2. Simular el consumo de un cliente y ver su factura mensual con tramos e impuestos.
3. Consultar clientes y su historial de simulaciones, en la divisa que quiera.

**Casos de uso**

| ID | Caso de uso | Resultado esperado |
| --- | --- | --- |
| UC-1 | Registrar un cliente | El cliente queda guardado; si es de España, su identificador fiscal se valida con el algoritmo oficial |
| UC-2 | Buscar un cliente por nombre de empresa o identificador fiscal | Lista de coincidencias en el dashboard |
| UC-3 | Abrir la ficha de un cliente | Ver sus datos y el historial de simulaciones guardadas |
| UC-4 | Ajustar usuarios con un slider | Proyección de la factura mensual en tiempo real, con desglose por tramo |
| UC-5 | Guardar una simulación | Queda persistida con usuarios, almacenamiento, llamadas API y coste calculado |
| UC-6 | Cambiar la divisa de visualización (EUR, USD, GBP…) | Todos los importes en pantalla se convierten al instante |

## 3. Funcionalidades

El sistema tiene cuatro módulos: clientes, simulaciones y precios, divisas y dashboard.

**Módulo de clientes**

- El usuario puede registrar un cliente con nombre de empresa, identificador fiscal (DNI/NIF/CIF), email de contacto, país y plan elegido. **[E]**
- El sistema valida de forma estricta el identificador fiscal con el algoritmo oficial de control cuando el país es España. **[E]**
- El sistema normaliza el identificador antes de validarlo (mayúsculas, sin espacios ni guiones). **[P]**
- El sistema rechaza un identificador fiscal ya registrado con un error de conflicto. **[P]**
- El sistema valida el formato del email y que los campos obligatorios no estén vacíos. **[P]**
- El usuario puede buscar clientes por nombre de empresa o por identificador fiscal. **[E]**
- El usuario puede abrir la ficha de un cliente y ver sus datos. **[E]**
- El usuario puede borrar un cliente desde su ficha, tras una confirmación, y con él se borra todo su historial de simulaciones. **[P]** Se añadió con la aplicación ya terminada, a petición del autor (spec 007).

**Módulo de simulaciones y precios**

- El usuario puede registrar una simulación para un cliente con usuarios activos, almacenamiento contratado y llamadas a la API estimadas. **[E]**
- El sistema calcula el coste mensual base con precios acumulativos por tramos y le suma el impuesto del país del cliente. **[E]**
- El sistema persiste la simulación con su cálculo: subtotal, tasa aplicada, impuesto, total y desglose por tramo. **[E]** + **[P]** para el desglose
- El usuario puede obtener una cotización en vivo sin guardarla (`POST /pricing/quote`). **[P]**
- El sistema guarda almacenamiento y llamadas API, pero no modifican el precio, porque el enunciado solo define tramos por usuario. **[P]**
- El usuario puede ver el historial de simulaciones de un cliente, de más reciente a más antigua. **[E]**

**Módulo de divisas (frontend)**

- El sistema consulta los tipos de cambio de `open.er-api.com` con EUR como base. **[E]**
- El usuario puede cambiar la divisa de visualización (EUR, USD, GBP, etc.) y ve los costes convertidos al instante. **[E]**
- El sistema guarda las tasas en caché; si la API falla, usa la última tasa guardada y avisa, o vuelve a EUR. **[P]**
- El sistema muestra la atribución «Rates By Exchange Rate API», que exige el servicio gratuito. **[P]**
- Los importes se guardan siempre en EUR; convertir es solo presentación. **[P]**
- Cada importe se muestra con los decimales de su divisa: 2 en EUR, USD, GBP y CHF, y ninguno en JPY. **[P]** Se precisó con la aplicación ya terminada, por una corrección del autor (spec 008).

**Módulo de dashboard (frontend)**

- Vista de buscador y listado de clientes. **[E]**
- Vista de detalle del cliente con tarjetas responsive y su historial de simulaciones. **[E]**
- Formulario de simulación interactiva con slider u otros controles, que proyecta la factura mensual en tiempo real y en la divisa elegida. **[E]**
- Estados de carga, error y vacío en cada pantalla que consulta datos. **[E]** para la API externa, **[P]** para el resto
- Formulario «Nuevo cliente» para registrar clientes desde la interfaz, con los errores de validación junto a cada campo. **[P]**

**Lo que hace el sistema por su cuenta**

- Publica documentación interactiva de la API (OpenAPI en `/docs`). **[P]**
- Carga datos de demostración con un script de seed para que el dashboard no esté vacío. **[P]**

**Fuera de alcance [P]:** autenticación y roles, editar clientes, generar PDF, facturación real, varios idiomas, despliegue real en AWS.

## 4. Flujos de usuario

Hay cuatro flujos principales; cada uno describe el camino feliz y qué pasa cuando algo falla. Todos los textos de error son claros y aparecen junto al elemento que falla.

**Flujo 1 — Registrar un cliente (UC-1)**

1. El usuario pulsa «Nuevo cliente» en el dashboard.
2. Rellena empresa, identificador fiscal, email, país y plan.
3. Pulsa «Guardar».
4. El sistema normaliza el identificador y, si el país es España, lo valida con el algoritmo oficial.
5. El sistema guarda el cliente y abre su ficha con un aviso de confirmación.

Errores:

- **Identificador español inválido:** respuesta 422; el mensaje sale junto al campo y el formulario conserva lo escrito.
- **Identificador ya registrado:** respuesta 409; mensaje «Ya existe un cliente con este identificador».
- **Email mal formado o campo vacío:** respuesta 422 con un error por campo.
- **La API no responde:** aviso con botón «Reintentar»; el formulario no se pierde.

**Flujo 2 — Buscar y abrir un cliente (UC-2, UC-3)**

1. El usuario entra en el dashboard y ve el buscador y el listado.
2. Escribe parte del nombre o del identificador fiscal.
3. El listado se filtra cuando deja de escribir un instante.
4. Hace clic en un cliente y abre su ficha con sus datos y su historial.

Errores:

- **Sin resultados:** mensaje «Ningún cliente coincide con …» y acceso a «Nuevo cliente».
- **API caída:** mensaje de error con «Reintentar».
- **Cliente inexistente:** respuesta 404 y pantalla «Cliente no encontrado».

**Flujo 3 — Simular y guardar (UC-4, UC-5)**

1. En la ficha del cliente, el usuario usa el simulador.
2. Mueve el slider de usuarios (o escribe el número) e indica almacenamiento y llamadas a la API.
3. En cada cambio, la pantalla pide una cotización al backend y muestra desglose por tramo, subtotal, impuesto y total.
4. Pulsa «Guardar simulación».
5. El sistema la persiste y la añade arriba del historial del cliente.

Errores:

- **Valor no válido (negativo, decimal, vacío):** el formulario lo marca junto al campo y no lo envía; si llegara al backend, respondería 422.
- **Falla la cotización:** se mantiene el último resultado y aparece «No se pudo actualizar».
- **Falla el guardado:** aviso con «Reintentar»; el formulario conserva los valores.

**Flujo 4 — Cambiar la divisa (UC-6)**

1. Al cargar la app, el sistema pide los tipos de cambio con EUR como base, o reutiliza los guardados si siguen vigentes.
2. El usuario abre el selector de divisa y elige una, por ejemplo USD.
3. Todos los importes visibles (fichas, historial, simulador) se recalculan con esa tasa.
4. La app recuerda la elección en el navegador.

Errores:

- **Mientras carga:** el selector aparece desactivado con un indicador y los importes se muestran en EUR.
- **La API falla (red, 429 o `result` distinto de `success`):** se usa la última tasa guardada con el aviso «Tasas del {fecha}. No se pudieron actualizar»; sin tasas guardadas, solo EUR con aviso.
- **Divisa ausente en la respuesta:** no aparece en el selector.

## 5. Arquitectura

Es una app web con backend propio en Python (FastAPI), base de datos SQLite y un frontend Angular que consume la API y un servicio externo de tipos de cambio. El enunciado deja el stack libre; esta elección coincide con el de la oferta. **[P]** salvo SQLite y la API de divisas, que son **[E]**.

```text
Frontend Angular  <-- HTTP + JSON -->  Backend FastAPI (Python)  <-->  SQLite (4 tablas)
                                        api -> services -> (domain | repositories)
                                        domain: cálculos puros y validadores
                                        repositories: único acceso a la base de datos
Frontend Angular  <-- tasas, con caché -->  API de tipos de cambio (open.er-api.com, base EUR)
```

El frontend habla con el backend propio y con el servicio de divisas; dentro del backend, todas las dependencias apuntan hacia el dominio.

| Pieza | Tecnología | Notas |
| --- | --- | --- |
| Tipo de app | Web | Un frontend y un backend en un solo repositorio |
| Frontend | Angular 22: componentes standalone, signals, HttpClient; RxJS solo para espera (debounce) y cancelación. Estilos con Tailwind CSS (spec 006) | Responsive |
| Backend | Python 3.12+ con FastAPI | Documentación OpenAPI automática en `/docs` |
| Validación de entrada | Pydantic v2 | Toda entrada se valida en el borde de la API |
| Acceso a datos | SQLAlchemy 2 y Alembic para migraciones | Nunca SQL concatenado |
| Base de datos | SQLite **[E]** | `PRAGMA foreign_keys=ON` en cada conexión |
| Tests | pytest + httpx en backend; el runner por defecto de Angular (Vitest) en frontend | Ver sección 6 |
| API externa | `open.er-api.com/v6/latest/EUR` **[E]** | Se llama desde el frontend; ver flujo 4 |
| Autenticación | Ninguna | Decisión de alcance (ADR 0007) |
| Despliegue | Solo en local, con instrucciones en el README | Sin despliegue real |

**Capas del backend.** Las dependencias van hacia dentro: `api` → `services` → (`repositories`, `domain`). El dominio no importa FastAPI ni SQLAlchemy.

- `api`: routers FastAPI. Solo HTTP; sin lógica de negocio ni SQL.
- `services`: casos de uso que orquestan dominio y repositorios.
- `repositories`: único lugar con acceso a la base de datos.
- `domain`: funciones puras de precios por tramos, impuestos y validadores de identificador fiscal. Sin entrada/salida.
- `schemas`: modelos Pydantic de entrada y salida.
- `db`: modelos, sesión, migraciones y seed.

**Estructura de carpetas** (la final; la propuesta inicial solo cambió en los detalles)

```text
saas-o-matic/
├── AGENTS.md               # reglas permanentes para la IA (CLAUDE.md lo importa)
├── README.md
├── ai-workspace/
│   ├── README.md           # guía del proceso
│   ├── docs/constitution.md
│   ├── specs/              # este documento y una carpeta por spec: spec, plan y tareas
│   ├── architecture/adr/
│   ├── prompts.md
│   └── ai-review-log.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/            # routers, documentación OpenAPI y mapeo de errores de dominio
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── domain/         # pricing, tax, tax_id (dni, nie, cif), customers, simulations
│   │   ├── schemas/
│   │   ├── db/             # modelos, sesión, migraciones y seed
│   │   └── core/           # configuración, formato de error y reloj
│   ├── tests/              # unit, integration (con base de datos) y api (por HTTP)
│   ├── requirements.txt    # y requirements-dev.txt
│   └── .env.example
└── frontend/
    └── src/app/
        ├── core/           # cliente de la API, tasas de cambio y divisa
        ├── features/       # customers (listado, alta, ficha, historial, borrado) y simulator
        └── shared/         # formato, componentes de interfaz y textos
```

**Decisiones de arquitectura (cada una, un ADR corto)**

| ADR | Decisión | Motivo |
| --- | --- | --- |
| 0001 | Python/FastAPI + Angular | El enunciado deja libertad; coincide con el stack de la oferta |
| 0002 | Importes en céntimos enteros, nunca `float` | Evita errores de redondeo en dinero |
| 0003 | Capas con dominio puro | Evita archivos masivos y permite testear sin BD |
| 0004 | Cotización en el backend (`POST /pricing/quote`) con espera tras cada cambio del slider | Una sola fuente de verdad. Alternativa descartada: duplicar el cálculo en el cliente |
| 0005 | Conversión de divisa solo en frontend, con caché y vuelta a EUR si falla | El enunciado lo pide en la interfaz; la API limita peticiones |
| 0006 | Tasas de impuesto en una tabla por país, no en la lógica | Configurable y fácil de ampliar |
| 0007 | Sin autenticación | Fuera del alcance del enunciado |

Durante el desarrollo se añadieron cuatro más: mypy (0008), el control del identificador fiscal (0009), las herramientas del frontend (0010) y Tailwind CSS (0011). El índice completo está en [`ai-workspace/README.md`](../README.md).

## 6. Requisitos no funcionales

La prueba puntúa robustez, seguridad y mantenibilidad tanto como las funciones, así que estos requisitos se tratan como parte de la entrega. Todos son **[P]** salvo los que marca el enunciado.

- **Usuarios simultáneos:** herramienta interna para un equipo comercial, diseñada para decenas de usuarios a la vez. SQLite es suficiente y el límite se documenta en el README.
- **Datos sensibles:** identificadores fiscales y emails pueden ser datos personales. Los datos de demostración son inventados, sin secretos en el repositorio y con `.env` ignorado por git.
- **Sin conexión:** no se soporta. Única excepción: las últimas tasas de cambio guardadas se reutilizan si falla la API externa.
- **Idioma:** interfaz y mensajes de error en español. Código, nombres técnicos y commits en inglés o con prefijos estándar; README en español.
- **Seguridad:** consultas parametrizadas vía ORM, entrada validada con Pydantic, CORS limitado al origen del frontend, errores sin detalles internos y sin trazas visibles al cliente.
- **Precisión del dinero:** céntimos enteros, redondeo definido en la sección 7 y probado en los límites 10/11 y 50/51.
- **Rendimiento:** cotización por debajo de 200 ms en local (medido después: p95 de 6,3 ms, README). El slider espera 200-300 ms tras el último cambio para no saturar la API.
- **Calidad del código:** archivos de menos de 300 líneas, funciones de menos de 40, tipado completo, sin código muerto ni `TODO` sueltos. Formateo, lint y tipos automáticos (ruff, mypy y ESLint).
- **Errores de la API:** formato uniforme, con código, mensaje y detalle por campo; mapeo de excepciones de dominio a HTTP en un único punto.
- **Tests:** dominio con el 100 % de los casos de la sección 7; API con respuestas 201, 422, 409 y 404 por endpoint; frontend con pruebas del servicio de divisas y del formulario de simulación. No se persigue una cifra de cobertura.
- **Responsive y accesibilidad básica:** usable desde 360 px de ancho; etiquetas en todos los campos; slider manejable con teclado; contraste suficiente.
- **Compatibilidad:** navegadores modernos (Chrome, Firefox, Edge, Safari).
- **Arranque sin fricción [E]:** backend y frontend se levantan en pocos pasos, desde una carpeta limpia, con versiones de Python y Node indicadas y datos de demo cargables con un comando.
- **Trazabilidad:** commits pequeños con prefijos (`docs`, `feat`, `test`, `fix`, `chore`). El historial debe mostrar las specs antes que el código.

## 7. Reglas de negocio y casos de prueba

Estas reglas son la fuente de los tests: cada fila de las tablas se convierte en una prueba automática, y todas las cifras están comprobadas con código. Se numeran RN-1, RN-2… para citarlas desde las specs y los prompts.

**7.1 Precio por tramos [E]**

- **RN-1:** el coste base es acumulativo por tramos. Cada tramo cobra solo los usuarios que caen en él, como los tramos del IRPF. No es precio por volumen: con 60 usuarios el coste correcto es 470 €, no 300 €.

| Tramo | Usuarios | Precio por usuario | En céntimos |
| --- | --- | --- | --- |
| 1 | 1 a 10 (el enunciado dice «0 a 10») | 10 € | 1000 |
| 2 | 11 a 50 | 8 € | 800 |
| 3 | 51 o más | 5 € | 500 |

```latex
\text{coste base}(u) = 10 \min(u, 10) + 8 \max(\min(u, 50) - 10, 0) + 5 \max(u - 50, 0)
```

- **RN-2 [P]:** usuarios = entero mayor o igual que 0, con un máximo de 100 000. Con 0 usuarios el coste es 0 €. Un valor negativo, decimal, texto, vacío o por encima del máximo devuelve 422.

| Usuarios | Tramo 1 | Tramo 2 | Tramo 3 | Coste base |
| --- | --- | --- | --- | --- |
| 0 | 0 € | 0 € | 0 € | 0,00 € |
| 1 | 10 € | 0 € | 0 € | 10,00 € |
| 10 | 100 € | 0 € | 0 € | 100,00 € |
| 11 | 100 € | 8 € | 0 € | 108,00 € |
| 15 | 100 € | 40 € | 0 € | 140,00 € (ejemplo del enunciado) |
| 50 | 100 € | 320 € | 0 € | 420,00 € |
| 51 | 100 € | 320 € | 5 € | 425,00 € |
| 60 | 100 € | 320 € | 50 € | 470,00 € |
| 100 | 100 € | 320 € | 250 € | 670,00 € |

**7.2 Impuestos**

- **RN-3 [E]:** total = subtotal + impuesto, donde impuesto = subtotal × tasa del país del cliente.
- **RN-4 [P]:** las tasas viven en una tabla configurable por país, no en la lógica. El enunciado no da valores; se adoptan estos supuestos: ES 21 %, PT 23 %, FR 20 %, DE 19 %, IT 22 %, GB 20 %, US 0 % (sin IVA federal; el impuesto sobre ventas depende del estado y no se modela). Un país fuera de la lista devuelve 422 «País no soportado».
- **RN-5 [P]:** el impuesto se calcula en céntimos y se redondea una sola vez, con la regla «mitad hacia arriba». Con estas tasas y precios el resultado ya es exacto; la regla protege ante tasas con decimales.
- **Fuera de alcance:** IGIC de Canarias, Ceuta y Melilla, e inversión del sujeto pasivo en operaciones entre empresas de la UE. Se mencionan en el README.

| Usuarios | País | Subtotal | Tasa | Impuesto | Total |
| --- | --- | --- | --- | --- | --- |
| 0 | ES | 0,00 € | 21 % | 0,00 € | 0,00 € |
| 1 | PT | 10,00 € | 23 % | 2,30 € | 12,30 € |
| 11 | DE | 108,00 € | 19 % | 20,52 € | 128,52 € |
| 15 | ES | 140,00 € | 21 % | 29,40 € | 169,40 € |
| 15 | US | 140,00 € | 0 % | 0,00 € | 140,00 € |
| 51 | FR | 425,00 € | 20 % | 85,00 € | 510,00 € |
| 60 | ES | 470,00 € | 21 % | 98,70 € | 568,70 € |
| 100 | GB | 670,00 € | 20 % | 134,00 € | 804,00 € |

**7.3 Dinero, divisas y simulación**

- **RN-6 [P]:** los importes son céntimos enteros en dominio, API y base de datos, con campos terminados en `_cents`. La API devuelve también `currency: "EUR"`.
- **RN-7 [E]:** convertir a otra divisa es solo presentación en el frontend: importe mostrado = importe en EUR × tasa EUR→divisa, redondeado a 2 decimales al mostrarlo. Nunca se guarda. **[P]** Los 2 decimales son los céntimos de las divisas que los tienen, como las que cita el enunciado; en una divisa sin céntimos, como el yen, el importe se redondea a la unidad. Se precisó con la aplicación ya terminada, por una corrección del autor (spec 008).
- **RN-8 [P]:** cada simulación guarda una instantánea: tasa de impuesto aplicada, desglose por tramo, subtotal, impuesto y total. Así el histórico no cambia si cambian las tarifas.
- **RN-9 [P]:** almacenamiento (en GB) y llamadas a la API (por mes) son enteros mayores o iguales que 0; se guardan pero no afectan al precio. Las unidades son un supuesto (§10, supuesto 8).

**7.4 Identificador fiscal español [E]**

- **RN-10 [E]:** si el país es España, el identificador se valida con el algoritmo de control y, si no coincide, devuelve 422. Para otros países **[P]** solo se comprueba un formato básico: de 5 a 20 caracteres alfanuméricos.
- **RN-11 [P]:** antes de validar se normaliza (mayúsculas; sin espacios, guiones ni puntos) y se guarda el valor normalizado. Así la unicidad funciona aunque lo escriban distinto.

| Tipo | Formato | Cálculo del control |
| --- | --- | --- |
| DNI | 8 dígitos + letra | letra = `TRWAGMYFPDXBNJZSQVHLCKE` en la posición (número mod 23) |
| NIE | X, Y o Z + 7 dígitos + letra | se sustituye X→0, Y→1, Z→2 y se aplica el cálculo del DNI |
| CIF | letra de entidad (`ABCDEFGHJNPQRSUVW`) + 7 dígitos + control | ver pasos siguientes |

Control del CIF:

1. Suma A: los dígitos en posiciones pares de los 7 (2.º, 4.º y 6.º).
2. Suma B: los dígitos en posiciones impares (1.º, 3.º, 5.º y 7.º), cada uno multiplicado por 2 y sumando las cifras del resultado (14 pasa a 1 + 4).
3. Dígito de control = (10 − (A + B) mod 10) mod 10. Su letra equivalente es la posición de ese dígito en `JABCDEFGHI`.
4. Tipo de control según la entidad: letra para P, Q, R, S, N y W; dígito para A, B, E y H; cualquiera de los dos para el resto.

**Aviso [P]:** la AEAT no publica el método de control del CIF ni qué entidades llevan dígito o letra; el paso 4 es la convención más extendida en validadores ([LookupTax](https://lookuptax.com/docs/tax-identification-number/spain-tax-id-guide)). Se documenta en un ADR. Los NIF especiales K, L y M (menores de 14, españoles en el extranjero, extranjeros sin NIE) tampoco tienen método publicado, así que quedan fuera: se rechazan con «Tipo de identificador no soportado».

| Entrada | Resultado | Motivo |
| --- | --- | --- |
| 12345678Z | válido | DNI correcto |
| 12345678A | inválido | letra de control incorrecta |
| 1234567Z | inválido | faltan dígitos |
| 00000000T | válido | resto 0 corresponde a T |
| 12.345.678-z | válido | se normaliza a 12345678Z |
| X1234567L | válido | NIE con X |
| Y1234567X | válido | NIE con Y |
| Z1234567R | válido | NIE con Z |
| X1234567A | inválido | letra incorrecta |
| B12345674 | válido | CIF con control de dígito |
| B12345675 | inválido | control incorrecto |
| N1234567D | válido | CIF con control de letra |
| N12345674 | inválido | la entidad N exige letra |
| K1234567X | rechazado | K, L y M no soportados |

Los identificadores de esta tabla son sintéticos y sirven solo para pruebas.

## 8. Contrato de API y modelo de datos

La API es REST con JSON y su contrato fija rutas, campos y errores antes de escribir código. Los dos `POST` obligatorios **[E]** van acompañados de endpoints de lectura **[P]** que el dashboard necesita.

**8.1 Convenciones [P]**

- JSON en UTF-8, campos en `snake_case`, fechas en ISO 8601 UTC e identificadores numéricos autoincrementales.
- Importes en céntimos enteros (`*_cents`) y tasas en puntos básicos (`tax_rate_bp`: 2100 = 21 %). Nunca `float`.
- El backend calcula todos los importes: el cliente no envía nunca precios ni totales.
- Todos los errores usan un formato único (8.4).

**8.2 Endpoints**

| Método y ruta | Qué hace | Éxito | Errores | Origen |
| --- | --- | --- | --- | --- |
| `POST /customers` | Registra un cliente | 201 | 422, 409 | **[E]** |
| `GET /customers?q=&limit=&offset=` | Busca por nombre o identificador fiscal; sin `q`, lista todos (por defecto 50) | 200 | 422 | **[P]** |
| `GET /customers/{id}` | Datos de un cliente | 200 | 404 | **[P]** |
| `DELETE /customers/{id}` | Borra el cliente y todo su historial, en una transacción (spec 007) | 204 | 404 | **[P]** |
| `POST /simulations` | Calcula y guarda una simulación | 201 | 404, 422 | **[E]** |
| `GET /customers/{id}/simulations` | Historial, de más reciente a más antigua, paginado como el listado (spec 004) | 200 | 404, 422 | **[P]** |
| `POST /pricing/quote` | Cotiza sin guardar, para el slider | 200 | 422 | **[P]** |

**8.3 Ejemplos y validaciones**

`POST /customers`, petición:

```json
{
  "company_name": "Acme Telecom S.L.",
  "tax_id": "B12345674",
  "contact_email": "compras@acme.example",
  "country": "ES",
  "plan": "business"
}
```

Respuesta `201` (mismos campos, con `id` y `created_at`):

```json
{
  "id": 1,
  "company_name": "Acme Telecom S.L.",
  "tax_id": "B12345674",
  "contact_email": "compras@acme.example",
  "country": "ES",
  "plan": "business",
  "created_at": "2026-11-13T10:00:00Z"
}
```

| Campo | Regla |
| --- | --- |
| `company_name` | Texto de 1 a 120 caracteres, sin espacios sobrantes |
| `tax_id` | Obligatorio; se normaliza (RN-11); si `country` es ES, algoritmo de control (7.4); único |
| `contact_email` | Email válido de hasta 254 caracteres |
| `country` | Código ISO 3166-1 de 2 letras, de la lista soportada (RN-4) |
| `plan` | `starter`, `business` o `enterprise`; no cambia el precio **[P]** |

`GET /customers` devuelve `{ "items": [ ...clientes ], "total": 1 }`. La búsqueda ignora mayúsculas y compara con el nombre o con el identificador normalizado.

`POST /simulations`, petición:

```json
{
  "customer_id": 1,
  "active_users": 15,
  "storage_gb": 200,
  "api_calls_per_month": 50000
}
```

La respuesta `201` incluye `id`, `customer_id`, los tres datos de entrada, `created_at` y la misma instantánea de precio que `POST /pricing/quote`. Con petición `{ "country": "ES", "users": 15 }`, el quote responde:

```json
{
  "users": 15,
  "currency": "EUR",
  "tiers": [
    { "tier": 1, "from_users": 1,  "to_users": 10,   "units": 10, "unit_price_cents": 1000, "amount_cents": 10000 },
    { "tier": 2, "from_users": 11, "to_users": 50,   "units": 5,  "unit_price_cents": 800,  "amount_cents": 4000 },
    { "tier": 3, "from_users": 51, "to_users": null, "units": 0,  "unit_price_cents": 500,  "amount_cents": 0 }
  ],
  "subtotal_cents": 14000,
  "tax_rate_bp": 2100,
  "tax_cents": 2940,
  "total_cents": 16940
}
```

**8.4 Errores**

Todos los errores devuelven el mismo formato. FastAPI usa otro por defecto para 422, así que se adapta en un único manejador.

```json
{
  "error": {
    "code": "validation_error",
    "message": "Datos no válidos",
    "details": [ { "field": "tax_id", "message": "El DNI/NIF/CIF no es válido" } ]
  }
}
```

| HTTP | `code` | Cuándo |
| --- | --- | --- |
| 422 | `validation_error` | Campo inválido, identificador español inválido, país no soportado, usuarios fuera de rango |
| 409 | `conflict` | Identificador fiscal ya registrado |
| 404 | `not_found` | Cliente inexistente o ruta que no existe |
| 405 | `method_not_allowed` | Método que la ruta no admite, con la cabecera `Allow` (specs 002 y 003) |
| 500 | `internal_error` | Fallo inesperado; mensaje genérico, sin detalles internos |

**8.5 Modelo de datos (SQLite) [P]**

Un cliente tiene muchas simulaciones, y cada simulación guarda tres filas de desglose (una por tramo). Reglas generales: `PRAGMA foreign_keys=ON` en cada conexión, importes en `INTEGER` y fechas en texto ISO 8601 UTC.

**`customers`**

| Columna | Tipo | Reglas |
| --- | --- | --- |
| `id` | INTEGER | Clave primaria autoincremental |
| `company_name` | TEXT | No nulo; índice para la búsqueda |
| `tax_id` | TEXT | No nulo; **único**; guardado normalizado |
| `contact_email` | TEXT | No nulo |
| `country` | TEXT | No nulo; 2 caracteres |
| `plan` | TEXT | No nulo; `CHECK` con los tres planes |
| `created_at` | TEXT | No nulo |

**`simulations`**

| Columna | Tipo | Reglas |
| --- | --- | --- |
| `id` | INTEGER | Clave primaria autoincremental |
| `customer_id` | INTEGER | No nulo; clave foránea a `customers.id`, sin borrado en cascada |
| `active_users` | INTEGER | No nulo; `CHECK` ≥ 0 |
| `storage_gb` | INTEGER | No nulo; `CHECK` ≥ 0 |
| `api_calls_per_month` | INTEGER | No nulo; `CHECK` ≥ 0 |
| `subtotal_cents` | INTEGER | No nulo |
| `tax_rate_bp` | INTEGER | No nulo; tasa aplicada en ese momento |
| `tax_cents` | INTEGER | No nulo |
| `total_cents` | INTEGER | No nulo |
| `created_at` | TEXT | No nulo; índice con `customer_id` para el historial |

**`simulation_tiers`**: clave primaria (`simulation_id`, `tier`), con `simulation_id` como clave foránea a `simulations.id`, `tier` (1 a 3), `from_users`, `to_users`, `units`, `unit_price_cents` y `amount_cents`, todos enteros no nulos salvo `to_users`, que es nulo en el tramo abierto. Los límites del tramo los añadió la spec 004 (D-3) para que el historial no dependa de la tarifa actual.

**`tax_rates`**: `country` (TEXT, clave primaria) y `rate_bp` (INTEGER, no nulo). Se rellena con una migración; los tramos de precio viven en una única constante del dominio.

## 9. Entregables y criterios de evaluación

Se entregan tres cosas en un solo repositorio: la aplicación funcionando, la carpeta `ai-workspace/` con el proceso de ingeniería y un README que permita levantar todo en local **[E]**.

| Criterio | Peso | Qué evalúan **[E]** | Dónde se ve **[P]** |
| --- | --- | --- | --- |
| Planificación y diseño | 35 % | Especificaciones claras y pasos lógicos del sistema antes de delegar código | Este documento y las specs (reglas, contrato y casos de prueba), con su plan y sus tareas. En el historial de git, cada spec está antes que su código |
| Criterio técnico y control de calidad | 25 % | Entender y auditar el código de la IA, sin aceptar soluciones subóptimas ni deuda técnica | `ai-review-log.md` con los fallos reales y su corrección, `AGENTS.md` con las reglas para la IA y la revisión del autor al cerrar cada spec |
| Calidad del software | 30 % | Backend robusto (validaciones, tramos exactos, persistencia limpia) y frontend fluido (responsive, estados de carga y error de la API externa) | Tests derivados de las tablas de casos, validación en cada capa, datos de demostración y estados de carga, error y vacío en cada pantalla |
| README y despliegue | 10 % | Levantar backend y frontend en local en pocos pasos y sin fricción | README con arranque rápido, probado en un clon limpio |

**Contenido de `ai-workspace/` [E]** (estructura libre, tres dimensiones):

1. **Planificación y specs:** cómo se desglosaron reglas de negocio, contratos de API y validaciones antes de programar, con las specs, prompts estructurados o planes de acción usados para guiar a la IA.
2. **Arquitectura:** estructura de la base de datos, organización de carpetas y directrices dadas a la IA para que el código sea limpio, modular y sin archivos masivos.
3. **Vibe coding y control de calidad:** el desarrollo iterativo real con la IA (capturas de prompts clave, hilos de conversación o notas). La empresa usa Claude, pero se puede usar cualquier otra IA.

La guía de la carpeta, con el orden de lectura, está en [`ai-workspace/README.md`](../README.md).

## 10. Supuestos y decisiones

El enunciado deja 13 huecos. Cada uno se cierra con un supuesto propio, explicado en el README (sección «Decisiones y supuestos») y, cuando afecta a la arquitectura, en un ADR.

| # | Tema | Qué dice el enunciado | Supuesto adoptado | Dónde se documenta |
| --- | --- | --- | --- | --- |
| 1 | Almacenamiento y llamadas API | Se registran en la simulación, pero la tarifa solo define tramos por usuario | Se guardan y no cambian el precio | README |
| 2 | Planes | «Plan elegido», sin lista | `starter`, `business`, `enterprise`, sin efecto en precio | README |
| 3 | Tasas de impuesto | «Impuesto correspondiente al país», sin valores | Tabla de 7 países (7.2) | README y ADR 0006 |
| 4 | País fuera de la lista | No dice | Error 422 «País no soportado» | README |
| 5 | Identificador fuera de España | Solo exige validar el de España | Formato básico de 5 a 20 caracteres alfanuméricos | README y ADR 0009 |
| 6 | CIF y NIF especiales | «Algoritmo oficial de control» | Tipo de control por entidad según la convención más extendida; K, L y M no soportados | README y ADR 0009 |
| 7 | Cero usuarios | Tramo 1 es «0 a 10» | Se permite y cuesta 0 € | README |
| 8 | Límites y unidades | No dice | Máximo 100 000 usuarios; almacenamiento en GB; llamadas por mes | README |
| 9 | Endpoints de lectura y cotización | Solo lista dos `POST` | Añadir `GET` de clientes, historial y `POST /pricing/quote` | ADR 0004 |
| 10 | Alta de clientes en la interfaz | Las vistas obligatorias no la incluyen | Formulario «Nuevo cliente» | README |
| 11 | Autenticación | No la menciona | Sin login ni roles | README y ADR 0007 |
| 12 | Divisas ofrecidas | «EUR, USD, GBP, etc.» | EUR, USD, GBP, CHF y JPY, solo si la API las devuelve; formato con `Intl.NumberFormat`, con los decimales de cada divisa (ninguno en JPY, spec 008) | README y ADR 0005 |
| 13 | Caché de tasas | «Tiempo real» | La API actualiza una vez al día y limita peticiones; se reutilizan las tasas hasta `time_next_update_utc` | ADR 0005 |

## 11. Orden de implementación

Se construye de dentro hacia fuera: dominio, base de datos, API, frontend y cierre. Cada pieza sigue el mismo ciclo: spec, plan, tareas, tests primero, código, revisión y anotación de lo corregido **[P]**. Así quedó repartido en specs:

| Orden | Spec | Contenido |
| --- | --- | --- |
| 1 | 001 | Dominio puro (`pricing` y `tax`) y tabla `tax_rates`, a partir de las tablas de 7.1 y 7.2 |
| 2 | 002 | `POST /pricing/quote`, formato único de error y CORS |
| 3 | 003 | Clientes, con el validador `tax_id` de 7.4, y el seed de demostración |
| 4 | 004 | Simulaciones con su instantánea e historial |
| 5 | 005 | Frontend: cliente de la API, divisas, listado, alta, ficha y simulador |
| 6 | 006 y 007 | Interfaz moderna y borrado de clientes, pedidos al usar la aplicación terminada |
| 7 | 008 | Yenes sin decimales: una corrección del autor a una decisión de la spec 005, también al usar la aplicación terminada |

Los prompts que guiaron cada fase están en [`prompts.md`](../prompts.md).

## Fuentes

- Enunciado del reto técnico de Roams.
- Plantilla Spec-First, de dominicode (estructura de las secciones 1 a 6).
- [ExchangeRate-API, Open Access endpoint](https://www.exchangerate-api.com/docs/free): actualización diaria, límite de peticiones, caché permitida y atribución obligatoria.
- [LookupTax, guía de identificadores fiscales de España](https://lookuptax.com/docs/tax-identification-number/spain-tax-id-guide): DNI, NIE, CIF y NIF K/L/M.
