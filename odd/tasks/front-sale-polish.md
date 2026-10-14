# Feature: front-sale-polish (SPEC-FRONT-005)

## Objective

Polish visual de Nueva venta: elegante, claro y entendible para el cajero,
con animaciones suaves en CSS puro. Sin cambiar comportamiento ni agregar
dependencias.

## Problem

Nueva venta funciona pero se ve cruda: input de cantidad sin label, botones
`Agregar` repetidos sin contexto accesible, tabla sin caption/scope, ticket y
estimado sin `aria-live`, sin foco visible, botones chicos para táctil,
`money()` hardcodeado sin `Intl`, y cero animación.

## Why

Criterio del usuario: elegante acorde al POS, animaciones suaves, visual
entendible y claro. Skills instaladas: `web-design-guidelines` (revisión UI)
+ `vercel-react-view-transitions` (guía; React 18 la limita a CSS puro).

## Scope

- SPEC `SPEC-FRONT-005-polish-nueva-venta` (DRAFT → APPROVED → VALIDATED).
- Frontend: `views/NewSaleView.jsx`, `components.jsx`, nuevo `index.css`
  + import en `main.jsx` (estilos, foco visible, touch 44px, `aria-live`,
  animaciones transform/opacity con `prefers-reduced-motion`).
- Docs: SPEC + ADR si aplica + este documento.

## Constraints

- Rama `feature/front-sale-polish` desde `main`.
- Sin cambios de comportamiento ni de contrato API (el total válido lo da el
  servidor al crear la venta).
- Sin dependencias nuevas (`<ViewTransition>` no existe en React 18.3.1;
  CSS puro, sin `transition:all`).
- Sin escritura fuera del scope autorizado; sin push/PR sin pedir.

## Checklist

- [x] SALE-POL-01 SPEC-FRONT-005 DRAFT + rama `feature/front-sale-polish` (commit 59613bd)
- [x] SALE-POL-02 SPEC-FRONT-005 → APPROVED 1.0.0 (gate del usuario, OQs)
- [ ] SALE-POL-03 Implementación polish + `npm run build` verde
- [ ] SALE-POL-04 Demo manual por AC + VALIDATED + merge (+ push si se pide)

## Authorized scope

Rama `feature/front-sale-polish`. Archivos:
`specs/frontend/SPEC-FRONT-005*`, `odd/tasks/front-sale-polish.md`,
`frontend/src/{views/NewSaleView.jsx,components.jsx,utils.js,main.jsx,index.css}`.
Prohibido: backend, cambios de API, nuevas dependencias, otros views,
compose, push/PR sin pedir.

## Acceptance criteria

- ACs `Given/When/Then` de la SPEC verificados (build + demo manual UI).
- `npm run build` verde y sin regresiones en el flujo vender.

## Checks aplicables

`cd frontend && npm run build` + demo manual por AC. Excepción TDD
documentada: frontend sin framework de tests (precedente `odd/tasks/front-*.md`);
verificación vigente = build + demo manual por AC. No inventar RED/GREEN.

## Route declaration

- SALE-POL-01: delegated spec-draft (preparation trigger: lectura de SPECs
  modelo + SKILL de docs).
- SALE-POL-03: delegated writer (2+ archivos no triviales).
- Verificación: writer self-report (`npm run build` observado) + parent spot check.

## Progress

- SALE-POL-01 cerrada: SPEC DRAFT v0.1.0 en rama `feature/front-sale-polish`
  (commit 59613bd).
- SALE-POL-02 cerrada: OQ-POL-01 claro acorde al POS, OQ-POL-02 base mínima
  reutilizable. SPEC APPROVED 1.0.0.

## Verification evidence

- SALE-POL-01: SPEC existe y está en DRAFT (spot check líneas 1-50);
  `git status` confirma rama y solo el `.md` nuevo. Sin código tocado.
- SALE-POL-02: SPEC en APPROVED 1.0.0, OQs DECIDED (spot check OQs + history).

## Next step

- SALE-POL-03: implementar el polish (writer delegado).
