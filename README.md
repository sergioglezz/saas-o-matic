# SaaS-O-Matic

Herramienta interna para que el equipo comercial simule y presupueste suscripciones SaaS multi-divisa. Este README se completará con las instrucciones de arranque al cerrar el proyecto; por ahora recoge las decisiones y supuestos ya tomados.

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

**Fuera de alcance:** editar o borrar clientes, validar el identificador fiscal de otros países y comprobar que el identificador o el correo existen de verdad.

## Backend: puesta en marcha

Pasos comprobados en un clon limpio, con Python 3.12 o superior (probado con 3.14):

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Windows con Git Bash; en Linux o macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head                 # crea la base de datos SQLite con las tasas de impuesto
python -m app.db.seed                # opcional: 10 clientes de demostración
uvicorn app.main:app --reload        # API en http://127.0.0.1:8000 y documentación en /docs
```

En PowerShell, el entorno se activa con `.venv\Scripts\Activate.ps1`. Los tests y el lint se ejecutan con `pytest`, `ruff check .`, `ruff format --check .` y `mypy .`. Las instrucciones del frontend se añadirán con su spec.

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
