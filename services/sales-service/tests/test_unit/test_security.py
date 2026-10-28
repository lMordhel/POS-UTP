"""AC-AUTH01 (SPEC-AUTH-001 T2): hashing, JWT y RBAC — skill python-testing-patterns (AAA)."""
from datetime import timedelta

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from app.core import security


def test_hash_no_plaintext_and_verify():
    hashed = security.hash_password("Secreta123")
    assert hashed != "Secreta123"
    assert security.verify_password("Secreta123", hashed) is True
    assert security.verify_password("otra-clave", hashed) is False


def test_access_token_roundtrip_claims():
    token = security.create_access_token("ana", "cajero")
    claims = security.decode_token(token)
    assert claims["sub"] == "ana"
    assert claims["rol"] == "cajero"
    assert claims["type"] == "access"


def test_expired_token_rejected():
    token = security.create_access_token(
        "ana", "cajero", expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(pyjwt.ExpiredSignatureError):
        security.decode_token(token)


def test_tampered_token_rejected():
    token = security.create_access_token("ana", "cajero") + "x"
    with pytest.raises(pyjwt.InvalidTokenError):
        security.decode_token(token)


def test_check_role_allows_and_forbids():
    assert security.check_role({"sub": "a", "rol": "admin"}, "admin")["rol"] == "admin"
    with pytest.raises(HTTPException) as exc:
        security.check_role({"sub": "c", "rol": "cajero"}, "admin")
    assert exc.value.status_code == 403


def test_service_token_has_admin_role_and_service_type():
    claims = security.decode_token(security.create_service_token())
    assert claims["sub"] == security.SERVICE_SUBJECT
    assert claims["rol"] == "admin"
    assert claims["type"] == "service"


def test_get_current_claims_rejects_refresh_token():
    """S1: un refresh firmado y vigente no es una credencial de acceso."""
    refresh = security.create_refresh_token("1", "admin", family="f-1")
    with pytest.raises(HTTPException) as exc:
        security.get_current_claims(refresh)
    assert exc.value.status_code == 401


def test_get_current_claims_rejects_token_without_type():
    """S1: no hay default permisivo cuando falta el claim `type`."""
    from app.core.config import get_settings

    settings = get_settings()
    token = pyjwt.encode(
        {"sub": "1", "rol": "admin"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc:
        security.get_current_claims(token)
    assert exc.value.status_code == 401
