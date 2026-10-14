"""AC-CLI05-01..07 (SPEC-SALES-005): cliente + pago en efectivo — AAA."""

from decimal import Decimal

import pytest

TOTAL_2x1_1x2 = Decimal("26.00")  # 10.50*2 + 5.00


@pytest.mark.integration
def test_ac01_venta_cliente_efectivo_con_vuelto(client, fake_stock, cashier_headers):
    """AC-CLI05-01: cliente + monto > total → 201, vuelto persistido, stock descontado."""
    resp = client.post(
        "/api/v1/sales",
        json={
            "items": [{"producto_id": 1, "cantidad": 2}, {"producto_id": 2, "cantidad": 1}],
            "cliente": "Juan Pérez",
            "monto_recibido": "30.00",
        },
        headers=cashier_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["cliente"] == "Juan Pérez"
    assert Decimal(str(body["monto_recibido"])) == Decimal("30.00")
    assert Decimal(str(body["vuelto"])) == Decimal("30.00") - TOTAL_2x1_1x2
    assert fake_stock.products[1].stock == 98
    assert fake_stock.products[2].stock == 2


@pytest.mark.integration
def test_ac02_monto_insuficiente_422_sin_venta_ni_stock(client, fake_stock, cashier_headers):
    """AC-CLI05-02: monto < total → 422, sin venta ni toque de stock."""
    resp = client.post(
        "/api/v1/sales",
        json={
            "items": [{"producto_id": 1, "cantidad": 2}, {"producto_id": 2, "cantidad": 1}],
            "monto_recibido": "25.99",
        },
        headers=cashier_headers,
    )
    assert resp.status_code == 422, resp.text
    assert fake_stock.adjust_calls == []
    assert fake_stock.products[1].stock == 100
    assert client.get("/api/v1/sales", headers=cashier_headers).json() == []


@pytest.mark.integration
def test_ac03_sin_cliente_ni_monto_compat_201_nulls(client, cashier_headers):
    """AC-CLI05-03: solo items (SPEC-SALES-001) → 201 con nulls."""
    resp = client.post(
        "/api/v1/sales",
        json={"items": [{"producto_id": 1, "cantidad": 1}]},
        headers=cashier_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["cliente"] is None
    assert body["monto_recibido"] is None
    assert body["vuelto"] is None


@pytest.mark.integration
def test_ac04_cliente_solo_espacios_normaliza_null(client, cashier_headers):
    """AC-CLI05-04a: cliente solo-espacios → null (venta 201)."""
    resp = client.post(
        "/api/v1/sales",
        json={"items": [{"producto_id": 1, "cantidad": 1}], "cliente": "   "},
        headers=cashier_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["cliente"] is None


@pytest.mark.integration
def test_ac04_cliente_mas_120_422(client, fake_stock, cashier_headers):
    """AC-CLI05-04b: cliente > 120 → 422 sin venta."""
    resp = client.post(
        "/api/v1/sales",
        json={"items": [{"producto_id": 1, "cantidad": 1}], "cliente": "x" * 121},
        headers=cashier_headers,
    )
    assert resp.status_code == 422, resp.text
    assert client.get("/api/v1/sales", headers=cashier_headers).json() == []


@pytest.mark.integration
def test_ac04_vuelto_en_request_422(client, cashier_headers):
    """FR-03/Validation: vuelto jamás viene del request → 422."""
    resp = client.post(
        "/api/v1/sales",
        json={
            "items": [{"producto_id": 1, "cantidad": 1}],
            "monto_recibido": "20.00",
            "vuelto": "9.50",
        },
        headers=cashier_headers,
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.integration
def test_ac05_idempotencia_cubre_cliente_y_monto(client, cashier_headers):
    """AC-CLI05-05: misma K + mismo cuerpo → replay; K con distinto cliente/monto → 422."""
    body = {
        "items": [{"producto_id": 1, "cantidad": 1}],
        "cliente": "Ana",
        "monto_recibido": "20.00",
    }
    headers = dict(cashier_headers, **{"Idempotency-Key": "K-CLI05"})
    first = client.post("/api/v1/sales", json=body, headers=headers)
    assert first.status_code == 201, first.text
    sale_id = first.json()["id"]
    second = client.post("/api/v1/sales", json=body, headers=headers)
    assert second.status_code == 200
    assert second.json()["id"] == sale_id
    assert second.headers.get("idempotent-replayed") == "true"
    other_cliente = dict(body, cliente="Beto")
    assert client.post("/api/v1/sales", json=other_cliente, headers=headers).status_code == 422
    other_monto = dict(body, monto_recibido="25.00")
    assert client.post("/api/v1/sales", json=other_monto, headers=headers).status_code == 422
    assert len(client.get("/api/v1/sales", headers=cashier_headers).json()) == 1


@pytest.mark.integration
def test_ac06_pago_exacto_vuelto_cero(client, cashier_headers):
    """AC-CLI05-06: monto == total → 201 con vuelto = 0 (no null)."""
    resp = client.post(
        "/api/v1/sales",
        json={
            "items": [{"producto_id": 1, "cantidad": 2}, {"producto_id": 2, "cantidad": 1}],
            "monto_recibido": "26.00",
        },
        headers=cashier_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert Decimal(str(body["vuelto"])) == Decimal("0")


@pytest.mark.integration
def test_ac07_lectura_expone_cliente_y_pago(client, cashier_headers):
    """AC-CLI05-07: GET /sales/{id} incluye cliente, monto_recibido y vuelto."""
    created = client.post(
        "/api/v1/sales",
        json={
            "items": [{"producto_id": 1, "cantidad": 1}],
            "cliente": "  Juan Pérez  ",
            "monto_recibido": "20.00",
        },
        headers=cashier_headers,
    )
    assert created.status_code == 201, created.text
    sale_id = created.json()["id"]
    detail = client.get(f"/api/v1/sales/{sale_id}", headers=cashier_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["cliente"] == "Juan Pérez"
    assert Decimal(str(body["monto_recibido"])) == Decimal("20.00")
    assert Decimal(str(body["vuelto"])) == Decimal("20.00") - Decimal("10.50")
