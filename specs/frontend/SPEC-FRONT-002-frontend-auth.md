# SPEC-FRONT-002 — Frontend con autenticación y roles

## Metadata

- ID: SPEC-FRONT-002
- Requirement: ERF-09/ERF-10 (extensión al frontend) + decisión de usuario (fase frontend).
- Service: Frontend (consume Sales + Stock autenticados)
- Status: VALIDATED
- Version: 1.0.0
- Priority: Alta

## Objective

Que el frontend opere contra el backend con auth: login, sesión con
renovación, UI según rol (`admin`/`cajero`) y manejo claro de 401/403/429/502.

## Scope

* Pantalla de login (usuario/contraseña → tokens; error 401 genérico).
* Sesión: guardar par de tokens, adjuntar `Bearer` en cada llamada, renovar con refresh ante 401 y reintentar una vez; si el refresh falla → logout a login.
* Logout manual (limpia tokens y estado).
* Puertas por rol: pestañas y botones según matriz (admin ve gestión de productos + Usuarios; cajero solo vende y consulta).
* Vista Usuarios (solo admin): listar, crear (usuario/password/rol), desactivar.
* Productos: crear/editar/desactivar solo admin; catálogo visible para ambos.
* Ventas (nueva + lista): ambos roles.
* Mensajes de error por código: 401 credenciales/sesión, 403 sin permiso, 429 reintenta, 502 servicio no disponible.

## Out of Scope

* Registro público, MFA, OAuth, recuperación/cambio de password.
* Tests automatizados de UI (ver OQ-FRONT-03).
* Cambios de endpoints backend (se consumen los existentes).
* Roles nuevos o permisos distintos de la matriz aprobada.

## Actors

* Cajero: login, vende, consulta productos/stock/ventas.
* Admin: todo lo anterior + gestiona productos y usuarios.

## Preconditions

* Backend en `main` con auth (SPEC-AUTH-001/002): login admin/cajero disponibles.
* `VITE_STOCK_URL`, `VITE_SALES_URL` apuntando a los servicios.

## Functional Requirements

* FR-01: Sin sesión válida, la app debe mostrar solo el login (ninguna vista ni llamada con datos).
* FR-02: Login válido debe guardar `{access_token, refresh_token, username, rol}` y entrar a las vistas del rol.
* FR-03: Cada llamada debe llevar `Authorization: Bearer <access>`; ante 401, renovar una vez con el refresh y reintentar; si falla, limpiar sesión y volver a login.
* FR-04: Las pestañas deben filtrarse por rol (cajero no ve Usuarios) y los botones de gestión deben renderizarse solo con permiso (la seguridad real sigue en el backend).
* FR-05: La vista Usuarios (admin) debe listar, crear y desactivar (sin borrado).
* FR-06: Los errores de API deben mostrarse con el banner existente, mapeados por código (401/403/429/502/422).

## Business Rules

* BR-01: Nunca guardar ni mostrar el password; nunca poner tokens en URLs.
* BR-02: Un 403 no cierra sesión (es falta de permiso, no de identidad); un 401 con refresh inválido sí.
* BR-03: Sin SPEC aprobada no se implementa (SDD-001); esta SPEC en DRAFT no autoriza código.

## API Contract

Sin endpoints nuevos: usa `POST /auth/login`, `POST /auth/refresh`,
`GET/POST/PATCH /users`, `GET/POST/PUT/DELETE /products`, `GET/PATCH stock`,
`POST/GET /sales` (contratos de SPECs previas).

## Validation Rules

* Login: usuario y password no vacíos antes de llamar.
* Crear usuario: username ≥ 3, password ≥ 8, rol válido (mismo contrato backend).

## Error Handling

* `401` en login → "Credenciales inválidas"; `401` en uso → renueva o sale a login.
* `403` → "Sin permiso para esta operación".
* `429` → "Demasiados intentos, reintenta en un momento".
* `502` → "Servicio no disponible, intenta de nuevo".
* `422` → detalle del backend tal cual.

## Acceptance Criteria

### AC-FRONT02-01 — Login y roles

Given credenciales de admin y de cajero
When cada uno inicia sesión
Then el admin debe ver 4 pestañas (incluida Usuarios) y el cajero 3 (sin Usuarios).

### AC-FRONT02-02 — Login inválido

Given credenciales incorrectas
When se intenta entrar
Then debe mostrar error sin entrar ni guardar tokens.

### AC-FRONT02-03 — Gestión solo admin

Given sesión de cajero
When mira Productos
Then no debe ver crear/editar/desactivar (y el backend ya lo bloquea con 403).

### AC-FRONT02-04 — Sesión renovada

Given access expirado con refresh válido
When se hace una operación
Then debe renovar en silencio y completar sin pedir login.

### AC-FRONT02-05 — Sesión muerta

Given refresh inválido o usuario desactivado
When se opera
Then debe volver a login con sesión limpia.

### AC-FRONT02-06 — Admin gestiona usuarios

Given sesión admin
When crea y desactiva un usuario desde la vista
Then la lista debe reflejarlo y el nuevo usuario debe poder entrar.

## Open Questions

* OQ-FRONT-01: DECIDED 2026-10-12 → `localStorage` (persiste recarga; tradeoff XSS documentado, sin tokens en URLs).
* OQ-FRONT-02: DECIDED 2026-10-12 → sí, vista Usuarios incluida (listar/crear/desactivar).
* OQ-FRONT-03: DECIDED 2026-10-12 → demo manual + `build` verde (precedente FRONT-001; Vitest en fase posterior si hace falta).

## Traceability

Requirement: ERF-09/ERF-10 (frontend)
Endpoint: Consume endpoints existentes (sin cambios)
Service: Frontend
Tests: Pendiente (propuesta: demo manual por AC + `npm run build`; decidir en OQ-FRONT-03)

## Technical Notes

* `api.js` centraliza: `request()` adjunta Bearer, maneja 401→refresh→retry×1→logout (callback a AuthContext). Nada de `fetch` directo en vistas.
* `AuthContext` (nuevo): `{user, login, logout, apiFetch}`; persistencia según OQ-FRONT-01.
* `UsersView.jsx` (nuevo, admin): tabla + crear + desactivar, mismo estilo (banner/errores) que vistas actuales.
* Skill `vercel-react-best-practices` (subconjunto no-Next.js) como en FRONT-001.
* Sin router: pestañas por estado como hoy; `App.jsx` puerta por sesión.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-12 | OQ-FRONT-01/02/03 DECIDED (localStorage/sí/manual); DRAFT → APPROVED (autoriza desarrollo) | User approval: localStorage, sí, manual |
| 1.0.0 | 2026-10-12 | APPROVED → VALIDATED (build verde + demo manual por usuario: todo OK) | Sign-off usuario en AC-FRONT02-01..06 |
|---|---|---|---|
| 0.1.0 | 2026-10-12 | Initial specification (DRAFT, no autoriza implementar) | Fase frontend con auth |
