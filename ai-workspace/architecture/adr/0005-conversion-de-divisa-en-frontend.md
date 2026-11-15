# ADR 0005 — Conversión de divisa solo en el frontend, con caché y vuelta a EUR

Estado: aceptado

## Contexto

El enunciado pide que el comercial vea los costes en la divisa que elija (EUR, USD, GBP…) al instante, con los tipos de cambio de `open.er-api.com` y EUR como base (UC-6, RN-7). Ese servicio gratuito actualiza las tasas una vez al día, limita las peticiones, permite guardarlas en caché y exige mostrar la atribución «Rates By Exchange Rate API» (§10 del documento 00, supuesto 14, y fuentes del 00).

## Decisión

- Solo el servicio de divisas del frontend llama a `open.er-api.com/v6/latest/EUR`. El backend no sabe nada de divisas: calcula, guarda y devuelve en EUR (ADR 0002).
- Importe mostrado = importe en EUR × tasa EUR→divisa, redondeado a 2 decimales al mostrarlo. Nunca se guarda (RN-7).
- Las tasas se guardan en caché y se reutilizan hasta `time_next_update_utc`.
- Si la API falla (red, 429 o `result` distinto de `success`), se usa la última tasa guardada con un aviso que indica de cuándo son; sin tasas guardadas, solo EUR con aviso (flujo 4 del 00).
- Se ofrecen EUR, USD, GBP, CHF y JPY, solo las que devuelva la API, formateadas con `Intl.NumberFormat` (supuesto 13). La app recuerda la divisa elegida en el navegador y muestra la atribución junto a las tasas.

## Alternativa descartada

Convertir en el backend y devolver los importes en la divisa pedida. El enunciado sitúa la conversión en la interfaz, y cada cambio de divisa costaría una petición al backend, que además dependería de un servicio externo con límite de peticiones.

## Consecuencias

- Cambiar de divisa no llama al backend; todos los importes visibles se recalculan al momento.
- El histórico no cambia con el tipo de cambio del día, porque solo se guarda en EUR.
- El frontend asume los estados de carga y error de la API externa: mientras carga, el selector está desactivado y los importes se muestran en EUR.
- Es la única excepción al «sin conexión» del 00 (§6): las últimas tasas guardadas siguen sirviendo si la API falla.
