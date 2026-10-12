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
    resp = client.options("/api/v1/sales", headers=_origin_headers("http://evil.test"))
    assert "access-control-allow-origin" not in resp.headers


@pytest.mark.integration
def test_cors_allows_frontend(client):
    """AC-HARD02-02."""
    resp = client.options(
        "/api/v1/sales", headers=_origin_headers("http://localhost:5173")
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
def test_login_rate_limited_429(client, seed_users):
    """AC-HARD02-03: 5/min en login, sexto → 429 con Retry-After."""
    for _ in range(5):
        assert (
            client.post(
                "/api/v1/auth/login", json={"username": "admin", "password": "mala"}
            ).status_code
            == 401
        )
    sixth = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "mala"}
    )
    assert sixth.status_code == 429
    assert "retry-after" in sixth.headers


@pytest.mark.integration
def test_prod_refuses_example_config(monkeypatch):
    """AC-HARD02-05: prod no arranca con admin o CORS de ejemplo."""
    monkeypatch.setenv("POS_ENV", "prod")
    monkeypatch.setenv("SALES_JWT_SECRET", "secreto-test-largo-1234567890")
    monkeypatch.setenv("SALES_ADMIN_PASSWORD", "change-me-admin")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        get_settings()
    monkeypatch.setenv("SALES_ADMIN_PASSWORD", "AdminProd123")
    monkeypatch.setenv("SALES_CORS_ORIGINS", "*")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        get_settings()
    get_settings.cache_clear()


@pytest.mark.integration
def test_docs_disabled_in_prod(monkeypatch):
    """AC-HARD02-06."""
    monkeypatch.setenv("POS_ENV", "prod")
    monkeypatch.setenv("SALES_JWT_SECRET", "secreto-test-largo-1234567890")
    monkeypatch.setenv("SALES_ADMIN_PASSWORD", "AdminProd123")
    monkeypatch.setenv("SALES_CORS_ORIGINS", "http://localhost:5173")
    get_settings.cache_clear()
    prod_app = importlib.reload(main_module).app
    try:
        with TestClient(prod_app) as c:
            assert c.get("/docs").status_code == 404
            assert c.get("/openapi.json").status_code == 404
    finally:
        get_settings.cache_clear()
        importlib.reload(main_module)
