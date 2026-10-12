"""Bootstrap del primer admin (SPEC-AUTH-001, FR-08 / OQ-AUTH-04 DECIDED)."""
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import get_settings
from app.repositories import user_repository


def ensure_admin_user(db: Session) -> object | None:
    """Crea el admin inicial desde env solo si no existe ningún usuario."""
    if user_repository.count(db) > 0:
        return None
    settings = get_settings()
    return user_repository.create_user(
        db,
        settings.ADMIN_USERNAME,
        security.hash_password(settings.ADMIN_PASSWORD),
        "admin",
    )
