# ADR 0007 — Sin autenticación ni roles

Estado: aceptado

## Contexto

El enunciado habla solo de «nuestro equipo comercial»: no menciona login, roles ni permisos (§2 del documento 00, supuesto 12 de §10). Es una herramienta interna para decenas de usuarios a la vez, con un único tipo de usuario, el comercial (§2 y §6 del 00).

## Decisión

- No hay login, roles ni permisos: todo usuario que abre la app puede hacer todo.
- Es una decisión de alcance y se documenta en el README.
- Las medidas de seguridad que no dependen de saber quién es el usuario sí se aplican: CORS limitado al origen del frontend, toda entrada validada con Pydantic, consultas por ORM, errores sin detalles internos y sin secretos en el repositorio (§6 del 00).

## Alternativa descartada

Login con usuario y contraseña, con o sin roles. Añadiría tablas, pantallas, dependencias y casos de prueba que el enunciado no pide y que ningún criterio de evaluación menciona (§9 del 00).

## Consecuencias

- Quien accede a la app puede leer y crear clientes con identificadores fiscales y emails, que pueden ser datos personales. Se acepta porque el despliegue es solo local y los datos de demostración son inventados (§5 y §6 del 00).
- No queda registro de qué comercial creó cada cliente o simulación.
- Añadir autenticación más adelante exige una spec nueva y un ADR (principio 1 de la constitución y `AGENTS.md`).
