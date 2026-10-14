# SPEC-FRONT-005 — Polish visual de Nueva venta

## Metadata

- ID: SPEC-FRONT-005
- Requirement: Transversal (polish de SPEC-FRONT-001, vista Nueva venta; sin ERF nuevo)
- Service: Frontend
- Status: VALIDATED
- Version: 1.0.0
- Priority: Media

## Objective

Nueva venta se ve y se entiende como un POS elegante: el cajero distingue el
catálogo, las líneas y el total a simple vista, con animaciones suaves en CSS
puro. Sin cambiar comportamiento ni contrato API.

## Quick path

1. Revisar OQs → aprobar esta SPEC (APPROVED 1.0.0, gate del usuario).
2. Implementar solo `frontend/src/{views/NewSaleView.jsx,components.jsx,utils.js,main.jsx,index.css}`.
3. Verificar: `cd frontend && npm run build` verde + demo manual por cada AC.

## Scope

* Vista Nueva venta (`views/NewSaleView.jsx`): label en input de cantidad,
  botones `Agregar` con contexto accesible, tabla con `caption`/`scope`,
  `aria-live` en estimado y ticket, foco visible, objetivos táctiles 44px.
* `money()` con `Intl.NumberFormat` (mismo formato, misma moneda).
* Nuevo `index.css` + import en `main.jsx`: estilos, foco visible, touch 44px,
  animaciones solo `transform`/`opacity` con `prefers-reduced-motion`.
* Componentes compartidos (`components.jsx`): `ErrorBanner`/`Loading` con el
  mismo polish si la vista los usa.

## Out of Scope

* Cambios de comportamiento: flujo catálogo → addLine → estimado → confirm →
  ticket queda intacto (el total válido lo da el servidor al crear la venta).
* Cambios de contrato API (`stockApi.list`, `salesApi.create` intactos).
* Nuevas dependencias (`<ViewTransition>` no existe en React 18.3.1; CSS puro,
  sin `transition:all`).
* Otros views, backend, compose.

## Actors

* Cajero (lector principal: necesita claridad y objetivos táctiles).
* Administrador (usa la misma vista).

## Preconditions

* SPEC-FRONT-001 implementada (flujo vender vigente).
* Servicios Stock (`:8002`) y Sales (`:8001`) accesibles.
* Rama `feature/front-sale-polish` desde `main`.

## Functional Requirements

| # | Requisito |
|---|---|
| FR-01 | El input de cantidad debe tener `label` visible asociado. |
| FR-02 | Cada botón `Agregar` debe tener contexto accesible (qué producto agrega). |
| FR-03 | La tabla de líneas debe tener `caption` y `scope` en encabezados. |
| FR-04 | Estimado y ticket deben anunciarse con `aria-live`. |
| FR-05 | Debe haber foco visible con teclado en controles interactivos. |
| FR-06 | Botones/controles táctiles: objetivo mínimo 44px. |
| FR-07 | `money()` debe formatear con `Intl.NumberFormat` (mismo formato/moneda). |
| FR-08 | Animaciones solo con `transform`/`opacity`, suaves; respetar `prefers-reduced-motion`. |

## Business Rules

* BR-01: Sin comportamiento nuevo: cantidades enteras > 0, venta no vacía,
  total del servidor (BR-01/BR-02 de SPEC-FRONT-001 intactos).
* BR-02: Sin SPEC aprobada no se implementa (SDD-001); este DRAFT no autoriza código.
* BR-03: Sin escritura fuera del scope autorizado; sin push/PR sin pedir.

## API Contract

Sin cambios: consume `GET /products` (vía `stockApi.list`) y `POST /sales`
(vía `salesApi.create`) según SPEC-FRONT-001.

## Validation Rules

* Sin cambios: cantidad > 0 antes de agregar línea; cuerpo de venta no vacío.

## Error Handling

* Sin cambios: 409 → "stock insuficiente"; 404 → "producto no encontrado";
  fallo de red → mensaje + reintento manual (SPEC-FRONT-001).

## Acceptance Criteria

### AC-POL05-01 — Cantidad con label

Given catálogo cargado
When el cajero ubica el input de cantidad
Then ve un `label` asociado que explica qué cantidad ingresa.

### AC-POL05-02 — Agregar con contexto

Given un producto del catálogo
When el lector de pantalla (o tooltip/instrumentación a11y) recorre su botón `Agregar`
Then anuncia a qué producto corresponde, sin ambigüedad entre filas.

### AC-POL05-03 — Tabla accesible

Given líneas agregadas
When se inspecciona la tabla
Then tiene `caption` descriptivo y encabezados con `scope`.

### AC-POL05-04 — Estimado y ticket anunciados

Given líneas en la venta
When cambia el estimado o aparece el ticket tras confirmar
Then la región tiene `aria-live` y el cambio es anunciado.

### AC-POL05-05 — Foco visible y táctil

Given navegación por teclado / pantalla táctil
When se recorre la vista o se tocan los botones
Then el foco es visible en cada control y los objetivos miden ≥ 44px.

### AC-POL05-06 — Formato moneda intacto

Given montos en catálogo, estimado y ticket
When se comparan antes/después del polish
Then mismo formato y moneda, ahora vía `Intl.NumberFormat`.

### AC-POL05-07 — Animaciones suaves y respetuosas

Given la vista en uso normal y con `prefers-reduced-motion`
When aparecen filas/ticket o cambian estados
Then las animaciones son suaves (solo `transform`/`opacity`, sin `transition:all`)
And con movimiento reducido no hay animación.

### AC-POL05-08 — Sin regresión del flujo vender

Given servicios en línea con un producto con stock
When se crea una venta desde la UI
Then la UI muestra el total del servidor y el stock listado disminuye
And `npm run build` está en verde.

## Open Questions

* OQ-POL-01: DECIDED → tono claro acorde al POS actual.
* OQ-POL-02: DECIDED → `index.css` como base mínima reutilizable (tokens, foco, touch, reduced-motion) + clases de Nueva venta.

## Traceability

Requirement: Transversal (polish de SPEC-FRONT-001, sin ERF nuevo)
Archivos: `frontend/src/{views/NewSaleView.jsx,components.jsx,utils.js,main.jsx,index.css}`
Tests: `cd frontend && npm run build` + demo manual por AC (excepción TDD
documentada: frontend sin framework de tests, precedente `odd/tasks/front-*.md`)

## Technical Notes

* Flujo vigente en `views/NewSaleView.jsx`: catálogo :15-32, `addLine` :34-55,
  estimado (`reduce`) :57-60 con render :123-128, `confirm` :62-83, ticket
  :89-91, tabla :95-114, líneas :115-122, botón confirmar :129-131; montaje en
  `App.jsx:38-39`.
* Helpers: `money`/`apiErrorMessage` en `utils.js`, `ErrorBanner`/`Loading` en
  `components.jsx`, `stockApi.list` (`api.js:78-85`), `salesApi.create`
  (`api.js:103-104`).
* Hallazgos a cubrir: sin `*.css` en `src/` (estilos inline); input sin label;
  botones `Agregar` repetidos; tabla sin `caption`/`scope`; ticket y estimado
  sin `aria-live`; sin foco visible; botones chicos; `money()` hardcodeado sin
  `Intl`; cero animación.
* CSS: propiedades animables baratas (`transform`/`opacity`); envolver en
  `@media (prefers-reduced-motion: reduce)` para desactivar.

## Checklist

* [x] OQ-POL-01/OQ-POL-02 decididas por el usuario.
* [x] Status → APPROVED 1.0.0 (autoriza SALE-POL-03).
* [x] Implementación toca solo archivos del scope.
* [x] `npm run build` verde + demo manual por cada AC (demo absorbida en Fase 1).
* [x] Status → VALIDATED + merge (SALE-POL-04).

## Next step

VALIDATED: merge a `main` con la rama apilada de Fase 1 (incluye este polish).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 0.1.0 | 2026-10-14 | Initial specification (DRAFT, no autoriza implementar) | Polish visual Nueva venta (SALE-POL-01) |
| 1.0.0 | 2026-10-14 | APPROVED: OQ-POL-01 claro acorde al POS, OQ-POL-02 base mínima reutilizable | Gate del usuario (SALE-POL-02) |
| 1.1.0 | 2026-10-14 | VALIDATED: demo manual OK absorbida en Fase 1 (SALE-PRO-04) | Demo usuario |
