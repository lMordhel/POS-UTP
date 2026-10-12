"""Seguridad base SPEC-AUTH-001 (T2): hash bcrypt, JWT HS256 y RBAC.

Stock y Sales comparten forma; cada servicio usa su propio secreto
(STOCK_JWT_SECRET / SALES_JWT_SECRET, mismo valor en despliegue).
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
CREDENTIALS_EXCEPTION = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    "credenciales inválidas",
    {"WWW-Authenticate": "Bearer"},
)
SERVICE_SUBJECT = "svc-sales"


def create_service_token() -> str:
    """Credencial Sales→Stock (ADR-008 addendum): secreto compartido, rol admin.

    Se genera fresca por llamada (TTL 15 min, uso inmediato): sin estado ni
    renovación. La atribución de usuario viaja en `motivo=venta:{id}`.
    """
    settings = get_settings()
    claims = _base_claims(SERVICE_SUBJECT, "admin", "service")
    claims["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_MINUTES
    )
    return pyjwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


def _base_claims(sub: str, rol: str, kind: str) -> dict:
    now = datetime.now(timezone.utc)
    return {"sub": sub, "rol": rol, "type": kind, "iat": now, "jti": str(uuid4())}


def create_access_token(sub: str, rol: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    claims = _base_claims(sub, rol, "access")
    claims["exp"] = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    )
    return pyjwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    sub: str, rol: str, family: str, expires_delta: timedelta | None = None
) -> str:
    settings = get_settings()
    claims = _base_claims(sub, rol, "refresh")
    claims["family"] = family
    claims["exp"] = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_DAYS)
    )
    return pyjwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    settings = get_settings()
    return pyjwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def get_current_claims(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return decode_token(token)
    except pyjwt.PyJWTError:
        raise CREDENTIALS_EXCEPTION from None


def check_role(claims: dict, *roles: str) -> dict:
    if claims.get("rol") not in roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "permiso insuficiente")
    return claims


def require_role(*roles: str):
    def dependency(claims: dict = Depends(get_current_claims)):
        return check_role(claims, *roles)

    return dependency
