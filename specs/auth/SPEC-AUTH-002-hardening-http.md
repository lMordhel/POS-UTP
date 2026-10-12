# SPEC-AUTH-002 — Hardening HTTP (CORS, rate limiting, configuración segura)

## Metadata

- ID: SPEC-AUTH-002
- Requirement: Plan de seguridad Fase 2 — endurece ERF-09/ERF-10 (sin ERF nuevo; no amplía funcionalidad, reduce superficie).
- Service: Sales + Stock
- Status: APPROVED
- Version: 1.0.0
- Priority: Muy alta

## Objective

Que el backend solo hable con el frontend autorizado, frene la fuerza bruta y el
abuso (login, ventas, escrituras), responda con cabeceras seguras y no arranque
en producción con valores de ejemplo.

## Scope

* CORS restrictivo por entorno en ambos servicios (fin de `allow_origins=["*"]`).
* Rate limiting por IP en auth y escrituras (librería propuesta: `slowapi`, almacenamiento en memoria).
* Cabeceras de seguridad en todas las respuestas.
* Fail-fast en producción (`POS_ENV=prod`) ante secretos/credenciales/CORS de ejemplo.
* `/docs`, `/redoc` y `/openapi.json` desactivados en producción (propuesto, OQ-HARD-01).

## Out of Scope

* WAF, TLS/HTTPS (responsabilidad del despliegue/reverse proxy, no del código).
* Rate limiting distribuido (Redis): con 1 réplica el almacenamiento en memoria basta; se documenta la limitación.
* Idempotencia de ventas, Alembic, optimización y observabilidad (Fases 3-6, SPECs propias).

## Actors

* Frontend autorizado (`http://localhost:5173` en dev; URL productiva por env).
* Atacante genérico: fuerza bruta a `/auth/login`, abuso de escrituras, hotlinking desde otros orígenes.
* Operador: configura orígenes, límites y secretos por entorno.

## Preconditions

* SPEC-AUTH-001 implementada (auth + RBAC existen; esta SPEC los endurece).
* Variables por servicio: `{STOCK,SALES}_CORS_ORIGINS`, `{STOCK,SALES}_JWT_SECRET`, `SALES_ADMIN_PASSWORD`, `POS_ENV`.

## Functional Requirements

* FR-01: Los orígenes CORS deben leerse de `{PREFIJO}_CORS_ORIGINS` (coma-separados). Default dev: `http://localhost:5173`. Nunca `*` salvo valor explícito documentado.
* FR-02: Límites por IP propuestos (configurables por env): `POST /auth/login` 5/minuto; `POST /auth/refresh` 20/minuto; `POST /sales` 60/minuto; `POST/PUT/DELETE /products` y `PATCH stock` 60/minuto. Lecturas sin límite (OQ-HARD-02).
* FR-03: Al superar el límite → `429` con header `Retry-After`, sin filtrar detalles internos.
* FR-04: Toda respuesta debe incluir `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`; el header `Server` no debe delatar versión.
* FR-05: Con `POS_ENV=prod`, el arranque debe fallar si `JWT_SECRET`, `ADMIN_PASSWORD` o `CORS_ORIGINS` conservan valores de ejemplo (extiende el fail-fast de T2).
* FR-06: Con `POS_ENV=prod`, `/docs`, `/redoc` y `/openapi.json` deben responder 404 (propuesto).

## Business Rules

* BR-01: La seguridad no depende del secreto del algoritmo: límites y orígenes viven en configuración, versionados solo como ejemplo.
* BR-02: El rate limiting es por IP de cliente directo (despliegue académico sin proxy; documentar que tras un proxy habría que usar `X-Forwarded-For`).
* BR-03: Sin SPEC aprobada no se implementa (SDD-001); esta SPEC en DRAFT no autoriza código.

## API Contract

Sin endpoints nuevos. Cambios observables:
* Preflight `OPTIONS` desde origen no listado → sin `Access-Control-Allow-Origin` (el navegador bloquea).
* `POST /auth/login` (y demás rutas limitadas) → `429 {detail} + Retry-After` al exceder.
* `GET /docs`, `/redoc`, `/openapi.json` → 404 con `POS_ENV=prod`.

## Validation Rules

* `CORS_ORIGINS`: lista no vacía en prod; cada origen con esquema `http(s)://` (validar al arrancar, 500 temprano no: fallo en arranque).
* Límites con formato `N/periodo` válido (`minute`, `hour`); valores <= 0 → error de configuración en arranque.

## Error Handling

* `429`: límite excedido (con `Retry-After` en segundos).
* Fallo de arranque en prod por config insegura: `RuntimeError` con mensaje que nombra la variable (solo en logs del operador, nunca al cliente).

## Acceptance Criteria

### AC-HARD02-01 — CORS bloquea origen no autorizado

Given `CORS_ORIGINS=http://localhost:5173`
When un navegador hace preflight desde `http://evil.test`
Then la respuesta no debe incluir `Access-Control-Allow-Origin: http://evil.test`.

### AC-HARD02-02 — CORS permite al frontend

Given el origen autorizado
When hace preflight a `/api/v1/sales`
Then debe recibir `Access-Control-Allow-Origin` exacto y 200.

### AC-HARD02-03 — Login frena fuerza bruta

Given el límite 5/minuto en `/auth/login`
When se hacen 6 logins en 60 segundos desde la misma IP
Then el sexto debe responder 429 con `Retry-After`.

### AC-HARD02-04 — Cabeceras seguras

Given cualquier respuesta de la API
When se inspeccionan sus headers
Then debe traer `nosniff`, `DENY` y `no-referrer`, sin versión en `Server`.

### AC-HARD02-05 — Prod no arranca con ejemplos

Given `POS_ENV=prod` con `JWT_SECRET` o `ADMIN_PASSWORD` de ejemplo
When arranca el servicio
Then debe fallar antes de servir (excepción clara en logs).

### AC-HARD02-06 — Sin docs en prod

Given `POS_ENV=prod`
When se pide `/docs` u `/openapi.json`
Then debe responder 404.

## Open Questions

* OQ-HARD-01: DECIDED 2026-10-12 → sí, desactivar `/docs`, `/redoc` y `/openapi.json` en producción (FR-06). En dev siguen activos.
* OQ-HARD-02: DECIDED 2026-10-12 → rate limit solo en escrituras + auth con los valores propuestos (login 5/min, refresh 20/min, escrituras 60/min); lecturas sin límite. El abuso futuro en lecturas se cubre con límite selectivo sin tocar el resto.

## Traceability

Requirement: Plan Fase 2 (endurece ERF-09/ERF-10, sin ERF nuevo)
Endpoint: Sin endpoints nuevos (429 en rutas limitadas; 404 en docs según OQ)
Service: Sales + Stock
Tests: Pendiente (futuros: `test_cors_forbids_unknown_origin`, `test_cors_allows_frontend`, `test_login_rate_limited_429`, `test_security_headers_present`, `test_prod_refuses_example_secrets`, `test_docs_disabled_in_prod`)

## Technical Notes

* Librería propuesta `slowapi` (estándar FastAPI; nueva dependencia como `bcrypt` en Fase 1). Límites leídos de settings para que los tests los bajen por env; el estado del limitador debe aislarse entre tests (documentar cómo en la implementación).
* CORS vía `CORSMiddleware` con orígenes de settings (reemplaza `["*"]` en ambos `main.py`).
* Headers vía middleware propio mínimo (3 cabeceras + `Server` genérico).
* Fail-fast: extender el chequeo de T2 en `get_settings()` (JWT + admin + CORS con `*` en prod).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-12 | OQ-HARD-01/02 DECIDED (sí a ambos); DRAFT → APPROVED (autoriza desarrollo) | User approval: sí, sí |
|---|---|---|---|
| 0.1.0 | 2026-10-12 | Initial specification (DRAFT, no autoriza implementar) | Plan de seguridad Fase 2 |
