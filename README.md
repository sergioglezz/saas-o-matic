# SaaS-O-Matic

Herramienta interna para que el equipo comercial simule y presupueste suscripciones SaaS multi-divisa. Este README recoge las decisiones y supuestos tomados, y cómo poner en marcha el backend y el frontend.

## Arranque rápido

Con Python 3.12 o superior y Node 26, abre dos terminales en la raíz del repositorio y ejecuta un comando en cada una.

En PowerShell (la terminal por defecto de Windows):

```powershell
cd backend; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt; .\.venv\Scripts\alembic upgrade head; .\.venv\Scripts\python -m app.db.seed; .\.venv\Scripts\uvicorn app.main:app
```

```powershell
cd frontend; npm install; npm start
```

En Git Bash, Linux o macOS (en Linux y macOS, con `.venv/bin/activate`):

```bash
cd backend && python -m venv .venv && source .venv/Scripts/activate && pip install -r requirements.txt && alembic upgrade head && python -m app.db.seed && uvicorn app.main:app
```

```bash
cd frontend && npm install && npm start
```

Abre **http://localhost:4200** (no `127.0.0.1:4200`, que el backend no admite). Las dos secciones de puesta en marcha del final explican cada paso, los tests y el lint.

## Decisiones y supuestos

### Tasas de impuesto por defecto (spec 001, decisión D-3)

El enunciado pide sumar «el impuesto correspondiente al país del cliente», pero no da valores. Se adoptan estas tasas como supuesto:

| País | Código | Tasa | En puntos básicos |
| --- | --- | --- | --- |
| España | ES | 21 % | 2100 |
| Portugal | PT | 23 % | 2300 |
| Francia | FR | 20 % | 2000 |
| Alemania | DE | 19 % | 1900 |
| Italia | IT | 22 % | 2200 |
| Reino Unido | GB | 20 % | 2000 |
| Estados Unidos | US | 0 % | 0 |

- Las tasas son datos, no código. Viven en la tabla `tax_rates` y las inserta la primera migración, así que están disponibles nada más preparar la base de datos, sin cargar los datos de demostración.
- Cambiar, añadir o quitar una tasa no exige tocar el cálculo.
- Cotizar para un país sin tasa configurada se rechaza como «país no soportado».
- Estados Unidos tiene 0 % porque no hay IVA federal. El impuesto sobre ventas de cada estado no se modela.

**Fuera de alcance:** el IGIC de Canarias, los impuestos de Ceuta y Melilla, y la inversión del sujeto pasivo en operaciones entre empresas de la UE.

### Clientes (spec 003)

- **Identificador fiscal.** Se normaliza antes de validarlo y de guardarlo: mayúsculas, sin espacios, guiones ni puntos. Con país España debe ser un DNI, un NIE o un CIF con el carácter de control correcto; en el resto de países solo se comprueba un formato básico de 5 a 20 letras o dígitos.
- **Control del CIF.** La AEAT no publica qué entidades llevan letra y cuáles dígito, así que se usa la convención más extendida (ADR 0009). Los NIF especiales `K`, `L` y `M` no se admiten: no tienen método de control publicado.
- **Identificador único.** No puede haber dos clientes con el mismo identificador normalizado, sea cual sea su país: el segundo alta responde 409.
- **Email.** Se valida con una regla propia (`local@dominio` con al menos un punto en el dominio), sin añadir ninguna biblioteca. No se admiten direcciones con caracteres no ASCII.
- **Planes.** `starter`, `business` y `enterprise`. El plan se guarda, pero no cambia el precio.
- **Búsqueda.** Por fragmento del nombre, sin distinguir mayúsculas (tampoco en `ñ` ni en vocales con tilde), o por fragmento del identificador, que se puede escribir con separadores. No se equiparan letras con y sin tilde: `telefonica` no encuentra `Telefónica`.
- **Ficha.** `GET /customers/{id}` responde 404 tanto si el cliente no existe como si `{id}` no es un número de cliente.
- **Datos de demostración.** `python -m app.db.seed` crea 10 clientes inventados, con identificadores sintéticos y correos de dominios `.example`. Se puede ejecutar varias veces: no duplica ni modifica lo que ya existe.

**Fuera de alcance:** editar clientes, validar el identificador fiscal de otros países y comprobar que el identificador o el correo existen de verdad. Borrar clientes se añadió después, con la spec 007.

### Simulaciones (spec 004)

- **Endpoints.** `POST /simulations` calcula y guarda una simulación; `GET /customers/{id}/simulations` devuelve el historial del cliente, de la más reciente a la más antigua, paginado con `limit` (1 a 100, por defecto 50) y `offset`, igual que el listado de clientes.
- **Mismo cálculo que la cotización.** La simulación se calcula con el país guardado en el cliente y con el mismo código que `POST /pricing/quote`: con los mismos datos, las cifras coinciden. La petición no lleva país ni importes; si los lleva, se rechazan.
- **Instantánea.** Cada simulación guarda la tasa aplicada, el subtotal, el impuesto, el total y los tres tramos con sus límites. Si después cambia una tasa o un país deja de estar soportado, el historial sigue mostrando lo que se guardó.
- **Campos.** `customer_id`, `active_users` (0 a 100 000, como la cotización), `storage_gb` y `api_calls_per_month`, los cuatro obligatorios. La simulación usa `active_users`; la cotización sigue usando `users`.
- **Almacenamiento y llamadas a la API.** Se guardan, pero no cambian el precio: la tarifa del enunciado solo define tramos por usuario. Como supuesto, admiten de 0 a 1 000 000 GB y de 0 a 1 000 000 000 llamadas al mes.
- **Errores.** Un cliente inexistente responde 404, siempre después de validar los datos. Si el país del cliente ya no tiene tasa de impuesto, no se puede guardar una simulación nueva (422 sobre `customer_id`), pero su historial se sigue leyendo.
- **Datos de demostración.** `python -m app.db.seed` añade 6 simulaciones a 5 clientes de demostración, que cubren los tres tramos y un país con impuesto 0. Solo se crean para los clientes de demostración que aún no tienen ninguna, así que se puede repetir y completa una base de datos sembrada antes.

**Fuera de alcance:** editar o borrar una simulación suelta (se borran todas con su cliente, spec 007), consultar una simulación suelta, comparar simulaciones, generar un PDF y guardar la divisa de visualización (la conversión es solo presentación).

### Frontend (spec 005)

- **Pantallas.** Listado y buscador en `/clientes`, alta en `/clientes/nuevo` y ficha con simulador e historial en `/clientes/{id}`. Cualquier otra dirección muestra «Página no encontrada».
- **Importes.** Todos los calcula el backend en euros. El navegador solo los convierte para mostrarlos y nunca envía ni guarda un importe convertido.
- **Divisas.** EUR, USD, GBP, CHF y JPY, con las tasas de [ExchangeRate API](https://www.exchangerate-api.com) (`open.er-api.com`, base EUR). Se piden al abrir la app y se guardan en el navegador hasta su próxima actualización. Si la API falla, se usan las últimas guardadas con un aviso; sin ninguna, todo se muestra en EUR. La atribución «Rates By Exchange Rate API» está siempre visible. La divisa elegida se recuerda en el navegador.
- **Conversión.** Cada importe se convierte por separado, con redondeo «mitad hacia arriba» sobre el valor exacto, así que en otra divisa la suma de subtotal e impuesto puede diferir del total en un céntimo. Es una conversión orientativa y la app lo avisa. Se muestran siempre 2 decimales, también en JPY.
- **Formato.** Español: coma decimal y punto de miles también con 4 cifras («1.234,56 €»). Las fechas, en la zona horaria del navegador.
- **Simulador.** Slider de 0 a 200 usuarios, más un campo que admite hasta 100 000. La cotización se pide 300 ms después del último cambio. «Guardar simulación» solo se activa cuando la cotización mostrada corresponde a los valores escritos: lo que se ve es lo que se guarda. El almacenamiento y las llamadas a la API se guardan, pero no cambian el precio.
- **Alta.** El navegador solo comprueba los campos obligatorios y las longitudes máximas. El formato del email y del identificador lo valida el backend, y su mensaje aparece junto al campo.
- **Listas largas.** El listado y el historial cargan de 50 en 50 con «Cargar más».

**Fuera de alcance:** refrescar las tasas con la app abierta, más divisas, conservar la búsqueda en la dirección, avisar al salir con datos sin guardar, funcionar sin conexión y pruebas automáticas en un navegador real, que se sustituyen por las comprobaciones manuales de la spec 005.

### Borrar clientes (spec 007)

Llegó con la aplicación ya terminada: al usarla, el autor echó en falta poder borrar un cliente y lo pidió como una funcionalidad nueva. Pasó por el mismo proceso que el resto: spec, plan, tareas y tests antes que el código (`ai-workspace/specs/007-delete-customer/` y el prompt P-19 de `ai-workspace/prompts.md`).

- **Desde la ficha.** «Borrar cliente» abre una confirmación que dice cuántas simulaciones se perderán y avisa de que no se puede deshacer. Escape o «Cancelar» la cierran sin borrar nada. Después de borrar, el listado muestra «Cliente «…» borrado».
- **Con todo su historial.** `DELETE /customers/{id}` borra el cliente, sus simulaciones y sus tramos en una sola transacción, y responde 204 sin cuerpo. Si algo falla, no se borra nada. Un cliente inexistente, o un `{id}` que no es un número de cliente, da 404.
- **Sin migraciones nuevas.** La base de datos sigue rechazando que se borre un cliente con simulaciones (spec 004). Por eso el servicio borra antes, de forma explícita, su historial. El identificador fiscal queda libre para un alta nueva, y el `id` no se vuelve a usar.

**Fuera de alcance:** deshacer un borrado o tener una papelera, borrar desde el listado o varios clientes a la vez, y borrar una simulación suelta.

## Backend: puesta en marcha

Pasos comprobados en un clon limpio, con Python 3.12 o superior (probado con 3.14):

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Windows con Git Bash; en Linux o macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head                 # crea la base de datos SQLite con las tasas de impuesto
python -m app.db.seed                # opcional: 10 clientes y 6 simulaciones de demostración
uvicorn app.main:app --reload        # API en http://127.0.0.1:8000 y documentación en /docs
```

En PowerShell, el entorno se activa con `.venv\Scripts\Activate.ps1`. Los tests y el lint se ejecutan con `pytest`, `ruff check .`, `ruff format --check .` y `mypy .`.

## Frontend: puesta en marcha

Necesita Node 26 LTS (probado con 26.13.1; ADR 0010) y el backend arrancado como se indica arriba. En otra terminal:

```bash
cd frontend
npm install                          # solo la primera vez
npm start                            # app en http://localhost:4200
```

Ábrela en `http://localhost:4200`, no en `http://127.0.0.1:4200`: el backend solo acepta peticiones del primer origen (CORS) y desde el segundo se vería «No se pudo conectar con el servidor».

Los tests se ejecutan con `npm test` (una sola pasada), el lint con `npm run lint` y la compilación de producción con `npm run build`.

## Rendimiento de la cotización (spec 002, RNF-2)

Medición informativa, hecha una vez; no bloquea la entrega. El objetivo es un percentil 95 por debajo de 200 ms.

| Dato | Valor |
| --- | --- |
| Resultado | p95 = 6,3 ms (mínimo 4,2 · mediana 5,3 · máximo 7,1) |
| Petición | `POST http://127.0.0.1:8000/pricing/quote` con `{"users": 15, "country": "ES"}` |
| Método | 100 peticiones seguidas, una conexión nueva por petición, tras 5 de calentamiento sin medir; el p95 es la muestra número 95 de las 100 ordenadas. Tiempo medido en el cliente con `time.perf_counter` y `urllib` de la biblioteca estándar |
| Servidor | `uvicorn app.main:app --reload`, ya arrancado, con la base de datos SQLite recién migrada |
| Máquina | AMD Ryzen 7 7735HS, 16 GB de RAM, Windows 11, Python 3.14.2 |

Tres repeticiones de la medición dieron un p95 de 6,2 a 6,3 ms.

**Aviso para Windows:** `uvicorn` escucha solo en `127.0.0.1`. Con `http://localhost:8000`, un cliente como `curl` intenta primero la dirección IPv6 (`::1`) y tarda unos 0,2 s más en cada conexión nueva (medido: 0,21 s frente a 0,006 s). El retraso es de la conexión, no de la API.
