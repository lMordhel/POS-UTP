# Feature: front-sale-cliente-efectivo (SPEC-FRONT-007)

## Objective

Cajero ingresa cliente (opcional) y monto recibido en efectivo; el ticket
muestra cliente + vuelto del servidor. Solo frontend; el backend ya acepta
ambos campos (SPEC-SALES-005 VALIDATED).

## Problem

La UI no envía `cliente` ni `monto_recibido`: `salesApi.create` manda solo
`{items}` y el ticket no muestra vuelto aunque el servidor lo calcula.

## Why

Decisión del usuario (2026-10-14): UI de cobro tras el backend de Fase 2.

## Scope

- SPEC `SPEC-FRONT-007-*` (DRAFT → APPROVED → VALIDATED).
- Frontend: `views/NewSaleView.jsx` (inputs cliente/monto + envío + ticket),
  `api.js` (`salesApi.create` extiende payload), estilos/`components.jsx`
  solo si hace falta.
  1. Input cliente opcional (trim, máx 120) + input monto recibido opcional.
  2. Enviar ambos en `create`; 422 insuficiente visible sin perder líneas.
  3. Ticket con cliente + monto + vuelto del servidor + botón Nueva venta.
- Docs: SPEC + este documento.

## Constraints

- Rama `feature/front-sale-cliente-efectivo` desde `main`.
- Sin cambios de contrato backend (campos ya existen, opcionales).
- Sin dependencias nuevas; CSS puro con `prefers-reduced-motion`; conservar
  polish (SPEC-005) y Fase 1 (SPEC-006): labels, aria-live, foco, 44px.
- Sin push/PR sin pedir.

## Checklist

- [x] PAGO-01 SPEC-FRONT-007 DRAFT + rama (commit 9a7cd34)
- [ ] PAGO-02 SPEC-FRONT-007 → APPROVED 1.0.0 (gate del usuario)
- [ ] PAGO-03 Implementación + `npm run build` verde
- [ ] PAGO-04 Demo manual por AC + VALIDATED + merge (+ push si se pide)

## Authorized scope

Rama `feature/front-sale-cliente-efectivo`. Archivos:
`specs/frontend/SPEC-FRONT-007*`, `odd/tasks/front-sale-cliente-efectivo.md`,
`frontend/src/{views/NewSaleView.jsx,api.js,components.jsx,index.css}`.
Prohibido: backend, cambios de API, nuevas dependencias, otros views,
compose, push/PR sin pedir.

## Acceptance criteria

- ACs `Given/When/Then` de la SPEC verificados (build + demo manual UI).
- Flujo vender sin regresiones (buscador, líneas, stock, estimado).

## Checks aplicables

`cd frontend && npm run build` + demo manual por AC. Excepción TDD
documentada: frontend sin framework de tests (precedente
`odd/tasks/front-*.md`); verificación = build + demo manual. No inventar
RED/GREEN.

## Route declaration

- PAGO-01: delegated spec-draft (preparation trigger: SPECs modelo).
- PAGO-03: delegated writer (2+ archivos no triviales).
- Verificación: writer self-report + parent spot check. RDD assess por
  work-unit commit.

## Progress

- PAGO-01 cerrada: SPEC-FRONT-007 DRAFT v0.1.0 en rama
  `feature/front-sale-cliente-efectivo` (commit 9a7cd34). 7 ACs, 3 OQs
  abiertas.

## Verification evidence

- PAGO-01: SPEC existe en DRAFT (spot check metadata); rama y commit
  verificados por parent. Solo la SPEC tocada, sin push.

## Next step

- PAGO-02: gate del usuario (OQ-PAG07-01..03) → APPROVED 1.0.0.
