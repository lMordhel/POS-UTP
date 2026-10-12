"""AC-BATCH06 (SPEC-STOCK-006): lectura por lote — AAA."""
import pytest


@pytest.mark.integration
def test_batch_returns_found_with_stock_in_order(client, sample_product, admin_headers):
    """AC-BATCH06-01: encontrados con stock, orden de petición, dedupe."""
    second = client.post(
        "/api/v1/products",
        json={"codigo": "B-2", "nombre": "B", "precio": "3.00", "cantidad_inicial": 7},
        headers=admin_headers,
    ).json()
    resp = client.post(
        "/api/v1/products/batch",
        json={"ids": [second["id"], sample_product["id"], 9999, second["id"]]},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [i["id"] for i in body] == [second["id"], sample_product["id"]]
    by_id = {i["id"]: i for i in body}
    assert by_id[second["id"]]["stock"] == 7
    assert by_id[sample_product["id"]]["stock"] == sample_product["stock"]


@pytest.mark.integration
@pytest.mark.parametrize(
    "payload",
    [{"ids": []}, {"ids": [0]}, {"ids": [-1]}, {"ids": ["x"]}, {}],
    ids=["empty", "zero", "negative", "string", "missing"],
)
def test_batch_invalid_returns_422(client, admin_headers, payload):
    """AC-BATCH06-02 (parte 1)."""
    assert client.post("/api/v1/products/batch", json=payload, headers=admin_headers).status_code == 422


@pytest.mark.integration
def test_batch_over_limit_returns_422(client, admin_headers):
    """AC-BATCH06-02 (tope 100)."""
    assert client.post(
        "/api/v1/products/batch", json={"ids": list(range(1, 102))}, headers=admin_headers
    ).status_code == 422


@pytest.mark.integration
def test_batch_rbac(client, admin_headers, cashier_headers):
    """AC-BATCH06-03: igual que lecturas (401/403/200)."""
    assert client.post("/api/v1/products/batch", json={"ids": [1]}).status_code == 401
    assert client.post(
        "/api/v1/products/batch", json={"ids": [1]}, headers=cashier_headers
    ).status_code == 200
    assert client.post(
        "/api/v1/products/batch", json={"ids": [1]}, headers=admin_headers
    ).status_code == 200
