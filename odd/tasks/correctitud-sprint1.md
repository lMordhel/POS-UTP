# Feature: correctitud-sprint1 (Sprint 1 — Correctitud)

Cierre de los 4 defectos confirmados por la auditoría del 2026-02 más el
apercibimiento de configuración (logging) y de entorno (.env.example/POS_ENV).
Resultado esperado: correctitud demostrada con tests que fallan antes del fix.

## Specs

### S1 — El refresh token no puede actuar como access token

> **No tocar el token de servicio.** `create_service_token()` emite
> `type="service"` y Stock lo acepta hoy en `get_current_claims`; la
> credencial Sales→Stock (ADR-008 addendum) sigue siendo válida.

Requisito del usuario, verbatim:

> Un refresh token sirve como access token.
> `sales/core/security.py:82-86` y `stock/core/security.py:67-71` decodifican el JWT
> y no validan `type == "access"`. Solo `auth_service.py:66` chequea
> `type == "refresh"`. Consecuencia: un token de 7 días funciona como access
> token de 15 minutos en todas las rutas protegidas. Toda tu rotación de refresh
> con detección de reuso —que está bien hecha— queda anulada.

Aceptación:
- `get_current_claims` rechaza con 401 toda credencial cuyo `type` no esté en la
  allowlist (`access`, `service`), en **ambos** servicios.
- Un refresh token válidamente firmado y vigente contra `GET /api/v1/sales`
  (Sales) y `GET /api/v1/products` (Stock) devuelve **401**, no 2xx.
- Un access token sigue devolviendo 2xx.
- El token de servicio (`type="service"`) sigue autenticando en Stock.
- Un token sin claim `type` se rechaza (401): no hay default permisivo.

### S2 — El ajuste de stock no puede perder escrituras concurrentes

> `product_service.py:138-152` hace leer-modificar-escribir sin bloqueo.

Aceptación:
- La lectura de la fila de inventario usada por `adjust_stock` toma un lock de
  fila (`SELECT ... FOR UPDATE`) en dialectos que lo soportan.
- El delta se aplica sobre el valor leído bajo lock, no sobre una lectura previa.
- Un test prueba el lock sobre el SQL **compilado** para Postgres (SQLite lo
  ignora: un test de dos hilos sobre SQLite no probaría nada y queda prohibido
  como evidencia).
- Los 409 por stock insuficiente y la traza de movimientos siguen intactos.

### S3 — Ningún error de Stock puede escapar como 500 crudo ni saltear la compensación

> `stock_client.py:78` y `:108` llaman `raise_for_status()` fuera del `try`. Un 401
> o un 404 de stock lanza `httpx.HTTPStatusError` crudo y sale como error interno,
> en vez de 502/404. Peor: `StockProductNotFoundError` (`stock_client.py:103`) no
> está importado en `sale_service.py`, así que un producto desactivado entre el
> batch y el ajuste también termina en 500.

Aceptación:
- Ningún `httpx.HTTPError` cruza el borde del cliente: todo status no esperado se
  traduce a `StockUnavailableError` (→ 502) o a la excepción de dominio correcta.
- `batch_get_products`: 401/403/5xx → `StockUnavailableError`; nunca
  `HTTPStatusError`.
- `adjust_stock`: 404 → `StockProductNotFoundError`; 409 → `StockInsufficientError`;
  401/403/5xx/422 → `StockUnavailableError`.
- `sale_service` mapea `StockProductNotFoundError` a 404 de dominio y **compensa**
  las líneas ya descontadas antes de propagar.
- Cualquier excepción no prevista durante el descuento compensa antes de
  propagarse: no queda stock debitado sin venta.
- `stock_client.py` deja de ser el único archivo sin tests: se cubre con
  `httpx.MockTransport`, sin red.

### S4 — Un rechazo de negocio no desloguea al usuario

> `frontend/src/api.js:46-50`: si el request reintentado después del refresh
> devuelve cualquier no-2xx, llama `onUnauthorized()`. Un 409 por stock
> insuficiente te expulsa y borra el carrito.

Aceptación:
- Tras un refresh exitoso, un retry que devuelve 409/422/500 **no** llama
  `onUnauthorized()`: propaga el error con `status` y mensaje.
- Un 401 tras el retry **sí** llama `onUnauthorized()` (sesión realmente muerta).
- Un refresh fallido sigue llamando `onUnauthorized()`.
- El camino sin retry no cambia de comportamiento.
- El comportamiento queda pinneado por un test ejecutable sin navegador.

### S5 — Logging configurado

> Logging configurado (nunca se llama `basicConfig`), `middleware.py:73` escribe al vacío.

Aceptación:
- Ambos servicios configuran logging una sola vez al importar la app
  (`basicConfig` con nivel por entorno).
- El access log de `ObservabilityMiddleware` aparece en stderr con formato
  parseable, sin handlers duplicados al reimportar.

### S6 — Entorno reproducible declarado

> .env.example backend + POS_ENV en compose — `config.py:12,19`; `docker-compose.yml:21-42`.

Aceptación:
- Existe `.env.example` por servicio con **todas** las variables que
  `Settings` acepta (más `POS_ENV`), sin secretos reales.
- `POS_ENV` aparece declarado explícitamente en el compose, junto a los secretos
  que hoy toman el default de dev.

## Tasks

| ID | Tarea | Spec | Ruta | Commit |
| --- | --- | --- | --- | --- |
| T1 | Entorno (venv 3.14 + deps) y línea base de tests | — | inline | — |
| T2 | Allowlist de `type` en `get_current_claims` (sales + stock) | S1 | inline | `fix(auth)` |
| T3 | Lock de fila en el ajuste de inventario | S2 | inline | `fix(stock)` |
| T4 | Mapeo de errores en `stock_client` + compensación de la saga | S3 | inline | `fix(sales)` |
| T5 | No desloguear ante rechazo de negocio | S4 | inline | `fix(front)` |
| T6 | `basicConfig` por servicio | S5 | inline | `chore(obs)` |
| T7 | `.env.example` x2 + `POS_ENV` en compose | S6 | inline | `chore(infra)` |
| T8 | Suite completa + verificación independiente | S1-S6 | verify | — |

Sin delegación de escritura: ninguna unidad llega al peso que justifica un worker
(cada fix son pocas líneas más su test en un solo módulo).

## Log

**L1 — Pedido original del usuario (verbatim, Plan / Sprint 1):**

> Sprint 1 — Correctitud (3-5 días). Los 4 bugs + logging.basicConfig + .env.example
> + tests que cubran stock_client y la carrera de oversell. Resultado: tu mejor
> historia de entrevista — "encontré un bypass de autenticación en mi propio
> sistema y lo cerré con un test que lo prueba".

Los cuatro defectos, el logging y el `.env.example` quedan citados verbatim en
S1-S6.

**L2 — Decisión de alcance (usuario):** "Sprint 1 completo — Los 4 bugs + el quinto
(compensación) + logging.basicConfig + .env.example + un test RED por hallazgo."
Sprint 2 (CI/Docker) y Sprint 3 (AWS) quedan fuera de esta ficha.

**L3 — Verificación de premisas (orquestador):** los 4 defectos se confirmaron
contra el código antes de escribir nada. Líneas exactas: `security.py:82` (sales) /
`:67` (stock); `product_service.py:138,145`; `stock_client.py:78,108`;
`api.js:47,50`. Greps recursivos confirman ausencia total de `with_for_update`,
`basicConfig`, `pool_size` y `pool_pre_ping` en los 71 archivos de backend.

**L4 — Hallazgo del orquestador (no estaba en la auditoría):** el defecto 3 no
termina en 500. `sale_service.py:243-248` sólo captura `StockInsufficientError` y
`StockUnavailableError`; un `StockProductNotFoundError` sube sin compensar. Las
líneas ya descontadas quedan debitadas, la venta se rollbackea y no hay venta:
**fuga silenciosa de inventario**. Se absorbe en S3 (es la misma causa raíz), no
como requisito nuevo.

**L5 — Restricción descubierta en el código (crítica para S1):** el fix ingenuo de
S1 (`type == "access"`) rompe la saga, porque `create_service_token()` emite
`type="service"`. Por eso la allowlist incluye `service` y hay un test que lo
protege.

## Progress

- [ ] T1 — entorno y línea base
- [ ] T2 — S1
- [ ] T3 — S2
- [ ] T4 — S3
- [ ] T5 — S4
- [ ] T6 — S5
- [ ] T7 — S6
- [ ] T8 — verificación
