# ADR 0006 — Tasas de impuesto en una tabla por país

Estado: aceptado

## Contexto

El enunciado exige sumar el impuesto del país del cliente (RN-3), pero no da ninguna tasa (§10 del documento 00, supuesto 4). Los valores adoptados (ES 21 %, PT 23 %, FR 20 %, DE 19 %, IT 22 %, GB 20 % y US 0 %) son supuestos de ejemplo que pueden cambiar, y la lista de países puede crecer (RN-4).

## Decisión

- Las tasas viven en la tabla `tax_rates`: `country` (TEXT, clave primaria) y `rate_bp` (INTEGER, no nulo) (§8.5 del 00).
- Dos `CHECK` protegen los datos: `country` son 2 letras mayúsculas, y `rate_bp` es un entero entre 0 y 10 000. El `typeof` evita que SQLite guarde 21.5 en una columna `INTEGER`. El servicio (`set_tax_rate`) valida además el rango antes de escribir (DT-5 del plan de 001).
- La migración `backend/app/db/migrations/versions/0001_create_tax_rates.py` crea la tabla e inserta las 7 tasas por defecto. Son parte de la preparación de la base de datos, no de los datos de demostración (D-5 de la spec 001).
- Un país está soportado si y solo si tiene tasa; si no, el cálculo devuelve «país no soportado» (422 en la API).
- El dominio recibe la tasa, no el país (ADR 0003). Los tramos de precio no van en tabla: son una constante del dominio.

## Alternativa descartada

Tasas como constante en el código del dominio. Cambiar o añadir un país obligaría a tocar el cálculo y sus tests, justo lo que RN-4 quiere evitar.

## Consecuencias

- Cambiar, añadir o quitar una tasa no toca el cálculo (RNF-3 de la spec 001, casos C-1 a C-6).
- Cada simulación guarda la tasa aplicada (`tax_rate_bp`), así que el histórico no cambia si cambia la tabla (RN-8).
- Cada cotización lee la base de datos una vez; si la fuente de tasas falla, la API responde 500 sin detalles internos (caso O-5 de la spec 002).
- No hay pantalla ni endpoint para editar tasas: se cambian como datos. Las migraciones creadas no se editan, así que cambiar los valores por defecto exige una migración nueva.
