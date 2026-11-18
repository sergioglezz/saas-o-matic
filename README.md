# SaaS-O-Matic

Herramienta interna para que un equipo comercial registre clientes corporativos, simule cuánto pagarían al mes por una suscripción SaaS (precio por tramos de usuarios más el impuesto de su país) y vea los importes en la divisa que prefiera. Tiene una API REST en Python (FastAPI y SQLite) y un dashboard en Angular.

Es una prueba técnica de desarrollo guiado por especificaciones (Spec-Driven Development) con IA. Cómo se hizo, con las specs, las decisiones de arquitectura, los prompts y la revisión del código generado, está en [`ai-workspace/`](ai-workspace/README.md).

## Cómo ejecutarla desde cero

Para quien acaba de descargar el repositorio. Son cinco pasos, y la primera vez se tarda un par de minutos. La aplicación tiene dos partes que se arrancan por separado, cada una en su propia terminal: el **backend** (la API, que calcula y guarda) y el **frontend** (la web que se abre en el navegador).

### 1. Instala lo necesario

| Programa | Versión | Para comprobar que lo tienes | Dónde conseguirlo |
| --- | --- | --- | --- |
| Git | Cualquiera | `git --version` | [git-scm.com](https://git-scm.com) |
| Python | 3.12 o superior | `python --version` (en macOS y Linux, `python3 --version`) | [python.org](https://www.python.org/downloads/) |
| Node.js | 26 LTS (trae npm) | `node --version` | [nodejs.org](https://nodejs.org) |

En Windows, al instalar Python, marca la casilla «Add python.exe to PATH».

### 2. Descarga el repositorio

```bash
git clone https://github.com/sergioglezz/saas-o-matic.git
cd saas-o-matic
```

### 3. Arranca el backend (primera terminal)

Desde la carpeta `saas-o-matic`, copia estas líneas en la terminal.

En Windows (PowerShell):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m app.db.seed
.venv\Scripts\python -m uvicorn app.main:app
```

En macOS o Linux:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m app.db.seed
.venv/bin/python -m uvicorn app.main:app
```

Qué hace cada línea:

1. Entra en la carpeta del backend.
2. Crea un entorno virtual de Python en `backend/.venv`, para que las dependencias del proyecto no se mezclen con las de tu equipo.
3. Instala las dependencias (FastAPI, SQLAlchemy y las demás).
4. Crea la base de datos, un archivo SQLite (`backend/saas_o_matic.db`), con las tasas de impuesto.
5. Carga los datos de demostración: 10 clientes y 6 simulaciones inventados. Si lo repites, no duplica nada.
6. Arranca la API.

Estará lista cuando la terminal muestre `Uvicorn running on http://127.0.0.1:8000`. **Deja esta terminal abierta.** La documentación interactiva de la API está en http://127.0.0.1:8000/docs.

### 4. Arranca el frontend (segunda terminal)

Abre otra terminal, también en la carpeta `saas-o-matic`. Los comandos son los mismos en Windows, macOS y Linux:

```bash
cd frontend
npm install
npm start
```

`npm install` descarga las dependencias de la web, y solo hace falta la primera vez. Estará lista cuando aparezca `Local: http://localhost:4200/`. **Deja también esta terminal abierta.**

### 5. Abre la aplicación

Entra en **http://localhost:4200**. Verás el listado con los 10 clientes de demostración. Abre uno para probar el simulador, y cambia la divisa en el selector de arriba.

Usa `localhost` y no `127.0.0.1:4200`: el backend solo acepta peticiones que vengan de `http://localhost:4200`, y desde la otra dirección la app mostraría «No se pudo conectar con el servidor».

### Las siguientes veces

Ya está todo instalado. Basta con arrancar las dos partes, cada una en su terminal y desde la carpeta `saas-o-matic`:

| | Windows (PowerShell) | macOS o Linux |
| --- | --- | --- |
| Backend | `cd backend` y después `.venv\Scripts\python -m uvicorn app.main:app` | `cd backend` y después `.venv/bin/python -m uvicorn app.main:app` |
| Frontend | `cd frontend` y después `npm start` | Igual |

Para pararlas, pulsa `Ctrl+C` en cada terminal.

### Si algo falla

| Qué ves | Qué hacer |
| --- | --- |
| Windows no reconoce `python` | Reinstala Python marcando «Add python.exe to PATH», o escribe `py -m venv .venv` en la segunda línea del paso 3 |
| La terminal no reconoce `npm` | Instala Node.js y abre una terminal nueva |
| La app dice «No se pudo conectar con el servidor» | Comprueba que la terminal del backend sigue abierta y sin errores, y que la dirección es `http://localhost:4200` |
| La app dice «Tipos de cambio no disponibles: importes en EUR» | Las tasas de cambio se descargan de Internet (`open.er-api.com`). Sin conexión, la app funciona igual, pero solo en euros |
| `npm start` dice `Port 4200 is already in use` | Cierra lo que esté usando ese puerto (por ejemplo, otra copia de la app) y vuelve a ejecutar `npm start`. Si te ofrece usar otro puerto, responde que no: el backend solo acepta el 4200 |
| `npm install` muestra avisos de vulnerabilidades o de `install-scripts` | No impiden arrancar. Las vulnerabilidades están en las herramientas de desarrollo; las dependencias que llegan al navegador no tienen ninguna (`npm audit --omit=dev`) |
| Quieres volver a los datos de demostración del principio | Detén el backend con `Ctrl+C`, borra `backend/saas_o_matic.db` y repite las líneas 4 a 6 del paso 3 |

## Qué hace

- **Listado y buscador** de clientes por empresa o por identificador fiscal.
- **Alta de clientes**, con validación estricta del DNI, NIE o CIF cuando el país es España.
- **Ficha del cliente con simulador:** al mover el slider de usuarios, la factura mensual se recalcula al momento, con el desglose por tramo y el impuesto. Cada simulación guardada aparece en el historial del cliente.
- **Divisas:** todos los importes se pueden ver en EUR, USD, GBP, CHF o JPY, con los tipos de cambio de ExchangeRate API.
- **Borrar un cliente** desde su ficha, junto con todo su historial.

La API tiene documentación interactiva en http://127.0.0.1:8000/docs:

| Método y ruta | Qué hace |
| --- | --- |
| `POST /pricing/quote` | Cotiza sin guardar; el simulador la pide en cada cambio |
| `POST /customers` | Registra un cliente |
| `GET /customers?q=&limit=&offset=` | Lista y busca clientes |
| `GET /customers/{id}` | Datos de un cliente |
| `DELETE /customers/{id}` | Borra un cliente y su historial |
| `POST /simulations` | Calcula y guarda una simulación |
| `GET /customers/{id}/simulations` | Historial del cliente, de la simulación más reciente a la más antigua |

Todos los errores tienen el mismo formato, `{"error": {"code", "message", "details"}}`, con un detalle por campo y los mensajes en español.

## Cómo está hecho

| Parte | Tecnología |
| --- | --- |
| Backend | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic y SQLite |
| Frontend | Angular 22 (componentes standalone y signals), Tailwind CSS 4 y Node 26 |
| Calidad | pytest, ruff y mypy estricto; Vitest, ESLint con reglas de capas y TypeScript estricto |

- **El backend calcula y el frontend muestra.** Todos los importes salen de un único cálculo en el backend; el navegador solo los convierte a otra divisa para enseñarlos (ADR 0004 y 0005).
- **Dinero exacto.** Céntimos enteros y tasas en puntos básicos (2100 = 21 %) en todas las capas, nunca `float`. El impuesto se redondea una sola vez, «mitad hacia arriba» (ADR 0002).
- **Capas.** `api` → `services` → (`repositories`, `domain`). Las reglas de negocio (tramos, impuestos e identificador fiscal) son Python puro, sin FastAPI ni SQL, y un test falla si algún módulo rompe la regla (ADR 0003).
- **Tests que salen de las specs.** Cada caso de las tablas de prueba, salvo las comprobaciones manuales, es un test que cita su identificador y su criterio de aceptación: 1071 tests en el backend y 378 en el frontend.

```text
backend/app/        api · services · repositories · domain · schemas · db (modelos, migraciones y seed) · core
frontend/src/app/   core (API, tasas y divisa) · features (clientes y simulador) · shared (formato y componentes)
ai-workspace/       constitución, specs, ADR, prompts y log de revisión
```

## Decisiones y supuestos

El enunciado deja huecos que hubo que cerrar. Estas son las decisiones que se notan al usar la aplicación; cada una está razonada en su spec o en su ADR.

### Precios e impuestos (specs 001 y 002)

- **Precio acumulativo por tramos** (lo fija el enunciado): cada tramo cobra solo los usuarios que caen en él. 10 € por usuario del 1 al 10, 8 € del 11 al 50 y 5 € a partir del 51. Con 60 usuarios son 470 €, no 300 €.
- **Usuarios:** de 0 a 100 000. Con 0 todo vale 0 € (el enunciado describe el primer tramo como «0 a 10»).
- **Tasas de impuesto.** El enunciado pide sumar «el impuesto correspondiente al país del cliente», pero no da valores. Se adoptan estas como supuesto:

| País | Código | Tasa | En puntos básicos |
| --- | --- | --- | --- |
| España | ES | 21 % | 2100 |
| Portugal | PT | 23 % | 2300 |
| Francia | FR | 20 % | 2000 |
| Alemania | DE | 19 % | 1900 |
| Italia | IT | 22 % | 2200 |
| Reino Unido | GB | 20 % | 2000 |
| Estados Unidos | US | 0 % | 0 |

- Las tasas son datos, no código. Viven en la tabla `tax_rates` y las inserta la primera migración, así que existen nada más preparar la base de datos, sin cargar los datos de demostración. Cambiar, añadir o quitar una tasa no exige tocar el cálculo (ADR 0006).
- Un país sin tasa configurada se rechaza como «País no soportado». El código se acepta en minúsculas y con espacios alrededor: `" es "` vale como `ES`.
- Estados Unidos tiene 0 % porque no hay IVA federal; el impuesto sobre ventas de cada estado no se modela.

**Fuera de alcance:** el IGIC de Canarias, los impuestos de Ceuta y Melilla, y la inversión del sujeto pasivo en operaciones entre empresas de la UE.

### Clientes (spec 003)

- **Identificador fiscal.** Se normaliza antes de validarlo y de guardarlo: mayúsculas, sin espacios, guiones ni puntos. Con país España debe ser un DNI, un NIE o un CIF con el carácter de control correcto; en el resto de países solo se comprueba un formato básico de 5 a 20 letras o dígitos.
- **Control del CIF.** La AEAT no publica qué entidades llevan letra y cuáles dígito, así que se usa la convención más extendida (ADR 0009). Los NIF especiales `K`, `L` y `M` no se admiten: no tienen método de control publicado.
- **Identificador único.** No puede haber dos clientes con el mismo identificador normalizado, sea cual sea su país: la segunda alta responde 409.
- **Email.** Se valida con una regla propia (`local@dominio`, con al menos un punto en el dominio), sin añadir ninguna biblioteca. No se admiten direcciones con caracteres no ASCII.
- **Planes.** `starter`, `business` y `enterprise`. El plan se guarda, pero no cambia el precio.
- **Búsqueda.** Por fragmento del nombre, sin distinguir mayúsculas (tampoco en `ñ` ni en vocales con tilde), o por fragmento del identificador, que se puede escribir con separadores. No se equiparan letras con y sin tilde: `telefonica` no encuentra `Telefónica`.
- **Ficha.** `GET /customers/{id}` responde 404 tanto si el cliente no existe como si `{id}` no es un número de cliente.
- **Datos de demostración.** `python -m app.db.seed` crea 10 clientes inventados, con identificadores sintéticos y correos de dominios `.example`. Se puede ejecutar varias veces: no duplica ni modifica lo que ya existe.

**Fuera de alcance:** editar clientes, validar el identificador fiscal de otros países y comprobar que el identificador o el correo existen de verdad.

### Simulaciones (spec 004)

- **Mismo cálculo que la cotización.** `POST /simulations` calcula con el país guardado en el cliente y con el mismo código que `POST /pricing/quote`: con los mismos datos, las cifras coinciden. La petición no lleva país ni importes; si los lleva, se rechazan.
- **Instantánea.** Cada simulación guarda la tasa aplicada, el subtotal, el impuesto, el total y los tres tramos con sus límites. Si después cambia una tasa o un país deja de estar soportado, el historial sigue mostrando lo que se guardó.
- **Campos.** `customer_id`, `active_users` (0 a 100 000, como la cotización), `storage_gb` y `api_calls_per_month`, los cuatro obligatorios. La simulación usa `active_users`; la cotización sigue usando `users`.
- **Almacenamiento y llamadas a la API.** Se guardan, pero no cambian el precio: la tarifa del enunciado solo define tramos por usuario. Como supuesto, admiten de 0 a 1 000 000 GB y de 0 a 1 000 000 000 llamadas al mes.
- **Historial.** `GET /customers/{id}/simulations` las devuelve de la más reciente a la más antigua, paginadas con `limit` (1 a 100, por defecto 50) y `offset`, igual que el listado de clientes.
- **Errores.** Un cliente inexistente responde 404, siempre después de validar los datos. Si el país del cliente ya no tiene tasa de impuesto, no se puede guardar una simulación nueva (422 sobre `customer_id`), pero su historial se sigue leyendo.
- **Datos de demostración.** El seed añade 6 simulaciones a 5 clientes de demostración, que cubren los tres tramos y un país con impuesto 0. Solo se crean para los clientes de demostración que aún no tienen ninguna, así que se puede repetir y completa una base de datos sembrada antes.

**Fuera de alcance:** editar, borrar o consultar una simulación suelta (se borran todas con su cliente, spec 007), comparar simulaciones, generar un PDF y guardar la divisa de visualización (la conversión es solo presentación).

### Frontend (specs 005 y 006)

- **Pantallas.** Listado y buscador en `/clientes`, alta en `/clientes/nuevo` y ficha con simulador e historial en `/clientes/{id}`. Cualquier otra dirección muestra «Página no encontrada».
- **Importes.** Todos los calcula el backend en euros. El navegador solo los convierte para mostrarlos y nunca envía ni guarda un importe convertido.
- **Divisas.** EUR, USD, GBP, CHF y JPY, con las tasas de [ExchangeRate API](https://www.exchangerate-api.com) (`open.er-api.com`, base EUR). Se piden al abrir la app y se guardan en el navegador hasta su próxima actualización. Si la API falla, se usan las últimas guardadas con un aviso; sin ninguna, todo se muestra en EUR. La atribución «Rates By Exchange Rate API» está siempre visible y la divisa elegida se recuerda en el navegador.
- **Conversión.** Cada importe se convierte por separado, con redondeo «mitad hacia arriba» sobre el valor exacto, así que en otra divisa la suma de subtotal e impuesto puede diferir del total en un céntimo (en yenes, en un yen). Es una conversión orientativa y la app lo avisa. Cada divisa se muestra con sus decimales: 2 en EUR, USD, GBP y CHF, y ninguno en JPY (spec 008).
- **Formato.** Español: coma decimal y punto de miles también con 4 cifras («1.234,56 €», «27.319 JPY»). Las fechas, en la zona horaria del navegador.
- **Simulador.** Slider de 0 a 200 usuarios, más un campo que admite hasta 100 000. La cotización se pide 300 ms después del último cambio. «Guardar simulación» solo se activa cuando la cotización mostrada corresponde a los valores escritos: lo que se ve es lo que se guarda.
- **Alta.** El navegador solo comprueba los campos obligatorios y las longitudes máximas. El formato del email y del identificador lo valida el backend, y su mensaje aparece junto al campo.
- **Listas largas.** El listado y el historial cargan de 50 en 50 con «Cargar más».
- **Aspecto (spec 006).** Estilos con [Tailwind CSS](https://tailwindcss.com) 4, que solo actúa al compilar y no añade código al navegador (ADR 0011). Tema índigo con contrastes comprobados, iconos propios, esqueletos mientras cargan los datos y animaciones de entrada que se desactivan si el sistema pide reducir el movimiento.

**Fuera de alcance:** refrescar las tasas con la app abierta, más divisas, conservar la búsqueda en la dirección, avisar al salir con datos sin guardar, funcionar sin conexión y pruebas automáticas en un navegador real, que se sustituyen por las comprobaciones manuales de la spec 005.

### Borrar clientes (spec 007)

No estaba en el enunciado ni en el plan inicial: el autor la echó en falta al usar la aplicación terminada, y entró como una spec nueva con el mismo proceso que el resto ([spec 007](ai-workspace/specs/007-delete-customer/spec.md)).

- **Desde la ficha.** «Borrar cliente» abre una confirmación que dice cuántas simulaciones se perderán y avisa de que no se puede deshacer. Escape o «Cancelar» la cierran sin borrar nada. Después de borrar, el listado muestra «Cliente «…» borrado».
- **Con todo su historial.** `DELETE /customers/{id}` borra el cliente, sus simulaciones y sus tramos en una sola transacción, y responde 204 sin cuerpo. Si algo falla, no se borra nada.
- **Sin migraciones nuevas.** La base de datos sigue rechazando que se borre un cliente con simulaciones (spec 004), así que el servicio borra antes, de forma explícita, su historial. El identificador fiscal queda libre para un alta nueva, y el `id` no se vuelve a usar.

**Fuera de alcance:** deshacer un borrado o tener una papelera, y borrar desde el listado o varios clientes a la vez.

### Yenes sin decimales (spec 008)

La spec 005 mostraba todos los importes con 2 decimales, también en yenes («27.319,14 JPY»). El yen no tiene céntimos, así que el autor corrigió esa decisión de la IA al usar la aplicación terminada, y el cambio entró como una spec nueva ([spec 008](ai-workspace/specs/008-currency-decimals/spec.md)). La regla RN-7 del enunciado, «redondeado a 2 decimales», se lee desde entonces como los céntimos de cada divisa.

- **Decimales de la divisa.** Cada importe se muestra con los decimales que fija la norma ISO 4217 para su divisa, los mismos que aplica `Intl.NumberFormat`: 2 en EUR, USD, GBP y CHF, y ninguno en JPY.
- **Redondeo.** En yenes, cada importe se redondea a yenes enteros, «mitad hacia arriba» y una sola vez sobre el valor exacto: 2983,495 yenes se muestran como «2.983 JPY», no como 2.984, que saldría de redondear primero a 2983,50.
- **Lo que no cambia.** El backend sigue calculando y guardando en céntimos de EUR, y la tasa de la cabecera conserva sus decimales («1 EUR = 161,27 JPY»).

### Límites conocidos

- **Sin autenticación ni roles** (ADR 0007): quien abre la app puede hacer todo. Se acepta porque es una herramienta interna que se ejecuta en local y los datos de demostración son inventados.
- **SQLite** basta para el uso previsto, decenas de comerciales a la vez (ADR 0001).
- **Sin límites de tamaño del cuerpo ni de peticiones:** la API no está pensada para exponerse a Internet.
- **Solo en local:** no hay despliegue ni contenedores.

## Para desarrollar

Versiones con las que se probó: Python 3.14 y Node 26.13.1 LTS (ADR 0010).

### Backend

Para los tests y el lint hacen falta también las dependencias de desarrollo. Con el entorno virtual activado, los comandos se escriben sin la ruta de `.venv`:

```bash
cd backend
source .venv/bin/activate            # Git Bash en Windows: source .venv/Scripts/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload        # se reinicia solo al cambiar el código
```

En PowerShell, el entorno se activa con `.venv\Scripts\Activate.ps1`.

La configuración se lee de variables de entorno, con valores por defecto para trabajar en local (`backend/.env.example`): `DATABASE_URL` (`sqlite:///./saas_o_matic.db`) y `FRONTEND_ORIGIN` (`http://localhost:4200`, el único origen que admite CORS). Nada carga un archivo `.env` por su cuenta, así que para arrancar no hace falta crear ninguno.

### Frontend

`npm start` vuelve a compilar y recarga el navegador cada vez que se guarda un archivo.

### Tests y lint

| | Backend (desde `backend/`) | Frontend (desde `frontend/`) |
| --- | --- | --- |
| Tests | `pytest` (1071) | `npm test` (378, una sola pasada) |
| Lint y formato | `ruff check .` y `ruff format --check .` | `npm run lint` |
| Tipos | `mypy .` | TypeScript estricto, al compilar con `npm run build` |

## Rendimiento de la cotización

El objetivo de la spec 002 (RNF-2) es un percentil 95 por debajo de 200 ms en local. Medido una vez: **p95 = 6,3 ms** (mínimo 4,2 · mediana 5,3 · máximo 7,1), y tres repeticiones dieron de 6,2 a 6,3 ms.

Método: 100 peticiones seguidas a `POST http://127.0.0.1:8000/pricing/quote` con `{"users": 15, "country": "ES"}`, una conexión nueva por petición, tras 5 de calentamiento sin medir; el p95 es la muestra 95 de las 100 ordenadas, con el tiempo medido en el cliente (`time.perf_counter` y `urllib`). Servidor `uvicorn app.main:app --reload` con la base de datos recién migrada, en un AMD Ryzen 7 7735HS con 16 GB de RAM, Windows 11 y Python 3.14.2.

**En Windows, llama a la API con `127.0.0.1` y no con `localhost`.** `uvicorn` solo escucha en `127.0.0.1`, y con `localhost` un cliente como `curl` prueba antes IPv6 (`::1`) y tarda unos 0,2 s más en cada conexión nueva (0,21 s frente a 0,006 s). El retraso es de la conexión, no de la API, y por eso el frontend usa `http://127.0.0.1:8000`.
