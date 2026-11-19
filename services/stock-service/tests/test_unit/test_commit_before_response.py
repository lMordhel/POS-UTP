"""La respuesta confirma una escritura YA commiteada.

Regresión real (verificada contra Postgres en docker compose): con el
`db.commit()` dentro del `yield` de `get_db`, FastAPI >= 0.106 lo ejecutaba
DESPUÉS de enviar la respuesta. Una lectura inmediata devolvía el estado
anterior (10/10 lecturas obsoletas sin espera, 0/10 con 300 ms) y un fallo de
commit no podía reportarse: el cliente ya tenía su 2xx.

Estos tests usan un archivo SQLite con conexiones independientes (no el
`StaticPool` compartido del conftest) porque con una sola conexión el commit es
invisible y el defecto queda oculto.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db  # noqa: F401 — get_db documenta el contrato
from app.main import app
from app.models import inventory, inventory_movement, product, stock_adjustment  # noqa: F401
from app.repositories.product_repository import product_repository
from app.schemas.product import ProductCreate
from app.services.product_service import product_service


@pytest.fixture()
def isolated_client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'commit.db'}")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    from app.core import database as database_module

    monkeypatch.setattr(database_module, "_request_session_factory", factory)
    with TestClient(app) as client:
        yield client, factory
    engine.dispose()


@pytest.mark.integration
def test_create_product_returns_after_commit(isolated_client, admin_headers):
    client, factory = isolated_client
    response = client.post(
        "/api/v1/products",
        json={"codigo": "C-001", "nombre": "Commit", "precio": "10.00", "cantidad_inicial": 10},
        headers=admin_headers,
    )
    assert response.status_code == 201
    product_id = response.json()["id"]

    other = factory()
    try:
        assert product_repository.get(other, product_id) is not None
    finally:
        other.close()


@pytest.mark.integration
def test_adjust_stock_returns_after_commit(isolated_client, admin_headers):
    client, factory = isolated_client
    created = client.post(
        "/api/v1/products",
        json={"codigo": "C-002", "nombre": "Commit", "precio": "10.00", "cantidad_inicial": 10},
        headers=admin_headers,
    ).json()

    response = client.patch(
        f"/api/v1/products/{created['id']}/stock",
        json={"delta": 5, "motivo": "prueba"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["cantidad"] == 15

    other = factory()
    try:
        assert product_service.get_stock(other, created["id"]).cantidad == 15
    finally:
        other.close()


@pytest.mark.integration
def test_failed_write_does_not_commit_the_successful_return(
    isolated_client, admin_headers
):
    """Un rechazo (409) no deja rastro: nada se confirma antes de responder."""
    client, factory = isolated_client
    created = client.post(
        "/api/v1/products",
        json={"codigo": "C-003", "nombre": "Commit", "precio": "10.00", "cantidad_inicial": 1},
        headers=admin_headers,
    ).json()

    response = client.patch(
        f"/api/v1/products/{created['id']}/stock",
        json={"delta": -5, "motivo": "sin stock"},
        headers=admin_headers,
    )
    assert response.status_code == 409

    other = factory()
    try:
        assert product_service.get_stock(other, created["id"]).cantidad == 1
    finally:
        other.close()
