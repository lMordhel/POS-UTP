# SPEC-STOCK-003 — Actualizar stock

## Metadata

- ID: SPEC-STOCK-003
- Requirement: ERF-05 — Actualizar stock
- Service: Stock
- Status: VALIDATED
- Version: 1.0.0
- Priority: Alta

## Objective

Permitir actualizar la cantidad disponible de un producto. Es el único punto
de escritura del inventario y el que descuenta existencias tras una venta.

## Scope

* Ajustar el inventario de un producto existente vía `PATCH`.
* Devolver el stock actualizado.

## Out of Scope

* La semántica exacta del cuerpo (absoluto vs. delta) está pendiente de
  decisión (OQ-ERF05-01); esta SPEC no la impone.
* Reservas, lotes, almacenes múltiples (fuera del alcance académico).

## Actors

* Responsable de inventario (ajuste manual futuro).
* Servicio Sales (descuento por venta confirmada).

## Preconditions

* El producto existe y tiene registro en `inventories`.

## Functional Requirements

* FR-01: El sistema debe actualizar el inventario solo vía este endpoint.
* FR-02: El sistema debe rechazar cantidades resultantes negativas.
* FR-03: El sistema debe devolver el stock actualizado tras el ajuste.

## Business Rules

* BR-01: `cantidad` resultante `>= 0`; violación → 422/409 según decisión.
* BR-02: Ajustes concurrentes no deben dejar stock negativo (control de
  concurrencia a definir en diseño; sin inventar mecanismos aún).

## API Contract

Endpoint: `PATCH /api/v1/products/{id}/stock`
Method: PATCH
Request (APPROVED 2026-09-29, opción B): `{delta: int (!= 0), motivo?: string <= 120}`
  (incremento/decremento sobre la cantidad actual).
Response: `200` StockRead `{producto_id, cantidad, updated_at}`; `404` si no
  existe; `422` validación (delta 0, cuerpo vacío); `409` si el ajuste dejaría
  stock negativo o es insuficiente.

## Validation Rules

* Cantidad/delta enteros; el resultado nunca negativo.
* Cuerpo vacío o campos extra → 422.

## Error Handling

* `404` producto inexistente, sin modificar registros.
* `422` cuerpo inválido.
* `409` stock insuficiente / ajuste inválido de negocio.

## Acceptance Criteria

### AC-ERF05-01 — Actualizar stock correctamente

Given existe un producto con stock disponible
When se solicita una actualización válida
Then el servicio debe actualizar el inventario
And debe devolver el stock actualizado.

### AC-ERF05-02 — Producto inexistente

Given el producto no existe
When se solicita actualizar su stock
Then el servicio debe responder 404
And no debe modificar ningún registro.

### AC-ERF05-03 — Cantidad inválida

Given existe un producto
When se solicita una actualización con valor inválido o que dejaría stock negativo
Then el servicio debe responder 422 o 409
And no debe modificar el inventario.

## Open Questions

* OQ-ERF05-01: DECIDED 2026-09-29 → opción B) delta (+/-) con `motivo` para
  auditar la saga de venta. La SPEC sigue DRAFT hasta su REVIEW; el contrato
  definitivo se fijará al aprobarla. Texto original: ¿`PATCH
  /products/{id}/stock` representa A) cantidad absoluta o B) delta (+/-)?
  Recomendación técnica: B con `motivo` para auditar la saga
  de venta, pero NO implementar hasta aprobación.

## Traceability

Requirement: ERF-05
Endpoint: PATCH /api/v1/products/{id}/stock
Service: Stock
Tests: Pendiente (futuros: test_update_stock_valid_quantity, test_update_stock_unknown_id_404, test_update_stock_negative_rejected)

## Technical Notes

* Al aprobarse la semántica, definir schemas `StockUpdate` / `StockRead`
  (skill pydantic) y documentar concurrencia mínima (transacción por fila).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-09-29 | IMPLEMENTED → VALIDATED (pytest en verde) | Tests confirman AC-ERF05-01..03 |
| 1.0.0 | 2026-09-29 | Approved; contract fixed to delta (OQ-ERF05-01 DECIDED) | User decision: delta + motivo |
| 0.1.0 | 2026-09-29 | Initial specification | Initial SDD setup |
