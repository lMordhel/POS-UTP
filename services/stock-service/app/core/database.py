"""DB wiring + Alembic (SPEC-OPS-001, sync variant).

Un solo camino: `init_db` migra (`upgrade head`) o adopta (`stamp head`
en DBs pre-Alembic con datos). Downgrade reservado a dev/tests.
"""
from collections.abc import Iterator
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


_settings = get_settings()
_connect_args = {"check_same_thread": False} if _settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(_settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

_ALEMBIC_DIR = Path(__file__).resolve().parents[2] / "alembic"
_BUSINESS_TABLES = {"products", "inventories"}


def _has_version_row(eng, names: set[str]) -> bool:
    """Tabla con fila (una tabla vacía es resto de un upgrade caído)."""
    if "alembic_version" not in names:
        return False
    with eng.connect() as conn:
        return conn.execute(text("select version_num from alembic_version")).fetchone() is not None


def _config(url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(_ALEMBIC_DIR))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def migrate_database(url: str) -> str:
    """Un solo camino (OQ-AUD-02): vacía → `upgrade head`; pre-Alembic con
    datos → `create_all` (rellena huecos), luego `stamp head` (adopta)."""
    cfg = _config(url)
    if len(ScriptDirectory.from_config(cfg).get_heads()) != 1:
        raise RuntimeError("historial con múltiples heads")
    eng = create_engine(url)
    try:
        names = set(inspect(eng).get_table_names())
        versioned = _has_version_row(eng, names)
        if not versioned:
            if names & _BUSINESS_TABLES:
                Base.metadata.create_all(bind=eng)
                command.stamp(cfg, "head")
                return "stamped"
            command.upgrade(cfg, "head")
            return "upgraded"
        command.upgrade(cfg, "head")
        return "upgraded"
    finally:
        eng.dispose()


def downgrade_database(url: str, revision: str = "base") -> None:
    """Solo dev/tests (BR-01: en prod solo hacia adelante)."""
    command.downgrade(_config(url), revision)


def check_db() -> bool:
    """SPEC-OPS-002: chequeo real para `/ready` (SELECT 1)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
        return True
    except Exception:
        return False


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
    from app.models import inventory, inventory_movement, product, stock_adjustment  # noqa: F401 — register tables

    migrate_database(_settings.DATABASE_URL)
