# SPEC-FRONT-006 — Nueva venta profesional (Fase 1)

## Metadata

- ID: SPEC-FRONT-006
- Requirement: Extensión de SPEC-FRONT-001 (vista Nueva venta; sin ERF nuevo)
- Service: Frontend
- Status: APPROVED
- Version: 1.0.0
- Priority: Alta

## Objective

El cajero vende rápido y sin errores: busca productos por código o nombre,
corrige sus líneas antes de confirmar, no puede pedir más que el stock
disponible y recibe un ticket legible con desglose, total y forma de empezar
otra venta. Solo frontend, sin cambios de API ni dependencias nuevas.

## Quick path

1. Resolver OQs → aprobar esta SPEC (APPROVED 1.0.0, gate del usuario).
2. Implementar solo `frontend/src/{views/NewSaleView.jsx,components.jsx,index.css}`.
3. Verificar: `cd frontend && npm run build` verde + demo manual por cada AC.

## Scope

* Vista Nueva venta (`views/NewSaleView.jsx`):
  1. Buscador de productos con debounce que usa `stockApi.list(q)` + Enter agrega.
  2. Quitar línea y corregir cantidad en líneas ya agregadas.
  3. Validar cantidad contra `stock` antes de agregar y antes de confirmar.
  4. Ticket con desglose por línea + total + botón "Nueva venta".
* Estilos/estados del buscador y del ticket en `components.jsx`/`index.css`
  solo si hacen falta (CSS puro, tono claro, `prefers-reduced-motion`).
* Conservar el polish de SPEC-FRONT-005 (label, `caption`/`scope`,
  `aria-live`, foco visible, 44px, `Intl.NumberFormat`).

## Out of Scope

* Cambios de comportamiento del servidor o de contrato API
  (`stockApi.list`, `salesApi.create` intactos; `Sale` sigue sin cliente).
* Nuevas dependencias.
* Otros views, backend, compose.
* Cliente/pagos/descuentos (Fase 2).

## Actors

* Cajero (lector principal: vende por volumen, necesita buscador y corrección).
* Administrador (usa la misma vista).

## Preconditions

* SPEC-FRONT-001 implementada (flujo vender vigente).
* SPEC-FRONT-005 implementada (polish vigente sobre el mismo archivo).
* Servicios Stock (`:8002`) y Sales (`:8001`) accesibles.
* Rama `feature/front-sale-fase1` apilada sobre `feature/front-sale-polish`.

## Functional Requirements

| # | Requisito |
|---|---|
| FR-01 | El buscador debe filtrar el catálogo con `stockApi.list(q)` server-side (ilike en código/nombre) con debounce, sin recargar la página. |
| FR-02 | Enter en el buscador agrega el primer resultado (o el único) con cantidad 1. Sin campo de cantidad previo (removido por demo 2026-10-14: redundante con corrección inline). |
| FR-03 | Cada línea agregada debe poder quitarse y su cantidad debe poder corregirse antes de confirmar. |
| FR-04 | La cantidad de una línea no debe poder superar el `stock` visible del producto, ni al agregar ni al confirmar. |
| FR-05 | El ticket tras confirmar debe mostrar desglose por línea (producto, cantidad, subtotal) + total del servidor + botón "Nueva venta" que limpia el estado para otra venta. |

## Business Rules

* BR-01: BR-01/BR-02 de SPEC-FRONT-001 intactos (sin productos inactivos,
  cantidades enteras > 0); el total válido lo da el servidor al crear la venta.
* BR-02: Sin SPEC aprobada no se implementa (SDD-001); este DRAFT no autoriza código.
* BR-03: Sin escritura fuera del scope autorizado; sin push/PR sin pedir.

## API Contract

Sin cambios: consume `GET /products?q=` (vía `stockApi.list(q)`, hoy siempre
llamado con `''`) y `POST /sales` con `{items}` (vía `salesApi.create`) según
SPEC-FRONT-001. La validación de stock de esta fase es solo cliente (UX
temprana); la autoridad sigue siendo el 409 del servidor.

## Validation Rules

* Cantidad entera > 0 antes de agregar línea o corregirla.
* Cantidad ≤ `stock` visible del producto antes de agregar/corregir/confirmar.
* Cuerpo de venta no vacío antes de confirmar.

## Error Handling

* Sin cambios en mapeo base (SPEC-FRONT-001): 409 → "stock insuficiente";
  404 → "producto no encontrado"; fallo de red → mensaje + reintento manual.
* Nuevo: exceso sobre stock visible → mensaje inline junto a la línea/buscador
  antes de llamar al servidor (no sustituye al 409).
* Buscador sin resultados → estado vacío explícito ("sin resultados"), no
  catálogo inventado.

## Acceptance Criteria

### AC-PRO06-01 — Buscador con debounce

Given catálogo con 100 productos
When el cajero escribe en el buscador
Then la vista pide `stockApi.list(q)` con debounce (no una petición por tecla)
And muestra solo los coincidentes por código o nombre.

### AC-PRO06-02 — Enter agrega

Given un término con resultados visibles
When el cajero pulsa Enter en el buscador
Then se agrega el primer resultado con cantidad 1
And el foco permanece en un lugar útil para seguir vendiendo.

### AC-PRO06-03 — Quitar línea

Given una venta con al menos una línea
When el cajero quita una línea
Then la línea desaparece y el estimado se recalcula
And quitar la última línea deja la venta vacía (confirmar queda bloqueado).

### AC-PRO06-04 — Corregir cantidad

Given una línea agregada
When el cajero corrige su cantidad a otro entero > 0 dentro del stock
Then la línea y el estimado se actualizan
And un valor inválido (0, negativo, no entero) se rechaza con mensaje.

### AC-PRO06-05 — Validación de stock al agregar

Given un producto con stock S visible
When el cajero intenta agregar (o acumular) más de S
Then la vista lo bloquea con mensaje inline y no llama al servidor.

### AC-PRO06-06 — Validación de stock al confirmar

Given líneas cuyas cantidades superan el stock visible (p. ej. stock cambiado)
When el cajero pulsa confirmar
Then la vista bloquea el POST con mensaje y no muestra ticket.

### AC-PRO06-07 — Ticket con desglose y Nueva venta

Given una venta confirmada
When aparece el ticket
Then muestra desglose por línea (producto, cantidad, subtotal) + total del servidor
And el botón "Nueva venta" limpia líneas, buscador y ticket para otra venta.

### AC-PRO06-08 — Sin regresión del flujo vender

Given servicios en línea con un producto con stock
When se crea una venta desde la UI
Then la UI muestra el total del servidor y el stock listado disminuye
And `npm run build` está en verde.

## Open Questions

* OQ-PRO-01: Debounce del buscador — DECIDED: 300 ms.
* OQ-PRO-02: Qué agrega Enter con varios resultados — DECIDED:
  el primer resultado con cantidad 1 (campo previo removido en demo:
  redundante con corrección inline).
* OQ-PRO-03: Cómo se corrige la cantidad — DECIDED: input numérico
  inline por línea (misma fila, sin modal).
* OQ-PRO-04: Desglose del ticket — DECIDED: producto, cantidad,
  precio unitario, subtotal + total del servidor; sin cliente (Fase 2).

## Traceability

Requirement: Extensión de SPEC-FRONT-001 (Nueva venta)
Archivos: `frontend/src/{views/NewSaleView.jsx,components.jsx,index.css}`
Tests: `cd frontend && npm run build` + demo manual por AC (excepción TDD
documentada: frontend sin framework de tests, precedente `odd/tasks/front-*.md`)

## Technical Notes

* Estado vigente en `views/NewSaleView.jsx`: catálogo :15-32 con
  `stockApi.list('')`, `addLine` :34-55, estimado (`reduce`) :57-60,
  `confirm` :62-83 con `salesApi.create(items)`, ticket :89-91, tabla
  :97-130, líneas :131-138, botón confirmar :145-147.
* `stockApi.list(q)` ya acepta búsqueda server-side (ilike en código/nombre);
  el frontend hoy siempre pasa `''` — la Fase 1 solo empieza a pasar `q`.
* `salesApi.create` solo envía `{items}`; `Sale` no tiene cliente (Fase 2).
* Riesgo de carrera: respuestas del buscador fuera de orden con debounce +
  peticiones async — ignorar respuestas viejas (o abortar) al implementar.
* Riesgo de concurrencia: el stock visible puede quedar obsoleto entre agregar
  y confirmar — el 409 del servidor sigue siendo la autoridad (AC-PRO06-08).
* A11y/polish heredado (SPEC-FRONT-005): mantener `label`, `caption`/`scope`,
  `aria-live` en estimado/ticket, foco visible, 44px, `Intl.NumberFormat`,
  animaciones solo `transform`/`opacity` con `prefers-reduced-motion`.

## Checklist

* [x] OQ-PRO-01..04 resueltas por el usuario.
* [x] Status → APPROVED 1.0.0 (autoriza SALE-PRO-03).
* [ ] Implementación toca solo archivos del scope.
* [ ] `npm run build` verde + demo manual por cada AC.
* [ ] Status → VALIDATED + merge (SALE-PRO-04; absorbe demo pendiente SALE-POL-04).

## Next step

SALE-PRO-03: implementar la Fase 1 según esta SPEC aprobada.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 0.1.0 | 2026-10-14 | Initial specification (DRAFT, no autoriza implementar) | Nueva venta profesional Fase 1 (SALE-PRO-01) |
| 1.0.0 | 2026-10-14 | APPROVED: OQ-PRO-01 300ms, OQ-PRO-02 primer resultado, OQ-PRO-03 inline+quitar, OQ-PRO-04 completo sin cliente | Gate del usuario (SALE-PRO-02) |
| 1.0.1 | 2026-10-14 | Ajuste demo: removido campo Cantidad para Enter; Enter agrega 1 (corrección inline) | Demo usuario SALE-PRO-04 |
