# SPEC-FRONT-008 — Correcciones de usabilidad del punto de venta

## Metadata

- ID: SPEC-FRONT-008
- Requirement: ERF-01, ERF-04, ERF-07 (transversal)
- Service: Frontend
- Status: VALIDATED
- Version: 1.0.0
- Priority: Media

## Objective

Corregir cinco defectos de usabilidad detectados al verificar la aplicación en
ejecución (Vite 6.4.3 + FastAPI + PostgreSQL en contenedores), sin ampliar el
alcance funcional ni las dependencias.

## Problem

La verificación en ejecución del 2026-10-21 encontró cinco comportamientos que
perjudican al cajero o incumplen la expectativa de presentación del curso:

1. El listado de ventas se devolvía en orden **ascendente**: la venta más
   reciente quedaba en la última página, invisible para quien opera el punto
   de venta.
2. Las fechas se mostraban en **formato US** (`9/28/2026, 9:15:07 PM`) porque
   `toLocaleString()` se llamaba sin locale.
3. El detalle de una venta se renderizaba **debajo de una tabla de 20 filas**,
   sin separación visual ni foco: el clic en «Ver» parecía no hacer nada.
4. El botón «Agregar» seguía **activo con stock 0** y el aviso de stock
   insuficiente aparecía en la cabecera, lejos de la fila.
5. La pestaña activa se renderizaba **deshabilitada**, lo que le quitaba el foco
   visible al teclado y no marcaba la sección en curso.

## Scope

* Orden del listado de ventas (backend `GET /api/v1/sales` + frontend).
* Formato de fecha es-PE en 24 horas.
* Panel de detalle de venta visible, focalizado y con cierre.
* Botón «Agregar» deshabilitado cuando no hay existencias.
* Pestañas de navegación con `aria-current` y estado activo visible.

## Out of Scope

* Rediseño visual completo de las vistas (Productos, Usuarios, Auditoría).
* Pruebas de interfaz automatizadas: sin runner de tests-UI (ADR-014, ADR-015,
  ADR-016); la verificación es la ejecución en navegador.
* Nuevos endpoints, filtros o functionalities (SDD-008).

## Actors

* Vendedor o encargado de ventas (`cajero`).
* Administrador de la microempresa (`admin`).

## Functional Requirements

* FR-01: El listado de ventas muestra la más reciente primero y la paginación
  recorta desde esa posición.
* FR-02: Las fechas se presentan en formato `dd/mm/aaaa, hh:mm:ss` (es-PE, 24 h).
* FR-03: El detalle de la venta se muestra **encima** del listado, recibe el
  foco al abrirse y ofrece una acción para cerrarlo.
* FR-04: Un producto sin existencias no se puede agregar desde el catálogo: el
  botón queda deshabilitado, rotulado «Sin stock» y explica el motivo.
* FR-05: La pestaña activa se marca con `aria-current="page"` y con estilo
  propio, y permanece habilitada.

## Acceptance Criteria

### AC-FRONT08-01 — Orden del listado de ventas

Given hay ventas registradas
When el cajero abre la pestaña Ventas
Then la primera fila debe ser la venta más reciente.

### AC-FRONT08-02 — Formato de fecha

Given una venta con fecha registrada
When se muestra en el listado
Then la fecha debe aparecer como `dd/mm/aaaa, hh:mm:ss` en 24 horas.

### AC-FRONT08-03 — Detalle de venta visible

Given el cajero pulsa «Ver» sobre una venta
Then debe aparecer un panel con el detalle **por encima** de la tabla, con el
foco en él, con `role="region"` y con una acción «Cerrar».

### AC-FRONT08-04 — Producto sin existencias

Given un producto con stock 0 en el catálogo
When el cajero mira la fila
Then el botón debe decir «Sin stock», estar deshabilitado y explicar el motivo;
no debe poder agregarse a la venta.

### AC-FRONT08-05 — Pestaña activa

Given el cajero navega entre secciones
Then la sección en curso debe tener `aria-current="page"` y estar resaltada, y
ninguna pestaña debe quedar deshabilitada.

## Verification

Los AC se verifican por **ejecución en navegador** (ego-browser sobre la
aplicación en marcha: Vite en `:5173`, Sales en `:8001`, Stock en `:8002`),
recorriendo las cinco vistas y capturando el estado del DOM. No hay runner de
tests-UI en el proyecto (ADR-014, ADR-015, ADR-016: «Sin registro/MFA/tests-UI
en esta fase»); es la misma excepción documentada en SPEC-FRONT-003.

El contrato del endpoint de ventas sí tiene cobertura automatizada: ver
SPEC-SALES-003 1.1.0 (AC-ERF07-04) y sus tests en `test_sales.py`.

## Traceability

Requirement: ERF-01, ERF-04, ERF-07 (transversal)
Endpoint: `GET /api/v1/sales` (orden), frontend sin endpoint propio
Service: Sales (orden) + Frontend (presentación)
Tests: `services/sales-service/tests/test_integration/test_sales.py`
(AC-ERF07-04); verificación manual en navegador para AC-FRONT08-01..05.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-21 | IMPLEMENTED → VALIDATED | AC-FRONT08-01..05 verificados en ejecución (sin errores de consola) |
| 1.0.0 | 2026-10-21 | APPROVED 1.0.0 | Decisión explícita del usuario (2026-10-21): «arregla los 5 hallazgos» tras el análisis en ejecución |
| 0.1.0 | 2026-10-21 | Initial specification (DRAFT) | Hallazgos de la verificación en ejecución del frontend |
