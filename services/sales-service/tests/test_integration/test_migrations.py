"""AC-OPS01-01/02/03 (SPEC-OPS-001): migraciones Sales — AAA."""
from sqlalchemy import create_engine, inspect

from app.core.database import Base, downgrade_database, migrate_database


def _tables(url: str) -> set[str]:
    eng = create_engine(url)
    try:
        return set(inspect(eng).get_table_names())
    finally:
        eng.dispose()


def test_baseline_upgrades_clean(tmp_path):
    """AC-OPS01-01."""
    url = f"sqlite:///{tmp_path}/fresh.db"
    assert migrate_database(url) == "upgraded"
    names = _tables(url)
    assert {"sales", "sale_details", "users", "refresh_tokens", "idempotency_keys", "alembic_version"} <= names


def test_adopt_legacy_db_preserves_data(tmp_path):
    """AC-OPS01-02: DB pre-Alembic con datos → stamp + conserva."""
    from decimal import Decimal

    from sqlalchemy.orm import Session

    from app.models.sale import Sale

    url = f"sqlite:///{tmp_path}/legacy.db"
    eng = create_engine(url)
    Base.metadata.create_all(bind=eng)
    with Session(eng) as session:
        session.add(Sale(total=Decimal("10.00"), estado="confirmada"))
        session.commit()
    eng.dispose()
    assert migrate_database(url) == "stamped"
    eng = create_engine(url)
    try:
        with Session(eng) as session:
            assert session.query(Sale).count() == 1
    finally:
        eng.dispose()
    assert migrate_database(url) == "upgraded"


def test_downgrade_reverts(tmp_path):
    """AC-OPS01-03."""
    url = f"sqlite:///{tmp_path}/down.db"
    migrate_database(url)
    downgrade_database(url)
    assert "sales" not in _tables(url)
    assert migrate_database(url) == "upgraded"
    assert "sales" in _tables(url)
