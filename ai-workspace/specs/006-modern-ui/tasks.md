# Tareas — 006 Interfaz moderna

Estado: v1.0, pendiente de la revisión del autor junto con la spec y el plan · Spec: `spec.md` v1.0 · Plan: `plan.md` v1.0

## Reglas de ejecución

- Una tarea cada vez, en orden, con el ciclo rojo → verde → revisar de 005.
- **Verificación completa** (desde `frontend/`): `npm test` con los 319 tests de 005 sin modificar, `npm run lint` y `npm run build` sin errores ni avisos.
- Archivos de menos de 300 líneas y funciones de menos de 40. Sin commits sin la autorización del autor.

## Progreso

| Tareas | RF | Estado |
| --- | --- | --- |
| T-01 a T-05 | RF-1 a RF-6 | Pendiente |

## Tareas

- [ ] **T-01. Tailwind y tema**
  - **RF:** RF-1, RF-6. ADR 0011; plan DT-1. **Casos:** RG-1.
  - **Archivos:** `.postcssrc.json`, `package.json`, `src/styles.css`.
  - **Hecho cuando:** las clases comunes tienen el tema nuevo, los 319 tests pasan sin tocarlos y el CSS final está por debajo de 40 kB.

- [ ] **T-02. Disposición, títulos, iniciales, etiquetas e iconos**
  - **RF:** RF-2, RF-3. Plan DT-6 a DT-8. **Casos:** IN-1 a IN-7, LY-1 a LY-8.
  - **Archivos:** `shared/format/initials.ts`, `shared/ui/icon.ts`, `shared/texts.ts`, plantillas, `initials.spec.ts` y `ui-layout.spec.ts`.
  - **Hecho cuando:** esos casos pasan, y también los 319 de 005.

- [ ] **T-03. Esqueletos de carga**
  - **RF:** RF-4. **Casos:** SK-1 a SK-4.
  - **Archivos:** `shared/ui/skeleton-cards.ts`, plantillas del listado, la ficha, el historial y el simulador, y `ui-loading.spec.ts`.
  - **Hecho cuando:** esos casos pasan, y también los 319 de 005.

- [ ] **T-04. Animaciones**
  - **RF:** RF-5. Plan DT-2 a DT-5. **Casos:** AN-1 a AN-7.
  - **Archivos:** `src/styles/motion.css`, plantillas y `ui-motion.spec.ts`.
  - **Hecho cuando:** esos casos pasan, y también los 319 de 005.

- [ ] **T-05. Comprobación en el navegador y cierre**
  - **RF:** todos. **Casos:** MA-1 a MA-7.
  - **Comprobación:** backend con el seed y frontend con `npm start`, en el navegador integrado a 360, 768 y 1280 px; resultados anotados aquí; README con Tailwind en la sección del frontend; criterios de la sección 10 de la spec marcados.
  - **Hecho cuando:** MA-1 a MA-7 cumplidos y la verificación completa en verde.
