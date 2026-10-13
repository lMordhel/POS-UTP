# SPEC-FRONT-003 — Gestión admin de catálogo e inventario

## Metadata

- ID: SPEC-FRONT-003
- Requirement: ERF-02/ERF-06 (extensión UI; consume endpoints existentes, sin backend nuevo).
- Service: Frontend (requiere sesión `admin`)
- Status: VALIDATED
- Version: 1.0.0
- Priority: Media

## Objective

Completar la gestión admin sin salir a Swagger: editar productos y ajustar
stock manualmente (con motivo), con la lista siempre recargada tras operar.

## Scope

* Edición inline por fila (botón Editar → formulario → `PUT /products/{id}` → reload).
* Ajuste manual por fila (delta + motivo → `PATCH stock` → reload).
* Puertas `isAdmin` existentes (cajero no ve estos controles).
* Errores mapeados: 404/409/422 con mensajes del banner.

## Out of Scope

* Crear/desactivar (ya existen en FRONT-002).
* Auditoría visible (idea #3, con endpoint propio).
* Impedir stock negativo en UI más allá de lo que el backend ya valida (409).

## Actors

* Administrador (único con estos controles).

## Preconditions

* SPEC-FRONT-002 implementada (sesión, `isAdmin`, `stockApi` con auth).

## Functional Requirements

* FR-01: Cada fila activa debe ofrecer Editar (admin) con los campos decididos en OQ-FADM-01; guardar hace `PUT` y recarga.
* FR-02: Cada fila debe ofrecer Ajustar (admin): delta entero ≠ 0 y motivo (obligatoriedad en OQ-FADM-02); confirma `PATCH` y recarga.
* FR-03: Tras cada operación exitosa la lista debe recargarse (sin estado local a mano).
* FR-04: `stockApi` suma `update(id, body)` y `adjust(id, delta, motivo)`.

## Business Rules

* BR-01: Delta 0 lo rechaza el backend (422); la UI no necesita impedirlo, solo mostrar el error.
* BR-02: Motivo admitido opcional por el backend (`None`); la UI decide si lo exige (OQ-FADM-02).
* BR-03: Sin SPEC aprobada no se implementa (SDD-001); esta SPEC en DRAFT no autoriza código.

## API Contract

Sin endpoints nuevos: `PUT /api/v1/products/{id}` (`ProductUpdate`) y
`PATCH /api/v1/products/{id}/stock` (`{delta, motivo?}`).

## Validation Rules

* Edición: mismos contratos que crear (precio > 0, textos no vacíos).
* Ajuste: delta entero (el ≠0 lo valida el backend con 422).

## Error Handling

* `404` → no encontrado (recargar); `409` → insuficiente; `422` → inválido; `403` → sin permiso (no debería pasar como admin).

## Acceptance Criteria

### AC-FADM03-01 — Editar actualiza y conserva stock

Given un producto con stock S
When el admin edita nombre/precio y guarda
Then la fila debe mostrar lo nuevo con stock S intacto.

### AC-FADM03-02 — Edición inválida

Given precio 0 o nombre vacío
When guarda
Then debe mostrar error sin llamar (cliente) o 422 del backend.

### AC-FADM03-03 — Ajuste suma y resta

Given stock S
When ajusta +5 con motivo y luego −2
Then debe quedar S+3 tras cada reload.

### AC-FADM03-04 — Ajuste sin stock

Given ajuste que deja negativo
When confirma
Then 409 con mensaje y stock intacto.

### AC-FADM03-05 — Cajero no ve gestión

Given sesión cajero
When mira Productos
Then ni Editar ni Ajustar deben renderizarse.

## Open Questions

* OQ-FADM-01: DECIDED 2026-10-12 → nombre, precio y descripción (codigo estable fuera; activo vía Desactivar).
* OQ-FADM-02: DECIDED 2026-10-12 → motivo opcional con placeholder que lo sugiera (fiel al backend).

## Traceability

Requirement: ERF-02/ERF-06 (UI de gestión)
Endpoint: Consume `PUT /products/{id}` y `PATCH stock` existentes
Service: Frontend
Tests: Pendiente (propuesta: demo manual por AC + `npm run build`, precedente FRONT-002)

## Technical Notes

* Reutilizar patrones vigentes (banner, loading, reload tras operar); `ProductRow` recibe `canEdit` + callbacks o la fila se parte en `ProductEditRow`.
* `stockApi.update` / `stockApi.adjust` en `api.js` (mismo canal con auth).
* Sin router ni tests-UI (precedente).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-12 | OQ-FADM-01/02 DECIDED (nombre+precio+desc / motivo opcional); DRAFT → APPROVED (autoriza desarrollo) | User approval: campos propuestos, opcional |
| 1.0.0 | 2026-10-12 | APPROVED → VALIDATED (build verde + demo manual por usuario: todo OK, incl. cambio de clave y UX mejorada) | Sign-off usuario |
|---|---|---|---|
| 0.1.0 | 2026-10-12 | Initial specification (DRAFT, no autoriza implementar) | Gestión admin UI (ideas 1+2) |
