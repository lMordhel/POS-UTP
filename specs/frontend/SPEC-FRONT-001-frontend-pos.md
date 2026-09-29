# SPEC-FRONT-001 — Frontend POS (React/Vite)

## Metadata

- ID: SPEC-FRONT-001
- Requirement: Transversal (consume ERF-01..ERF-08 vía APIs reales)
- Service: Frontend
- Status: IMPLEMENTED
- Version: 1.0.0
- Priority: Media

## Objective

Interfaz mínima del POS que consume las APIs reales de Stock (`:8002`) y
Sales (`:8001`): gestionar productos, registrar ventas y consultar ventas.
Sin datos falsos permanentes.

## Scope

* Vista Productos: listar (GET /products), crear (POST), desactivar (DELETE).
* Vista Nueva venta: buscar productos, armar líneas, confirmar (POST /sales),
  mostrar total; errores 409/404 visibles.
* Vista Ventas: listar + detalle (GET /sales[/{id}]).
* Config por env: `VITE_STOCK_URL`, `VITE_SALES_URL`.

## Out of Scope

Auth, pagos, reportes, edición de ventas (sin ERF; SDD-008).

## Actors

* Vendedor o encargado de ventas.
* Administrador de la microempresa.

## Preconditions

* Ambos servicios accesibles en las URLs configuradas.

## Functional Requirements

* FR-01: Todo dato mostrado proviene de las APIs (loading/error explícitos).
* FR-02: La venta se confirma con un solo POST; el total mostrado es el del servidor.
* FR-03: Tras vender, el stock visible se refresca desde Stock.

## Business Rules

* BR-01: No ofrecer productos inactivos en Nueva venta.
* BR-02: Cantidades enteras > 0 (validación cliente + servidor).

## API Contract

Consume (sin endpoints propios): `GET/POST /products`, `PUT/DELETE
/products/{id}`, `POST /sales`, `GET /sales[/{id}]` (ver SPECs de Stock/Sales).

## Validation Rules

* Cantidad > 0 antes de agregar línea; cuerpo de venta no vacío.

## Error Handling

* 409 → "stock insuficiente"; 404 → "producto no encontrado"; fallo de red →
  mensaje + reintento manual. Sin crashes por `&&` con conteos (ternarios).

## Acceptance Criteria

### AC-FRONT-01 — Flujo demo E2E

Given servicios en línea con un producto con stock
When se crea una venta desde la UI
Then la UI muestra el total del servidor
And el stock listado disminuye.

### AC-FRONT-02 — Sin backend

Given un servicio caído
When se abre la vista afectada
Then la UI muestra error, no datos inventados.

## Open Questions

No aplica en el alcance actual.

## Traceability

Requirement: Transversal ERF-01..ERF-08
Endpoint: Consume (no expone)
Service: Frontend
Tests: Smoke manual + `npm run build` en verde

## Technical Notes

* Skill vercel-react-best-practices, subconjunto Vite: `async-parallel`
  (Promise.all), imports directos, sin componentes dentro de componentes,
  ternarios explícitos, `setState` funcional.
* Sin React Router: navegación por pestañas con estado (alcance académico).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-09-29 | IMPLEMENTED (build verde + serve 200 + backends healthy) | Smoke: AC-FRONT-01 demo manual pendiente |
| 1.0.0 | 2026-09-29 | Approved; scope mínimo sobre APIs reales | User decision: frontend Vite |
