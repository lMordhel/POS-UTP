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
