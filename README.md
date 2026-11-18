# SaaS-O-Matic

Herramienta interna para que un equipo comercial registre clientes corporativos, simule cuánto pagarían al mes por una suscripción SaaS (precio por tramos de usuarios más el impuesto de su país) y vea los importes en la divisa que prefiera.

- **Backend:** API REST en Python con FastAPI y SQLite. Calcula y guarda todos los importes.
- **Frontend:** dashboard en Angular. Muestra los datos y convierte la divisa.

Es una prueba técnica de desarrollo guiado por especificaciones (Spec-Driven Development) con IA. Cómo se hizo, con las specs, las decisiones de arquitectura, los prompts y la revisión del código generado, está en [`ai-workspace/`](ai-workspace/README.md).

## Qué hace

- **Listado y buscador** de clientes, por empresa o por identificador fiscal.
- **Alta de clientes**, con validación del DNI, NIE o CIF cuando el país es España.
- **Ficha con simulador:** al mover el slider de usuarios, la factura mensual se recalcula al momento, con el desglose por tramos y el impuesto. Cada simulación guardada pasa al historial del cliente.
- **Divisas:** los importes se pueden ver en EUR, USD, GBP, CHF o JPY.
- **Borrar un cliente** desde su ficha, con todo su historial.

## Cómo ejecutarlo

Hace falta tener instalados **Git**, **Python 3.12 o superior** y **Node.js 26 LTS**, que trae npm. En Windows, al instalar Python, marca la casilla «Add python.exe to PATH».

El backend y el frontend se arrancan por separado, cada uno en su propia terminal.

### 1. Descarga el repositorio

```bash
git clone https://github.com/sergioglezz/saas-o-matic.git
cd saas-o-matic
```

### 2. Arranca el backend (primera terminal)

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

Estos comandos crean un entorno virtual, instalan las dependencias, crean la base de datos con las tasas de impuesto, cargan 10 clientes y 6 simulaciones de demostración, todos inventados, y arrancan la API. Está lista cuando aparece `Uvicorn running on http://127.0.0.1:8000`, y su documentación interactiva queda en http://127.0.0.1:8000/docs. No hace falta crear ningún archivo `.env`: la configuración tiene valores por defecto (`backend/.env.example`).

### 3. Arranca el frontend (segunda terminal)

Desde la carpeta `saas-o-matic`, igual en todos los sistemas:

```bash
cd frontend
npm install
npm start
```

### 4. Abre la aplicación

Entra en **http://localhost:4200**. Usa `localhost` y no `127.0.0.1`: el backend solo acepta peticiones que vengan de `http://localhost:4200`.

Las siguientes veces basta con el último comando de cada parte: el de `uvicorn` en el backend y `npm start` en el frontend. Para pararlas, pulsa `Ctrl+C` en cada terminal.

### Si algo falla

| Qué ves | Qué hacer |
| --- | --- |
| La app dice «No se pudo conectar con el servidor» | Comprueba que la terminal del backend sigue abierta y sin errores, y que la dirección es `http://localhost:4200` |
| La app dice «Tipos de cambio no disponibles: importes en EUR» | Las tasas de cambio se descargan de Internet (`open.er-api.com`). Sin conexión, la app funciona igual, pero solo en euros |
| Windows no reconoce `python` | Reinstala Python marcando «Add python.exe to PATH», o usa `py` en lugar de `python` en la segunda línea del backend |
| `npm install` avisa de vulnerabilidades | No impide arrancar: están en las herramientas de desarrollo, y lo que llega al navegador no tiene ninguna (`npm audit --omit=dev`) |
| Quieres volver a los datos de demostración | Para el backend, borra `backend/saas_o_matic.db` y repite los comandos de `alembic`, `seed` y `uvicorn` |

## Tests y calidad

Para los tests del backend hacen falta las dependencias de desarrollo: `pip install -r requirements-dev.txt` dentro del entorno virtual.

| | Backend (desde `backend/`) | Frontend (desde `frontend/`) |
| --- | --- | --- |
| Tests | `pytest` (1071 tests) | `npm test` (378 tests, una sola pasada) |
| Lint y tipos | `ruff check .`, `ruff format --check .` y `mypy .` | `npm run lint` y `npm run build` |

Los tests salen de las specs: cada caso de sus tablas de prueba, salvo las comprobaciones manuales, es un test que cita su identificador y su criterio de aceptación.

## Cómo está hecho

| Parte | Tecnología |
| --- | --- |
| Backend | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic y SQLite |
| Frontend | Angular 22 con signals, Tailwind CSS 4 y Node 26 |
| Calidad | pytest, ruff y mypy; Vitest, ESLint y TypeScript estricto |

- **El backend calcula y el frontend muestra.** Todos los importes salen de un único cálculo en el backend. El navegador solo los convierte a otra divisa para enseñarlos, y nunca envía ni guarda un importe convertido (ADR 0004 y 0005).
- **Dinero exacto.** Céntimos enteros y tasas en puntos básicos (2100 = 21 %) en todas las capas, nunca `float` (ADR 0002).
- **Capas.** `api` → `services` → (`repositories`, `domain`). Las reglas de negocio son Python puro, sin FastAPI ni SQL, y un test falla si algún módulo rompe la regla (ADR 0003).
- **Errores con un único formato:** `{"error": {"code", "message", "details"}}`, con los mensajes en español.

| API | Qué hace |
| --- | --- |
| `POST /pricing/quote` | Cotiza sin guardar; el simulador la pide en cada cambio |
| `POST /customers` · `GET /customers` · `GET /customers/{id}` · `DELETE /customers/{id}` | Alta, listado con búsqueda, ficha y borrado de clientes |
| `POST /simulations` · `GET /customers/{id}/simulations` | Guardar una simulación e historial del cliente |

## Decisiones y supuestos

El enunciado deja huecos que hubo que cerrar. Estos son los que se notan al usar la aplicación; cada uno está razonado en su spec o en su ADR.

- **Precio por tramos acumulativo**, como fija el enunciado: 10 € por usuario del 1 al 10, 8 € del 11 al 50 y 5 € a partir del 51. Con 60 usuarios son 470 €. Se admiten de 0 a 100 000 usuarios, y con 0 todo vale 0 €.
- **Tasas de impuesto.** El enunciado no da valores, así que se adoptan estos. Se guardan en una tabla de la base de datos, no en el código (ADR 0006).

  | ES | PT | FR | DE | IT | GB | US |
  | --- | --- | --- | --- | --- | --- | --- |
  | 21 % | 23 % | 20 % | 19 % | 22 % | 20 % | 0 % |

  Estados Unidos tiene 0 % porque no hay IVA federal. Un país que no está en la tabla se rechaza como «País no soportado». Quedan fuera el IGIC de Canarias, los impuestos de Ceuta y Melilla y la inversión del sujeto pasivo entre empresas de la UE.
- **Identificador fiscal.** Se normaliza (mayúsculas, sin espacios, guiones ni puntos) y no puede repetirse. En España debe ser un DNI, un NIE o un CIF con su carácter de control correcto (ADR 0009); en otros países basta un formato básico de 5 a 20 letras o dígitos.
- **Planes** `starter`, `business` y `enterprise`: se guardan, pero no cambian el precio.
- **Alta de clientes en la interfaz**, aunque el enunciado no la pide entre las vistas.
- **Simulaciones.** Guardan una copia del cálculo (tasa, tramos, impuesto y total), así que el historial no cambia si después cambia una tasa. El almacenamiento (de 0 a 1 000 000 GB) y las llamadas a la API (de 0 a 1 000 000 000 al mes) se guardan, pero no cambian el precio: la tarifa solo define tramos por usuario.
- **Divisas.** Las tasas de cambio vienen de [ExchangeRate API](https://www.exchangerate-api.com) y se guardan en el navegador hasta su próxima actualización. Si la API falla, se usan las últimas guardadas, y sin ninguna todo se ve en euros. Cada divisa lleva sus decimales: 2 en EUR, USD, GBP y CHF, y ninguno en JPY (spec 008).
- **Añadidos con la aplicación terminada:** la interfaz moderna (spec 006), el borrado de clientes (spec 007) y los yenes sin decimales (spec 008) salieron de usar la aplicación, y cada uno siguió el mismo proceso que el resto.

### Límites conocidos

- **Sin autenticación ni roles** (ADR 0007): quien abre la app puede hacer todo. Es una herramienta interna que se ejecuta en local, con datos inventados.
- **SQLite** basta para el uso previsto, decenas de comerciales a la vez (ADR 0001).
- **Sin límites de tamaño del cuerpo ni de peticiones:** la API no está pensada para exponerse a Internet.
- **NIF especiales `K`, `L` y `M`:** no se admiten, porque no tienen un método de control publicado (ADR 0009).
- **Solo en local:** no hay despliegue ni contenedores.

**Rendimiento:** el objetivo era cotizar en menos de 200 ms en local, y la medición dio un p95 de 6,3 ms. Se hicieron 100 peticiones seguidas a `POST /pricing/quote` en un AMD Ryzen 7 7735HS, con Windows 11 y Python 3.14 (spec 002, RNF-2).
