# SPEC-STOCK-002 — Consultar stock

## Metadata

- ID: SPEC-STOCK-002
- Requirement: ERF-04 — Consultar stock
- Service: Stock
- Status: VALIDATED
- Version: 1.0.0
- Priority: Alta

## Objective

Permitir consultar la cantidad disponible de un producto para validar
disponibilidad antes de una venta y supervisar existencias.

## Scope

* Devolver la cantidad disponible de un producto por `id`.
* Incluir marca temporal de última actualización del inventario.

## Out of Scope

* Modificar cantidades (ver SPEC-STOCK-003).
* Reservar o bloquear stock (sin ERF que lo respalde; no inventar).

## Actors

* Vendedor o encargado de ventas.
* Responsable de inventario.
* Servicio Sales (validación previa a la venta).

## Preconditions

* El producto existe en `stock_db`.

## Functional Requirements

* FR-01: El sistema debe devolver `producto_id` y `cantidad` disponible.
* FR-02: El sistema debe devolver `updated_at` del registro de inventario.

## Business Rules

* BR-01: La cantidad nunca es negativa (`CHECK >= 0`).
* BR-02: Solo Stock puede informar el stock oficial.

## API Contract

Endpoint: `GET /api/v1/products/{id}/stock`
Method: GET
Request: path `id: int`
Response: `200 {producto_id, cantidad, updated_at}`; `404` si el producto no existe.

## Validation Rules

* `id` entero positivo; inválido → 422.

## Error Handling

* `404` producto inexistente, sin efectos secundarios.
* `422` id inválido.

## Acceptance Criteria

### AC-ERF04-01 — Consultar stock existente

Given existe un producto con inventario registrado
When se solicita `GET /api/v1/products/{id}/stock`
Then el servicio debe responder 200
And debe devolver la cantidad disponible y su `updated_at`.

### AC-ERF04-02 — Producto inexistente

Given el producto no existe
When se solicita su stock
Then el servicio debe responder 404
And no debe modificar ningún registro.

## Open Questions

No aplica en el alcance actual.

## Traceability

Requirement: ERF-04
Endpoint: GET /api/v1/products/{id}/stock
Service: Stock
Tests: Pendiente (futuros: test_get_stock_existing, test_get_stock_unknown_id_404)

## Technical Notes

* Lectura de la tabla `inventories` por `producto_id`; índice único en
  `producto_id`. Schema futuro `StockRead`.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-09-29 | IMPLEMENTED → VALIDATED (pytest en verde) | Tests confirman AC-ERF04-01..02 |
| 1.0.0 | 2026-09-29 | Approved for implementation (REVIEW passed) | Stock vertical, second batch |
| 0.1.0 | 2026-09-29 | Initial specification | Initial SDD setup |
