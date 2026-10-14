# Feature: sales-cliente-efectivo (SPEC-SALES-005)

## Objective

Venta con cliente (texto libre opcional) y pago en efectivo (monto recibido +
vuelto calculado server-side). Backend `sales-service`, TDD real
(RED → GREEN → REFACTOR) con pytest, migración incremental.

## Problem

`Sale` no tiene cliente ni pago: el ticket no identifica al comprador y la caja
no registra efectivo/vuelto. SPEC-SALES-001 los excluye explícitamente (nuevo
ERF requerido).

## Why

Decisión del usuario (2026-10-14): Fase 2 con solo efectivo; modo backend
clásico (SPEC + gate + TDD) para que nada se rompa.

## Scope

- SPEC `SPEC-SALES-005-*` + ERF nuevo (DRAFT → APPROVED → VALIDATED).
- `sales-service`: columna `cliente` nullable + `monto_recibido`/`vuelto` en
  `sales` (migración lineal, baseline intacta), schemas Pydantic
  (`SaleCreate`/`SaleRead`), validación en service (vuelto = recibido − total,
  422 si < total; precios y vuelto nunca del request), tests pytest.
- Docs: SPEC + ERF + este documento.

## Constraints

- Rama `feature/sales-cliente-efectivo` desde `main`.
- Un solo head Alembic; baseline `5df949f9a5f2` intacta; prod solo adelante.
- Principio vigente: totales/precios siempre server-side desde Stock.
- Sin impuestos/QR. Sin frontend en esta fase (siguiente paso).
- Sin push/PR sin pedir.

## Checklist

- [x] SALE-EFE-01 SPEC-SALES-005 DRAFT (+ ERF) + rama (commit 2e49024)
- [ ] SALE-EFE-02 SPEC-SALES-005 → APPROVED 1.0.0 (gate del usuario, OQs)
- [ ] SALE-EFE-03 Implementación TDD (RED observado → GREEN → REFACTOR) + pytest verde
- [ ] SALE-EFE-04 Smoke contra compose/Postgres + VALIDATED + merge (+ push si se pide)

## Authorized scope

Rama `feature/sales-cliente-efectivo`. Archivos:
`specs/sales/SPEC-SALES-005*`, `docs/ERF-*.md` (si nuevo),
`odd/tasks/sales-cliente-efectivo.md`,
`services/sales-service/{app/{models/sale,schemas/sale,services/sale_service,api/v1/endpoints/sales},alembic/versions/*,tests/}`.
Prohibido: stock-service, frontend, impuestos/QR, compose fuera de smoke,
push/PR sin pedir.

## Acceptance criteria

- ACs `Given/When/Then` de la SPEC verificados (pytest + smoke).
- Suites previas en verde, sin regresiones (idempotencia/saga intactas).

## Checks aplicables

TDD estricto: `python -m pytest tests -q -p no:cacheprovider` desde
`services/sales-service`; observar RED antes de implementar, GREEN después,
REFACTOR con tests en verde. Nunca inventar evidencia RED/GREEN ni el runner.

## Route declaration

- SALE-EFE-01: delegated spec-draft (preparation trigger: SPECs/ERFs modelo).
- SALE-EFE-03: delegated writer (múltiples archivos no triviales) con TDD
  estricto observado.
- Verificación: writer self-report (`<comando>: <resultado>` observado) +
  parent spot check + assess RDD por work-unit commit.

## Progress

- SALE-EFE-01 cerrada: SPEC-SALES-005 DRAFT v0.1.0 + ERF-11 nuevo en rama
  `feature/sales-cliente-efectivo` (commit 2e49024). 7 ACs, 5 OQs abiertas
  (OQ-CLI05-01 ERF nuevo ya aplicada).

## Verification evidence

- SALE-EFE-01: SPEC existe en DRAFT (spot check metadata); rama y commit
  verificados por parent. Solo SPEC+ERF tocados, sin push.

## Next step

- SALE-EFE-02: gate del usuario (OQ-CLI05-02..06) → APPROVED 1.0.0.
