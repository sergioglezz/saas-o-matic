# Constitución de SaaS-O-Matic

1. **Simplicidad.** Stack cerrado: FastAPI + SQLite y Angular. No entra ninguna dependencia, servicio ni funcionalidad que no pida la spec sin una justificación escrita en `docs/`.
2. **La spec manda.** Cada cambio de código responde a un requisito identificado de la spec y lo cita en el commit. Si código y spec divergen, se actualiza primero la spec.
3. **Capas separadas.** Las reglas de negocio (precios por tramos, impuestos, identificadores fiscales) son Python puro, sin FastAPI ni SQL. La API solo valida y traduce, y el acceso a SQLite vive únicamente en la capa de repositorio.
4. **Dinero exacto y trazable.** Importes en céntimos enteros (`*_cents`, `INTEGER` en SQLite) y tasas en puntos básicos (`*_bp`), nunca `float`; se guardan siempre en EUR y el redondeo es explícito. Cada simulación guarda una instantánea de su cálculo, y el esquema solo cambia con migraciones de Alembic.
5. **Tests y revisión humana.** Cada regla de negocio tiene test unitario y cada endpoint, test de integración. La suite pasa antes de cada commit, y ningún código generado por IA se integra sin que el autor lo haya leído y sepa explicarlo.
6. **Calidad, seguridad e idioma.** ruff, mypy, ESLint y TypeScript strict pasan sin errores. Se valida toda entrada y no hay secretos en el repo. Código e identificadores en inglés; documentación y mensajes al usuario en español.
