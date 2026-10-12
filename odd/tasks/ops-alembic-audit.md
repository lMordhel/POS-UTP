# Feature: ops-alembic-audit (SPEC-OPS-001 1.0.0)

## Objective

Esquema versionado con Alembic en ambos servicios y movimientos de inventario
auditables + logs de seguridad, sin cambiar endpoints.

## Problem

`create_all` no versiona ni evoluciona con datos; los ajustes manuales de stock
no dejan traza con actor; eventos de seguridad sin logs.

## Why

Plan de seguridad Fase 4 (prioridad Alta) + SPEC-OPS-001 APPROVED 1.0.0.
OQ-AUD-01/02/03 DECIDED (tabla+logs, un solo camino, sí baseline).

## Scope

- `services/*/alembic/` (env.py + versions/baseline con upgrade/downgrade) + `alembic` en requirements.
- `init_db` adoptar-o-migrar + bootstrap preservado.
- Stock: `inventory_movements` (modelo, repo, hook en adjust con actor desde claims) + endpoint pasa claims.
- Sales: logs en auth_service (login, refresh) y user_service (CRUD).
- Tests: `test_migrations.py` por servicio, movimientos + replay, logs con caplog.
- Docs: SPEC → VALIDATED, ADR-011 ya APPROVED, `docs/MIGRATIONS.md` (cómo crear revisión y sellar DB vieja).

## Constraints

- Rama `feature/ops-alembic-audit` desde `main`.
- Delegación no disponible → inline acotado.
- Sin endpoints nuevos; sin expiración/purga; sin seeds de negocio.
- Downgrade solo dev/tests; en prod solo hacia adelante.

## Checklist

- [x] F4-T1 — SPEC-OPS-001 DRAFT + rama + ADR-011 PROPOSED
- [x] F4-T2 — SPEC-OPS-001 → APPROVED 1.0.0 (OQ tabla+logs/todo/sí)
- [x] F4-T3 — Migraciones + auditoría con TDD (Alembic, movements, logs)
- [x] F4-T4 — Verificación completa + SPEC VALIDATED

## Authorized scope

Rama `feature/ops-alembic-audit`. Archivos: `specs/ops/SPEC-OPS-001*`,
`docs/{DECISIONS,MIGRATIONS}.md`,
`services/*/alembic/**`, `services/*/requirements.txt`,
`services/*/app/core/database.py`,
`services/stock-service/app/{models/inventory_movement,repositories/inventory_movement_repository,services/product_service,api/v1/endpoints/stock}.py`,
`services/sales-service/app/services/{auth_service,user_service}.py`,
`services/*/tests/test_integration/{test_migrations,test_audit*}.py`,
`odd/tasks/ops-alembic-audit.md`.
Prohibido: endpoints nuevos, RBAC, saga, hardening, frontend, compose, push/PR sin pedir.

## Acceptance criteria

- AC-OPS01-01..06 verificados con los tests nombrados en la SPEC.
- Suites previas en verde (86/86 + nuevos) + E2E sin regresiones.

## Checks aplicables

`py -m pytest tests -q -p no:cacheprovider` por servicio; `py infra/e2e_check.py`.
TDD ROJO→VERDE donde haya RED ejecutable.

## Progress

- Feature completa y validada en `feature/ops-alembic-audit` (4/4 tareas).

## Verification evidence

- Stock: 47 passed (42 previos + 3 migraciones + 2 auditoría). Sales: 50 passed (44 + 3 migraciones + 3 logs).
- `py infra/e2e_check.py` → OK (ejerce migrate en DBs temporales).
- SPEC-OPS-001 1.0.0 VALIDATED; ADR-011 APPROVED; `docs/MIGRATIONS.md` creada.
- Commits: 7af6564 (SPEC DRAFT), d28d92d (SPEC APPROVED), 8626382 (implementación), + cierre.

## Next step

- Decisión del usuario: merge a `main`. Luego Fase 5 (SPEC optimización) o Fase 6 (observabilidad) cuando quiera.

## Verification evidence

- (pendiente) commits + pytest por tarea.

## Next step

- F4-T3: env.py + baselines + init_db + movements + logs + tests.

## Rationale

- Alembic por servicio (no multi-DB): simple y fiel a la propiedad de datos.
- Adoptar-o-migrar preserva las DBs demo con datos.
- Auditoría a nivel DB + logs; lectura vía endpoints existentes y Fase 6.
