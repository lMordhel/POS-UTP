# SPEC-STOCK-001 — Consultar productos

## Metadata

- ID: SPEC-STOCK-001
- Requirement: ERF-02 — Consultar productos
- Service: Stock
- Status: VALIDATED
- Version: 1.0.0
- Priority: Alta

## Objective

Permitir consultar el catálogo de productos de la microempresa, incluyendo su
stock disponible agregado de solo lectura, para apoyar las operaciones de venta
y la supervisión de inventario.

## Scope

* Listar productos paginados con filtros básicos.
* Obtener el detalle de un producto con su stock.
* El `stock` devuelto es un agregado de lectura del inventario (no editable
  por estos endpoints).

## Out of Scope

* Mutar stock (ver SPEC-STOCK-003).
* Crear/editar/eliminar productos (ver SPEC-STOCK-004).
* Reportes o analítica (sin ERF que los respalde).

## Actors

* Vendedor o encargado de ventas (consulta para vender).
* Responsable de inventario.
* Administrador de la microempresa.
* Servicio Sales (consumidor HTTP del catálogo).

## Preconditions

* Servicio Stock operativo con acceso a `stock_db`.
* Existen productos registrados (si no, lista vacía válida).

## Functional Requirements

* FR-01: El sistema debe listar productos con paginación (`skip`, `limit`).
* FR-02: El sistema debe permitir filtrar por texto (`q` en código/nombre) y
  por estado (`activo`).
* FR-03: El sistema debe devolver cada producto con su cantidad disponible.
* FR-04: El sistema debe devolver el detalle de un producto por `id`.

## Business Rules

* BR-01: Solo el servicio Stock es dueño del catálogo y del inventario
  (ver OQ-ERF02-01).
* BR-02: El `stock` expuesto aquí es derivado de `inventories`; no se acepta
  como entrada en estos endpoints.

## API Contract

Endpoint: `GET /api/v1/products`
Method: GET
Request (query): `q?: string, activo?: boolean, skip: int >= 0 = 0, limit: int 1..100 = 20`
Response: `200` lista paginada de ProductRead
  `[{id, codigo, nombre, descripcion, precio, activo, stock, created_at, updated_at}]`

Endpoint: `GET /api/v1/products/{id}`
Method: GET
Request: path `id: int`
Response: `200` ProductRead; `404` si no existe.

## Validation Rules

* `skip >= 0`, `1 <= limit <= 100` (fuera de rango → 422).
* `q` con strip de espacios; cadena vacía equivale a sin filtro.

## Error Handling

* `404` producto inexistente en detalle. Sin efectos secundarios.
* `422` parámetros de paginación inválidos.

## Acceptance Criteria

### AC-ERF02-01 — Listar productos paginados

Given existen productos registrados
When se solicita `GET /api/v1/products?skip=0&limit=20`
Then el servicio debe responder 200
And debe devolver la lista con su stock agregado.

### AC-ERF02-02 — Filtrar productos

Given existen productos activos e inactivos
When se solicita con `q` o `activo=false`
Then el servicio debe devolver solo los coincidentes.

### AC-ERF02-03 — Producto inexistente

Given el producto no existe
When se solicita `GET /api/v1/products/{id}`
Then el servicio debe responder 404
And no debe modificar ningún registro.

## Open Questions

* OQ-ERF02-01: DECIDED 2026-09-29 → dueño = Stock; Ventas solo consume por HTTP
  (ADR-002 APPROVED). Texto original: La matriz de trazabilidad del documento
  asigna ERF-02 al "Servicio de Ventas", pero la propiedad arquitectónica del
  catálogo es de Stock (ADR-002). ¿Se confirma dueño = Stock y Ventas solo
  consume por HTTP? Sin resolver; no implementar hasta decisión.

## Traceability

Requirement: ERF-02
Endpoint: GET /api/v1/products, GET /api/v1/products/{id}
Service: Stock (propuesto; ver OQ-ERF02-01)
Tests: Pendiente (futuros: test_list_products_paginated, test_list_products_filtered, test_get_product_unknown_id_404)

## Technical Notes

* Schemas Pydantic futuros: `ProductRead` (salida, `from_attributes=True`);
  validación de query con `Field(ge=0)` / `Field(ge=1, le=100)` (skill pydantic).
* Solape con ERF-08: mismo endpoint base, distinto propósito académico
  (operativa vs. supervisión); no duplicar implementación.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-09-29 | IMPLEMENTED → VALIDATED (pytest en verde) | Tests confirman AC-ERF02-01..03 |
| 1.0.0 | 2026-09-29 | Approved for implementation (REVIEW passed) | Stock vertical, second batch |
| 0.1.0 | 2026-09-29 | Initial specification | Initial SDD setup |
