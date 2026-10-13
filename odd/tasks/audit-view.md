# Feature: audit-view (SPEC-STOCK-007 1.0.0)

## Objective

Auditoría visible: endpoint de movimientos (solo admin) + vista Auditoría con
filtro y paginado.

## Problem

Los movimientos solo se ven entrando a la DB.

## Why

SPEC-STOCK-007 APPROVED 1.0.0. OQ-AUDV-01/02 DECIDED (filtro/snapshot).

## Scope

- Stock: migración `codigo`/`nombre` en movements, endpoint `GET /stock/movements`, repo+service+schema, tests.
- Frontend: `stockApi.movements`, `AuditView.jsx`, pestaña admin.
- Docs: SPEC → VALIDATED, ADR-017 ya APPROVED.

## Constraints

- Rama `feature/audit-view` desde `main`.
- Migración incremental (baseline intacta, historial lineal).
- Sin escritura/borrado de movimientos; sin exportar/gráficas.

## Checklist

- [x] SPEC-STOCK-007 DRAFT + rama + ADR-017 PROPOSED
- [x] SPEC-STOCK-007 → APPROVED 1.0.0 (OQ filtro/snapshot)
- [ ] Implementar endpoint + UI con TDD/demo manual
- [ ] VALIDATED + merge + reporte

## Authorized scope

Rama `feature/audit-view`. Archivos: `specs/stock/SPEC-STOCK-007*`,
`docs/DECISIONS.md`,
`services/stock-service/{alembic/versions/*,app/{models/inventory_movement,repositories/inventory_movement_repository,services/product_service,api/v1/endpoints/stock,schemas/stock},tests/}`,
`frontend/src/{api.js,views/AuditView.jsx,App.jsx}`,
`odd/tasks/audit-view.md`.
Prohibido: saga, RBAC, hardening, frontend fuera de Auditoría, compose, push/PR sin pedir.

## Acceptance criteria

- AC-AUDV07-01..04 verificados (tests backend + demo manual UI).
- Suites previas en verde + E2E sin regresiones + build verde.

## Checks aplicables

`py -m pytest` por servicio; `npm run build`; demo manual UI. TDD donde aplique.

## Progress

- SPEC aprobada; pendiente implementar.

## Verification evidence

- (pendiente) commits + pytest + demo manual.

## Next step

- Implementar endpoint + UI y verificar.

## Rationale

- Snapshot evita joins y sobrevive a cambios del catálogo; migración incremental cuida el historial.
