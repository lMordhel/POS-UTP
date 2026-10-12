"""AC-HARD02 (SPEC-AUTH-002): CORS, rate limiting, headers y config — AAA."""
import importlib

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.core.config import get_settings


def _origin_headers(origin, method="POST"):
    return {"Origin": origin, "Access-Control-Request-Method": method}


@pytest.mark.integration
def test_cors_forbids_unknown_origin(client):
    """AC-HARD02-01."""
    resp = client.options("/api/v1/products", headers=_origin_headers("http://evil.test"))
    assert "access-control-allow-origin" not in resp.headers


@pytest.mark.integration
def test_cors_allows_frontend(client):
    """AC-HARD02-02."""
    resp = client.options(
        "/api/v1/products", headers=_origin_headers("http://localhost:5173")
    )
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


@pytest.mark.integration
def test_security_headers_present(client):
    """AC-HARD02-04."""
    resp = client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("referrer-policy") == "no-referrer"
    assert "uvicorn" not in resp.headers.get("server", "").lower()


@pytest.mark.integration
def test_write_rate_limited_429(client, admin_headers):
    """AC-HARD02-03: 60/min en escrituras, request 61 → 429 con Retry-After."""
    for i in range(60):
        resp = client.post(
            "/api/v1/products",
            json={
                "codigo": f"RL-{i}",
                "nombre": "R",
                "precio": "1.00",
                "cantidad_inicial": 1,
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
    last = client.post(
        "/api/v1/products",
        json={"codigo": "RL-60", "nombre": "R", "precio": "1.00", "cantidad_inicial": 1},
        headers=admin_headers,
    )
    assert last.status_code == 429
    assert "retry-after" in last.headers


@pytest.mark.integration
def test_prod_refuses_example_config(monkeypatch):
    """AC-HARD02-05: prod no arranca con secreto o CORS de ejemplo."""
    monkeypatch.setenv("POS_ENV", "prod")
    monkeypatch.setenv("STOCK_JWT_SECRET", "change-me-dev-only")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        get_settings()
    monkeypatch.setenv("STOCK_JWT_SECRET", "secreto-test-largo-1234567890")
    monkeypatch.setenv("STOCK_CORS_ORIGINS", "*")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        get_settings()
    get_settings.cache_clear()


@pytest.mark.integration
def test_docs_disabled_in_prod(monkeypatch):
    """AC-HARD02-06."""
    monkeypatch.setenv("POS_ENV", "prod")
    monkeypatch.setenv("STOCK_JWT_SECRET", "secreto-test-largo-1234567890")
    monkeypatch.setenv("STOCK_CORS_ORIGINS", "http://localhost:5173")
    get_settings.cache_clear()
    prod_app = importlib.reload(main_module).app
    try:
        with TestClient(prod_app) as c:
            assert c.get("/docs").status_code == 404
            assert c.get("/openapi.json").status_code == 404
    finally:
        get_settings.cache_clear()
        importlib.reload(main_module)
