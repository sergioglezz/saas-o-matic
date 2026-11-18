# Plan técnico — 006 Interfaz moderna

**Estado:** ✅ ejecutado y revisado por el autor · **Spec:** [spec.md](spec.md) v1.0 · **Se apoya en:** el plan 005, el ADR 0011 y el frontend de 005, sin cambiar su comportamiento

## 1. Resumen y alcance

- **Construye:** Tailwind CSS en la compilación, el tema y los estilos comunes, la disposición nueva, los títulos, las iniciales, las etiquetas de plan, los iconos, los esqueletos de carga y las animaciones.
- **Cubre:** RF-1 a RF-6 y RNF-1 a RNF-4 de la spec 006.
- **No toca:** la lógica, los servicios, los textos y los tests de 005, ni el backend.
- **Dependencias:** `tailwindcss` 4.3.3, `@tailwindcss/postcss` 4.3.3 y `postcss` 8.5.31, solo de desarrollo y con versión exacta (ADR 0011).

## 2. Archivos

| Archivo | Cambio | RF |
| --- | --- | --- |
| `frontend/.postcssrc.json` | Nuevo: activa `@tailwindcss/postcss` en la compilación de Angular | 1 |
| `frontend/package.json` y `package-lock.json` | Las tres dependencias de desarrollo | 1 |
| `src/styles.css` | `@import "tailwindcss"`, el tema (`@theme`), la base y las clases comunes con `@apply` (`card`, `narrow`, `button`, `field`, `badge`, `avatar`, `notice`…) | 1, 2, 3 |
| `src/styles/motion.css` | Nuevo: `@keyframes`, las clases de 5.2 y la regla de reducir movimiento | 4, 5 |
| `src/styles/tables.css` | Nuevo en T-05: las tablas de tramos, sacadas de `styles.css` para que no pase de 300 líneas (RNF-3) | 2 |
| `shared/format/initials.ts` | Nuevo, puro: `initials(name)` | 3 |
| `shared/ui/icon.ts` | Nuevo: `app-icon` con un juego fijo de iconos SVG propios, siempre `aria-hidden` | 3 |
| `shared/ui/skeleton-cards.ts` | Nuevo: `app-skeleton-cards`, N marcadores con forma de tarjeta, `aria-hidden` | 4 |
| `shared/texts.ts` | Los textos T6 de 5.1 | 3 |
| Plantillas de `app`, `currency-bar`, listado, alta, ficha, simulador, historial, tarjeta, avisos, «Cargar más» y no encontrada | Clases de Tailwind para la disposición, títulos, iniciales, etiquetas, iconos, esqueletos y clases de animación | 2 a 5 |
| CSS de cada componente | Se vacían o se reducen: los estilos pasan al tema | 1 |

## 3. Decisiones técnicas

| # | Decisión | Por qué | RF |
| --- | --- | --- | --- |
| DT-1 | Clases comunes con `@apply` en `styles.css`, utilidades en las plantillas solo para la disposición | Las plantillas cambian poco, los tests de 005 se apoyan en su estructura, y el tema queda en un solo sitio | 1 |
| DT-2 | Animaciones de entrada con CSS al insertar el elemento | Corren en el navegador sin código; en los tests no hacen nada y se comprueban por sus clases (prototipo del ADR 0011) | 5 |
| DT-3 | Retraso escalonado con la variable `--i` y `min(var(--i), 10)` en la hoja | La plantilla solo pone la posición; el límite de 450 ms vive en un solo sitio | 5 |
| DT-4 | Destello de los totales volviendo a crear su bloque con cada cotización: `@for (quote of [flow.quote()]; track quote)` | Una animación CSS solo se repite si el elemento es nuevo; la divisa no cambia el objeto de la cotización (AN-7) | 5 |
| DT-5 | Reducir movimiento con una sola regla global que deja animaciones y transiciones en 1 ms | Cubre también lo que se añada después, sin repetirlo en cada clase | 5 |
| DT-6 | Iconos en un componente con sus trazos SVG, sin texto | Cero dependencias; `textContent` y nombres accesibles de 005 no cambian | 3 |
| DT-7 | Tarjetas estrechas con `mx-auto` y `max-w-[40rem]` en la clase `narrow` | Corrige el centrado del alta y de las otras dos tarjetas a la vez | 2 |
| DT-8 | Cabecera `sticky` con fondo translúcido y desenfoque | Siempre visible sin tapar el contenido | 2 |

## 4. Estrategia de tests

- **U:** `initials.spec.ts` (IN-1 a IN-7).
- **C**, con los mismos ayudantes de 005: `ui-layout.spec.ts` (LY), `ui-loading.spec.ts` (SK) y `ui-motion.spec.ts` (AN).
- **Regresión:** los 319 tests de 005, sin modificarlos, en cada tarea.
- **M:** MA-1 a MA-7 en el navegador integrado, con el backend y el seed, midiendo con el propio navegador (márgenes, `animationName`, anchura del documento).

## 5. Trazabilidad

| RF | Casos |
| --- | --- |
| RF-1 | MA-6, RG-1 y revisión |
| RF-2 | LY-2, LY-3, LY-5, MA-1 a MA-3, MA-7 |
| RF-3 | LY-1, LY-4, LY-6 a LY-8, IN-1 a IN-7 |
| RF-4 | SK-1 a SK-4 |
| RF-5 | AN-1 a AN-7, MA-4, MA-5 |
| RF-6 | RG-1 |

## 6. Cumplimiento de la constitución

1. **Simplicidad:** tres dependencias de desarrollo con su ADR; ninguna en ejecución.
2. **La spec manda:** cada tarea cita sus RF y casos.
3. **Capas:** nada cambia en `core/`; `initials` es puro y lo vigila el lint.
4. **Dinero:** no cambia; el frontend sigue sin calcular importes.
5. **Tests:** primero los nuevos casos en rojo; la suite de 005 como red de seguridad.
6. **Calidad e idioma:** lint, tipado estricto y textos en español.
