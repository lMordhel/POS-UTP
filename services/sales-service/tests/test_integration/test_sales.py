"""AC-ERF01/03/07 tests for SPEC-SALES-001/002/003 (skill python-testing-patterns)."""

from decimal import Decimal

import pytest


@pytest.mark.integration
def test_register_sale_valid_calculates_total_and_discounts_stock(client, fake_stock, cashier_headers):
    """AC-ERF01-01: venta válida → 201, total=Σ subtotales, stock descontado."""
    response = client.post(
        "/api/v1/sales",
        json={"items": [{"producto_id": 1, "cantidad": 2}, {"producto_id": 2, "cantidad": 1}]},
        headers=cashier_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["estado"] == "confirmada"
    assert Decimal(str(body["total"])) == Decimal("10.50") * 2 + Decimal("5.00")
    assert fake_stock.products[1].stock == 98
    assert fake_stock.products[2].stock == 2
    lines = {i["producto_id"]: i for i in body["items"]}
    assert lines[1]["precio_unitario"] == "10.50" or Decimal(str(lines[1]["precio_unitario"])) == Decimal("10.50")
    assert Decimal(str(lines[1]["subtotal"])) == Decimal("21.00")


@pytest.mark.integration
def test_register_sale_insufficient_stock_returns_409_without_sale(client, fake_stock, cashier_headers):
    """AC-ERF01-02: sin stock → 409, sin venta confirmada, sin descuentos."""
    response = client.post("/api/v1/sales", json={"items": [{"producto_id": 2, "cantidad": 10}]}, headers=cashier_headers)
    assert response.status_code == 409
    assert fake_stock.products[2].stock == 3
    assert fake_stock.adjust_calls == []
    assert client.get("/api/v1/sales", headers=cashier_headers).json() == []


@pytest.mark.integration
def test_register_sale_unknown_product_returns_404(client, cashier_headers):
    """AC-ERF01-03 / AC-ERF03-03."""
    response = client.post("/api/v1/sales", json={"items": [{"producto_id": 999, "cantidad": 1}]}, headers=cashier_headers)
    assert response.status_code == 404


@pytest.mark.integration
def test_register_sale_inactive_product_returns_404(client, cashier_headers):
    """AC-ERF01-03 / AC-ERF03-03."""
    response = client.post("/api/v1/sales", json={"items": [{"producto_id": 3, "cantidad": 1}]}, headers=cashier_headers)
    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.parametrize(
    "payload",
    [
        {"items": []},
        {"items": [{"producto_id": 1, "cantidad": 0}]},
        {"items": [{"producto_id": 1, "cantidad": -2}]},
        {"items": [{"producto_id": 0, "cantidad": 1}]},
        {},
    ],
    ids=["empty", "zero-qty", "negative-qty", "zero-id", "no-items"],
)
def test_register_sale_invalid_returns_422(client, cashier_headers, payload):
    """AC-ERF01-04 / AC-ERF03-02."""
    assert client.post("/api/v1/sales", json=payload, headers=cashier_headers).status_code == 422


@pytest.mark.integration
def test_sale_lines_snapshot_prices_and_subtotals(client, cashier_headers):
    """AC-ERF03-01: snapshot de precio + subtotal=cantidad×precio."""
    response = client.post("/api/v1/sales", json={"items": [{"producto_id": 1, "cantidad": 3}]}, headers=cashier_headers)
    assert response.status_code == 201
    (line,) = response.json()["items"]
    assert Decimal(str(line["precio_unitario"])) == Decimal("10.50")
    assert Decimal(str(line["subtotal"])) == Decimal("31.50")


@pytest.mark.integration
def test_duplicate_lines_are_merged(client, fake_stock, cashier_headers):
    """OQ-ERF03-01 DECIDED: duplicados se fusionan sumando cantidades."""
    response = client.post(
        "/api/v1/sales",
        json={"items": [{"producto_id": 1, "cantidad": 2}, {"producto_id": 1, "cantidad": 3}]},
        headers=cashier_headers,
    )
    assert response.status_code == 201
    (line,) = response.json()["items"]
    assert line["cantidad"] == 5
    assert Decimal(str(line["subtotal"])) == Decimal("52.50")
    assert fake_stock.products[1].stock == 95


@pytest.mark.integration
def test_stock_unavailable_returns_502_without_sale(client, fake_stock, cashier_headers):
    """Stock caído → 502, sin venta persistida."""
    fake_stock.fail_unavailable = True
    response = client.post("/api/v1/sales", json={"items": [{"producto_id": 1, "cantidad": 1}]}, headers=cashier_headers)
    assert response.status_code == 502
    assert client.get("/api/v1/sales", headers=cashier_headers).json() == []


@pytest.mark.integration
def test_list_and_get_sale(client, cashier_headers):
    """AC-ERF07-01/02/03."""
    created = client.post("/api/v1/sales", json={"items": [{"producto_id": 1, "cantidad": 1}]}, headers=cashier_headers)
    sale_id = created.json()["id"]
    listing = client.get("/api/v1/sales", headers=cashier_headers)
    assert listing.status_code == 200 and len(listing.json()) == 1
    detail = client.get(f"/api/v1/sales/{sale_id}", headers=cashier_headers)
    assert detail.status_code == 200
    assert len(detail.json()["items"]) == 1
    assert client.get("/api/v1/sales/9999", headers=cashier_headers).status_code == 404
