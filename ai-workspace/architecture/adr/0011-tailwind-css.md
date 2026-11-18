# ADR 0011 — Tailwind CSS para el diseño del frontend

Estado: aceptado (con la spec 006)

## Contexto

La spec 005 resolvió el frontend con CSS propio y sin bibliotecas (005 RNF-9, plan DT-18). Funciona, pero el aspecto es plano: la caja del alta no está centrada, la ficha no aprovecha el escritorio y no hay animaciones. El autor pidió una interfaz moderna con una biblioteca de estilos y animaciones, y la spec 006 lo concreta. Por el principio 1 de la constitución, toda dependencia nueva necesita un ADR.

Restricciones que salen de 005:

- Sus controles son nativos (campos, desplegables, slider) porque garantizan el teclado, el límite de caracteres e Intro sin código propio (005 DT-10 y DT-11), y sus 319 tests se apoyan en ellos.
- Los tests C usan un reloj falso y un DOM simulado (plan 005, sección 10): nada puede esperar a un fotograma ni a un evento de animación para terminar una navegación o quitar un elemento.

## Decisión

- **Tailwind CSS 4.3.3** con su integración de PostCSS (`@tailwindcss/postcss` 4.3.3 y `postcss` 8.5.31), versiones exactas y solo de desarrollo. La compilación de Angular 22 la usa al detectar `.postcssrc.json`. No añade JavaScript a la aplicación: genera, al compilar, solo el CSS de las clases que aparecen en las plantillas.
- El tema (colores, sombras, curvas de animación) vive en `@theme` de `src/styles.css`. Las clases que ya usan las plantillas (`card`, `button`, `field`…) se definen con `@apply`, y las plantillas usan utilidades de Tailwind para la disposición.
- **Animaciones con CSS propio:** `@keyframes` en `src/styles.css` y clases (`anim-page`, `anim-rise`, `anim-fade`, `anim-expand`, `anim-flash`) que el navegador ejecuta al insertar cada elemento. Los tests comprueban las clases; el navegador real, que las animaciones corren. Todo se anula con `prefers-reduced-motion: reduce`.
- Se eligieron versiones publicadas hace al menos un mes.

## Alternativas descartadas

- **Angular Material:** cambia los controles nativos por los suyos (por ejemplo, el desplegable), con lo que se pierden las garantías nativas de 005 y habría que reescribir sus tests.
- **Bootstrap:** aspecto más anticuado y JavaScript propio en ejecución para componentes que la app no usa.
- **`@angular/animations` y `animate.enter` / `animate.leave` de Angular:** el prototipo mostró que en el DOM simulado de los tests no aplican ninguna clase, así que no se podrían comprobar; y el paquete `@angular/animations` está obsoleto desde Angular 20.2.
- **Transiciones del router (`withViewTransitions`):** el prototipo mostró que cada navegación espera un fotograma que el reloj falso no da, y una decena de tests de 005 se quedaban colgados.
- **Seguir con CSS propio:** no cumple la petición del autor y obliga a escribir a mano lo que Tailwind ya resuelve (escala de espaciado, sombras, estados).

## Consecuencias

- `package.json` gana tres dependencias de desarrollo y el repositorio un `.postcssrc.json`. La compilación de Angular ya traía `postcss` 8.5.33 como dependencia propia, y ahora comparte la 8.5.31: un cambio de parche dentro de la misma versión menor, con la suite y la compilación en verde. El CSS final ocupa 22,1 kB sin comprimir.
- Quien escriba plantillas puede usar las utilidades de Tailwind; los estilos comunes siguen en `src/styles.css`.
- Actualizar Tailwind de versión mayor exige revisar este ADR.
