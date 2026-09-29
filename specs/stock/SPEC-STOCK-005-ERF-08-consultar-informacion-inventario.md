# SPEC-STOCK-005 — Consultar información de inventario

## Metadata

- ID: SPEC-STOCK-005
- Requirement: ERF-08 — Consultar información de inventario
- Service: Stock
- Status: VALIDATED
- Version: 1.0.0
- Priority: Media

## Objective

Permitir supervisar la información de inventario (productos con existencias)
para el administrador y el responsable de inventario.

## Scope

* Consultar productos con su stock para supervisión.
* Reutilizar la lectura de SPEC-STOCK-001 con propósito de supervisión.

## Out of Scope

* Reportes agregados, valorizaciones, kardex, alertas de mínimo
  (sin ERF que los respalde; no inventar).
* Cualquier mutación.

## Actors

* Responsable de inventario.
* Administrador de la microempresa.

## Preconditions

* Servicio Stock operativo; existen o no productos (lista vacía válida).

## Functional Requirements

* FR-01: El sistema debe exponer productos con su cantidad disponible para
  supervisión, con paginación.
* FR-02: El sistema debe permitir distinguir activos/inactivos.

## Business Rules

* BR-01: Solo lectura; ningún endpoint de esta SPEC muta datos.
* BR-02: No introducir métricas nuevas (rotación, valorizado) sin ERF o
  decisión aprobada.

## API Contract

Endpoint: `GET /api/v1/products`
Method: GET
Request (query): `activo?, skip, limit` (igual base que SPEC-STOCK-001)
Response: `200` lista de `{id, codigo, nombre, precio, activo, stock}`.

## Validation Rules

* Las mismas de paginación de SPEC-STOCK-001 (`skip >= 0`, `1 <= limit <= 100`).

## Error Handling

* `422` paginación inválida. No hay 404 (lista vacía → 200 con `[]`).

## Acceptance Criteria

### AC-ERF08-01 — Supervisar inventario

Given existen productos con stock
When se solicita `GET /api/v1/products` para supervisión
Then el servicio debe responder 200
And debe incluir la cantidad disponible por producto.

### AC-ERF08-02 — Sin productos

Given no hay productos registrados
When se solicita la información de inventario
Then el servicio debe responder 200 con lista vacía.

## Open Questions

* OQ-ERF08-01: El documento distingue ERF-02 (operativa de venta) de ERF-08
  (supervisión), pero ambos se satisfacen con el mismo endpoint base. ¿Se
  acepta una sola implementación con dos propósitos trazados, o el tribunal
  exige endpoints diferenciados? No implementar diferenciación hasta decisión.

## Traceability

Requirement: ERF-08
Endpoint: GET /api/v1/products
Service: Stock
Tests: Pendiente (futuros: test_inventory_info_lists_stock, test_inventory_info_empty_200)

## Technical Notes

* Intencionalmente sin endpoint nuevo: evita endpoints innecesarios (Regla del
  proyecto). Si a futuro se aprueba un reporte, será SPEC nueva versionada.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-09-29 | IMPLEMENTED → VALIDATED (pytest en verde) | Tests confirman AC-ERF08-01..02 |
| 1.0.0 | 2026-09-29 | Approved for implementation (REVIEW passed) | Stock vertical, second batch |
| 0.1.0 | 2026-09-29 | Initial specification | Initial SDD setup |
