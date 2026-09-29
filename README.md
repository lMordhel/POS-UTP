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
* **sales-service** (FastAPI): ventas y detalles; valida precios/stock y descuenta vía HTTP a Stock → ERF-01/03/07.
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

## Demo en 1 minuto

1. Stock docs → `POST /products` (ej. `{"codigo":"DEMO-1","nombre":"Café","precio":"25.90","cantidad_inicial":50}`).
2. Frontend → Nueva venta → Agregar → Confirmar → total del servidor.
3. Verificar stock descontado y venta en la pestaña Ventas.

## Tests

```powershell
cd services/stock-service; py -m pytest tests -q   # 25 tests
cd ../sales-service; py -m pytest tests -q          # 13 tests
cd ../..; py infra/e2e_check.py                     # E2E real Ventas→Stock
```

## Estructura

```text
specs/            # especificaciones SDD (fuente de verdad)
  architecture/ stock/ sales/ frontend/
docs/             # DECISIONS.md, TRACEABILITY.md
services/stock-service | services/sales-service
frontend/         # React + Vite (VITE_STOCK_URL, VITE_SALES_URL)
infra/            # docker-compose.yml, postgres/init.sql, e2e_check.py
```

## Reglas

* Sin SPEC aprobada no hay funcionalidad nueva (`.agents/rules/spec-driven-development.md`).
* Fuera de alcance sin ERF: auth, pagos/QR, facturación, descuentos, brokers.
