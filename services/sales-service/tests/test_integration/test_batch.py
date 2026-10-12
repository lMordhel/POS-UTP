"""AC-BATCH06-04 (SPEC-STOCK-006): la saga usa una sola lectura batch — AAA."""
import pytest


@pytest.mark.integration
def test_register_sale_uses_single_batch_read(client, fake_stock, cashier_headers):
    """Venta de 2 productos → 1 batch + 2 ajustes (no 4 lecturas + 2 ajustes)."""
    resp = client.post(
        "/api/v1/sales",
        json={"items": [{"producto_id": 1, "cantidad": 1}, {"producto_id": 2, "cantidad": 1}]},
        headers=cashier_headers,
    )
    assert resp.status_code == 201
    assert len(fake_stock.batch_calls) == 1
    assert sorted(fake_stock.batch_calls[0]) == [1, 2]
