# ADR 0004 — Cotización en el backend con espera tras el slider

Estado: aceptado

## Contexto

El simulador proyecta la factura mensual en tiempo real mientras el comercial mueve el slider de usuarios (UC-4). El enunciado solo define dos `POST`, para crear clientes y simulaciones; no dice cómo se calcula la proyección antes de guardar (§10 del documento 00, supuesto 9). El 00 fija que el backend calcula todos los importes y que el cliente no envía nunca precios ni totales (§8.1).

## Decisión

- El backend expone `POST /pricing/quote`, que cotiza sin guardar: responde 200 con el mismo desglose, subtotal, impuesto y total que guardará una simulación (§8.2 y §8.3 del 00).
- El endpoint no calcula nada por su cuenta: usa el cálculo de la spec 001 (`quote` en `backend/app/services/pricing.py`), el mismo que usará `POST /simulations` para guardar.
- El frontend espera tras el último cambio del slider antes de pedir la cotización (300 ms, spec 005 D-4) y cancela la petición anterior si sigue en curso (§5 y §6 del 00).
- El mismo supuesto 9 añade los `GET` de clientes e historial que necesita el dashboard (§8.2 del 00).

## Alternativa descartada

Duplicar el cálculo en el frontend. Las reglas de tramos, impuesto y redondeo existirían dos veces, en Python y en TypeScript, y podrían divergir: el comercial vería una cifra y se guardaría otra. Además, el navegador necesitaría las tasas de impuesto, que viven en la base de datos (ADR 0006).

## Consecuencias

- Una sola fuente de verdad: cualquier importe que se muestre o se guarde sale del mismo cálculo (RNF-4 de la spec 001, RNF-1 de la 002).
- Cada movimiento del slider cuesta una petición; la espera evita saturar la API. El objetivo es cotizar en menos de 200 ms en local, y la medición dio un p95 de 6,3 ms (README).
- Si la cotización falla, el simulador mantiene el último resultado y avisa «No se pudo actualizar» (flujo 3 del 00).
