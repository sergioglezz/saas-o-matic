# Tareas — 006 Interfaz moderna

**Estado:** ✅ todas las tareas completadas y revisadas por el autor · **Spec:** [spec.md](spec.md) v1.0 · **Plan:** [plan.md](plan.md)

## Reglas de ejecución

- Una tarea cada vez, en orden, con el ciclo rojo → verde → revisar de 005.
- **Verificación completa** (desde `frontend/`): `npm test` con los 319 tests de 005 sin modificar, `npm run lint` y `npm run build` sin errores ni avisos.
- Archivos de menos de 300 líneas y funciones de menos de 40. Sin commits sin la autorización del autor.

## Progreso

| Tareas | RF | Estado |
| --- | --- | --- |
| T-01 a T-04 | RF-1 a RF-6 | ✅ Completadas: 352 tests en verde (los 319 de 005 sin modificar y 33 nuevos: IN-1 a IN-7, LY-1 a LY-8, SK-1 a SK-4 y AN-1 a AN-7), lint sin errores y compilación sin avisos; CSS final de 22,1 kB. Cada tarea empezó en rojo. Fallos corregidos: entradas 41 y 42 del log |
| T-05 | Todos | ✅ Completada: MA-1 a MA-7 comprobados en el navegador integrado, con el backend y el frontend reales |

## Tareas

- [x] **T-01. Tailwind y tema**
  - **RF:** RF-1, RF-6. ADR 0011; plan DT-1. **Casos:** RG-1.
  - **Archivos:** `.postcssrc.json`, `package.json`, `src/styles.css`.
  - **Hecho cuando:** las clases comunes tienen el tema nuevo, los 319 tests pasan sin tocarlos y el CSS final está por debajo de 40 kB.

- [x] **T-02. Disposición, títulos, iniciales, etiquetas e iconos**
  - **RF:** RF-2, RF-3. Plan DT-6 a DT-8. **Casos:** IN-1 a IN-7, LY-1 a LY-8.
  - **Archivos:** `shared/format/initials.ts`, `shared/ui/icon.ts`, `shared/texts.ts`, plantillas, `initials.spec.ts` y `ui-layout.spec.ts`.
  - **Hecho cuando:** esos casos pasan, y también los 319 de 005.

- [x] **T-03. Esqueletos de carga**
  - **RF:** RF-4. **Casos:** SK-1 a SK-4.
  - **Archivos:** `shared/ui/skeleton-cards.ts`, plantillas del listado, la ficha, el historial y el simulador, y `ui-loading.spec.ts`.
  - **Hecho cuando:** esos casos pasan, y también los 319 de 005.

- [x] **T-04. Animaciones**
  - **RF:** RF-5. Plan DT-2 a DT-5. **Casos:** AN-1 a AN-7.
  - **Archivos:** `src/styles/motion.css`, plantillas y `ui-motion.spec.ts`.
  - **Hecho cuando:** esos casos pasan, y también los 319 de 005.

- [x] **T-05. Comprobación en el navegador y cierre**
  - **RF:** todos. **Casos:** MA-1 a MA-7.
  - **Comprobación:** backend con el seed y frontend con `npm start`, en el navegador integrado a 360, 768 y 1280 px; resultados anotados aquí; README con Tailwind en la sección del frontend; criterios de la sección 10 de la spec marcados.
  - **Resultado:**
    - **MA-1 ✅** Alta, «Página no encontrada» y «Cliente no encontrado» a 1280 px: 320 px de margen a cada lado en las tres.
    - **MA-2 ✅** Ficha a 1280 px: los datos y el simulador en dos columnas, a la misma altura. A 768 px, uno debajo del otro.
    - **MA-3 ✅** Listado, alta, ficha, «Página no encontrada» y «Cliente no encontrado» a 360 px. La ficha se probó con JPY y los tres desgloses del historial abiertos. En ninguna pantalla hay desplazamiento horizontal, y la tabla de tramos se muestra en bloques con sus etiquetas.
    - **MA-4 ✅** Listado y ficha: la página y las tarjetas tienen `animationName` `rise-in`.
    - **MA-5 ✅** La regla de `prefers-reduced-motion` está en el CSS servido. El navegador integrado no permite activar esa opción del sistema, así que se aplicó el contenido de la regla sin su condición: animaciones y transiciones pasan a 1 ms (sin ella duran 320 ms y 150 ms).
    - **MA-6 ✅** Contraste medido con los colores aplicados, iguales a la tabla 5.3:
      - texto 17,9:1 y 17,1:1; texto secundario 7,6:1 y 7,2:1;
      - botón 6,3:1; enlaces 7,9:1 y 7,6:1;
      - error 6,5:1 y 5,9:1, aviso 7,1:1 y 6,8:1, éxito 5,5:1 y 5,2:1;
      - etiquetas de plan 9,5:1, 8,9:1 y 8,2:1; iniciales 6,4:1; borde de los controles 4,8:1.
    - **MA-7 ✅** Al bajar hasta el final de la ficha, la cabecera (`sticky`) sigue arriba del todo.
  - **RNF-3:** `styles.css` tenía 307 líneas. Las tablas pasaron a `src/styles/tables.css`, importado como `motion.css`, y ahora tiene 268. El CSS final mide lo mismo (22,2 kB).
  - **Verificación final:** 365 tests (los 352 de la 006 más los 13 de la 007), lint y compilación en verde. README con Tailwind en la sección del frontend.
  - **Hecho cuando:** MA-1 a MA-7 cumplidos y la verificación completa en verde.
