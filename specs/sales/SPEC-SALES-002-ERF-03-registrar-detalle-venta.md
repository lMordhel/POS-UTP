# SPEC-SALES-002 — Registrar detalle de venta

## Metadata

- ID: SPEC-SALES-002
- Requirement: ERF-03 — Registrar detalle de venta
- Service: Sales
- Status: VALIDATED
- Version: 1.0.0
- Priority: Alta

## Objective

Registrar las líneas (detalle) de una venta: producto, cantidad, precio
unitario snapshot y subtotal, como parte atómica de `POST /api/v1/sales`.

## Scope

* Validar y persistir cada línea junto a su venta (todo o nada).
* Snapshot de `precio_unitario` vigente al vender.

## Out of Scope

* Endpoint independiente de detalles (no existe; evita endpoints innecesarios).
* Edición posterior de líneas de una venta confirmada (sin ERF).
* Descuentos por línea (fuera de alcance).

## Actors

* Vendedor o encargado de ventas.
* Servicio Stock (origen del precio oficial).

## Preconditions

* Venta en curso de creación vía SPEC-SALES-001.
* Productos existen, activos y con stock (camino feliz).

## Functional Requirements

* FR-01: Cada línea debe tener `producto_id`, `cantidad > 0`,
  `precio_unitario` (snapshot), `subtotal = cantidad × precio_unitario`.
* FR-02: Las líneas se persisten atómicamente con la venta (todo o nada
  respecto a `ventas_db`; el descuento en Stock sigue la saga de
  SPEC-SALES-001).
* FR-03: `producto_id` es referencia lógica a Stock (sin FK física cross-DB).

## Business Rules

* BR-01: Cantidad entera > 0; violación → 422.
* BR-02: Precio snapshot > 0 copiado de Stock; nunca proviene del cliente.
* BR-03: Subtotal con 2 decimales.

## API Contract

Endpoint: `POST /api/v1/sales` (líneas dentro del cuerpo; sin endpoint propio)
Method: POST
Request: `{items: [{producto_id, cantidad}]}` (ver SPEC-SALES-001)
Response: `201` venta con `items` detallados; mismos errores que SPEC-SALES-001.

## Validation Rules

* Ítems no vacíos; sin duplicados ambiguos (si el mismo `producto_id` aparece
  dos veces, el diseño debe definir si se fusiona o se rechaza con 422 —
  registrar decisión al aprobar).

## Error Handling

* `404` producto de alguna línea inexistente.
* `409` stock insuficiente en alguna línea.
* `422` líneas vacías o cantidades inválidas.

## Acceptance Criteria

### AC-ERF03-01 — Registrar líneas válidas

Given una venta con líneas válidas
When se registra la venta
Then el servicio debe persistir cada línea con su snapshot de precio y subtotal.

### AC-ERF03-02 — Línea con cantidad inválida

Given una línea con cantidad <= 0
When se registra la venta
Then el servicio debe responder 422
And no debe persistir la venta.

### AC-ERF03-03 — Línea con producto inexistente

Given una línea con `producto_id` inexistente
When se registra la venta
Then el servicio debe responder 404
And no debe modificar inventario.

## Open Questions

* OQ-ERF03-01: DECIDED 2026-09-29 → las líneas duplicadas del mismo producto se
  fusionan sumando cantidades antes de validar (comportamiento documentado y
  testeado). Texto original: ¿Líneas duplicadas del mismo producto se fusionan
  o se rechazan con 422? Definir al pasar a REVIEW.

## Traceability

Requirement: ERF-03
Endpoint: POST /api/v1/sales (líneas)
Service: Sales
Tests: Pendiente (futuros: test_sale_lines_snapshot_prices, test_sale_line_invalid_quantity_422, test_sale_line_unknown_product_404)

## Technical Notes

* Tabla `sale_details` (`venta_id` FK, `producto_id` lógico, `cantidad`,
  `precio_unitario`, `subtotal`). Schemas futuros `SaleDetailCreate/Read`
  (skill pydantic).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-09-29 | IMPLEMENTED → VALIDATED (pytest en verde) | Tests confirman AC-ERF03-01..03 + fusión |
| 1.0.0 | 2026-09-29 | Approved; duplicados se fusionan (OQ-ERF03-01 DECIDED) | User decision: continue sales vertical |
| 0.1.0 | 2026-09-29 | Initial specification | Initial SDD setup |
