# Plan técnico — 007 Borrar cliente

Estado: v1.0, pendiente de la revisión del autor junto con la spec · Spec: `spec.md` v1.0 · Base: el código de 003, 004, 005 y 006

## 1. Archivos

| Archivo | Cambio | RF |
| --- | --- | --- |
| `backend/app/repositories/simulations.py` | `delete_for_customer(customer_id) -> int`: borra los tramos y las simulaciones del cliente, sin confirmar la transacción | 1 |
| `backend/app/repositories/customers.py` | `delete(customer_id)`: borra el cliente y confirma la transacción; si falla, la deshace | 1 |
| `backend/app/services/customers.py` | `delete_customer(id, customers, simulations)`, el protocolo `CustomerHistory` y `delete` en `CustomerStore` | 1 |
| `backend/app/api/dependencies.py` | `get_customer_history`: el repositorio de simulaciones como `CustomerHistory`, sobre la sesión de la petición | 1 |
| `backend/app/api/customers.py` | `DELETE /customers/{customer_id}`: valida el `{id}`, llama al servicio y responde 204 | 1 |
| `backend/app/api/customers_docs.py` | `DELETE_RESPONSES` con 204 y 404 | 1 |
| `backend/app/main.py` | `DELETE` en los métodos de CORS | 1 |
| `backend/tests/integration/test_customer_deletion.py` | BR-8 y BR-11 (D) | 1 |
| `backend/tests/api/test_customers_delete.py` | BR-1 a BR-7, BR-9 y BR-10 (I) | 1 |
| `backend/tests/api/test_customers_protocol.py` | ER-3 de 003: `Allow` pasa a «DELETE, GET» y `DELETE` sale de los métodos rechazados (CA-1.6) | 1 |
| `backend/tests/api/test_simulations_protocol.py` | ER-10 de 004: sondea con `PUT` en lugar de `DELETE` y la ficha espera «DELETE, GET» (CA-1.6) | 1 |
| `frontend/src/app/core/api/customers-api.ts` | `remove(id)` | 2 |
| `frontend/src/app/shared/texts.ts` | Textos T7 | 2 |
| `frontend/src/app/features/customers/delete-customer.ts` | Nuevo: botón, confirmación y estado del borrado | 2 |
| `frontend/src/app/features/customers/customer-detail-page.*` | Usa `app-delete-customer` en la tarjeta; pasa el total del historial y atiende el 404 | 2 |
| `frontend/src/app/features/customers/customer-list-page.*` | Aviso T7-OK leído del estado de la navegación | 2 |
| `frontend/src/app/features/customers/delete-customer.css` | Botón de peligro y caja de confirmación, con los colores del tema de 006 (en el componente, para que `styles.css` no crezca) | 2 |
| `frontend/src/app/features/customers/delete-customer.spec.ts` | BF-1 a BF-9 (C) | 2 |

## 2. Algoritmos

```text
delete_customer(id, customers, simulations):
    si customers.get(id) es None: CustomerNotFoundError           # CA-1.3
    removed = simulations.delete_for_customer(id)                  # tramos y simulaciones, sin commit
    customers.delete(id)                                           # commit: todo o nada (CA-1.2)
    return removed
```

Los dos repositorios reciben la misma `Session`: FastAPI resuelve `get_db_session` una sola vez por petición. Si `customers.delete` falla, hace `rollback()` y las simulaciones vuelven (BR-8).

**Confirmación (frontend):** estados `closed`, `asking`, `deleting` y `failed`. «Borrar cliente» pasa a `asking` y lleva el foco a la caja; «Cancelar» o Escape vuelven a `closed` y el foco al botón; «Sí, borrar» pasa a `deleting` y pide la `DELETE`. Con 204, el componente emite `deleted` y la ficha navega a `/clientes` con el estado `{ deleted: empresa }`; con 404, emite `missing` y la ficha muestra T-NFC; con cualquier otro fallo, `failed` con «Reintentar».

## 3. Decisiones técnicas

| # | Decisión | Por qué |
| --- | --- | --- |
| DT-1 | Protocolo `CustomerHistory` en el servicio de clientes, con solo `delete_for_customer` | El servicio de clientes no importa el de simulaciones (sin dependencias circulares) y cada repositorio sigue tocando solo sus tablas |
| DT-2 | Borrado de tramos y simulaciones con sentencias `DELETE`, en ese orden | Respeta las claves ajenas sin cargar las filas |
| DT-3 | Componente propio para la confirmación, dentro de la tarjeta | La ficha no crece y el componente se prueba entero (BF) |
| DT-4 | El método del cliente de la API se llama `remove` | `delete` es válido como nombre de método en TypeScript, pero al leerlo se confunde con el operador `delete` |

## 4. Tests

- **D:** `test_customer_deletion.py`, con la base de datos de prueba de 003 y 004.
- **I:** `test_customers_delete.py`, con el cliente de pruebas de la API.
- **C:** `delete-customer.spec.ts`, con los ayudantes de 005.
- **Regresión:** las suites completas. Por CA-1.6 cambian dos tests anteriores: ER-3 de 003 y ER-10 de 004, que comprobaba con `DELETE` el `Allow` de la ficha. Los dos siguen comprobando lo mismo, ahora con «DELETE, GET».
