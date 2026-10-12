"""AC-OPS01-04/05 (SPEC-OPS-001): auditoría de movimientos — AAA."""
import pytest
from sqlalchemy.orm import sessionmaker

from app.models.inventory_movement import InventoryMovement


def _movements(db_engine):
    Session = sessionmaker(bind=db_engine)
    db = Session()
    try:
        return db.query(InventoryMovement).order_by(InventoryMovement.id).all()
    finally:
        db.close()


@pytest.mark.integration
def test_adjust_writes_movement_with_actor(client, sample_product, admin_headers, db_engine):
    """AC-OPS01-04: ajuste manual de admin deja traza completa."""
    start = sample_product["stock"]
    resp = client.patch(
        f"/api/v1/products/{sample_product['id']}/stock",
        json={"delta": -7, "motivo": "ajuste manual"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    (movement,) = _movements(db_engine)
    assert movement.producto_id == sample_product["id"]
    assert movement.delta == -7
    assert movement.cantidad_antes == start
    assert movement.cantidad_despues == start - 7
    assert movement.motivo == "ajuste manual"
    assert movement.actor_sub == "1" and movement.actor_rol == "admin"
    assert movement.clave is None


@pytest.mark.integration
def test_keyed_adjust_writes_movement_once(client, sample_product, admin_headers, db_engine):
    """AC-OPS01-04/05: primer apply audita; replay no agrega fila."""
    url = f"/api/v1/products/{sample_product['id']}/stock"
    headers = {**admin_headers, "Idempotency-Key": "AUD-1"}
    assert client.patch(url, json={"delta": -3, "motivo": "venta:9"}, headers=headers).status_code == 200
    assert client.patch(url, json={"delta": -3, "motivo": "venta:9"}, headers=headers).status_code == 200
    movements = _movements(db_engine)
    assert len(movements) == 1
    assert movements[0].clave == "AUD-1"
    assert movements[0].motivo == "venta:9"
