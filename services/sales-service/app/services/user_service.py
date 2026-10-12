"""Gestión de usuarios solo admin (SPEC-AUTH-001, FR-05)."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import security
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import UserCreate, UserUpdate


class UserExistsError(ValueError):
    pass


def create(db: Session, data: UserCreate) -> User:
    try:
        user = user_repository.create_user(
            db, data.username, security.hash_password(data.password), data.rol
        )
        db.flush()
        return user
    except IntegrityError:
        raise UserExistsError(f"username duplicado: {data.username}") from None


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return user_repository.list_users(db, skip, limit)


def get(db: Session, user_id: int) -> User | None:
    return user_repository.get_by_id(db, user_id)


def update(db: Session, user_id: int, data: UserUpdate) -> User | None:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        return None
    if data.rol is not None:
        user.rol = data.rol
    if data.activo is not None:
        user.activo = data.activo
    if data.password is not None:
        user.password_hash = security.hash_password(data.password)
    db.flush()
    return user
