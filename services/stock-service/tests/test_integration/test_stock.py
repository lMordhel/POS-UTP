"""AC-ERF04/ERF05 tests for SPEC-STOCK-002/003 (GET stock + PATCH delta)."""

import pytest


@pytest.mark.integration
def test_get_stock_existing(client, sample_product):
    """AC-ERF04-01: stock existente → 200 con cantidad y updated_at."""
    response = client.get(f"/api/v1/products/{sample_product['id']}/stock")
    assert response.status_code == 200
    body = response.json()
    assert body["producto_id"] == sample_product["id"]
    assert body["cantidad"] == sample_product["stock"]


@pytest.mark.integration
def test_get_stock_unknown_id_returns_404(client):
    """AC-ERF04-02."""
    assert client.get("/api/v1/products/9999/stock").status_code == 404


@pytest.mark.integration
def test_adjust_stock_delta_decrements_and_returns_updated(client, sample_product):
    """AC-ERF05-01: delta válido → inventario actualizado."""
    start = sample_product["stock"]
    response = client.patch(
        f"/api/v1/products/{sample_product['id']}/stock",
        json={"delta": -30, "motivo": "venta"},
    )
    assert response.status_code == 200
    assert response.json()["cantidad"] == start - 30

    response = client.patch(
        f"/api/v1/products/{sample_product['id']}/stock",
        json={"delta": 10, "motivo": "ajuste"},
    )
    assert response.json()["cantidad"] == start - 20


@pytest.mark.integration
def test_adjust_stock_unknown_id_returns_404(client):
    """AC-ERF05-02."""
    response = client.patch("/api/v1/products/9999/stock", json={"delta": -1})
    assert response.status_code == 404


@pytest.mark.integration
def test_adjust_stock_below_zero_returns_409_without_changes(client, sample_product):
    """AC-ERF05-03: resultado negativo → 409 sin modificar."""
    response = client.patch(
        f"/api/v1/products/{sample_product['id']}/stock",
        json={"delta": -(sample_product["stock"] + 1)},
    )
    assert response.status_code == 409
    check = client.get(f"/api/v1/products/{sample_product['id']}/stock")
    assert check.json()["cantidad"] == sample_product["stock"]


@pytest.mark.integration
@pytest.mark.parametrize("payload", [{"delta": 0}, {}], ids=["zero-delta", "empty-body"])
def test_adjust_stock_invalid_returns_422(client, sample_product, payload):
    assert (
        client.patch(
            f"/api/v1/products/{sample_product['id']}/stock", json=payload
        ).status_code
        == 422
    )
