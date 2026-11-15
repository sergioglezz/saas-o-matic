# SaaS-O-Matic

Herramienta interna para que el equipo comercial simule y presupueste suscripciones SaaS multi-divisa. Este README se completará con las instrucciones de arranque al cerrar el proyecto; por ahora recoge las decisiones y supuestos ya tomados.

## Decisiones y supuestos

### Tasas de impuesto por defecto (spec 001, decisión D-3)

El enunciado pide sumar «el impuesto correspondiente al país del cliente», pero no da valores. Se adoptan estas tasas como supuesto:

| País | Código | Tasa | En puntos básicos |
| --- | --- | --- | --- |
| España | ES | 21 % | 2100 |
| Portugal | PT | 23 % | 2300 |
| Francia | FR | 20 % | 2000 |
| Alemania | DE | 19 % | 1900 |
| Italia | IT | 22 % | 2200 |
| Reino Unido | GB | 20 % | 2000 |
| Estados Unidos | US | 0 % | 0 |

- Las tasas son datos, no código. Viven en la tabla `tax_rates` y las inserta la primera migración, así que están disponibles nada más preparar la base de datos, sin cargar los datos de demostración.
- Cambiar, añadir o quitar una tasa no exige tocar el cálculo.
- Cotizar para un país sin tasa configurada se rechaza como «país no soportado».
- Estados Unidos tiene 0 % porque no hay IVA federal. El impuesto sobre ventas de cada estado no se modela.

**Fuera de alcance:** el IGIC de Canarias, los impuestos de Ceuta y Melilla, y la inversión del sujeto pasivo en operaciones entre empresas de la UE.
