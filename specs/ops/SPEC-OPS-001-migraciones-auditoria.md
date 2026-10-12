# SPEC-OPS-001 — Migraciones con Alembic y auditoría

## Metadata

- ID: SPEC-OPS-001
- Requirement: Plan de seguridad Fase 4, transversal (toca ERF-02/05/06 en Stock y ERF-09 en Sales sin cambiar endpoints; sin ERF nuevo).
- Service: Stock + Sales
- Status: APPROVED
- Version: 1.0.0
- Priority: Alta

## Objective

Esquema versionado (fin de `create_all` como única vía) y movimientos de
inventario auditables (quién, qué, cuánto, antes/después, por qué), más logs
estructurados de los eventos de seguridad.

## Scope

* Alembic por servicio (`alembic/` + `versions/` + revisión baseline autogenerada con downgrade).
* `init_db` con flujo adoptar-o-migrar: DB vacía → `upgrade head`; DB pre-Alembic con tablas → `stamp head` (conserva datos); arranque falla si hay múltiples heads.
* Bootstrap del admin preservado tras migrar (OQ-AUTH-04 sigue vigente).
* Tabla `inventory_movements` en `stock_db`: un registro por cada `PATCH stock` aplicado (actor `sub`/`rol` desde claims, motivo, delta, antes/después, clave de idempotencia nullable). Los replays por clave no crean movimiento (nada cambió).
* Logs estructurados en Sales (std logger, Fase 6 los consumirá): login ok/fallido, refresh reutilizado, CRUD de usuarios, saga 502/compensación agotada (ya existe el de compensación).
* Documentar cómo generar una revisión (`revision --autogenerate`) y cómo sellar una DB vieja.

## Out of Scope

* Purga/retención de auditoría y de claves (nota futura).
* Endpoint de consulta de movimientos (se audita a nivel DB; Fase 6 expondrá métricas).
* Outbox/broker, dashboards, seed de datos salvo admin.
* Migraciones de datos complejas (backfills): baseline + incrementales simples.

## Actors

* Operador: aplica/sella migraciones, configura `DATABASE_URL`.
* Auditor: lee `inventory_movements` y logs.
* Servicios: migran al arrancar (`init_db`), escriben auditoría al operar.

## Preconditions

* Dependencia `alembic` agregada en ambos `requirements.txt`.
* Modelos actuales como fuente para la baseline (incluye `users`, `refresh_tokens`, `idempotency_keys`, `stock_adjustments`).

## Functional Requirements

* FR-01: Cada servicio debe tener `alembic/env.py` que lea `DATABASE_URL` de settings y `Base.metadata` propio, y directorio `versions/` con revisión baseline (upgrade + downgrade) del esquema actual.
* FR-02: `init_db` debe: si no hay tabla `alembic_version` y existen tablas de negocio → `stamp head` (adopta, conserva datos); si no → `upgrade head`. Con múltiples heads → error de arranque.
* FR-03: Tras migrar, el bootstrap de admin (FR-08 de SPEC-AUTH-001) debe seguir funcionando.
* FR-04: Cada `PATCH stock` aplicado debe insertar un `inventory_movement` con `producto_id`, `delta`, `cantidad_antes`, `cantidad_despues`, `motivo`, `actor_sub`, `actor_rol` y `clave` (nullable). El actor sale de los claims del endpoint (usuario o `svc-sales`).
* FR-05: Los replays por clave (sin cambio) no deben crear movimientos.
* FR-06: Sales debe emitir logs con logger nombrado y campos fijos en: login ok/fallido (sin passwords), refresh reutilizado, crear/editar/desactivar usuario, saga 502.
* FR-07: Documentar en cada servicio cómo crear una revisión y cómo sellar una DB pre-Alembic.

## Business Rules

* BR-01: En producción solo hacia adelante (downgrade reservado a dev/tests).
* BR-02: Los movimientos son inmutables: sin endpoints de escritura ni borrado.
* BR-03: Sin SPEC aprobada no se implementa (SDD-001); esta SPEC en DRAFT no autoriza código.

## API Contract

Sin endpoints nuevos ni cambios de contrato. Cambios observables: arranque migra/sella; cada PATCH deja traza auditable; logs nuevos.

## Validation Rules

* IDs de revisión únicos por servicio; mensajes descriptivos; cada revisión con `downgrade()` funcional.
* `motivo` obligatorio en movimientos (heredado de `StockAdjust`); actor siempre presente ( endpoint autenticado).

## Error Handling

* Múltiples heads o revisión rota → fallo de arranque con mensaje del operador.
* DB ilegible/inaccesible → fallo de arranque (igual que hoy).

## Acceptance Criteria

### AC-OPS01-01 — Baseline aplica limpio

Given sqlite vacío
When se ejecuta `upgrade head` de cada servicio
Then deben existir todas las tablas del esquema actual (incluidas auth/saga).

### AC-OPS01-02 — Adopta DB pre-Alembic con datos

Given una DB creada con `create_all` y una fila de negocio
When arranca `init_db`
Then debe sellar head, conservar la fila y seguir operando.

### AC-OPS01-03 — Downgrade revierte

Given baseline aplicada en sqlite de prueba
When se ejecuta `downgrade base`
Then las tablas de la baseline deben desaparecer y `upgrade head` restaura.

### AC-OPS01-04 — Todo ajuste queda auditado

Given un `PATCH stock` aplicado (con y sin clave; con usuario y con servicio)
When se consulta `inventory_movements`
Then debe haber una fila con actor, motivo, delta, antes/después y clave.

### AC-OPS01-05 — Replay no audita de más

Given un replay por clave (sin cambio)
When se consulta `inventory_movements`
Then no debe aparecer fila nueva para ese replay.

### AC-OPS01-06 — Eventos de seguridad en logs

Given login fallido, refresh reutilizado y CRUD de usuarios
When se ejecutan
Then deben emitirse logs con usuario/resultado (nunca passwords).

## Open Questions

* OQ-AUD-01: DECIDED 2026-10-12 → movimientos en tabla + seguridad en logs (ventas inmutables ya auditan; usuarios bajo volumen; ampliar en Fase 6+ si hace falta).
* OQ-AUD-02: DECIDED 2026-10-12 → un solo camino (`upgrade head` / adoptar-o-migrar en todo entorno); tests con `create_all` en memoria + test de head limpio.
* OQ-AUD-03: DECIDED 2026-10-12 → sí, baseline única por servicio + seed solo-admin vía bootstrap (sin seeds de negocio en migraciones).

## Traceability

Requirement: Plan Fase 4 (transversal; endurece ERF-02/05/06 y ERF-09 sin cambiar endpoints)
Endpoint: Sin cambios (auditoría a nivel DB + logs)
Service: Stock (migraciones + movements) + Sales (migraciones + logs)
Tests: Pendiente (futuros: `test_baseline_upgrades_clean`, `test_init_db_adopts_legacy_db`, `test_downgrade_reverts`, `test_adjust_writes_movement`, `test_keyed_replay_writes_no_movement`, `test_security_events_logged`)

## Technical Notes

* Estructura por servicio: `alembic/env.py` (URL desde settings en runtime; `alembic.ini` mínimo o config programática), `versions/<rev>_baseline.py`. Downgrade de baseline: `drop_table` en orden inverso.
* `init_db`: inspector → `has_table("alembic_version")`; `stamp`/`upgrade` vía API de Alembic (`command.stamp/upgrade` con `Config` construida en código, sin depender del cwd).
* Actor: el endpoint pasa `claims` al servicio (`adjust_stock(..., actor=...)`); servicio-a-servicio deja `svc-sales` y la atribución fina sigue en `motivo=venta:{id}`.
* Tests: sqlite archivo temporal (no `:memory:` estático, para ejercer stamp/upgrade reales); caplog para logs.
* Comandos a documentar: `alembic revision --autogenerate -m "..."` y sellado de DBs viejas.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-12 | OQ-AUD-01/02/03 DECIDED (tabla+logs, un solo camino, sí baseline); DRAFT → APPROVED (autoriza desarrollo) | User approval: tabla+logs, todo, sí |
|---|---|---|---|
| 0.1.0 | 2026-10-12 | Initial specification (DRAFT, no autoriza implementar) | Plan de seguridad Fase 4 |
