# SPEC-STOCK-007 — Lectura de auditoría de inventario (+ UI)

## Metadata

- ID: SPEC-STOCK-007
- Requirement: ERF-05/ERF-06 (extensión de lectura; sin ERF nuevo, sin cambiar escrituras).
- Service: Stock (endpoint) + Frontend (vista Auditoría, solo admin)
- Status: APPROVED
- Version: 1.0.0
- Priority: Media

## Objective

Ver la auditoría de Fase 4 sin entrar a la DB: movimientos con actor, motivo,
delta y antes/después, filtrables por producto y paginados.

## Scope

* `GET /api/v1/stock/movements` (solo `admin`): `producto_id?`, `skip`, `limit` (1..100); orden nuevos primero; cada fila con `codigo` + `nombre` por join de lectura.
* Repo + service delgados (reutilizan capas vigentes).
* Vista Auditoría en frontend (pestaña solo admin): filtro por producto (id o código), tabla, `Pager` reutilizado.
* Tests backend + demo manual UI.

## Out of Scope

* Escritura/borrado de movimientos (inmutables, BR-02 de SPEC-OPS-001).
* Auditoría de ventas/usuarios en tabla (decidido en OQ-AUD-01).
* Exportar CSV, gráficas, filtros por fecha/actor en esta fase.

## Actors

* Administrador (único lector; cajero → 403).

## Preconditions

* SPEC-OPS-001 implementada (tabla `inventory_movements` existe y se escribe).
* Sesión admin en frontend (SPEC-FRONT-002).

## Functional Requirements

* FR-01: El endpoint debe responder 200 con lista de `{id, producto_id, codigo, nombre, delta, cantidad_antes, cantidad_despues, motivo, actor_sub, actor_rol, clave, created_at}`.
* FR-02: Filtros según OQ-AUDV-01 (propuesta: `producto_id` + paginado).
* FR-03: Solo `admin` (401 sin token, 403 otro rol); rate limit de lectura: sin límite (OQ-HARD-02 vigente).
* FR-04: La vista debe pedir paginado (truco limit+1, `Pager`), mostrar actor/motivo/antes→después y filtrar sin recargar la página entera.
* FR-05: Snapshot al registrar: se copian `codigo`/`nombre` vigentes a la fila (columnas nuevas vía migración incremental); filas viejas quedan con NULL y la UI muestra "—".

## Business Rules

* BR-01: La auditoría es solo lectura por API (BR-02 de SPEC-OPS-001 intacto).
* BR-02: Sin `codigo`/`nombre` inventados: si el producto no existe (borrado físico nunca ocurre; borrado lógico conserva la fila), igual se muestra con lo guardado.
* BR-03: Sin SPEC aprobada no se implementa (SDD-001); esta SPEC en DRAFT no autoriza código.

## API Contract

* `GET /api/v1/stock/movements?producto_id=1&skip=0&limit=20` → `200 [{...}]` (nuevos primero). Errores: `401/403`, `422` (filtros inválidos).

## Validation Rules

* `producto_id` entero > 0 si se envía; `skip ≥ 0`; `1 ≤ limit ≤ 100`.

## Error Handling

* `401/403` según RBAC; `422` en filtros inválidos.

## Acceptance Criteria

### AC-AUDV07-01 — Lista con actor y motivo

Given ajustes con motivo por admin y por saga (`svc-sales`)
When se pide el listado
Then cada fila debe traer actor, motivo, delta y antes→después correctos.

### AC-AUDV07-02 — Filtro y paginado

Given 25 movimientos de 2 productos
When filtra por uno y pagina
Then solo los suyos, 20 por página, sin repetir.

### AC-AUDV07-03 — RBAC

Given sin token → 401; Given cajero → 403; Given admin → 200.

### AC-AUDV07-04 — UI solo admin

Given cajero → sin pestaña Auditoría; Given admin → tabla con filtro y pager funcionando (demo manual).

## Open Questions

* OQ-AUDV-01: DECIDED 2026-10-13 → filtro por producto + paginado.
* OQ-AUDV-02: DECIDED 2026-10-13 → snapshot de `codigo`/`nombre` copiados al registrar.

## Traceability

Requirement: ERF-05/ERF-06 (lectura de auditoría)
Endpoint: `GET /api/v1/stock/movements` (nuevo, lectura)
Service: Stock (endpoint) + Frontend (vista)
Tests: Pendiente (futuros: `test_movements_list_filter_paging`, `test_movements_rbac`, demo manual UI)

## Technical Notes

* Capas vigentes: endpoint delgado en `endpoints/stock.py` (o módulo `audit.py` si crece) → `product_service.list_movements` → repo existente + join; schema `MovementRead`.
* Snapshot: al registrar se copian `codigo`/`nombre` actuales (nueva columna o tabla separada... ver decisión de implementación: añadir `codigo`/`nombre` a `inventory_movements` vía migración Alembic + baseline actualizada; datos viejos quedan con NULL → UI muestra "—").
* Frontend: `stockApi.movements({producto_id, skip, limit})` + `AuditView.jsx` con `Pager`; pestaña condicional admin.
* Migración: nueva revisión Alembic (no tocar la baseline; historial lineal).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | OQ-AUDV-01/02 DECIDED (filtro/snapshot); DRAFT → APPROVED (autoriza desarrollo) | User approval: filtro, codigo/nombre |
|---|---|---|---|
| 0.1.0 | 2026-10-13 | Initial specification (DRAFT, no autoriza implementar) | Auditoría visible (idea #3) |
