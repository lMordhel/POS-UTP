"""Shared fixtures (skill python-testing-patterns + fastapi-templates testing)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from app.models import inventory, inventory_movement, product, stock_adjustment  # noqa: F401 — register tables

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_engine, monkeypatch):
    TestingSession = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    # Se parchea el punto de inyección de `get_db`, no `SessionLocal`: así el
    # test usa el mismo wiring que producción (commit en la ruta, antes de
    # responder) sin arrastrar el bootstrap de `init_db` a la DB del test.
    from app.core import database as database_module

    monkeypatch.setattr(database_module, "_request_session_factory", TestingSession)

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _fresh_limiter():
    """Aísla el rate limiting entre tests (SPEC-AUTH-002)."""
    try:
        from app.core import middleware as middleware_module
    except ImportError:
        yield
        return
    middleware_module.limiter.reset()
    yield


@pytest.fixture()
def admin_headers():
    """Token admin (Stock solo verifica firma/rol, sin tabla users)."""
    from app.core import security as security_module

    token = security_module.create_access_token("1", "admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def cashier_headers():
    from app.core import security as security_module

    token = security_module.create_access_token("2", "cajero")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_product(client, admin_headers):
    resp = client.post(
        "/api/v1/products",
        json={
            "codigo": "P-001",
            "nombre": "Producto base",
            "descripcion": "Para tests",
            "precio": "10.50",
            "cantidad_inicial": 100,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    return resp.json()
