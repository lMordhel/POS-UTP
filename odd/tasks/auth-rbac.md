# Feature: auth-rbac (SPEC-AUTH-001 1.0.0)

## Objective

Cerrar el acceso al backend con autenticación JWT y autorización por roles
(`admin`/`cajero`), con enforcement en backend según la matriz aprobada.

## Problem

Cualquiera con la URL opera la API: sin usuarios, tokens ni roles; CORS `*`;
ventas sin idempotencia (fases 2+ fuera de esta feature).

## Why

Decisión de usuario 2026-10-12 (Opción 1, modelo mínimo académico) + SPEC-AUTH-001
APPROVED 1.0.0. ERF-09/ERF-10 propuestos al documento académico.

## Scope

- `services/sales-service`: `core/security.py`, modelos `User`/`RefreshToken`,
  `auth`+`users` (routers delgados → services → repositories), bootstrap admin,
  RBAC en routers Sales.
- `services/stock-service`: `core/security.py` (solo verificación) + RBAC en routers.
- Tests por AC (AC-AUTH01-01..10) + docs (TRACEABILITY → VALIDATED).

## Constraints

- Sin SPEC aprobada no hay funcionalidad (ya cumplido: 1.0.0 APPROVED).
- Delegación de subagentes no disponible en este runtime (free tier) → trabajo
  inline en archivos acotados, un paso por vez.
- Servidores de demo corriendo del árbol (sin reload): no les afecta el código
  hasta reiniciarlos; tests usan TestClient aislado.
- Nueva dependencia: `bcrypt` (+ `pyjwt` ya instalado). Solo `requirements.txt`.

## Checklist

- [x] T1 — SPEC-AUTH-001 → APPROVED 1.0.0 + rama `feature/auth-rbac` + este documento
- [x] T2 — `core/security.py` en Sales y Stock (hash bcrypt, JWT HS256, `require_role`) + `bcrypt` en requirements (commit `feat(auth)`, tests 5/5 en ambos)
- [x] T3 — Modelos `users`/`refresh_tokens` + bootstrap admin desde env en Sales (TDD 4/4)
- [x] T4 — `auth/login`, `auth/refresh` rotativo, `users` CRUD + RBAC en routers Sales (TDD 11/11; bug revocación-rollback cazado por test)
- [x] T5 — RBAC en routers Stock según matriz (TDD 4/4; suites existentes migradas a headers)
- [x] T6 — Verificación completa + TRACEABILITY → VALIDATED

## Authorized scope

Rama `feature/auth-rbac`. Archivos: `specs/auth/*`, `docs/{DECISIONS,TRACEABILITY}.md`,
`services/sales-service/{app/{core/security,models/,schemas/,services/,repositories/,api/},requirements.txt,tests/}`,
`services/stock-service/{app/{core/security,api/},requirements.txt,tests/}`.
Prohibido: frontend, infra/compose, `.env` con secretos reales, push/PR sin pedir.

## Acceptance criteria

- AC-AUTH01-01..10 verificados con tests nombrados en la SPEC.
- `pytest` verde en ambos servicios + E2E previo sin regresiones.
- TRACEABILITY ERF-09/10 → Validated con tests reales.

## Checks aplicables

`py -m pytest tests -q -p no:cacheprovider` en cada servicio; `py infra/e2e_check.py`.
Excepción TDD documentada donde no haya RED ejecutable con sentido.

## Progress

- Feature completa y validada en `feature/auth-rbac` (6/6 tareas, 1 commit por tarea).

## Verification evidence

- Sales: 33 passed (`test_security` 6, `test_users` 4, `test_sales` 12, `test_auth` 11).
- Stock: 34 passed (25 previos + `test_security` 5 + `test_rbac` 4).
- `py infra/e2e_check.py` → OK con login (venta 201, stock 5→3, 401/409/404).
- SPEC-AUTH-001 1.0.0 VALIDATED; ERF-09/10 Validated en TRACEABILITY.
- Commits: c99ecee (T1 docs), 827a55e (T2), 01df2bb (T3), 6dc52f6 (T4), b993bc4 (T5), d959799 (T6).

## Next step

- Decisión del usuario: merge a `main` / PR (no se pushea sin pedir). Luego Fase 2 (SPEC hardening: CORS, rate limit) o demo con login en frontend (futura SPEC).
- Nota demo: los servidores de modo local corrían código pre-auth (detenidos para el E2E); al reiniciarlos usarán el código nuevo y el frontend actual quedará sin acceso hasta tener login.

## Verification evidence

- (pendiente) commit T1 + pytest por tarea.

## Next step

- Cerrar T1 con commit docs, luego T2 (instalar bcrypt + `core/security.py`).

## Rationale

- Usuarios en `ventas_db`/Sales (ADR-006): evita tercer servicio (YAGNI).
- Refresh rotativo con reúso (ADR-007): estándar demostrable, sin estado distribuido.
- Ventas inmutables (BR-05): el requisito del cajero se cumple por construcción.
