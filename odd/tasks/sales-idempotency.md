# Feature: sales-idempotency (SPEC-SALES-004 1.0.0)

## Objective

Reintentos seguros de `POST /sales`: sin ventas ni descuentos duplicados,
timeouts ambiguos resolubles y compensación visible (sin `pass` silencioso).

## Problem

Sin clave, un reintento tras timeout crea otra venta y otro descuento; la
compensación traga excepciones; `adjust_stock` es read-check-write sin lock.

## Why

Plan de seguridad Fase 3 (prioridad Muy alta) + SPEC-SALES-004 APPROVED 1.0.0.
OQ-SAGA-01/02/03 DECIDED (200+header, sin expiración, 422). Endurece ERF-01/03.

## Scope

- Sales: tabla `idempotency_keys`, repo, header en `POST /sales`, replay 200,
  mismatch 422, guarda concurrente 409, compensación con reintentos + log.
- Stock: tabla `stock_adjustments`, header opcional en `PATCH stock`, replay sin re-aplicar.
- `stock_client.adjust_stock(..., idem_key)` + Fake actualizado.
- Tests: `test_saga.py` (Sales), `test_idempotency.py` (Stock), E2E con replay.
- Docs: SPEC → VALIDATED, ADR-010 ya APPROVED, TRACEABILITY (sin filas nuevas).

## Constraints

- Rama `feature/sales-idempotency` desde `main` (lleva Fases 1-2 mergeadas).
- Delegación no disponible → inline acotado.
- Sin header: comportamiento idéntico al actual (compatibilidad + E2E viejo).
- Sin expiración de claves; sin outbox/broker; sin endpoints nuevos de incidentes.

## Checklist

- [x] F3-T1 — SPEC-SALES-004 DRAFT + rama + ADR-010 PROPOSED
- [x] F3-T2 — SPEC-SALES-004 → APPROVED 1.0.0 (OQ 200/sin-exp/422)
- [ ] F3-T3 — Implementar idempotencia + saga robusta con TDD
- [ ] F3-T4 — Verificación completa + SPEC VALIDATED + reporte

## Authorized scope

Rama `feature/sales-idempotency`. Archivos: `specs/sales/SPEC-SALES-004*`,
`docs/DECISIONS.md`, `services/sales-service/{app/{models/idempotency,repositories/idempotency_repository,services/sale_service,api/v1/endpoints/sales,clients/stock_client},tests/}`,
`services/stock-service/{app/{models/stock_adjustment,services/product_service,api/v1/endpoints/stock},tests/}`,
`infra/e2e_check.py`, `odd/tasks/sales-idempotency.md`.
Prohibido: matriz RBAC, hardening, modelos previos, frontend, compose, push/PR sin pedir.

## Acceptance criteria

- AC-SAGA04-01..06 verificados con los tests nombrados en la SPEC.
- Suites previas en verde (79/79 + nuevos) + E2E sin regresiones.

## Checks aplicables

`py -m pytest tests -q -p no:cacheprovider` por servicio; `py infra/e2e_check.py`.
TDD ROJO→VERDE donde haya RED ejecutable.

## Progress

- SPEC aprobada; pendiente implementar.

## Verification evidence

- (pendiente) commits + pytest por tarea.

## Next step

- F3-T3: modelos + repos + saga con claves + endpoints + tests.

## Rationale

- Doble nivel de claves (venta + línea) resuelve el timeout ambiguo sin broker.
- 200+header en replay (convención Stripe/PayPal); 422 ante mismatch (seguro).
- Concurrencia por restricción única (determinista, sin threads en tests).
