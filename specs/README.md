# SDD en POS-UTP — Guía de Specifications

## Qué es SDD en este proyecto

Spec-Driven Development significa que `specs/` es la **fuente de verdad** del
comportamiento funcional. El código, los schemas Pydantic y los tests existen
para cumplir y demostrar lo que la SPEC dice, no al revés.

```text
Requerimiento académico (ERF-01..ERF-08)
        ↓
Specification (specs/stock|sales/*.md)
        ↓
Acceptance Criteria (Given/When/Then)
        ↓
Technical Design (API contract)
        ↓
Tests (pytest, derivados de los ACs)
        ↓
Implementation (FastAPI: router → service → repository)
        ↓
Validation (SPEC → VALIDATED)
```

Skills aplicables (nombres reales):

* `fastapi-templates` — estructura y capas al implementar.
* `pydantic` — contratos Request/Response/Validation → schemas Create/Update/Read.
* `python-testing-patterns` — tests AAA derivados de ACs, fixtures, mocks.
* `vercel-react-best-practices` — solo en fase frontend (Vite; aplica el
  subconjunto no-Next.js: `async-parallel`, `bundle-*`, `rerender-*`).

## Cómo crear una Specification

1. Identifica el ERF (01..08) y el servicio dueño (Stock o Sales).
2. Copia la plantilla (sección "Plantilla" abajo).
3. Completa Metadata (`ID`, `Requirement`, `Service`, `Status: DRAFT`,
   `Version: 0.1.0`, `Priority`).
4. Describe Objective/Scope/Out of Scope sin inventar negocio.
5. Define Functional Requirements + Business Rules + API Contract +
   Validation Rules + Error Handling.
6. Redacta Acceptance Criteria en formato Given/When/Then, incluyendo al menos
   un escenario negativo (404/409/422).
7. Si hay contradicción con el documento académico o la arquitectura, NO la
   resuelvas: añádela a `## Open Questions`.
8. Rellena `## Traceability` y crea la fila inicial de `## Change History`.

## Estados

`DRAFT → REVIEW → APPROVED → IMPLEMENTED → VALIDATED`
(+ `REJECTED`, `CHANGED`, `DEPRECATED`).
Solo `APPROVED` autoriza a implementar. Ver
`.agents/rules/spec-driven-development.md`.

## Cómo aprobar una Specification

1. Cambiar `Status: DRAFT → REVIEW` y pedir revisión.
2. Resolver o aceptar formalmente cada `Open Questions`
   (registrar en `docs/DECISIONS.md`).
3. Cambiar a `Status: APPROVED`, subir versión a `1.0.0`,
   añadir fila en Change History.
4. Actualizar `docs/TRACEABILITY.md` (Status `Approved`).

## Cómo relacionarla con un ERF

* Un ERF → una SPEC (excepción documentada: ERF-02/ERF-08 comparten endpoint
  base pero con propósito distinto; ver Technical Notes de cada SPEC).
* Campo `Requirement: ERF-XX — nombre` + fila en `docs/TRACEABILITY.md`.

## Cómo derivar tests

Cada AC → uno o más tests: `AC-ERF05-01 → test_update_stock_valid_quantity`.
Negativos también (ej. `AC-ERF05-02 → test_update_stock_unknown_id_404`).
Sin tests huérfanos: todo test referencia una SPEC, una regla técnica o una
necesidad de infraestructura.

## Cómo modificar una Specification

* Si está `DRAFT`: editar libremente, añadir fila de historial si el cambio es
  relevante.
* Si está `APPROVED` o superior: pasar a `CHANGED`, versionar
  (compatible → patch, comportamiento → minor, incompatible → major),
  volver a `REVIEW` y actualizar trazabilidad. Nunca edición silenciosa.

## Cómo manejar decisiones pendientes

Registrar en `## Open Questions` con formato `OQ-XXX: pregunta + contexto +
opciones`. No implementar lo afectado hasta que haya decisión en
`docs/DECISIONS.md`.

## Plantilla

Ver el archivo de regla `.agents/rules/spec-driven-development.md` para el
flujo, y cualquier SPEC existente como ejemplo estructural. Secciones mínimas:

```markdown
# SPEC-XXX — Nombre
## Metadata / Objective / Scope / Out of Scope / Actors / Preconditions
## Functional Requirements / Business Rules / API Contract
## Validation Rules / Error Handling / Acceptance Criteria (Given/When/Then)
## Open Questions / Traceability / Technical Notes / Change History
```

Si una sección no aplica: escribir `No aplica en el alcance actual.`
No inventar información.

## Ejemplo pequeño

```text
### AC-ERF05-01 — Actualizar stock correctamente
Given existe un producto con stock disponible
When se solicita una actualización válida
Then el servicio debe actualizar el inventario
And debe devolver el stock actualizado

### AC-ERF05-02 — Producto inexistente
Given el producto no existe
When se solicita actualizar su stock
Then el servicio debe responder 404
And no debe modificar ningún registro
```
