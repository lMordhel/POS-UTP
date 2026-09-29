# SPEC-SALES-001 — Registrar venta

## Metadata

- ID: SPEC-SALES-001
- Requirement: ERF-01 — Registrar venta
- Service: Sales
- Status: VALIDATED
- Version: 1.0.0
- Priority: Alta

## Objective

Permitir registrar una operación de venta con sus líneas, calculando el total
en el servidor, validando disponibilidad en Stock y descontando inventario
tras la confirmación.

## Scope

* Crear una venta a partir de `{items: [{producto_id, cantidad}]}`.
* Resolver precios oficiales desde Stock (snapshot en la venta).
* Validar disponibilidad (ERF-04) y descontar stock (ERF-05).
* Devolver la venta creada con total y líneas.

## Out of Scope

* Impuestos, vuelto, pago en efectivo, cobro QR (ver OQ-ERF01-01/02; fuera del
  alcance aprobado aunque el documento los mencione).
* Descuentos, promociones, clientes, facturación (sin ERF).

## Actors

* Vendedor o encargado de ventas.
* Servicio Stock (validación y descuento vía HTTP).
* Administrador (consulta posterior vía ERF-07).

## Preconditions

* Servicio Sales operativo con acceso a `ventas_db`.
* Servicio Stock accesible (para precios y disponibilidad).
* Productos activos con stock suficiente (camino feliz).

## Functional Requirements

* FR-01: El sistema debe aceptar líneas con `producto_id` y `cantidad > 0`.
* FR-02: El sistema debe resolver `precio_unitario` desde Stock al momento de
  la venta y guardarlo como snapshot (no confiar en precio enviado por cliente).
* FR-03: El sistema debe calcular `subtotal = cantidad × precio_unitario` y
  `total = Σ subtotales` en el servidor.
* FR-04: El sistema debe verificar disponibilidad en Stock antes de confirmar.
* FR-05: El sistema debe descontar stock en Stock solo tras crear la venta, y
  no dejar ventas confirmadas sin descuento. Diseño DECIDED 2026-09-29
  (OQ-ARCH-01): sin estados persistidos `pendiente/fallida`; ante fallo de
  Stock la transacción de `ventas_db` hace rollback y los descuentos ya
  aplicados se compensan (delta inverso). Solo se persiste `confirmada`.

## Business Rules

* BR-01: Venta sin líneas → 422.
* BR-02: Producto inexistente/inactivo → 404.
* BR-03: Stock insuficiente → 409, sin venta confirmada.
* BR-04: Total con 2 decimales; sin impuestos ni vuelto en el alcance actual.

## API Contract

Endpoint: `POST /api/v1/sales`
Method: POST
Request: `{items: [{producto_id: int > 0, cantidad: int > 0}]}` (mínimo 1 ítem)
Response: `201 {id, fecha, total, estado, items: [{producto_id, cantidad, precio_unitario, subtotal}]}`; errores `404/409/422`, `502` si Stock falla de forma no controlada.

## Validation Rules

* `items` no vacío; `cantidad` entero > 0; `producto_id` entero > 0.
* Sin precios en el request (se ignoran o rechazan con 422 según diseño).

## Error Handling

* `404` producto inexistente/inactivo.
* `409` stock insuficiente (sin venta confirmada).
* `422` cuerpo inválido o venta vacía.
* `502` Stock inaccesible o error inesperado (con mensaje controlado, sin
  filtrar detalles internos).

## Acceptance Criteria

### AC-ERF01-01 — Registrar venta válida

Given productos activos con stock suficiente
When se solicita `POST /api/v1/sales` con líneas válidas
Then el servicio debe responder 201
And debe calcular el total como suma de subtotales
And debe descontar el stock en Stock.

### AC-ERF01-02 — Stock insuficiente

Given un producto sin stock suficiente
When se solicita registrar la venta
Then el servicio debe responder 409
And no debe dejar una venta confirmada.

### AC-ERF01-03 — Producto inexistente

Given un `producto_id` inexistente
When se solicita registrar la venta
Then el servicio debe responder 404
And no debe modificar inventario.

### AC-ERF01-04 — Venta vacía o inválida

Given un cuerpo sin ítems o con cantidades <= 0
When se solicita registrar la venta
Then el servicio debe responder 422.

## Open Questions

* OQ-ERF01-01: DECIDED 2026-09-29 → `total` = Σ subtotales, sin impuestos/vuelto
  en el alcance actual; cualquier cobro/impuesto exige ERF nuevo. Texto
  original: Los criterios CA-02 del documento exigen "impuestos y vuelto al
  pagar en efectivo". Las reglas del proyecto prohíben pagos/facturación sin
  ERF aprobado. ¿Se excluyen impuestos/vuelto del alcance (propuesto) o se
  crea ERF nuevo? NO implementar hasta decisión.
* OQ-ERF01-02: La solicitud CR-001 (cobro QR) figura como aprobada en el
  documento pero choca con Regla 1/2. ¿Se registra como diferida/rechazada?
  NO implementar hasta decisión.

## Traceability

Requirement: ERF-01
Endpoint: POST /api/v1/sales
Service: Sales (consume Stock vía HTTP)
Tests: Pendiente (futuros: test_register_sale_valid, test_register_sale_insufficient_stock_409, test_register_sale_unknown_product_404, test_register_sale_empty_422)

## Technical Notes

* Cliente HTTP `clients/stock_client.py` (httpx, timeout, errores tipados;
  skill fastapi-templates para capas). Reintento solo en fallos transitorios
  (patrón retry de skill testing); nunca reintentar 404/409/422.
* Total y subtotales con `NUMERIC(12,2)`; snapshot de precio en `sale_details`.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-09-29 | IMPLEMENTED → VALIDATED (13/13 pytest en verde) | Tests confirman AC-ERF01-01..04 |
| 1.0.0 | 2026-09-29 | Approved; saga sin estados persistidos (OQ-ARCH-01 DECIDED) | User decision: continue sales vertical |
| 0.1.0 | 2026-09-29 | Initial specification | Initial SDD setup |
