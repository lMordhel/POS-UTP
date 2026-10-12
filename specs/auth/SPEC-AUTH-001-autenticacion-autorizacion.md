# SPEC-AUTH-001 — Autenticación y autorización por roles (modelo mínimo académico)

## Metadata

- ID: SPEC-AUTH-001
- Requirement: ERF-09 (autenticación) + ERF-10 (autorización por roles) — propuestos por el usuario el 2026-10-12 para el documento académico (OQ-AUTH-02 DECIDED); base: decisión aprobada Opción 1 (modelo mínimo: `admin` + `cajero`, sin registro público). Ampliación de alcance autorizada (auth figuraba fuera de alcance en `architecture.md` y SDD-008; ver D-AUTH-SCOPE en `docs/DECISIONS.md`).
- Service: Sales (emisión de tokens, gestión de usuarios en `ventas_db`) + Stock y Sales (verificación y enforcement)
- Status: APPROVED
- Version: 1.0.0
- Priority: Muy alta (Fase 1 del plan de seguridad)

## Objective

Cerrar el acceso al backend: solo usuarios autenticados operan la API, y cada
rol solo ejecuta las operaciones permitidas. El frontend puede ocultar botones,
pero los permisos se verifican obligatoriamente en el backend.

## Scope

* Modelo de usuarios en `ventas_db`, gestionado por Sales (ADR-006).
* Login con usuario/contraseña; contraseña con hash adecuado, nunca en texto plano.
* JWT de acceso de corta duración (15 min propuesto) + refresh rotativo con detección de reúso (OQ-AUTH-01 DECIDED).
* RBAC con dos roles: `admin`, `cajero`, según la matriz aprobada abajo.
* Enforcement en backend en todos los endpoints de Stock y Sales.
* Gestión de usuarios solo por `admin`: crear, editar, desactivar (sin borrado físico).
* Bootstrap del primer `admin` desde variables de entorno, solo si la tabla está vacía (OQ-AUTH-04 DECIDED).

## Out of Scope

* Registro público / autoservicio (rechazado en Opción 1).
* OAuth/SSO, MFA, recuperación de contraseña.
* CORS restrictivo, rate limiting y configuración segura → futura SPEC (Fase 2 del plan).
* Idempotencia de ventas y corrección de la saga → futura SPEC (Fase 3).
* Migraciones Alembic y auditoría → futura SPEC (Fase 4).
* Optimización de llamadas Sales→Stock, logs/métricas → futuras SPECs (Fases 5-6).

## Actors

* Administrador (`admin`): gestiona productos, usuarios y roles; consulta todo; ajusta stock.
* Cajero (`cajero`): registra ventas; consulta productos, stock y todas las ventas en lectura; sin gestión de usuarios, productos ni ajustes manuales.
* Servicio Sales: autentica (login/refresh), emite tokens, gestiona usuarios.
* Servicio Stock: valida tokens y aplica RBAC en sus endpoints (no almacena usuarios).

## Preconditions

* `ventas_db` disponible; tabla `users` creada (vía `init_db` en esta fase; migraciones en Fase 4).
* Secreto JWT configurado por entorno (`SALES_JWT_SECRET` / `STOCK_JWT_SECRET`, mismo valor); arranque falla si es el valor de ejemplo en producción.
* Primer `admin` creado por bootstrap (variables de entorno, solo si no existe ningún usuario).

## Functional Requirements

* FR-01: El sistema debe almacenar usuarios con `username` único, `password_hash` (bcrypt, propuesta: cost 12), `rol` (`admin|cajero`) y `activo` (bool). Nunca texto plano.
* FR-02: `POST /api/v1/auth/login` con `{username, password}` válidos debe responder 200 con `{access_token, token_type: "bearer"}`. El token incluye `sub`, `rol`, `iat`, `exp`, `jti`.
* FR-03: Toda petición (salvo `/health` y `/auth/login`) debe exigir `Authorization: Bearer <token>`; sin token o con token inválido/expirado → 401. Usuario desactivado → 401 aunque el token sea válido.
* FR-04: Cada endpoint debe verificar el rol según la matriz RBAC; rol insuficiente → 403.
* FR-05: Solo `admin` gestiona usuarios: `POST /api/v1/users`, `GET /api/v1/users`, `GET /api/v1/users/{id}`, `PATCH /api/v1/users/{id}` (editar rol, activar/desactivar). Sin borrado físico.
* FR-06: La expiración propuesta del access token es 15 minutos.
* FR-07: `POST /api/v1/auth/refresh` con un refresh válido debe rotar: emite un par nuevo (access + refresh) e invalida el refresh usado. Reutilizar un refresh ya rotado → 401 y revocación de toda la familia de tokens (detección de reúso, OQ-AUTH-01 DECIDED).
* FR-08: En el arranque, si la tabla `users` está vacía, el sistema debe crear el primer `admin` desde `ADMIN_USERNAME`/`ADMIN_PASSWORD` (OQ-AUTH-04 DECIDED). Si ya existe al menos un usuario, no debe hacer nada.

## Business Rules

* BR-01: Los permisos se verifican en el backend. Ocultar botones en el frontend es solo UX; un `cajero` que llame directo a `PATCH /products/{id}/stock` debe recibir 403.
* BR-02: Contraseñas nunca en texto plano ni en logs; verificación con comparación segura.
* BR-03: Desactivar (no borrar) usuarios que se van; los tokens vigentes de un usuario desactivado dejan de aceptarse.
* BR-04: Sin SPEC aprobada no se implementa (SDD-001); esta SPEC en REVIEW aún no autoriza código.
* BR-05: Las ventas registradas son inmutables: no existen endpoints de modificación ni eliminación de ventas (OQ-AUTH-03 DECIDED). De crearse en el futuro, serían solo `admin`.

## Matriz RBAC aprobada (con esta SPEC)

| Endpoint | `admin` | `cajero` |
|---|---|---|
| `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `GET /health` | público | público |
| `GET /api/v1/products`, `GET /api/v1/products/{id}` (Stock) | ✅ | ✅ |
| `POST /api/v1/products`, `PUT /api/v1/products/{id}`, `DELETE /api/v1/products/{id}` (Stock) | ✅ | ⛔ 403 |
| `GET /api/v1/products/{id}/stock` (Stock) | ✅ | ✅ |
| `PATCH /api/v1/products/{id}/stock` (Stock) | ✅ | ⛔ 403 |
| `POST /api/v1/sales` (Sales) | ✅ | ✅ |
| `GET /api/v1/sales`, `GET /api/v1/sales/{id}` (Sales) | ✅ | ✅ lectura (sin modificar ni eliminar: no existen esos endpoints) |
| `POST /api/v1/users`, `GET /api/v1/users*`, `PATCH /api/v1/users/{id}` (Sales) | ✅ | ⛔ 403 |

## API Contract

* `POST /api/v1/auth/login` — Request: `{username: str, password: str}`. Response: `200 {access_token: str, refresh_token: str, token_type: "bearer"}`; errores `401` credenciales inválidas, `422` cuerpo inválido.
* `POST /api/v1/auth/refresh` — Request: `{refresh_token: str}`. Response: `200` par nuevo rotado; errores `401` refresh inválido, expirado o reutilizado (con revocación de la familia).
* `POST /api/v1/users` (admin) — Request: `{username, password (≥ 8 propuesto), rol}`. Response: `201 {id, username, rol, activo}` (sin hash). Errores `401/403/422/409` (username duplicado).
* `PATCH /api/v1/users/{id}` (admin) — Request parcial: `{rol?, activo?, password?}`. Response: `200` usuario actualizado; `404` inexistente.
* Autenticación: header `Authorization: Bearer <JWT>`; esquema de autorización por dependencia `require_role(...)` (skill fastapi-templates: router delgado → service → repository).

## Validation Rules

* `username`: 3-50 caracteres, único (comparación exacta; definir sensibilidad a mayúsculas al aprobar).
* `password`: mínimo 8 caracteres (propuesto); se almacena solo su hash.
* `rol`: exactamente `admin` o `cajero`; cualquier otro valor → 422.
* Token: firma válida, `exp` vigente, `rol` conocido; cualquier fallo → 401 (sin distinguir la causa al cliente).

## Error Handling

* `401`: sin token, token inválido/expirado, credenciales inválidas, usuario desactivado, refresh reutilizado. Mensaje genérico, sin filtrar detalles internos.
* `403`: token válido pero rol insuficiente para el endpoint.
* `404`: usuario inexistente (solo `admin`).
* `409`: `username` duplicado.
* `422`: cuerpo inválido (rol desconocido, password corto, etc.).

## Acceptance Criteria

### AC-AUTH01-01 — Login válido

Given un usuario activo con credenciales correctas
When se solicita `POST /api/v1/auth/login`
Then el servicio debe responder 200
And debe devolver access + refresh JWT con claims `sub`, `rol`, `iat`, `exp`, `jti`.

### AC-AUTH01-02 — Credenciales inválidas

Given credenciales incorrectas (usuario inexistente o password erróneo)
When se solicita login
Then el servicio debe responder 401
And no debe distinguir cuál de los dos datos falló.

### AC-AUTH01-03 — Endpoint protegido sin token

Given ningún token (o token expirado/manipulado)
When se llama a cualquier endpoint protegido
Then el servicio debe responder 401.

### AC-AUTH01-04 — Cajero bloqueado en gestión de catálogo

Given un token con rol `cajero`
When se solicita `POST /api/v1/products` o `PATCH /api/v1/products/{id}/stock`
Then el servicio debe responder 403
And no debe modificar ningún registro.

### AC-AUTH01-05 — Cajero vende y consulta

Given un token con rol `cajero`
When se solicita `POST /api/v1/sales` con líneas válidas
Then el servicio debe responder 201 (previa validación de stock existente)
And debe poder consultar todas las ventas en lectura.

### AC-AUTH01-06 — Gestión de usuarios solo admin

Given un token `admin`
When se crea, edita o desactiva un usuario
Then el servicio debe responder 201/200
And un token `cajero` en los mismos endpoints debe recibir 403.

### AC-AUTH01-07 — Usuario desactivado pierde acceso

Given un usuario desactivado con un token aún vigente
When se llama a cualquier endpoint protegido
Then el servicio debe responder 401.

### AC-AUTH01-08 — Enforcement real en backend

Given un `cajero` que evita el frontend y llama directo a la API
When intenta una operación de `admin`
Then el backend debe responder 403 (la UI no es la barrera de seguridad).

### AC-AUTH01-09 — Refresh válido rota el par

Given un refresh token válido no usado
When se solicita `POST /api/v1/auth/refresh`
Then el servicio debe responder 200 con un par nuevo
And el refresh anterior debe quedar invalidado (un segundo uso → 401).

### AC-AUTH01-10 — Reúso de refresh revoca la familia

Given un refresh ya rotado (reutilizado por atacante o cliente desincronizado)
When se solicita `POST /api/v1/auth/refresh` con él
Then el servicio debe responder 401
And debe revocar toda la familia de tokens de ese usuario.

## Open Questions

* OQ-AUTH-01: DECIDED 2026-10-12 → refresh rotativo con detección de reúso (opción elegida por el usuario). Implementar según FR-07 / AC-AUTH01-09/10 al aprobarse la SPEC.
* OQ-AUTH-02: DECIDED 2026-10-12 → añadir ERF-09 (autenticación) y ERF-10 (autorización por roles) al documento académico. Textos propuestos: ERF-09 "el sistema debe autenticar usuarios con usuario/contraseña, emitir tokens de corta duración con renovación y rechazar accesos sin credenciales válidas"; ERF-10 "el sistema debe restringir cada operación según el rol, verificando permisos en el backend". Pendiente: edición del `.docx` por el usuario (fuera del repo).
* OQ-AUTH-03: DECIDED 2026-10-12 → el cajero consulta todas las ventas en lectura; no existen endpoints de modificación/eliminación (BR-05, inmutabilidad del historial).
* OQ-AUTH-04: DECIDED 2026-10-12 → bootstrap del primer `admin` desde `ADMIN_USERNAME`/`ADMIN_PASSWORD`, solo si la tabla `users` está vacía (FR-08).

## Traceability

Requirement: ERF-09 (autenticación) + ERF-10 (autorización por roles), propuestos 2026-10-12 para el documento académico
Endpoint: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST/GET/PATCH /api/v1/users`, enforcement en endpoints Stock + Sales
Service: Sales (emisión y gestión); Stock + Sales (validación y RBAC)
Tests: Pendiente (futuros: `test_login_valid`, `test_login_invalid_401`, `test_protected_no_token_401`, `test_cashier_forbidden_stock_403`, `test_cashier_can_sell_201`, `test_admin_user_crud`, `test_deactivated_user_401`, `test_expired_token_401`, `test_backend_enforcement_bypass_403`, `test_refresh_rotates_pair`, `test_refresh_reuse_revokes_family`, `test_bootstrap_admin_from_env`)

## Technical Notes

* Usuarios en `ventas_db`, gestionados por Sales (ADR-006). Stock valida JWT con el mismo secreto; no almacena usuarios ni hace llamadas entre servicios para autenticar.
* Capas (skills `fastapi-templates`/`pydantic`/`python-testing-patterns`): `api/v1/endpoints/auth.py` + `users.py` (routers delgados), `services/auth_service.py` + `user_service.py`, `repositories/user_repository.py`, `core/security.py` (hash + JWT + refresh rotation + `require_role`), schemas `UserCreate/UserRead/UserUpdate`, `TokenPair`, `LoginRequest`, `RefreshRequest`. Tabla `refresh_tokens` (jti, familia, revocado, expira) para rotación y detección de reúso.
* JWT propuesto: HS256, secreto por entorno, fail-fast si es valor de ejemplo en producción.
* Fases 2-6 del plan (hardening, idempotencia, Alembic, optimización, observabilidad) van en SPECs separadas; esta SPEC no las autoriza.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-12 | REVIEW → APPROVED (usuario conforme; autoriza desarrollo) | User approval: pasa al desarrollo |
|---|---|---|---|
| 0.1.0 | 2026-10-12 | OQ-AUTH-01..04 DECIDED; entra refresh rotativo + bootstrap por env; Status DRAFT → REVIEW | Respuestas del usuario a las 4 preguntas |
| 0.1.0 | 2026-10-12 | Initial specification (DRAFT, no autoriza implementar) | Decisión usuario Opción 1 + plan de seguridad por fases |
