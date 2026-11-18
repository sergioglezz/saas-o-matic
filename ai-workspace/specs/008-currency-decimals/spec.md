# 008 — Importes en yenes sin decimales

**Estado:** ✅ completada (v1.0) y revisada por el autor · **Depende de:** [spec 005](../005-frontend/spec.md) · **Fuentes:** [00-spec-first](../00-spec-first.md), [constitución](../../docs/constitution.md) y [ADR 0005](../../architecture/adr/0005-conversion-de-divisa-en-frontend.md)

Leyenda de origen: **[E]** viene del enunciado; **[P]** es una propuesta, una petición del autor o una decisión D-x de la sección 9.

## 1. Contexto y objetivo

La spec 005 muestra todos los importes con 2 decimales, también en yenes (CA-5.4 y D-8): 169,40 € salen como «27.319,14 JPY». Se decidió así porque RN-7 **[E]** dice «redondeado a 2 decimales al mostrarlo», y D-8 ya avisaba de que mostrar el yen sin decimales exigiría cambiar esa regla.

**De dónde sale esta spec:** al usar la aplicación terminada, el autor vio los yenes con decimales y lo corrigió (prompt P-18 de `ai-workspace/prompts.md`). El yen no tiene subunidad: esos decimales son fracciones de yen que no aparecen en ningún precio real. Pidió mostrarlos sin decimales y lo más parecido a la realidad, redondeando u ocultando los decimales. Como cambia un criterio de una spec aprobada, el cambio entra por una spec nueva, igual que la 006 y la 007 (constitución, principio 2).

**Objetivo:** mostrar cada importe con los decimales que tiene su divisa según la norma ISO 4217 (2 en EUR, USD, GBP y CHF, ninguno en JPY), con un único redondeo «mitad hacia arriba» sobre el valor exacto.

**Cómo se lee RN-7 desde ahora (P-1):** los «2 decimales» de RN-7 son los céntimos de las divisas que los tienen, como las que cita el enunciado (EUR, USD, GBP). En una divisa sin céntimos, el importe se redondea a su unidad. El resto de RN-7 no cambia: la conversión solo sirve para mostrar y nunca se guarda.

**Relación con la spec 005:** en JPY, esta spec sustituye a CA-5.2 (redondeo a 2 decimales), a la parte de CA-5.4 que dice «siempre 2 decimales, también en JPY», a D-8, a los casos CV-9, CV-10 y CV-15, al ejemplo en JPY de la tabla 5.7 y al caso límite «JPY con 2 decimales» de su §8. El resto de RF-5 sigue en vigor: EUR, USD, GBP y CHF no cambian, y la tasa de T-EQ (CA-4.7) no es un importe, así que conserva sus decimales («1 EUR = 161,27 JPY»). El backend no cambia: calcula y guarda en céntimos de EUR (ADR 0002). Con la aprobación del autor, cada documento anterior que fijaba los 2 decimales en yenes lleva una nota que remite aquí: el 00 (§3, RN-7, supuesto 12 y §11), la spec 005 con su plan y el ADR 0005.

## 2. Requisitos funcionales

### RF-1. Decimales de cada divisa

Origen: RN-7 **[E]**, petición del autor **[P]** y P-1; 005 RF-5; D-1 a D-4.

- **CA-1.1** El sistema deberá mostrar cada importe con los decimales de su divisa según ISO 4217: 2 en EUR, USD, GBP y CHF, y ninguno en JPY.
- **CA-1.2** Donde la divisa elegida es JPY, el sistema deberá convertir cada importe por separado como `*_cents` × tasa ÷ 100 y redondearlo a yenes enteros con la regla «mitad hacia arriba», una sola vez y sobre el resultado exacto de esa operación: 1850 céntimos × 161.27 ÷ 100 = 2983,495 → 2983, y no 2984, que saldría de redondear primero a 2983,50.
- **CA-1.3** El sistema deberá escribir los importes en JPY en formato español, sin coma ni parte decimal, con punto como separador de miles también con 4 cifras y, tras un espacio, el código «JPY»: «27.319 JPY», «1.613 JPY», «0 JPY».
- **CA-1.4** El sistema deberá seguir mostrando la tasa de T-EQ con hasta 4 decimales, como dice 005 CA-4.7: «1 EUR = 161,27 JPY».
- **CA-1.5** El sistema deberá seguir mostrando los importes en EUR, USD, GBP y CHF como en 005 CA-5.2 a CA-5.4.

## 3. Contrato observable

No hay textos nuevos, ni cambios en la API ni en lo que se guarda en el navegador. Solo cambia cómo se escriben los importes en JPY:

| Importe en EUR, con JPY 161.27 | Antes (005) | Ahora |
| --- | --- | --- |
| 16940 céntimos | «27.319,14 JPY» | «27.319 JPY» |
| 60520570 | «97.601.523,24 JPY» | «97.601.523 JPY» |
| 0 | «0,00 JPY» | «0 JPY» |

## 4. Casos de prueba

Niveles: **U** = función pura; **C** = pantalla en el DOM simulado, como en 005; **M** = navegador real.

### 4.1 Formato y conversión · U

| # | Situación | Resultado esperado |
| --- | --- | --- |
| YN-1 | 16940 céntimos, JPY 161.27 | «27.319 JPY» (27.319,138 baja; sustituye a 005 CV-9) |
| YN-2 | 60520570, JPY 161.27 | «97.601.523 JPY» (97.601.523,2399 baja; sustituye a CV-10) |
| YN-3 | 0, JPY 161.27 | «0 JPY» (sustituye a CV-15) |
| YN-4 | 5000, JPY 161.27 | «8.064 JPY» (8063,5 exacto sube) |
| YN-5 | 1850, JPY 161.27 | «2.983 JPY» (2983,495 baja: un solo redondeo) |
| YN-6 | 1, JPY 161.27 | «2 JPY» (1,6127 sube) |
| YN-7 | 1000, JPY 161.27 | «1.613 JPY» (miles agrupados con 4 cifras) |
| YN-8 | Decimales de EUR, USD, GBP, CHF y JPY | 2, 2, 2, 2 y 0 |

### 4.2 Ficha del cliente · C · cliente 1 con la cotización y la simulación de partida (005 §6.4)

| # | Situación | Resultado esperado |
| --- | --- | --- |
| YN-9 | Elegir JPY | Simulador e historial con «22.578 JPY», «4.741 JPY» y «27.319 JPY»; ninguna petición nueva |
| YN-10 | Con JPY, abrir el desglose del historial | Precio por usuario «1.613 JPY», «1.290 JPY» y «806 JPY»; importes «16.127 JPY», «6.451 JPY» y «0 JPY» |
| YN-11 | Con JPY, la cabecera | «1 EUR = 161,27 JPY» y T-ORI, sin cambios |

### 4.3 Comprobaciones manuales · M

| # | Comprobación | Resultado esperado |
| --- | --- | --- |
| MA-1 | Backend y frontend reales con el seed: elegir JPY en una ficha con historial y abrir su desglose | Ningún importe con decimales; la tasa de la cabecera conserva los suyos |
| MA-2 | Lo mismo a 360 px de ancho | Sin desplazamiento horizontal |

## 5. Requisitos no funcionales

- **RNF-1 Sin dependencias nuevas:** los decimales de cada divisa los da `Intl.NumberFormat`, que ya se usa para el formato (supuesto 12 del 00).
- **RNF-2 Solo cambia el frontend:** el backend sigue calculando y guardando en céntimos de EUR, sin migraciones (constitución, principio 4).
- **RNF-3 Calidad:** ESLint y TypeScript estricto sin errores; archivos de menos de 300 líneas y funciones de menos de 40.

## 6. Casos límite

- **Doble redondeo:** 2983,495 se queda en 2983 (YN-5).
- **Medio yen exacto:** sube (YN-4).
- **Un céntimo:** 1,6127 yenes se muestran como 2 (YN-6).
- **Importes que no cuadran:** como en 005 D-6, cada importe se convierte por separado, así que la suma de los convertidos puede diferir del total convertido en 1 yen. T-ORI avisa de que la conversión es orientativa.

## 7. Fuera de alcance

- Ofrecer otras divisas o cambiar las que se ofrecen (005 CA-3.5).
- El redondeo de efectivo, como los 5 céntimos del franco suizo en metálico.
- Cambiar el formato de los importes en las otras cuatro divisas o el de la tasa de T-EQ.

## 8. Criterios de finalización

- [x] Cada caso U y C de la sección 4 tiene un test que lo cita y pasa.
- [x] Los tests de la spec 005 que cambian con el nuevo criterio están anotados: CV-9, CV-10 y CV-15, que pasan a ser YN-1 a YN-3.
- [x] MA-1 y MA-2 comprobados en un navegador real.
- [x] Tests, lint y compilación del frontend sin errores.
- [x] Notas en los documentos anteriores que fijaban los 2 decimales en yenes, con su fila en el historial de la spec 005.
- [x] Revisión del autor.

## 9. Decisiones

- **P-1. Petición del autor:** los yenes, sin decimales y lo más parecido a la realidad. Sustituye a 005 D-8.
- **D-1. Redondear, no ocultar los decimales.** El autor dejó abiertas las dos opciones. Ocultarlos es truncar: siempre hacia abajo y con un error de hasta casi 1 yen. Redondear «mitad hacia arriba» sigue la misma regla que el resto de importes (RN-5 y 005 CA-5.2), con un error máximo de medio yen.
- **D-2. Un solo redondeo, sobre el valor exacto.** Redondear primero a centésimas de yen y después a yenes da otro resultado en los importes acabados en «,495» (YN-5).
- **D-3. Los decimales salen de la norma ISO 4217, no de una excepción para JPY.** La regla es la misma para las cinco divisas, y es la que ya aplica `Intl.NumberFormat`.
- **D-4. La tasa de T-EQ no cambia.** No es un importe, y sus decimales son los que permiten comprobar la conversión.

## 10. Historial de cambios

| Versión | Cambio |
| --- | --- |
| 1.0 | Versión inicial, a partir de la corrección del autor (P-18) |
| 1.0 (revisión) | El autor revisó el cambio y lo dio por bueno (P-18). Sin cambios en los requisitos: §1 cita las notas que se añadieron, con su aprobación, en los documentos anteriores, y §8 marca la revisión |
