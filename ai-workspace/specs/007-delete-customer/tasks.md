# Tareas — 007 Borrar cliente

Estado: v1.0 ejecutadas, revisadas y aprobadas por el autor · Spec: `spec.md` v1.0 (aprobada) · Plan: `plan.md` v1.0

## Reglas de ejecución

- Una tarea cada vez, con el ciclo rojo → verde → revisar.
- **Verificación:** backend con `pytest`, `ruff check .`, `ruff format --check .` y `mypy .`; frontend con `npm test`, `npm run lint` y `npm run build`.
- Sin commits sin la autorización del autor.

## Progreso

| Tareas | RF | Estado |
| --- | --- | --- |
| T-01 a T-04 | RF-1 y RF-2 | ✅ Completadas |

## Tareas

- [x] **T-01. Borrado en el servicio y los repositorios**
  - **RF:** RF-1 (CA-1.1, CA-1.2, CA-1.4, CA-1.8). Plan DT-1 y DT-2. **Casos:** BR-8 y BR-11.
  - **Hecho cuando:** esos casos pasan y la suite del backend sigue en verde.
  - **Resultado:** `test_customer_deletion.py` con 5 tests en verde; suite completa, ruff y mypy en verde.

- [x] **T-02. Ruta `DELETE /customers/{id}`, CORS y documentación**
  - **RF:** RF-1 (CA-1.1 a CA-1.7). **Casos:** BR-1 a BR-7, BR-9 y BR-10; ER-3 de 003 actualizado.
  - **Hecho cuando:** esos casos pasan, con ruff y mypy en verde.
  - **Resultado:** `test_customers_delete.py` con 14 tests en verde. ER-3 de 003 y ER-10 de 004 actualizados (plan §4). Backend: 1069 tests, ruff y mypy en verde.

- [x] **T-03. Borrar desde la ficha**
  - **RF:** RF-2. Plan DT-3 y DT-4. **Casos:** BF-1 a BF-9.
  - **Hecho cuando:** esos casos pasan y la suite del frontend sigue en verde, con lint y compilación.
  - **Resultado:** `delete-customer.spec.ts` con 13 tests en verde (BF-1 a BF-9 y CA-2.9). Frontend: 365 tests, lint y compilación en verde.

- [x] **T-04. Comprobación real y documentación**
  - **Casos:** MA-1 y MA-2. README: el borrado en las decisiones del frontend y fuera de alcance actualizado.
  - **Hecho cuando:** MA-1 y MA-2 comprobados y anotados aquí.
  - **Resultado:** backend y frontend reales en marcha, con la base de datos del seed, en el navegador integrado. Se usaron dos clientes de demostración con solo la simulación del seed, para poder restaurarlos después.
    - **MA-1 ✅** Ficha de Nordwind Systeme GmbH: la confirmación dice «Se borrará también su simulación.». Con «Sí, borrar», se abre `/clientes` con «Cliente «Nordwind Systeme GmbH» borrado» y 9 clientes. Su ficha da «Cliente no encontrado», la API responde 404 al cliente y a su historial, y al volver al listado el aviso ya no está.
    - **MA-2 ✅** Ficha de Lusitânia Cloud Lda, solo con teclado. Tab llega a «Borrar cliente» con el foco visible e Intro abre la confirmación con el foco dentro. Tab pasa a «Sí, borrar» (anillo de foco visible) e Intro borra: listado con «Cliente «Lusitânia Cloud Lda» borrado» y sin el cliente. Antes, con Acme, Escape y «Cancelar» cerraron la confirmación y devolvieron el foco al botón; la cifra del aviso era la real («sus 3 simulaciones»), y a 360 px no había desplazamiento horizontal.
    - **Restauración:** `python -m app.db.seed` volvió a crear los dos clientes con su simulación. Les dio los ids 13 y 14, no los antiguos: el `id` no se reutiliza (CA-1.5).
  - README con la sección «Borrar clientes (spec 007)», que explica de dónde salió la funcionalidad, y con los «fuera de alcance» de 003 y 004 corregidos.
