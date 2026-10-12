"""AC-OPS01-01/02/03 (SPEC-OPS-001): migraciones Stock — AAA."""
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
    assert {"products", "inventories", "stock_adjustments", "inventory_movements", "alembic_version"} <= names


def test_adopt_legacy_db_preserves_data(tmp_path):
    """AC-OPS01-02: DB pre-Alembic con datos → stamp + conserva."""
    from sqlalchemy.orm import Session

    from app.models.product import Product

    url = f"sqlite:///{tmp_path}/legacy.db"
    eng = create_engine(url)
    Base.metadata.create_all(bind=eng)
    with Session(eng) as session:
        session.add(Product(codigo="LEG-1", nombre="Legado", precio="9.99"))
        session.commit()
    eng.dispose()
    assert migrate_database(url) == "stamped"
    assert "LEG-1" in [
        p.codigo for p in _products(url)
    ]
    assert migrate_database(url) == "upgraded"


def _products(url: str):
    from sqlalchemy.orm import Session

    from app.models.product import Product

    eng = create_engine(url)
    try:
        with Session(eng) as session:
            return list(session.query(Product).all())
    finally:
        eng.dispose()


def test_downgrade_reverts(tmp_path):
    """AC-OPS01-03."""
    url = f"sqlite:///{tmp_path}/down.db"
    migrate_database(url)
    downgrade_database(url)
    assert "products" not in _tables(url)
    assert migrate_database(url) == "upgraded"
    assert "products" in _tables(url)
