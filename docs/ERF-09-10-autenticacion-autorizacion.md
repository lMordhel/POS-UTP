# ERF-09 y ERF-10 — Autenticación y autorización por roles

> Documento de trabajo para trasladar al documento académico (`.docx`).
> Estado: propuesta estructurada lista para revisión. Base implementada y
> validada en `main` (SPEC-AUTH-001 1.0.0 VALIDATED, SPEC-AUTH-002 1.0.0 VALIDATED).

## Contexto

El sistema operaba sin control de acceso: cualquier cliente con la URL podía
crear productos, registrar ventas y modificar inventario. ERF-09 y ERF-10
cierran esa brecha con un modelo mínimo académico (dos roles, sin registro
público), verificado en el backend (el frontend solo oculta botones; los
permisos se exigen en la API).

Decisiones que los respaldan: Opción 1 (admin/cajero, sin registro público),
D-AUTH-SCOPE (ampliación de alcance aprobada), ADR-006/007/008.

---

## ERF-09 — Autenticación de usuarios

**Descripción:** el sistema debe autenticar usuarios con usuario y contraseña,
emitir tokens de corta duración con renovación y rechazar accesos sin
credenciales válidas.

**Alcance:**
- Gestión de usuarios en `ventas_db` (servicio Sales; sin microservicio nuevo).
- Login con usuario/contraseña; contraseñas con hash bcrypt, nunca en texto plano.
- Tokens JWT de acceso (15 min) + refresh rotativo con detección de reutilización
  (el reúso revoca la familia completa).
- Bootstrap del primer administrador desde variables de entorno, solo si no
  existe ningún usuario.
- Gestión de usuarios (crear, editar, desactivar; sin borrado físico) solo por `admin`.

**Fuera de alcance:** registro público/autoservicio, OAuth/SSO, MFA,
recuperación de contraseña.

**Endpoints principales:**
- `POST /api/v1/auth/login` → 200 `{access_token, refresh_token}` / 401.
- `POST /api/v1/auth/refresh` → 200 par rotado / 401 (incluye reúso detectado).
- `POST /api/v1/users`, `GET /api/v1/users*`, `PATCH /api/v1/users/{id}` (solo `admin`).

**Criterios de aceptación:**
1. Credenciales correctas → 200 con par de tokens (claims `sub`, `rol`, `iat`, `exp`, `jti`).
2. Credenciales incorrectas → 401 sin distinguir usuario de password.
3. Sin token (o expirado/manipulado) → 401 en cualquier endpoint protegido.
4. Usuario desactivado → 401 aunque su token siga vigente.
5. Refresh válido → rota el par e invalida el anterior.
6. Refresh reutilizado → 401 + revocación de la familia.

**Trazabilidad:** SPEC-AUTH-001 (AC-AUTH01-01/02/03/06/07/09/10) + SPEC-AUTH-002
(hardening: rate limit en login/refresh, CORS, fail-fast). Tests:
`test_auth.py` (11 passed), `test_security.py`, E2E con login.

---

## ERF-10 — Autorización por roles

**Descripción:** el sistema debe restringir cada operación según el rol del
usuario, verificando permisos en el backend.

**Roles:**
- **Administrador (`admin`):** gestionar productos, gestionar usuarios y roles,
  consultar todo, ajustar stock manualmente.
- **Cajero (`cajero`):** registrar ventas; consultar productos, stock y todas
  las ventas en lectura. Sin gestión de usuarios, productos ni ajustes manuales.

**Matriz de permisos (aprobada):**

| Endpoint | `admin` | `cajero` |
|---|---|---|
| `POST /auth/login`, `POST /auth/refresh`, `GET /health` | público | público |
| `GET /products`, `GET /products/{id}`, `GET .../stock` | ✅ | ✅ |
| `POST/PUT/DELETE /products`, `PATCH .../stock` | ✅ | ⛔ 403 |
| `POST /sales`, `GET /sales*` | ✅ | ✅ (lectura total; ventas inmutables, sin endpoints de modificación/eliminación) |
| `POST/GET/PATCH /users*` | ✅ | ⛔ 403 |

**Reglas:**
- Sin token o token inválido → 401; token válido sin rol suficiente → 403.
- Las llamadas internas Sales→Stock usan credencial de servicio (secreto
  compartido, rol admin); la atribución al usuario viaja en el motivo (`venta:{id}`).

**Criterios de aceptación:**
1. Cajero en gestión de catálogo o ajustes → 403 sin modificar nada.
2. Cajero vende (201) y consulta ventas.
3. Solo admin gestiona usuarios (cajero → 403).
4. Bypass del frontend (llamada directa) → el backend responde 403 igual.

**Trazabilidad:** SPEC-AUTH-001 (AC-AUTH01-04/05/06/08) + SPEC-AUTH-002.
Tests: `test_auth.py`, `test_rbac.py` (Stock), suites migradas a headers.

---

## Relación con ERF-01..ERF-08

ERF-09/10 no cambian el negocio existente: ventas, productos e inventario se
comportan igual, ahora con identidad y permisos. La saga suma credencial de
servicio interna sin afectar contratos.

## Pendiente para el `.docx`

- [ ] Revisar textos y matriz con el docente/equipo.
- [ ] Numerar como ERF-09/ERF-10 en el documento académico.
- [ ] Adjuntar evidencias si se piden (tests en verde, SPECs 1.0.0 VALIDATED).
