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
