# Plan técnico — 008 Importes en yenes sin decimales

**Estado:** ✅ ejecutado y revisado por el autor · **Spec:** [spec.md](spec.md) v1.0 · **Se apoya en:** el formato de la spec 005 (plan DT-3 y DT-16)

## 1. Archivos

| Archivo | Cambio | RF |
| --- | --- | --- |
| `frontend/src/app/shared/format/money.ts` | `currencyDecimals(code)`; `toHundredths(cents, rate)` pasa a ser `toMinorUnits(cents, rate, decimals)`; `formatMoney` escribe cada importe con los decimales de su divisa | 1 |
| `frontend/src/app/shared/format/money.spec.ts` | YN-1 a YN-8. CV-9, CV-10 y CV-15 salen de la tabla de 005, sustituidos por YN-1 a YN-3; los casos de `toHundredths` siguen, ahora con `toMinorUnits(…, 2)` | 1 |
| `frontend/src/app/features/customers/currency-on-detail.spec.ts` | YN-9 a YN-11 | 1 |

## 2. Algoritmo

```text
currencyDecimals(code):
    Intl.NumberFormat("es-ES", { style: "currency", currency: code })
        .resolvedOptions().maximumFractionDigits          # ISO 4217: EUR 2, JPY 0

toMinorUnits(cents, rate, decimals):
    (dígitos, escala) = decimal exacto de rate            # "161.27" -> (16127, 2), como en 005
    # importe = cents × dígitos ÷ 10^(escala + 2) unidades; en unidades mínimas, × 10^decimals
    return mitad hacia arriba(cents × dígitos ÷ 10^(escala + 2 − decimals))

formatMoney(cents, display):
    decimals = currencyDecimals(display.code)
    mínimas  = display.rate es null ? cents : toMinorUnits(cents, display.rate, decimals)
    return formato(display.code).format(texto decimal de mínimas con decimals decimales)
```

Con 2 decimales, el desplazamiento es la escala de la tasa, igual que el `toHundredths` de 005: EUR, USD, GBP y CHF dan los mismos resultados que antes.

## 3. Decisiones técnicas

| # | Decisión | Por qué | Alternativa descartada |
| --- | --- | --- | --- |
| DT-1 | Los decimales de cada divisa salen de las opciones resueltas de `Intl.NumberFormat` | `Intl` ya aplica ISO 4217 (sección 4), y así no hay una tabla propia que mantener (D-3) | Una tabla `{ JPY: 0 }` en el código |
| DT-2 | Un solo desplazamiento, de escala + 2 − decimales, sobre el producto exacto | Redondea una sola vez (D-2, YN-5) y reutiliza `roundHalfUp` de 005, que ya admite desplazamientos negativos | Redondear a centésimas y después a unidades |
| DT-3 | El formateador ya no fija `minimumFractionDigits` ni `maximumFractionDigits` | `Intl` usa los decimales de la divisa, y recibe el importe ya redondeado como texto con esos mismos decimales, así que no vuelve a redondear | Fijarlos por divisa en cada formateador |

## 4. Comprobaciones previas

Antes de escribir el plan se comprobaron con Node 26.13.1 (ADR 0010) las salidas de `Intl` con `es-ES`, `style: "currency"` y `useGrouping: "always"`:

| Comprobación | Resultado | Consecuencia |
| --- | --- | --- |
| Decimales resueltos de EUR, USD, GBP y CHF | 2 como mínimo y como máximo | Mismo formato que en 005 (CV-1 a CV-8) |
| Decimales resueltos de JPY | 0 como mínimo y como máximo | DT-1 se cumple |
| JPY con «27319», «1613» y «0» como texto | «27.319 JPY», «1.613 JPY» y «0 JPY», con espacio no separable | CA-1.3 se cumple con `Intl`; los tests normalizan el espacio, como en 005 |
| JPY con «1234.56» como texto | «1.235 JPY»: `Intl` redondea por su cuenta | Por eso el texto le llega ya redondeado y sin decimales (DT-3) |

## 5. Tests

- **U:** `money.spec.ts`.
- **C:** `currency-on-detail.spec.ts`, con los ayudantes de 005.
- **Regresión:** la suite completa del frontend. Por CA-1.1 cambian tres casos de 005, CV-9, CV-10 y CV-15, que pasan a ser YN-1 a YN-3 con el resultado nuevo. Los demás casos de formato de 005 no cambian.
