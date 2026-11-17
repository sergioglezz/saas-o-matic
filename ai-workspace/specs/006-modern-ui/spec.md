# 006 — Interfaz moderna: diseño, disposición y animaciones

Estado: v1.0 · Pendiente de la revisión del autor · Fuente de verdad: `ai-workspace/specs/00-spec-first.md` · Constitución: `ai-workspace/docs/constitution.md` · Depende de: spec 005 (aprobada); ADR 0011

Leyenda de origen: **[E]** viene del enunciado; **[P]** es una propuesta (decisiones D-x de la sección 11) o una petición del autor.

## 1. Contexto y objetivo

La spec 005 dejó el frontend completo y probado, pero con un aspecto plano: la caja del alta queda pegada a la izquierda, la ficha apila todo en una columna también en el escritorio, las pantallas no tienen títulos y nada se mueve. El enunciado valora un «frontend fluido (responsive, estados de carga y error de la API externa)» (§9 del 00) **[E]**, y el autor pidió una interfaz moderna, con una biblioteca de estilos y animaciones **[P]**.

**Objetivo:** el mismo frontend de 005, con un diseño moderno basado en Tailwind CSS (ADR 0011), una disposición centrada que aprovecha el ancho disponible, títulos claros y animaciones suaves que señalan lo que cambia, sin alterar ningún texto ni comportamiento de 005.

**Por qué:** el comercial usa la app delante del cliente. Una pantalla ordenada transmite confianza, y una animación breve lleva la vista a lo importante: la tarjeta recién guardada o el total que acaba de cambiar.

**No cambia:** el backend, los contratos de la API, ni los textos, controles, rutas, peticiones y comportamientos de 005.

## 2. Usuarios

- **Comercial:** usa la app en el escritorio y en el móvil.
- **Personas que prefieren reducir el movimiento:** lo indican en su sistema operativo y no deben ver animaciones.

## 3. Historias de usuario

- **HU-1.** Como comercial, quiero que cada pantalla esté centrada y ordenada a cualquier ancho, para leerla de un vistazo.
- **HU-2.** Como comercial, quiero distinguir cada cliente por sus iniciales y su plan, para encontrarlo antes en el listado.
- **HU-3.** Como comercial, quiero que la app me señale lo que acaba de cambiar, para no tener que buscarlo.
- **HU-4.** Como persona sensible al movimiento, quiero que la app no se anime si así lo pido en mi sistema.

## 4. Requisitos funcionales

### RF-1. Tema visual

Origen: petición del autor **[P]**, ADR 0011; D-1 y D-2.

- **CA-1.1** El sistema deberá aplicar en todas las pantallas un mismo tema: fondo gris muy claro, tarjetas blancas con borde fino, sombra suave y esquinas redondeadas, color de marca índigo en las acciones principales y los enlaces, y la tipografía del sistema operativo.
- **CA-1.2** El sistema deberá mantener un contraste de al menos 4,5:1 en todos los textos y de 3:1 en los bordes de los controles.
- **CA-1.3** El sistema deberá mostrar en cada control enfocado con el teclado un anillo de foco del color de marca, separado del control.
- **CA-1.4** El sistema deberá diferenciar en los botones los estados normal, al pasar el ratón, pulsado y desactivado.

### RF-2. Disposición

Origen: petición del autor **[P]** (caja del alta sin centrar), 005 RNF-3 **[E]**; D-3 y D-4.

- **CA-2.1** El sistema deberá centrar horizontalmente el contenido de cada pantalla, con un ancho máximo de 1100 px.
- **CA-2.2** El sistema deberá centrar horizontalmente las tarjetas estrechas, con un ancho máximo de 40 rem: el alta, «Página no encontrada» y «Cliente no encontrado».
- **CA-2.3** El sistema deberá mantener la cabecera visible arriba al desplazarse por la página.
- **CA-2.4** Desde 1024 px de ancho, el sistema deberá mostrar en la ficha la tarjeta del cliente y el simulador en dos columnas, de un tercio y dos tercios del ancho; por debajo de ese ancho, apilados. El historial deberá ir debajo, a todo el ancho.
- **CA-2.5** El sistema deberá seguir cumpliendo 005 RNF-3: ningún desplazamiento horizontal desde 360 px de ancho y, hasta 480 px, el desglose en bloques.

### RF-3. Títulos e identificación

Origen: §3 del 00 **[E]** (buscador, ficha, simulador e historial), 005 RNF-4; D-5 a D-7.

- **CA-3.1** El sistema deberá mostrar en el listado el título T6-CLI «Clientes».
- **CA-3.2** El sistema deberá mostrar en la ficha los títulos de sección T6-SIM «Simulador» y T6-HIS «Historial de simulaciones», y cada sección deberá tener su título como nombre accesible.
- **CA-3.3** El sistema deberá mostrar junto a cada cliente del listado y en la tarjeta de la ficha un círculo con las iniciales de la empresa, oculto a los lectores de pantalla. Las iniciales son la primera letra de cada una de las dos primeras palabras que tienen alguna letra; si solo una palabra tiene letras, sus dos primeras letras; si ninguna, «#». Siempre en mayúsculas.
- **CA-3.4** El sistema deberá mostrar el plan como una etiqueta de color distinto para cada uno, con el texto de 005 («Starter», «Business» o «Enterprise»).
- **CA-3.5** El sistema deberá mostrar iconos decorativos (buscar, nuevo, volver, éxito, error y actualizar) sin texto y ocultos a los lectores de pantalla, de modo que los textos y nombres accesibles de 005 no cambian.

### RF-4. Estados de carga

Origen: §9 del 00 **[E]** (estados de carga), 005 CA-6.7, CA-9.2 y CA-10.4; D-8.

- **CA-4.1** Mientras cargan el listado, la ficha o el historial, el sistema deberá mostrar, además del texto de carga de 005, marcadores con la forma del contenido que va a aparecer (esqueletos), con un brillo que los recorre y ocultos a los lectores de pantalla.
- **CA-4.2** El sistema deberá mostrar T-UPD «Actualizando…» acompañado de un icono que gira.

### RF-5. Animaciones

Origen: petición del autor **[P]**; D-9 a D-12.

- **CA-5.1** Cuando se abre una pantalla, el sistema deberá mostrar su contenido con un fundido y un desplazamiento vertical de 8 px, en menos de 300 ms.
- **CA-5.2** Cuando aparecen las tarjetas de clientes o de simulaciones, el sistema deberá animarlas una tras otra, cada una 45 ms después de la anterior y con un retraso máximo de 450 ms.
- **CA-5.3** Cuando aparece un aviso (T-REG, T-SOK, los errores de RF-2 de 005 y los avisos de tasas), el sistema deberá mostrarlo con un fundido.
- **CA-5.4** Cuando se despliega el desglose de una simulación del historial, el sistema deberá mostrarlo con un fundido y un desplazamiento vertical.
- **CA-5.5** Cuando llega una cotización nueva con respuesta 200, el sistema deberá resaltar los totales del simulador con un destello de fondo de menos de 1 s. Al cambiar solo la divisa, no.
- **CA-5.6** Al pasar el ratón por un cliente del listado, el sistema deberá elevar su tarjeta con una transición; al pulsar un botón, deberá reducirlo ligeramente.
- **CA-5.7** Si el sistema operativo pide reducir el movimiento (`prefers-reduced-motion: reduce`), el sistema no deberá animar nada: animaciones y transiciones instantáneas, también la de los esqueletos y el icono que gira.
- **CA-5.8** El sistema no deberá esperar a ninguna animación para responder: los controles funcionan desde que aparecen, y ningún comportamiento de 005 depende de una animación.

### RF-6. Compatibilidad con 005

Origen: spec 005 aprobada; D-13.

- **CA-6.1** El sistema deberá mantener todos los textos, controles, rutas, peticiones y comportamientos de 005: sus 319 tests deberán pasar sin modificarlos.

## 5. Contrato observable

### 5.1 Textos nuevos

Se suman a la tabla 5.6 de 005.

| ID | Texto | Dónde |
| --- | --- | --- |
| T6-CLI | Clientes | Título del listado |
| T6-SIM | Simulador | Título de la sección del simulador |
| T6-HIS | Historial de simulaciones | Título de la sección del historial |

### 5.2 Clases de animación

Son el contrato entre las plantillas y la hoja de estilos, y lo que comprueban los tests C.

| Clase | Dónde | Animación |
| --- | --- | --- |
| `anim-page` | Raíz de cada pantalla | Fundido y 8 px hacia arriba |
| `anim-rise` | Cada tarjeta de cliente o de simulación, con la variable `--i` igual a su posición en la lista | Igual, con retraso de `min(--i, 10) × 45 ms` |
| `anim-fade` | Cada aviso de CA-5.3 | Fundido |
| `anim-expand` | Desglose desplegado del historial | Fundido y desplazamiento |
| `anim-flash` | Bloque de totales del simulador | Destello de fondo; el bloque se vuelve a crear con cada cotización nueva |
| `skeleton` | Cada marcador de carga | Brillo que recorre el marcador |

### 5.3 Paleta

| Uso | Color | Contraste |
| --- | --- | --- |
| Texto | `#0f172a` sobre blanco y sobre `#f8fafc` | 17,9:1 y 17,1:1 |
| Texto secundario | `#475569` | 7,6:1 y 7,2:1 |
| Botón principal | Blanco sobre `#4f46e5` | 6,3:1 |
| Enlaces | `#4338ca` | 7,9:1 y 7,6:1 |
| Error, aviso y éxito | `#b91c1c`, `#92400e` y `#047857`, también sobre sus fondos claros | De 5,2:1 a 7,1:1 |
| Etiquetas de plan | Starter `#334155` sobre `#f1f5f9`; Business `#3730a3` sobre `#eef2ff`; Enterprise `#5b21b6` sobre `#f5f3ff` | 9,5:1, 8,9:1 y 8,2:1 |
| Iniciales | `#4338ca` sobre `#e0e7ff` | 6,4:1 |
| Borde de los controles | `#64748b` | 4,8:1 |

## 6. Casos de prueba

Niveles: **U** = función pura; **C** = pantalla en el DOM simulado, como en 005; **M** = comprobación en un navegador real con el backend y el seed.

### 6.1 Iniciales · U

| # | Entrada | Salida |
| --- | --- | --- |
| IN-1 | «Acme Telecom S.L.» | «AT» |
| IN-2 | «Estudio Lucía Ferrer» | «EL» |
| IN-3 | «pepeviyuela» | «PE» |
| IN-4 | «Ñandú Redes» | «ÑR» |
| IN-5 | «3M España» | «ME» (la primera letra de «3M» es la M) |
| IN-6 | «123 456» y la cadena vacía | «#» |
| IN-7 | «<b>Acme</b>» | «BA» (texto literal, una sola palabra) |

### 6.2 Disposición y títulos · C

| # | Situación | Resultado esperado |
| --- | --- | --- |
| LY-1 | Abrir `/clientes` | Título h1 «Clientes»; la pantalla tiene `anim-page` |
| LY-2 | Abrir `/clientes/nuevo` y una dirección desconocida | La tarjeta tiene las clases de tarjeta estrecha centrada |
| LY-3 | Ficha de Acme con 404 | La tarjeta T-NFC es estrecha y centrada |
| LY-4 | Ficha de Acme cargada | Secciones con títulos h2 «Simulador» e «Historial de simulaciones», y cada sección con `aria-labelledby` hacia su título |
| LY-5 | Ficha de Acme cargada | Rejilla de dos columnas desde 1024 px con la tarjeta y el simulador; el historial fuera de ella |
| LY-6 | Listado con Acme (`business`) y clientes `starter` y `enterprise` | Cada plan en una etiqueta con la clase de su plan; textos de 005 iguales |
| LY-7 | Listado y ficha de Acme | Círculo «AT» oculto a los lectores de pantalla (`aria-hidden`) |
| LY-8 | Cualquier pantalla | Ningún icono tiene texto; todos son `aria-hidden` |

### 6.3 Carga · C

| # | Situación | Resultado esperado |
| --- | --- | --- |
| SK-1 | Listado esperando respuesta | T-LCL y al menos 3 esqueletos `aria-hidden`; al llegar la respuesta, ninguno |
| SK-2 | Ficha esperando respuesta | T-LCU y esqueletos; al llegar, ninguno |
| SK-3 | Historial esperando respuesta | T-LHI y esqueletos; al llegar, ninguno |
| SK-4 | Cotización en curso | T-UPD con un icono `spin` oculto a los lectores de pantalla |

### 6.4 Animaciones · C

| # | Situación | Resultado esperado |
| --- | --- | --- |
| AN-1 | Listado con 3 clientes | Cada tarjeta con `anim-rise` y `--i` 0, 1 y 2 |
| AN-2 | «Cargar más» con 50 mostrados | Las nuevas tarjetas siguen con `--i` 50, 51… (la hoja limita el retraso) |
| AN-3 | Historial con 3 simulaciones | Cada tarjeta con `anim-rise` y su `--i` |
| AN-4 | T-REG, T-SOK, T-CON del listado y T-RNO | Cada aviso con `anim-fade` |
| AN-5 | «Ver desglose» | La tabla desplegada dentro de un bloque con `anim-expand` |
| AN-6 | Cotización de 15 y después de 60 | El bloque de totales tiene `anim-flash` y es un elemento nuevo tras la de 60 |
| AN-7 | Cotización de 15 y cambio a USD | El bloque de totales es el mismo elemento (sin nuevo destello) |

### 6.5 Regresión · C

| # | Situación | Resultado esperado |
| --- | --- | --- |
| RG-1 | Los 319 tests de 005 | Pasan sin modificarlos |

### 6.6 Comprobaciones manuales · M

| # | Comprobación | Resultado esperado |
| --- | --- | --- |
| MA-1 | Alta, «Página no encontrada» y «Cliente no encontrado» a 1280 px | Márgenes izquierdo y derecho iguales (±1 px) |
| MA-2 | Ficha a 1280 px y a 768 px | Dos columnas a 1280 px; apilada a 768 px |
| MA-3 | Todas las pantallas a 360 px, con JPY y desgloses abiertos | Sin desplazamiento horizontal |
| MA-4 | Abrir el listado y la ficha | Las animaciones corren (`animationName` distinto de `none` en las tarjetas) |
| MA-5 | Con «reducir movimiento» del sistema | Ninguna animación ni transición visible; la regla está en el CSS |
| MA-6 | Contraste con los colores aplicados | Los de la tabla 5.3 |
| MA-7 | Desplazarse por la ficha | La cabecera sigue visible |

## 7. Requisitos no funcionales

- **RNF-1 Sin JavaScript nuevo en ejecución:** Tailwind solo actúa al compilar (ADR 0011).
- **RNF-2 Peso:** el CSS final no supera los 40 kB sin comprimir; los presupuestos de `angular.json` no cambian.
- **RNF-3 Calidad:** TypeScript estricto, lint sin errores, archivos de menos de 300 líneas y funciones de menos de 40.
- **RNF-4 Accesibilidad:** la de 005 RNF-4, más CA-1.2, CA-1.3, CA-3.5 y CA-5.7.

## 8. Casos límite

- Nombres sin letras, con letras acentuadas o con aspecto de HTML (IN-4 a IN-7).
- Muchas tarjetas: el retraso se limita a 450 ms, aunque haya cientos (AN-2).
- Cambio de divisa: convierte sin destello (AN-7).
- Reducir movimiento: también los esqueletos y el icono que gira (MA-5).

## 9. Fuera de alcance

- Modo oscuro, tipografías descargadas y temas que elija el usuario.
- Bibliotecas de componentes que cambien los controles nativos de 005.
- Transiciones entre pantallas del router y animaciones de salida.
- Cualquier cambio de texto, comportamiento, ruta o petición de 005, y del backend.

## 10. Criterios de finalización

- [ ] Cada caso U y C de las tablas 6.1 a 6.5 tiene un test que lo cita y pasa.
- [ ] Los 319 tests de 005 pasan sin modificarlos.
- [ ] MA-1 a MA-7 comprobados en un navegador real y anotados en `tasks.md`.
- [ ] Lint y compilación de producción sin errores ni avisos; CSS final por debajo de 40 kB.
- [ ] ADR 0011 redactado; dependencias con versión exacta.
- [ ] Ninguna dependencia fuera de las del ADR 0011.

## 11. Decisiones

Todas son **[P]**.

- **D-1. Tailwind CSS 4** (ADR 0011): moderno, sin JavaScript en ejecución y compatible con los controles nativos de 005.
- **D-2. Tema índigo sobre grises pizarra**, con la tipografía del sistema: contraste comprobado (5.3) y sin descargar fuentes.
- **D-3. Tarjetas estrechas centradas** (40 rem): resuelve la caja del alta sin centrar que señaló el autor.
- **D-4. Ficha en dos columnas desde 1024 px:** en el escritorio, el simulador queda a la vista junto a los datos del cliente.
- **D-5. Tres títulos nuevos** (5.1): el listado y las secciones de la ficha no tenían título, y los lectores de pantalla navegan por títulos.
- **D-6. Iniciales en un círculo:** identifican cada cliente sin imágenes ni peticiones.
- **D-7. Iconos propios en SVG**, dibujados en el proyecto: sin otra dependencia.
- **D-8. Esqueletos además del texto de carga:** muestran la forma de lo que llega; el texto de 005 sigue para los lectores de pantalla.
- **D-9. Animaciones con CSS propio y clases** (5.2), no con las de Angular ni con las transiciones del router: el prototipo de la ADR 0011 mostró que unas no se pueden comprobar en los tests y las otras cuelgan sus navegaciones.
- **D-10. Duraciones cortas** (200 a 320 ms, el destello 900 ms) y un retraso escalonado limitado a 450 ms: se ven sin hacer esperar.
- **D-11. Destello de los totales al llegar cada cotización**, no al cambiar de divisa: señala un cambio de precio, no de presentación.
- **D-12. Reducir movimiento lo anula todo**, también los esqueletos y el icono que gira.
- **D-13. 005 no cambia:** sus tests son la red de seguridad del rediseño.

## 12. Historial de cambios

| Versión | Cambio |
| --- | --- |
| 1.0 | Versión inicial, tras un prototipo con Tailwind 4 y las animaciones de Angular 22 (ADR 0011) |
