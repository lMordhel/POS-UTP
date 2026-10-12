"""AC-AUTH01 (SPEC-AUTH-001 T5): RBAC en Stock — ERF-10, matriz aprobada."""
import pytest


@pytest.mark.integration
def test_no_token_returns_401(client, sample_product):
    """AC-AUTH01-03 en Stock."""
    assert client.get("/api/v1/products").status_code == 401
    assert client.post("/api/v1/products", json={}).status_code == 401
    assert client.patch(
        f"/api/v1/products/{sample_product['id']}/stock", json={"delta": -1}
    ).status_code == 401


@pytest.mark.integration
def test_cashier_reads_ok(client, sample_product, cashier_headers):
    """AC-AUTH01-05 (lectura): cajero consulta catálogo y stock."""
    assert client.get("/api/v1/products", headers=cashier_headers).status_code == 200
    assert client.get(
        f"/api/v1/products/{sample_product['id']}", headers=cashier_headers
    ).status_code == 200
    assert client.get(
        f"/api/v1/products/{sample_product['id']}/stock", headers=cashier_headers
    ).status_code == 200


@pytest.mark.integration
def test_cashier_forbidden_writes_403(client, sample_product, cashier_headers):
    """AC-AUTH01-04: cajero no gestiona productos ni ajusta stock."""
    pid = sample_product["id"]
    assert client.post(
        "/api/v1/products",
        json={"codigo": "X-1", "nombre": "X", "precio": "1.00", "cantidad_inicial": 1},
        headers=cashier_headers,
    ).status_code == 403
    assert client.put(
        f"/api/v1/products/{pid}", json={"nombre": "X"}, headers=cashier_headers
    ).status_code == 403
    assert client.delete(f"/api/v1/products/{pid}", headers=cashier_headers).status_code == 403
    assert client.patch(
        f"/api/v1/products/{pid}/stock", json={"delta": -1}, headers=cashier_headers
    ).status_code == 403


@pytest.mark.integration
def test_admin_writes_ok(client, admin_headers):
    """Admin gestiona catálogo según matriz."""
    resp = client.post(
        "/api/v1/products",
        json={"codigo": "ADM-1", "nombre": "Admin", "precio": "9.99", "cantidad_inicial": 5},
        headers=admin_headers,
    )
    assert resp.status_code == 201
