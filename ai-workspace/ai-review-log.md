# Log de revisión del trabajo generado por IA

Registro de los fallos reales encontrados en lo que generó la IA (documentos, código y tests) durante la funcionalidad 001, cómo se detectaron y cómo se corrigieron. Cumple el principio 5 de la constitución: ningún código generado por IA se integra sin que el autor lo haya leído y sepa explicarlo.

## Cómo se revisa

1. **Antes del código:** cada documento (constitución, spec, plan, tareas) se revisa contra `00-spec-first.md` y `AGENTS.md` y lo aprueba el autor antes de pasar al siguiente.
2. **Durante el código:** cada tarea sigue rojo → verde → revisar. Los tests salen de las tablas de la spec y se ejecutan antes de implementar, para confirmar que fallan por el motivo esperado.
3. **Al cerrar cada bloque:** verificación completa con `pytest`, `ruff check`, `ruff format --check` y `mypy` estricto; validación contra los CA de la spec; y aprobación del autor antes de cada commit.
4. **Al cerrar la funcionalidad (T-12):**
   - instalación desde cero en un clon limpio con un entorno virtual nuevo;
   - la suite, el lint y los tipos ejecutados en cada commit de código, uno a uno;
   - comprobación de que cada CA y cada caso de la spec aparecen citados en algún test.

## Registro

| # | Dónde | Qué había generado la IA | Problema | Cómo se detectó | Corrección |
| --- | --- | --- | --- | --- | --- |
| 1 | Constitución, principio 4 | Importes con `Decimal` y «cada presupuesto guarda el tipo de cambio» | Contradecía `00-spec-first.md`: RN-6 exige céntimos enteros y RN-7 dice que la conversión de divisa nunca se guarda. También chocaba con `AGENTS.md` | Revisión cruzada de documentos al empezar la spec 001 | Principio reescrito: céntimos (`*_cents`), puntos básicos (`*_bp`), siempre en EUR, instantánea por simulación y migraciones de Alembic (commit `4495997`) |
| 2 | Constitución, principio 1 | Las justificaciones de dependencias iban «en `docs/`» | Los ADR viven en `ai-workspace/architecture/adr/` | Revisión QA de la spec 001 | Ruta corregida (`4495997`) |
| 3 | Spec 001 v1.0 | Primera versión de la spec, ya aprobada | 38 hallazgos: ambigüedades (mensajes de error, qué es un «entero JSON», normalización del país), contradicciones (un criterio que no se podía probar, un detalle interno dentro de los criterios), casos límite sin cubrir y choques con la constitución | Revisión QA pedida por el autor | v1.1 con 13 RF y 95 casos de prueba (`4495997`) |
| 4 | Aclaración de la spec 001 | Una opción de respuesta decía que la cotización devolvería `"ES"` | El contrato de §8.3 no incluye `country` en la respuesta | Relectura del contrato al redactar la spec | Se mantuvo el contrato y se registró como decisión D-2 |
| 5 | Spec 001 v1.1 frente al encargo del plan | La spec incluía el endpoint `POST /pricing/quote` | El plan pedido cubría solo el núcleo del cálculo, así que no podía cubrir todos los RF | Lectura de los documentos antes de planificar | Spec dividida: 001 v1.2 (núcleo) y 002 (endpoint), sin cambios de comportamiento (`4495997`) |
| 6 | T-01, `backend/.env.example` | Comentario «Copy to .env» | Nada carga un `.env`: la configuración se lee del entorno y no hay `python-dotenv` | Revisión al escribir `config.py` en T-07 | Comentario corregido (`56a9f98`) |
| 7 | T-07, `test_session.py` | Test que comparaba la URL de la base de datos como texto | En Windows, `render_as_string()` escribe `C:` como `C%3A`, así que el test fallaba aunque el código era correcto | Ejecución de la suite | Se comparan objetos URL con `make_url`. El test comprueba lo mismo y con la misma exigencia (`56a9f98`) |
| 8 | T-07, mensaje del commit (antes `aae98cc`) | Mensaje sin ningún RF ni CA | Incumple el principio 2: el modelo `TaxRate` da soporte a RF-4 y RF-13 | Comprobación de los mensajes de commit en T-12 | El autor decidió reescribirlo, ya que la historia no estaba publicada (el remoto solo tenía `87d69d3`). Se hizo un rebase que solo cambia ese mensaje; se comprobó que los 8 commits reescritos conservan exactamente el mismo contenido. Ahora es `56a9f98` |
| 9 | T-08, `tests/integration/conftest.py` | Docstring de 101 caracteres | Supera el límite de 100 de ruff (E501) | `ruff check` en la verificación del bloque | Docstring acortado antes del commit (`332451f`) |
| 10 | T-12, script de verificación | `export PATH="C:/...:$PATH"` en bash | En bash `:` separa rutas, así que `C:` partía la ruta. Se ejecutó un `pytest` ajeno al entorno nuevo y ruff, mypy y alembic no se encontraron | Salida incoherente («1 error», «command not found») | Cada ejecutable se llama por su ruta completa. No afecta al código del repositorio |
| 11 | T-12, comprobación de trazabilidad | Script que buscaba cada CA en el texto completo de los archivos de test | Contaba como cubierto un CA citado solo en el docstring de un archivo. Así dio por cubierto CA-4.2, que ningún test comprobaba entero: no había test de que un país añadido pasa a estar soportado. En T-12 se afirmó que los 29 CA estaban citados, y no era exacto | Revisión requisito por requisito con una trazabilidad más estricta, que solo cuenta los docstrings de cada test y cruza con el resultado de pytest | Nuevo test `test_supported_countries_are_exactly_the_configured_ones`: país sin tasa no soportado, con tasa soportado y, al quitarla, otra vez no soportado. Se comprobó que falla si el servicio deja de rechazar países sin tasa. Se quitó la cita inexacta del docstring del archivo de la migración |

## Reglas que salen de este registro

- **Revisar cada documento nuevo contra `00-spec-first.md` y `AGENTS.md` antes de aprobarlo** (entradas 1, 2 y 5).
- **En tests que deben funcionar en varios sistemas operativos, comparar estructuras y no textos renderizados** (entrada 7).
- **Todo commit que toca código cita el RF o CA al que da soporte, también en las tareas de infraestructura** (entrada 8).
- **Ningún comentario o ejemplo promete un comportamiento que el código no tiene** (entrada 6).
- **La trazabilidad de un CA se comprueba a nivel de test y con su resultado, no buscando el identificador en el archivo** (entrada 11).
