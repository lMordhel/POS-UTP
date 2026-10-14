# Feature: front-sale-fase1 (SPEC-FRONT-006)

## Objective

Nueva venta profesional para el cajero: buscador de productos, líneas
corregibles, validación de stock antes de confirmar y ticket con desglose.
Solo frontend, sin cambios de API ni dependencias nuevas.

## Problem

La venta es vaga: catálogo en scroll infinito sin buscador (con 100 productos
es tedioso), una línea agregada no se puede quitar ni corregir, se puede pedir
más que el stock y recién falla al confirmar, y el ticket es una línea de
texto sin desglose ni forma de empezar otra venta.

## Why

Decisión del usuario (2026-10-14): Fase 1 primero. Usa el `q` de búsqueda que
el backend ya expone (`ilike` en código/nombre) — sin cambios backend.

## Scope

- SPEC `SPEC-FRONT-006-*` (DRAFT → APPROVED → VALIDATED).
- Frontend: `views/NewSaleView.jsx` (+ `components.jsx`/`index.css` si hace
  falta para el buscador y el ticket).
  1. Buscador con debounce (usa `stockApi.list(q)`) + Enter agrega.
  2. Quitar línea y corregir cantidad en líneas agregadas.
  3. Validar cantidad contra `stock` antes de agregar/confirmar.
  4. Ticket con desglose + total + botón "Nueva venta".
- Docs: SPEC + este documento.

## Constraints

- Rama `feature/front-sale-fase1` apilada sobre `feature/front-sale-polish`
  (el polish no está mergeado; mismo archivo).
- Sin cambios de comportamiento del servidor ni de contrato API.
- Sin dependencias nuevas; CSS puro con `prefers-reduced-motion`.
- Sin push/PR sin pedir. La demo de esta fase absorbe la demo pendiente de
  SALE-POL-04 (misma vista).

## Checklist

- [x] SALE-PRO-01 SPEC-FRONT-006 DRAFT + rama `feature/front-sale-fase1` (commit 2d6b596)
- [ ] SALE-PRO-02 SPEC-FRONT-006 → APPROVED 1.0.0 (gate del usuario)
- [ ] SALE-PRO-03 Implementación Fase 1 + `npm run build` verde
- [ ] SALE-PRO-04 Demo manual por AC + VALIDATED + merge (+ push si se pide)

## Authorized scope

Rama `feature/front-sale-fase1`. Archivos: `specs/frontend/SPEC-FRONT-006*`,
`odd/tasks/front-sale-fase1.md`,
`frontend/src/{views/NewSaleView.jsx,components.jsx,index.css}`.
Prohibido: backend, cambios de API, nuevas dependencias, otros views,
compose, cliente/pagos (Fase 2), push/PR sin pedir.

## Acceptance criteria

- ACs `Given/When/Then` de la SPEC verificados (build + demo manual UI).
- Flujo vender sin regresiones (estimado, confirmación, ticket).

## Checks aplicables

`cd frontend && npm run build` + demo manual por AC. Excepción TDD
documentada: frontend sin framework de tests (precedente
`odd/tasks/front-*.md`); verificación = build + demo manual. No inventar
RED/GREEN.

## Route declaration

- SALE-PRO-01: delegated spec-draft (preparation trigger: SPECs modelo).
- SALE-PRO-03: delegated writer (2+ archivos no triviales).
- Verificación: writer self-report (`npm run build` observado) + parent spot
  check. RDD assess por work-unit commit como en el feature anterior.

## Progress

- SALE-PRO-01 cerrada: SPEC-FRONT-006 DRAFT v0.1.0 en rama
  `feature/front-sale-fase1` apilada sobre polish (commit 2d6b596). 8 ACs,
  4 OQs abiertas.

## Verification evidence

- SALE-PRO-01: SPEC existe en DRAFT (spot check metadata); rama y commit
  verificados por parent. Solo la SPEC tocada, sin push.

## Next step

- SALE-PRO-02: gate del usuario (OQ-PRO-01..04) → APPROVED 1.0.0.
