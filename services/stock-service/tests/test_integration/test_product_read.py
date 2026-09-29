"""AC-ERF02/ERF08 tests for SPEC-STOCK-001/005 (listado, filtros, paginación, detalle)."""

import pytest


def _create(client, codigo, nombre="N", precio="5.00", cantidad=10, activo=True):
    resp = client.post(
        "/api/v1/products",
        json={
            "codigo": codigo,
            "nombre": nombre,
            "precio": precio,
            "cantidad_inicial": cantidad,
        },
    )
    assert resp.status_code == 201
    pid = resp.json()["id"]
    if not activo:
        assert client.delete(f"/api/v1/products/{pid}").status_code == 200
    return pid


@pytest.mark.integration
def test_list_products_returns_stock_aggregated(client, sample_product):
    """AC-ERF02-01 / AC-ERF08-01: lista con stock agregado."""
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    items = response.json()
    assert any(
        i["id"] == sample_product["id"] and i["stock"] == sample_product["stock"]
        for i in items
    )


@pytest.mark.integration
def test_list_products_pagination(client):
    for n in range(5):
        _create(client, f"P-PG-{n}")
    page1 = client.get("/api/v1/products?skip=0&limit=2")
    page2 = client.get("/api/v1/products?skip=2&limit=2")
    assert page1.status_code == 200 and page2.status_code == 200
    assert len(page1.json()) == 2 and len(page2.json()) == 2
    assert {i["id"] for i in page1.json()} != {i["id"] for i in page2.json()}


@pytest.mark.integration
def test_list_products_invalid_pagination_returns_422(client):
    assert client.get("/api/v1/products?limit=0").status_code == 422
    assert client.get("/api/v1/products?limit=101").status_code == 422
    assert client.get("/api/v1/products?skip=-1").status_code == 422


@pytest.mark.integration
def test_list_products_filter_by_text_and_activo(client, sample_product):
    """AC-ERF02-02: filtros q y activo."""
    pid_off = _create(client, "P-OFF-1", nombre="Apagado", activo=False)
    by_text = client.get("/api/v1/products?q=P-001")
    assert by_text.status_code == 200
    assert all("P-001" in i["codigo"] for i in by_text.json())

    inactive = client.get("/api/v1/products?activo=false")
    assert inactive.status_code == 200
    ids = {i["id"] for i in inactive.json()}
    assert pid_off in ids and sample_product["id"] not in ids


@pytest.mark.integration
def test_get_product_detail_includes_stock(client, sample_product):
    response = client.get(f"/api/v1/products/{sample_product['id']}")
    assert response.status_code == 200
    assert response.json()["stock"] == sample_product["stock"]


@pytest.mark.integration
def test_inventory_info_empty_returns_200_list(client):
    """AC-ERF08-02: sin productos → 200 con []."""
    assert client.get("/api/v1/products").status_code == 200
    assert client.get("/api/v1/products").json() == []
