# Feature: ops-observability (SPEC-OPS-002 1.0.0)

## Objective

Observabilidad mínima sin dependencias: access log JSON con request id,
`/metrics` Prometheus y `/ready` con chequeo real de DB.

## Problem

Sin visibilidad: ni conteos, ni latencias, ni readiness (solo `/health`
estático); logs de negocio en texto sin correlación.

## Why

Plan Fase 6 (última, prioridad Media) + SPEC-OPS-002 APPROVED 1.0.0.
OQ-OBS-01/02/03 DECIDED (hand-rolled/propia/ya).

## Scope

- `services/*/app/core/metrics.py` (nuevo): contadores + latencias + render.
- `services/*/app/core/middleware.py`: `ObservabilityMiddleware` (+ access log).
- `services/*/app/main.py`: middleware + `GET /metrics` + `GET /ready`.
- `services/*/app/core/database.py`: `check_db()`.
- Tests: `test_observability.py` por servicio (5 ACs).
- E2E: espera también `/ready`.
- Docs: SPEC → VALIDATED, ADR-013 ya APPROVED.

## Constraints

- Rama `feature/ops-observability` desde `main`.
- Delegación no disponible → inline acotado.
- Sin dependencias nuevas; sin tracing; sin propagación profunda del request id.
- El middleware nunca cambia códigos (BR-01); etiquetas acotadas (BR-02).

## Checklist

- [x] F6-T1 — SPEC-OPS-002 DRAFT + rama + ADR-013 PROPOSED
- [x] F6-T2 — SPEC-OPS-002 → APPROVED 1.0.0 (OQ hand-rolled/propia/ya)
- [x] F6-T3 — Observabilidad con TDD (metrics, middleware, ready)
- [x] F6-T4 — Verificación completa + SPEC VALIDATED

## Authorized scope

Rama `feature/ops-observability`. Archivos: `specs/ops/SPEC-OPS-002*`,
`docs/DECISIONS.md`,
`services/*/app/{main.py,core/metrics.py,core/middleware.py,core/database.py}`,
`services/*/tests/test_integration/test_observability.py`,
`infra/e2e_check.py`, `odd/tasks/ops-observability.md`.
Prohibido: negocio, RBAC, saga, hardening, migraciones, frontend, compose, push/PR sin pedir.

## Acceptance criteria

- AC-OBS02-01..05 verificados con los tests nombrados en la SPEC.
- Suites previas en verde (106/106 + nuevos) + E2E sin regresiones.

## Checks aplicables

`py -m pytest tests -q -p no:cacheprovider` por servicio; `py infra/e2e_check.py`.
TDD ROJO→VERDE donde haya RED ejecutable.

## Progress

- Feature completa y validada en `feature/ops-observability` (4/4 tareas). Plan de 6 fases COMPLETO.

## Verification evidence

- Stock: 60 passed (55 previos + 5 observabilidad). Sales: 56 passed (51 + 5).
- `py infra/e2e_check.py` → OK (espera también `/ready`).
- SPEC-OPS-002 1.0.0 VALIDATED; ADR-013 APPROVED.
- Commits: 76d0b0c (SPEC DRAFT), 4bcd596 (SPEC APPROVED), be222a8 (implementación), + cierre.

## Plan completo (6/6 fases en main tras merge)

- Fase 1 auth+RBAC (SPEC-AUTH-001) → Fase 2 hardening (SPEC-AUTH-002) → Fase 3 idempotencia (SPEC-SALES-004) → Fase 4 migraciones+auditoría (SPEC-OPS-001) → Fase 5 batch (SPEC-STOCK-006) → Fase 6 observabilidad (SPEC-OPS-002).

## Next step

- Decisión del usuario: merge a `main`, luego push/limpieza pendientes (17+ commits sobre origin/main).

## Verification evidence

- (pendiente) commits + pytest por tarea.

## Next step

- F6-T3: metrics + middleware + endpoints + check_db + tests.

## Rationale

- Hand-rolled: 3 contadores no justifican dependencia; contrato `/metrics` migrable.
- Ready local: evita flapping y acoples; E2E cubre integración.
