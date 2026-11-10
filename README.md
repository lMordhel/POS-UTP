# POS-UTP — Sistema de Ventas para Microempresas

Proyecto académico (Diseño e Implementación de Arquitectura Empresarial):
POS modular con microservicios. Fuente de verdad funcional: `specs/`.

## Arquitectura

```text
Frontend Vite (:5173) ──► Sales (:8001) ──► Stock (:8002)
                                │                  │
                           ventas_db            stock_db
                        (PostgreSQL, 1 instancia, 2 DBs)
```

* **stock-service** (FastAPI): productos, inventario, consulta/actualización de stock → ERF-02/04/05/06/08.
* **sales-service** (FastAPI): ventas y detalles; valida precios/stock y descuenta vía HTTP a Stock → ERF-01/03/07; cliente (texto libre) y pago en efectivo con vuelto server-side → ERF-11.
* Sin API Gateway (YAGNI, 2 servicios). Decisiones en `docs/DECISIONS.md`, trazabilidad en `docs/TRACEABILITY.md`.

## Requisitos

* Docker + Docker Compose (backend + Postgres).
* Node 18+ y npm (frontend).

## Levantar todo

```powershell
# Backend + Postgres (primera vez o con cambios)
docker compose -f infra/docker-compose.yml up -d --build

# Ver estado / salud
docker compose -f infra/docker-compose.yml ps
Invoke-RestMethod http://localhost:8002/health
Invoke-RestMethod http://localhost:8001/health

# Frontend (otra terminal)
cd frontend
npm install   # solo primera vez
npm run dev   # http://localhost:5173
```

Swagger: http://localhost:8002/docs (Stock), http://localhost:8001/docs (Sales).

```powershell
# Apagar
docker compose -f infra/docker-compose.yml down
```

## Entorno y configuración

Cada servicio lee su configuración con pydantic-settings (`env_prefix` `SALES_` /
`STOCK_`) desde variables de entorno o desde un `.env` en la carpeta del
servicio; `infra/.env` alimenta al compose. Los `.env` no se versionan (ver
`.gitignore`): la plantilla versionada de cada servicio es su `.env.example`,
que se copia a `.env` y se ajusta. Esto es el inventario de lo que acepta cada uno, y
un test por servicio (`tests/test_unit/test_env_example.py`) falla si la plantilla
se desactualiza respecto de `Settings`.

| Variable | Servicio | Default | Para qué |
| --- | --- | --- | --- |
| `POS_ENV` | ambos | `dev` | `prod` desactiva `/docs` y activa el fail-fast de secretos |
| `POS_LOG_LEVEL` | ambos | `INFO` | nivel del root logger |
| `SALES_DATABASE_URL` / `STOCK_DATABASE_URL` | sales / stock | `sqlite:///./*.db` | Postgres en compose |
| `SALES_STOCK_SERVICE_URL` | sales | `http://localhost:8002` | cliente Sales→Stock (ADR-003) |
| `SALES_STOCK_TIMEOUT_SECONDS` | sales | `5.0` | timeout del cliente |
| `SALES_JWT_SECRET` / `STOCK_JWT_SECRET` | sales / stock | `change-me-dev-only` | **mismo valor**: Sales firma el token de servicio que Stock verifica (ADR-008) |
| `SALES_API_V1_STR` / `STOCK_API_V1_STR` | sales / stock | `/api/v1` | prefijo de la API |
| `SALES_JWT_ALGORITHM` / `STOCK_JWT_ALGORITHM` | sales / stock | `HS256` | algoritmo de firma |
| `SALES_ACCESS_TOKEN_MINUTES` / `STOCK_ACCESS_TOKEN_MINUTES` | sales / stock | `15` | vida del access token |
| `SALES_REFRESH_TOKEN_DAYS` / `STOCK_REFRESH_TOKEN_DAYS` | sales / stock | `7` | vida del refresh token |
| `SALES_ADMIN_USERNAME` / `SALES_ADMIN_PASSWORD` | sales | `admin` / `change-me-admin` | admin de bootstrap |
| `SALES_CORS_ORIGINS` / `STOCK_CORS_ORIGINS` | sales / stock | `http://localhost:5173` | orígenes permitidos |
| `SALES_RATE_LOGIN`, `SALES_RATE_REFRESH`, `SALES_RATE_WRITE`, `STOCK_RATE_WRITE` | sales / stock | ver `core/config.py` | límites slowapi |

Con `POS_ENV=prod`, cualquiera de los secretos de ejemplo hace fallar el arranque
a propósito (`app/core/config.py`).

## Demo en 1 minuto

1. Stock docs → `POST /products` (ej. `{"codigo":"DEMO-1","nombre":"Café","precio":"25.90","cantidad_inicial":50}`).
2. Frontend → Nueva venta → Agregar → Confirmar → total del servidor.
3. Verificar stock descontado y venta en la pestaña Ventas.

## Tests

```powershell
cd services/stock-service; py -m pytest tests -q   # 72 tests
cd ../sales-service; py -m pytest tests -q          # 87 tests
cd ../..; py infra/e2e_check.py                     # E2E real Ventas→Stock
cd frontend; npm test                               # 4 tests (vitest, sin navegador)
```

## Deploy del frontend (Vercel)

El frontend es un build estático de Vite: Vercel lo sirve sin más configuración que
la carpeta raíz y las dos variables de entorno.

1. En Vercel: **New Project** → importar el repo `POS-UTP`.
2. **Root Directory**: `frontend` (el repo es un monorepo; si se deja la raíz, el
   build falla porque no encuentra `package.json`).
3. Framework: **Vite**, que lo detecta solo. `frontend/vercel.json` fija build,
   salida e instalación igual, para que el deploy no dependa del autodetectado.
4. **Environment Variables** en Production y Preview:
   - `VITE_SALES_URL` → URL pública del sales-service
   - `VITE_STOCK_URL` → URL pública del stock-service

Las `VITE_*` se **hornean en el bundle al compilar**, no se leen en runtime:
si cambia una URL hay que redeployar, no alcanza con guardar la variable.

### Lo que no va a funcionar todavía

- **Front en Vercel contra back local: no.** El navegador bloquea que una página
  HTTPS llame a `http://localhost` (mixed content) y el login falla en la consola.
  Para probar el front desplegado contra el back de tu máquina, publicá los puertos
  por un túnel HTTPS (`cloudflared`, `ngrok`) y poné esas URLs en las variables.
- Cuando el back tenga dominio público, agregalo a `SALES_CORS_ORIGINS` y
  `STOCK_CORS_ORIGINS` (lista separada por comas; `*` no se acepta con
  `POS_ENV=prod`).
- `POS_ENV=prod` exige secretos reales: si quedan los de ejemplo, el arranque
  falla a propósito.

El backend **no** se despliega en Vercel: el modelo serverless choca con el pool de
conexiones a Postgres, los locks de fila de `adjust_stock` y la saga
Sales→Stock con compensación. Su host queda pendiente de decisión.

## Estructura

```text
specs/            # especificaciones SDD (fuente de verdad)
  architecture/ stock/ sales/ frontend/
docs/             # DECISIONS.md, TRACEABILITY.md, ERF-*.md
services/stock-service | services/sales-service
frontend/         # React + Vite (VITE_STOCK_URL, VITE_SALES_URL)
infra/            # docker-compose.yml, postgres/init.sql, e2e_check.py
```

## Reglas

* Sin SPEC aprobada no hay funcionalidad nueva (`.agents/rules/spec-driven-development.md`).
* Fuera de alcance sin ERF: pagos con tarjeta/QR, facturación electrónica, descuentos, brokers.
