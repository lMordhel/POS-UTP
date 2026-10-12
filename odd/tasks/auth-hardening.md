# Feature: auth-hardening (SPEC-AUTH-002 1.0.0)

## Objective

Endurecer HTTP en ambos servicios: CORS restrictivo, rate limiting en auth +
escrituras, cabeceras seguras, fail-fast en prod y docs desactivados en prod.

## Problem

`allow_origins=["*"]`, sin freno a fuerza bruta/abuso, sin cabeceras de
seguridad, arranque permisivo con secretos de ejemplo y docs expuestos.

## Why

Plan de seguridad Fase 2 (prioridad Muy alta) + SPEC-AUTH-002 APPROVED 1.0.0.
OQ-HARD-01/02 DECIDED (sí, sí). Endurece ERF-09/10 sin ERF nuevo.

## Scope

- `services/*/app/core/config.py`: `CORS_ORIGINS`, límites por env, fail-fast extendido.
- `services/*/app/core/middleware.py` (nuevo): `SecurityHeadersMiddleware` + `make_limiter()` + handler 429.
- `services/*/app/main.py`: CORS desde settings, middleware, limiter, docs off en prod.
- `services/*/requirements.txt`: `slowapi`.
- Tests: `test_hardening.py` por servicio (CORS, 429, headers, fail-fast, docs-off) + fixtures de limiter aislado.
- Docs: SPEC → VALIDATED, ADR-009 ya APPROVED, TRACEABILITY (sin filas nuevas: endurece ERF-09/10).

## Constraints

- Rama `feature/auth-hardening` apilada sobre `feature/auth-rbac` (necesita el código de Fase 1); el merge sigue el orden de la pila.
- Delegación no disponible → inline en archivos acotados.
- slowapi en memoria: 1 réplica (documentado en SPEC, fuera de alcance Redis).
- No tocar comportamiento funcional (solo 429/headers/CORS/config).

## Checklist

- [x] F2-T1 — SPEC-AUTH-002 DRAFT + rama + ADR-009 PROPOSED
- [x] F2-T2 — SPEC-AUTH-002 → APPROVED 1.0.0 (OQ-HARD-01/02 sí, sí)
- [ ] F2-T3 — Implementar hardening en Sales y Stock con TDD
- [ ] F2-T4 — Verificación completa + SPEC VALIDATED + reporte

## Authorized scope

Rama `feature/auth-hardening`. Archivos: `specs/auth/SPEC-AUTH-002*`,
`docs/DECISIONS.md`, `services/*/app/{main.py,core/config.py,core/middleware.py}`,
`services/*/requirements.txt`, `services/*/tests/{conftest.py,test_integration/test_hardening.py}`,
`odd/tasks/auth-hardening.md`.
Prohibido: cambiar matriz RBAC, saga, modelos, frontend, compose, push/PR sin pedir.

## Acceptance criteria

- AC-HARD02-01..06 verificados con los tests nombrados en la SPEC.
- Suites previas en verde (67/67 + nuevos) + E2E sin regresiones.

## Checks aplicables

`py -m pytest tests -q -p no:cacheprovider` por servicio; `py infra/e2e_check.py`.
TDD ROJO→VERDE donde haya RED ejecutable.

## Progress

- SPEC aprobada; pendiente implementar.

## Verification evidence

- (pendiente) commits + pytest por tarea.

## Next step

- F2-T3: instalar slowapi + config/middleware/mains + tests.

## Rationale

- `slowapi` estándar (como `bcrypt` en Fase 1); en memoria basta con 1 réplica.
- Decisiones OQ del usuario aplicadas tal cual (docs off en prod, lecturas sin límite).
