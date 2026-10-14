# SPEC-FRONT-007 — Cobro con cliente y efectivo en Nueva venta

## Metadata

- ID: SPEC-FRONT-007
- Requirement: Extensión de SPEC-FRONT-006 (vista Nueva venta; sin ERF nuevo; backend SPEC-SALES-005 VALIDATED)
- Service: Frontend
- Status: DRAFT
- Version: 0.1.0
- Priority: Alta

## Objective

El cajero cobra en efectivo sin salir de Nueva venta: ingresa el cliente
(opcional) y el monto recibido (opcional), ve el error si el monto no cubre
el total sin perder su venta, y entrega un ticket que muestra cliente, monto
y vuelto calculados por el servidor. Solo frontend; el contrato backend ya
existe y es backward compatible.

## Quick path

1. Resolver OQs → aprobar esta SPEC (APPROVED 1.0.0, gate del usuario).
2. Implementar solo `frontend/src/{views/NewSaleView.jsx,api.js}` (+ `components.jsx`/`index.css` solo si hace falta).
3. Verificar: `cd frontend && npm run build` verde + demo manual por cada AC-PAG07-0x.

## Scope

* Vista Nueva venta (`views/NewSaleView.jsx`):
  1. Input cliente opcional (texto libre) + input monto recibido opcional.
  2. Envío de ambos en `salesApi.create`; error 422 por monto insuficiente visible sin perder líneas y sin mostrar ticket.
  3. Ticket con cliente + monto recibido + vuelto del servidor + botón "Nueva venta".
* `api.js`: `salesApi.create` extiende el payload con `cliente` y `monto_recibido` (solo cuando tienen valor; nunca envía `vuelto`).
* Estilos/estados de los nuevos inputs y del ticket en `components.jsx`/`index.css` solo si hacen falta (CSS puro, tono claro, `prefers-reduced-motion`).
* Conservar todo el polish de SPEC-FRONT-005 y la Fase 1 de SPEC-FRONT-006: labels, `aria-live`, foco útil, 44px, `Intl.NumberFormat`, buscador debounce 300 ms, Enter agrega primero con 1, corrección inline, validación de stock.

## Out of Scope

* Cambios de comportamiento del servidor o de contrato API (campos ya existen y son opcionales; SPEC-SALES-005 manda).
* Impuestos, descuentos, QR u otros medios de pago.
* Nuevas dependencias.
* Otros views, backend, compose.

## Actors

* Cajero (lector principal: cobra en efectivo por volumen, no puede perder la venta ante un error de monto).
* Administrador (usa la misma vista).

## Preconditions

* SPEC-FRONT-005 y SPEC-FRONT-006 implementadas y VALIDATED en `main` (buscador, líneas, stock, ticket, polish vigentes).
* SPEC-SALES-005 VALIDATED (backend acepta `cliente` + `monto_recibido`, calcula `vuelto`, expone los tres en `SaleRead`).
* Servicios Stock (`:8002`) y Sales (`:8001`) accesibles.
* Rama `feature/front-sale-cliente-efectivo` desde `main`.

## Functional Requirements

| # | Requisito |
|---|---|
| FR-01 | La vista debe ofrecer un input de cliente opcional (texto libre) antes de confirmar. Normalización en envío: `trim()`; vacío → no se envía (o `null`); máx. 120 caracteres. |
| FR-02 | La vista debe ofrecer un input de monto recibido opcional (efectivo) antes de confirmar. Vacío → venta sin pago registrado (compatibilidad SPEC-SALES-001). |
| FR-03 | `salesApi.create` debe enviar `{items, cliente?, monto_recibido?}`; nunca debe enviar `vuelto`. |
| FR-04 | Ante 422 por monto insuficiente, la vista debe mostrar el error de forma visible sin descartar líneas, cliente ni monto, y sin mostrar ticket. |
| FR-05 | El ticket tras confirmar debe mostrar cliente + monto recibido + vuelto tomados de la respuesta del servidor (no calculados en cliente), además del desglose y total ya vigentes. |
| FR-06 | El botón "Nueva venta" debe limpiar líneas, buscador, ticket y los nuevos campos (detalle en OQ-PAG07-03, recomendado: limpia todo). |
| FR-07 | Todo lo vigente de SPEC-FRONT-005/006 debe seguir funcionando sin regresión (buscador, Enter, líneas, stock, estimado, ticket base, polish). |

## Business Rules

* BR-01: BR-01/BR-02 de SPEC-FRONT-006 intactos; el total y el vuelto válidos los da el servidor al crear la venta. El cliente nunca calcula el vuelto para mostrarlo.
* BR-02: Sin SPEC aprobada no se implementa (SDD-001); este DRAFT no autoriza código.
* BR-03: Sin escritura fuera del scope autorizado; sin push/PR sin pedir.

## API Contract

Sin cambios (consume el endpoint extendido según SPEC-SALES-005, backward compatible):

* `POST /api/v1/sales` con `{items, cliente?: string | null, monto_recibido?: decimal >= 0 | null}` vía `salesApi.create`.
* Respuesta `201 {id, fecha, total, estado, cliente, monto_recibido, vuelto, items: [...]}`; errores `404/409/422` vigentes + `422` si `monto_recibido < total`.
* Estado actual: `salesApi.create(items)` solo envía `{items}` (`api.js:104`); esta SPEC autoriza extenderlo.

## Validation Rules

* Cliente: opcional; `trim()`; vacío → omitir/`null`; más de 120 caracteres → bloqueo local con mensaje (el servidor responde 422 como autoridad).
* Monto: opcional; vacío → no se envía; presente → numérico ≥ 0 con hasta 2 decimales; negativo o no numérico → bloqueo local con mensaje (detalle en OQ-PAG07-01).
* Cuerpo de venta no vacío + cantidades valgentes contra stock visible antes de confirmar (SPEC-FRONT-006 intacta).
* Monto < total → lo decide el servidor (422); la vista no intenta predecir el total final.

## Error Handling

* Mapeo base intacto (SPEC-FRONT-001/006): 409 → "stock insuficiente"; 404 → "producto no encontrado"; fallo de red → mensaje + reintento manual.
* Nuevo: 422 por monto insuficiente → mensaje visible junto al input de monto (y/o zona de confirmación) con el faltante si el servidor lo informa; conserva líneas, cliente y monto; no muestra ticket; el foco va al input de monto.
* Nuevo: 422 por cliente/monto inválido → mensaje inline junto al campo correspondiente; conserva el resto del estado.
* Errores inline con `aria-live="polite"`; foco al primer error tras confirmar fallido (polish vigente).

## Acceptance Criteria

### AC-PAG07-01 — Inputs cliente y monto opcionales

Given la vista Nueva venta con al menos una línea
When el cajero mira la zona de cobro
Then ve un input de cliente opcional (con label) y un input de monto recibido opcional (con label)
And ambos pueden quedar vacíos sin bloquear la confirmación.

### AC-PAG07-02 — Envío de cliente y monto

Given líneas válidas + cliente "Juan Pérez" + monto 100
When el cajero confirma
Then la vista llama a `salesApi.create` con `{items, cliente: "Juan Pérez", monto_recibido: 100}`
And nunca envía `vuelto` en el request.

### AC-PAG07-03 — Venta sin cliente ni monto (compatibilidad)

Given líneas válidas con cliente y monto vacíos
When el cajero confirma
Then la venta se crea como hoy (cuerpo `{items}`)
And el ticket no inventa cliente, monto ni vuelto (muestra solo lo que el servidor devuelva).

### AC-PAG07-04 — Monto insuficiente sin perder la venta

Given líneas con total T y monto M < T
When el cajero confirma y el servidor responde 422
Then la vista muestra un error visible de monto insuficiente
And conserva líneas, cliente y monto (nada se borra)
And no muestra ticket.

### AC-PAG07-05 — Ticket con cliente, monto y vuelto del servidor

Given una venta confirmada con cliente y efectivo
When aparece el ticket
Then muestra el desglose + total vigentes (SPEC-FRONT-006)
And además cliente, monto recibido y vuelto tomados de la respuesta del servidor
And con pago exacto muestra vuelto 0 (no lo oculta); sin pago registrado no muestra fila de pago (detalle en OQ-PAG07-02).

### AC-PAG07-06 — Nueva venta limpia el cobro

Given un ticket visible tras cobrar
When el cajero pulsa "Nueva venta"
Then se limpian líneas, buscador, ticket, cliente y monto, listos para el siguiente cobro.

### AC-PAG07-07 — Sin regresión del flujo vender + polish

Given servicios en línea con un producto con stock
When se vende desde la UI (con y sin cliente/monto)
Then el buscador (debounce 300 ms), Enter, corrección inline, validación de stock, estimado y ticket base funcionan como en SPEC-FRONT-006
And se conservan labels, `aria-live`, foco útil, 44px, `Intl.NumberFormat`, CSS puro con `prefers-reduced-motion`
And `npm run build` está en verde.

## Open Questions

* OQ-PAG07-01: ¿Monto con formato/validación local antes de enviar? — OPEN. Recomendación: validación local mínima no agresiva (numérico ≥ 0, hasta 2 decimales; vacío = omitir) + mensajes inline; sin formateo en vivo con separadores de miles (rompe edición y `Intl`); el servidor es la autoridad (422 si M < T). Input con `type="text" inputMode="decimal"`, `name`/`autocomplete="off"`, placeholder con ejemplo terminado en `…`. Decidir en gate PAGO-02.
* OQ-PAG07-02: ¿Ticket muestra vuelto 0 cuando no hay pago? — OPEN. Recomendación: no confundir `null` con `0` (contrato SPEC-SALES-005 FR-06): `vuelto: null` → ocultar fila de pago (venta sin pago registrado); `vuelto: 0` → mostrar "Vuelto: 0,00 (pago exacto)". Decidir en gate PAGO-02.
* OQ-PAG07-03: ¿Limpiar cliente/monto con Nueva venta? — OPEN. Recomendación: sí, limpiar todo (cliente, monto, líneas, ticket, buscador) para no arrastrar datos del comprador anterior al siguiente cobro; es lo que AC-PAG07-06 especifica salvo que el gate indique conservar el cliente. Decidir en gate PAGO-02.

## Traceability

Requirement: Extensión de SPEC-FRONT-006 (Nueva venta) + contrato SPEC-SALES-005 (cliente/efectivo)
Archivos: `frontend/src/{views/NewSaleView.jsx,api.js}` (+ `components.jsx`/`index.css` solo si hace falta)
Tests: `cd frontend && npm run build` + demo manual por AC (excepción TDD documentada: frontend sin framework de tests, precedente `odd/tasks/front-*.md`)

## Technical Notes

* Estado vigente: `salesApi.create(items)` solo envía `{items}` (`api.js:104`); `NewSaleView` con buscador debounce 300 ms, Enter agrega primero con 1, líneas con corrección inline, validación de stock, ticket con desglose + Nueva venta.
* Contrato servidor (SPEC-SALES-005): `cliente` texto libre (`strip()`, máx. 120, vacío→`null`); `monto_recibido` ≥ 0; `vuelto` calculado server-side; 422 si monto < total; `SaleRead` expone los tres campos.
* Riesgos: (1) carrera del buscador fuera de orden — ignorar respuestas viejas (heredado SPEC-FRONT-006); (2) total estimado local ≠ total servidor — no prevalidar M < T en cliente, solo validad formato; (3) inputs controlados caros por tecla — mantenerlos baratos o no controlados (Web Interface Guidelines: performance).
* A11y/polish exigido (SPEC-FRONT-005 + Web Interface Guidelines): `<label>` clicable (`htmlFor`) en ambos inputs; `aria-live="polite"` en errores y ticket; foco visible (`:focus-visible`, nunca `outline: none` sin reemplazo); botones/inputs ≥ 44px; moneda con `Intl.NumberFormat`; animaciones solo `transform`/`opacity` con `prefers-reduced-motion`; `touch-action: manipulation`; sin bloquear pegado; tramitar `cliente` largo con `break-words`/`truncate` en el ticket (contenido generado por el usuario).

## Checklist

* [ ] OQ-PAG07-01..03 resueltas por el usuario.
* [ ] Status → APPROVED 1.0.0 (autoriza PAGO-03).
* [ ] Implementación toca solo archivos del scope.
* [ ] `npm run build` verde + demo manual por cada AC.
* [ ] Status → VALIDATED + merge (PAGO-04).

## Next step

Resolver OQs en gate PAGO-02; luego APPROVED 1.0.0 e implementación (PAGO-03).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 0.1.0 | 2026-10-14 | Initial specification (DRAFT, no autoriza implementar) | PAGO-01: UI de cobro cliente + efectivo |
