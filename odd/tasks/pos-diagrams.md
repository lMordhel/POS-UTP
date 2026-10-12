# Feature: pos-diagrams (diagramas POS-UTP con diagram-design)

## Objective

Publicar en `Diagrams/` los diagramas 1 (Architecture) y 2 (Sequence saga de venta)
del POS-UTP como HTML autocontenido con la skin custom POS-UTP.

## Problem

La arquitectura solo existe como ASCII en README/specs; la saga de venta
(validar → verificar → crear → descontar, con ramas de fallo) no tiene
representación visual verificable.

## Why

Pedido explícito del usuario (arrancar con 1 y 2); valor académico y de
documentación. Style gate §0 superado con skin custom POS-UTP (2026-10-12).

## Scope

- `Diagrams/architecture.html` (tipo Architecture, `doc-inline`, mixed).
- `Diagrams/sale-saga-sequence.html` (tipo Sequence, `doc-wide`, engineer).
- Este archivo `odd/tasks/pos-diagrams.md`.

## Constraints

- Rama actual `feature/ops-alembic-audit` (no es default; no se crea rama nueva).
- Delegación no disponible → inline acotado (precedente: ops-alembic-audit).
- Commits solo de rutas propias (`Diagrams/`, este archivo); prohibido tocar
  el trabajo sucio ajeno en `services/` ni hacer push/PR sin pedir.
- Skill: type reference obligatoria antes de dibujar; budget ≤9 nodos,
  ≤12 flechas, ≤2 acentos; `self_check.py` debe pasar.
- Sin RED/WRITE TDD aplicable (sin runner determinista para HTML visual):
  excepción documentada; verificación = estructural (`self_check.py` + taste gate §9).

## Checklist

- [x] D1-T1 — `Diagrams/architecture.html` + self_check PASS + commit unidad
- [x] D1-T2 — `Diagrams/sale-saga-sequence.html` + self_check PASS + commit unidad

## Authorized scope

`Diagrams/architecture.html`, `Diagrams/sale-saga-sequence.html`,
`odd/tasks/pos-diagrams.md`. Prohibido: resto del repo, push/PR.

## Acceptance criteria

- Ambos HTML abren en navegador, usan tokens POS-UTP (paper `#f7f5f0`,
  accent `#c2410c`), pasan `scripts/self_check.py` y el taste gate §9
  (conectores ortogonales, máscaras, leyenda inferior, aria, min-width=viewBox).
- Commits de unidad con identidad registrada abajo.

## Checks aplicables

`py .agents/skills/diagram-design/scripts/self_check.py Diagrams/<file>.html`
por diagrama; relectura estructural (readback) paternal.

## Route declaration

Ruta: inline directo (delegated direct imposible: sin mecanismo de
subagentes en este runtime). Trigger evidence: 2 archivos no-triviales
habrían exigido un writer; se ejecuta inline con nota explícita, no silenciosa.

## Delivery strategy

`single-pr` (2 archivos docs, muy por debajo del budget de entrega).
Forecast: ~600 líneas autoradas acumuladas (2 HTML).

## Progress

- 2026-10-12: documento creado; skin custom activa (custom-unsaved, sin marker).

## Verification evidence

- `py .agents/skills/diagram-design/scripts/self_check.py Diagrams/architecture.html` → OK
- `py .agents/skills/diagram-design/scripts/self_check.py Diagrams/sale-saga-sequence.html` → OK
  (typo `</ Rapidão div>` detectado en revisión y corregido antes del commit)
- Taste gate §9 verificado por construcción: conectores ortogonales r=8,
  máscaras con gap 8px, leyenda inferior, `role="img"` + `aria-labelledby`,
  `min-width` = viewBox (960 / 1280), grid 4px, coral ≤1 por diagrama.
- Excepción TDD registrada en Constraints (sin runner para HTML visual).

## Commits

- `3a05bed` docs(diagrams): add POS-UTP system architecture diagram (D1-T1)
- `ed675ed` docs(diagrams): add sale saga sequence diagram (D1-T2)
- Este archivo viaja en el commit de cierre (abajo).
