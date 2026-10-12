"""Acceso a datos de usuarios y refresh tokens (SPEC-AUTH-001, skill fastapi-templates)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.user import RefreshToken, User


def create_user(db: Session, username: str, password_hash: str, rol: str) -> User:
    user = User(username=username, password_hash=password_hash, rol=rol)
    db.add(user)
    db.flush()
    return user


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).one_or_none()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).one_or_none()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).order_by(User.id).offset(skip).limit(limit).all()


def count(db: Session) -> int:
    return db.query(User).count()


def create_refresh(
    db: Session, jti: str, user_id: int, family: str, expira=None
) -> RefreshToken:
    record = RefreshToken(
        jti=jti,
        user_id=user_id,
        family=family,
        expira=expira or (datetime.now(timezone.utc) + timedelta(days=7)),
    )
    db.add(record)
    db.flush()
    return record


def get_refresh_by_jti(db: Session, jti: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.jti == jti).one_or_none()


def revoke_family(db: Session, family: str) -> int:
    rows = db.query(RefreshToken).filter(RefreshToken.family == family).all()
    for record in rows:
        record.revocado = True
    db.flush()
    return len(rows)
