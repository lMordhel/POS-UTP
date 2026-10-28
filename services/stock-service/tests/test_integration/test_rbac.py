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


@pytest.mark.integration
def test_refresh_token_rejected_as_access(client):
    """S1: el refresh (7 días) no autentica rutas protegidas de Stock."""
    from app.core import security

    refresh = security.create_refresh_token("1", "admin", family="f-stock-1")
    headers = {"Authorization": f"Bearer {refresh}"}
    assert client.get("/api/v1/products", headers=headers).status_code == 401
    assert client.patch(
        "/api/v1/products/1/stock", json={"delta": -1}, headers=headers
    ).status_code == 401


def _service_token() -> str:
    """Réplica del token que emite Sales (ADR-008 addendum): rol admin, type service."""
    from datetime import datetime, timedelta, timezone

    import jwt as pyjwt

    from app.core.config import get_settings

    settings = get_settings()
    now = datetime.now(timezone.utc)
    return pyjwt.encode(
        {
            "sub": "svc-sales",
            "rol": "admin",
            "type": "service",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


@pytest.mark.integration
def test_service_token_still_allowed(client, sample_product):
    """S1 (regresión): cerrar el bypass no rompe la credencial Sales→Stock."""
    headers = {"Authorization": f"Bearer {_service_token()}"}
    assert client.get("/api/v1/products", headers=headers).status_code == 200
    assert client.patch(
        f"/api/v1/products/{sample_product['id']}/stock",
        json={"delta": -1, "motivo": "venta:1"},
        headers=headers,
    ).status_code == 200


_PUBLIC = {"/health", "/metrics", "/ready"}


def _protected_routes() -> list[tuple[str, str]]:
    """(método, ruta con id concreto) de todo lo que NO es público."""
    import re

    import app.main as main_module

    found: list[tuple[str, str]] = []
    for path, operations in main_module.app.openapi()["paths"].items():
        if path in _PUBLIC:
            continue
        concrete = re.sub(r"\{[^}]+\}", "1", path)
        found.extend((method.upper(), concrete) for method in operations)
    return sorted(found)


@pytest.mark.integration
def test_every_protected_route_rejects_refresh_token(client):
    """S1: barrido completo — el refresh no autentica NINGUNA ruta de Stock."""
    from app.core import security

    refresh = security.create_refresh_token("1", "admin", family="f-sweep")
    headers = {"Authorization": f"Bearer {refresh}"}
    routes = _protected_routes()
    assert routes, "el barrido no enumeró rutas: revisar _protected_routes"
    for method, path in routes:
        resp = client.request(method, path, headers=headers)
        assert resp.status_code == 401, f"{method} {path} devolvió {resp.status_code}"


@pytest.mark.integration
def test_every_protected_route_accepts_access_token(client, admin_headers):
    """S1 (regresión): el barrido no puede pasar por rechazar todo."""
    routes = _protected_routes()
    assert routes
    for method, path in routes:
        resp = client.request(method, path, headers=admin_headers)
        assert resp.status_code != 401, f"{method} {path} rechazó un access token válido"
