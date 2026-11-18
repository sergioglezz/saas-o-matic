# SaaS-O-Matic: frontend

Dashboard en Angular 22 con Tailwind CSS 4 (specs 005 y 006). El arranque, las decisiones visibles y los supuestos están en el [README principal](../README.md); las herramientas y versiones, en los ADR [0010](../ai-workspace/architecture/adr/0010-herramientas-del-frontend.md) y [0011](../ai-workspace/architecture/adr/0011-tailwind-css.md).

- `npm start`: servidor de desarrollo en `http://localhost:4200`, con el backend en `http://127.0.0.1:8000`.
- `npm test`: tests en una sola pasada.
- `npm run lint`: lint con las reglas de capas del ADR 0010.
- `npm run build`: compilación de producción en `dist/`.
