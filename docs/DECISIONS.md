# Decisiones arquitectónicas — POS-UTP

> Estados: `PROPOSED` = propuesta pendiente de aprobación; `APPROVED` = aprobada.
> Ninguna decisión pasa a `APPROVED` sin autorización explícita. Los cambios
> relevantes se registran aquí además del `Change History` de cada SPEC.

## ADR-001 — API Gateway: NO implementar inicialmente

- Status: PROPOSED
- Decisión: No implementar API Gateway en Fase 1. El frontend consume ambas
  APIs directamente.
- Motivo: alcance académico con solo dos microservicios; el gateway añadiría
  latencia, punto único de fallo y código sin ERF que lo respalde (YAGNI).
- Afecta a: SPEC-ARCH-001.

## ADR-002 — Propiedad de datos

- Status: APPROVED (2026-09-29, decisión de usuario)
- Decisión: Stock → productos e inventario; Sales → ventas y detalles de venta.
  Sin FK físicas ni queries cross-DB. `producto_id` en Ventas es referencia
  lógica verificada por HTTP.
- Motivo: "cada servicio propietario de sus datos" (microservicios reales, no
  monolito disfrazado).
- Conflicto resuelto: la matriz del documento asignaba ERF-02 al "Servicio de
  Ventas"; se confirma dueño = Stock (OQ-ERF02-01 DECIDED).

## ADR-003 — Comunicación Ventas → Stock por HTTP

- Status: PROPOSED
- Decisión: Cliente tipado `clients/stock_client.py` en Sales (httpx, timeout,
  errores tipados). Reintento solo en fallos transitorios; nunca en
  404/409/422. Fallo no controlado de Stock → 502 controlado.
- Motivo: contrato explícito y testeable; sin broker (fuera de alcance).

## ADR-004 — Base de datos PostgreSQL: dos bases lógicas

- Status: PROPOSED
- Decisión: Una instancia PostgreSQL con `ventas_db` y `stock_db`;
  conexiones, migraciones y credenciales separadas por servicio.
- Motivo: preserva propiedad de datos con costo académico mínimo. Dos
  instancias físicas quedan como opción futura de Compose.

## ADR-005 — Stock en tabla separada (no columna de Producto)

- Status: APPROVED (2026-09-29, al aprobar SPEC-STOCK-004 que crea
  `products` + `inventories` atómicamente)
- Decisión: Tabla `inventories` (`producto_id` único FK → `products.id`,
  `cantidad >= 0`, `updated_at`). Sin columna `stock` en `products`; el stock
  en lecturas es agregado de solo lectura.
- Motivo: el dominio académico lista Producto, Inventario y Stock como clases
  separadas; evita doble fuente de verdad y bloqueo de catálogo por ventas.
- Alternativa descartada: `products.stock INT` (más simple, contradice el
  dominio).

## Decisiones diferidas / conflictos con el documento (no implementar)

- D-ERF01-IMPUESTOS: CA-02 exige impuestos/vuelto en efectivo. DECIDED
  2026-09-29: excluidos; `total` = Σ subtotales. Ver OQ-ERF01-01.
- D-ERF01-QR: CR-001 (cobro QR) figura aprobada en el documento pero viola
  Regla 1/2. Propuesta: registrar como diferida/rechazada. Ver OQ-ERF01-02.
  Estado: pendiente.
- D-ERF05-SEMANTICA: DECIDED 2026-09-29 → PATCH con delta (+/-) y `motivo`.
  Ver OQ-ERF05-01. El contrato se fijará al aprobar SPEC-STOCK-003.
- D-ERF02-DUEÑO: DECIDED 2026-09-29 → dueño = Stock. Ver OQ-ERF02-01.
- D-ERF08-SOLAPE: ERF-02 y ERF-08 comparten endpoint base con distinto
  propósito. Ver OQ-ERF08-01. Estado: pendiente.

## ADR-006 — Usuarios en ventas_db, gestionados por Sales

- Status: APPROVED (2026-10-12, con SPEC-AUTH-001 1.0.0)
- Decisión: Los usuarios viven en `ventas_db` y los gestiona Sales (sin tercer microservicio en este alcance). Stock valida el JWT con el mismo secreto y aplica RBAC; no almacena usuarios ni consulta a Sales para autenticar.
- Motivo: alcance mínimo académico con 2 servicios; un servicio de identidad separado no tiene ERF ni escala que lo justifique (YAGNI).
- Bootstrap DECIDED 2026-10-12 (OQ-AUTH-04): primer `admin` desde `ADMIN_USERNAME`/`ADMIN_PASSWORD`, solo si la tabla `users` está vacía.
- Afecta a: SPEC-AUTH-001.

## ADR-007 — Tokens JWT de corta duración + hash de contraseñas

- Status: APPROVED (2026-10-12, con SPEC-AUTH-001 1.0.0; hash nunca-en-texto-plano como principio)
- Decisión: Access JWT propuesto de 15 min (HS256, secreto por entorno, fail-fast si es valor de ejemplo en producción). Contraseñas con bcrypt (cost 12 propuesto), nunca en texto plano ni en logs.
- Renovación DECIDED 2026-10-12 (OQ-AUTH-01): refresh rotativo con detección de reúso — cada uso emite un par nuevo e invalida el anterior; reutilizar un refresh rotado → 401 + revocación de la familia.
- Afecta a: SPEC-AUTH-001.

## ADR-008 — RBAC admin/cajero con enforcement en backend

- Status: APPROVED (2026-10-12, con SPEC-AUTH-001 1.0.0; la matriz rige desde la aprobación)
- Decisión: Roles `admin` (productos, usuarios/roles, todo en lectura, ajustes de stock) y `cajero` (vender, consultar productos/stock/ventas; sin gestión de usuarios, productos ni ajustes manuales). El backend verifica el rol en cada endpoint; ocultar botones en el frontend es solo UX.
- Alcance de consulta DECIDED 2026-10-12 (OQ-AUTH-03): el cajero consulta todas las ventas en lectura; las ventas son inmutables (no existen endpoints de modificación/eliminación; de crearse serían solo `admin`).
- Identidad de servicio DECIDED 2026-10-12 (addendum de implementación, gap detectado por E2E): las llamadas internas Sales→Stock usan credencial de servicio (`create_service_token`: secreto compartido, rol `admin`, `type=service`, fresca por llamada sin estado). El rol del usuario final no se propaga a Stock; la atribución viaja en `motivo=venta:{id}`. La matriz RBAC rige llamadas directas de usuarios.
- Afecta a: SPEC-AUTH-001.

## ADR-009 — Hardening HTTP (CORS, rate limiting, config segura)

- Status: APPROVED (2026-10-12, con SPEC-AUTH-002 1.0.0)
- Decisión: CORS por env (default dev `http://localhost:5173`, fin de `*`); rate limit por IP en auth+escrituras con `slowapi` en memoria (login 5/min propuesto; lecturas sin límite); cabeceras `nosniff`/`DENY`/`no-referrer` + `Server` genérico; fail-fast en prod ante secretos/CORS de ejemplo; `/docs` desactivado en prod.
- Pendientes (OQ-HARD-01/02): confirmar cierre de docs en prod y alcance del rate limit.
- Afecta a: SPEC-AUTH-002.

## ADR-010 — Idempotencia extremo a extremo en la saga de venta

- Status: APPROVED (2026-10-12, con SPEC-SALES-004 1.0.0)
- Decisión: Doble nivel de claves opacas: `Idempotency-Key` por venta en `POST /sales` (tabla `idempotency_keys` + hash de cuerpo + guarda concurrente por restricción única) y clave por línea `{K}:{producto_id}` hacia Stock (tabla `stock_adjustments`; replay no re-aplica). Compensación con 3 intentos + log estructurado ante fallo final; timeout ambiguo resoluble por reintento con la misma clave.
- Fundamento medido: `adjust_stock` es read-check-write sin lock y la compensación actual traga excepciones (`except Exception: pass` en `sale_service.py`).
- Pendientes (OQ-SAGA-01/02/03): código del replay, expiración de claves, misma-clave-distinto-cuerpo.
- Afecta a: SPEC-SALES-004.

## ADR-011 — Migraciones Alembic + auditoría de inventario

- Status: APPROVED (2026-10-12, con SPEC-OPS-001 1.0.0)
- Decisión: Alembic por servicio con baseline autogenerada (upgrade + downgrade); `init_db` adopta-o-migra (stamp head si hay tablas sin versión, upgrade si no); bootstrap admin preservado. Auditoría: tabla `inventory_movements` por cada ajuste aplicado (actor desde claims, motivo, antes/después, clave nullable; replays no auditan); eventos de seguridad en logs estructurados (sin tablas extra).
- Fundamento: `create_all` no versiona y no puede evolucionar el esquema con datos; los ajustes manuales de admin hoy no dejan traza con actor.
- Pendientes (OQ-AUD-01/02/03): alcance de auditoría, upgrade-head en todo vs solo prod, baseline+seed mínimo.
- Afecta a: SPEC-OPS-001.

## ADR-012 — Lectura por lote para la saga (sin cambiar semántica)

- Status: APPROVED (2026-10-12, con SPEC-STOCK-006 1.0.0)
- Decisión: `POST /api/v1/products/batch` aditivo (producto + stock, tope 100, RBAC lector); Sales lo usa como único camino de lectura (3N → N+1 llamadas); ajustes por línea intactos; sin cachés, threads ni batch de escritura en esta fase.
- Fundamento medido: la saga hace N×(`get_product` + `get_stock`) secuenciales + N ajustes.
- Pendientes (OQ-BATCH-01/02/03): encontrados-vs-404, camino único, tope.
- Afecta a: SPEC-STOCK-006.

## ADR-013 — Observabilidad mínima sin dependencias nuevas

- Status: APPROVED (2026-10-12, con SPEC-OPS-002 1.0.0)
- Decisión: Access log JSON con `X-Request-ID` (middleware propio); `/metrics` hand-rolled en formato Prometheus (contadores + latencias + `app_info`, en memoria/1 réplica); `/ready` solo DB propia (200/503); `/health` intacto. Sin OTel, sin Prometheus/Grafana, sin propagación profunda del request id en esta fase.
- Pendientes (OQ-OBS-01/02/03): hand-rolled vs librería, alcance de ready, unificación de logs.
- Afecta a: SPEC-OPS-002.

## ADR-014 — Frontend con autenticación y roles

- Status: APPROVED (2026-10-12, con SPEC-FRONT-002 1.0.0)
- Decisión: Login + sesión con refresh ante 401, puertas de UI por rol (matriz ERF-10), vista Usuarios para admin, errores mapeados por código; `api.js` como único canal HTTP. Sin registro/MFA/tests-UI en esta fase.
- Pendientes (OQ-FRONT-01/02/03): almacenamiento de tokens, alcance de vista Usuarios, estrategia de verificación.
- Afecta a: SPEC-FRONT-002.

## ADR-015 — Gestión admin en UI (editar + ajuste con motivo)

- Status: APPROVED (2026-10-12, con SPEC-FRONT-003 1.0.0)
- Decisión: Edición inline y ajuste manual con motivo solo admin, vía endpoints existentes; reload tras operar; sin auditoría visible ni tests-UI en esta fase.
- Pendientes (OQ-FADM-01/02): campos editables, obligatoriedad del motivo en UI.
- Afecta a: SPEC-FRONT-003.

## ADR-016 — Paginación en UI con truco limit+1

- Status: APPROVED (2026-10-13, con SPEC-FRONT-004 1.0.0)
- Decisión: Sin backend nuevo: pedir `limit+1` para detectar siguiente; tamaño y vistas por OQ; búsqueda reinicia a página 0.
- Pendientes (OQ-PAG-01/02): tamaño fijo o selector; vistas incluidas.
- Afecta a: SPEC-FRONT-004.

## ADR-017 — Auditoría visible (endpoint + UI solo admin)

- Status: PROPOSED (la aprobación de SPEC-STOCK-007 lo aprueba)
- Decisión: `GET /api/v1/stock/movements` (solo admin, con codigo/nombre por snapshot, paginado) + vista Auditoría con filtro y `Pager`; migraciones incrementales (no se reescribe la baseline).
- Pendientes (OQ-AUDV-01/02): filtros vs lista plana; snapshot vs solo IDs.
- Afecta a: SPEC-STOCK-007.

## D-AUTH-SCOPE — Ampliación de alcance: seguridad backend

- Status: DECIDED (2026-10-12, decisión de usuario — Opción 1)
- Decisión: Auth/RBAC entra al alcance aunque figuraba fuera de alcance (architecture.md, SDD-008). Excepción documentada: la decisión aprobada del usuario cubre el requisito de SDD-008 ("toda adición exige ERF o decisión aprobada").
- ERF-09 (autenticación) y ERF-10 (autorización por roles) DECIDED 2026-10-12 para el documento académico (OQ-AUTH-02); la edición del `.docx` queda a cargo del usuario (fuera del repo).
- Plan por fases con SPEC propia cada una: 1 auth+RBAC (SPEC-AUTH-001) → 2 hardening → 3 idempotencia/saga → 4 Alembic/auditoría → 5 optimización Sales→Stock → 6 observabilidad.

## Historial

| Fecha | Cambio |
|---|---|
| 2026-10-12 | SPEC-AUTH-002 0.1.0 DRAFT (Fase 2: CORS, rate limiting, config segura); ADR-009 PROPOSED |
| 2026-10-12 | SPEC-AUTH-002 1.0.0 VALIDATED (79/79 pytest + E2E; OQ-HARD-01/02 sí, sí) |
| 2026-10-12 | SPEC-SALES-004 1.0.0 VALIDATED (86/86 pytest + E2E con replay; OQ-SAGA 200/sin-exp/422) |
| 2026-10-12 | SPEC-OPS-001 1.0.0 VALIDATED (97/97 pytest + E2E; OQ-AUD tabla+logs/todo/sí) |
| 2026-10-12 | SPEC-STOCK-006 1.0.0 VALIDATED (106/106 pytest + E2E; OQ-BATCH encontrados/siempre/100) |
| 2026-10-12 | SPEC-OPS-002 1.0.0 VALIDATED (116/116 pytest + E2E; OQ-OBS hand-rolled/propia/ya) |
| 2026-10-12 | SPEC-FRONT-002 1.0.0 VALIDATED (build verde + demo manual por usuario: todo OK) |
| 2026-10-13 | SPEC-FRONT-004 1.0.0 VALIDATED (build verde + demo manual por usuario: todo OK) |
| 2026-10-12 | SPEC-FRONT-003 1.0.0 VALIDATED (build verde + demo manual por usuario: todo OK) |
| 2026-10-12 | SPEC-AUTH-001 1.0.0 APPROVED (usuario conforme; autoriza desarrollo); ADR-006/007/008 → APPROVED |
| 2026-10-12 | SPEC-AUTH-001 1.0.0 VALIDATED (67/67 pytest + E2E con login); identidad de servicio Sales→Stock (addendum ADR-008) |
| 2026-10-12 | SPEC-AUTH-001 0.1.0 DRAFT (Opción 1: admin/cajero, sin registro público); ADR-006/007/008 PROPOSED; D-AUTH-SCOPE DECIDED (ampliación de alcance a seguridad backend) |

| Fecha | Cambio |
|---|---|
| 2026-09-29 | Frontend Vite IMPLEMENTED (SPEC-FRONT-001): productos/venta/ventas sobre APIs reales, build verde, serve 200; demo manual AC-FRONT-01 pendiente |
| 2026-09-29 | Fase 3: infra/docker-compose.yml + Dockerfiles + init.sql (ventas_db/stock_db); E2E real Ventas→Stock por HTTP en verde (infra/e2e_check.py); docker CLI no disponible en esta máquina, compose entregado sin ejecutar |
| 2026-09-29 | SPEC-SALES-001/002/003 1.0.0 APPROVED → VALIDATED (13/13 pytest); OQ-ERF03-01 (fusión) y OQ-ARCH-01 (sin estados) DECIDED; backend ERF-01..08 completo |
| 2026-09-29 | SPEC-STOCK-001/002/003/005 1.0.0 APPROVED → VALIDATED (25/25 pytest); stock-service completa ERF-02/04/05/06/08 |
| 2026-09-29 | SPEC-STOCK-004 0.1.0 → 1.0.0 APPROVED; ADR-002 y ADR-005 PROPOSED → APPROVED; OQ-ERF02-01, OQ-ERF05-01, OQ-ERF01-01 DECIDED |
