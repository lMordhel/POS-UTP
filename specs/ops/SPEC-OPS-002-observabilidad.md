# SPEC-OPS-002 — Observabilidad (logs, métricas, salud)

## Metadata

- ID: SPEC-OPS-002
- Requirement: Plan de seguridad Fase 6, transversal (sin ERF nuevo; hace consumible lo instrumentado en Fases 1-5).
- Service: Stock + Sales
- Status: DRAFT
- Version: 0.1.0
- Priority: Media

## Objective

Que cada servicio cuente qué pasa (métricas), lo narre estructurado (logs JSON
con request id) y diga si está listo (readiness), sin dependencias nuevas.

## Scope

* Middleware de acceso: una línea JSON por request (`method`, `route`, `status`, `duration_ms`, `request_id`) en logger `app.access`; header `X-Request-ID` generado o propagado.
* `GET /metrics` en ambos servicios: formato texto Prometheus con `http_requests_total{method,route,status}`, `http_request_duration_seconds_{sum,count}` y `app_info{version}`. Contadores en memoria (1 réplica, documentado).
* `GET /ready`: chequea DB propia (`SELECT 1`) → 200 `{status:"ok"}` o 503. `/health` queda como liveness sin cambios.
* Etiqueta `route` = plantilla de ruta (`/api/v1/products/{product_id}`), nunca path crudo (cardinalidad acotada).

## Out of Scope

* Tracing distribuido (OTel), Prometheus/Grafana, alertas, agregación de logs.
* Propagación del request id a logs de negocio (futura; hoy solo access log + header).
* Readiness con dependencias cruzadas (Sales no chequea Stock; la integración la cubre el E2E).
* Métricas de negocio extra (ventas por minuto, etc.): futuras con la misma base.

## Actors

* Operador: scrapea `/metrics`, usa `/ready` en orquestadores, lee logs JSON.
* Cliente: puede enviar `X-Request-ID` para correlación.

## Preconditions

* Fases 1-5 implementadas (logs de seguridad y middleware base existen).

## Functional Requirements

* FR-01: Cada respuesta debe traer `X-Request-ID` (recibido o generado UUID4); el access log debe incluirlo junto a `method`, `route`, `status` y `duration_ms` en JSON de una línea.
* FR-02: `GET /metrics` debe exponer contadores por `{method, route, status}` y suma/conteo de duraciones, más `app_info{version="1.0.0"}`; `Content-Type: text/plain; version=0.0.4`. Sin autenticación (igual que `/health`).
* FR-03: `GET /ready` debe ejecutar `SELECT 1` en la DB propia: ok → 200; fallo → 503 `{status:"unready"}`. Sin autenticación.
* FR-04: La etiqueta `route` debe usar la plantilla (sin IDs reales); rutas no encontradas → `route="unknown"`.
* FR-05: Los logs de negocio existentes (auth, saga, compensación) siguen en texto; el JSON aplica al access log (convivencia documentada, unificación futura).

## Business Rules

* BR-01: Observar no frena: el middleware nunca bloquea ni cambia códigos (solo añade header y cuenta).
* BR-02: Cardinalidad acotada: sin valores libres (IDs, usernames, queries) en etiquetas.
* BR-03: Sin SPEC aprobada no se implementa (SDD-001); esta SPEC en DRAFT no autoriza código.

## API Contract

* `GET /metrics` → 200 texto Prometheus. `GET /ready` → 200/503 JSON. Ambos públicos. Header `X-Request-ID` en todas las respuestas.

## Validation Rules

* `X-Request-ID` entrante: se acepta tal cual (opaco, ≤ 128 propuesto; si excede, se genera uno nuevo).
* Duraciones en segundos (float) para métricas, ms enteros en logs.

## Error Handling

* `/ready` con DB caída → 503 (no 500).
* Fallo del propio middleware de métricas → nunca 500: ante error interno, cuenta lo contable y sigue.

## Acceptance Criteria

### AC-OBS02-01 — Request id de ida y vuelta

Given un `GET /health` con `X-Request-ID: abc`
When responde
Then debe devolver el mismo header y el access log debe incluirlo.

### AC-OBS02-02 — Métricas cuentan por plantilla

Given llamadas a `GET /api/v1/products/1` y `/2` (autenticadas)
When se pide `/metrics`
Then `http_requests_total` debe agruparlas bajo `route="/api/v1/products/{product_id}"` con sus status.

### AC-OBS02-03 — Latencias y app_info

Given tráfico cursado
When se pide `/metrics`
Then debe haber `http_request_duration_seconds_sum/count` y `app_info{version="1.0.0"} 1`.

### AC-OBS02-04 — Readiness real

Given DB operativa → `/ready` 200; Given chequeo roto (doble con engine inválido) → 503 `{status:"unready"}`.

### AC-OBS02-05 — Access log JSON

Given cualquier request
When se inspecciona el log `app.access`
Then debe ser JSON con `method`, `route`, `status`, `duration_ms`, `request_id`.

## Open Questions

* OQ-OBS-01: ¿Métricas hand-rolled mínimas sin dependencia (propuesta) o `prometheus_client`? La propuesta evita una dependencia por 3 contadores con formato válido.
* OQ-OBS-02: ¿`/ready` solo DB propia (propuesta; integración vía E2E) o también chequea Sales→Stock? Chequear abajo acopla readiness y genera flapping.
* OQ-OBS-03: ¿Access log JSON ya (propuesta) y unificación de logs de negocio después, o todo junto ahora? Todo junto duplica el alcance de la fase.

## Traceability

Requirement: Plan Fase 6 (transversal; consume Fases 1-5, sin ERF nuevo)
Endpoint: `GET /metrics`, `GET /ready` (nuevos, públicos) + header en todos
Service: Stock + Sales
Tests: Pendiente (futuros: `test_request_id_echo`, `test_metrics_groups_by_template`, `test_metrics_latency_and_info`, `test_ready_ok_and_unready`, `test_access_log_json`)

## Technical Notes

* Middleware propio (Starlette `BaseHTTPMiddleware`, como el de headers): mide con `perf_counter`, resuelve plantilla vía `request.scope["route"].path` con fallback, actualiza contadores en módulo `core/metrics.py` (dicts + Lock), log JSON con `json.dumps`.
* `check_db()` testeable en `core/database.py` (SELECT 1 con engine propio/timeout corto); endpoint delgado.
* Tests: TestClient emite requests reales (métricas suben); `X-Request-ID` custom; 503 con monkeypatch del check o engine inválido; caplog en `app.access`.
* E2E sin cambios (pasa por el middleware y suma métricas, sin assertions nuevas salvo 200 en `/ready`).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 0.1.0 | 2026-10-12 | Initial specification (DRAFT, no autoriza implementar) | Plan de seguridad Fase 6 |
