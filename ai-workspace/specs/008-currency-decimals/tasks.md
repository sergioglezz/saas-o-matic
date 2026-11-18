# Tareas — 008 Importes en yenes sin decimales

**Estado:** ✅ todas las tareas completadas y revisadas por el autor · **Spec:** [spec.md](spec.md) v1.0 · **Plan:** [plan.md](plan.md)

## Reglas de ejecución

- Una tarea cada vez, con el ciclo rojo → verde → revisar.
- **Verificación:** `npm test`, `npm run lint` y `npm run build` en `frontend/`.
- Sin commits sin la autorización del autor.

## Progreso

| Tareas | RF | Estado |
| --- | --- | --- |
| T-01 a T-05 | RF-1 | ✅ Completadas |

## Tareas

- [x] **T-01. Spec, plan y tareas**
  - **Hecho cuando:** los tres documentos existen y la sección 4 del plan recoge las salidas de `Intl` comprobadas con Node.
  - **Resultado:** `spec.md`, `plan.md` y `tasks.md` de la 008.

- [x] **T-02. Decimales de cada divisa en el formato**
  - **RF:** RF-1 (CA-1.1 a CA-1.3 y CA-1.5). Plan DT-1 a DT-3. **Casos:** YN-1 a YN-8.
  - **Hecho cuando:** esos casos pasan, después de verlos fallar, y CV-1 a CV-8 y CV-11 a CV-14 de 005 siguen en verde.
  - **Resultado:** primero, los tests no compilaban porque faltaban `currencyDecimals` y `toMinorUnits`. Con dos esbozos que hacían lo mismo que el código de 005, fallaron por el motivo esperado (YN-1: «27.319,14 JPY» en vez de «27.319 JPY»; YN-8: 2 decimales en JPY). Con el código, `money.spec.ts` queda en verde; CV-9, CV-10 y CV-15 salen de la tabla de 005 y pasan a ser YN-1 a YN-3 (plan §5).

- [x] **T-03. Yenes en la ficha del cliente**
  - **RF:** RF-1 (CA-1.1, CA-1.2 y CA-1.4). **Casos:** YN-9 a YN-11.
  - **Hecho cuando:** esos casos pasan y la suite del frontend sigue en verde, con lint y compilación.
  - **Resultado:** YN-9 y YN-10 fallaron antes del código («22.577,80 JPY») y pasan después. YN-11 pasa desde el principio, como se esperaba: comprueba que la tasa de T-EQ no cambia. Frontend: 378 tests (365 antes: 16 nuevos y 3 de 005 sustituidos), lint, Prettier y compilación de producción en verde.

- [x] **T-04. Comprobación real y documentación**
  - **Casos:** MA-1 y MA-2. README, guía de `ai-workspace`, prompt P-20 y entrada del log.
  - **Hecho cuando:** MA-1 y MA-2 comprobados y anotados aquí.
  - **Resultado:** backend y frontend reales en marcha, con la base de datos del autor y las tasas reales del 18/11/2026 (1 EUR = 175,2828 JPY), en el navegador integrado.
    - **MA-1 ✅** Ficha de Acme Telecom S.L. con JPY: los 25 importes en yenes de la página (simulador, tres simulaciones y un desglose abierto) salen sin decimales, y el único número con decimales es la tasa de la cabecera, «1 EUR = 175,2828 JPY». Las cifras coinciden con un cálculo a mano: 16940 céntimos → «29.693 JPY» y, en el desglose, 32000 céntimos × 175,2828 = 56.090,496 → «56.090 JPY», un caso real en el que redondear dos veces habría dado 56.091. Con USD, los importes siguen con 2 decimales («109,99 US$»). La consola no muestra errores. La divisa se dejó en JPY, como estaba.
    - **MA-2 ✅** A 360 px, con el desglose abierto, la página mide 360 px de ancho: sin desplazamiento horizontal.
  - README: la conversión y el formato del frontend, con una sección «Yenes sin decimales (spec 008)». Guía de `ai-workspace` con la spec 008, prompt P-20 y entrada 54 del log.

- [x] **T-05. Notas en los documentos anteriores**
  - **Hecho cuando:** ningún documento dice que los yenes se muestran con 2 decimales sin remitir a esta spec, y cada spec aprobada que cambia lo registra en su historial (log, entrada 53).
  - **Resultado:** tras revisar el cambio, el autor aprobó tocar los documentos aprobados (P-20). Notas en el 00 (§3, RN-7, supuesto 12 y orden de implementación), en la spec 005 (CA-5.2, CA-5.4, tabla 5.7, CV-9, CV-10, CV-15, §8, D-8 y una fila en su historial), en su plan (archivos, interfaces, algoritmo y prototipo) y en el ADR 0005 (estado y decisión). P-20 recoge los dos mensajes del autor con una redacción cuidada, y la guía de `ai-workspace` y el log presentan el cambio como una corrección del autor a la IA. Se buscaron con `grep` todas las menciones de JPY, «2 decimales», RN-7, D-8, CV-9, CV-10 y CV-15 en la documentación, y se comprobaron los enlaces y las anclas de los documentos tocados.
