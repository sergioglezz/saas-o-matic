# Spec-First — SaaS-O-Matic

## 1. Visión del producto

SaaS-O-Matic es una herramienta interna con la que el equipo comercial simulada, optimiza y presupuesta suscripciones SaaS multi-divisa para clientes corporativos. Un comercial calcula en segundos cuánto pagaría un cliente al mes según su número de usuarios, guarda la simulación y la ve en la divisa que prefiera.

- **Qué es:** prueba técnica de Spec-Driven Development. Se entrega una API REST con base de datos y un dashboard web que se comunican entre sí.
- **Qué se evalúa:** planificación y diseño 35 %, criterio técnico y control de calidad 25 %, calidad del software 30 %, README y despliegue 10 %. El proceso con IA pesa más que el código.
- **Repositorio:** `saas-o-matic`, con una carpeta `ai-workspace/` en la raíz que documenta el proceso.

Leyenda de este documento: **[Enunciado]** es lo que dice la prueba; **[Propuesta]** es una decisión que el enunciado no fija y que conviene confirmar o cambiar.

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

Audiencia indirecta: los evaluadores de Roams. Clonan el repositorio, levantan el proyecto con el README y leen `ai-workspace/`. Su experiencia es parte del producto.

## 3. Funcionalidades

El sistema tiene cuatro módulos: clientes, simulaciones y precios, divisas y dashboard. En cada línea, **[E]** = lo exige el enunciado y **[P]** = propuesta para completar un hueco.

**Módulo de clientes**

- El usuario puede registrar un cliente con nombre de empresa, identificador fiscal (DNI/NIF/CIF), email de contacto, país y plan elegido. **[E]**
- El sistema valida de forma estricta el identificador fiscal con el algoritmo oficial de control cuando el país es España. **[E]**
- El sistema normaliza el identificador antes de validarlo (mayúsculas, sin espacios ni guiones). **[P]**
- El sistema rechaza un identificador fiscal ya registrado con un error de conflicto. **[P]**
- El sistema valida el formato del email y que los campos obligatorios no estén vacíos. **[P]**
- El usuario puede buscar clientes por nombre de empresa o por identificador fiscal. **[E]**
- El usuario puede abrir la ficha de un cliente y ver sus datos. **[E]**

**Módulo de simulaciones y precios**

- El usuario puede registrar una simulación para un cliente con usuarios activos, almacenamiento contratado y llamadas a la API estimadas. **[E]**
- El sistema calcula el coste mensual base con precios acumulativos por tramos y le suma el impuesto del país del cliente. **[E]**
- El sistema persiste la simulación con su cálculo: subtotal, tasa aplicada, impuesto, total y desglose por tramo. **[E]** + **[P]** para el desglose
- El usuario puede obtener una cotización en vivo sin guardarla (`POST /pricing/quote`). **[P]**
- El sistema guarda almacenamiento y llamadas API, pero no modifican el precio, porque el enunciado solo define tramos por usuario. **[P]** Pendiente de confirmar.
- El usuario puede ver el historial de simulaciones de un cliente, de más reciente a más antigua. **[E]**

**Módulo de divisas (frontend)**

- El sistema consulta los tipos de cambio de `open.er-api.com` con EUR como base. **[E]**
- El usuario puede cambiar la divisa de visualización (EUR, USD, GBP, etc.) y ve los costes convertidos al instante. **[E]**
- El sistema guarda las tasas en caché; si la API falla, usa la última tasa guardada y avisa, o vuelve a EUR. **[P]**
- El sistema muestra la atribución «Rates By Exchange Rate API», que exige el servicio gratuito. **[P]**
- Los importes se guardan siempre en EUR; convertir es solo presentación. **[P]**

**Módulo de dashboard (frontend)**

- Vista de buscador y listado de clientes. **[E]**
- Vista de detalle del cliente con tarjetas responsive y su historial de simulaciones. **[E]**
- Formulario de simulación interactiva con slider u otros controles, que proyecta la factura mensual en tiempo real y en la divisa elegida. **[E]**
- Estados de carga, error y vacío en cada pantalla que consulta datos. **[E]** para la API externa, **[P]** para el resto

* Formulario «Nuevo cliente» para registrar clientes desde la interfaz, con los errores de validación junto a cada campo. **[P]**

**Lo que hace el sistema por su cuenta**

- Publica documentación interactiva de la API (OpenAPI en `/docs`). **[P]**
- Carga datos de demostración con un script de seed para que el dashboard no esté vacío. **[P]**

**Fuera de alcance [P]:** autenticación y roles, editar o borrar clientes, generar PDF, facturación real, varios idiomas, despliegue real en AWS.

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

1. Desde la ficha del cliente, el usuario abre el simulador.
2. Mueve el slider de usuarios (o escribe el número) e indica almacenamiento y llamadas a la API.
3. En cada cambio, la pantalla pide una cotización al backend y muestra desglose por tramo, subtotal, impuesto y total.
4. Pulsa «Guardar simulación».
5. El sistema la persiste y la añade arriba del historial del cliente.

Errores:

- **Valor no válido (negativo, decimal, vacío):** el control lo impide; si llega al backend, responde 422.
- **Falla la cotización:** se mantiene el último resultado y aparece «No se pudo actualizar».
- **Falla el guardado:** aviso con «Reintentar»; el formulario conserva los valores.

**Flujo 4 — Cambiar la divisa (UC-6)**

1. Al cargar la app, el sistema pide los tipos de cambio con EUR como base, o reutiliza los guardados si siguen vigentes.
2. El usuario abre el selector de divisa y elige una, por ejemplo USD.
3. Todos los importes visibles (fichas, historial, simulador) se recalculan con esa tasa.
4. La app recuerda la elección en el navegador.

Errores:

- **Mientras carga:** el selector aparece desactivado con un indicador y los importes se muestran en EUR.
- **La API falla (red, 429 o `result` distinto de `success`):** se usa la última tasa guardada con el aviso «Tasas de [fecha]»; sin tasas guardadas, solo EUR con aviso.
- **Divisa ausente en la respuesta:** no aparece en el selector.

## 5. Arquitectura

Es una app web con backend propio en Python (FastAPI), base de datos SQLite y un frontend Angular que consume la API y un servicio externo de tipos de cambio. El enunciado deja el stack libre; esta elección coincide con el de la oferta. **[P]** salvo SQLite y la API de divisas, que son **[E]**.

```text
Frontend Angular  <-- HTTP + JSON -->  Backend FastAPI (Python)  <-->  SQLite (4 tablas)
                                        api -> services -> (domain | repositories)
                                        domain: calculos puros y validadores
                                        repositories: unico acceso a la BD
Frontend Angular  <-- tasas, con cache -->  API de tipos de cambio (open.er-api.com, base EUR)
```

El frontend habla con tu API y con el servicio de divisas; dentro del backend, todas las dependencias apuntan hacia el dominio.

| Pieza | Tecnología | Notas |
| --- | --- | --- |
| Tipo de app | Web | Un frontend y un backend en un solo repositorio |
| Frontend | Angular: componentes standalone, signals, HttpClient; RxJS solo para espera (debounce) y cancelación | Responsive |
| Backend | Python 3.12+ con FastAPI | Documentación OpenAPI automática en `/docs` |
| Validación de entrada | Pydantic v2 | Toda entrada se valida en el borde de la API |
| Acceso a datos | SQLAlchemy 2 y Alembic para migraciones | Nunca SQL concatenado |
| Base de datos | SQLite **[E]** | `PRAGMA foreign_keys=ON` en cada conexión |
| Tests | pytest + httpx en backend; el runner por defecto de Angular en frontend | Ver sección 6 |
| API externa | `open.er-api.com/v6/latest/EUR` **[E]** | Se llama desde el frontend; ver flujo 4 |
| Autenticación | Ninguna | Decisión de alcance |
| Despliegue | Solo en local, con instrucciones en el README | Nota opcional sobre AWS y Terraform al final del README |

**Capas del backend.** Las dependencias van hacia dentro: `api` → `services` → (`repositories`, `domain`). El dominio no importa FastAPI ni SQLAlchemy.

- `api`: routers FastAPI. Solo HTTP; sin lógica de negocio ni SQL.
- `services`: casos de uso que orquestan dominio y repositorios.
- `repositories`: único lugar con acceso a la base de datos.
- `domain`: funciones puras de precios por tramos, impuestos y validadores de identificador fiscal. Sin entrada/salida.
- `schemas`: modelos Pydantic de entrada y salida.
- `db`: modelos, sesión, migraciones y seed.

**Estructura de carpetas propuesta**

```text
saas-o-matic/
├── CLAUDE.md
├── README.md
├── ai-workspace/
│   ├── specs/
│   ├── architecture/adr/
│   ├── prompts/
│   └── ai-review-log.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/            # routers: customers, simulations, pricing
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── domain/         # pricing, tax, tax_id (dni, nie, cif)
│   │   ├── schemas/
│   │   ├── db/             # models, session, migrations, seed
│   │   └── core/           # config, errores
│   ├── tests/              # unit (domain) y api
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/app/
        ├── core/           # cliente de API, servicio de divisas, errores
        ├── features/       # customers (lista, detalle, formulario), simulator
        └── shared/         # componentes de UI, pipe de dinero
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

## 6. Requisitos no funcionales

La prueba puntúa robustez, seguridad y mantenibilidad tanto como las funciones, así que estos requisitos se tratan como parte de la entrega. Todos son **[P]** salvo los que marca el enunciado.

- **Usuarios simultáneos:** herramienta interna para un equipo comercial, diseñada para decenas de usuarios a la vez. SQLite es suficiente y el límite se documenta en el README.
- **Datos sensibles:** identificadores fiscales y emails pueden ser datos personales. Los datos de demostración son inventados, sin secretos en el repositorio y con `.env` ignorado por git.
- **Sin conexión:** no se soporta. Única excepción: las últimas tasas de cambio guardadas se reutilizan si falla la API externa.
- **Idioma:** interfaz y mensajes de error en español. Código, nombres técnicos y commits en inglés o con prefijos estándar; README en español.
- **Seguridad:** consultas parametrizadas vía ORM, entrada validada con Pydantic, CORS limitado al origen del frontend, errores sin detalles internos y sin trazas visibles al cliente.
- **Precisión del dinero:** céntimos enteros, redondeo definido en la sección 7 y probado en los límites 10/11 y 50/51.
- **Rendimiento:** cotización por debajo de 200 ms en local (objetivo, no medición). El slider espera 200-300 ms tras el último cambio para no saturar la API.
- **Calidad del código:** archivos de menos de 300 líneas, funciones de menos de 40, tipado completo, sin código muerto ni `TODO` sueltos. Formateo y lint automáticos (por ejemplo ruff y ESLint).
- **Errores de la API:** formato uniforme, con código, mensaje y detalle por campo; mapeo de excepciones de dominio a HTTP en un único punto.
- **Tests:** dominio con el 100 % de los casos de la sección 7; API con respuestas 201, 422, 409 y 404 por endpoint; frontend con pruebas del servicio de divisas y del formulario de simulación. No se persigue una cifra de cobertura.
- **Responsive y accesibilidad básica:** usable desde 360 px de ancho; etiquetas en todos los campos; slider manejable con teclado; contraste suficiente.
- **Compatibilidad:** navegadores modernos (Chrome, Firefox, Edge, Safari).
- **Arranque sin fricción (README, 10 % de la nota) [E]:** backend y frontend se levantan en pocos pasos, desde una carpeta limpia, con versiones de Python y Node indicadas y datos de demo cargables con un comando.
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
- **RN-4 [P]:** las tasas viven en una tabla configurable por país, no en la lógica. El enunciado no da valores; estos son supuestos de ejemplo a confirmar: ES 21 %, PT 23 %, FR 20 %, DE 19 %, IT 22 %, GB 20 %, US 0 % (sin IVA federal; el impuesto sobre ventas depende del estado y no se modela). Un país fuera de la lista devuelve 422 «País no soportado».
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
- **RN-7 [E]:** convertir a otra divisa es solo presentación en el frontend: importe mostrado = importe en EUR × tasa EUR→divisa, redondeado a 2 decimales al mostrarlo. Nunca se guarda.
- **RN-8 [P]:** cada simulación guarda una instantánea: tasa de impuesto aplicada, desglose por tramo, subtotal, impuesto y total. Así el histórico no cambia si cambian las tarifas.
- **RN-9 [P]:** almacenamiento (en GB) y llamadas a la API (por mes) son enteros mayores o iguales que 0; se guardan pero no afectan al precio. Las unidades son un supuesto a confirmar.

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
| `POST /simulations` | Calcula y guarda una simulación | 201 | 404, 422 | **[E]** |
| `GET /customers/{id}/simulations` | Historial, de más reciente a más antigua | 200 | 404 | **[P]** |
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
| 404 | `not_found` | Cliente inexistente |
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
| `customer_id` | INTEGER | No nulo; clave foránea a `customers.id` |
| `active_users` | INTEGER | No nulo; `CHECK` ≥ 0 |
| `storage_gb` | INTEGER | No nulo; `CHECK` ≥ 0 |
| `api_calls_per_month` | INTEGER | No nulo; `CHECK` ≥ 0 |
| `subtotal_cents` | INTEGER | No nulo |
| `tax_rate_bp` | INTEGER | No nulo; tasa aplicada en ese momento |
| `tax_cents` | INTEGER | No nulo |
| `total_cents` | INTEGER | No nulo |
| `created_at` | TEXT | No nulo; índice con `customer_id` para el historial |

**`simulation_tiers`**: clave primaria (`simulation_id`, `tier`), con `simulation_id` como clave foránea a `simulations.id`, `tier` (1 a 3), `units`, `unit_price_cents` y `amount_cents`, todos enteros no nulos.

**`tax_rates`**: `country` (TEXT, clave primaria) y `rate_bp` (INTEGER, no nulo). Se rellena con una migración; los tramos de precio viven en una única constante del dominio.

## 9. Entregables y criterios de evaluación

Se entregan tres cosas en un solo repositorio: la aplicación funcionando, la carpeta `ai-workspace/` con el proceso de ingeniería y un README que permita levantar todo en local. **[E]** El 60 % de la nota es proceso, no código.

| Criterio | Peso | Qué evalúan **[E]** | Cómo lo demostramos **[P]** |
| --- | --- | --- | --- |
| Planificación y diseño | 35 % | Especificaciones claras y pasos lógicos del sistema antes de delegar código | Specs con reglas, contrato y casos de prueba; commit de documentación anterior al primer commit de código |
| Criterio técnico y control de calidad | 25 % | Entender y auditar el código de la IA, sin aceptar soluciones subóptimas ni deuda técnica | `ai-review-log.md` con fallos reales, una pasada de revisión independiente, `CLAUDE.md` con reglas |
| Calidad del software | 30 % | Backend robusto (validaciones, tramos exactos, persistencia limpia) y frontend fluido (responsive, estados de carga y error de la API externa) | Tests con los casos de la sección 7, validaciones por capa, seed de demo, estados en cada pantalla |
| README y despliegue | 10 % | Levantar backend y frontend en local en pocos pasos y sin fricción | README probado desde una carpeta limpia |

**Contenido de `ai-workspace/` [E]** (estructura libre, tres dimensiones):

1. **Planificación y specs:** cómo se desglosaron reglas de negocio, contratos de API y validaciones antes de programar, con las specs, prompts estructurados o planes de acción usados para guiar a la IA.
2. **Arquitectura:** estructura de la base de datos, organización de carpetas y directrices dadas a la IA para que el código sea limpio, modular y sin archivos masivos.
3. **Vibe coding y control de calidad:** el desarrollo iterativo real con la IA (capturas de prompts clave, hilos de conversación o notas). La empresa usa Claude, pero se puede usar cualquier otra IA.

**Estructura propuesta [P]:** `specs/`, `architecture/` con `adr/`, `prompts/`, `ai-review-log.md` y un `README.md` de una página que cuenta el proceso. Las directrices permanentes viven en `CLAUDE.md`, en la raíz del repositorio.

**Cómo entregar [P]**

- Responder al correo de Andrea con el enlace al repositorio, antes del jueves 19 de noviembre a las 23:00. Lo ideal es entregar el miércoles por la noche o el jueves a mediodía.
- Mantener el repositorio privado mientras se trabaja; hacerlo público al entregar o invitar a quien indique la empresa.
- No subir el `.docx` de la prueba, `.env`, `node_modules`, `.venv` ni la base de datos.
- Probar el README clonando el repositorio en una carpeta limpia antes de enviar.

## 10. Supuestos y decisiones por confirmar

El enunciado deja 14 huecos. Dos conviene preguntarlos a Andrea y el resto se documenta como decisión propia en el README (sección «Decisiones y supuestos») y en un ADR cuando afecten a la arquitectura. Documentarlos con una razón clara demuestra criterio.

| # | Tema | Qué dice el enunciado | Supuesto adoptado | Acción |
| --- | --- | --- | --- | --- |
| 1 | Almacenamiento y llamadas API | Se registran en la simulación, pero la tarifa solo define tramos por usuario | Se guardan y no cambian el precio | **Preguntar** |
| 2 | Fecha límite | El correo decía «lunes 19 de noviembre»; el 19 es jueves | Jueves 19 de noviembre de 2026, 23:00 | **Preguntar** (confirmar por escrito) |
| 3 | Planes | «Plan elegido», sin lista | `starter`, `business`, `enterprise`, sin efecto en precio | Documentar |
| 4 | Tasas de impuesto | «Impuesto correspondiente al país», sin valores | Tabla de 7 países (7.2) | Documentar |
| 5 | País fuera de la lista | No dice | Error 422 «País no soportado» | Documentar |
| 6 | Identificador fuera de España | Solo exige validar el de España | Formato básico de 5 a 20 caracteres alfanuméricos | Documentar |
| 7 | CIF y NIF especiales | «Algoritmo oficial de control» | Tipo de control por entidad según la convención más extendida; K, L y M no soportados | ADR |
| 8 | Cero usuarios | Tramo 1 es «0 a 10» | Se permite y cuesta 0 € | Documentar |
| 9 | Límites y unidades | No dice | Máximo 100 000 usuarios; almacenamiento en GB; llamadas por mes | Documentar |
| 10 | Endpoints de lectura y cotización | Solo lista dos `POST` | Añadir `GET` de clientes, historial y `POST /pricing/quote` | ADR |
| 11 | Alta de clientes en la interfaz | Las vistas obligatorias no la incluyen | Formulario «Nuevo cliente» | Documentar |
| 12 | Autenticación | No la menciona | Sin login ni roles | ADR |
| 13 | Divisas ofrecidas | «EUR, USD, GBP, etc.» | EUR, USD, GBP, CHF y JPY, solo si la API las devuelve; formato con `Intl.NumberFormat` | Documentar |
| 14 | Caché de tasas | «Tiempo real» | La API actualiza una vez al día y limita peticiones; se reutilizan las tasas hasta `time_next_update_utc` | ADR |

## 11. Orden de implementación y prompt de arranque

Se trabaja en seis jornadas, de hoy viernes 13 al jueves 19 de noviembre, siempre en orden: dominio, base de datos, API, frontend y revisión. Cada pieza sigue el mismo ciclo: spec, pedir tests, pedir código, revisar, anotar lo corregido. **[P]**

| Fecha | Objetivo | Entregable de la jornada |
| --- | --- | --- |
| Vie 13 nov | Entender y preparar | Repositorio con el kit, este documento revisado, correo a Andrea enviado |
| Sáb 14 nov | Specs y arquitectura | Specs del backend, modelo de datos y ADRs; commit `docs:` antes de programar |
| Dom 15 nov | Backend | Dominio con tests, base de datos y endpoints |
| Lun 16 nov | Frontend (1) | Cliente de API, servicio de divisas, dashboard y buscador |
| Mar 17 nov | Frontend (2) | Ficha del cliente, simulador, estados de carga y error, responsive |
| Mié 18 nov | Revisión y README | Pasada de revisor independiente, correcciones, README, resumen de `ai-workspace`, prueba en carpeta limpia |
| Jue 19 nov | Colchón y entrega | Enviar antes de mediodía; el límite es a las 23:00 |

**Orden de construcción**

1. **Dominio puro, con tests primero:** `pricing`, `tax` y `tax_id`, a partir de las tablas de las secciones 7.1, 7.2 y 7.4.
2. **Base de datos:** modelos, migración inicial, tabla `tax_rates` y script de seed con datos inventados.
3. **API:** manejador de errores uniforme, `POST /customers`, lecturas de clientes, `POST /pricing/quote`, `POST /simulations` e historial.
4. **Frontend:** cliente de API y servicio de divisas, dashboard con buscador, ficha del cliente, simulador, formulario de cliente, y estados de carga, error y vacío.
5. **Cierre:** revisión independiente, README y prueba desde cero.

**Antes de abrir Claude Code**

- [ ] Leer este documento entero y cambiar lo que no compartas o no entiendas.
- [ ] Enviar el correo a Andrea con las dos preguntas de la sección 10.
- [ ] Guardar este documento como `ai-workspace/specs/00-spec-first.md` (exportado a Markdown) y hacer commit.
- [ ] Abrir Claude Code en la carpeta del repositorio, en modo plan, y pegar el prompt de arranque.

**Prompt de arranque**

```markdown
Eres mi compañero de desarrollo en el reto técnico SaaS-O-Matic. Antes de hacer nada, lee `CLAUDE.md` y el documento completo `ai-workspace/specs/00-spec-first.md`.

Reglas de esta sesión:
1. No escribas código todavía.
2. Resume en 10 líneas lo que has entendido: qué construimos, para quién, y las reglas de precio e impuestos.
3. Lista las ambigüedades, contradicciones y casos límite que veas, ordenados por importancia. Distingue lo que viene del enunciado [E] de lo que es propuesta [P].
4. Hazme las preguntas que necesites, de una en una.
5. Cuando acordemos las respuestas, propón una spec por feature en `ai-workspace/specs/` y el orden de implementación. Espera mi aprobación antes de seguir.
```

**Prompt para cada feature**

```markdown
Vamos con la feature: <nombre>.
1. Lee la sección <número> del documento y la spec `ai-workspace/specs/<archivo>.md`.
2. Escribe primero los tests a partir de la tabla de casos de prueba. Ejecútalos y confirma que fallan.
3. Implementa lo mínimo para que pasen, respetando las capas de `CLAUDE.md`.
4. Al terminar, resume qué archivos tocaste y qué decisiones tomaste.
No añadas nada fuera de la spec. Si algo es ambiguo, pregúntame.
```

**Prompt de revisor independiente (miércoles, en una sesión nueva)**

```markdown
Actúa como revisor independiente: no has escrito este código. Revisa el repositorio con esta lista: 1) corrección de las reglas RN-1 a RN-11, 2) seguridad (SQL, validación de entrada, CORS, secretos), 3) manejo de errores y estados de carga, 4) mantenibilidad (archivos largos, capas rotas, duplicación), 5) tests que faltan. Devuelve los hallazgos ordenados por gravedad, con archivo y línea, sin modificar nada.
```

## Fuentes

- Enunciado del reto técnico de Roams y correo de Andrea (documentos recibidos por el candidato).
- Plantilla Spec-First, de dominicode (estructura de las secciones 1 a 6).
- [ExchangeRate-API, Open Access endpoint](https://www.exchangerate-api.com/docs/free): actualización diaria, límite de peticiones, caché permitida y atribución obligatoria.
- [LookupTax, guía de identificadores fiscales de España](https://lookuptax.com/docs/tax-identification-number/spain-tax-id-guide): DNI, NIE, CIF y NIF K/L/M.
