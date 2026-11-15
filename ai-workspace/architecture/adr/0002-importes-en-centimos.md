# ADR 0002 — Importes en céntimos enteros y tasas en puntos básicos

Estado: aceptado

## Contexto

El sistema suma tramos de precio y aplica tasas de impuesto como el 21 %. Un `float` binario no representa exactamente cantidades como 0,1, y los errores de redondeo en dinero se acumulan y se ven en el total. El documento 00 exige precisión al céntimo, probada en los límites 10/11 y 50/51 (§6), y un redondeo definido para el impuesto (RN-5). El principio 4 de la constitución lo recoge como «dinero exacto y trazable».

## Decisión

- Todo importe es un entero en céntimos de euro, en campos terminados en `_cents`, en el dominio, en la API y en la base de datos (`INTEGER` en SQLite) (RN-6, §8.1 del 00).
- Toda tasa es un entero en puntos básicos, en campos terminados en `_bp`: 2100 = 21 %.
- Nunca se usa `float`. Los importes se guardan siempre en EUR y la API devuelve `currency: "EUR"`.
- El subtotal es una suma exacta de productos enteros. El único redondeo es el del impuesto: una sola vez, «mitad hacia arriba» y con aritmética entera, `(subtotal_cents * rate_bp + 5000) // 10000`, en `tax_cents` de `backend/app/domain/tax.py`.

## Alternativa descartada

Importes en euros con `float`: introduce errores de redondeo en sumas y porcentajes. `round()` de Python tampoco sirve para el impuesto, porque redondea 210,5 a 210 (redondeo bancario). `Decimal` sería exacto, pero añade un tipo numérico innecesario cuando los enteros bastan (DT-1 del plan de 001).

## Consecuencias

- Los casos de las tablas de la spec 001 se comprueban al céntimo y dan el mismo resultado en todas las ejecuciones.
- El sufijo `_cents` o `_bp` hace visible la unidad de cada campo, y mypy (ADR 0008) detecta un `float` donde se espera un entero.
- El frontend recibe céntimos y los formatea; convertir a otra divisa es solo presentación (ADR 0005).
- SQLite admite un `REAL` en una columna `INTEGER`; por eso `tax_rates` añade un `CHECK` con `typeof` (ADR 0006).
