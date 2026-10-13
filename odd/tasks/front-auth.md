# Feature: front-auth (SPEC-FRONT-002 1.0.0)

## Objective

Frontend operando contra backend autenticado: login, sesión con refresh,
puertas por rol y vista Usuarios, con demo manual como verificación.

## Problem

El frontend actual llama sin tokens: todo 401 contra el backend de `main`.

## Why

SPEC-FRONT-002 APPROVED 1.0.0. OQ-FRONT-01/02/03 DECIDED
(localStorage/sí/manual). Completa ERF-09/10 en UI.

## Scope

- `frontend/src/auth.jsx` (nuevo): AuthContext + sesión en localStorage + refresh ante 401.
- `frontend/src/api.js`: Bearer en cada llamada + `authApi` (login/refresh/users).
- `frontend/src/views/LoginView.jsx`, `UsersView.jsx` (nuevos).
- `App.jsx`: puerta por sesión + tabs por rol + logout.
- `ProductsView.jsx` + `ProductRow`: gestión solo admin.
- `utils.js`: mensajes 401/403/429.
- Docs: SPEC → VALIDATED, ADR-014 ya APPROVED.

## Constraints

- Rama `feature/front-auth` desde `main`.
- Sin router, sin Vitest (demo manual + build, OQ-FRONT-03).
- Sin endpoints backend nuevos; sin registro/MFA.
- Verificación: `npm run build` verde + demo manual por AC (con backend real).

## Checklist

- [x] F7-T1 — SPEC-FRONT-002 DRAFT + rama + ADR-014 PROPOSED
- [x] F7-T2 — SPEC-FRONT-002 → APPROVED 1.0.0 (OQ localStorage/sí/manual)
- [x] F7-T3 — Login/sesión/RBAC en frontend (build verde; bug atob corregido)
- [x] F7-T4 — Demo manual por usuario OK + SPEC VALIDATED

## Authorized scope

Rama `feature/front-auth`. Archivos: `specs/frontend/SPEC-FRONT-002*`,
`docs/DECISIONS.md`, `frontend/src/{auth.jsx,api.js,utils.js,components.jsx,App.jsx,views/LoginView.jsx,views/UsersView.jsx,views/ProductsView.jsx}`,
`odd/tasks/front-auth.md`.
Prohibido: backend, compose, deps nuevas, push/PR sin pedir.

## Acceptance criteria

- AC-FRONT02-01..06 verificados con demo manual contra backend real.
- `npm run build` verde.

## Checks aplicables

`npm run build` en `frontend/`; demo manual por AC (login ambos roles,
401/403, refresh silencioso, usuarios admin). Sin RED/GREEN automatizado
(excepción TDD documentada: sin framework de tests en frontend).

## Progress

- Feature completa y validada en `feature/front-auth` (4/4 tareas).

## Verification evidence

- `npm run build` verde (35 módulos).
- Demo manual por usuario: todo OK (sign-off 2026-10-12, AC-FRONT02-01..06).
- SPEC-FRONT-002 1.0.0 VALIDATED; ADR-014 APPROVED.
- Commits: 5a39a31 (SPEC DRAFT), 4c6c7d8 (SPEC APPROVED), 4b4add6 (implementación), + cierre.

## Next step

- Merge a `main` (este turno).

## Verification evidence

- (pendiente) commits + build + tabla de demo manual.

## Next step

- F7-T3: auth.jsx + api.js + vistas + App.

## Rationale

- `api.js` como único canal HTTP (igual que hoy); AuthContext mínimo sin router.
- Demo manual como FRONT-001 (coherencia, sin Vitest en esta fase).
