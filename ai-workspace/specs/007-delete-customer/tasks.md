# Tareas — 007 Borrar cliente

Estado: v1.0, pendiente de la revisión del autor junto con la spec y el plan · Spec: `spec.md` v1.0 · Plan: `plan.md` v1.0

## Reglas de ejecución

- Una tarea cada vez, con el ciclo rojo → verde → revisar.
- **Verificación:** backend con `pytest`, `ruff check .`, `ruff format --check .` y `mypy .`; frontend con `npm test`, `npm run lint` y `npm run build`.
- Sin commits sin la autorización del autor.

## Progreso

| Tareas | RF | Estado |
| --- | --- | --- |
| T-01 a T-04 | RF-1 y RF-2 | Pendiente |

## Tareas

- [ ] **T-01. Borrado en el servicio y los repositorios**
  - **RF:** RF-1 (CA-1.1, CA-1.2, CA-1.4, CA-1.8). Plan DT-1 y DT-2. **Casos:** BR-8 y BR-11.
  - **Hecho cuando:** esos casos pasan y la suite del backend sigue en verde.

- [ ] **T-02. Ruta `DELETE /customers/{id}`, CORS y documentación**
  - **RF:** RF-1 (CA-1.1 a CA-1.7). **Casos:** BR-1 a BR-7, BR-9 y BR-10; ER-3 de 003 actualizado.
  - **Hecho cuando:** esos casos pasan, con ruff y mypy en verde.

- [ ] **T-03. Borrar desde la ficha**
  - **RF:** RF-2. Plan DT-3 y DT-4. **Casos:** BF-1 a BF-9.
  - **Hecho cuando:** esos casos pasan y la suite del frontend sigue en verde, con lint y compilación.

- [ ] **T-04. Comprobación real y documentación**
  - **Casos:** MA-1 y MA-2. README: el borrado en las decisiones del frontend y fuera de alcance actualizado.
  - **Hecho cuando:** MA-1 y MA-2 comprobados y anotados aquí.
