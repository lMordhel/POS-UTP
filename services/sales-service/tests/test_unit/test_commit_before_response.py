"""La respuesta confirma una escritura YA commiteada (sales-service).

Mismo defecto que en stock-service: el `db.commit()` dentro del `yield` de
`get_db` corría DESPUÉS de enviar la respuesta (FastAPI >= 0.106), así que un
cliente que leía justo después de escribir veía el estado anterior y un fallo
de commit no podía reportarse.

Archivo SQLite con conexiones independientes: con el `StaticPool` compartido
del conftest el commit es invisible y el defecto quedaría oculto.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import security
from app.core.database import Base
from app.main import app
from app.models import idempotency, sale, sale_detail, user  # noqa: F401
from app.repositories import user_repository


@pytest.fixture()
def isolated_client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'commit.db'}")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    from app.core import database as database_module

    monkeypatch.setattr(database_module, "_request_session_factory", factory)

    db = factory()
    admin = user_repository.create_user(
        db, "admin", security.hash_password("Admin1234"), "admin"
    )
    db.commit()
    admin_id = admin.id
    db.close()

    token = security.create_access_token(str(admin_id), "admin")
    with TestClient(app) as client:
        yield client, factory, {"Authorization": f"Bearer {token}"}
    engine.dispose()


@pytest.mark.integration
def test_create_user_returns_after_commit(isolated_client):
    client, factory, headers = isolated_client
    response = client.post(
        "/api/v1/users",
        json={"username": "nuevo", "password": "Nuevo1234", "rol": "cajero"},
        headers=headers,
    )
    assert response.status_code == 201
    user_id = response.json()["id"]

    other = factory()
    try:
        assert user_repository.get_by_id(other, user_id) is not None
    finally:
        other.close()


@pytest.mark.integration
def test_rejected_write_leaves_nothing_committed(isolated_client):
    """Un 409 no confirma nada: la respuesta de error y la DB coinciden."""
    client, factory, headers = isolated_client
    response = client.post(
        "/api/v1/users",
        json={"username": "admin", "password": "Otro1234", "rol": "cajero"},
        headers=headers,
    )
    assert response.status_code == 409

    other = factory()
    try:
        assert user_repository.get_by_username(other, "admin").rol == "admin"
    finally:
        other.close()
