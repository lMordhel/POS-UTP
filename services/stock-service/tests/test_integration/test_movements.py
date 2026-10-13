"""AC-AUDV07 (SPEC-STOCK-007): lectura de auditoría — AAA."""
import pytest


def _adjust(client, admin_headers, pid, delta, motivo="venta:1", key=None):
    headers = dict(admin_headers)
    if key:
        headers["Idempotency-Key"] = key
    return client.patch(
        f"/api/v1/products/{pid}/stock", json={"delta": delta, "motivo": motivo}, headers=headers
    )


@pytest.mark.integration
def test_movements_list_with_snapshot(client, sample_product, admin_headers):
    """AC-AUDV07-01."""
    assert _adjust(client, admin_headers, sample_product["id"], -4, "merma").status_code == 200
    resp = client.get("/api/v1/stock/movements", headers=admin_headers)
    assert resp.status_code == 200
    (row,) = resp.json()
    assert row["producto_id"] == sample_product["id"]
    assert row["codigo"] == sample_product["codigo"]
    assert row["nombre"] == sample_product["nombre"]
    assert row["delta"] == -4 and row["cantidad_antes"] == sample_product["stock"]
    assert row["cantidad_despues"] == sample_product["stock"] - 4
    assert row["motivo"] == "merma"
    assert row["actor_sub"] == "1" and row["actor_rol"] == "admin"


@pytest.mark.integration
def test_movements_filter_and_paging(client, sample_product, admin_headers):
    """AC-AUDV07-02."""
    other = client.post(
        "/api/v1/products",
        json={"codigo": "M-2", "nombre": "M", "precio": "2.00", "cantidad_inicial": 50},
        headers=admin_headers,
    ).json()
    for _ in range(3):
        _adjust(client, admin_headers, sample_product["id"], -1)
    _adjust(client, admin_headers, other["id"], -1)
    filtered = client.get(
        f"/api/v1/stock/movements?producto_id={other['id']}", headers=admin_headers
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert all(r["producto_id"] == other["id"] for r in filtered.json())
    page1 = client.get("/api/v1/stock/movements?skip=0&limit=2", headers=admin_headers)
    page2 = client.get("/api/v1/stock/movements?skip=2&limit=2", headers=admin_headers)
    assert len(page1.json()) == 2 and len(page2.json()) == 2
    ids1 = [r["id"] for r in page1.json()]
    ids2 = [r["id"] for r in page2.json()]
    assert not set(ids1) & set(ids2)
    assert ids1 == sorted(ids1, reverse=True)


@pytest.mark.integration
def test_movements_rbac(client, admin_headers, cashier_headers):
    """AC-AUDV07-03."""
    assert client.get("/api/v1/stock/movements").status_code == 401
    assert client.get("/api/v1/stock/movements", headers=cashier_headers).status_code == 403
    assert client.get("/api/v1/stock/movements", headers=admin_headers).status_code == 200
