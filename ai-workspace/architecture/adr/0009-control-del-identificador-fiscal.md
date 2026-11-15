# ADR 0009 — Control del identificador fiscal español

Estado: aceptado por delegación del autor, pendiente de su revisión

## Contexto

El enunciado exige validar de forma estricta el identificador fiscal con «el algoritmo oficial de control» cuando el país es España (RN-10). Para el DNI y el NIE el cálculo es público y único. Para el CIF, la AEAT no publica el método ni qué entidades llevan dígito o letra de control, y los NIF especiales `K`, `L` y `M` tampoco tienen método publicado (§7.4 y supuesto 7 de §10 del documento 00).

## Decisión

- **DNI:** 8 dígitos y una letra, la de la posición (número mod 23) en `TRWAGMYFPDXBNJZSQVHLCKE`.
- **NIE:** `X`, `Y` o `Z`, 7 dígitos y una letra; se sustituye `X`→0, `Y`→1 y `Z`→2 y se aplica el cálculo del DNI.
- **CIF:** letra de entidad de `ABCDEFGHJNPQRSUVW`, 7 dígitos y un control.
  - Dígito de control = (10 − (A + B) mod 10) mod 10, con A = suma de los dígitos en posición par y B = suma de las cifras del doble de cada dígito en posición impar. Su letra equivalente es la de esa posición en `JABCDEFGHI`.
  - Tipo de control según la entidad, con la convención más extendida entre validadores ([LookupTax](https://lookuptax.com/docs/tax-identification-number/spain-tax-id-guide)): letra para `N`, `P`, `Q`, `R`, `S` y `W`; dígito para `A`, `B`, `E` y `H`; cualquiera de los dos para el resto.
- **NIF `K`, `L` y `M`:** se rechazan con «Tipo de identificador no soportado».
- El identificador se normaliza antes de validarlo y se guarda normalizado (RN-11): mayúsculas, sin espacios, guiones ni puntos.
- El algoritmo vive en `backend/app/domain/tax_id.py`, como Python puro (ADR 0003), y sus casos son las tablas 6.1 y 6.2 de la spec 003.

## Alternativa descartada

- Aceptar dígito o letra para cualquier entidad del CIF: más simple, pero daría por buenos identificadores que los validadores habituales rechazan (por ejemplo, una entidad `N` con dígito).
- Usar una biblioteca de validación de identificadores: sería una dependencia nueva para unas 60 líneas de código, contra el principio 1 de la constitución.
- Inventar un control para `K`, `L` y `M`: se validaría con una regla sin respaldo.

## Consecuencias

- Los casos de §7.4 del 00 se cumplen al carácter y se prueban sin base de datos ni servidor.
- Un cliente real con un NIF `K`, `L` o `M` no se puede registrar con país España; se documenta en el README como límite conocido.
- Si la convención del CIF resultara distinta para alguna entidad, el cambio es una tabla en un único módulo.
- Fuera de España solo se comprueba el formato básico (de 5 a 20 letras o dígitos); no se valida el control de ningún otro país.
