# Spec-Driven Development — Reglas del proyecto POS-UTP

Fuente de verdad: `specs/`. Ninguna funcionalidad nueva importante se implementa
desde una petición informal. Flujo obligatorio:

```text
1. Identificar requerimiento (ERF-01..ERF-08 o decisión aprobada)
2. Crear/modificar Specification en specs/ (DRAFT → REVIEW → APPROVED)
3. Definir criterios de aceptación (Given/When/Then, positivos y negativos)
4. Revisar diseño técnico (API contract + notas)
5. Crear/actualizar tests derivados de los ACs
6. Implementar (solo si SPEC está APPROVED)
7. Ejecutar tests
8. Validar implementación contra la SPEC (→ VALIDATED)
```

## Ciclo de vida

```text
DRAFT → REVIEW → APPROVED → IMPLEMENTED → VALIDATED
```

Estados terminales / especiales: `REJECTED`, `CHANGED`, `DEPRECATED`.

* `DRAFT`: borrador, **no autoriza a implementar**.
* `REVIEW`: en revisión por el equipo/docente.
* `APPROVED`: autoriza implementación. Versionar como `1.0.0`.
* `IMPLEMENTED`: existe código asociado (sin validar aún).
* `VALIDATED`: tests + validación confirman que el código cumple la SPEC.
* `CHANGED`: una SPEC aprobada fue modificada (exige nueva revisión y versión minor/major).
* Versiones: `0.x.y` = no aprobada; cambio compatible `→ x.y+1 / 0.x+1`;
  cambio de comportamiento `→ minor`; cambio incompatible `→ major`.

## Reglas

### SDD-001

No implementar una funcionalidad nueva importante sin Specification en estado APPROVED.

### SDD-002

No modificar silenciosamente una Specification aprobada. Todo cambio registra una
fila en `## Change History` y, si es relevante, en `docs/DECISIONS.md`.

### SDD-003

Toda modificación funcional debe actualizar `docs/TRACEABILITY.md`
(ERF → SPEC → AC → Endpoint → Service → Test).

### SDD-004

Los tests deben validar los criterios de aceptación. Cada AC importante tiene al
menos un test asociado (`AC-XXX → test_...`). Los escenarios negativos también
tienen tests. Base: skill `python-testing-patterns` (AAA, fixtures, parametrize,
mocks para dependencias externas, `pytest.raises(match=...)`).

### SDD-005

El código no debe definir unilateralmente el comportamiento del sistema.
El comportamiento lo define la SPEC; Pydantic implementa el contrato
(skill `pydantic`: separar Create/Update/Read, constraints declarativos antes
que validadores custom); FastAPI lo expone
(skill `fastapi-templates`: router delgado → service → repository).

### SDD-006

Ante una contradicción entre código y Specification, detenerse y reportar el
conflicto. No "arreglar" el código ni la SPEC silenciosamente.

### SDD-007

Ante una contradicción entre Specification y documento académico
(`AVANCE DE PROYECTO FINAL 1.docx`, ERF-01..ERF-08), detenerse y solicitar
decisión. Registrarla en `## Open Questions` y en `docs/DECISIONS.md`.

### SDD-008

No introducir funcionalidades fuera del alcance para "mejorar" el sistema
(auth JWT, pagos, facturación electrónica, clientes, descuentos, mensajería,
cachés, orquestadores). Toda adición exige ERF o decisión aprobada.

### SDD-009

No modificar requisitos académicos únicamente por conveniencia técnica.
Si la técnica lo exige, elevarlo a decisión pendiente.

### SDD-010

Mantener trazabilidad completa: `ERF → SPEC → AC → API → CODE → TEST`.
