# 005 — Frontend: dashboard, simulador y divisas

**Estado:** ✅ completada (v1.2) · **Depende de:** specs [002](../002-pricing-quote-api/spec.md), [003](../003-customers/spec.md) y [004](../004-simulations/spec.md), y ADR 0004, 0005 y 0007 · **Fuentes:** [00-spec-first](../00-spec-first.md) y [constitución](../../docs/constitution.md)

Leyenda de origen: **[E]** viene del enunciado y no se puede contradecir; **[P]** es una propuesta del documento 00, una respuesta del autor a las preguntas previas (P-1 a P-5) o una decisión tomada al redactar esta spec (D-x). Las respuestas y las decisiones están en la sección 11.

## 1. Contexto y objetivo

El backend ya calcula, guarda y devuelve en EUR los clientes, las cotizaciones y las simulaciones (specs 001 a 004). Falta la interfaz con la que el comercial hace sus tres acciones (§2 del 00): registrar un cliente, simular y guardar, y consultar clientes e historial en la divisa que quiera.

El enunciado pide un dashboard web con buscador y listado de clientes, una ficha con tarjetas responsive y el historial de simulaciones, un simulador interactivo que proyecte la factura mensual en tiempo real y en la divisa elegida, y estados de carga y error de la API externa de tipos de cambio **[E]**. Lo resume en un «frontend fluido (responsive, estados de carga y error de la API externa)» (§9 del 00).

**Objetivo:** un dashboard que consume la API de 002 a 004 sin calcular ningún importe (ADR 0004) y que solo convierte, para mostrarlos, los importes en EUR a la divisa elegida, con las tasas de `open.er-api.com`, caché y vuelta a EUR (RN-7, ADR 0005). Cubre UC-1 a UC-6 y los flujos 1 a 4 del 00.

**Por qué así:** con una sola fuente de verdad para el dinero, el comercial nunca ve una cifra y guarda otra; y convertir en el navegador no cuesta peticiones al backend ni lo hace depender de un servicio externo.

**Cierra una decisión aplazada:** la dirección del backend que usa el navegador (entrada 15 de `ai-review-log.md`; D-1).

**No cambia el backend:** usa los contratos de 002 a 004 tal como están.

## 2. Usuarios

- **Comercial** (único usuario, sin autenticación, ADR 0007): busca y registra clientes, simula, guarda y consulta el historial, desde el escritorio o desde el móvil.
- **Backend de SaaS-O-Matic** (dependencia): la API de 002 a 004.
- **ExchangeRate API** (dependencia externa): `open.er-api.com`, gratuita; actualiza una vez al día, limita las peticiones y exige atribución.

## 3. Historias de usuario

- **HU-1.** Como comercial, quiero buscar clientes por empresa o identificador fiscal, para encontrar uno en segundos (UC-2).
- **HU-2.** Como comercial, quiero registrar un cliente y ver junto a cada campo qué está mal, para corregirlo sin perder lo escrito (UC-1).
- **HU-3.** Como comercial, quiero abrir la ficha de un cliente con sus datos y su historial, para retomar la última conversación (UC-3).
- **HU-4.** Como comercial, quiero mover un slider de usuarios y ver al momento la factura mensual con su desglose por tramo y su impuesto, para negociar en directo (UC-4).
- **HU-5.** Como comercial, quiero guardar exactamente la simulación que estoy viendo, para presentársela al cliente más tarde (UC-5).
- **HU-6.** Como comercial, quiero ver todos los importes en la divisa que elija, para hablar con el cliente en su moneda (UC-6).
- **HU-7.** Como comercial, quiero que la app me diga qué ha fallado y me deje reintentar sin perder lo que estaba haciendo, para no depender de que todo funcione siempre (flujos 1 a 4).

## 4. Requisitos funcionales

Los textos entre comillas latinas son literales. Los que llevan identificador (`T-…`) están en la tabla 5.6. Los importes, porcentajes, números y fechas siguen el formato de RF-5.

### RF-1. Pantallas y navegación

Origen: §3 módulo de dashboard **[E]** (buscador y listado, ficha, simulador), §3 formulario «Nuevo cliente» **[P]**, flujos 1 a 3 **[P]**; D-2 y D-15.

- **CA-1.1** El sistema deberá ofrecer tres pantallas, cada una en su dirección: el listado y buscador en `/clientes`, el alta en `/clientes/nuevo` y la ficha del cliente, con su simulador y su historial, en `/clientes/{id}`.
- **CA-1.2** Cuando el usuario abre `/`, el sistema deberá mostrar el listado y cambiar la dirección a `/clientes`.
- **CA-1.3** Si la dirección no es `/` ni ninguna de las de CA-1.1, entonces el sistema deberá mostrar T-NFP «Página no encontrada» con el enlace T-VOL «Volver al listado», sin hacer ninguna petición al backend.
- **CA-1.4** Cuando el usuario abre directamente o recarga una de las direcciones de CA-1.1, el sistema deberá mostrar esa misma pantalla.
- **CA-1.5** El sistema deberá mostrar en todas las pantallas una cabecera con el nombre «SaaS-O-Matic», que enlaza con `/clientes`, el selector de divisa (RF-4) y la línea de tasas con la atribución (RF-3).
- **CA-1.6** Cuando el usuario cambia de pantalla, el sistema deberá hacerlo sin recargar la página y conservando la divisa elegida y las tasas obtenidas.
- **CA-1.7** El sistema deberá mostrar en el alta y en la ficha el enlace «Volver al listado», que abre `/clientes`.

### RF-2. Comunicación con el backend y errores generales

Origen: §8.1 y §8.4 **[P]**, §6 seguridad **[P]**, flujos 1 a 3 **[P]**, entrada 15 de `ai-review-log.md`; D-1, D-5 y D-16.

- **CA-2.1** El sistema deberá dirigir todas las peticiones al backend a `http://127.0.0.1:8000`, solo con las rutas, parámetros y campos de la tabla 5.2, y no deberá enviar nunca un importe, una tasa de impuesto ni un tipo de cambio (§8.1 del 00).
- **CA-2.2** Si una petición al backend no obtiene respuesta (backend parado, red caída o petición bloqueada por CORS) o no termina en 10 segundos, entonces el sistema deberá darla por fallida y, fuera del simulador, mostrar T-CON «No se pudo conectar con el servidor».
- **CA-2.3** Si el backend responde, fuera del simulador, con un estado para el que la tabla 5.3 indica T-SRV o con un cuerpo que no es JSON, entonces el sistema deberá mostrar T-SRV «Error del servidor. Inténtalo de nuevo».
- **CA-2.4** El sistema no deberá mostrar nunca el cuerpo crudo de una respuesta, trazas, estados HTTP ni los `code` del backend (`validation_error`, `internal_error`…).
- **CA-2.5** Cuando muestra T-CON o T-SRV, el sistema deberá ofrecer el botón T-RET «Reintentar»; al pulsarlo, deberá repetir la misma petición con los mismos datos y volver al estado de carga de esa parte de la pantalla.
- **CA-2.6** El sistema deberá mostrar los `message` de los `details` del backend tal como llegan, sin traducirlos ni cambiarlos.

### RF-3. Tasas de cambio

Origen: §3 módulo de divisas **[E]** (`open.er-api.com` con base EUR) y **[P]** (caché y atribución), flujo 4 **[P]**, §10 supuestos 12 y 13, ADR 0005; D-10, D-11 y D-17.

- **CA-3.1** Cuando se carga la app, si el navegador tiene tasas guardadas cuya `time_next_update_unix` es posterior al instante actual, el sistema deberá usarlas sin hacer ninguna petición a la API de tasas.
- **CA-3.2** Cuando se carga la app sin tasas guardadas o con tasas caducadas (`time_next_update_unix` anterior o igual al instante actual), el sistema deberá hacer una única petición `GET https://open.er-api.com/v6/latest/EUR`.
- **CA-3.3** El sistema deberá dar por válida una respuesta de la API de tasas solo si tiene estado 200 y es un objeto JSON con `result` = `"success"`, `base_code` = `"EUR"`, `rates` como objeto, y `time_last_update_unix` y `time_next_update_unix` como números.
- **CA-3.4** Cuando recibe una respuesta válida, el sistema deberá usarla y guardarla en el navegador en lugar de las tasas anteriores.
- **CA-3.5** El sistema deberá ofrecer como divisas, en este orden, EUR, USD, GBP, CHF y JPY: EUR siempre, con tasa 1, y cada una de las demás solo si `rates` tiene para ella un número finito mayor que 0. No deberá ofrecer ninguna otra divisa de `rates`.
- **CA-3.6** Si la petición falla (sin respuesta, más de 10 segundos, estado distinto de 200, cuerpo que no es JSON o respuesta no válida según CA-3.3) y hay tasas guardadas, aunque estén caducadas, entonces el sistema deberá usarlas y mostrar el aviso T-RFL «Tasas del {fecha}. No se pudieron actualizar» con «Reintentar».
- **CA-3.7** Si la petición falla y no hay tasas guardadas, entonces el sistema deberá ofrecer solo EUR y mostrar el aviso T-RNO «Tipos de cambio no disponibles: importes en EUR» con «Reintentar».
- **CA-3.8** Cuando el usuario pulsa «Reintentar» en un aviso de tasas, el sistema deberá repetir la petición de CA-3.2: si tiene éxito, el aviso desaparece y se usan las tasas nuevas; si falla, se aplica otra vez CA-3.6 o CA-3.7.
- **CA-3.9** Mientras usa tasas sin aviso de fallo, el sistema deberá mostrar junto al selector T-RAT «Tasas del {fecha}».
- **CA-3.10** El sistema deberá escribir {fecha} como la fecha de `time_last_update_unix` en la zona horaria del navegador, con el formato `dd/mm/aaaa`.
- **CA-3.11** El sistema deberá mostrar en todas las pantallas, junto al selector y en cualquier estado de las tasas, el texto T-ATR «Rates By Exchange Rate API» como enlace a `https://www.exchangerate-api.com`.
- **CA-3.12** El sistema no deberá pedir las tasas en ningún momento distinto de CA-3.2 y CA-3.8: ni al cambiar de pantalla ni al cambiar de divisa.
- **CA-3.13** Si las tasas guardadas en el navegador no se pueden leer o no cumplen CA-3.3, entonces el sistema deberá tratarlas como inexistentes.

### RF-4. Selector de divisa

Origen: UC-6 **[E]**, flujo 4 **[P]**, §10 supuesto 12; D-12 y D-13.

- **CA-4.1** El sistema deberá mostrar un selector con la etiqueta «Divisa» y una opción por divisa ofrecida (CA-3.5), con los textos «EUR (euro)», «USD (dólar estadounidense)», «GBP (libra esterlina)», «CHF (franco suizo)» y «JPY (yen japonés)».
- **CA-4.2** Mientras espera la respuesta de la API de tasas, el sistema deberá mostrar el selector desactivado, el indicador T-LRT «Cargando tasas…» y todos los importes en EUR.
- **CA-4.3** Cuando el usuario elige una divisa, el sistema deberá mostrar al instante en esa divisa todos los importes visibles (simulador e historial), sin hacer ninguna petición al backend ni a la API de tasas.
- **CA-4.4** Cuando el usuario elige una divisa, el sistema deberá recordarla en el navegador.
- **CA-4.5** Cuando las tasas están disponibles (recibidas o leídas del navegador), el sistema deberá seleccionar la divisa recordada si está entre las ofrecidas, y EUR si no hay ninguna recordada.
- **CA-4.6** Si la divisa recordada no está entre las ofrecidas (falta en `rates`, solo hay EUR o es un valor desconocido), entonces el sistema deberá seleccionar EUR y conservar la divisa recordada hasta que el usuario elija otra.
- **CA-4.7** Donde la divisa elegida no es EUR, el sistema deberá mostrar junto al selector T-EQ «1 EUR = {tasa} {código}», con la tasa en formato español, redondeada «mitad hacia arriba» a 4 decimales como máximo y sin ceros finales («1 EUR = 1,0823 USD»), y la nota T-ORI «Conversión orientativa: los importes se calculan y guardan en EUR».

### RF-5. Conversión y formato

Origen: RN-6 **[P]**, RN-7 **[E]**, §10 supuesto 12, ADR 0004 y 0005; D-6 a D-9.

- **CA-5.1** El sistema deberá mostrar cada importe a partir del campo `*_cents` que devuelve el backend, sin calcular ningún importe por su cuenta: no suma tramos, no aplica impuestos ni recalcula subtotales o totales.
- **CA-5.2** Donde la divisa elegida no es EUR, el sistema deberá convertir cada importe por separado como `*_cents` × tasa ÷ 100 y redondear a 2 decimales con la regla «mitad hacia arriba» sobre el resultado exacto de esa operación, tomando la tasa con los decimales con que la escribe la respuesta (100 céntimos × 1.005 = 1,005 → 1,01). (Desde la spec 008, en JPY se redondea a yenes enteros, una sola vez: 008 CA-1.2.)
- **CA-5.3** Donde la divisa elegida es EUR, el sistema deberá mostrar los céntimos tal cual, sin multiplicar ni redondear (16940 → «169,40 €»).
- **CA-5.4** El sistema deberá escribir los importes en formato español: coma decimal, punto como separador de miles también con 4 cifras («1.234,56»), siempre 2 decimales, también en JPY (RN-7), y detrás, tras un espacio, «€» para EUR, «US$» para USD y el código para GBP, CHF y JPY. (Desde la spec 008, los importes en JPY se escriben sin decimales, «27.319 JPY», porque el yen no tiene céntimos: 008 CA-1.1 y CA-1.3.)
- **CA-5.5** El sistema deberá escribir la tasa de impuesto (`tax_rate_bp`) como porcentaje en formato español, sin ceros decimales sobrantes y con un espacio antes de «%»: 2100 → «21 %», 1950 → «19,5 %», 2125 → «21,25 %», 0 → «0 %».
- **CA-5.6** El sistema deberá escribir los números que no son importes (usuarios, unidades, almacenamiento, llamadas, `{n}` y `{total}`) sin decimales y con punto como separador de miles, también con 4 cifras (1000 → «1.000»).
- **CA-5.7** El sistema deberá escribir las fechas con hora (`created_at` de una simulación) en la zona horaria del navegador como `dd/mm/aaaa hh:mm`, en formato de 24 horas, y las fechas sin hora como `dd/mm/aaaa`.
- **CA-5.8** El sistema no deberá enviar ni guardar nunca un importe convertido (RN-7).

### RF-6. Listado y búsqueda de clientes

Origen: UC-2 **[E]**, §3 «vista de buscador y listado de clientes» **[E]**, flujo 2 **[P]**, 003 RF-5; D-4 y D-20.

- **CA-6.1** Cuando se abre `/clientes`, el sistema deberá mostrar el buscador vacío, pedir `GET /customers?limit=50&offset=0` y mostrar cada cliente con su empresa, su identificador fiscal, su país y su plan, en el orden en que llegan.
- **CA-6.2** El sistema deberá escribir el país por su nombre en español (ES España, PT Portugal, FR Francia, DE Alemania, IT Italia, GB Reino Unido, US Estados Unidos), o el código tal cual si no es ninguno de ellos, y el plan como «Starter», «Business» o «Enterprise».
- **CA-6.3** El sistema deberá mostrar sobre el listado un campo de búsqueda con la etiqueta «Buscar por empresa o identificador fiscal», que admite como máximo 120 caracteres, y el botón T-NEW «Nuevo cliente», que abre `/clientes/nuevo`.
- **CA-6.4** Cuando pasan 300 ms desde el último cambio del buscador, el sistema deberá pedir `GET /customers` con `q` igual al texto tal como está escrito, `limit=50` y `offset=0`, y sustituir el listado por la respuesta; si el texto está vacío o solo tiene espacios, la petición deberá ir sin `q`.
- **CA-6.5** Si el texto cambia varias veces con menos de 300 ms entre cambios, entonces el sistema deberá hacer una sola petición, con el último texto.
- **CA-6.6** Si llega la respuesta de una búsqueda que ya no corresponde al último texto pedido, entonces el sistema deberá descartarla.
- **CA-6.7** Mientras espera la respuesta, el sistema deberá mostrar T-LCL «Cargando clientes…» en lugar del listado y mantener el buscador editable.
- **CA-6.8** Cuando la respuesta tiene `total` = 0 y la búsqueda está vacía, el sistema deberá mostrar T-EMP «Todavía no hay clientes» y el botón «Nuevo cliente».
- **CA-6.9** Cuando la respuesta tiene `total` = 0 y hay texto de búsqueda, el sistema deberá mostrar T-NOR «Ningún cliente coincide con «{texto}»», con el texto sin espacios exteriores, y el botón «Nuevo cliente».
- **CA-6.10** Si la petición falla, entonces el sistema deberá mostrar el error de RF-2 con «Reintentar» y conservar el texto de búsqueda.
- **CA-6.11** Cuando el usuario activa un cliente del listado (clic, toque o Intro), el sistema deberá abrir `/clientes/{id}`.

### RF-7. «Cargar más»

Origen: respuesta del autor P-5 **[P]**; 003 CA-5.6 y CA-5.7, 004 CA-5.3.

Se aplica al listado de clientes, con o sin búsqueda, y al historial de simulaciones.

- **CA-7.1** Cuando una lista muestra menos elementos que su `total`, el sistema deberá mostrar debajo T-MOS «Mostrando {n} de {total}» y el botón T-MAS «Cargar más».
- **CA-7.2** Cuando el usuario pulsa «Cargar más», el sistema deberá pedir la misma consulta con `limit=50` y `offset` igual al número de elementos mostrados, y añadir al final los elementos recibidos cuyo `id` no esté ya en la lista.
- **CA-7.3** Cuando llega una página, el sistema deberá usar como `total` el de esa respuesta.
- **CA-7.4** Mientras espera la página, el sistema deberá mostrar el botón desactivado con el texto T-LMO «Cargando…» y sin cambiar los elementos mostrados; pulsarlo otra vez no deberá hacer ninguna petición.
- **CA-7.5** Si la página falla, entonces el sistema deberá conservar los elementos mostrados y mostrar bajo la lista el error de RF-2 con «Reintentar», que repite esa misma petición.
- **CA-7.6** Cuando la lista muestra tantos elementos como su `total` o más, el sistema no deberá mostrar T-MOS ni «Cargar más».
- **CA-7.7** Cuando cambia el texto de búsqueda, el sistema deberá volver a la primera página (CA-6.4).

### RF-8. Alta de cliente

Origen: UC-1 **[E]**, §3 formulario «Nuevo cliente» **[P]**, flujo 1 **[P]**, 003 RF-1 a RF-4; respuestas P-1 y P-2; D-14.

- **CA-8.1** Cuando se abre `/clientes/nuevo`, el sistema deberá mostrar un formulario vacío con cinco campos etiquetados, «Empresa», «Identificador fiscal (DNI/NIF/CIF)», «Email de contacto», «País» y «Plan», y los botones «Guardar» y «Cancelar».
- **CA-8.2** El sistema deberá ofrecer en «País» un desplegable sin opción preseleccionada con los 7 países de RN-4 por su nombre en español y en orden alfabético: Alemania, España, Estados Unidos, Francia, Italia, Portugal y Reino Unido (P-1).
- **CA-8.3** El sistema deberá ofrecer en «Plan» un desplegable sin opción preseleccionada con «Starter», «Business» y «Enterprise», en ese orden.
- **CA-8.4** El sistema deberá impedir escribir más de 120 caracteres en «Empresa», 30 en «Identificador fiscal (DNI/NIF/CIF)» y 254 en «Email de contacto».
- **CA-8.5** Cuando el usuario pulsa «Guardar», o Intro en un campo de texto, con algún campo vacío o con solo espacios, el sistema no deberá enviar nada, deberá mostrar T-OBL «Campo obligatorio» junto a cada uno de esos campos y deberá llevar el foco al primero de ellos en el orden del formulario.
- **CA-8.6** El sistema no deberá comprobar en el navegador nada más que CA-8.4 y CA-8.5: el formato del email y del identificador, y su carácter de control, los valida el backend (P-2).
- **CA-8.7** Cuando el usuario pulsa «Guardar» con los cinco campos rellenos, el sistema deberá enviar `POST /customers` con `company_name`, `tax_id` y `contact_email` tal como están escritos, `country` con el código de 2 letras del país elegido y `plan` con `starter`, `business` o `enterprise`.
- **CA-8.8** Mientras espera la respuesta, el sistema deberá mostrar «Guardar» desactivado con el texto T-GDO «Guardando…»; pulsarlo otra vez no deberá hacer ninguna petición.
- **CA-8.9** Cuando el backend responde 201, el sistema deberá abrir `/clientes/{id}` con el `id` recibido y mostrar en la ficha el aviso T-REG «Cliente registrado».
- **CA-8.10** Si el backend responde 422, entonces el sistema deberá mostrar el `message` de cada detalle junto al campo que nombra su `field`, si es uno de los cinco; si algún detalle nombra otro campo, o no hay detalles, deberá mostrar además sobre el formulario T-DNV «Datos no válidos».
- **CA-8.11** Si el backend responde 409, entonces el sistema deberá mostrar junto a «Identificador fiscal (DNI/NIF/CIF)» el `message` de su detalle («Ya existe un cliente con este identificador»).
- **CA-8.12** Si el envío falla por conexión o con una respuesta para la que la tabla 5.3 indica T-SRV, entonces el sistema deberá mostrar sobre el formulario el error de RF-2 con «Reintentar», que reenvía exactamente el mismo cuerpo.
- **CA-8.13** Si la respuesta no es un 201, entonces el sistema deberá conservar todo lo escrito en el formulario.
- **CA-8.14** Cuando el usuario cambia un campo que muestra un mensaje de error, el sistema deberá quitar el mensaje de ese campo y dejar los de los demás.
- **CA-8.15** Cuando el usuario pulsa «Cancelar», el sistema deberá abrir `/clientes` sin enviar nada.

### RF-9. Ficha del cliente

Origen: UC-3 **[E]**, §3 «vista de detalle del cliente con tarjetas responsive» **[E]**, flujo 2 **[P]**, 003 RF-6; D-17 y D-21.

- **CA-9.1** Cuando se abre `/clientes/{id}`, el sistema deberá pedir `GET /customers/{id}` con el `{id}` de la dirección tal como está escrito.
- **CA-9.2** Mientras espera la respuesta, el sistema deberá mostrar T-LCU «Cargando cliente…», sin simulador ni historial.
- **CA-9.3** Cuando la respuesta es 200, el sistema deberá mostrar una tarjeta con la empresa como título y «Identificador fiscal», «Email de contacto», «País» (CA-6.2), «Plan» (CA-6.2) y «Fecha de alta» (`created_at`, sin hora), y debajo el simulador (RF-11) y el historial (RF-10).
- **CA-9.4** Si la respuesta es 404, entonces el sistema deberá mostrar T-NFC «Cliente no encontrado» con «Volver al listado», sin simulador ni historial y sin ninguna otra petición al backend.
- **CA-9.5** Si la petición falla por otro motivo, entonces el sistema deberá mostrar el error de RF-2 con «Reintentar».
- **CA-9.6** Cuando se llega desde un alta (CA-8.9), el sistema deberá mostrar T-REG «Cliente registrado» hasta que el usuario salga de la ficha.

### RF-10. Historial de simulaciones

Origen: §3 «historial de simulaciones de un cliente, de más reciente a más antigua» **[E]**, UC-3, flujo 3 paso 5 **[P]**, 004 RF-5; respuesta P-5; D-18.

- **CA-10.1** Cuando la ficha se ha cargado (CA-9.3), el sistema deberá pedir `GET /customers/{id}/simulations?limit=50&offset=0` y mostrar cada simulación en una tarjeta, en el orden en que llegan.
- **CA-10.2** El sistema deberá mostrar en cada tarjeta la fecha y hora (`created_at`), «Usuarios activos», «Almacenamiento» en GB («200 GB»), «Llamadas a la API al mes», «Subtotal», «Impuesto ({tasa})» con la tasa de CA-5.5 y su importe, y «Total mensual» destacado.
- **CA-10.3** El sistema deberá ofrecer en cada tarjeta el botón «Ver desglose», inicialmente con el desglose oculto, que muestra la tabla de CA-12.6 con los tramos guardados y pasa a decir «Ocultar desglose»; al pulsarlo de nuevo, la oculta.
- **CA-10.4** Mientras espera la respuesta, el sistema deberá mostrar T-LHI «Cargando historial…» en la sección del historial, con la tarjeta del cliente y el simulador ya disponibles.
- **CA-10.5** Cuando `total` = 0, el sistema deberá mostrar T-HVA «Este cliente aún no tiene simulaciones».
- **CA-10.6** Si la petición falla, entonces el sistema deberá mostrar en la sección del historial el error de RF-2 con «Reintentar», sin afectar a la tarjeta del cliente ni al simulador.
- **CA-10.7** El sistema deberá paginar el historial con «Cargar más» (RF-7).
- **CA-10.8** Cuando se guarda una simulación (CA-13.4) con el historial cargado, el sistema deberá añadirla la primera con los datos de la respuesta 201, sin volver a pedir el historial, y sumar 1 a `total`.
- **CA-10.9** Cuando se guarda una simulación con el historial en error o cargando, el sistema deberá descartar la petición en curso, si la hay, y pedir otra vez la primera página del historial.

### RF-11. Simulador: valores de entrada

Origen: UC-4 **[E]**, §3 «formulario de simulación interactiva con slider u otros controles» **[E]**, flujo 3 **[P]**, RN-2 y RN-9 **[P]**, 004 RF-2; respuesta P-3; D-3.

- **CA-11.1** Cuando se muestra el simulador, el sistema deberá mostrar tres valores con estas etiquetas e iniciales: «Usuarios activos» 15, «Almacenamiento (GB)» 0 y «Llamadas a la API al mes» 0.
- **CA-11.2** El sistema deberá ofrecer para «Usuarios activos» un slider de 0 a 200 con paso 1 y un campo numérico sincronizados: mover el slider pone su valor en el campo, y escribir en el campo un valor válido de 0 a 200 lleva el slider a ese valor.
- **CA-11.3** Si el campo tiene un valor válido de 201 a 100 000, entonces el sistema deberá dejar el slider en su máximo (200) y usar el valor del campo; si después se mueve el slider, el campo deberá tomar el valor del slider.
- **CA-11.4** El sistema deberá permitir manejar el slider con el teclado: flecha derecha o arriba suma 1, flecha izquierda o abajo resta 1, Inicio lo lleva a 0 y Fin a 200.
- **CA-11.5** El sistema deberá considerar válido un valor de usuarios escrito solo con dígitos `0`–`9` cuyo número esté entre 0 y 100 000 (`007` vale 7).
- **CA-11.6** Si el valor de usuarios no es válido (vacío, con signo, decimales, exponente, letras o fuera de rango), entonces el sistema deberá mostrar junto al campo T-USR «Debe ser un número entero entre 0 y 100000», no deberá pedir ninguna cotización con él y deberá mantener sin cambios la última cotización mostrada.
- **CA-11.7** Si «Almacenamiento (GB)» no está escrito solo con dígitos o no está entre 0 y 1 000 000, entonces el sistema deberá mostrar junto al campo T-STO «Debe ser un número entero entre 0 y 1000000».
- **CA-11.8** Si «Llamadas a la API al mes» no está escrito solo con dígitos o no está entre 0 y 1 000 000 000, entonces el sistema deberá mostrar junto al campo T-APC «Debe ser un número entero entre 0 y 1000000000».
- **CA-11.9** Cuando cambian el almacenamiento o las llamadas, el sistema no deberá pedir ninguna cotización ni cambiar ningún importe (RN-9).
- **CA-11.10** El sistema no deberá enviar al backend ningún valor que no sea válido según CA-11.5, CA-11.7 o CA-11.8.

### RF-12. Simulador: cotización en tiempo real

Origen: UC-4 **[E]** «proyecta la factura mensual en tiempo real», flujo 3 pasos 2 y 3 y sus errores **[P]**, ADR 0004, §6 del 00 (espera de 200 a 300 ms) **[P]**, 002; D-4.

- **CA-12.1** Cuando se muestra el simulador, el sistema deberá pedir sin esperar `POST /pricing/quote` con `users` 15 y el `country` del cliente tal como lo devolvió la ficha.
- **CA-12.2** Cuando el valor de usuarios cambia a un valor válido y pasan 300 ms sin otro cambio, el sistema deberá pedir `POST /pricing/quote` con ese valor como `users` y el `country` del cliente.
- **CA-12.3** Si el valor cambia varias veces con menos de 300 ms entre cambios (por ejemplo, al arrastrar el slider), entonces el sistema deberá hacer una sola petición, con el último valor.
- **CA-12.4** Si al cumplirse los 300 ms el valor coincide con el de la cotización mostrada sin error, entonces el sistema no deberá pedir otra.
- **CA-12.5** Si llega la respuesta de una cotización que ya no corresponde al último valor pedido, entonces el sistema deberá descartarla.
- **CA-12.6** Cuando llega una cotización 200, el sistema deberá mostrar una tabla de desglose con una fila por cada uno de los 3 tramos de `tiers`, también los que tienen 0 unidades, y las columnas «Tramo» (número), «Usuarios» («{from_users} a {to_users}», o «{from_users} o más» si `to_users` es `null`), «Unidades», «Precio por usuario» (`unit_price_cents`) e «Importe» (`amount_cents`); y debajo «Subtotal», «Impuesto ({tasa})» y «Total mensual» destacado.
- **CA-12.7** Mientras un cambio a un valor válido espera los 300 ms o hay una cotización en curso, el sistema deberá mostrar la última cotización con el indicador T-UPD «Actualizando…».
- **CA-12.8** Si la cotización falla (sin respuesta, más de 10 segundos, cuerpo que no es JSON o cualquier estado distinto de 200 que no sea el de CA-12.9), entonces el sistema deberá mantener la última cotización mostrada, si la hay, y mostrar T-NUP «No se pudo actualizar» con «Reintentar», que pide la cotización del valor actual de usuarios.
- **CA-12.9** Si la cotización responde 422 con el detalle `{field: "country", message: "País no soportado"}`, entonces el sistema deberá mostrar T-CNS «El país del cliente no está soportado» en lugar de la cotización, sin «Reintentar».
- **CA-12.10** Cuando cambia la divisa, el sistema deberá convertir la cotización mostrada sin pedir otra (CA-4.3).

### RF-13. Guardar simulación

Origen: UC-5 **[E]**, flujo 3 pasos 4 y 5 y sus errores **[P]**, 004 RF-1; respuesta P-4; D-19.

- **CA-13.1** El sistema deberá activar «Guardar simulación» solo mientras se cumplen a la vez: los tres valores son válidos (RF-11); la cotización mostrada es la respuesta 200 a una petición con el valor actual de usuarios; ningún cambio de usuarios espera los 300 ms ni hay una cotización en curso; y no hay un guardado en curso (P-4).
- **CA-13.2** Cuando el usuario pulsa «Guardar simulación», el sistema deberá enviar `POST /simulations` con `customer_id` igual al `id` del cliente y `active_users`, `storage_gb` y `api_calls_per_month` como enteros JSON, sin ningún otro campo.
- **CA-13.3** Mientras espera la respuesta, el sistema deberá mostrar el botón desactivado con T-GDO «Guardando…» y los tres valores desactivados; pulsarlo otra vez no deberá hacer ninguna petición.
- **CA-13.4** Cuando el backend responde 201, el sistema deberá añadir la simulación al historial (CA-10.8 y CA-10.9), mostrar T-SOK «Simulación guardada» hasta que cambie un valor del simulador, se guarde otra vez o el usuario salga de la ficha, y dejar en el simulador los mismos valores y la misma cotización.
- **CA-13.5** El sistema deberá mostrar en el historial los importes de la respuesta 201, aunque difieran de la cotización que se veía.
- **CA-13.6** Si el guardado falla sin respuesta, en más de 10 segundos, con un 5xx o con un cuerpo que no es JSON, entonces el sistema deberá mostrar T-SKO «No se pudo guardar la simulación» con «Reintentar», que reenvía exactamente el mismo cuerpo, y dejar sin cambios el historial y los valores del simulador.
- **CA-13.7** Si el guardado responde 422 con el detalle `{field: "customer_id", message: "El país del cliente no está soportado"}`, entonces el sistema deberá mostrar T-CNS «El país del cliente no está soportado», sin «Reintentar».
- **CA-13.8** Si el guardado responde con cualquier otro estado 4xx, entonces el sistema deberá mostrar T-SKO «No se pudo guardar la simulación», sin «Reintentar».

## 5. Contrato observable

### 5.1 Direcciones de la app

La app se sirve en `http://localhost:4200`, el único origen que autoriza el backend (002 CA-9.1).

| Dirección | Pantalla |
| --- | --- |
| `/` | Redirige a `/clientes` |
| `/clientes` | Listado y buscador |
| `/clientes/nuevo` | Alta de cliente |
| `/clientes/{id}` | Ficha del cliente, con simulador e historial |
| Cualquier otra | «Página no encontrada» |

### 5.2 Peticiones al backend

Base `http://127.0.0.1:8000`; contratos de 002, 003 y 004 sin cambios. Las peticiones con cuerpo llevan `Content-Type: application/json`. Los parámetros de consulta se comparan como conjunto, sin importar su orden.

| Petición | Cuándo | Cuerpo |
| --- | --- | --- |
| `GET /customers?limit=50&offset={n}`, con `q` si hay texto | Abrir el listado, buscar, «Cargar más» | — |
| `POST /customers` | «Guardar» en el alta | `company_name`, `tax_id`, `contact_email`, `country`, `plan` |
| `GET /customers/{id}` | Abrir la ficha | — |
| `GET /customers/{id}/simulations?limit=50&offset={n}` | Ficha cargada, «Cargar más», guardado con el historial en error o cargando | — |
| `POST /pricing/quote` | Mostrar el simulador, cambio de usuarios más 300 ms, «Reintentar» | `users`, `country` |
| `POST /simulations` | «Guardar simulación» | `customer_id`, `active_users`, `storage_gb`, `api_calls_per_month` |

### 5.3 Qué ve el usuario según la respuesta del backend

| Respuesta | Lecturas (listado, ficha, historial) | Alta | Cotización | Guardar simulación |
| --- | --- | --- | --- | --- |
| 200 o 201 | Los datos | Ficha con T-REG | Desglose y totales | Tarjeta en el historial y T-SOK |
| 404 | Ficha: T-NFC. Listado e historial: T-SRV + Reintentar | T-SRV + Reintentar | T-NUP + Reintentar | T-SKO |
| 409 | T-SRV + Reintentar | `message` junto al identificador fiscal | T-NUP + Reintentar | T-SKO |
| 422 | T-SRV + Reintentar | `message` junto a cada campo; T-DNV si nombra otro o no hay detalles | `country` «País no soportado»: T-CNS. Otro: T-NUP + Reintentar | `customer_id` «El país del cliente no está soportado»: T-CNS. Otro: T-SKO |
| Otro 4xx | T-SRV + Reintentar | T-SRV + Reintentar | T-NUP + Reintentar | T-SKO |
| 5xx o cuerpo que no es JSON | T-SRV + Reintentar | T-SRV + Reintentar | T-NUP + Reintentar | T-SKO + Reintentar |
| Sin respuesta o más de 10 s | T-CON + Reintentar | T-CON + Reintentar | T-NUP + Reintentar | T-SKO + Reintentar |

### 5.4 Petición a la API de tasas

`GET https://open.er-api.com/v6/latest/EUR`, sin parámetros ni cabeceras propias. Solo se usan `result`, `base_code`, `rates`, `time_last_update_unix` y `time_next_update_unix`. Respuesta de referencia para los casos de prueba (1794787200 = 16/11/2026 00:00 UTC; 1794873600 = 17/11/2026 00:00 UTC):

```json
{
  "result": "success",
  "time_last_update_unix": 1794787200,
  "time_next_update_unix": 1794873600,
  "base_code": "EUR",
  "rates": { "EUR": 1, "USD": 1.0823, "GBP": 0.8452, "CHF": 0.9361, "JPY": 161.27, "MXN": 19.85 }
}
```

### 5.5 Lo que se guarda en el navegador

Solo la divisa elegida y la última respuesta válida de la API de tasas (los cinco campos de 5.4). Ningún dato de clientes ni de simulaciones.

### 5.6 Textos de la interfaz

**Mensajes y avisos** (además, los `message` de los `details` del backend de 003 y 004, que se muestran tal cual):

| ID | Texto | Dónde |
| --- | --- | --- |
| T-CON | No se pudo conectar con el servidor | Petición sin respuesta fuera del simulador |
| T-SRV | Error del servidor. Inténtalo de nuevo | Respuesta no prevista fuera del simulador |
| T-RET | Reintentar | Botón de cada error recuperable y de los avisos de tasas |
| T-LRT | Cargando tasas… | Junto al selector, mientras cargan las tasas |
| T-RAT | Tasas del {fecha} | Junto al selector, sin fallo |
| T-RFL | Tasas del {fecha}. No se pudieron actualizar | Fallo con tasas guardadas |
| T-RNO | Tipos de cambio no disponibles: importes en EUR | Fallo sin tasas guardadas |
| T-EQ | 1 EUR = {tasa} {código} | Divisa distinta de EUR |
| T-ORI | Conversión orientativa: los importes se calculan y guardan en EUR | Divisa distinta de EUR |
| T-ATR | Rates By Exchange Rate API | Siempre, enlazado a `https://www.exchangerate-api.com` |
| T-NEW | Nuevo cliente | Botón del listado |
| T-LCL | Cargando clientes… | Listado |
| T-EMP | Todavía no hay clientes | Listado vacío sin búsqueda |
| T-NOR | Ningún cliente coincide con «{texto}» | Búsqueda sin resultados |
| T-MOS | Mostrando {n} de {total} | Lista incompleta |
| T-MAS | Cargar más | Botón de lista incompleta |
| T-LMO | Cargando… | Botón «Cargar más» en espera |
| T-OBL | Campo obligatorio | Campo vacío en el alta |
| T-DNV | Datos no válidos | 422 del alta que no se puede pintar junto a un campo |
| T-GDO | Guardando… | Botones de guardar en espera |
| T-REG | Cliente registrado | Ficha tras un alta |
| T-LCU | Cargando cliente… | Ficha |
| T-NFC | Cliente no encontrado | Ficha con 404 |
| T-NFP | Página no encontrada | Dirección desconocida |
| T-VOL | Volver al listado | Alta, ficha, T-NFC y T-NFP |
| T-LHI | Cargando historial… | Historial |
| T-HVA | Este cliente aún no tiene simulaciones | Historial vacío |
| T-USR | Debe ser un número entero entre 0 y 100000 | Usuarios no válidos |
| T-STO | Debe ser un número entero entre 0 y 1000000 | Almacenamiento no válido |
| T-APC | Debe ser un número entero entre 0 y 1000000000 | Llamadas no válidas |
| T-UPD | Actualizando… | Cotización pendiente |
| T-NUP | No se pudo actualizar | Cotización fallida |
| T-CNS | El país del cliente no está soportado | Cotización o guardado con un país retirado |
| T-SOK | Simulación guardada | Tras un guardado |
| T-SKO | No se pudo guardar la simulación | Guardado fallido |

T-USR, T-STO y T-APC coinciden con los mensajes del backend para los mismos campos (004, sección 5).

**Etiquetas y botones:** «SaaS-O-Matic», «Divisa», «Buscar por empresa o identificador fiscal», «Empresa», «Identificador fiscal (DNI/NIF/CIF)», «Email de contacto», «País», «Plan», «Guardar», «Cancelar», «Identificador fiscal», «Fecha de alta», «Usuarios activos», «Almacenamiento (GB)», «Almacenamiento», «Llamadas a la API al mes», «Tramo», «Usuarios», «Unidades», «Precio por usuario», «Importe», «Subtotal», «Impuesto ({tasa})», «Total mensual», «Guardar simulación», «Ver desglose», «Ocultar desglose».

### 5.7 Formatos (RF-5)

| Dato | Ejemplo |
| --- | --- |
| Importe en EUR | 16940 → «169,40 €»; 123456 → «1.234,56 €» |
| Importe convertido | 16940 con USD 1.0823 → «183,34 US$»; con JPY 161.27 → «27.319,14 JPY» (desde la spec 008, «27.319 JPY») |
| Tasa de impuesto | 2100 → «21 %»; 1950 → «19,5 %» |
| Número | 50000 → «50.000» |
| Fecha y hora | `2026-11-16T10:00:00Z` en Madrid → «16/11/2026 11:00» |
| Rango de tramo | (11, 50) → «11 a 50»; (51, `null`) → «51 o más» |

## 6. Casos de prueba

Niveles: **U** = regla pura, sin pantalla ni red; **C** = pantalla con el backend y la API de tasas sustituidos por respuestas preparadas, el reloj controlado y la zona horaria `Europe/Madrid`; **M** = comprobación manual en un navegador real con el backend arrancado y el seed cargado.

Datos de partida de los casos C, salvo que se indique otra cosa: cliente 1 = Acme Telecom S.L. (`B12345674`, `compras@acme.example`, `ES`, `business`, `created_at` `2026-11-13T10:00:00Z`); tasas = respuesta de 5.4, vigentes; cotización = respuesta de §8.3 del 00 (15 usuarios, ES); simulación = la de SI-1 de 004 (sección 5 de 004). Los textos se comparan con los espacios normalizados (el espacio antes de «€», «US$» o «%» puede ser no separable). Cuando un caso C depende de un comportamiento nativo del navegador (teclado, límite de caracteres, Intro), el test C comprueba el control nativo que lo garantiza y MA-3 comprueba el comportamiento en un navegador real.

### 6.1 Formato y conversión · U

| # | Entrada | Salida esperada |
| --- | --- | --- |
| CV-1 | 16940 céntimos, EUR | «169,40 €» |
| CV-2 | 0, EUR | «0,00 €» |
| CV-3 | 123456, EUR | «1.234,56 €» (miles agrupados con 4 cifras) |
| CV-4 | 99999, EUR | «999,99 €» |
| CV-5 | 60520570, EUR | «605.205,70 €» |
| CV-6 | 16940, USD 1.0823 | «183,34 US$» |
| CV-7 | 16940, GBP 0.8452 | «143,18 GBP» |
| CV-8 | 16940, CHF 0.9361 | «158,58 CHF» |
| CV-9 | 16940, JPY 161.27 | «27.319,14 JPY» (2 decimales también en JPY; desde la spec 008, «27.319 JPY», caso YN-1) |
| CV-10 | 60520570, JPY 161.27 | «97.601.523,24 JPY» (desde la spec 008, «97.601.523 JPY», caso YN-2) |
| CV-11 | 100, USD 1.005 | «1,01 US$» (1,005 exacto sube) |
| CV-12 | 1, USD 1.5 | «0,02 US$» (0,015 exacto sube) |
| CV-13 | 50, USD 1.09 | «0,55 US$» (0,545 exacto sube) |
| CV-14 | 1, USD 1.4 | «0,01 US$» (0,014 baja) |
| CV-15 | 0, JPY 161.27 | «0,00 JPY» (desde la spec 008, «0 JPY», caso YN-3) |
| CV-16 | Tasas de impuesto 2100, 1950, 2125, 0, 10000 y 1 | «21 %», «19,5 %», «21,25 %», «0 %», «100 %» y «0,01 %» |
| CV-17 | Números 0, 15, 1000, 50000, 100000 y 1000000000 | «0», «15», «1.000», «50.000», «100.000» y «1.000.000.000» |
| CV-18 | `created_at` `2026-11-16T10:00:00Z` | «16/11/2026 11:00» |
| CV-19 | `2026-11-16T23:30:00Z` | «17/11/2026 00:30» (cambia el día) |
| CV-20 | `2026-07-01T10:00:00Z` | «01/07/2026 12:00» (horario de verano) |
| CV-21 | Sin hora: `2026-11-13T10:00:00Z` y `time_last_update_unix` 1794787200 | «13/11/2026» y «16/11/2026» |
| CV-22 | Tasas de T-EQ 1.0823, 161.27, 0.845234, 1.08 y 1.23456 | «1,0823», «161,27», «0,8452», «1,08» y «1,2346» |
| CV-23 | Límites de tramo (1, 10), (11, 50) y (51, `null`) | «1 a 10», «11 a 50» y «51 o más» |

### 6.2 Reglas de entrada, divisas y caché · U

| # | Entrada | Salida esperada |
| --- | --- | --- |
| VE-1 | Usuarios `0`, `15`, `007` y `100000` | Válidos: 0, 15, 7 y 100000 |
| VE-2 | Usuarios vacío, `-1`, `+5`, `1.5`, `1,5`, `1e3`, `abc` y `100001` | No válidos (T-USR) |
| VE-3 | Almacenamiento `0` y `1000000`; `-1`, `1000001`, `1.5` y vacío | Válidos; no válidos (T-STO) |
| VE-4 | Llamadas `0` y `1000000000`; `-1`, `1000000001`, `2.0` y vacío | Válidas; no válidas (T-APC) |
| VE-5 | `rates` de 5.4 | EUR, USD, GBP, CHF y JPY, en ese orden |
| VE-6 | `rates` de 5.4 sin JPY | EUR, USD, GBP y CHF |
| VE-7 | `rates` con USD 0, GBP -1, CHF `"0.93"` y JPY `null` | Solo EUR |
| VE-8 | `rates` `{}` | Solo EUR |
| VE-9 | `rates` de 5.4 sin la clave EUR | EUR igualmente, con tasa 1 |
| VE-10 | `time_next_update_unix` 1794873600 con el instante en 1794873599, 1794873600 y 1794873601 | Vigentes, caducadas y caducadas |
| VE-11 | Respuestas con `result` `"error"`; con `base_code` `"USD"`; sin `rates`; con `rates` como lista; sin `time_next_update_unix`; con `time_last_update_unix` como texto | No válidas las seis |

### 6.3 Tasas de cambio · C

| # | Situación | Resultado esperado |
| --- | --- | --- |
| TC-1 | Sin tasas guardadas; la API responde 5.4 | 1 petición; selector activo con 5 divisas; T-RAT «Tasas del 16/11/2026»; tasas guardadas en el navegador |
| TC-2 | Tasas de 5.4 guardadas; instante 1794873599 | 0 peticiones; 5 divisas y T-RAT |
| TC-3 | Tasas guardadas; instante 1794873600 | 1 petición |
| TC-4 | TC-3 con una respuesta válida en la que USD vale 1.09 | Se usa y se guarda la nueva; con USD elegido, T-EQ «1 EUR = 1,09 USD» |
| TC-5 | Tasas guardadas caducadas; la API no responde | Se usan las guardadas; T-RFL «Tasas del 16/11/2026. No se pudieron actualizar» con «Reintentar» |
| TC-6 | TC-5 con respuesta 429, 500, `result` `"error"`, `base_code` `"USD"` y cuerpo `no es json` | Lo mismo que TC-5 en los cinco |
| TC-7 | TC-5 con una respuesta que llega a los 10 s | Lo mismo que TC-5; la respuesta tardía se ignora |
| TC-8 | Sin tasas guardadas; la API falla | Solo EUR; T-RNO con «Reintentar»; importes en EUR |
| TC-9 | TC-8 y «Reintentar» con la API correcta | 2.ª petición; el aviso desaparece; 5 divisas; tasas guardadas |
| TC-10 | TC-5 y «Reintentar» que vuelve a fallar | T-RFL sigue visible |
| TC-11 | Tasas guardadas ilegibles (texto que no es JSON); la API responde 5.4 | 1 petición; igual que TC-1 |
| TC-12 | Almacenamiento del navegador no disponible | La app funciona; 1 petición en cada carga; la divisa elegida no se recuerda al recargar |
| TC-13 | Recorrer listado, alta y ficha y volver, cambiando 3 veces de divisa | 1 sola petición de tasas en total |
| TC-14 | Mientras la API no ha respondido (antes de 10 s) | Selector desactivado; T-LRT; importes en EUR |
| TC-15 | La respuesta de 5.4 incluye MXN | MXN no se ofrece |
| TC-16 | En los estados de TC-1, TC-5, TC-8 y TC-14, en las cuatro pantallas | T-ATR visible y enlazado a `https://www.exchangerate-api.com` |

### 6.4 Selector de divisa · C · ficha del cliente 1 con la cotización y la simulación de partida

| # | Situación | Resultado esperado |
| --- | --- | --- |
| DV-1 | Opciones con 5.4 | «EUR (euro)», «USD (dólar estadounidense)», «GBP (libra esterlina)», «CHF (franco suizo)» y «JPY (yen japonés)», en ese orden |
| DV-2 | Elegir USD | Simulador e historial en USD: subtotal «151,52 US$», impuesto «31,82 US$», total «183,34 US$»; 0 peticiones al backend y a la API de tasas |
| DV-3 | Con USD elegido | T-EQ «1 EUR = 1,0823 USD» y T-ORI visibles |
| DV-4 | Elegir USD y volver a EUR | Total «169,40 €»; sin T-EQ ni T-ORI |
| DV-5 | Elegir CHF | Subtotal «131,05 CHF», impuesto «27,52 CHF», total «158,58 CHF» (cada importe convertido por separado) |
| DV-6 | Elegir GBP y recargar con las tasas vigentes | GBP seleccionada |
| DV-7 | Divisa recordada JPY; la respuesta no trae JPY | EUR seleccionada; al recargar con JPY en la respuesta, JPY seleccionada |
| DV-8 | Divisa recordada `XYZ` | EUR |
| DV-9 | Divisa recordada USD; las tasas fallan sin tasas guardadas | Solo EUR; la divisa recordada sigue siendo USD |
| DV-10 | Sin divisa recordada | EUR |
| DV-11 | Divisa recordada USD, mientras cargan las tasas | Importes en EUR y selector desactivado; al llegar las tasas, USD |

### 6.5 Listado y búsqueda · C

Respuesta de partida: Acme Telecom S.L. (`id` 1, `B12345674`, ES, `business`), Albion Connect Ltd (`id` 5, `GB123456789`, GB, `starter`) y Liberty Mesh Inc. (`id` 6, `US123456789`, US, `enterprise`), `total` 3.

| # | Situación | Resultado esperado |
| --- | --- | --- |
| LI-1 | Abrir `/clientes` | Buscador vacío; `GET /customers?limit=50&offset=0`; 3 clientes en el orden recibido |
| LI-2 | Fila de Acme | «Acme Telecom S.L.», «B12345674», «España» y «Business» |
| LI-3 | Cliente con `country` `MX` en la respuesta | País «MX» |
| LI-4 | Escribir `acme` y esperar 300 ms | `GET /customers?q=acme&limit=50&offset=0` |
| LI-5 | Escribir `acme` y esperar 299 ms | 0 peticiones nuevas; al llegar a 300 ms, 1 |
| LI-6 | Escribir `a`, `ac`, `acm` y `acme` con 100 ms entre cambios | 1 petición, con `q=acme` |
| LI-7 | Buscar `zzz` con `total` 0 | T-NOR «Ningún cliente coincide con «zzz»» y «Nuevo cliente» |
| LI-8 | Buscar `  zzz  ` con `total` 0 | `q` enviado con sus espacios; texto «Ningún cliente coincide con «zzz»» |
| LI-9 | Borrar el texto; en otra prueba, escribir solo espacios | Petición sin `q` |
| LI-10 | `total` 0 sin búsqueda | T-EMP y «Nuevo cliente» |
| LI-11 | Buscar `a&b=c%` | El backend recibe `q` = `a&b=c%` |
| LI-12 | Buscar `ac` (respuesta lenta) y después `acme` (rápida) | Solo se ven los resultados de `acme`, también cuando llega después la respuesta de `ac` |
| LI-13 | Límite del buscador | Límite nativo de 120 caracteres; en un navegador real no se puede escribir el 121.º (MA-3) |
| LI-14 | Mientras espera | T-LCL; el buscador sigue editable |
| LI-15 | El backend no responde | T-CON con «Reintentar»; el texto se conserva; «Reintentar» repite la misma petición |
| LI-16 | El backend responde 500 | T-SRV con «Reintentar» |
| LI-17 | Activar Acme con clic | `/clientes/1`; el cliente es un enlace a `/clientes/1`, que Intro activa en un navegador real (MA-3) |
| LI-18 | Pulsar «Nuevo cliente» | `/clientes/nuevo` |
| LI-19 | Cliente con `company_name` `<b>Acme</b>` | Se ve el texto `<b>Acme</b>` tal cual, sin negrita |

### 6.6 «Cargar más» · C

| # | Situación | Resultado esperado |
| --- | --- | --- |
| CM-1 | `total` 120 y primera página de 50 | «Mostrando 50 de 120» y «Cargar más» |
| CM-2 | Pulsar «Cargar más» | `GET /customers?limit=50&offset=50`; 100 elementos; «Mostrando 100 de 120» |
| CM-3 | Pulsar otra vez (llegan 20) | Petición con `offset=100`; 120 elementos; sin T-MOS ni «Cargar más» |
| CM-4 | `total` 50 con 50 elementos | Sin T-MOS ni «Cargar más» |
| CM-5 | `total` 51 con 50 elementos | «Mostrando 50 de 51» y «Cargar más» |
| CM-6 | Pulsar «Cargar más» dos veces seguidas | 1 petición; el botón muestra T-LMO desactivado mientras espera |
| CM-7 | La segunda página falla | Siguen los 50; error de RF-2 con «Reintentar» bajo la lista, que repite `offset=50` |
| CM-8 | Búsqueda `acme` con `total` 70 | La segunda página lleva `q=acme` |
| CM-9 | Con 100 mostrados, cambiar la búsqueda | Petición con `offset=0`; solo los resultados nuevos |
| CM-10 | La segunda página repite un `id` ya mostrado | Aparece una sola vez |
| CM-11 | La segunda página trae `total` 121 | «Mostrando 100 de 121» |
| CM-12 | Historial del cliente 1 con `total` 60 | «Cargar más» pide `GET /customers/1/simulations?limit=50&offset=50` |

### 6.7 Alta de cliente · C · datos válidos = petición de la sección 5 de 003

| # | Situación | Resultado esperado |
| --- | --- | --- |
| AL-1 | Abrir `/clientes/nuevo` | 5 campos vacíos con sus etiquetas; «País» con los 7 en orden alfabético y sin selección; «Plan» con los 3 y sin selección |
| AL-2 | «Guardar» con todo vacío | 0 peticiones; T-OBL en los 5 campos; foco en «Empresa» |
| AL-3 | «Empresa» con 3 espacios y el resto válido | 0 peticiones; T-OBL solo en «Empresa» |
| AL-4 | Datos válidos y «Guardar» | `POST /customers` con exactamente el cuerpo de la sección 5 de 003 |
| AL-5 | AL-4 con 201 e `id` 1 | `/clientes/1` con T-REG |
| AL-6 | Datos válidos y envío del formulario, que es lo que hace Intro en un campo de texto (MA-3) | Igual que AL-4 |
| AL-7 | Email `abc` | Se envía; con el 422 de `contact_email`, «Debe ser un email válido» junto a «Email de contacto» |
| AL-8 | `tax_id` `12345678A` con España | Se envía; con el 422, «El DNI/NIF/CIF no es válido» junto al identificador |
| AL-9 | 422 con detalles de `tax_id` y de `contact_email` | Cada mensaje junto a su campo |
| AL-10 | 409 | «Ya existe un cliente con este identificador» junto al identificador |
| AL-11 | 422 con `country` «País no soportado» | Junto a «País» |
| AL-12 | 422 con un detalle de `body` | T-DNV sobre el formulario |
| AL-13 | Sin respuesta; en otra prueba, 500 | T-CON o T-SRV con «Reintentar», que reenvía el mismo cuerpo |
| AL-14 | Tras cada error de AL-7 a AL-13 | Los cinco campos conservan lo escrito |
| AL-15 | «Guardar» dos veces seguidas | 1 petición; T-GDO desactivado mientras espera |
| AL-16 | Tras AL-9, cambiar el identificador | Desaparece su mensaje; el del email sigue |
| AL-17 | Límites de empresa, identificador y email | Límites nativos de 120, 30 y 254 caracteres; en un navegador real no se puede escribir más (MA-3) |
| AL-18 | Identificador `12.345.678-z`; 201 con `12345678Z` | Se envía `12.345.678-z`; la ficha muestra «12345678Z» |
| AL-19 | Elegir «Reino Unido» y «Enterprise» | El cuerpo lleva `"country": "GB"` y `"plan": "enterprise"` |
| AL-20 | «Cancelar» con datos escritos | `/clientes`; 0 peticiones |

### 6.8 Ficha y navegación · C

| # | Situación | Resultado esperado |
| --- | --- | --- |
| FI-1 | Abrir `/clientes/1` | `GET /customers/1`; tarjeta con «Acme Telecom S.L.», «B12345674», «compras@acme.example», «España», «Business» y «13/11/2026»; después `GET /customers/1/simulations?limit=50&offset=0` y `POST /pricing/quote` con `{"users": 15, "country": "ES"}` |
| FI-2 | Mientras espera la ficha | T-LCU; sin simulador ni historial |
| FI-3 | `GET /customers/999` responde 404 | T-NFC con «Volver al listado»; ninguna otra petición |
| FI-4 | Abrir `/clientes/abc` (el backend responde 404) | Igual que FI-3 |
| FI-5 | La ficha responde 500 y, tras «Reintentar», 200 | T-SRV con «Reintentar»; la segunda petición carga la ficha |
| FI-6 | Abrir `/`, `/clientes/1/otra` y `/desconocida` | `/clientes`; T-NFP; T-NFP; ninguna petición al backend en los dos últimos |
| FI-7 | Recargar en `/clientes/1` y en `/clientes/nuevo` | La misma pantalla |
| FI-8 | Desde la ficha, pulsar «Volver al listado» y, en otra prueba, «SaaS-O-Matic» | `/clientes` en los dos |
| FI-9 | Tras un alta, salir de la ficha y volver a ella | T-REG ya no aparece |

### 6.9 Historial · C · cliente 1

| # | Situación | Resultado esperado |
| --- | --- | --- |
| HI-1 | Historial con la simulación de partida | Tarjeta: «16/11/2026 11:00»; «Usuarios activos» 15; «Almacenamiento» «200 GB»; «Llamadas a la API al mes» «50.000»; «Subtotal» «140,00 €»; «Impuesto (21 %)» «29,40 €»; «Total mensual» «169,40 €» |
| HI-2 | 3 simulaciones con `id` 3, 2 y 1 | 3 tarjetas en ese orden |
| HI-3 | «Ver desglose» en HI-1 | Filas: 1 «1 a 10» 10 «10,00 €» «100,00 €»; 2 «11 a 50» 5 «8,00 €» «40,00 €»; 3 «51 o más» 0 «5,00 €» «0,00 €»; el botón dice «Ocultar desglose» |
| HI-4 | Pulsar «Ocultar desglose» | La tabla se oculta |
| HI-5 | `total` 0 | T-HVA |
| HI-6 | Mientras espera | T-LHI; tarjeta del cliente y simulador visibles |
| HI-7 | El historial responde 500 | T-SRV con «Reintentar» en la sección del historial; tarjeta del cliente y simulador funcionan |
| HI-8 | HI-3 con USD | Precios «10,82 US$», «8,66 US$» y «5,41 US$»; importes «108,23 US$», «43,29 US$» y «0,00 US$»; total «183,34 US$» |
| HI-9 | Simulación con `tax_rate_bp` 0 | «Impuesto (0 %)» «0,00 €» |

### 6.10 Simulador: valores de entrada · C · cotizaciones con respuesta 200

| # | Situación | Resultado esperado |
| --- | --- | --- |
| SM-1 | Mostrar el simulador | Slider y campo en 15; almacenamiento 0; llamadas 0 |
| SM-2 | Llevar el slider a 60 | Campo en 60 |
| SM-3 | Escribir 150 | Slider en 150 |
| SM-4 | Escribir 201; en otra prueba, 100000 | Slider en 200; cotización con `users` 201 y 100000 |
| SM-5 | Escribir 100001 | T-USR; ninguna petición; «Guardar simulación» desactivado; la cotización anterior sigue igual |
| SM-6 | Escribir vacío, `-1`, `1.5`, `1e3` y `abc` | T-USR en los cinco; ninguna petición |
| SM-7 | Escribir `0` | Cotización con `users` 0 |
| SM-8 | Escribir `007` | Cotización con `users` 7 |
| SM-9 | Tras escribir 201, llevar el slider a 199 | Campo en 199 |
| SM-10 | Control del slider | Control de rango nativo de 0 a 200 con paso 1. En un navegador real (MA-3), desde 15: flecha derecha, dos veces flecha izquierda, Inicio y Fin dan 16, 14, 0 y 200 |
| SM-11 | Almacenamiento `1000000`; después `1000001`, `-1` y `1.5` | Válido; T-STO y «Guardar simulación» desactivado en los tres |
| SM-12 | Llamadas `1000000000`; después `1000000001` | Válido; T-APC y «Guardar simulación» desactivado |
| SM-13 | Cambiar el almacenamiento a 200 y las llamadas a 50000 | Ninguna petición; los importes no cambian |

### 6.11 Cotización · C · cliente 1 (ES)

| # | Situación | Resultado esperado |
| --- | --- | --- |
| CO-1 | Respuesta de §8.3 a la cotización inicial | Filas: 1 «1 a 10» 10 «10,00 €» «100,00 €»; 2 «11 a 50» 5 «8,00 €» «40,00 €»; 3 «51 o más» 0 «5,00 €» «0,00 €». «Subtotal» «140,00 €»; «Impuesto (21 %)» «29,40 €»; «Total mensual» «169,40 €» |
| CO-2 | Llevar el slider de 15 a 60 paso a paso, con 50 ms entre pasos, y parar | 1 petición, con `users` 60, 300 ms después del último paso |
| CO-3 | Cambiar a 60 y esperar 299 ms | 0 peticiones; al llegar a 300 ms, 1 |
| CO-4 | Con la cotización de 15 mostrada, pasar a 16 y volver a 15 en menos de 300 ms | 0 peticiones; «Guardar simulación» activo |
| CO-5 | Petición de 60 en curso; cambiar a 100; la respuesta de 60 llega después de la de 100 | Solo se muestra la de 100 |
| CO-6 | Durante la espera de 300 ms y durante la petición | La cotización anterior con T-UPD; «Guardar simulación» desactivado |
| CO-7 | Tras mostrar la de 15, la cotización de 60 no responde | Sigue la de 15; T-NUP con «Reintentar»; «Guardar simulación» desactivado |
| CO-8 | CO-7 y «Reintentar» con respuesta 200 | `POST /pricing/quote` con `users` 60; desaparece T-NUP; se ve la de 60; «Guardar simulación» activo |
| CO-9 | La cotización inicial falla | Sin importes; T-NUP con «Reintentar»; «Guardar simulación» desactivado |
| CO-10 | Cotización con 500, con 404 y con un 422 de `users` | T-NUP con «Reintentar» en los tres |
| CO-11 | 422 con `country` «País no soportado» | T-CNS sin «Reintentar»; sin importes; «Guardar simulación» desactivado |
| CO-12 | Respuesta preparada con los tramos de §8.3 y `subtotal_cents` 14001 | «Subtotal» «140,01 €»: se muestra el del backend, no la suma de los tramos |
| CO-13 | Respuesta para `users` 0 | Los 3 tramos con 0 unidades; todos los importes «0,00 €» |
| CO-14 | Respuesta para `users` 60 | Filas con 10, 40 y 10 unidades e importes «100,00 €», «320,00 €» y «50,00 €»; «Subtotal» «470,00 €»; «Impuesto (21 %)» «98,70 €»; «Total mensual» «568,70 €» |
| CO-15 | Cambiar de divisa con una cotización mostrada | 0 peticiones; importes convertidos |
| CO-16 | La cotización no responde en 10 s | T-NUP con «Reintentar» |

### 6.12 Guardar simulación · C · cliente 1, simulador en 15 usuarios, 200 GB y 50000 llamadas, con la cotización de §8.3 mostrada

| # | Situación | Resultado esperado |
| --- | --- | --- |
| GU-1 | Estado de partida | «Guardar simulación» activo |
| GU-2 | Pulsar «Guardar simulación» | `POST /simulations` con exactamente la petición de la sección 5 de 004 |
| GU-3 | GU-2 con el 201 de la sección 5 de 004 | La tarjeta de HI-1 aparece la primera; `total` + 1; T-SOK; el simulador sigue en 15, 200 y 50000 con la misma cotización |
| GU-4 | Historial vacío y guardado con 201 | Desaparece T-HVA; 1 tarjeta |
| GU-5 | Pulsar dos veces seguidas | 1 petición; T-GDO y los tres valores desactivados mientras espera |
| GU-6 | Sin respuesta; en otra prueba, 500 | T-SKO con «Reintentar», que reenvía el mismo cuerpo; historial y valores sin cambios |
| GU-7 | 201 con `tax_rate_bp` 2150, `tax_cents` 3010 y `total_cents` 17010 | La tarjeta muestra «Impuesto (21,5 %)» «30,10 €» y «Total mensual» «170,10 €» |
| GU-8 | 422 con `customer_id` «El país del cliente no está soportado» | T-CNS sin «Reintentar» |
| GU-9 | 404 | T-SKO sin «Reintentar» |
| GU-10 | Usuarios no válidos; almacenamiento no válido; llamadas no válidas; espera de 300 ms; cotización en curso; cotización fallida; T-CNS | «Guardar simulación» desactivado en los siete |
| GU-11 | Historial en error y guardado con 201 | Nueva petición `GET /customers/1/simulations?limit=50&offset=0` |
| GU-12 | Con USD elegido, guardado con 201 | La nueva tarjeta, en USD |
| GU-13 | Tras T-SOK, cambiar un valor del simulador | T-SOK desaparece |
| GU-14 | Guardar dos veces con los mismos valores, esperando cada respuesta | 2 peticiones y 2 tarjetas |

### 6.13 Errores generales · C

| # | Situación | Resultado esperado |
| --- | --- | --- |
| ER-1 | Todas las peticiones al backend de los casos anteriores | Van a `http://127.0.0.1:8000` |
| ER-2 | Cuerpos enviados en AL-4, CO-1 y GU-2 | Ninguno lleva campos `*_cents`, `tax_rate_bp` ni tipos de cambio |
| ER-3 | El listado responde 500 con un cuerpo HTML que contiene «Traceback» | Solo T-SRV; en pantalla no aparecen «Traceback», «500» ni `internal_error` |
| ER-4 | El listado responde 200 con un cuerpo que no es JSON | T-SRV con «Reintentar» |
| ER-5 | El listado no responde en 10 s | T-CON con «Reintentar» |
| ER-6 | El listado responde 422 | T-SRV con «Reintentar»; no aparece `validation_error` |

### 6.14 Comprobaciones manuales · M

| # | Comprobación | Resultado esperado |
| --- | --- | --- |
| MA-1 | Con 360 px de ancho, recorrer listado, alta, ficha (simulador e historial) y página no encontrada | Sin desplazamiento horizontal; tarjetas apiladas; ningún texto ni importe cortado |
| MA-2 | Con 1280 px de ancho, las mismas pantallas | Ficha e historial en tarjetas, legibles |
| MA-3 | Solo con teclado: flujo 1 (alta) y flujo 3 (simular y guardar) | Se completan; el foco siempre es visible; Intro envía el alta (AL-6) y abre un cliente del listado (LI-17); el slider cumple SM-10; los campos no admiten más caracteres que su límite (LI-13, AL-17) |
| MA-4 | Con el seed: buscar «acme», abrir la ficha, simular 60 usuarios, guardar y elegir USD | La simulación aparece la primera; importes en USD; T-ATR visible |
| MA-5 | Con la API de tasas real | T-RAT con la fecha de la última actualización; las divisas que devuelva la API |
| MA-6 | Parar el backend con la app abierta y arrancarlo de nuevo | T-CON con «Reintentar»; tras arrancarlo, «Reintentar» funciona |
| MA-7 | MA-4 en Chrome, Firefox y Edge, y en Safari si hay equipo | Funciona igual |
| MA-8 | Contraste de textos y botones con las herramientas del navegador | Al menos 4,5:1 |
| MA-9 | Lector de pantalla en el alta y en el simulador | Los errores se leen con su campo; el total actualizado se anuncia sin mover el foco |

## 7. Requisitos no funcionales

- **RNF-1 Una sola fuente de verdad** (constitución, principio 3; ADR 0004): el navegador no calcula ningún importe; solo convierte para mostrar (RN-7). Se comprueba con CO-12 y en revisión.
- **RNF-2 Fluidez** (§6 del 00): espera de 300 ms tras el último cambio; con el backend local, la cotización se ve en menos de 1 s desde que se suelta el slider (objetivo, comprobado en MA-4). Cambiar de divisa no hace ninguna petición.
- **RNF-3 Responsive [E]:** usable desde 360 px de ancho sin desplazamiento horizontal; la ficha y el historial se presentan en tarjetas (MA-1, MA-2).
- **RNF-4 Accesibilidad básica** (§6 del 00): todos los campos con etiqueta visible; los errores asociados a su campo y anunciados; slider manejable con teclado (CA-11.4); foco visible; contraste de al menos 4,5:1; el total del simulador y los avisos (T-REG, T-SOK, errores) se anuncian sin mover el foco.
- **RNF-5 Idioma** (constitución, principio 6): todos los textos visibles en español, los de la sección 5; los nombres técnicos del código, en inglés.
- **RNF-6 Seguridad:** los textos que llegan del backend o de la API de tasas se muestran siempre como texto literal, nunca como formato o código (LI-19); sin secretos (la API de tasas no usa clave); el navegador solo se comunica con el backend y con la API de tasas; los datos de clientes no se guardan en el navegador ni aparecen en la dirección de la app.
- **RNF-7 Calidad** (constitución, principio 6; `AGENTS.md`): TypeScript estricto y sin `any`, lint sin errores, archivos de menos de 300 líneas y funciones de menos de 40.
- **RNF-8 Tests** (§6 del 00): todos los casos U y C son automáticos; como mínimo cubren las tasas y la conversión (RF-3 a RF-5) y el simulador (RF-11 a RF-13).
- **RNF-9 Simplicidad** (constitución, principio 1): ninguna dependencia fuera de las del proyecto base del framework de la ADR 0001; cualquier otra necesita su ADR.
- **RNF-10 Compatibilidad** (§6 del 00): versiones actuales de Chrome, Firefox, Edge y Safari.
- **RNF-11 Arranque sin fricción [E]** (§6 del 00): el README explica cómo levantar el frontend en pocos pasos, con la versión de Node indicada, y que se abre en `http://localhost:4200`.

## 8. Casos límite

- **Slider frente a campo:** valores de 201 a 100 000 dejan el slider al máximo y mandan los del campo (SM-4, SM-9).
- **Rangos:** 0 y 100 000 usuarios valen; 100 001 no (SM-5, SM-7, VE-1, VE-2); lo mismo en los límites de almacenamiento y llamadas (SM-11, SM-12).
- **Valores con forma de número:** signo, decimales, exponente y coma decimal no valen; los ceros a la izquierda sí (VE-2, SM-8).
- **Espera de 300 ms:** a los 299 ms no hay petición y a los 300 ms sí (LI-5, CO-3).
- **Respuestas desordenadas:** solo se muestra la del último texto o valor pedido (LI-12, CO-5).
- **Volver al valor mostrado:** no se pide otra cotización (CO-4).
- **Redondeo exacto:** 1,005, 0,015 y 0,545 suben aunque su representación aproximada quede por debajo (CV-11 a CV-13).
- **Importes convertidos que no cuadran:** en CHF, 131,05 + 27,52 = 158,57, pero el total convertido es 158,58 (DV-5). Es esperado: cada importe se convierte por separado (D-6) y T-ORI avisa de que la conversión es orientativa.
- **JPY con 2 decimales** (CV-9; desde la spec 008, sin decimales) y **miles con 4 cifras** (CV-3).
- **Caducidad exacta de las tasas:** en el instante `time_next_update_unix` ya están caducadas (TC-3, VE-10).
- **Tasas guardadas ilegibles o almacenamiento no disponible** (TC-11, TC-12).
- **Divisa ausente, con valor no válido o desconocida** (VE-6, VE-7, DV-7, DV-8).
- **Tasa de impuesto cambiada entre la cotización y el guardado:** manda el 201 (GU-7).
- **País del cliente retirado del backend:** en el alta (AL-11), la cotización (CO-11) y el guardado (GU-8).
- **Identificador normalizado por el backend:** la ficha muestra el valor guardado (AL-18).
- **Doble pulsación** en «Guardar», «Guardar simulación» y «Cargar más» (AL-15, GU-5, CM-6).
- **Páginas que se solapan** porque otro comercial dio de alta un cliente entre medias (CM-10, CM-11).
- **Zona horaria:** cambio de día y horario de verano (CV-19, CV-20).
- **Texto con aspecto de HTML** en el nombre de la empresa (LI-19).
- **Dirección `{id}` rara** (`abc`): la resuelve el 404 del backend (FI-4).
- **Abrir la app desde `127.0.0.1:4200`:** CORS rechaza las peticiones y se ve T-CON. El README indica la dirección correcta (RNF-11).
- **Guardar dos veces lo mismo:** se permite y crea dos simulaciones (GU-14).

## 9. Fuera de alcance

- Cualquier cambio en el backend; si hiciera falta, iría en una spec propia.
- Editar o borrar clientes o simulaciones, ver una simulación suelta, comparar simulaciones y generar PDF (§3 del 00). Borrar clientes se añadió después, con la spec 007.
- Simular sin cliente o con un país distinto del suyo.
- Cargar en el simulador los valores de una simulación del historial.
- Que el almacenamiento o las llamadas cambien el precio (§10 supuesto 1; D-22).
- Refrescar las tasas con la app abierta (solo al cargarla o con «Reintentar»), ofrecer más divisas, guardar la divisa en el backend o asociarla a un cliente.
- Conservar la búsqueda en la dirección de la app, filtros u orden propios del listado y otros tamaños de página.
- Avisar al salir con datos sin guardar.
- Funcionar sin conexión, salvo las tasas guardadas (§6 del 00).
- Autenticación y roles (ADR 0007), varios idiomas y temas visuales.
- Pruebas automáticas de extremo a extremo en un navegador real: exigirían una dependencia nueva; se sustituyen por las comprobaciones MA-1 a MA-9.
- Despliegue real.

## 10. Criterios de finalización

**Funcionalidad**

- [x] Cada caso U y C de las tablas 6.1 a 6.13 tiene un test automático que lo cita por su identificador y pasa (179 de 179, comprobado en T-17).
- [x] Cada criterio CA-x de la sección 4 está cubierto por al menos un test que lo cita por su identificador y pasa (117 de 117).
- [x] MA-1 a MA-9 se han comprobado a mano y su resultado está anotado (navegador y ancho): MA-1 a MA-6 y MA-8 en Chromium, anotados en `tasks.md` (T-16); MA-7 y MA-9, en la revisión del autor.
- [x] Con backend y frontend arrancados de verdad y el seed cargado, los flujos 1 a 4 del 00 se completan, también sus caminos de error (T-16).
- [x] Los comandos del frontend de `AGENTS.md` (arranque, tests y lint) funcionan y quedan confirmados en ese archivo.
- [x] El README explica cómo levantar el frontend (versión de Node, instalación, arranque y dirección `http://localhost:4200`) y se ha probado en una carpeta limpia: una copia con solo lo que entraría en un commit, instalada de cero con `npm ci`, pasa tests, lint y compilación (T-17).
- [x] La suite del backend sigue pasando sin haber tocado el backend (1051 tests, ruff y mypy; `git status` sin cambios en `backend/`).

**Cumplimiento de la constitución** (comprobación en revisión)

- [x] Principio 1: ninguna dependencia fuera del proyecto base de Angular CLI más angular-eslint y las que instala su esquema, todas con su ADR (0010).
- [x] Principio 2: cada commit de código cita el RF-x o CA-x de esta spec que implementa (los 17 commits de T-01 a T-17).
- [x] Principio 3: el navegador no calcula importes (CO-12 y revisión del código: ninguna operación con `*_cents` fuera de `money.ts`).
- [x] Principio 4: los importes se reciben en céntimos de EUR y nunca se envían ni se guardan convertidos (ER-2 y CA-5.8).
- [x] Principio 5: la suite pasa en cada commit, verificado uno a uno en una copia aparte (tests con el recuento de su tarea, lint y compilación); las correcciones al código generado están anotadas en `ai-workspace/ai-review-log.md` (entradas 32 a 40); el autor revisó la spec y el trabajo y aprobó el cierre.
- [x] Principio 6: TypeScript estricto y lint sin errores; todos los textos visibles en español.

## 11. Decisiones

### 11.1 Respuestas del autor a las preguntas previas

- **P-1. Países del alta:** lista fija con los 7 de RN-4 en el navegador. Si el backend deja de soportar uno, su 422 «País no soportado» aparece junto a «País» (AL-11). Descartadas: un endpoint nuevo de países (reabriría el backend) y texto libre (peor experiencia).
- **P-2. Validación en el navegador:** solo campos obligatorios y longitudes máximas; el resto lo valida el backend y su mensaje se muestra junto al campo. Descartadas: replicar las reglas de 003, incluido el control del DNI/NIE/CIF (duplicaría reglas de negocio que podrían divergir), y no validar nada.
- **P-3. Rango del slider:** de 0 a 200 con paso 1, con un campo numérico hasta 100 000. Descartadas: de 0 a 1 000 (los dos primeros tramos ocuparían el 5 % de la barra) y de 0 a 100 000 (impracticable).
- **P-4. Guardar con la cotización desactualizada:** «Guardar simulación» solo está activo si la cotización mostrada corresponde a los valores actuales: lo que se ve es lo que se guarda. Descartada: activo siempre que los valores sean válidos.
- **P-5. Listas largas:** botón «Cargar más» con «Mostrando {n} de {total}», en el listado y en el historial. Descartadas: mostrar solo los 50 primeros (el historial antiguo quedaría inaccesible) y páginas numeradas.

### 11.2 Decisiones tomadas al redactar

Todas son **[P]** y el autor las confirmó al aprobar la spec. Ninguna contradice el enunciado.

- **D-1. Backend en `http://127.0.0.1:8000`** y no en `localhost:8000`: en Windows, `localhost` añade unos 0,2 s a cada conexión nueva (entrada 15 del log), más que la espera del slider. La app sigue sirviéndose en `http://localhost:4200`, el origen que autoriza CORS.
- **D-2. Simulador e historial en la ficha:** el flujo 3 parte de la ficha y añade la simulación «arriba del historial»; así el comercial la ve aparecer sin cambiar de pantalla. Alternativa: una pantalla propia para el simulador.
- **D-3. Valores iniciales del simulador:** 15 usuarios (ejemplo del enunciado, que ya cruza dos tramos), 0 GB y 0 llamadas. Alternativa: los de la última simulación, que obligaría a esperar al historial.
- **D-4. Espera de 300 ms** en el slider y en el buscador: el 00 pide de 200 a 300 ms para el slider y «un instante» para el buscador; un único valor es más fácil de probar.
- **D-5. Límite de 10 s por petición**, al backend y a la API de tasas, para que ningún estado de carga sea infinito.
- **D-6. Conversión importe a importe con redondeo «mitad hacia arriba» sobre el valor exacto**, la misma regla que RN-5. Los importes convertidos pueden no cuadrar por un céntimo (DV-5); se acepta porque la conversión es orientativa y T-ORI lo avisa. Alternativa: convertir solo el total, que dejaría el desglose en EUR.
- **D-7. Formato español con miles agrupados también con 4 cifras.** La convención española no agrupa los números de 4 cifras («1234,56»); se agrupan para que las columnas de importes se lean igual. Símbolos: «€», «US$» y el código para GBP, CHF y JPY, los del formato español habitual.
- **D-8. JPY con 2 decimales**, porque RN-7 **[E]** fija 2 decimales al mostrar. Mostrarlo sin decimales, lo habitual en yenes, exigiría cambiar RN-7. (Sustituida por la spec 008: al usar la aplicación terminada, el autor corrigió esta decisión, que no se le había preguntado. Desde entonces, RN-7 se lee como «a los céntimos de la divisa», y el yen se muestra sin decimales.)
- **D-9. Fechas en la zona horaria del navegador**, con `dd/mm/aaaa hh:mm` en 24 horas.
- **D-10. Tasas pedidas solo al cargar la app y con «Reintentar»**, válidas hasta `time_next_update_unix`; caducadas, solo sirven de respaldo si falla la API (ADR 0005, §10 supuesto 13).
- **D-11. Atribución siempre visible**, también sin tasas: es más simple y cumple «junto a las tasas».
- **D-12. T-EQ y T-ORI con una divisa distinta de EUR:** el comercial sabe a qué tasa se convierte y que la factura se calcula en EUR.
- **D-13. Divisa recordada no disponible:** se muestra EUR sin borrar la preferencia, que vuelve cuando la divisa esté disponible.
- **D-14. 30 caracteres para el identificador fiscal en el navegador:** el backend admite separadores que luego quita (RN-11) y exige 20 como máximo tras normalizar; 30 deja sitio a formas como `12.345.678-Z`.
- **D-15. Direcciones en español** (`/clientes`…), porque las ve el usuario, y «Página no encontrada» para las demás.
- **D-16. Mensajes propios para los errores que no tienen detalle por campo** (T-CON, T-SRV, T-NUP, T-SKO); los del backend se muestran tal cual.
- **D-17. La ficha se pide antes que el historial y la cotización**, para que un 404 muestre un único mensaje y no tres errores.
- **D-18. Desglose plegado en el historial y desplegado en el simulador:** tarjetas compactas en el móvil; en el simulador el desglose es lo que se explora.
- **D-19. Tras guardar, el simulador conserva valores y cotización**, para ajustar y guardar otra variante.
- **D-20. Países y planes con nombre legible** (CA-6.2) y el código tal cual si el país no se reconoce.
- **D-21. Un `{id}` no numérico en la dirección se resuelve con el 404 del backend** (003 CA-6.3), sin repetir la regla en el navegador.
- **D-22. Almacenamiento y llamadas a la API sin efecto en el precio** (§10 supuesto 1 del 00, RN-9): se guardan con cada simulación, pero el precio solo depende de los usuarios, porque la tarifa del enunciado solo define tramos por usuario. Por eso el simulador no pide otra cotización cuando cambian (CA-11.9, SM-13). Cobrarlos exigiría precios que el enunciado no da.

No quedan dudas abiertas: el supuesto 1 del 00, la última, se cerró como decisión D-22.

## 12. Historial de cambios

| Versión | Cambio |
| --- | --- |
| 1.0 | Versión inicial, redactada tras cinco preguntas al autor (P-1 a P-5) |
| 1.1 | Al planificar: un DOM simulado no reproduce el teclado del slider, la activación con Intro ni el límite de caracteres al escribir, que son comportamientos nativos del navegador. LI-13, LI-17, AL-6, AL-17 y SM-10 comprueban en nivel C el control nativo que los garantiza, y MA-3 comprueba el comportamiento en un navegador real. No cambia ningún CA. El autor pidió seguir con el plan y la implementación y revisar la spec al final |
| 1.1 (cierre) | Sin cambios en los requisitos. Implementada según `plan.md` y `tasks.md`: 319 tests en verde; los 117 CA y los 179 casos U y C con un test que los cita y pasa; copia limpia con `npm ci`, arranque real con el seed y MA-1 a MA-6 y MA-8 comprobados |
| 1.2 (revisión) | El autor revisó la spec y el trabajo realizado y aprobó el cierre. El supuesto 1 del 00 se cierra como decisión D-22, sin cambiar ningún CA; las correcciones al código generado están anotadas en el log (entradas 32 a 40). Spec cerrada |
| 1.2 (edición) | Sin cambios en los requisitos. Estado y referencias al día, y la sección 11 sin el apartado de dudas abiertas, ya cerradas, tras revisar toda la documentación (entrada 49 de `ai-review-log.md`) |
| 1.2 (edición, spec 008) | En JPY, los importes se muestran sin decimales: la spec 008 sustituye CA-5.2 y CA-5.4 en JPY, D-8 y los casos CV-9, CV-10 y CV-15 (YN-1 a YN-3). Aquí solo se añaden notas que remiten a ella, en esos puntos, en la tabla 5.7 y en §8. Es una corrección del autor (P-20 de `prompts.md` y entrada 54 de `ai-review-log.md`), aprobada por él |
