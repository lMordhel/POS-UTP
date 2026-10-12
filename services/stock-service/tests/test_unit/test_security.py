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
