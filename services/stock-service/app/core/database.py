"""DB wiring (skill fastapi-templates: core/database, sync variant).

Async was evaluated; sync SQLAlchemy is used for academic simplicity and
reliable SQLite/Postgres tests on Windows. DI shape (get_db via Depends)
and layering are unchanged.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


_settings = get_settings()
_connect_args = {"check_same_thread": False} if _settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(_settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    from app.models import product, inventory  # noqa: F401 — register tables

    Base.metadata.create_all(bind=engine)
