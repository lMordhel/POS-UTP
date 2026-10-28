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
servicio; `infra/.env` alimenta al compose. Ninguno se versiona (ver
`.gitignore`): esto es el inventario de lo que acepta cada uno.

| Variable | Servicio | Default | Para qué |
| --- | --- | --- | --- |
| `POS_ENV` | ambos | `dev` | `prod` desactiva `/docs` y activa el fail-fast de secretos |
| `POS_LOG_LEVEL` | ambos | `INFO` | nivel del root logger |
| `SALES_DATABASE_URL` / `STOCK_DATABASE_URL` | sales / stock | `sqlite:///./*.db` | Postgres en compose |
| `SALES_STOCK_SERVICE_URL` | sales | `http://localhost:8002` | cliente Sales→Stock (ADR-003) |
| `SALES_STOCK_TIMEOUT_SECONDS` | sales | `5.0` | timeout del cliente |
| `SALES_JWT_SECRET` / `STOCK_JWT_SECRET` | sales / stock | `change-me-dev-only` | **mismo valor**: Sales firma el token de servicio que Stock verifica (ADR-008) |
| `SALES_JWT_ALGORITHM` | ambos | `HS256` | algoritmo de firma |
| `SALES_ACCESS_TOKEN_MINUTES` | sales | `15` | vida del access token |
| `SALES_REFRESH_TOKEN_DAYS` | sales | `7` | vida del refresh token |
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
