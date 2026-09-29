# SPEC-STOCK-004 — Gestionar inventario (CRUD de productos)

## Metadata

- ID: SPEC-STOCK-004
- Requirement: ERF-06 — Gestionar inventario
- Service: Stock
- Status: VALIDATED
- Version: 1.0.0
- Priority: Alta

## Objective

Permitir gestionar el catálogo de productos (crear, actualizar, desactivar)
y su registro inicial de inventario.

## Scope

* Crear producto con cantidad inicial.
* Actualizar datos del catálogo (código, nombre, descripción, precio, activo).
* Desactivación lógica (borrado lógico).
* Consultas puntuales de apoyo (el listado general vive en SPEC-STOCK-001).

## Out of Scope

* Ajustes posteriores de stock (ver SPEC-STOCK-003).
* Eliminación física de registros.
* Proveedores, categorías, promociones (fuera de alcance).

## Actors

* Responsable de inventario.
* Administrador de la microempresa.

## Preconditions

* Servicio Stock operativo con acceso a `stock_db`.

## Functional Requirements

* FR-01: Crear producto con `codigo` único, datos válidos y cantidad inicial `>= 0`.
* FR-02: Actualizar parcialmente datos del catálogo sin alterar cantidad
  (la cantidad solo cambia vía SPEC-STOCK-003).
* FR-03: Desactivar producto (borrado lógico `activo=false`).
* FR-04: Los productos inactivos no deben ofrecerse para nuevas ventas
  (regla de consumo en Sales; aquí se expone el flag).

## Business Rules

* BR-01: `codigo` único; duplicado → 409.
* BR-02: `precio > 0`; `cantidad inicial >= 0`.
* BR-03: No hay borrado físico en el alcance actual.

## API Contract

Endpoint: `POST /api/v1/products`
Method: POST
Request: `{codigo, nombre, descripcion?, precio, cantidad_inicial >= 0}`
Response: `201` ProductRead; `409` código duplicado; `422` validación.

Endpoint: `PUT /api/v1/products/{id}`
Method: PUT
Request: `{codigo?, nombre?, descripcion?, precio?, activo?}` (sin cantidad)
Response: `200` ProductRead; `404` si no existe; `409` código duplicado; `422` validación.

Endpoint: `DELETE /api/v1/products/{id}`
Method: DELETE
Request: path `id`
Response: `200` o `204` con producto desactivado (`activo=false`); `404` si no existe.

## Validation Rules

* `codigo`: no vacío, strip, longitud máxima a definir en diseño (sugerido <= 32).
* `nombre`: no vacío (strip); `precio`: número > 0 con 2 decimales.
* `cantidad_inicial`: entero >= 0.

## Error Handling

* `409` código duplicado.
* `404` producto inexistente en PUT/DELETE.
* `422` validación de campos.

## Acceptance Criteria

### AC-ERF06-01 — Crear producto válido

Given datos válidos con código único
When se solicita `POST /api/v1/products`
Then el servicio debe responder 201
And debe crear el producto con su inventario inicial.

### AC-ERF06-02 — Código duplicado

Given existe un producto con el mismo código
When se intenta crear otro con ese código
Then el servicio debe responder 409
And no debe crear registros.

### AC-ERF06-03 — Actualizar producto

Given existe un producto
When se solicita `PUT /api/v1/products/{id}` con datos válidos
Then el servicio debe responder 200 con el producto actualizado
And no debe alterar la cantidad de inventario.

### AC-ERF06-04 — Desactivar producto

Given existe un producto activo
When se solicita `DELETE /api/v1/products/{id}`
Then el servicio debe marcarlo inactivo
And las ventas nuevas no deben ofrecerlo.

### AC-ERF06-05 — Validaciones

Given datos inválidos (precio <= 0, código vacío, cantidad negativa)
When se solicita crear o actualizar
Then el servicio debe responder 422.

## Open Questions

No aplica en el alcance actual.

## Traceability

Requirement: ERF-06
Endpoint: POST /api/v1/products, PUT /api/v1/products/{id}, DELETE /api/v1/products/{id}
Service: Stock
Tests: Pendiente (futuros: test_create_product_valid, test_create_product_duplicate_codigo_409, test_update_product_valid, test_deactivate_product, test_create_product_invalid_422)

## Technical Notes

* Schemas futuros: `ProductCreate` (con `cantidad_inicial`), `ProductUpdate`
  (sin cantidad), `ProductRead` (skill pydantic). Transacción: crear `products`
  + `inventories` de forma atómica.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-09-29 | IMPLEMENTED → VALIDATED (12/12 pytest en verde) | Tests confirman AC-ERF06-01..05 |
| 1.0.0 | 2026-09-29 | Approved for implementation (REVIEW passed) | User decision: start with SPEC-STOCK-004 |
| 0.1.0 | 2026-09-29 | Initial specification | Initial SDD setup |
