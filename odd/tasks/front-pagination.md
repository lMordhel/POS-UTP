# Feature: front-pagination (SPEC-FRONT-004 1.0.0)

## Objective

Listados por páginas (20 fijos) en Productos, Ventas y Usuarios, sin backend
nuevo, con Anterior/Siguiente y búsqueda que reinicia.

## Problem

Las tres vistas cargan todo de una vez; con datos reales se ponen lentas.

## Why

SPEC-FRONT-004 APPROVED 1.0.0. OQ-PAG-01/02 DECIDED (fijo 20 / tres vistas).

## Scope

- `api.js`: `skip/limit` en los tres `list` (default `limit = PAGE_SIZE+1`).
- `components.jsx`: `Pager` reutilizable.
- `ProductsView/SalesView/UsersView`: estado de página + truco limit+1.
- `utils.js`: `PAGE_SIZE = 20`.
- Docs: SPEC → VALIDATED, ADR-016 ya APPROVED.

## Constraints

- Rama `feature/front-pagination` desde `main`.
- Sin backend nuevo; sin totales (truco limit+1); sin router/tests-UI.
- `NewSaleView` (catálogo para vender) queda sin paginar en esta fase.

## Checklist

- [x] SPEC-FRONT-004 DRAFT + rama + ADR-016 PROPOSED
- [x] SPEC-FRONT-004 → APPROVED 1.0.0 (OQ fijo/tres vistas)
- [x] Paginación en 3 vistas + fix CORS compose (build verde)
- [x] Demo manual OK + VALIDATED + merge + push

## Authorized scope

Rama `feature/front-pagination`. Archivos: `specs/frontend/SPEC-FRONT-004*`,
`docs/DECISIONS.md`, `frontend/src/{api.js,utils.js,components.jsx,views/ProductsView.jsx,views/SalesView.jsx,views/UsersView.jsx}`,
`odd/tasks/front-pagination.md`.
Prohibido: backend, compose, push/PR sin pedir.

## Acceptance criteria

- AC-PAG04-01..03 verificados con demo manual (25 productos de prueba).
- `npm run build` verde.

## Checks aplicables

`npm run build`; demo manual por AC. Excepción TDD documentada.

## Progress

- Feature completa y validada en `feature/front-pagination` (4/4 tareas + fix CORS).

## Verification evidence

- `npm run build` verde.
- Demo manual por usuario: todo OK (pager en 3 vistas tras recarga forzada).
- SPEC-FRONT-004 1.0.0 VALIDATED; ADR-016 APPROVED.
- 25 productos P-PAG sembrados para la demo (limpiar cuando quieran).

## Verification evidence

- (pendiente) commits + build + demo manual.

## Next step

- Implementar UI y verificar.

## Rationale

- Truco limit+1 evita endpoint de conteo; tamaño fijo evita selector innecesario.
