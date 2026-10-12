# SPEC-STOCK-006 — Lectura por lote para la saga (optimización Fase 5)

## Metadata

- ID: SPEC-STOCK-006
- Requirement: Plan de seguridad Fase 5 — optimiza ERF-01/ERF-03 (sin ERF nuevo; sin cambios de comportamiento, solo menos llamadas).
- Service: Stock (endpoint batch) + Sales (consume el batch en la saga)
- Status: APPROVED
- Version: 1.0.0
- Priority: Media

## Objective

Bajar la saga de ~3N llamadas HTTP secuenciales a N+1: una lectura por lote
(producto + stock juntos) en vez de N×(`get_product` + `get_stock`), manteniendo
idénticas semánticas 404/409/422, idempotencia y auditoría.

## Scope

* `POST /api/v1/products/batch` en Stock: `{ids: [...]}` → lista de productos con stock agregado (mismo shape que `ProductRead`).
* Sales usa el batch como único camino de lectura de la saga (precios + disponibilidad).
* Ajustes por línea sin cambios (con clave, secuenciales, auditados).
* Contadores de llamadas en el doble de tests para probar la reducción (sin asserts de tiempo).

## Out of Scope

* Escrituras por lote (reimplementaría la saga dentro de Stock).
* Cachés (SDD-008: exigirían ERF o decisión aparte; no se proponen aquí).
* Clientes async, threads, pooling, réplicas de lectura.
* Cambios en matriz RBAC, idempotencia, hardening o migraciones.

## Actors

* Servicio Sales: único consumidor del batch (saga).
* Cajero/admin: sin cambios visibles (misma API de ventas).

## Preconditions

* SPEC-SALES-004 implementada (claves por línea y servicio existen).
* RBAC vigente: el batch exige rol lector (admin/cajero), igual que las lecturas actuales.

## Functional Requirements

* FR-01: `POST /api/v1/products/batch` con `{ids: [int...]}` (1..100 propuesto, OQ-BATCH-03) debe responder 200 con los productos encontrados, cada uno con su stock agregado; ignora duplicados.
* FR-02: Los ids inexistentes no deben aparecer en la respuesta (OQ-BATCH-01); Sales mantiene la semántica actual: producto faltante o inactivo → 404 de la venta.
* FR-03: Sales debe resolver precios oficiales y disponibilidad exclusivamente desde el batch (un solo camino, OQ-BATCH-02), y conservar validaciones, snapshot, total e idempotencia idénticos.
* FR-04: Los ajustes por línea siguen uno por uno con su clave (sin cambios).
* FR-05: Sin batch (llamadas viejas una por una) todo debe seguir funcionando: el batch es aditivo, no reemplaza los endpoints de lectura.

## Business Rules

* BR-01: Optimizar no cambia comportamiento: mismos códigos, mismos totales, misma saga ante fallos.
* BR-02: El tope del lote protege al servidor (coherente con `limit <= 100`).
* BR-03: Sin SPEC aprobada no se implementa (SDD-001); esta SPEC en DRAFT no autoriza código.

## API Contract

* `POST /api/v1/products/batch` — Request: `{ids: [int > 0], 1..100}`. Response: `200 [{id, codigo, nombre, descripcion, precio, activo, stock, ...}]` (shape `ProductRead`, solo encontrados, orden de petición). Errores: `401/403` (RBAC lector), `422` (lista vacía, ids inválidos o > 100).
* `POST /sales` sin cambios de contrato.

## Validation Rules

* `ids`: mínimo 1, máximo 100; elementos enteros > 0; duplicados se colapsan.

## Error Handling

* `401/403`: según RBAC (igual que lecturas actuales).
* `422`: cuerpo inválido del lote.
* La saga conserva 404/409/422/502 exactly como hoy (verificado por suites existentes).

## Acceptance Criteria

### AC-BATCH06-01 — Lote devuelve encontrados con stock

Given productos 1 y 2 existentes y 999 inexistente
When se pide el batch `[1, 2, 999, 1]`
Then debe responder 200 con 1 y 2 (una vez cada uno), cada uno con su stock
And sin rastro de 999.

### AC-BATCH06-02 — Lote inválido

Given `ids` vacío, con 070501+ ids
When se pide el batch
Then debe responder 422.

### AC-BATCH06-03 — RBAC del batch

Given sin token o rol ajeno a lectura
When se pide el batch
Then 401/403 según corresponda (igual que `GET /products`).

### AC-BATCH06-04 — Saga usa una sola lectura

Given venta de 3 productos distintos
When se registra
Then Stock debe recibir 1 lectura batch + 3 ajustes (contado en el doble), no 6 lecturas + 3 ajustes.

### AC-BATCH06-05 — Semántica intacta

Given las suites existentes (ventas, idempotencia, E2E)
When corren contra el nuevo camino
Then todo debe seguir en verde sin cambios en assertions.

## Open Questions

* OQ-BATCH-01: DECIDED 2026-10-12 → solo encontrados; Sales decide (flexible, resiliente, patrón Stripe/Shopify; un inexistente no tumba el lote).
* OQ-BATCH-02: DECIDED 2026-10-12 → siempre, camino único (sin bifurcación N==1; overhead mínimo).
* OQ-BATCH-03: DECIDED 2026-10-12 → sí, tope 100 (seguro, ampliable sin romper compatibilidad).

## Traceability

Requirement: Plan Fase 5 (optimiza ERF-01/ERF-03, sin ERF nuevo)
Endpoint: `POST /api/v1/products/batch` (nuevo, aditivo); `POST /sales` sin cambios
Service: Stock (batch) + Sales (consume)
Tests: Pendiente (futuros: `test_batch_returns_found_with_stock`, `test_batch_invalid_422`, `test_batch_rbac`, `test_saga_single_batch_read`, suites existentes intactas)

## Technical Notes

* Capas vigentes: endpoint delgado → `product_service.get_batch(ids)` (nuevo, reutiliza `get_with_stock`) → repo existente; schemas `BatchRequest`/`BatchResponse = list[ProductRead]`.
* `stock_client.batch_get_products(ids)` en Sales (errores tipados como el resto); `sale_service` reemplaza los dos bucles de lectura por una llamada; `FakeStockClient` la implementa con contadores.
* Sin hilos ni async: la ganancia es menos round-trips, no paralelismo.
* E2E sin cambios (ejerce el camino nuevo por debajo).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-12 | OQ-BATCH-01/02/03 DECIDED (encontrados/siempre/100); DRAFT → APPROVED (autoriza desarrollo) | User approval: encontrados, siempre, 100 |
|---|---|---|---|
| 0.1.0 | 2026-10-12 | Initial specification (DRAFT, no autoriza implementar) | Plan de seguridad Fase 5 |
