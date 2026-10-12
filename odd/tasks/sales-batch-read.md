# Feature: sales-batch-read (SPEC-STOCK-006 1.0.0)

## Objective

Bajar la saga de ~3N llamadas a N+1 con lectura por lote, sin cambiar
comportamiento, códigos, idempotencia ni auditoría.

## Problem

Cada venta hace N×(`get_product` + `get_stock`) secuenciales + N ajustes.

## Why

Plan Fase 5 (prioridad Media) + SPEC-STOCK-006 APPROVED 1.0.0.
OQ-BATCH-01/02/03 DECIDED (encontrados/siempre/100). Optimiza ERF-01/03.

## Scope

- Stock: `BatchRequest`, `get_batch` (service), `POST /products/batch` (RBAC lector), tests batch.
- Sales: `stock_client.batch_get_products`, saga por camino único batch, fake + contadores, test de llamada única.
- Docs: SPEC → VALIDATED, ADR-012 ya APPROVED, TRACEABILITY ERF-01/03.

## Constraints

- Rama `feature/sales-batch-read` desde `main`.
- Delegación no disponible → inline acotado.
- Sin cachés/threads/batch-escritura; lecturas viejas intactas (aditivo).
- Sin asserts de tiempo (contadores, no wall-clock).

## Checklist

- [x] F5-T1 — SPEC-STOCK-006 DRAFT + rama + ADR-012 PROPOSED
- [x] F5-T2 — SPEC-STOCK-006 → APPROVED 1.0.0 (OQ encontrados/siempre/100)
- [x] F5-T3 — Batch + consumo en saga con TDD (3N→N+1)
- [x] F5-T4 — Verificación completa + SPEC VALIDATED

## Authorized scope

Rama `feature/sales-batch-read`. Archivos: `specs/stock/SPEC-STOCK-006*`,
`docs/DECISIONS.md`,
`services/stock-service/{app/{schemas/product,services/product_service,api/v1/endpoints/products},tests/}`,
`services/sales-service/{app/{clients/stock_client,services/sale_service},tests/}`,
`odd/tasks/sales-batch-read.md`.
Prohibido: matriz RBAC, saga (salvo consumo), hardening, migraciones, frontend, compose, push/PR sin pedir.

## Acceptance criteria

- AC-BATCH06-01..05 verificados con los tests nombrados en la SPEC.
- Suites previas en verde (97/97 + nuevos) + E2E sin regresiones.

## Checks aplicables

`py -m pytest tests -q -p no:cacheprovider` por servicio; `py infra/e2e_check.py`.
TDD ROJO→VERDE donde haya RED ejecutable.

## Progress

- Feature completa y validada en `feature/sales-batch-read` (4/4 tareas).

## Verification evidence

- Stock: 55 passed (47 previos + 8 batch). Sales: 51 passed (50 + 1 batch-usage).
- `py infra/e2e_check.py` → OK (ejerce el camino batch por debajo).
- SPEC-STOCK-006 1.0.0 VALIDATED; ADR-012 APPROVED; ERF-01/03 actualizados.
- Commits: 14b2d3a (SPEC DRAFT), 3e55562 (SPEC APPROVED), 0a7a9e1 (implementación), + cierre.

## Next step

- Decisión del usuario: merge a `main`. Luego Fase 6 (observabilidad) cuando quiera.

## Verification evidence

- (pendiente) commits + pytest por tarea.

## Next step

- F5-T3: schemas/service/endpoint batch + cliente + saga + tests.

## Rationale

- Lote aditivo de lectura: riesgo mínimo, ganancia clara (3N→N+1).
- Camino único en Sales: sin bifurcaciones ni modos.
