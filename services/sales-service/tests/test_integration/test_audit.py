"""AC-OPS01-06 (SPEC-OPS-001): eventos de seguridad en logs — AAA."""
import logging

import pytest


@pytest.mark.integration
def test_login_failure_logged(client, seed_users, caplog):
    with caplog.at_level(logging.INFO, logger="app.services.auth_service"):
        assert client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "mala"}
        ).status_code == 401
    assert any("login fallido" in r.message and "admin" in r.message for r in caplog.records)


@pytest.mark.integration
def test_login_ok_and_user_crud_logged(client, seed_users, admin_headers, caplog):
    with caplog.at_level(logging.INFO, logger="app.services.auth_service"):
        assert client.post(
            "/api/v1/auth/login", json={"username": "caja", "password": "Caja1234"}
        ).status_code == 200
    assert any("login ok" in r.message for r in caplog.records)
    with caplog.at_level(logging.INFO, logger="app.services.user_service"):
        resp = client.post(
            "/api/v1/users",
            json={"username": "auditado", "password": "Secreta12", "rol": "cajero"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
    assert any("usuario creado" in r.message and "auditado" in r.message for r in caplog.records)


@pytest.mark.integration
def test_refresh_reuse_logged(client, seed_users, caplog):
    first = client.post(
        "/api/v1/auth/login", json={"username": "caja", "password": "Caja1234"}
    ).json()
    second = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    ).json()
    with caplog.at_level(logging.WARNING, logger="app.services.auth_service"):
        assert client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        ).status_code == 401
    assert any("refresh reutilizado" in r.message for r in caplog.records)
    assert second["refresh_token"]
