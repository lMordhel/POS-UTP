# SPEC-SALES-004 — Idempotencia de ventas y robustez de la saga

## Metadata

- ID: SPEC-SALES-004
- Requirement: Plan de seguridad Fase 3 — endurece ERF-01/ERF-03 (sin ERF nuevo; no amplía funcionalidad, elimina duplicados y fugas ante fallos).
- Service: Sales (clave de venta) + Stock (clave por línea)
- Status: APPROVED
- Version: 1.0.0
- Priority: Muy alta

## Objective

Que reintentar `POST /sales` (timeout, error de red, doble clic) nunca cree dos
ventas ni descuente dos veces; que un timeout ambiguo en Stock no deje
descuentos huérfanos; y que la compensación falle de forma visible, no silenciosa.

## Scope

* Header opcional `Idempotency-Key` en `POST /api/v1/sales` (clave por venta).
* Tabla `idempotency_keys` en `ventas_db` (clave única, hash del cuerpo, venta resultante).
* Clave por línea hacia Stock (`{clave_venta}:{producto_id}`) vía header en `PATCH stock`.
* Tabla `stock_adjustments` en `stock_db` (clave única, delta aplicado, cantidad resultante): ajuste con clave repetida no re-aplica.
* Compensación con reintentos acotados + log estructurado ante fallo final.
* Reintento seguro de un ajuste con timeout (misma clave de línea).

## Out of Scope

* Outbox/broker, saga orquestada o coreografía con eventos.
* Expiración/purga de claves (nota futura; sin TTL en esta fase).
* Endpoint de consulta de incidentes (la reconciliación usa `GET /sales` y `GET stock` existentes).
* Idempotencia en otros endpoints (solo `POST /sales` y su saga).

## Actors

* Cajero/cliente HTTP que reintenta ante timeout o error de red.
* Servicio Sales: dueño de la clave de venta y de la compensación.
* Servicio Stock: aplica cada línea exactamente una vez por clave.

## Preconditions

* SPEC-AUTH-001/SPEC-AUTH-002 implementadas (la saga corre autenticada).
* Tablas nuevas creadas vía `init_db` (migraciones en Fase 4).

## Functional Requirements

* FR-01: `POST /sales` acepta header opcional `Idempotency-Key` (opaco, ≤ 64 caracteres propuesto). Sin header: comportamiento actual sin cambios.
* FR-02: Con clave K nueva: ejecutar la saga; al confirmar, persistir `(K, hash_cuerpo, venta_id)` y responder 201.
* FR-03: Con clave K repetida y mismo cuerpo: no re-ejecutar nada; responder la venta original (código propuesto en OQ-SAGA-01) con header `Idempotent-Replayed: true`.
* FR-04: Con clave K repetida y cuerpo distinto (hash SHA-256 del JSON canónico): responder 422 sin tocar negocio.
* FR-05: Dos peticiones concurrentes con la misma K: la restricción única decide; la perdedora lee el resultado (si la ganadora completó) o recibe 409 con indicación de reintentar (si sigue en proceso).
* FR-06: Cada línea de la saga llama a Stock con clave `{K}:{producto_id}` (header `Idempotency-Key` en el `PATCH`; llamadas sin clave de venta usan el comportamiento actual).
* FR-07: Stock con clave de línea repetida: devolver la cantidad registrada sin re-aplicar el delta (exactamente-una-vez por clave).
* FR-08: La compensación ante fallo parcial debe reintentar cada reverso hasta 3 veces con espera corta; si agota los intentos, log estructurado (`venta_id`, producto, delta pendiente) y responder 502. Nunca `pass` silencioso.
* FR-09: Un timeout en `adjust_stock` no demuestra nada: con clave de línea, el reintento es seguro (replay del lado Stock); sin clave de venta del cliente, el comportamiento ante timeout sigue siendo 502 como hoy.

## Business Rules

* BR-01: La idempotencia cubre reintentos del mismo negocio, no negocios distintos con la misma clave (FR-04).
* BR-02: Las claves las genera el cliente (UUID recomendado); el servidor nunca las inventa por el cliente.
* BR-03: Sin SPEC aprobada no se implementa (SDD-001); esta SPEC en DRAFT no autoriza código.

## API Contract

* `POST /api/v1/sales` + header `Idempotency-Key: <K>`:
  - Primera vez → `201` venta (igual que hoy).
  - Replay mismo cuerpo → respuesta idéntica + header `Idempotent-Replayed: true` (código en OQ-SAGA-01).
  - Misma K, cuerpo distinto → `422`.
  - K en proceso concurrente → `409` con indicación de reintentar.
* `PATCH /api/v1/products/{id}/stock` + header `Idempotency-Key: <K:pid>` (servicio-a-servicio; opcional y backward compatible):
  - Clave nueva → aplica y registra; clave repetida → `200` con la cantidad registrada.

## Validation Rules

* Clave: no vacía, ≤ 64 caracteres; otro formato → 422.
* Hash de cuerpo: SHA-256 sobre JSON canónico (`sort_keys`, sin espacios); mismatch → 422.

## Error Handling

* `422`: clave inválida o reutilizada con cuerpo distinto.
* `409`: clave en proceso (concurrente) o stock insuficiente (sin cambios, como hoy).
* `502`: Stock inaccesible o compensación agotada (con mensaje controlado).
* Fallo final de compensación: log estructurado con todo lo necesario para conciliar a mano.

## Acceptance Criteria

### AC-SAGA04-01 — Replay devuelve la misma venta

Given una venta confirmada con clave K
When se repite `POST /sales` con K y el mismo cuerpo
Then debe responder la misma venta (mismo id y total) sin crear otra
And sin mover stock (verificado en Stock).

### AC-SAGA04-02 — Misma clave, distinto cuerpo

Given clave K usada con un cuerpo
When se usa K con líneas distintas
Then debe responder 422 sin crear venta ni tocar stock.

### AC-SAGA04-03 — Timeout ambiguo no duplica

Given un ajuste que hace timeout tras aplicar en Stock (doble simulado)
When la saga reintenta la línea con la misma clave
Then Stock debe devolver lo registrado sin re-aplicar
And debe haber una sola venta con un solo descuento.

### AC-SAGA04-04 — Concurrencia con la misma clave

Given dos `POST /sales` simultáneos con la misma K
When ambos compiten
Then debe quedar exactamente una venta y un juego de descuentos.

### AC-SAGA04-05 — Compensación que falla se ve

Given un reverso que falla de forma persistente (doble simulado)
When se agotan los 3 intentos
Then debe responder 502 y emitir el log con `venta_id`, producto y delta pendiente.

### AC-SAGA04-06 — Sin clave, todo igual que hoy

Given `POST /sales` sin header
When se procesa
Then el comportamiento y códigos deben ser los actuales (201/404/409/502).

## Open Questions

* OQ-SAGA-01: DECIDED 2026-10-12 → `200` + header `Idempotent-Replayed: true` (convención Stripe/PayPal: distingue "creado ahora" de "ya existía", facilita debugging y cliente).
* OQ-SAGA-02: DECIDED 2026-10-12 → sin expiración en esta fase (simple, sin edge de "expiró al reintentar"; purga futura sin cambiar contrato).
* OQ-SAGA-03: DECIDED 2026-10-12 → `422` (misma clave + mismo request = mismo resultado; protege contra bugs/reúso malicioso).

## Traceability

Requirement: Plan Fase 3 (endurece ERF-01/ERF-03, sin ERF nuevo)
Endpoint: `POST /api/v1/sales` (+ header), `PATCH stock` (+ header)
Service: Sales (clave de venta) + Stock (clave por línea)
Tests: Pendiente (futuros: `test_replay_returns_same_sale`, `test_same_key_different_body_422`, `test_timeout_retry_no_double_discount`, `test_concurrent_same_key_single_sale`, `test_failed_compensation_502_and_log`, `test_no_key_unchanged_behavior`, `test_stock_keyed_replay_no_reapply`)

## Technical Notes

* Tablas: `ventas_db.idempotency_keys(clave única, cuerpo_hash, venta_id FK, creada)` y `stock_db.stock_adjustments(clave única, producto_id, delta, cantidad_resultante, creada)`. Estados de proceso: fila `procesando` (venta_id NULL) para la guarda concurrente (FR-05).
* Hash: SHA-256 del cuerpo serializado canónico.
* Compensación: 3 intentos, espera ~0.2s/0.5s (constantes testeables); `logging` estructurado (Fase 6 lo consumirá).
* Tests con dobles que simulan timeout-tras-aplicar y reverso persistente-fallido; concurrencia con hilos sobre la misma K.
* Capas según skills vigentes (service → repository; schemas con el header como parámetro de endpoint, no del body).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-12 | OQ-SAGA-01/02/03 DECIDED (200+header, sin expiración, 422); DRAFT → APPROVED (autoriza desarrollo) | User approval: 200, sin expiración, 422 |
|---|---|---|---|
| 0.1.0 | 2026-10-12 | Initial specification (DRAFT, no autoriza implementar) | Plan de seguridad Fase 3 |
