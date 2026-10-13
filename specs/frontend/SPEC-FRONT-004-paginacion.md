# SPEC-FRONT-004 — Paginación en listados

## Metadata

- ID: SPEC-FRONT-004
- Requirement: UX en listados (sin ERF nuevo; usa paginación backend existente `skip/limit`).
- Service: Frontend (Productos y Ventas; Usuarios fuera salvo decisión)
- Status: APPROVED
- Version: 1.0.0
- Priority: Media

## Objective

Que Productos y Ventas naveguen por páginas en vez de cargar todo, con
Anterior/Siguiente, sin duplicados ni saltos, y búsqueda que reinicia a la
primera página.

## Scope

* Estado de página por vista + botones Anterior/Siguiente (+ deshabilitados en bordes).
* Técnica sin backend nuevo: pedir `limit+1` para saber si hay siguiente (sin total).
* Tamaño de página según OQ-PAG-01; vistas según OQ-PAG-02.
* La búsqueda (`q`) reinicia a página 0; el detalle de venta no pagina.

## Out of Scope

* Contador total de páginas (requeriría total del backend; el truco limit+1 lo evita).
* Tamaño de página configurable por el usuario en esta fase (ver OQ).
* Ordenamientos/filtros nuevos.

## Actors

* Cajero y admin (ambos navegan igual; sin cambios de permisos).

## Preconditions

* Backend con `skip/limit` (existe en productos, ventas y usuarios).

## Functional Requirements

* FR-01: Cada vista paginada debe pedir `skip = page*size`, `limit = size+1`; si vuelven `size+1`, mostrar `size` y habilitar Siguiente.
* FR-02: Anterior deshabilitado en página 0; Siguiente deshabilitado sin fila extra.
* FR-03: Cambiar la búsqueda debe volver a página 0.
* FR-04: Tamaño y vistas según OQ-PAG-01/02.

## Business Rules

* BR-01: Sin duplicados ni huecos al navegar (el orden backend por id lo garantiza).
* BR-02: Sin SPEC aprobada no se implementa (SDD-001); esta SPEC en DRAFT no autoriza código.

## API Contract

Sin endpoints nuevos: `GET /products?skip&limit&q...` y `GET /sales?skip&limit` existentes.

## Validation Rules

* `page` entero ≥ 0 en estado; nunca pedir `skip` negativo.

## Error Handling

* Errores de página iguales a los de lista (banner existente).

## Acceptance Criteria

### AC-PAG04-01 — Navega sin perder ni repetir

Given 25 productos
When avanza y retrocede páginas
Then debe ver los 25 exactamente una vez entre todas.

### AC-PAG04-02 — Bordes

Given primera página → Anterior deshabilitado; Given última → Siguiente deshabilitado.

### AC-PAG04-03 — Búsqueda reinicia

Given en página 2
When escribe en Buscar
Then vuelve a página 0 con resultados filtrados.

## Open Questions

* OQ-PAG-01: DECIDED 2026-10-13 → fijo 20 (igual al default backend).
* OQ-PAG-02: DECIDED 2026-10-13 → las tres vistas (incluida Usuarios).

## Traceability

Requirement: UX listados (sin ERF nuevo)
Endpoint: Consume paginación existente
Service: Frontend
Tests: Pendiente (propuesta: demo manual por AC + `npm run build`, precedente)

## Technical Notes

* `api.js`: `list` acepta `{skip, limit}` (default limit 21 interno para el truco +1); las vistas cortan a `size`.
* Componente `Pager` mínimo reutilizable en `components.jsx` (Anterior/Siguiente + "Página N").
* Sin router ni tests-UI (precedente).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | OQ-PAG-01/02 DECIDED (fijo 20 / tres vistas); DRAFT → APPROVED (autoriza desarrollo) | User approval: fijo, usuarios también |
|---|---|---|---|
| 0.1.0 | 2026-10-13 | Initial specification (DRAFT, no autoriza implementar) | Paginación UI |
