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

## Historial

| Fecha | Cambio |
|---|---|
| 2026-09-29 | Frontend Vite IMPLEMENTED (SPEC-FRONT-001): productos/venta/ventas sobre APIs reales, build verde, serve 200; demo manual AC-FRONT-01 pendiente |
| 2026-09-29 | Fase 3: infra/docker-compose.yml + Dockerfiles + init.sql (ventas_db/stock_db); E2E real Ventas→Stock por HTTP en verde (infra/e2e_check.py); docker CLI no disponible en esta máquina, compose entregado sin ejecutar |
| 2026-09-29 | SPEC-SALES-001/002/003 1.0.0 APPROVED → VALIDATED (13/13 pytest); OQ-ERF03-01 (fusión) y OQ-ARCH-01 (sin estados) DECIDED; backend ERF-01..08 completo |
| 2026-09-29 | SPEC-STOCK-001/002/003/005 1.0.0 APPROVED → VALIDATED (25/25 pytest); stock-service completa ERF-02/04/05/06/08 |
| 2026-09-29 | SPEC-STOCK-004 0.1.0 → 1.0.0 APPROVED; ADR-002 y ADR-005 PROPOSED → APPROVED; OQ-ERF02-01, OQ-ERF05-01, OQ-ERF01-01 DECIDED |
