"""AC-HARD02 no; AC-SAGA04 (SPEC-SALES-004): idempotencia en Stock — AAA."""
import pytest


@pytest.mark.integration
def test_keyed_replay_does_not_reapply(client, sample_product, admin_headers):
    """AC-SAGA04-03 (lado Stock): misma clave, distinto delta → registrado."""
    pid = sample_product["id"]
    url = f"/api/v1/products/{pid}/stock"
    first = client.patch(url, json={"delta": -10, "motivo": "venta:1"},
                         headers={**admin_headers, "Idempotency-Key": "K-1"})
    assert first.status_code == 200
    start = sample_product["stock"]
    assert first.json()["cantidad"] == start - 10
    replay = client.patch(url, json={"delta": -99, "motivo": "otro"},
                          headers={**admin_headers, "Idempotency-Key": "K-1"})
    assert replay.status_code == 200
    assert replay.json()["cantidad"] == start - 10
    check = client.get(url, headers=admin_headers)
    assert check.json()["cantidad"] == start - 10


@pytest.mark.integration
def test_unkeyed_adjust_unchanged(client, sample_product, admin_headers):
    """Sin clave: comportamiento actual."""
    pid = sample_product["id"]
    resp = client.patch(f"/api/v1/products/{pid}/stock",
                        json={"delta": -5, "motivo": "venta"},
                        headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["cantidad"] == sample_product["stock"] - 5
