# SPEC-SALES-003 — Consultar ventas

## Metadata

- ID: SPEC-SALES-003
- Requirement: ERF-07 — Consultar ventas
- Service: Sales
- Status: VALIDATED
- Version: 1.0.0
- Priority: Media

## Objective

Permitir consultar las ventas registradas, en lista paginada y por detalle con
sus líneas, para supervisión y operativa.

## Scope

* Listar ventas paginadas.
* Obtener una venta por `id` con sus líneas.

## Out of Scope

* Filtros por fechas, totales, anulaciones, reportes (sin ERF; no inventar).
* Edición o borrado de ventas.

## Actors

* Vendedor o encargado de ventas.
* Administrador de la microempresa.

## Preconditions

* Servicio Sales operativo con acceso a `ventas_db`.

## Functional Requirements

* FR-01: Listar ventas con paginación (`skip`, `limit`).
* FR-02: Devolver cada venta con `id`, `fecha`, `total`, `estado` y sus líneas.
* FR-03: Detalle por `id` con líneas completas.

## Business Rules

* BR-01: Solo lectura; ningún endpoint de esta SPEC muta datos.
* BR-02: El `total` mostrado es el calculado y persistido al registrar.

## API Contract

Endpoint: `GET /api/v1/sales`
Method: GET
Request (query): `skip: int >= 0 = 0, limit: int 1..100 = 20`
Response: `200` lista de SaleRead.

Endpoint: `GET /api/v1/sales/{id}`
Method: GET
Request: path `id: int`
Response: `200` SaleRead con ítems; `404` si no existe.

## Validation Rules

* `skip >= 0`, `1 <= limit <= 100`; violación → 422.

## Error Handling

* `404` venta inexistente en detalle.
* `422` paginación inválida.

## Acceptance Criteria

### AC-ERF07-01 — Listar ventas

Given existen ventas registradas
When se solicita `GET /api/v1/sales`
Then el servicio debe responder 200 con la lista paginada.

### AC-ERF07-02 — Consultar detalle

Given existe una venta
When se solicita `GET /api/v1/sales/{id}`
Then el servicio debe responder 200 con sus líneas y totales.

### AC-ERF07-03 — Venta inexistente

Given la venta no existe
When se solicita su detalle
Then el servicio debe responder 404.

## Open Questions

No aplica en el alcance actual.

## Traceability

Requirement: ERF-07
Endpoint: GET /api/v1/sales, GET /api/v1/sales/{id}
Service: Sales
Tests: Pendiente (futuros: test_list_sales, test_get_sale_detail, test_get_sale_unknown_id_404)

## Technical Notes

* Schemas futuros `SaleRead` + `SaleDetailRead` (`from_attributes=True`).
  Sin joins cross-DB: el detalle sale íntegro de `ventas_db`.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-09-29 | IMPLEMENTED → VALIDATED (pytest en verde) | Tests confirman AC-ERF07-01..03 |
| 1.0.0 | 2026-09-29 | Approved for implementation (REVIEW passed) | User decision: continue sales vertical |
| 0.1.0 | 2026-09-29 | Initial specification | Initial SDD setup |
