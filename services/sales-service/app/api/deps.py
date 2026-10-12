"""Dependencias FastAPI de autenticación (SPEC-AUTH-001, BR-01/BR-03)."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    CREDENTIALS_EXCEPTION,
    check_role,
    get_current_claims,
)
from app.models.user import User
from app.repositories import user_repository


def get_current_user(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_claims),
) -> User:
    try:
        user_id = int(claims.get("sub", ""))
    except (TypeError, ValueError):
        raise CREDENTIALS_EXCEPTION from None
    user = user_repository.get_by_id(db, user_id)
    if user is None or not user.activo:
        raise CREDENTIALS_EXCEPTION
    return user


def require_active_role(*roles: str):
    def dependency(user: User = Depends(get_current_user)):
        check_role({"rol": user.rol}, *roles)
        return user

    return dependency
