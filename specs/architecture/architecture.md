# Architecture — POS-UTP (SPEC de arquitectura, Status: DRAFT)

## Metadata

- ID: SPEC-ARCH-001
- Requirement: Transversal (ERF-01..ERF-08)
- Service: Stock + Sales + Frontend (futuro)
- Status: DRAFT
- Version: 0.1.0
- Priority: Alta

## Objective

Fijar la arquitectura inicial del Sistema de Ventas para Microempresas (POS):
dos microservicios FastAPI independientes (Stock y Sales), comunicación
Ventas → Stock por HTTP, sin API Gateway en Fase 1, con propiedad de datos
estricta sobre PostgreSQL (dos bases lógicas).

## Scope

* Servicio `stock-service`: productos, inventario, consulta/actualización de stock.
* Servicio `sales-service`: ventas y detalles de venta; consume a Stock por HTTP.
* Contratos bajo prefijo `/api/v1` (convención `fastapi-templates`).
* Frontend React/Vite posterior, consumiendo ambas APIs directamente.
* Trazabilidad ERF → SPEC → endpoint (ver `docs/TRACEABILITY.md`).

## Out of Scope

Auth/JWT, roles, pagos, facturación electrónica, clientes, descuentos,
promociones, Redis/Kafka/RabbitMQ, Kubernetes, Elasticsearch, API Gateway
(ver ADR-001). Nada de esto tiene ERF que lo respalde.

## Diagrama

```text
Frontend Vite ──HTTP──► Sales (:8001) ──HTTP──► Stock (:8002)
     │                       │                        │
     └───────── lectura catálogo directa a Stock ─────┘
                                 │                        │
                            ventas_db                  stock_db
                     (misma instancia PG, DBs lógicas separadas)
```

## Decisiones (resumen; detalle en docs/DECISIONS.md, todas PROPOSED)

* ADR-001: sin API Gateway inicialmente (YAGNI, 2 servicios).
* ADR-002: propiedad de datos — Stock: productos+inventario;
  Sales: ventas+detalles. Sin FK físicas cross-DB; `producto_id` en Ventas es
  referencia lógica.
* ADR-003: comunicación Ventas → Stock por HTTP (httpx, timeout, errores
  tipados; reintento solo en fallos transitorios).
* ADR-004: PostgreSQL, una instancia, dos databases (`ventas_db`, `stock_db`),
  conexiones y migraciones separadas.
* ADR-005: stock en tabla `inventories` separada (`producto_id` único,
  `cantidad >= 0`), NO como columna de `Producto` (dominio: Producto,
  Inventario y Stock son clases separadas).

## Capas por servicio (skill fastapi-templates)

```text
main.py (delgado: lifespan + CORS + include router)
core/{config.py,database.py} (Settings via pydantic-settings, get_db con Depends)
api/v1/{router.py,endpoints/*.py} (routers delgados, mapean HTTPException)
schemas/*.py (Pydantic Create/Update/Read)
services/*.py (reglas de negocio)
repositories/*.py (acceso a datos)
clients/stock_client.py (solo en Sales)
tests/{conftest.py,test_unit/,test_integration/}
```

## Saga de venta (sin orquestador pesado)

1. Sales valida líneas (cantidad > 0, producto existe vía Stock).
2. Sales verifica disponibilidad (ERF-04).
3. Sales crea la venta (estado inicial `confirmada` solo tras descuento, o
   `fallida` si Stock falla — detalle en SPEC-SALES-001).
4. Sales descuenta stock vía `PATCH` (ERF-05).
5. Ante fallo de Stock: responder 409/502 según caso y no dejar venta
   confirmada huérfana.

## Open Questions

* OQ-ARCH-01: ¿Saga con estados `pendiente/confirmada/fallida` o transacción
  simple con rollback? Afecta a SPEC-SALES-001.
* OQ-ARCH-02: ¿Confirmar gateway diferido a Fase 4+ o descartarlo del acta?

## Traceability

Requirement: Transversal ERF-01..ERF-08.
Endpoint: No aplica en el alcance actual (documento de arquitectura).
Service: Stock, Sales. Tests: No aplica (se valida por revisión).

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 0.1.0 | 2026-09-29 | Initial architecture draft | Initial SDD setup |
