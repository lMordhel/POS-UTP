# Feature: front-admin-manage (SPEC-FRONT-003 1.0.0)

## Objective

Gestión admin completa en UI: editar producto y ajuste manual de stock,
solo admin, con reload y errores mapeados.

## Problem

Crear/desactivar existen; editar y ajustar solo por Swagger.

## Why

SPEC-FRONT-003 APPROVED 1.0.0. OQ-FADM-01/02 DECIDED
(nombre+precio+desc / motivo opcional). Ideas 1+2 del plan front.

## Scope

- `api.js`: `stockApi.update` + `stockApi.adjust`.
- `ProductsView.jsx`: paneles Editar y Ajustar (admin) + botones por fila.
- `components.jsx`: `ProductRow` con Editar/Ajustar condicionales.
- Docs: SPEC → VALIDATED, ADR-015 ya APPROVED.

## Constraints

- Rama `feature/front-admin-manage` desde `main`.
- Sin router/tests-UI; demo manual + build (precedente).
- Sin endpoints backend nuevos; sin auditoría visible.

## Checklist

- [x] SPEC-FRONT-003 DRAFT + rama + ADR-015 PROPOSED
- [x] SPEC-FRONT-003 → APPROVED 1.0.0 (OQ campos/motivo)
- [x] Gestión admin + UX + cambio de clave (build verde)
- [x] Demo manual OK + VALIDATED + merge

## Authorized scope

Rama `feature/front-admin-manage`. Archivos: `specs/frontend/SPEC-FRONT-003*`,
`docs/DECISIONS.md`, `frontend/src/{api.js,views/ProductsView.jsx,components.jsx}`,
`odd/tasks/front-admin-manage.md`.
Prohibido: backend, compose, push/PR sin pedir.

## Acceptance criteria

- AC-FADM03-01..05 verificados con demo manual contra backend real.
- `npm run build` verde.

## Checks aplicables

`npm run build`; demo manual por AC. Excepción TDD documentada (sin framework UI).

## Progress

- SPEC aprobada; pendiente implementar.

## Verification evidence

- (pendiente) commits + build + demo manual.

## Next step

- Implementar UI y verificar.

## Rationale

- Reutiliza patrones (banner, reload, puertas isAdmin); cambios acotados a 3 ficheros.
