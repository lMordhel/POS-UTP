# SPEC-SALES-005 — Venta con cliente y pago en efectivo

## Metadata

- ID: SPEC-SALES-005
- Requirement: ERF-11 — Venta con cliente y pago en efectivo (nuevo; SPEC-SALES-001 excluye vuelto/pago/cliente y exige ERF nuevo, ver OQ-ERF01-01)
- Service: Sales
- Status: DRAFT
- Version: 0.1.0
- Priority: Alta

## Objective

Registrar una venta identificando al comprador (texto libre opcional) y
cerrando la caja en efectivo: el cliente entrega un monto, el servidor calcula
y persiste el vuelto. Nada de lo ya validado se rompe (precios y totales
siguen server-side desde Stock; idempotencia/saga intactas).

## Scope

* Campo `cliente` opcional en `POST /api/v1/sales` (texto libre, normalizado).
* Campo `monto_recibido` opcional en `POST /api/v1/sales` (efectivo entregado).
* Cálculo server-side `vuelto = monto_recibido − total`; persistido en `sales`.
* `SaleRead` y `GET /sales*` exponen `cliente`, `monto_recibido`, `vuelto`.
* Migración Alembic lineal: solo `add_column` nullable sobre baseline
  `5df949f9a5f2` intacta; un solo head.
* Hash de idempotencia (SPEC-SALES-004) ampliado a cliente + monto.

## Out of Scope

* Impuestos, descuentos, promociones, facturación.
* Cobro QR u otros medios de pago (efectivo solo, Fase 2).
* Frontend (siguiente paso tras VALIDATED).
* Expiración/purga de claves de idempotencia (SPEC-SALES-004, sin cambios).

## Actors

* Cajero (registra la venta con cliente y efectivo).
* Servicio Stock (precios y descuentos, sin cambios).
* Administrador (consulta posterior vía ERF-07; ve cliente/vuelto).

## Preconditions

* SPEC-SALES-001/002/003/004 VALIDATED en `main` (comportamiento base intacto).
* Servicio Sales operativo con acceso a `ventas_db`; Stock accesible.
* Migración aplicada (columnas presentes, nullable).

## Functional Requirements

* FR-01: `POST /api/v1/sales` acepta `cliente` opcional (texto libre).
  Normalización propuesta: `strip()`; cadena vacía tras `strip()` → `null`;
  longitud máxima 120 (más en OQ-CLI05-02).
* FR-02: `POST /api/v1/sales` acepta `monto_recibido` opcional (decimal ≥ 0,
  2 decimales). Ausente → venta sin pago registrado (compatibilidad con
  SPEC-SALES-001).
* FR-03: Con `monto_recibido` presente, el servidor calcula
  `vuelto = monto_recibido − total` y lo persiste. El request nunca envía
  `vuelto` (si llega, se ignora o 422 según gate; recomendado: 422 si el
  cuerpo trae `vuelto`, coherente con "sin precios en el request" de
  SPEC-SALES-001).
* FR-04: `monto_recibido < total` → 422, sin venta confirmada y sin tocar
  stock (antes de persistir, mismo orden que BR-03 de SPEC-SALES-001).
* FR-05: `monto_recibido == total` → 201 con `vuelto = 0` (pago exacto válido).
* FR-06: Sin `monto_recibido` → `vuelto` es `null` (no `0`); distingue "pagó
  exacto" de "pago no registrado".
* FR-07: `SaleRead` y `GET /sales`, `GET /sales/{id}` incluyen `cliente`,
  `monto_recibido`, `vuelto` (nullables).
* FR-08: El hash de idempotencia (`_body_hash`) incluye `cliente`
  normalizado + `monto_recibido`: mismo K + mismo negocio → replay;
  misma K + distinto cliente/monto → 422 (FR-04 de SPEC-SALES-004).

## Business Rules

* BR-01: Totales y precios siempre server-side desde Stock (principio
  vigente). `monto_recibido` es dato del pagador, no precio: no altera el total.
* BR-02: `vuelto` nunca viene del request; solo se deriva o es `null`.
* BR-03: Validación de pago insuficiente ocurre antes de persistir la venta
  (sin compensación necesaria; sin ventas confirmadas sin cobro válido).
* BR-04: `NUMERIC(12,2)` para `monto_recibido` y `vuelto`, igual que `total`.
* BR-05: Sin SPEC aprobada no se implementa (SDD-001); este DRAFT no autoriza código.

## API Contract

Endpoint: `POST /api/v1/sales` (existente, extendido, backward compatible)
Method: POST
Request: `{items: [{producto_id: int > 0, cantidad: int > 0}], cliente?: string | null, monto_recibido?: decimal >= 0 | null}`
Response: `201 {id, fecha, total, estado, cliente, monto_recibido, vuelto, items: [...]}`; errores `404/409/422` (como hoy), `422` si `monto_recibido < total`, `502` si Stock falla.

## Validation Rules

* `items`: sin cambios (no vacío; `cantidad`, `producto_id` enteros > 0).
* `cliente`: `null` o string; tras `strip()`, `1..120` caracteres (vacío → `null`); otro caso → 422.
* `monto_recibido`: `null` o decimal ≥ 0 con 2 decimales; negativo o no numérico → 422.
* `monto_recibido < total` → 422 (pago insuficiente).
* `vuelto` en el request → 422 (recomendado; a confirmar en gate).

## Error Handling

* `404` producto inexistente/inactivo (sin cambios).
* `409` stock insuficiente (sin cambios).
* `422` cuerpo inválido, venta vacía, cliente inválido, monto inválido,
  monto < total, o `vuelto` enviado por el cliente.
* `502` Stock inaccesible o compensación agotada (sin cambios).

## Acceptance Criteria

### AC-CLI05-01 — Venta con cliente y efectivo con vuelto

Given productos activos con stock suficiente y total T
When se solicita `POST /api/v1/sales` con `cliente: "Juan Pérez"` y `monto_recibido > T`
Then el servicio debe responder 201
And debe persistir `cliente` normalizado y `vuelto = monto_recibido − T`
And debe descontar el stock en Stock.

### AC-CLI05-02 — Pago insuficiente

Given productos con stock suficiente y total T
When se solicita la venta con `monto_recibido < T`
Then el servicio debe responder 422
And no debe crear venta ni tocar stock.

### AC-CLI05-03 — Venta sin cliente ni monto (compatibilidad)

Given productos activos con stock suficiente
When se solicita `POST /api/v1/sales` solo con `items` (cuerpo SPEC-SALES-001)
Then el servicio debe responder 201
And `cliente`, `monto_recibido` y `vuelto` deben ser `null`.

### AC-CLI05-04 — Cliente inválido

Given un cuerpo con `cliente` solo-espacios o de más de 120 caracteres
When se solicita registrar la venta
Then solo-espacios debe normalizarse a `null` (venta 201) o 422 según gate
And más de 120 caracteres debe responder 422 sin crear venta.

### AC-CLI05-05 — Idempotencia cubre cliente y monto

Given una venta confirmada con clave K, cliente C y monto M
When se repite `POST /sales` con K y el mismo cuerpo (C, M)
Then debe responder la misma venta con `Idempotent-Replayed: true`
And cuando se usa K con distinto cliente o monto debe responder 422 sin crear venta.

### AC-CLI05-06 — Pago exacto

Given productos con stock suficiente y total T
When se solicita la venta con `monto_recibido == T`
Then debe responder 201 con `vuelto = 0` (no `null`).

### AC-CLI05-07 — Lectura expone cliente y pago

Given una venta con cliente y efectivo registrada
When se consulta `GET /sales/{id}`
Then debe incluir `cliente`, `monto_recibido` y `vuelto` persistidos.

## Open Questions

* OQ-CLI05-01 — ERF nuevo vs enmienda de ERF-01. Recomendación: ERF nuevo
  (ERF-11). SPEC-SALES-001 excluye pago/cliente explícitamente y está
  VALIDATED; enmendarla reabriría su gate. Requiere decisión en SALE-EFE-02.
* OQ-CLI05-02 — Cliente: opcional, `strip()`, máx. 120, ¿en hash de
  idempotencia? Recomendación: sí a todo (opcional; vacío→`null`; 120 cubre
  nombres compuestos; incluir en hash para que replay distinga negocios).
  Requiere decisión en SALE-EFE-02.
* OQ-CLI05-03 — `monto_recibido`: ¿opcional-nullable o requerido?
  Recomendación: opcional-nullable (backward compatible con SPEC-SALES-001;
  Fase 2 es solo efectivo pero hay ventas ya registradas sin pago).
  Requiere decisión en SALE-EFE-02.
* OQ-CLI05-04 — Vuelto: ¿persistido o derivado al leer? ¿permitir pago
  exacto? Recomendación: persistido `NUMERIC(12,2)` (auditable en caja) y
  exacto permitido (`vuelto = 0`). Requiere decisión en SALE-EFE-02.
* OQ-CLI05-05 — Migración: ¿nullable o NOT NULL + default? Recomendación:
  nullable (lineal, baseline intacta, single head; NOT NULL obligaría a
  backfill y rompe la regla de prod-solo-adelante). Requiere decisión en
  SALE-EFE-02.
* OQ-CLI05-06 — Alcance: confirmar que impuestos/QR quedan fuera.
  Recomendación: fuera (Fase 2 solo efectivo; QR/impuestos exigen ERF nuevo).
  Requiere decisión en SALE-EFE-02.

## Traceability

Requirement: ERF-11 (nuevo, DRAFT)
Endpoint: POST /api/v1/sales (extendido) + GET /sales* (lectura)
Service: Sales (consume Stock vía HTTP, sin cambios)
Tests: Pendiente (futuros: test_venta_cliente_efectivo_vuelto, test_monto_insuficiente_422, test_sin_cliente_compat_201, test_cliente_invalido_422, test_idempotencia_con_cliente_monto, test_pago exacto_vuelto_cero, test_lectura_expone_cliente_pago)

## Technical Notes

* Modelo: `sales.cliente VARCHAR(120) NULL`, `sales.monto_recibido
  NUMERIC(12,2) NULL`, `sales.vuelto NUMERIC(12,2) NULL`. Solo `add_column`;
  `down_revision = 5df949f9a5f2`; `database.py:46-47` guarda single head.
* Schemas: `SaleCreate` suma `cliente` + `monto_recibido` (Pydantic; `vuelto`
  jamás en el request). `SaleRead` suma los tres campos (nullables).
* Service: validar pago antes de persistir (sin compensación); `vuelto`
  calculado tras `total` server-side (`sale_service.py:184`); `_body_hash`
  (`:48-57`) suma cliente normalizado + monto; `_merge_items` (`:78-82`) sin cambios.
* Tests: pytest desde `services/sales-service` (`pytest.ini`
  testpaths=tests, markers unit/integration; conftest SQLite + TestClient +
  FakeStockClient). TDD RED → GREEN → REFACTOR en SALE-EFE-03.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 0.1.0 | 2026-10-14 | Initial specification (DRAFT, no autoriza implementar) | SALE-EFE-01: cliente + efectivo Fase 2 |
