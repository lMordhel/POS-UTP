# SPEC-SALES-003 — Consultar ventas

## Metadata

- ID: SPEC-SALES-003
- Requirement: ERF-07 — Consultar ventas
- Service: Sales
- Status: VALIDATED
- Version: 1.1.0
- Priority: Media

## Objective

Permitir consultar las ventas registradas, en lista paginada y por detalle con
sus líneas, para supervisión y operativa.

## Scope

* Listar ventas paginadas.
* Obtener una venta por `id` con sus líneas.
* Ordenar la lista de ventas por fecha de registro, de la más reciente a la más
  antigua (1.1.0).

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
* FR-04: El listado se devuelve por defecto en orden descendente por `id`
  (la venta más reciente primero); `order=asc` devuelve la más antigua primero
  (1.1.0).

## Business Rules

* BR-01: Solo lectura; ningún endpoint de esta SPEC muta datos.
* BR-02: El `total` mostrado es el calculado y persistido al registrar.
* BR-03: `skip` y `limit` recortan sobre el orden vigente, de modo que la
  primera página contiene siempre las ventas más recientes (1.1.0).

## API Contract

Endpoint: `GET /api/v1/sales`
Method: GET
Request (query): `skip: int >= 0 = 0, limit: int 1..100 = 20, order: "asc"|"desc" = "desc"`
Response: `200` lista de SaleRead.

Endpoint: `GET /api/v1/sales/{id}`
Method: GET
Request: path `id: int`
Response: `200` SaleRead con ítems; `404` si no existe.

## Validation Rules

* `skip >= 0`, `1 <= limit <= 100`; violación → 422.
* `order` ∈ {`asc`, `desc`}; violación → 422 (1.1.0).

## Error Handling

* `404` venta inexistente en detalle.
* `422` paginación inválida u `order` inválido (1.1.0).

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

### AC-ERF07-04 — Orden del listado (1.1.0)

Given existen ventas registradas
When se solicita `GET /api/v1/sales`
Then la respuesta debe traer la venta más reciente en la primera posición.

Given existen ventas registradas
When se solicita `GET /api/v1/sales?order=asc`
Then la respuesta debe traer la venta más antigua en la primera posición.

Given ventas registradas
When se solicita `GET /api/v1/sales?limit=2` y luego `?limit=2&skip=2`
Then las dos páginas deben repartirse las ventas desde la más reciente.

Given cualquier estado
When se solicita `GET /api/v1/sales?order=xyz`
Then el servicio debe responder 422.

## Open Questions

No aplica en el alcance actual.

## Traceability

Requirement: ERF-07
Endpoint: GET /api/v1/sales, GET /api/v1/sales/{id}
Service: Sales
Tests: `tests/test_integration/test_sales.py` — `test_list_and_get_sale`
(AC-ERF07-01..03), `test_list_sales_returns_newest_first_by_default`,
`test_list_sales_accepts_explicit_ascending_order`,
`test_list_sales_paginates_from_the_newest`,
`test_list_sales_rejects_unknown_order` (AC-ERF07-04).

## Technical Notes

* Schemas futuros `SaleRead` + `SaleDetailRead` (`from_attributes=True`).
  Sin joins cross-DB: el detalle sale íntegro de `ventas_db`.
* El orden se aplica en la capa de repositorio
  (`app/repositories/sale_repository.py`, `order_by(Sale.id.desc())`), no en el
  endpoint: el router queda delgado (skill `fastapi-templates`).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.1.0 | 2026-10-21 | Orden descendente por defecto + `order` opcional; AC-ERF07-04; tests | Verificación en ejecución: la venta más reciente quedaba en la última página, invisible para el cajero. Decisión del usuario (ADR-018) |
| 1.0.0 | 2026-09-29 | IMPLEMENTED → VALIDATED (pytest en verde) | Tests confirman AC-ERF07-01..03 |
| 1.0.0 | 2026-09-29 | Approved for implementation (REVIEW passed) | User decision: continue sales vertical |
| 0.1.0 | 2026-09-29 | Initial specification | Initial SDD setup |
