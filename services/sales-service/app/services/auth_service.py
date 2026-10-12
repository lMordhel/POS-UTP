"""Login y refresh con rotación (SPEC-AUTH-001, FR-02/07)."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt as pyjwt
from sqlalchemy.orm import Session

from app.core import security
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import TokenPair


class InvalidCredentialsError(Exception):
    pass


class RefreshInvalidError(Exception):
    pass


class RefreshReuseError(Exception):
    pass


def authenticate(db: Session, username: str, password: str) -> User:
    user = user_repository.get_by_username(db, username)
    if user is None or not user.activo:
        raise InvalidCredentialsError("credenciales inválidas")
    if not security.verify_password(password, user.password_hash):
        raise InvalidCredentialsError("credenciales inválidas")
    return user


def _pair_for(db: Session, user: User, family: str) -> TokenPair:
    settings = security.get_settings()
    access = security.create_access_token(str(user.id), user.rol)
    refresh = security.create_refresh_token(str(user.id), user.rol, family)
    jti = security.decode_token(refresh)["jti"]
    user_repository.create_refresh(
        db,
        jti=jti,
        user_id=user.id,
        family=family,
        expira=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_DAYS),
    )
    return TokenPair(access_token=access, refresh_token=refresh)


def login(db: Session, username: str, password: str) -> TokenPair:
    user = authenticate(db, username, password)
    return _pair_for(db, user, family=str(uuid4()))


def refresh_pair(db: Session, token: str) -> TokenPair:
    try:
        claims = security.decode_token(token)
    except pyjwt.PyJWTError:
        raise RefreshInvalidError("refresh inválido") from None
    if claims.get("type") != "refresh":
        raise RefreshInvalidError("no es un refresh token")
    record = user_repository.get_refresh_by_jti(db, claims.get("jti", ""))
    if record is None:
        raise RefreshInvalidError("refresh desconocido")
    user = user_repository.get_by_id(db, record.user_id)
    if user is None or not user.activo:
        raise RefreshInvalidError("usuario no disponible")
    if record.revocado:
        if record.rotado:
            user_repository.revoke_family(db, record.family)
            db.commit()  # persiste la revocación aunque se lance 401 (el get_db haría rollback)
            raise RefreshReuseError("refresh reutilizado: familia revocada")
        raise RefreshInvalidError("refresh revocado")
    record.revocado = True
    record.rotado = True
    db.flush()
    return _pair_for(db, user, family=record.family)
