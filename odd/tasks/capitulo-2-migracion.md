# Feature: capitulo-2-migracion (sección 2.5 del documento académico)

## Objective

Redactar el contenido definitivo de la sección **2.5 Oportunidades, soluciones y
planificación de migración** (TOGAF, fases E–H) del Capítulo 2 del documento
académico, sustituyendo el esqueleto por notas "Pendiente" y llenando las siete
tablas de la sección.

## Problem

El Capítulo 2 del DOCX está en esqueleto. La sección 2.5 sólo tiene encabezados
(2.5.1–2.5.8), una nota gris "Pendiente: …" por subsección, siete tablas vacías
y un marcador de figura. Sin contenido, la rúbrica **APF2** queda sin sustento
en los criterios "Oportunidades y Migración (E, F)" (4 pts) y "Gobernanza
(G, H)" (3 pts), y el criterio "Sustentación y Coherencia" del Proyecto Final
(alineación Capítulo 1 ↔ Capítulo 2 ↔ Capítulo 3) no puede evaluarse.

## Why

Asignación 1.5 — Rodríguez Vasquez, Matias Junior. La evidencia que sostiene la
sección YA EXISTE en el repositorio y no hay que inventarla: 17 ADRs con
justificación y alternativas descartadas, un plan por fases ya ejecutado y
validado (SPEC de auth, hardening, idempotencia, Alembic/auditoría, lectura por
lote, observabilidad), `infra/docker-compose.yml`, migraciones Alembic por
servicio, suites de pruebas y un E2E real entre servicios.

## Scope

- **Entrega:** `docx/AVANCE DE PROYECTO FINAL 1.docx` (no versionado en git) y
  `Diagrams/migracion-roadmap.{html,png}` (fuente y render de la Figura 2.5.1).
- Cero cambios de código en `services/`, `frontend/`, `infra/`.
- Secciones 2.5.1 a 2.5.8: texto redactado (no notas) + 7 tablas con datos
  (Tablas 2.5.1 a 2.5.7) + Figura 2.5.1 (hoja de ruta) con su pie de fuente.
- Párrafo introductorio de 2.5 reescrito para explicar la correspondencia con
  las fases E, F, G y H del ADM.
- Regeneración de los tres índices del documento (general, de tablas, de figuras)
  y verificación de paginación.

## Out of scope

- Secciones 2.1–2.4 y todo el Capítulo 3: pertenecen a los demás integrantes.
- Conclusiones y recomendaciones: solo se deja la nota de trabajo ya existente.
- `docx/respaldo/`: no se toca.

## Constraints

- **Sin dato sin respaldo.** Cada afirmación del texto debe ser rastreable a un
  ADR, una SPEC, una ruta del repositorio o el historial de commits. Si no está
  documentado, no se escribe.
- El DOCX **no está versionado** en git (`?? docx/`): el contenido del documento
  no genera commit; el artefacto versionado de esta feature es este documento.
- Idioma del texto: español académico neutro. Los nombres de tecnología,
  endpoints, tablas y comandos se escriben tal cual existen en el código.
- Formato de la casa: Arial 11, interlineado 1.5, márgenes 2.54 cm, rótulos
  `Tabla 2.5.x` / `Figura 2.5.x` con pie "Fuente: Elaboración propia.".
- No borrar las notas "Pendiente" de otras secciones: son guía para el resto
  del equipo.

## Checklist

- [x] T1 — Mapear la evidencia real del repositorio (explorador read-only +
      `docs/DECISIONS.md`, `specs/architecture/architecture.md`,
      `infra/docker-compose.yml`)
- [x] T2 — Crear este documento + espejo Engram (`odd/capitulo-2-migracion/tasks`)
- [x] T3 — Redactar 2.5.1 a 2.5.4: brechas arquitectónicas, oportunidades de
      mejora, alternativas tecnológicas evaluadas y justificación de la solución
      seleccionada
- [x] T4 — Redactar 2.5.5 a 2.5.8: plan de migración por fases, priorización y
      dependencias, riesgos y mitigación, criterios de validación
- [x] T5 — Llenar las 7 tablas de 2.5 con datos reales y consistentes con el texto
- [x] T6 — Inyectar en el DOCX vía COM (Word): sustituir notas por texto,
      llenar tablas, colocar la Figura 2.5.1
- [x] T7 — Regenerar los tres índices, verificar integridad y guardar

## Authorized scope

Rama `feature/capitulo-2-migracion`.

- Permitido: `odd/tasks/capitulo-2-migracion.md`,
  `Diagrams/migracion-roadmap.html`, `Diagrams/migracion-roadmap.png`,
  `docx/AVANCE DE PROYECTO FINAL 1.docx`.
- Prohibido: `services/`, `frontend/`, `infra/`, `specs/`, `docs/`,
  `docx/respaldo/`, y push/PR sin autorización explícita.

## Acceptance criteria

- Las 8 subsecciones de 2.5 quedan con texto redactado; no queda ninguna nota
  "Pendiente" dentro de 2.5.
- Las 7 tablas 2.5.1–2.5.7 quedan con datos: ≥ 4 brechas, ≥ 4 oportunidades,
  ≥ 3 alternativas comparadas con justificación, 4 fases de migración con
  entregables y criterios de aceptación, ≥ 4 actividades priorizadas, ≥ 4
  riesgos con mitigación, ≥ 4 criterios de validación.
- Cada tabla de migración incluye entregables y criterios de aceptación
  verificables (comando, archivo o prueba).
- Los tres índices se regeneran con páginas correctas y sin entradas fantasma.
- El DOCX abre en Word sin aviso de reparación, conserva las 21 imágenes y el
  pie con número de página.

## Checks aplicables

- Extracción de texto del DOCX (`zipfile` + `ElementTree`) para confirmar el
  contenido de 2.5 y la ausencia de "Pendiente" en la sección.
- Conteo de `word/media/*` (debe seguir en 21) y `testzip()` del zip.
- Trazabilidad manual de cada afirmación a ADR/SPEC/ruta/commit.
- Word COM: `Documents.Open` → `TablesOfContents.Update()` → `Save`, sin
  excepciones.

## Progress

- Feature completa el 2026-10-20: 7/7 tareas. El DOCX quedó en 61 páginas y
  10 342 palabras, con las tres secciones de 2.5 redactadas, sus siete tablas
  pobladas y la Figura 2.5.1 insertada.

## Verification evidence

- **Extracción del DOCX** (`zipfile` + `ElementTree`): 0 notas "Pendiente: "
  entre 2.5 y 3.0; los 8 subencabezados 2.5.1–2.5.8 con su texto; las 7 tablas
  con 7, 6, 9, 8, 6, 8 y 8 filas de datos respectivamente.
- **Índices regenerados**: general 88 entradas (2.5.1 en p. 39, 2.5.8 en
  p. 53); índice de tablas 12 entradas (Tablas 2.5.1 a 2.5.7 en pp. 40–55);
  índice de figuras 13 entradas (Figura 2.5.1 en p. 49).
- **Integridad del archivo**: `testzip()` sin errores; 22 imágenes en
  `word/media` (21 originales + la hoja de ruta); 22 dibujos en línea; acentos,
  raya (U+2014) y punto medio (U+00B7) correctos en el texto.
- **Trazabilidad de los datos**: cada tabla de 2.5 se apoya en ADRs 001–012 y
  017 y en SPECs validadas; los criterios V-01 a V-08 citan endpoints y
  comprobaciones reales (`infra/e2e_check.py`, suites de 61 y 54 pruebas,
  revisiones Alembic, rutas `/health`, `/ready` y `/metrics`).
- **Figura**: `Diagrams/migracion-roadmap.html` renderizado a PNG con Chrome
  headless a escala 2x; el eje temporal es real (28 sep – 14 oct 2026).

## Next step

- Los integrantes de Cancho, Martínez, Molina y Palacios redactan sus
  secciones (2.1–2.4) sobre la misma evidencia (ADR, SPEC, compose y suites).
- Pendiente de todo el equipo: rotular con los estilos `CaptionFigura` y
  `CaptionTabla` las imágenes y tablas del Capítulo 1 que aún no tienen rótulo,
  y ampliar conclusiones y recomendaciones con los resultados de los capítulos
  2 y 3.
- El DOCX no está versionado en git: decidir con el equipo si se versiona o si
  se sigue trabajando fuera del control de versiones.

## Rationale

- **Por qué 2.5 con evidencia ya ejecutada:** las fases E (oportunidades) y F
  (migración) del ADM no se inventan; describen la transición real de la
  solución, que en este proyecto ocurrió por fases SPEC con validación y commit.
  Documentar la transición ejecutada es más defendible ante la rúbrica que una
  planificación hipotética.
- **Por qué 7 tablas:** son los entregables que la asignación 1.5 exige
  explícitamente ("matriz de brechas, tabla comparativa de alternativas y plan
  de migración con fases, actividades, dependencias y criterios de aceptación").
- **Por qué las fases son las del repositorio:** el plan por fases de
  `D-AUTH-SCOPE` (auth+RBAC → hardening → idempotencia/saga → Alembic/auditoría
  → optimización Sales→Stock → observabilidad) es la secuencia real ejecutada y
  verificada, con fechas y SPEC asociadas.
