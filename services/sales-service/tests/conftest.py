"""Shared fixtures: SQLite + TestClient + FakeStockClient (no real HTTP)."""

import sys
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

from app.clients.stock_client import (  # noqa: E402
    StockInsufficientError,
    StockProduct,
    StockProductNotFoundError,
    StockUnavailableError,
)
from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services import sale_service as sale_service_module  # noqa: E402


class FakeStockClient:
    """In-memory Stock double. Mirrors StockClient interface."""

    def __init__(self):
        self.reset()
        self.fail_unavailable = False

    def reset(self):
        self.products = {
            1: StockProduct(
                id=1, codigo="P-001", nombre="Café", precio=Decimal("10.50"),
                activo=True, stock=100,
            ),
            2: StockProduct(
                id=2, codigo="P-002", nombre="Azúcar", precio=Decimal("5.00"),
                activo=True, stock=3,
            ),
            3: StockProduct(
                id=3, codigo="P-003", nombre="Inactivo", precio=Decimal("7.00"),
                activo=False, stock=50,
            ),
        }
        self.adjust_calls: list[tuple[int, int, str]] = []

    def _guard(self):
        if self.fail_unavailable:
            raise StockUnavailableError("stock caído (fake)")

    def get_product(self, product_id: int) -> StockProduct:
        self._guard()
        try:
            return self.products[product_id]
        except KeyError:
            raise StockProductNotFoundError(f"producto inexistente: {product_id}")

    def get_stock(self, product_id: int) -> int:
        return self.get_product(product_id).stock

    def adjust_stock(self, product_id: int, delta: int, motivo: str) -> int:
        self._guard()
        product = self.get_product(product_id)
        new_qty = product.stock + delta
        if new_qty < 0:
            raise StockInsufficientError("stock insuficiente (fake)")
        product.stock = new_qty
        self.adjust_calls.append((product_id, delta, motivo))
        return new_qty


@pytest.fixture()
def fake_stock():
    return FakeStockClient()


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from app.models import sale, sale_detail  # noqa: F401 — register tables

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_engine, fake_stock, monkeypatch):
    TestingSession = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    monkeypatch.setattr(sale_service_module.sale_service, "client", fake_stock)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
