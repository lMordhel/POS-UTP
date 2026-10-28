"""AC-SAGA04 (SPEC-SALES-004): idempotencia de ventas y saga robusta — AAA."""
import logging

import pytest


def _post(client, headers, body, key=None):
    extra = dict(headers)
    if key:
        extra["Idempotency-Key"] = key
    return client.post("/api/v1/sales", json=body, headers=extra)


@pytest.mark.integration
def test_replay_returns_same_sale_without_reapplying(client, fake_stock, cashier_headers):
    """AC-SAGA04-01."""
    body = {"items": [{"producto_id": 1, "cantidad": 2}]}
    first = _post(client, cashier_headers, body, key="K-REPLAY")
    assert first.status_code == 201
    sale_id = first.json()["id"]
    calls_after_first = len(fake_stock.adjust_calls)
    second = _post(client, cashier_headers, body, key="K-REPLAY")
    assert second.status_code == 200
    assert second.json()["id"] == sale_id
    assert second.headers.get("idempotent-replayed") == "true"
    assert len(fake_stock.adjust_calls) == calls_after_first
    assert fake_stock.products[1].stock == 100 - 2


@pytest.mark.integration
def test_same_key_different_body_returns_422(client, cashier_headers):
    """AC-SAGA04-02."""
    assert _post(client, cashier_headers, {"items": [{"producto_id": 1, "cantidad": 1}]}, key="K-MISMATCH").status_code == 201
    second = _post(client, cashier_headers, {"items": [{"producto_id": 1, "cantidad": 2}]}, key="K-MISMATCH")
    assert second.status_code == 422
    assert len(client.get("/api/v1/sales", headers=cashier_headers).json()) == 1


@pytest.mark.integration
def test_processing_key_returns_409(client, cashier_headers, db_engine):
    """AC-SAGA04-04 (determinista): marcador en proceso → 409 sin duplicar."""
    from sqlalchemy.orm import sessionmaker

    from app.repositories import idempotency_repository

    Session = sessionmaker(bind=db_engine)
    db = Session()
    idempotency_repository.create_processing(db, "K-BUSY", "hash-x")
    db.commit()
    db.close()
    resp = _post(client, cashier_headers, {"items": [{"producto_id": 1, "cantidad": 1}]}, key="K-BUSY")
    assert resp.status_code == 409
    assert client.get("/api/v1/sales", headers=cashier_headers).json() == []


@pytest.mark.integration
def test_timeout_ambiguity_heals_on_retry(client, fake_stock, cashier_headers):
    """AC-SAGA04-03: aplica-y-falla una vez; el retry con la misma clave cuadra."""
    fake_stock.fail_once_negative = True
    body = {"items": [{"producto_id": 1, "cantidad": 2}]}
    first = _post(client, cashier_headers, body, key="K-TIMEOUT")
    assert first.status_code == 502
    second = _post(client, cashier_headers, body, key="K-TIMEOUT")
    assert second.status_code == 201
    assert fake_stock.products[1].stock == 100 - 2


@pytest.mark.integration
def test_failed_compensation_502_and_log(client, fake_stock, cashier_headers, caplog):
    """AC-SAGA04-05: reverso persistentemente fallido → 502 + log."""
    fake_stock.fail_adjust_ids = {2}
    fake_stock.fail_compensate = True
    body = {"items": [{"producto_id": 1, "cantidad": 1}, {"producto_id": 2, "cantidad": 1}]}
    with caplog.at_level(logging.ERROR):
        resp = _post(client, cashier_headers, body, key="K-COMPENSA")
    assert resp.status_code == 502
    assert any("compensaci" in r.message and "venta" in r.message for r in caplog.records)
    assert client.get("/api/v1/sales", headers=cashier_headers).json() == []


@pytest.mark.integration
def test_product_vanishing_mid_saga_is_404_and_compensates(
    client, fake_stock, cashier_headers
):
    """S3: un producto desactivado entre el batch y el ajuste no deja stock debitado.

    Antes del fix `StockProductNotFoundError` no se capturaba en la saga: la
    excepción subía como 500 y las líneas ya descontadas quedaban debitadas sin
    venta (fuga silenciosa de inventario).
    """
    fake_stock.fail_not_found_ids = {2}
    body = {
        "items": [
            {"producto_id": 1, "cantidad": 2},
            {"producto_id": 2, "cantidad": 1},
        ]
    }
    resp = _post(client, cashier_headers, body, key="K-NOTFOUND")
    assert resp.status_code == 404
    assert client.get("/api/v1/sales", headers=cashier_headers).json() == []
    # La línea 1 ya se había descontado: la compensación la devuelve.
    assert fake_stock.products[1].stock == 100


@pytest.mark.integration
def test_unexpected_error_during_discount_compensates(
    client, fake_stock, cashier_headers
):
    """S3: cualquier fallo no previsto compensa antes de propagarse."""
    fake_stock.fail_unexpected_ids = {2}
    body = {
        "items": [
            {"producto_id": 1, "cantidad": 2},
            {"producto_id": 2, "cantidad": 1},
        ]
    }
    with pytest.raises(RuntimeError):
        _post(client, cashier_headers, body, key="K-UNEXPECTED")
    assert fake_stock.products[1].stock == 100
    assert client.get("/api/v1/sales", headers=cashier_headers).json() == []
