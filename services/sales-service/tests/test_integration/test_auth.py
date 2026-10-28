"""AC-AUTH01 (SPEC-AUTH-001 T4): login, RBAC, users y refresh — AAA + integración."""
import pytest
from fastapi.testclient import TestClient


def _login(client: TestClient, username: str, password: str):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


@pytest.mark.integration
def test_login_valid_returns_pair(client, seed_users):
    """AC-AUTH01-01."""
    response = _login(client, "admin", "Admin1234")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]


@pytest.mark.integration
def test_login_invalid_returns_401(client, seed_users):
    """AC-AUTH01-02: no distingue usuario de password."""
    assert _login(client, "admin", "mala").status_code == 401
    assert _login(client, "nadie", "Clave123").status_code == 401


@pytest.mark.integration
def test_protected_without_token_401(client, seed_users):
    """AC-AUTH01-03."""
    assert client.get("/api/v1/sales").status_code == 401
    assert client.post("/api/v1/sales", json={"items": [{"producto_id": 1, "cantidad": 1}]}).status_code == 401
    assert client.get("/api/v1/users").status_code == 401


@pytest.mark.integration
def test_cashier_forbidden_users_403(client, cashier_headers):
    """AC-AUTH01-06/08: cajero directo a gestión de usuarios → 403."""
    assert client.get("/api/v1/users", headers=cashier_headers).status_code == 403
    assert client.post(
        "/api/v1/users",
        json={"username": "x", "password": "Secreta12", "rol": "cajero"},
        headers=cashier_headers,
    ).status_code == 403


@pytest.mark.integration
def test_cashier_can_sell_and_read(client, cashier_headers):
    """AC-AUTH01-05."""
    created = client.post(
        "/api/v1/sales",
        json={"items": [{"producto_id": 1, "cantidad": 1}]},
        headers=cashier_headers,
    )
    assert created.status_code == 201
    assert client.get("/api/v1/sales", headers=cashier_headers).status_code == 200


@pytest.mark.integration
def test_admin_user_crud(client, admin_headers):
    """AC-AUTH01-06: crear, duplicado 409, listar, desactivar; sin hash expuesto."""
    created = client.post(
        "/api/v1/users",
        json={"username": "nuevo", "password": "Secreta12", "rol": "cajero"},
        headers=admin_headers,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["username"] == "nuevo" and body["rol"] == "cajero"
    assert "password_hash" not in body and "password" not in body
    dup = client.post(
        "/api/v1/users",
        json={"username": "nuevo", "password": "OtraClave1", "rol": "cajero"},
        headers=admin_headers,
    )
    assert dup.status_code == 409
    listing = client.get("/api/v1/users", headers=admin_headers)
    assert listing.status_code == 200 and len(listing.json()) >= 3
    patched = client.patch(
        f"/api/v1/users/{body['id']}", json={"activo": False}, headers=admin_headers
    )
    assert patched.status_code == 200 and patched.json()["activo"] is False
    assert client.get("/api/v1/users/9999", headers=admin_headers).status_code == 404


@pytest.mark.integration
def test_deactivated_user_loses_access(client, admin_headers):
    """AC-AUTH01-07."""
    created = client.post(
        "/api/v1/users",
        json={"username": "fuera", "password": "Secreta12", "rol": "cajero"},
        headers=admin_headers,
    ).json()
    token = _login(client, "fuera", "Secreta12").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/sales", headers=headers).status_code == 200
    client.patch(f"/api/v1/users/{created['id']}", json={"activo": False}, headers=admin_headers)
    assert client.get("/api/v1/sales", headers=headers).status_code == 401


@pytest.mark.integration
def test_expired_token_401(client, seed_users):
    """AC-AUTH01-03 con token expirado."""
    from datetime import timedelta

    from app.core import security

    expired = security.create_access_token("1", "admin", expires_delta=timedelta(seconds=-1))
    headers = {"Authorization": f"Bearer {expired}"}
    assert client.get("/api/v1/sales", headers=headers).status_code == 401


@pytest.mark.integration
def test_refresh_rotates_pair(client, seed_users):
    """AC-AUTH01-09: refresh válido rota; el anterior queda invalidado."""
    first = _login(client, "caja", "Caja1234").json()
    second = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert second.status_code == 200
    assert second.json()["refresh_token"] != first["refresh_token"]
    reuse = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert reuse.status_code == 401


@pytest.mark.integration
def test_refresh_reuse_revokes_family(client, seed_users):
    """AC-AUTH01-10: reusar un refresh rotado revoca la familia completa."""
    first = _login(client, "caja", "Caja1234").json()
    second = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    ).json()
    assert client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}
    ).status_code == 401


@pytest.mark.integration
def test_refresh_token_rejected_as_access(client, seed_users):
    """S1: el refresh (7 días) no autentica rutas protegidas.

    Antes del fix un token de 7 días entraba como access de 15 minutos en
    cualquier ruta, anulando la rotación con detección de reuso.
    """
    pair = _login(client, "caja", "Caja1234").json()
    headers = {"Authorization": f"Bearer {pair['refresh_token']}"}
    assert client.get("/api/v1/sales", headers=headers).status_code == 401
    assert client.get("/api/v1/users", headers=headers).status_code == 401


@pytest.mark.integration
def test_access_token_still_accepted(client, seed_users):
    """S1 (regresión): el access de 15 minutos sigue entrando."""
    pair = _login(client, "caja", "Caja1234").json()
    headers = {"Authorization": f"Bearer {pair['access_token']}"}
    assert client.get("/api/v1/sales", headers=headers).status_code == 200


_PUBLIC = {"/health", "/metrics", "/ready", "/api/v1/auth/login", "/api/v1/auth/refresh"}


def _protected_routes() -> list[tuple[str, str]]:
    """(método, ruta con id concreto) de todo lo que NO es público.

    Se enumera desde el OpenAPI para que una ruta nueva quede cubierta sin
    tocar el test.
    """
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
def test_every_protected_route_rejects_refresh_token(client, seed_users):
    """S1: barrido completo — el refresh no autentica NINGUNA ruta protegida.

    Un test acotado a /sales solo probaría la ruta que elegí. Este recorre todo
    lo que expone el servicio, así que una ruta nueva sin la dependencia de
auth también lo hace fallar.
    """
    pair = _login(client, "caja", "Caja1234").json()
    headers = {"Authorization": f"Bearer {pair['refresh_token']}"}
    routes = _protected_routes()
    assert routes, "el barrido no enumeró rutas: revisar _protected_routes"
    for method, path in routes:
        resp = client.request(method, path, headers=headers)
        assert resp.status_code == 401, f"{method} {path} devolvió {resp.status_code}"


@pytest.mark.integration
def test_every_protected_route_accepts_access_token(client, admin_headers, seed_users):
    """S1 (regresión): el barrido anterior no puede pasar por rechazar todo."""
    routes = _protected_routes()
    assert routes
    for method, path in routes:
        resp = client.request(method, path, headers=admin_headers)
        assert resp.status_code != 401, f"{method} {path} rechazó un access token válido"
