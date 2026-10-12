"""AC-AUTH01 (SPEC-AUTH-001 T3): users, refresh_tokens y bootstrap admin — AAA."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core import security
from app.repositories import user_repository
from app.services import bootstrap


@pytest.fixture()
def clean_settings(monkeypatch):
    monkeypatch.setenv("SALES_ADMIN_USERNAME", "jefe")
    monkeypatch.setenv("SALES_ADMIN_PASSWORD", "Clave1234")
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


def test_create_and_get_user(db_engine):
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=db_engine)
    db = Session()
    user = user_repository.create_user(
        db, "ana", security.hash_password("Secreta123"), "cajero"
    )
    db.commit()
    found = user_repository.get_by_username(db, "ana")
    assert found.id == user.id
    assert found.password_hash != "Secreta123"
    assert security.verify_password("Secreta123", found.password_hash)
    assert found.activo is True
    db.close()


def test_duplicate_username_rejected(db_engine):
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=db_engine)
    db = Session()
    user_repository.create_user(db, "ana", "hash-1", "cajero")
    db.commit()
    with pytest.raises(IntegrityError):
        user_repository.create_user(db, "ana", "hash-2", "admin")
        db.commit()
    db.rollback()
    db.close()


def test_refresh_lifecycle_and_revoke(db_engine):
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=db_engine)
    db = Session()
    user = user_repository.create_user(db, "ana", "hash", "cajero")
    db.commit()
    rt = user_repository.create_refresh(
        db, jti="jti-1", user_id=user.id, family="fam-1", expira=None
    )
    db.commit()
    assert user_repository.get_refresh_by_jti(db, "jti-1").id == rt.id
    assert user_repository.get_refresh_by_jti(db, "OTRO") is None
    user_repository.revoke_family(db, "fam-1")
    db.commit()
    assert user_repository.get_refresh_by_jti(db, "jti-1").revocado is True
    db.close()


def test_bootstrap_creates_admin_only_when_empty(db_engine, clean_settings):
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=db_engine)
    db = Session()
    created = bootstrap.ensure_admin_user(db)
    db.commit()
    assert created is not None
    assert created.username == "jefe" and created.rol == "admin"
    assert security.verify_password("Clave1234", created.password_hash)
    assert bootstrap.ensure_admin_user(db) is None
    db.commit()
    assert user_repository.count(db) == 1
    db.close()
