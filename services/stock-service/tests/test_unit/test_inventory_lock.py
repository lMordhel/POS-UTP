"""S2: el ajuste de inventario no puede perder escrituras concurrentes.

Por qué este test no usa dos hilos: SQLite —el motor de toda la suite— ignora
`FOR UPDATE` en silencio. Un test de concurrencia sobre SQLite pasaría igual
con y sin el lock, así que no probaría nada. La evidencia se toma donde el lock
existe de verdad: el SQL compilado para Postgres (motor de despliegue), más la
verificación de que `adjust_stock` atraviesa el lector bloqueante.
"""
import pytest
from sqlalchemy.dialects import postgresql


def test_locked_statement_compiles_with_for_update():
    """El lector bloqueante emite `SELECT ... FOR UPDATE` en Postgres."""
    from app.repositories.product_repository import locked_inventory_statement

    sql = str(locked_inventory_statement(7).compile(dialect=postgresql.dialect()))

    assert "FOR UPDATE" in sql.upper()
    assert "inventories" in sql
    # El lock es sobre la fila de ese producto, no una tabla entera.
    assert "producto_id" in sql


@pytest.mark.integration
def test_adjust_stock_reads_inventory_under_row_lock(
    client, sample_product, admin_headers, monkeypatch
):
    """`adjust_stock` pasa por el lector bloqueante (no por el de lectura suelta).

    Sin esto el fix podría existir en el repositorio y no usarse nunca; el
    read-modify-write seguiría perdiendo escrituras igual que antes.
    """
    from app.repositories.product_repository import inventory_repository

    locked_reads: list[int] = []
    original = inventory_repository.get_by_product_for_update

    def spy(db, producto_id):
        locked_reads.append(producto_id)
        return original(db, producto_id)

    monkeypatch.setattr(inventory_repository, "get_by_product_for_update", spy)

    resp = client.patch(
        f"/api/v1/products/{sample_product['id']}/stock",
        json={"delta": -3, "motivo": "venta:1"},
        headers=admin_headers,
    )

    assert resp.status_code == 200
    assert resp.json()["cantidad"] == sample_product["stock"] - 3
    assert locked_reads == [sample_product["id"]]
