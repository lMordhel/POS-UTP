"""S3: el cliente HTTP Sales→Stock no puede dejar escapar un error crudo.

Estos tests ejercitan `stock_client.py` de verdad, sin red: `httpx.request` se
reemplaza por un doble que devuelve una respuesta canónica. Antes del fix el
cliente llamaba `raise_for_status()` fuera del `try`, así que un 401/404/422 de
Stock salía como `httpx.HTTPStatusError` y el endpoint lo convertía en 500.
"""
import httpx
import pytest

from app.clients.stock_client import (
    StockClient,
    StockInsufficientError,
    StockProductNotFoundError,
    StockUnavailableError,
)


def _client() -> StockClient:
    return StockClient(base_url="http://stock.test", timeout=1.0, max_retries=2)


@pytest.fixture()
def stock_http(monkeypatch):
    """Doble de `httpx.request`: fija status/cuerpo o lanza, y cuenta llamadas."""
    state: dict = {"calls": 0, "status": 200, "payload": [], "exc": None}

    def fake_request(method, url, **kwargs):
        state["calls"] += 1
        if state["exc"] is not None:
            raise state["exc"]
        return httpx.Response(
            state["status"],
            json=state["payload"],
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    return state


def test_batch_with_401_is_unavailable(stock_http):
    """Un 401 de Stock (credencial de servicio inválida) es 502, no 500."""
    stock_http["status"] = 401
    stock_http["payload"] = {"detail": "credenciales inválidas"}
    with pytest.raises(StockUnavailableError):
        _client().batch_get_products([1])


def test_batch_with_500_is_unavailable(stock_http):
    """Regresión: el 5xx ya se mapeaba y debe seguir mapeándose."""
    stock_http["status"] = 500
    stock_http["payload"] = {"detail": "boom"}
    with pytest.raises(StockUnavailableError):
        _client().batch_get_products([1])


def test_adjust_with_404_is_product_not_found(stock_http):
    """Regresión: 404 → excepción de dominio para responder 404."""
    stock_http["status"] = 404
    stock_http["payload"] = {"detail": "producto inexistente"}
    with pytest.raises(StockProductNotFoundError):
        _client().adjust_stock(7, -1, "venta:1")


def test_adjust_with_409_is_insufficient(stock_http):
    """Regresión: 409 → stock insuficiente (409 en la API de ventas)."""
    stock_http["status"] = 409
    stock_http["payload"] = {"detail": "stock insuficiente: disponible=0, delta=-1"}
    with pytest.raises(StockInsufficientError) as exc:
        _client().adjust_stock(7, -1, "venta:1")
    assert "stock insuficiente" in str(exc.value)


def test_adjust_with_401_is_unavailable(stock_http):
    stock_http["status"] = 401
    stock_http["payload"] = {"detail": "credenciales inválidas"}
    with pytest.raises(StockUnavailableError):
        _client().adjust_stock(7, -1, "venta:1")


def test_adjust_with_unexpected_status_is_unavailable(stock_http):
    """Un 422 de Stock (payload inválido nuestro) tampoco es un 500 crudo."""
    stock_http["status"] = 422
    stock_http["payload"] = {"detail": "delta inválido"}
    with pytest.raises(StockUnavailableError):
        _client().adjust_stock(7, -1, "venta:1")


def test_transient_network_error_retries_then_unavailable(stock_http):
    """Regresión: sigue reintentando sólo fallos de transporte."""
    stock_http["exc"] = httpx.ConnectError("sin ruta al host")
    with pytest.raises(StockUnavailableError):
        _client().batch_get_products([1])
    assert stock_http["calls"] == 2
