# ERF-11 — Venta con cliente y pago en efectivo

> Documento de trabajo para trasladar al documento académico (`.docx`).
> Estado: implementado y validado con SPEC-SALES-005 1.1.0 (VALIDATED).
> Base: SPEC-SALES-001 excluye vuelto/pago/cliente y exige ERF nuevo
> (OQ-ERF01-01); SPEC-SALES-005 lo especifica (DRAFT, sin implementar).

## Contexto

El ticket actual no identifica al comprador y la caja no registra
efectivo/vuelto: `Sale` (`app/models/sale.py`) solo guarda `total` y
`estado`. ERF-11 cierra esa brecha en Fase 2 (solo efectivo, sin frontend
en esta fase) sin romper lo validado: precios y totales siguen calculados
server-side desde Stock, y la idempotencia/saga (SPEC-SALES-004) queda intacta.

Decisión del usuario (2026-10-14): Fase 2 con solo efectivo, modo backend
clásico (SPEC + gate + TDD) para que nada se rompa.

---

## ERF-11 — Venta con cliente y pago en efectivo

**Descripción:** el sistema debe registrar ventas identificando al comprador
(texto libre opcional) y cerrando el cobro en efectivo: dado un monto
recibido, el servidor calcula y persiste el vuelto, rechazando el pago
insuficiente antes de confirmar la venta.

**Alcance:**
- `cliente` opcional en `POST /api/v1/sales` (texto libre; normalizado con
  `strip()`; vacío → `null`; máx. 120 caracteres propuesto).
- `monto_recibido` opcional (decimal ≥ 0, 2 decimales); ausente → venta sin
  pago registrado (compatibilidad con ERF-01).
- `vuelto = monto_recibido − total` calculado y persistido server-side; el
  request nunca lo envía; pago exacto válido (`vuelto = 0`).
- Lectura (`GET /sales`, `GET /sales/{id}`) expone `cliente`,
  `monto_recibido`, `vuelto`.
- Migración lineal solo con columnas nullable (baseline intacta, un head).
- Idempotencia ampliada a cliente + monto (mismo negocio → replay;
  distinto → 422).

**Fuera de alcance:** impuestos, descuentos, facturación, cobro QR u otros
medios, frontend, expiración/purga de claves de idempotencia.

**Endpoints principales:**
- `POST /api/v1/sales` (+ `cliente`, `monto_recibido` opcionales) →
  201 `{id, fecha, total, estado, cliente, monto_recibido, vuelto, items}` /
  404 / 409 / 422 (incluye monto < total) / 502.
- `GET /api/v1/sales`, `GET /api/v1/sales/{id}` → incluyen los tres campos.

**Criterios de aceptación:**
1. Cliente + monto mayor al total → 201 con `vuelto` calculado y stock
   descontado (AC-CLI05-01).
2. Monto menor al total → 422 sin venta ni movimiento de stock (AC-CLI05-02).
3. Cuerpo solo con `items` → 201 con los tres campos en `null` (AC-CLI05-03).
4. Cliente inválido → vacío normalizado a `null`, >120 → 422 (AC-CLI05-04,
   detalle al gate).
5. Misma clave + mismo cliente/monto → replay; distinto → 422 (AC-CLI05-05).
6. Monto igual al total → 201 con `vuelto = 0` (AC-CLI05-06).
7. Lectura de la venta → expone cliente y pago persistidos (AC-CLI05-07).

**Trazabilidad:** SPEC-SALES-005 (AC-CLI05-01..07). Tests pendientes
(SALE-EFE-03, TDD): venta con vuelto, monto insuficiente 422,
compatibilidad sin cliente, cliente inválido, idempotencia con
cliente/monto, pago exacto, lectura.

---

## Relación con ERF-01..ERF-10

ERF-11 no cambia el negocio validado: ERF-01/03/07 se comportan igual cuando
no se envían cliente/monto (AC-CLI05-03); la saga e idempotencia (Fase 3)
solo amplían su hash. ERF-09/10 no se ven afectados (mismo modelo de
identidad y permisos). Se crea como ERF nuevo —no enmienda de ERF-01—
porque SPEC-SALES-001 está VALIDATED y excluyó el cobro explícitamente.

## Pendiente para el `.docx`

- [ ] Revisar textos y criterios con el docente/equipo (gate SALE-EFE-02,
  OQ-CLI05-01..06 con recomendación en la SPEC).
- [ ] Numerar como ERF-11 en el documento académico.
- [ ] Adjuntar evidencias si se piden (SPEC-SALES-005 VALIDATED + pytest en
  verde tras SALE-EFE-03/04).
